"""INS-005 Tester edge-case tests for setup.iss"""

import pathlib
import re
import tomllib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SETUP_ISS = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
PYPROJECT = REPO_ROOT / "pyproject.toml"
LAUNCHER_SPEC = REPO_ROOT / "launcher.spec"


def read_iss() -> str:
    return SETUP_ISS.read_text(encoding="utf-8")


def read_pyproject() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# GUID format
# ---------------------------------------------------------------------------

class TestAppIdGuid:
    def test_app_id_is_valid_guid_format(self):
        """AppId must contain a properly formatted GUID.

        Inno Setup uses {{ to produce a literal { in string values, so the raw
        text in the .iss file looks like:
            AppId={{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
        where {{ is the escaped opening brace and the trailing } closes it.
        """
        content = read_iss()
        # Match the Inno Setup double-brace escaped GUID: AppId={{GUID}
        guid_pattern = re.compile(
            r"AppId=\{\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}"
        )
        assert guid_pattern.search(content), (
            "AppId must use Inno Setup GUID format: AppId={{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}"
        )

    def test_app_id_guid_is_not_all_zeros(self):
        """AppId GUID must not be all-zeros (placeholder sentinel)"""
        content = read_iss()
        assert "00000000-0000-0000-0000-000000000000" not in content, (
            "AppId must not be the null GUID — it would not uniquely identify the installer"
        )


# ---------------------------------------------------------------------------
# No hardcoded absolute paths
# ---------------------------------------------------------------------------

class TestNoHardcodedPaths:
    @pytest.mark.parametrize("drive_letter", ["C:", "D:", "E:", "F:", "G:"])
    def test_no_hardcoded_drive_letter(self, drive_letter):
        content = read_iss()
        assert drive_letter + "\\" not in content and drive_letter + "/" not in content, (
            f"setup.iss must not contain hardcoded drive path '{drive_letter}\\' or '{drive_letter}/'"
        )

    def test_source_path_is_relative_not_absolute(self):
        """Source path must navigate from the .iss file up to the repo root using ..\\  segments."""
        content = read_iss()
        match = re.search(r'Source:\s*"([^"]+)"', content)
        assert match, "No Source: path found"
        source_val = match.group(1)
        parts = [p for p in source_val.split("\\") if p]
        assert parts[:3] == ["..", "..", ".."], (
            f"Source path {source_val!r} must start with three ..\\  segments "
            "to navigate from src/installer/windows/ to the repo root"
        )

    def test_default_dir_uses_autopf_not_direct_path(self):
        """DefaultDirName must use {autopf} macro at the start of its value."""
        content = read_iss()
        assert re.search(r"DefaultDirName=\{autopf\}", content), (
            "DefaultDirName must literally start with {autopf}"
        )


# ---------------------------------------------------------------------------
# Output file naming convention
# ---------------------------------------------------------------------------

class TestOutputFilename:
    def test_output_base_filename_declared(self):
        content = read_iss()
        assert "OutputBaseFilename=" in content, "OutputBaseFilename must be declared"

    def test_output_base_filename_contains_setup(self):
        """Follow the <AppName>-Setup naming convention."""
        content = read_iss()
        match = re.search(r"OutputBaseFilename=(\S+)", content)
        assert match, "OutputBaseFilename must have a value"
        assert "Setup" in match.group(1), (
            "OutputBaseFilename should include 'Setup' to be recognisable on end-user machines"
        )

    def test_output_base_filename_no_spaces(self):
        """Output filename must not contain spaces (would require quoting on all installer CLIs)."""
        content = read_iss()
        match = re.search(r"OutputBaseFilename=(.+)", content)
        assert match, "OutputBaseFilename must have a value"
        filename_value = match.group(1).strip()
        assert " " not in filename_value, (
            f"OutputBaseFilename '{filename_value}' must not contain spaces"
        )


# ---------------------------------------------------------------------------
# Files section flags
# ---------------------------------------------------------------------------

class TestFilesFlags:
    def test_createallsubdirs_flag_present(self):
        """Files entry must include createallsubdirs to mirror full onedir tree."""
        content = read_iss()
        assert "createallsubdirs" in content, (
            "Files entry must include 'createallsubdirs' flag alongside recursesubdirs"
        )

    def test_ignoreversion_flag_present(self):
        """ignoreversion flag must be set to prevent version-check failures on DLLs."""
        content = read_iss()
        assert "ignoreversion" in content, (
            "Files entry must include 'ignoreversion' flag — PyInstaller bundles have no consistent version info"
        )


# ---------------------------------------------------------------------------
# Compression settings
# ---------------------------------------------------------------------------

class TestCompression:
    def test_compression_is_lzma(self):
        content = read_iss()
        assert re.search(r"^Compression=lzma", content, re.MULTILINE), (
            "Compression must be set to 'lzma' for best-in-class size reduction"
        )

    def test_solid_compression_enabled(self):
        content = read_iss()
        assert re.search(r"^SolidCompression=yes", content, re.MULTILINE), (
            "SolidCompression=yes is required to achieve maximum lzma compression ratio"
        )


# ---------------------------------------------------------------------------
# Privileges and architecture
# ---------------------------------------------------------------------------

class TestPrivilegesAndArch:
    def test_privileges_required_is_exactly_admin(self):
        """PrivilegesRequired must be 'admin', not 'lowest' — installer writes to Program Files."""
        content = read_iss()
        assert re.search(r"^PrivilegesRequired=admin$", content, re.MULTILINE), (
            "PrivilegesRequired must be exactly 'admin' — writing to {autopf} requires elevation"
        )

    def test_architecture_directives_not_present(self):
        """ArchitecturesAllowed/ArchitecturesInstallMode removed — not supported by CI Inno Setup (BUG-041)."""
        content = read_iss()
        assert "ArchitecturesAllowed" not in content, (
            "ArchitecturesAllowed must not be present — not supported by chocolatey Inno Setup on CI (BUG-041)"
        )
        assert "ArchitecturesInstallMode" not in content, (
            "ArchitecturesInstallMode must not be present — not supported by chocolatey Inno Setup on CI (BUG-041)"
        )


# ---------------------------------------------------------------------------
# Shortcuts and uninstaller
# ---------------------------------------------------------------------------

class TestShortcutsAndUninstaller:
    def test_start_menu_shortcut_uses_group_macro(self):
        """Start Menu shortcut must use {group} macro for proper placement."""
        content = read_iss()
        assert "{group}" in content, (
            "[Icons] section must contain a {group} shortcut for the Start Menu"
        )

    def test_desktop_shortcut_is_opt_in(self):
        """Desktop shortcut must be unchecked by default — do not pollute desktops."""
        content = read_iss()
        # Check the desktopicon task has Flags: unchecked
        assert re.search(r"desktopicon.*Flags:.*unchecked", content, re.IGNORECASE), (
            "Desktop shortcut task must have 'Flags: unchecked' so it is opt-in only"
        )

    def test_uninstall_delete_type_is_filesandirs(self):
        """UninstallDelete entry must use 'filesandirs' to clean up the entire install tree."""
        content = read_iss()
        assert re.search(r"Type:\s*filesandirs", content), (
            "UninstallDelete must use 'Type: filesandirs' to remove all installed files"
        )

    def test_uninstall_targets_app_macro(self):
        """UninstallDelete must reference {app} — not a hardcoded path."""
        content = read_iss()
        assert re.search(r'Name:\s*"\{app\}"', content), (
            "UninstallDelete Name must be '{app}' — never a hardcoded path"
        )


# ---------------------------------------------------------------------------
# Version consistency with pyproject.toml
# ---------------------------------------------------------------------------

class TestVersionConsistency:
    def test_app_version_matches_pyproject_toml(self):
        """AppVersion in setup.iss must match version in pyproject.toml."""
        pyproject = read_pyproject()
        expected_version = pyproject["project"]["version"]
        content = read_iss()
        assert f'MyAppVersion "{expected_version}"' in content, (
            f"AppVersion in setup.iss must match pyproject.toml version '{expected_version}'"
        )


# ---------------------------------------------------------------------------
# Exe name consistency with PyInstaller spec
# ---------------------------------------------------------------------------

class TestExeNameConsistency:
    def test_exe_name_matches_pyinstaller_spec_name(self):
        """MyAppExeName must be '<spec-name>.exe' where spec-name is the EXE name= in launcher.spec."""
        spec_content = LAUNCHER_SPEC.read_text(encoding="utf-8")
        # Extract name='launcher' from EXE(...) block
        match = re.search(r"name='([^']+)'", spec_content)
        assert match, "Could not find name= in launcher.spec EXE block"
        spec_exe_name = match.group(1) + ".exe"

        iss_content = read_iss()
        assert f'MyAppExeName "{spec_exe_name}"' in iss_content, (
            f"MyAppExeName in setup.iss must be '{spec_exe_name}' to match PyInstaller output"
        )

    def test_source_dir_matches_pyinstaller_collect_name(self):
        """The source directory in setup.iss must match the COLLECT name= in launcher.spec."""
        spec_content = LAUNCHER_SPEC.read_text(encoding="utf-8")
        # COLLECT(..., name='launcher') defines the output folder
        collect_match = re.search(r"coll\s*=\s*COLLECT\(.*?name='([^']+)'", spec_content, re.DOTALL)
        assert collect_match, "Could not find COLLECT name= in launcher.spec"
        collect_name = collect_match.group(1)

        iss_content = read_iss()
        expected_source = rf"dist\{collect_name}\*"
        assert expected_source in iss_content, (
            f"Source in setup.iss must reference 'dist\\{collect_name}\\*' to match COLLECT output"
        )


# ---------------------------------------------------------------------------
# Wizard style
# ---------------------------------------------------------------------------

class TestWizardStyle:
    def test_wizard_style_is_modern(self):
        """WizardStyle=modern gives the installer a contemporary look."""
        content = read_iss()
        assert re.search(r"^WizardStyle=modern$", content, re.MULTILINE), (
            "WizardStyle must be set to 'modern'"
        )
