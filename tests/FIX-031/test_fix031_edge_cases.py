"""
FIX-031 — Tester-added edge-case tests for bottom-up ad-hoc code signing.

These tests cover gaps not addressed by the Developer's original 10 tests:
  - Python.framework signing is guarded by 'if [ -d ... ]'
  - find commands target _internal/ specifically (not a broader directory)
  - ALL codesign --sign lines use --force (not just some)
"""
import re
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "src" / "installer" / "macos" / "build_dmg.sh"


def _script_text() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def _script_lines():
    return _script_text().splitlines()


# ---------------------------------------------------------------------------
# Edge Case 1: Python.framework signing guarded by if [ -d ... ]
# ---------------------------------------------------------------------------

def test_python_framework_signing_guarded_by_if_d():
    """Python.framework signing must be inside an 'if [ -d ... ]' guard.

    Without this guard, the build fails on DMG targets that don't include
    an embedded Python.framework (e.g., future Linux or minimal builds).
    """
    text = _script_text()
    assert re.search(r'if\s+\[\s+-d[^]]*Python\.framework', text), (
        "Python.framework codesign block must be guarded by 'if [ -d ... ]' — "
        "the framework may not be present in all build configurations"
    )


# ---------------------------------------------------------------------------
# Edge Case 2: find commands target _internal/ directory specifically
# ---------------------------------------------------------------------------

def test_find_dylib_targets_internal_directory():
    """The find .dylib command must target _internal/, not a broader path.

    Signing the entire Contents/MacOS directory would attempt to re-sign
    the main launcher executable via glob, which the explicit later step handles.
    Using _internal/ keeps library signing scoped to embedded libraries.
    """
    lines = _script_lines()
    dylib_find_lines = [
        line for line in lines
        if "find" in line and "*.dylib" in line
    ]
    assert dylib_find_lines, "No 'find *.dylib' line found in build_dmg.sh"
    assert all("_internal" in line for line in dylib_find_lines), (
        "find *.dylib command must target the _internal/ directory — "
        f"offending lines: {[l for l in dylib_find_lines if '_internal' not in l]}"
    )


def test_find_so_targets_internal_directory():
    """The find .so command must target _internal/, not a broader path."""
    lines = _script_lines()
    so_find_lines = [
        line for line in lines
        if "find" in line and "*.so" in line
    ]
    assert so_find_lines, "No 'find *.so' line found in build_dmg.sh"
    assert all("_internal" in line for line in so_find_lines), (
        "find *.so command must target the _internal/ directory — "
        f"offending lines: {[l for l in so_find_lines if '_internal' not in l]}"
    )


# ---------------------------------------------------------------------------
# Edge Case 3: ALL codesign --sign lines must use --force
# ---------------------------------------------------------------------------

def test_all_sign_invocations_use_force():
    """Every codesign --sign invocation must include --force.

    Without --force, re-running the sign step on an already-signed binary
    raises 'is already signed' and aborts the build (per set -euo pipefail).
    """
    sign_lines = [
        line for line in _script_lines()
        if "codesign" in line
        and "--sign" in line
        and not line.strip().startswith("#")
    ]
    assert sign_lines, "No codesign --sign lines found"
    missing_force = [line.strip() for line in sign_lines if "--force" not in line]
    assert not missing_force, (
        "The following codesign --sign lines are missing --force:\n"
        + "\n".join(f"  {l}" for l in missing_force)
    )
