"""
FIX-031 — Tests for bottom-up ad-hoc code signing in build_dmg.sh

Verifies that build_dmg.sh uses the bottom-up signing pattern introduced to fix
the 'bundle format unrecognized' CI failure caused by codesign --deep attempting
to recursively sign the python3.11 stdlib directory (not a valid bundle).

The correct signing order is:
  1. Individual .dylib files (find -exec codesign)
  2. Individual .so files (find -exec codesign)
  3. Python.framework with --deep (valid nested bundle)
  4. Main launcher executable
  5. .app bundle WITHOUT --deep (avoids python3.11 dir issue)
  6. codesign --verify --deep --strict (post-sign verification)
"""
import re
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "src" / "installer" / "macos" / "build_dmg.sh"


def _script_text() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def _script_lines():
    return _script_text().splitlines()


# ---------------------------------------------------------------------------
# Test 1: find command for .dylib files
# ---------------------------------------------------------------------------

def test_find_dylib_command_exists():
    """build_dmg.sh must contain a find command that signs .dylib files."""
    lines = _script_lines()
    assert any(
        "find" in line and "*.dylib" in line and "codesign" in line
        for line in lines
    ), "No 'find ... *.dylib ... codesign' command found in build_dmg.sh"


# ---------------------------------------------------------------------------
# Test 2: find command for .so files
# ---------------------------------------------------------------------------

def test_find_so_command_exists():
    """build_dmg.sh must contain a find command that signs .so files."""
    lines = _script_lines()
    assert any(
        "find" in line and "*.so" in line and "codesign" in line
        for line in lines
    ), "No 'find ... *.so ... codesign' command found in build_dmg.sh"


# ---------------------------------------------------------------------------
# Test 3: Python.framework signing uses --deep
# ---------------------------------------------------------------------------

def test_python_framework_signed_with_deep():
    """Python.framework must be signed with codesign --deep (valid nested bundle)."""
    sign_lines = [
        line for line in _script_lines()
        if "codesign" in line and "--sign" in line
    ]
    assert any(
        "--deep" in line and "Python.framework" in line
        for line in sign_lines
    ), (
        "codesign --deep not found for Python.framework — "
        "Python.framework is a valid bundle and requires --deep"
    )


# ---------------------------------------------------------------------------
# Test 4: Main launcher executable signing exists
# ---------------------------------------------------------------------------

def test_main_launcher_signed():
    """The main launcher executable must be explicitly signed before the .app bundle."""
    sign_lines = [
        line for line in _script_lines()
        if "codesign" in line and "--sign" in line
    ]
    assert any(
        "Contents/MacOS/launcher" in line and "--deep" not in line
        for line in sign_lines
    ), (
        "codesign for main launcher (Contents/MacOS/launcher) not found or "
        "incorrectly uses --deep"
    )


# ---------------------------------------------------------------------------
# Test 5: Final .app bundle signing does NOT use --deep
# ---------------------------------------------------------------------------

def test_app_bundle_sign_no_deep():
    """The final .app bundle signing must NOT use --deep (prevents python3.11 dir error)."""
    sign_lines = [
        line for line in _script_lines()
        if "codesign" in line and "--sign" in line
    ]
    app_bundle_lines = [
        line for line in sign_lines
        if line.rstrip().endswith('"${APP_BUNDLE}"')
    ]
    assert app_bundle_lines, (
        "No codesign --sign line targeting '\"${APP_BUNDLE}\"' found"
    )
    assert not any("--deep" in line for line in app_bundle_lines), (
        "--deep must NOT appear on the final .app bundle codesign line; "
        "use bottom-up signing instead to avoid the python3.11 directory issue"
    )


# ---------------------------------------------------------------------------
# Test 6: codesign --verify --deep --strict exists
# ---------------------------------------------------------------------------

def test_verify_deep_strict_present():
    """codesign --verify --deep --strict must be present to catch signing failures."""
    verify_lines = [
        line for line in _script_lines()
        if "codesign" in line and "--verify" in line
    ]
    assert verify_lines, "codesign --verify line not found in build_dmg.sh"
    assert any("--deep" in line and "--strict" in line for line in verify_lines), (
        "codesign --verify must use both --deep and --strict"
    )


# ---------------------------------------------------------------------------
# Test 7: Bottom-up signing happens BEFORE .app bundle signing
# ---------------------------------------------------------------------------

def test_dylib_so_signed_before_app_bundle():
    """find-based dylib/so signing must occur before the final .app bundle sign."""
    lines = _script_lines()

    dylib_indices = [
        i for i, line in enumerate(lines)
        if "find" in line and "*.dylib" in line and "codesign" in line
    ]
    so_indices = [
        i for i, line in enumerate(lines)
        if "find" in line and "*.so" in line and "codesign" in line
    ]
    app_bundle_indices = [
        i for i, line in enumerate(lines)
        if "codesign" in line and "--sign" in line and line.rstrip().endswith('"${APP_BUNDLE}"')
    ]

    assert dylib_indices, "find .dylib codesign not found"
    assert so_indices, "find .so codesign not found"
    assert app_bundle_indices, "Final .app bundle codesign not found"

    assert max(dylib_indices) < min(app_bundle_indices), (
        "dylib signing must come before final .app bundle signing"
    )
    assert max(so_indices) < min(app_bundle_indices), (
        ".so signing must come before final .app bundle signing"
    )


# ---------------------------------------------------------------------------
# Test 8: Step 3.5 label exists
# ---------------------------------------------------------------------------

def test_step_35_label_present():
    """Script must contain the Step 3.5 label to identify the signing block."""
    text = _script_text()
    assert "Step 3.5" in text, "Step 3.5 label not found in build_dmg.sh"
    assert "bottom-up" in text.lower(), (
        "Step 3.5 comment should mention 'bottom-up' to explain the approach"
    )


# ---------------------------------------------------------------------------
# Test 9: set -euo pipefail is still set
# ---------------------------------------------------------------------------

def test_pipefail_still_set():
    """'set -euo pipefail' must be present so any signing failure aborts the build."""
    text = _script_text()
    assert "pipefail" in text, (
        "'set -euo pipefail' not found — codesign failures may be silently ignored"
    )


# ---------------------------------------------------------------------------
# Test 10: Signing order: dylibs/so → framework → launcher → bundle
# ---------------------------------------------------------------------------

def test_signing_order_bottom_up():
    """Signing must proceed bottom-up: dylibs/so first, framework next,
    launcher executable, then the .app bundle last (before verify)."""
    lines = _script_lines()

    def first_index(predicate):
        for i, line in enumerate(lines):
            if predicate(line):
                return i
        return None

    def last_index(predicate):
        result = None
        for i, line in enumerate(lines):
            if predicate(line):
                result = i
        return result

    dylib_idx = first_index(
        lambda l: "find" in l and "*.dylib" in l and "codesign" in l
    )
    so_idx = first_index(
        lambda l: "find" in l and "*.so" in l and "codesign" in l
    )
    framework_idx = first_index(
        lambda l: "codesign" in l and "--sign" in l and "Python.framework" in l
    )
    launcher_idx = first_index(
        lambda l: "codesign" in l and "--sign" in l and "Contents/MacOS/launcher" in l
    )
    bundle_idx = first_index(
        lambda l: "codesign" in l and "--sign" in l and l.rstrip().endswith('"${APP_BUNDLE}"')
    )
    verify_idx = first_index(
        lambda l: "codesign" in l and "--verify" in l
    )

    assert dylib_idx is not None, "dylib signing not found"
    assert so_idx is not None, ".so signing not found"
    assert framework_idx is not None, "Python.framework signing not found"
    assert launcher_idx is not None, "launcher signing not found"
    assert bundle_idx is not None, "final .app bundle signing not found"
    assert verify_idx is not None, "codesign --verify not found"

    # Enforce order: dylibs/so → framework → launcher → bundle → verify
    assert max(dylib_idx, so_idx) < framework_idx, (
        "dylib/so signing must precede Python.framework signing"
    )
    assert framework_idx < launcher_idx, (
        "Python.framework signing must precede launcher signing"
    )
    assert launcher_idx < bundle_idx, (
        "launcher signing must precede final .app bundle signing"
    )
    assert bundle_idx < verify_idx, (
        "final .app bundle signing must precede codesign --verify"
    )
