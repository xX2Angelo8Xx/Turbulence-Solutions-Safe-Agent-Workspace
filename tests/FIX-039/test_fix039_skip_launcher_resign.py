"""
Tests for FIX-039: Skip launcher re-sign inside .app — verify pre-bundle binary

Verifies that build_dmg.sh and release.yml have been correctly updated:
- The launcher is NOT re-signed inside the .app bundle (avoids CFBundleExecutable
  bundle-validation trigger)
- Verification uses the pre-bundle binary at dist/launcher/launcher
- .dylib, .so, and Python.framework signing is preserved
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
RELEASE_YML = REPO_ROOT / ".github" / "workflows" / "release.yml"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _dmg_content() -> str:
    return BUILD_DMG.read_text(encoding="utf-8")


def _release_content() -> str:
    return RELEASE_YML.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# build_dmg.sh — removed launcher signing inside .app
# ---------------------------------------------------------------------------

def test_build_dmg_no_force_sign_launcher_in_bundle():
    """codesign --force --sign - must NOT target Contents/MacOS/launcher."""
    content = _dmg_content()
    # Pattern: codesign --force --sign - followed by a path containing
    # Contents/MacOS/launcher (but not _internal/ which are valid dylib/so/framework paths)
    matches = re.findall(
        r'codesign\s+--force\s+--sign\s+-\s+["\$\{]*.*Contents/MacOS/launcher[^/_]',
        content,
    )
    assert matches == [], (
        f"build_dmg.sh still re-signs launcher inside the .app bundle: {matches}"
    )


def test_build_dmg_no_verify_launcher_in_bundle():
    """codesign --verify must NOT target Contents/MacOS/launcher (triggers bundle validation)."""
    content = _dmg_content()
    matches = re.findall(
        r'codesign\s+--verify.*Contents/MacOS/launcher[^/_]',
        content,
    )
    assert matches == [], (
        f"build_dmg.sh still verifies launcher inside the .app bundle: {matches}"
    )


def test_build_dmg_verify_pre_bundle_binary():
    """codesign --verify must target the pre-bundle binary at dist/launcher/launcher."""
    content = _dmg_content()
    # Accept both literal dist/launcher/launcher and variable form ${DIST_DIR}/launcher/launcher
    pattern = re.compile(
        r'codesign\s+--verify\s+["\$\{]*(?:DIST_DIR[}\"]*/|\s*dist/)launcher/launcher'
    )
    assert pattern.search(content), (
        "build_dmg.sh does not verify the pre-bundle binary at dist/launcher/launcher"
    )


# ---------------------------------------------------------------------------
# build_dmg.sh — dylib / so / Python.framework signing preserved
# ---------------------------------------------------------------------------

def test_build_dmg_still_signs_dylib():
    """Signing of .dylib files must be preserved.
    Updated: --options runtime is now used between --force and --sign.
    """
    content = _dmg_content()
    # Accept --options runtime between --force and --sign (current approach)
    pattern = re.compile(r'\*\.dylib.*codesign.*--force.*--sign\s+-', re.DOTALL)
    assert pattern.search(content), "build_dmg.sh does not sign .dylib files"


def test_build_dmg_still_signs_so():
    """Signing of .so files must be preserved.
    Updated: --options runtime is now used between --force and --sign.
    """
    content = _dmg_content()
    # Accept --options runtime between --force and --sign (current approach)
    pattern = re.compile(r'\*\.so.*codesign.*--force.*--sign\s+-', re.DOTALL)
    assert pattern.search(content), "build_dmg.sh does not sign .so files"


def test_build_dmg_still_signs_python_framework():
    """Signing of Python.framework must be preserved.
    Updated: --options runtime and --entitlements are now used with --deep --force --sign.
    """
    content = _dmg_content()
    # Accept --options runtime and --entitlements between --deep --force and --sign
    pattern = re.compile(r'codesign\s+--deep.*--force.*--sign\s+-.*Python\.framework')
    assert pattern.search(content), "build_dmg.sh does not sign Python.framework"


def test_build_dmg_still_verifies_python_framework():
    """Verification of Python.framework must be preserved."""
    content = _dmg_content()
    pattern = re.compile(r'codesign\s+--verify.*Python\.framework')
    assert pattern.search(content), "build_dmg.sh does not verify Python.framework"


# ---------------------------------------------------------------------------
# release.yml — verification updated to pre-bundle binary
# ---------------------------------------------------------------------------

def test_release_yml_no_verify_launcher_in_bundle():
    """release.yml must NOT verify launcher at Contents/MacOS/launcher."""
    content = _release_content()
    matches = re.findall(
        r'codesign\s+--verify.*Contents/MacOS/launcher',
        content,
    )
    assert matches == [], (
        f"release.yml still references Contents/MacOS/launcher for verification: {matches}"
    )


def test_release_yml_verifies_pre_bundle_binary():
    """release.yml must verify dist/launcher/launcher (pre-bundle binary)."""
    content = _release_content()
    assert "dist/launcher/launcher" in content, (
        "release.yml does not verify the pre-bundle binary at dist/launcher/launcher"
    )


def test_release_yml_still_verifies_python_framework():
    """release.yml must still verify Python.framework signature."""
    content = _release_content()
    assert "Python.framework" in content and "codesign" in content, (
        "release.yml no longer verifies Python.framework"
    )
    pattern = re.compile(r'codesign\s+--verify.*Python\.framework')
    assert pattern.search(content), "release.yml does not verify Python.framework"


# ---------------------------------------------------------------------------
# Regression: original bug patterns must be absent
# ---------------------------------------------------------------------------

def test_regression_no_sign_cfbundleexecutable_in_app():
    """Regression: the original BUG-072 trigger line must not be present."""
    content = _dmg_content()
    # The exact offending line from the CI failure
    assert 'codesign --force --sign - "${APP_BUNDLE}/Contents/MacOS/launcher"' not in content, (
        "Regression: BUG-072 codesign --force --sign - line is still present in build_dmg.sh"
    )


def test_regression_no_verify_cfbundleexecutable_in_app():
    """Regression: verifying launcher inside the .app (old pattern) must be absent."""
    content = _dmg_content()
    assert 'codesign --verify "${APP_BUNDLE}/Contents/MacOS/launcher"' not in content, (
        "Regression: old codesign --verify inside .app is still present in build_dmg.sh"
    )


def test_regression_release_yml_old_verify_gone():
    """Regression: old release.yml launcher verify path must be absent."""
    content = _release_content()
    assert "dist/AgentEnvironmentLauncher.app/Contents/MacOS/launcher" not in content, (
        "Regression: old release.yml verification path still present"
    )
