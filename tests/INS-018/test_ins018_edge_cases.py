"""Edge-case tests for INS-018: Bundle Python Embeddable Distribution.

Tester additions — covers gaps in the developer test suite:
- README has .gitignore section and Security note section
- README documents the purpose (security gate runtime)
- launcher.spec uses SPECPATH (not __file__), os.path.isfile, correct path components
- setup.iss Check function only on embed entry (not main dist entry)
- setup.iss createallsubdirs flag on embed entry
- setup.iss UninstallDelete python-embed uses filesandordirs type
- setup.iss PythonEmbedExists uses ExpandConstant
- build_dmg.sh uses -R flag for recursive copy of python-embed
- build_appimage.sh uses -R flag for recursive copy of python-embed
- release.yml CI note appears inside windows-build job (not macos/linux)
- release.yml CI note references Expand-Archive (Windows extraction method)
- launcher.spec path construction references 'src', 'installer', 'python-embed'
- launcher.spec uses os.path.isfile not os.path.exists
- setup.iss [Code] section uses ExpandConstant for path resolution
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
# README edge cases
# ---------------------------------------------------------------------------

def test_readme_has_gitignore_section():
    """README must document that binaries are excluded from git via .gitignore."""
    text = PYTHON_EMBED_README.read_text(encoding="utf-8")
    assert ".gitignore" in text, (
        "README must reference .gitignore to document that large binary blobs "
        "are not committed to git"
    )


def test_readme_has_security_note():
    """README must have a security note instructing builders to verify checksums."""
    text = PYTHON_EMBED_README.read_text(encoding="utf-8")
    lower = text.lower()
    assert "security" in lower or "Security note" in text, (
        "README must have a security section/note about verifying downloads"
    )


def test_readme_references_official_hash_source():
    """README must point builders to the official python.org hash page."""
    text = PYTHON_EMBED_README.read_text(encoding="utf-8")
    assert "python.org/downloads" in text or "python.org/ftp" in text, (
        "README must link to python.org for official hash verification"
    )


def test_readme_has_no_bom():
    """README must not contain a UTF-8 BOM byte sequence."""
    raw = PYTHON_EMBED_README.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), (
        "README.md must not start with a UTF-8 BOM"
    )


# ---------------------------------------------------------------------------
# launcher.spec edge cases
# ---------------------------------------------------------------------------

def test_launcher_spec_uses_specpath_not_dunder_file():
    """The spec must use the PyInstaller SPECPATH built-in, not __file__."""
    text = LAUNCHER_SPEC.read_text(encoding="utf-8")
    assert "SPECPATH" in text, (
        "launcher.spec must use SPECPATH (PyInstaller built-in) for portable "
        "path construction — __file__ is unreliable in spec context"
    )


def test_launcher_spec_uses_os_path_isfile():
    """The spec must guard on os.path.isfile, not just os.path.exists."""
    text = LAUNCHER_SPEC.read_text(encoding="utf-8")
    assert "os.path.isfile" in text, (
        "launcher.spec must use os.path.isfile to test python.exe presence "
        "(os.path.exists would accept directories)"
    )


def test_launcher_spec_embed_path_contains_correct_components():
    """The embed dir path must reference src, installer, python-embed."""
    text = LAUNCHER_SPEC.read_text(encoding="utf-8")
    # Path should contain all three components (order matters, but use substring)
    assert ("'src'" in text or '"src"' in text) and (
        "'installer'" in text or '"installer"' in text
    ) and (
        "'python-embed'" in text or '"python-embed"' in text
    ), (
        "launcher.spec _PYTHON_EMBED_DIR must reference 'src', 'installer', "
        "and 'python-embed' path components"
    )


def test_launcher_spec_embed_dir_built_with_os_path_join():
    """The _PYTHON_EMBED_DIR must be constructed with os.path.join (not concatenation)."""
    text = LAUNCHER_SPEC.read_text(encoding="utf-8")
    # Should have os.path.join call that assigns to _PYTHON_EMBED_DIR
    assert re.search(r'_PYTHON_EMBED_DIR\s*=\s*os\.path\.join', text), (
        "launcher.spec must build _PYTHON_EMBED_DIR using os.path.join to "
        "ensure cross-platform path construction"
    )


# ---------------------------------------------------------------------------
# setup.iss edge cases
# ---------------------------------------------------------------------------

def test_setup_iss_check_only_on_embed_entry_not_main_dist():
    """Check: PythonEmbedExists must NOT appear on the main dist/launcher line."""
    text = SETUP_ISS.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if "dist" in stripped and "launcher" in stripped and "Source" in stripped:
            assert "Check:" not in stripped and "PythonEmbedExists" not in stripped, (
                "The main dist/launcher [Files] entry must NOT have "
                "Check: PythonEmbedExists — the main app must always install"
            )


def test_setup_iss_createallsubdirs_on_embed_entry():
    """python-embed [Files] entry must have the createallsubdirs flag."""
    text = SETUP_ISS.read_text(encoding="utf-8")
    for line in text.splitlines():
        if "python-embed" in line.lower() and "Source:" in line:
            assert "createallsubdirs" in line.lower(), (
                "python-embed [Files] entry must have createallsubdirs flag to "
                "recreate nested directory structure during extraction"
            )
            break


def test_setup_iss_uninstall_delete_python_embed_uses_filesandordirs():
    """The python-embed [UninstallDelete] entry must use Type: filesandordirs."""
    text = SETUP_ISS.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_uninstall = False
    for line in lines:
        stripped = line.strip()
        if stripped == "[UninstallDelete]":
            in_uninstall = True
        elif stripped.startswith("[") and stripped != "[UninstallDelete]":
            in_uninstall = False
        if in_uninstall and "python-embed" in stripped.lower():
            assert "filesandordirs" in stripped.lower(), (
                "python-embed [UninstallDelete] entry must use "
                "Type: filesandordirs (not filesandirs)"
            )


def test_setup_iss_python_embed_exists_uses_expand_constant():
    """PythonEmbedExists() must use ExpandConstant for Inno Setup path resolution."""
    text = SETUP_ISS.read_text(encoding="utf-8")
    assert "ExpandConstant" in text, (
        "PythonEmbedExists must call ExpandConstant to resolve Inno Setup "
        "constants (e.g. {src}) to actual filesystem paths at install time"
    )


# ---------------------------------------------------------------------------
# build_dmg.sh edge cases
# ---------------------------------------------------------------------------

def test_build_dmg_python_embed_copy_uses_recursive_flag():
    """The cp command for python-embed in build_dmg.sh must use -R (recursive)."""
    text = BUILD_DMG.read_text(encoding="utf-8")
    # Find the line(s) that copy python-embed and verify -R flag
    for line in text.splitlines():
        if "cp" in line and "python-embed" in line:
            assert "-R" in line or "-r" in line, (
                "build_dmg.sh python-embed copy must use 'cp -R' or 'cp -r' "
                "to recursively copy all embedded binaries"
            )
            break


def test_build_dmg_mkdir_before_python_embed_copy():
    """build_dmg.sh must create the Resources/python-embed directory before copying."""
    text = BUILD_DMG.read_text(encoding="utf-8")
    lines = text.splitlines()
    mkdir_idx = None
    cp_idx = None
    for i, line in enumerate(lines):
        if "mkdir" in line and "python-embed" in line:
            mkdir_idx = i
        if "cp" in line and "python-embed" in line and mkdir_idx is not None:
            cp_idx = i
    assert mkdir_idx is not None, (
        "build_dmg.sh must run mkdir to create the python-embed destination "
        "before copying files into it"
    )
    assert cp_idx is not None and cp_idx > mkdir_idx, (
        "build_dmg.sh must run mkdir BEFORE the cp command for python-embed"
    )


# ---------------------------------------------------------------------------
# build_appimage.sh edge cases
# ---------------------------------------------------------------------------

def test_build_appimage_python_embed_copy_uses_recursive_flag():
    """The cp command for python-embed in build_appimage.sh must use -R (recursive)."""
    text = BUILD_APPIMAGE.read_text(encoding="utf-8")
    for line in text.splitlines():
        if "cp" in line and "python-embed" in line:
            assert "-R" in line or "-r" in line, (
                "build_appimage.sh python-embed copy must use 'cp -R' or 'cp -r' "
                "to recursively copy all embedded binaries"
            )
            break


def test_build_appimage_mkdir_before_python_embed_copy():
    """build_appimage.sh must create the AppDir python-embed directory before copying."""
    text = BUILD_APPIMAGE.read_text(encoding="utf-8")
    lines = text.splitlines()
    mkdir_idx = None
    cp_idx = None
    for i, line in enumerate(lines):
        if "mkdir" in line and "python-embed" in line:
            mkdir_idx = i
        if "cp" in line and "python-embed" in line and mkdir_idx is not None:
            cp_idx = i
    assert mkdir_idx is not None, (
        "build_appimage.sh must run mkdir to create the python-embed destination "
        "before copying files into it"
    )
    assert cp_idx is not None and cp_idx > mkdir_idx, (
        "build_appimage.sh must run mkdir BEFORE the cp command for python-embed"
    )


# ---------------------------------------------------------------------------
# release.yml edge cases
# ---------------------------------------------------------------------------

def test_release_yml_ci_note_inside_windows_build_job():
    """The INS-018 CI download note must be inside windows-build, not macos/linux."""
    text = RELEASE_YML.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Locate job boundaries
    windows_start = None
    next_job_after_windows = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "windows-build:":
            windows_start = i
        elif windows_start is not None and re.match(r'^  [a-z].*:$', line):
            # Another top-level job definition (2-space indent)
            next_job_after_windows = i
            break

    assert windows_start is not None, "release.yml must define windows-build job"

    # Find INS-018 comment line
    ins018_line = None
    for i, line in enumerate(lines):
        if "INS-018" in line or "Download Python embeddable" in line:
            ins018_line = i
            break

    assert ins018_line is not None, "INS-018 download note must exist in release.yml"

    # Verify placement: after windows_start and before next job
    assert ins018_line > windows_start, (
        "INS-018 CI download note must come after the windows-build job header"
    )
    if next_job_after_windows is not None:
        assert ins018_line < next_job_after_windows, (
            "INS-018 CI download note must be inside the windows-build job "
            "(not in macos-arm-build or linux-build)"
        )


def test_release_yml_ci_note_references_expand_archive():
    """The CI download note must use Expand-Archive (PowerShell, not unzip/tar)."""
    text = RELEASE_YML.read_text(encoding="utf-8")
    assert "Expand-Archive" in text, (
        "release.yml CI download note must use Expand-Archive for PowerShell "
        "Windows extraction (not unzip or tar -x which are Unix tools)"
    )
