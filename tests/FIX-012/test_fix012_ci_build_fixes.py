"""
FIX-012: Fix macOS PyInstaller target-arch and Windows Inno Setup directives.

Tests:
  1. build_dmg.sh does NOT contain --target-arch in PyInstaller invocation (BUG-040)
  2. build_dmg.sh still contains PyInstaller/pyinstaller command
  3. build_dmg.sh still passes --distpath, --workpath, --noconfirm flags
  4. build_dmg.sh still passes the spec file to PyInstaller
  5. setup.iss does NOT contain ArchitecturesInstallMode (BUG-041)
  6. setup.iss does NOT contain ArchitecturesAllowed (BUG-041)
  7. setup.iss still has required [Setup] directives
"""

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
SETUP_ISS = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"


def read_dmg() -> str:
    return BUILD_DMG.read_text(encoding="utf-8")


def read_iss() -> str:
    return SETUP_ISS.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# build_dmg.sh — BUG-040 regression
# ---------------------------------------------------------------------------

class TestBuildDmgTargetArch:
    def test_target_arch_flag_absent(self):
        """--target-arch must NOT appear in the PyInstaller invocation (BUG-040)."""
        content = read_dmg()
        assert "--target-arch" not in content, (
            "--target-arch must be removed from build_dmg.sh — "
            "not allowed when a .spec file is given to PyInstaller"
        )

    def test_pyinstaller_command_present(self):
        """PyInstaller invocation must still exist in the script."""
        content = read_dmg()
        assert re.search(r"python\s+-m\s+PyInstaller", content, re.IGNORECASE), (
            "build_dmg.sh must still invoke python -m PyInstaller"
        )

    def test_distpath_flag_present(self):
        """--distpath flag must still be passed to PyInstaller."""
        content = read_dmg()
        assert "--distpath" in content, (
            "--distpath must still be present in the PyInstaller invocation"
        )

    def test_workpath_flag_present(self):
        """--workpath flag must still be passed to PyInstaller."""
        content = read_dmg()
        assert "--workpath" in content, (
            "--workpath must still be present in the PyInstaller invocation"
        )

    def test_noconfirm_flag_present(self):
        """--noconfirm flag must still be passed to PyInstaller."""
        content = read_dmg()
        assert "--noconfirm" in content, (
            "--noconfirm must still be present in the PyInstaller invocation"
        )

    def test_spec_file_passed_to_pyinstaller(self):
        """Spec file variable must still be the last argument to PyInstaller."""
        content = read_dmg()
        assert "${SPEC_FILE}" in content, (
            '${SPEC_FILE} must still be referenced in the PyInstaller invocation'
        )

    def test_spec_file_variable_defined(self):
        """SPEC_FILE variable must be defined in the script constants section."""
        content = read_dmg()
        assert re.search(r'SPEC_FILE\s*=\s*"launcher\.spec"', content), (
            'SPEC_FILE must be defined as "launcher.spec" in build_dmg.sh constants'
        )


# ---------------------------------------------------------------------------
# setup.iss — BUG-041 regression
# ---------------------------------------------------------------------------

class TestSetupIssArchDirectives:
    def test_architectures_install_mode_absent(self):
        """ArchitecturesInstallMode must NOT be present in setup.iss (BUG-041)."""
        content = read_iss()
        assert "ArchitecturesInstallMode" not in content, (
            "ArchitecturesInstallMode must be removed from setup.iss — "
            "not supported by CI Inno Setup version (chocolatey)"
        )

    def test_architectures_allowed_absent(self):
        """ArchitecturesAllowed must NOT be present in setup.iss (BUG-041)."""
        content = read_iss()
        assert "ArchitecturesAllowed" not in content, (
            "ArchitecturesAllowed must be removed from setup.iss — "
            "not supported by CI Inno Setup version (chocolatey)"
        )

    def test_setup_section_present(self):
        """[Setup] section must still be present."""
        content = read_iss()
        assert "[Setup]" in content, "[Setup] section must exist in setup.iss"

    def test_app_id_present(self):
        """AppId must still be present."""
        content = read_iss()
        assert "AppId=" in content, "AppId directive must exist in [Setup] section"

    def test_app_name_present(self):
        """AppName must still be present."""
        content = read_iss()
        assert "AppName=" in content, "AppName directive must exist in [Setup] section"

    def test_app_version_present(self):
        """AppVersion must still be present."""
        content = read_iss()
        assert "AppVersion=" in content, "AppVersion directive must exist in [Setup] section"

    def test_output_base_filename_present(self):
        """OutputBaseFilename must still be present."""
        content = read_iss()
        assert "OutputBaseFilename=" in content, (
            "OutputBaseFilename directive must exist in [Setup] section"
        )

    def test_privileges_required_admin(self):
        """PrivilegesRequired=admin must still be set."""
        content = read_iss()
        assert re.search(r"^PrivilegesRequired=admin$", content, re.MULTILINE), (
            "PrivilegesRequired=admin must still be present in setup.iss"
        )
