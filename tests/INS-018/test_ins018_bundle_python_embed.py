"""Tests for INS-018: Bundle Python Embeddable Distribution.

Covers:
- src/installer/python-embed/README.md exists and documents Windows/macOS/Linux
- launcher.spec contains the conditional python-embed datas entry
- setup.iss contains the python-embed [Files] entry with Check: PythonEmbedExists
- setup.iss contains the [UninstallDelete] entry for python-embed
- setup.iss contains the PythonEmbedExists() [Code] function
- build_dmg.sh copies python-embed into app bundle when present
- build_appimage.sh copies python-embed into AppDir when present
- release.yml has a CI note comment for python-embed download
"""

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
PYTHON_EMBED_README = REPO_ROOT / "src" / "installer" / "python-embed" / "README.md"
LAUNCHER_SPEC = REPO_ROOT / "launcher.spec"
SETUP_ISS = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
BUILD_APPIMAGE = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
RELEASE_YML = REPO_ROOT / ".github" / "workflows" / "release.yml"


# ---------------------------------------------------------------------------
# README tests
# ---------------------------------------------------------------------------

def test_python_embed_readme_exists():
    assert PYTHON_EMBED_README.exists(), "src/installer/python-embed/README.md must exist"


def test_python_embed_readme_mentions_windows_download():
    text = PYTHON_EMBED_README.read_text(encoding="utf-8")
    assert "python.org/ftp/python" in text, "README must reference the python.org download URL"


def test_python_embed_readme_mentions_macos():
    text = PYTHON_EMBED_README.read_text(encoding="utf-8")
    assert "macOS" in text or "macos" in text.lower(), "README must document macOS instructions"


def test_python_embed_readme_mentions_linux():
    text = PYTHON_EMBED_README.read_text(encoding="utf-8")
    assert "Linux" in text or "linux" in text.lower(), "README must document Linux instructions"


def test_python_embed_readme_mentions_expected_layout():
    text = PYTHON_EMBED_README.read_text(encoding="utf-8")
    assert "python.exe" in text, "README must show python.exe in the expected layout"


def test_python_embed_readme_mentions_security():
    text = PYTHON_EMBED_README.read_text(encoding="utf-8")
    assert "SHA256" in text or "checksum" in text.lower(), (
        "README must mention checksum/SHA256 verification for security"
    )


# ---------------------------------------------------------------------------
# launcher.spec tests
# ---------------------------------------------------------------------------

def test_launcher_spec_imports_os():
    text = LAUNCHER_SPEC.read_text(encoding="utf-8")
    assert "import os" in text


def test_launcher_spec_has_python_embed_dir_variable():
    text = LAUNCHER_SPEC.read_text(encoding="utf-8")
    assert "_PYTHON_EMBED_DIR" in text, (
        "launcher.spec must define _PYTHON_EMBED_DIR for the python-embed path"
    )


def test_launcher_spec_checks_python_exe_before_adding():
    text = LAUNCHER_SPEC.read_text(encoding="utf-8")
    assert "python.exe" in text, (
        "launcher.spec must guard the python-embed entry on python.exe presence"
    )


def test_launcher_spec_python_embed_bundle_variable():
    text = LAUNCHER_SPEC.read_text(encoding="utf-8")
    assert "_python_embed_bundle" in text, (
        "launcher.spec must collect optional datas in _python_embed_bundle"
    )


def test_launcher_spec_python_embed_destination():
    text = LAUNCHER_SPEC.read_text(encoding="utf-8")
    assert "'python-embed'" in text, (
        "launcher.spec must set 'python-embed' as the PyInstaller destination"
    )


def test_launcher_spec_merges_datas():
    text = LAUNCHER_SPEC.read_text(encoding="utf-8")
    assert "_python_embed_bundle" in text and "] + _python_embed_bundle" in text, (
        "launcher.spec must merge _python_embed_bundle into the datas list"
    )


def test_launcher_spec_conditional_does_not_break_empty_case():
    """Verify the conditional block returns an empty list when python.exe absent."""
    text = LAUNCHER_SPEC.read_text(encoding="utf-8")
    # Should initialise to [] before the conditional
    assert "_python_embed_bundle = []" in text


# ---------------------------------------------------------------------------
# setup.iss tests
# ---------------------------------------------------------------------------

def test_setup_iss_has_python_embed_files_entry():
    text = SETUP_ISS.read_text(encoding="utf-8")
    assert "python-embed" in text.lower(), (
        "setup.iss must reference python-embed in [Files]"
    )


def test_setup_iss_python_embed_source_path():
    text = SETUP_ISS.read_text(encoding="utf-8")
    assert r"..\python-embed\*" in text, (
        "setup.iss [Files] source must point to ..\\python-embed\\*"
    )


def test_setup_iss_python_embed_dest_dir():
    text = SETUP_ISS.read_text(encoding="utf-8")
    assert '"{app}\\python-embed"' in text or '"{app}\\\\python-embed"' in text or (
        'python-embed"' in text and "{app}" in text
    ), "setup.iss must install python-embed to {app}\\python-embed"


def test_setup_iss_python_embed_skipifsourcedoesntexist():
    """FIX-055: python-embed [Files] entry must use skipifsourcedoesntexist flag.

    The old runtime Check: PythonEmbedExists function has been replaced with the
    compile-time skipifsourcedoesntexist Inno Setup flag.  This flag silently skips
    the Files entry when the source directory does not exist at compile time, allowing
    dev builds to compile without the python-embed directory present.
    """
    text = SETUP_ISS.read_text(encoding="utf-8")
    assert "skipifsourcedoesntexist" in text, (
        "setup.iss python-embed [Files] entry must use skipifsourcedoesntexist flag "
        "(FIX-055 replaced PythonEmbedExists runtime check with this compile-time flag)"
    )


def test_setup_iss_has_code_section():
    text = SETUP_ISS.read_text(encoding="utf-8")
    assert "[Code]" in text, "setup.iss must have a [Code] section for PythonEmbedExists"


def test_setup_iss_python_embed_no_check_parameter():
    """FIX-055: python-embed [Files] line must NOT use a Check: parameter.

    The old PythonEmbedExists runtime function required a Check: clause on the
    [Files] entry.  FIX-055 removes this in favour of the compile-time
    skipifsourcedoesntexist flag, so no Check: parameter should appear on the
    python-embed Files line.
    """
    text = SETUP_ISS.read_text(encoding="utf-8")
    for line in text.splitlines():
        if "python-embed" in line.lower() and "Source:" in line:
            assert "Check:" not in line, (
                "python-embed [Files] entry must not use Check: — "
                "FIX-055 replaced PythonEmbedExists with skipifsourcedoesntexist"
            )
            break


def test_setup_iss_uninstall_delete_python_embed():
    text = SETUP_ISS.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_uninstall = False
    has_python_embed = False
    for line in lines:
        stripped = line.strip()
        if stripped == "[UninstallDelete]":
            in_uninstall = True
        elif stripped.startswith("[") and stripped != "[UninstallDelete]":
            in_uninstall = False
        if in_uninstall and "python-embed" in stripped.lower():
            has_python_embed = True
    assert has_python_embed, (
        "setup.iss [UninstallDelete] must include an entry for python-embed"
    )


def test_setup_iss_recursesubdirs_flag_on_python_embed():
    text = SETUP_ISS.read_text(encoding="utf-8")
    # Find the python-embed Files line and check it has recursesubdirs
    for line in text.splitlines():
        if "python-embed" in line.lower() and "Source:" in line:
            assert "recursesubdirs" in line.lower(), (
                "python-embed [Files] entry must have recursesubdirs flag"
            )
            break


# ---------------------------------------------------------------------------
# build_dmg.sh tests
# ---------------------------------------------------------------------------

def test_build_dmg_references_python_embed():
    text = BUILD_DMG.read_text(encoding="utf-8")
    assert "python-embed" in text.lower(), (
        "build_dmg.sh must reference python-embed"
    )


def test_build_dmg_checks_for_python_embed_presence():
    text = BUILD_DMG.read_text(encoding="utf-8")
    assert "PYTHON_EMBED_SRC" in text, (
        "build_dmg.sh must define PYTHON_EMBED_SRC variable"
    )


def test_build_dmg_copies_to_resources():
    text = BUILD_DMG.read_text(encoding="utf-8")
    assert "Resources/python-embed" in text, (
        "build_dmg.sh must copy python-embed into Contents/Resources/python-embed"
    )


def test_build_dmg_python_embed_conditional():
    text = BUILD_DMG.read_text(encoding="utf-8")
    # Must have an if-block guarding the copy
    assert re.search(r'if \[.*python', text), (
        "build_dmg.sh must guard python-embed copy with a conditional"
    )


def test_build_dmg_skips_gracefully_when_not_populated():
    text = BUILD_DMG.read_text(encoding="utf-8")
    assert "skipping" in text.lower(), (
        "build_dmg.sh must log a skip message when python-embed is not present"
    )


# ---------------------------------------------------------------------------
# build_appimage.sh tests
# ---------------------------------------------------------------------------

def test_build_appimage_references_python_embed():
    text = BUILD_APPIMAGE.read_text(encoding="utf-8")
    assert "python-embed" in text.lower(), (
        "build_appimage.sh must reference python-embed"
    )


def test_build_appimage_checks_for_python_embed_presence():
    text = BUILD_APPIMAGE.read_text(encoding="utf-8")
    assert "PYTHON_EMBED_SRC" in text, (
        "build_appimage.sh must define PYTHON_EMBED_SRC variable"
    )


def test_build_appimage_copies_into_appdir():
    text = BUILD_APPIMAGE.read_text(encoding="utf-8")
    assert "python-embed" in text and "AppDir" in text, (
        "build_appimage.sh must copy python-embed into the AppDir"
    )


def test_build_appimage_python_embed_conditional():
    text = BUILD_APPIMAGE.read_text(encoding="utf-8")
    assert re.search(r'if \[.*python', text), (
        "build_appimage.sh must guard python-embed copy with a conditional"
    )


def test_build_appimage_skips_gracefully_when_not_populated():
    text = BUILD_APPIMAGE.read_text(encoding="utf-8")
    assert "skipping" in text.lower(), (
        "build_appimage.sh must log a skip message when python-embed is not present"
    )


# ---------------------------------------------------------------------------
# release.yml tests
# ---------------------------------------------------------------------------

def test_release_yml_has_python_embed_ci_note():
    text = RELEASE_YML.read_text(encoding="utf-8")
    assert "python-embed" in text.lower(), (
        "release.yml must contain a CI note about downloading the python-embed package"
    )


def test_release_yml_ci_note_is_commented_out():
    """The download step must be commented for now (not yet active in CI)."""
    text = RELEASE_YML.read_text(encoding="utf-8")
    # The INS-018 download block should appear as a YAML comment block
    assert "# INS-018" in text or "# - name: Download Python embeddable" in text, (
        "release.yml INS-018 CI note must be present as a comment"
    )


def test_release_yml_ci_note_references_python_org():
    text = RELEASE_YML.read_text(encoding="utf-8")
    assert "python.org/ftp/python" in text, (
        "release.yml CI note must reference the python.org FTP download URL"
    )
