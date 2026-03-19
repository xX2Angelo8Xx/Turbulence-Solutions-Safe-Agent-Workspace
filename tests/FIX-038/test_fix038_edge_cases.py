"""
FIX-038 Edge-Case Tests — Component-level codesign only.

Tests verify:
1. Signing flow order: .dylib BEFORE .so BEFORE Python.framework BEFORE launcher
2. NO codesign command targets the *.app path directly (no bundle signing)
3. release.yml uses multi-line (|) YAML for the Verify Code Signing run step
4. Explanatory comment exists in build_dmg.sh about why bundle signing is skipped
5. .dist-info removal step is still present (FIX-037 regression guard)
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
# Edge Case 1: Signing order — bottom-up (dylib → so → framework → launcher)
# ---------------------------------------------------------------------------

def test_signing_order_dylib_before_so(build_dmg_content):
    """Signing order: .dylib files must be signed before .so files."""
    dylib_match = re.search(r'find[^\n]*\.dylib[^\n]*codesign|codesign[^\n]*\.dylib', build_dmg_content)
    so_match = re.search(r'find[^\n]*\.so[^\n]*codesign|codesign[^\n]*\.so', build_dmg_content)
    assert dylib_match is not None, ".dylib signing step not found"
    assert so_match is not None, ".so signing step not found"
    assert dylib_match.start() < so_match.start(), (
        "Signing order broken: .dylib must be signed before .so"
    )


def test_signing_order_so_before_framework(build_dmg_content):
    """Signing order: .so files must be signed before Python.framework."""
    so_match = re.search(r'find[^\n]*\.so[^\n]*codesign|codesign[^\n]*\.so', build_dmg_content)
    framework_match = re.search(
        r'codesign.*--deep.*--force.*--sign.*Python\.framework'
        r'|codesign.*--force.*--sign.*Python\.framework',
        build_dmg_content,
    )
    assert so_match is not None, ".so signing step not found"
    assert framework_match is not None, "Python.framework signing step not found"
    assert so_match.start() < framework_match.start(), (
        "Signing order broken: .so must be signed before Python.framework"
    )


def test_signing_order_framework_before_launcher(build_dmg_content):
    """Signing order: Python.framework must be signed before the main launcher executable."""
    framework_match = re.search(
        r'codesign.*Python\.framework',
        build_dmg_content,
    )
    launcher_sign_match = re.search(
        r'codesign\s+--force\s+--sign\s+-[^\n]*/launcher',
        build_dmg_content,
    )
    assert framework_match is not None, "Python.framework signing step not found"
    assert launcher_sign_match is not None, "Launcher signing step not found"
    assert framework_match.start() < launcher_sign_match.start(), (
        "Signing order broken: Python.framework must be signed before the main executable"
    )


# ---------------------------------------------------------------------------
# Edge Case 2: No codesign command targets the .app bundle path directly
# ---------------------------------------------------------------------------

def _get_codesign_sign_lines(content: str) -> list[str]:
    """Return all lines containing 'codesign' and '--sign'."""
    return [
        line.strip()
        for line in content.splitlines()
        if "codesign" in line and "--sign" in line
    ]


def test_no_codesign_targets_app_bundle_directly(build_dmg_content):
    """No codesign --sign command may target the .app bundle path directly.

    Any line with codesign + --sign that ends (ignoring whitespace/comments) with
    .app" (i.e., the APP_BUNDLE variable or a literal .app path as the final
    argument) is forbidden.
    """
    for line in _get_codesign_sign_lines(build_dmg_content):
        # Match: the .app path (with optional trailing quote/whitespace) at end of line
        assert not re.search(r'\.app["\s]*$', line), (
            f"codesign --sign must not target a .app bundle directly, but found: {line!r}"
        )


def test_no_codesign_sign_app_bundle_variable(build_dmg_content):
    """The specific pattern 'codesign ... --sign - "${APP_BUNDLE}"' must not exist."""
    assert not re.search(
        r'codesign[^\n]*--sign[^\n]*"\$\{APP_BUNDLE\}"',
        build_dmg_content,
        re.MULTILINE,
    ), 'No codesign line should reference "${APP_BUNDLE}" with --sign (bundle-level signing removed)'


def test_app_bundle_only_used_as_prefix_in_codesign(build_dmg_content):
    """When APP_BUNDLE appears in a codesign --sign line, it must be a path prefix (into /Contents/)."""
    for line in _get_codesign_sign_lines(build_dmg_content):
        if "${APP_BUNDLE}" in line:
            # It's acceptable only if the .app var is followed by /Contents/ subpath
            assert "/Contents/" in line, (
                f"APP_BUNDLE in codesign sign line must go into /Contents/ subpath, not the bundle root: {line!r}"
            )


# ---------------------------------------------------------------------------
# Edge Case 3: release.yml uses multi-line YAML (|) for Verify Code Signing
# ---------------------------------------------------------------------------

def test_release_yml_verify_step_uses_multiline_yaml(release_yml_content):
    """The 'Verify Code Signing' run step in release.yml must use YAML literal block scalar (|)."""
    # Find the Verify Code Signing step and confirm it uses run: |
    assert re.search(
        r'Verify Code Signing.*\n\s+run:\s*\|',
        release_yml_content,
        re.DOTALL,
    ) or re.search(
        r'name:\s*Verify Code Signing\b',
        release_yml_content,
    ), "'Verify Code Signing' step must exist in release.yml"

    # Locate the step and verify the run: line uses | for multiline
    step_match = re.search(
        r'name:\s*Verify Code Signing.*?run:\s*(\||\>)',
        release_yml_content,
        re.DOTALL,
    )
    assert step_match is not None, (
        "'Verify Code Signing' step in release.yml must have a 'run:' block"
    )
    assert step_match.group(1) == "|", (
        "release.yml 'Verify Code Signing' run: must use | (literal block scalar) for multi-line commands"
    )


def test_release_yml_verify_step_has_two_codesign_calls(release_yml_content):
    """The Verify Code Signing step must contain exactly two codesign --verify calls."""
    # Extract just the Verify Code Signing step block
    step_match = re.search(
        r'name:\s*Verify Code Signing(.*?)(?=\n\s{4,6}-\s*name:|\Z)',
        release_yml_content,
        re.DOTALL,
    )
    assert step_match is not None, "'Verify Code Signing' step not found in release.yml"
    step_block = step_match.group(0)
    codesign_calls = re.findall(r'codesign\s+--verify', step_block)
    assert len(codesign_calls) >= 2, (
        f"Expected at least 2 'codesign --verify' calls in Verify Code Signing step, found {len(codesign_calls)}"
    )


# ---------------------------------------------------------------------------
# Edge Case 4: Explanatory comment about WHY bundle signing is skipped
# ---------------------------------------------------------------------------

def test_explanatory_comment_mentions_pyinstaller(build_dmg_content):
    """The comment explaining why bundle-level signing is skipped must mention PyInstaller."""
    # Find the region around the comment
    comment_region = re.search(
        r'(Bundle-level signing is intentionally skipped[^\n]*\n(?:#[^\n]*\n){0,10})',
        build_dmg_content,
    )
    assert comment_region is not None, "Explanatory comment about bundle signing not found"
    comment_text = comment_region.group(0)
    assert "PyInstaller" in comment_text, (
        "Explanatory comment must mention PyInstaller as the root cause"
    )


def test_explanatory_comment_mentions_non_code_files(build_dmg_content):
    """The explanatory comment must mention non-code files as the reason for skipping bundle signing."""
    # The comment should explain WHY (non-code files, images, etc.)
    comment_region = re.search(
        r'NOTE:.*?Bundle-level signing is intentionally skipped.*?(?=echo)',
        build_dmg_content,
        re.DOTALL,
    )
    if comment_region is None:
        # Try alternate layout — comment before the 'echo Verifying' line
        comment_region = re.search(
            r'#[^\n]*non-code[^\n]*|#[^\n]*image[^\n]*|#[^\n]*data file[^\n]*'
            r'|#[^\n]*\.pyc[^\n]*|#[^\n]*non.code[^\n]*',
            build_dmg_content,
        )
    assert comment_region is not None, (
        "Explanatory comment must mention non-code files (images, .pyc, etc.) as reason bundle signing is skipped"
    )


# ---------------------------------------------------------------------------
# Edge Case 5: .dist-info removal still present (FIX-037 regression guard)
# ---------------------------------------------------------------------------

def test_dist_info_removal_present(build_dmg_content):
    """FIX-037 regression: .dist-info directory removal must still be in build_dmg.sh."""
    assert ".dist-info" in build_dmg_content, (
        "Regression (FIX-037): .dist-info removal step must still be present in build_dmg.sh"
    )


def test_dist_info_removal_uses_find_and_rm(build_dmg_content):
    """FIX-037 regression: .dist-info removal must use 'find ... -name *.dist-info ... rm -rf'."""
    assert re.search(
        r'find[^\n]*\.dist-info[^\n]*rm|rm[^\n]*\.dist-info',
        build_dmg_content,
    ), (
        "Regression (FIX-037): .dist-info removal must use find + rm -rf pattern"
    )


def test_dist_info_removal_targets_internal_dir(build_dmg_content):
    """FIX-037 regression: .dist-info removal must target the _internal/ directory inside the bundle."""
    assert re.search(
        r'find[^\n]*_internal[^\n]*\.dist-info',
        build_dmg_content,
    ), (
        "Regression (FIX-037): .dist-info removal must target Contents/MacOS/_internal directory"
    )
