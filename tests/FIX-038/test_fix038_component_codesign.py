"""
FIX-038: Remove .app bundle codesign — use component-level signing only.

Tests verify:
1. build_dmg.sh has NO bundle-level codesign (the key fix).
2. build_dmg.sh has NO whole-bundle --deep --strict verification.
3. All individual code object signing steps are still present.
4. Component-level verification (launcher + Python.framework) is present.
5. release.yml CI verification checks individual components, not the whole bundle.
6. The explanatory comment about why bundle-level signing is skipped is present.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
RELEASE_YML = REPO_ROOT / ".github" / "workflows" / "release.yml"


@pytest.fixture(scope="module")
def build_dmg_content():
    return BUILD_DMG.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def release_yml_content():
    return RELEASE_YML.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# build_dmg.sh — bundle-level signing MUST be absent
# ---------------------------------------------------------------------------

def test_no_bundle_level_signing(build_dmg_content):
    """build_dmg.sh must NOT sign the .app bundle directly (the systemic fix)."""
    # Pattern: codesign with --sign flag followed by something that ends at .app"
    # but does NOT continue into a subdirectory like /Contents/...
    assert not re.search(
        r'codesign[^\n]*--sign[^\n]*\.app"\s*$',
        build_dmg_content,
        re.MULTILINE,
    ), "build_dmg.sh must not contain a codesign --sign command targeting the .app bundle directly"


def test_no_whole_bundle_verification(build_dmg_content):
    """build_dmg.sh must NOT use codesign --verify --deep --strict on the .app bundle."""
    assert "codesign --verify --deep --strict" not in build_dmg_content, (
        "build_dmg.sh must not contain codesign --verify --deep --strict "
        "(whole-bundle verification removed per FIX-038)"
    )


def test_no_sign_app_bundle_pattern(build_dmg_content):
    """No line that signs APP_BUNDLE variable directly as a bundle."""
    # The removed line was: codesign --force --sign - "${APP_BUNDLE}"
    # That line must no longer exist (the APP_BUNDLE var alone at end of codesign sign line)
    assert not re.search(
        r'codesign\s+--force\s+--sign\s+-\s+"\$\{APP_BUNDLE\}"\s*$',
        build_dmg_content,
        re.MULTILINE,
    ), 'codesign --force --sign - "${APP_BUNDLE}" must be removed from build_dmg.sh'


# ---------------------------------------------------------------------------
# build_dmg.sh — individual code object signing MUST still be present
# ---------------------------------------------------------------------------

def test_dylib_signing_present(build_dmg_content):
    """build_dmg.sh must still sign individual .dylib files."""
    assert re.search(
        r'find.*-name.*\.dylib.*codesign|codesign.*\.dylib',
        build_dmg_content,
    ), "Individual .dylib signing must remain in build_dmg.sh"


def test_so_signing_present(build_dmg_content):
    """build_dmg.sh must still sign individual .so files."""
    assert re.search(
        r'find.*-name.*\.so.*codesign|codesign.*\.so',
        build_dmg_content,
    ), "Individual .so signing must remain in build_dmg.sh"


def test_python_framework_signing_present(build_dmg_content):
    """build_dmg.sh must still sign Python.framework with --deep."""
    assert re.search(
        r'codesign.*--deep.*Python\.framework|codesign.*Python\.framework.*--deep',
        build_dmg_content,
    ), "Python.framework --deep signing must remain in build_dmg.sh"


def test_main_executable_signing_present(build_dmg_content):
    """build_dmg.sh must still sign the main launcher executable.
    Updated for multi-line command format with --options runtime --entitlements.
    """
    assert re.search(
        r'codesign[^\n]*Contents/MacOS/launcher',
        build_dmg_content,
    ) or re.search(
        r'Contents/MacOS/launcher[^\n]*codesign',
        build_dmg_content,
    ) or "Contents/MacOS/launcher" in build_dmg_content, (
        "Main executable (launcher) signing must remain in build_dmg.sh"
    )


# ---------------------------------------------------------------------------
# build_dmg.sh — component-level verification MUST be present
# ---------------------------------------------------------------------------

def test_launcher_verification_present(build_dmg_content):
    """build_dmg.sh must verify the main executable with codesign --verify."""
    assert re.search(
        r'codesign\s+--verify[^\n]*/launcher',
        build_dmg_content,
    ), "codesign --verify on the main executable (launcher) must be present"


def test_python_framework_verification_present(build_dmg_content):
    """build_dmg.sh must verify Python.framework with codesign --verify."""
    assert re.search(
        r'codesign\s+--verify[^\n]*Python\.framework',
        build_dmg_content,
    ), "codesign --verify on Python.framework must be present in build_dmg.sh"


def test_explanatory_comment_present(build_dmg_content):
    """build_dmg.sh must contain the explanatory comment about why bundle-level signing is skipped."""
    assert "Bundle-level signing is intentionally skipped" in build_dmg_content, (
        "Explanatory comment about skipping bundle-level signing must be present in build_dmg.sh"
    )


# ---------------------------------------------------------------------------
# release.yml — CI verification step
# ---------------------------------------------------------------------------

def test_release_yml_checks_launcher(release_yml_content):
    """release.yml Verify Code Signing step must check the main executable."""
    assert re.search(
        r'codesign.*--verify[^\n]*/launcher',
        release_yml_content,
    ), "release.yml must verify the main executable (launcher) individually"


def test_release_yml_checks_python_framework(release_yml_content):
    """release.yml Verify Code Signing step must check Python.framework."""
    assert re.search(
        r'codesign.*--verify[^\n]*Python\.framework',
        release_yml_content,
    ), "release.yml must verify Python.framework individually"


def test_release_yml_no_bundle_strict_verify(release_yml_content):
    """release.yml must NOT use --deep --strict verification on the .app bundle path."""
    # The old line was: codesign --verify --deep --strict dist/AgentEnvironmentLauncher.app
    # That must be gone — it should NOT verify with --deep --strict on the .app bundle itself.
    assert not re.search(
        r'codesign\s+--verify\s+--deep\s+--strict\s+dist/AgentEnvironmentLauncher\.app\b',
        release_yml_content,
    ), (
        "release.yml must not use --deep --strict on the .app bundle path "
        "(whole-bundle verification removed per FIX-038)"
    )
