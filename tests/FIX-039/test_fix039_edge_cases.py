"""
FIX-039 Edge-Case Tests — Skip launcher re-sign inside .app; verify pre-bundle binary.

Tester-added edge cases covering:
1. No codesign --sign line anywhere targets Contents/MacOS/launcher.
2. The explanatory comment about CFBundleExecutable / bundle-validation is present.
3. The DIST_DIR variable form is used in the verify command (not a hardcoded 'dist/').
4. The pre-bundle verify step comes BEFORE the hdiutil DMG creation step.
5. release.yml Verify Code Signing step does NOT reference any '.app' path.
6. release.yml Verify Code Signing step uses the pre-bundle path for the main binary.
7. No `codesign --strict` flag is added accidentally (only --verify without flagging).
8. build_dmg.sh has the NOTE comment about PyInstaller ad-hoc signature.
9. Signing of .dylib/.so still scoped to _internal/ (not leaking outside bundle).
10. The dist/launcher/launcher verify precedes Python.framework verify in both files.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
RELEASE_YML = REPO_ROOT / ".github" / "workflows" / "release.yml"


def _dmg() -> str:
    return BUILD_DMG.read_text(encoding="utf-8")


def _yml() -> str:
    return RELEASE_YML.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Edge 1: No codesign --sign targeting Contents/MacOS/launcher anywhere
# ---------------------------------------------------------------------------

def test_no_codesign_sign_any_form_on_bundle_launcher():
    """No codesign --sign line of any form should target Contents/MacOS/launcher."""
    content = _dmg()
    # Covers both --sign - and --sign <cert> forms
    lines_with_sign = [
        l for l in content.splitlines()
        if "codesign" in l and "--sign" in l and "Contents/MacOS/launcher" in l
    ]
    assert lines_with_sign == [], (
        f"Found codesign --sign targeting Contents/MacOS/launcher: {lines_with_sign}"
    )


# ---------------------------------------------------------------------------
# Edge 2: Explanatory comment about CFBundleExecutable present
# ---------------------------------------------------------------------------

def test_build_dmg_has_cfbundleexecutable_comment():
    """build_dmg.sh must contain a comment explaining why launcher is NOT re-signed."""
    content = _dmg()
    assert "CFBundleExecutable" in content, (
        "build_dmg.sh is missing the explanatory comment about CFBundleExecutable "
        "/ bundle-validation triggering"
    )


# ---------------------------------------------------------------------------
# Edge 3: DIST_DIR variable form used in the verify command
# ---------------------------------------------------------------------------

def test_build_dmg_verify_uses_dist_dir_variable():
    """The pre-bundle verify should use ${DIST_DIR} variable, not hardcoded 'dist/'."""
    content = _dmg()
    # Pattern: codesign --verify followed by "${DIST_DIR}/launcher/launcher"
    pattern = re.compile(r'codesign\s+--verify\s+"\$\{DIST_DIR\}/launcher/launcher"')
    assert pattern.search(content), (
        "build_dmg.sh verify of pre-bundle binary should use "
        '"${DIST_DIR}/launcher/launcher" (DIST_DIR variable form)'
    )


# ---------------------------------------------------------------------------
# Edge 4: Pre-bundle verify step appears BEFORE hdiutil DMG creation
# ---------------------------------------------------------------------------

def test_build_dmg_verify_before_hdiutil():
    """Pre-bundle binary verify must appear before the hdiutil DMG creation step."""
    content = _dmg()
    verify_match = re.search(r'codesign\s+--verify\s+["\$\{]*(?:DIST_DIR\}.*|dist/)launcher', content)
    hdiutil_match = re.search(r'hdiutil\s+create', content)
    assert verify_match is not None, "Pre-bundle verify step not found"
    assert hdiutil_match is not None, "hdiutil create step not found"
    assert verify_match.start() < hdiutil_match.start(), (
        "Pre-bundle verify must come BEFORE hdiutil DMG creation"
    )


# ---------------------------------------------------------------------------
# Edge 5: release.yml Verify Code Signing step contains no .app reference
# ---------------------------------------------------------------------------

def test_release_yml_verify_step_no_app_path():
    """release.yml Verify Code Signing step must not reference the launcher inside the .app.

    Referencing Contents/MacOS/_internal/Python.framework is legitimate (it is a standalone
    code object). Referencing Contents/MacOS/launcher (the CFBundleExecutable) is forbidden
    because it triggers macOS bundle validation.
    """
    content = _yml()
    # Find the Verify Code Signing step block
    verify_step_match = re.search(
        r'- name: Verify Code Signing\s+run:\s*\|(.+?)(?=\n\s+-\s+(?:name|uses)|\Z)',
        content,
        re.DOTALL,
    )
    assert verify_step_match, "Verify Code Signing step not found in release.yml"
    step_body = verify_step_match.group(1)
    # Must NOT reference Contents/MacOS/launcher (the CFBundleExecutable — triggers bundle validation)
    # (Contents/MacOS/_internal/Python.framework is OK — it's a code object inside _internal/)
    # Match 'Contents/MacOS/launcher' but not 'Contents/MacOS/launcher' followed by '/_internal'
    forbidden = re.findall(r'Contents/MacOS/launcher(?!/_internal|/[^/]*/_internal)', step_body)
    assert forbidden == [], (
        f"release.yml Verify Code Signing step references Contents/MacOS/launcher "
        f"(CFBundleExecutable path): {forbidden}"
    )


# ---------------------------------------------------------------------------
# Edge 6: release.yml Verify Code Signing step uses pre-bundle launcher path
# ---------------------------------------------------------------------------

def test_release_yml_verify_step_uses_pre_bundle_launcher():
    """release.yml Verify Code Signing must reference dist/launcher/launcher."""
    content = _yml()
    verify_step_match = re.search(
        r'- name: Verify Code Signing\s+run:\s*\|(.+?)(?=\n\s+-\s+(?:name|uses)|\Z)',
        content,
        re.DOTALL,
    )
    assert verify_step_match, "Verify Code Signing step not found in release.yml"
    step_body = verify_step_match.group(1)
    assert "dist/launcher/launcher" in step_body, (
        "release.yml Verify Code Signing step must reference dist/launcher/launcher"
    )


# ---------------------------------------------------------------------------
# Edge 7: No --strict flag added to the pre-bundle verify
# ---------------------------------------------------------------------------

def test_build_dmg_verify_pre_bundle_no_strict():
    """The pre-bundle binary verify in build_dmg.sh must NOT use --strict.

    --strict triggers full bundle validation which would fail on the non-code
    files inside the .app's _internal/ directory.
    """
    content = _dmg()
    # Find the line with codesign --verify on launcher/launcher
    for line in content.splitlines():
        if "codesign" in line and "--verify" in line and "launcher/launcher" in line:
            assert "--strict" not in line, (
                f"Pre-bundle verify must not use --strict: {line!r}"
            )


# ---------------------------------------------------------------------------
# Edge 8: NOTE comment about PyInstaller ad-hoc signature present
# ---------------------------------------------------------------------------

def test_build_dmg_has_pyinstaller_presign_note():
    """build_dmg.sh must contain a note about PyInstaller's ad-hoc signing."""
    content = _dmg()
    # The comment should mention PyInstaller signs the binary
    assert "PyInstaller" in content and (
        "ad-hoc" in content or "Re-signing" in content or "already" in content
    ), (
        "build_dmg.sh is missing a NOTE comment explaining that "
        "PyInstaller already signs the binary"
    )


# ---------------------------------------------------------------------------
# Edge 9: .dylib/.so signing scoped to _internal/ (not leaking to MacOS root)
# ---------------------------------------------------------------------------

def test_build_dmg_dylib_signing_scoped_to_internal():
    """The find command for .dylib signing must target _internal/, not the whole bundle."""
    content = _dmg()
    # The signing find command should contain _internal
    dylib_sign_match = re.search(
        r'find[^\n]*\.dylib[^\n]*codesign|find\s+"[^"]*"[^\n]*\.dylib',
        content,
    )
    assert dylib_sign_match, ".dylib signing find command not found"
    # The found region should reference _internal
    surrounding = content[
        max(0, dylib_sign_match.start() - 100):dylib_sign_match.end() + 200
    ]
    assert "_internal" in surrounding, (
        ".dylib signing should be scoped to the _internal/ subdirectory"
    )


def test_build_dmg_so_signing_scoped_to_internal():
    """The find command for .so signing must target _internal/, not the whole bundle."""
    content = _dmg()
    so_sign_match = re.search(
        r'find[^\n]*\.so[^\n]*codesign|find\s+"[^"]*"[^\n]*\.so',
        content,
    )
    assert so_sign_match, ".so signing find command not found"
    surrounding = content[
        max(0, so_sign_match.start() - 100):so_sign_match.end() + 200
    ]
    assert "_internal" in surrounding, (
        ".so signing should be scoped to the _internal/ subdirectory"
    )


# ---------------------------------------------------------------------------
# Edge 10: Pre-bundle verify precedes Python.framework verify
# ---------------------------------------------------------------------------

def test_build_dmg_launcher_verify_before_framework_verify():
    """Pre-bundle launcher verify must come BEFORE Python.framework verify."""
    content = _dmg()
    launcher_verify = re.search(
        r'codesign\s+--verify\s+["\$\{]*(?:DIST_DIR\}/|dist/)launcher/launcher',
        content,
    )
    framework_verify = re.search(
        r'codesign\s+--verify[^\n]*Python\.framework',
        content,
    )
    assert launcher_verify, "Pre-bundle launcher verify step not found"
    assert framework_verify, "Python.framework verify step not found"
    assert launcher_verify.start() < framework_verify.start(), (
        "Pre-bundle launcher verify must appear before Python.framework verify"
    )
