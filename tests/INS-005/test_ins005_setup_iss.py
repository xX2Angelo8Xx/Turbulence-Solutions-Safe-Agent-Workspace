"""Tests for INS-005: Windows Installer (setup.iss)"""

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SETUP_ISS = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"


def read_iss() -> str:
    return SETUP_ISS.read_text(encoding="utf-8")


class TestFileExists:
    def test_file_exists(self):
        assert SETUP_ISS.exists(), f"setup.iss not found at {SETUP_ISS}"

    def test_file_non_empty(self):
        assert SETUP_ISS.stat().st_size > 0, "setup.iss is empty"


class TestSections:
    @pytest.mark.parametrize("section", [
        "[Setup]", "[Files]", "[Icons]", "[Run]", "[UninstallDelete]"
    ])
    def test_required_section_present(self, section):
        content = read_iss()
        assert section in content, f"Missing required section: {section}"


class TestSetupValues:
    def test_app_name(self):
        content = read_iss()
        assert 'MyAppName "Agent Environment Launcher"' in content

    def test_app_version(self):
        content = read_iss()
        assert 'MyAppVersion "2.0.0"' in content

    def test_app_publisher(self):
        content = read_iss()
        assert 'MyAppPublisher "Turbulence Solutions"' in content

    def test_uses_autopf_not_hardcoded(self):
        content = read_iss()
        assert "{autopf}" in content, "DefaultDirName must use {autopf} macro, not a hardcoded path"
        assert "C:\\Program Files" not in content, "Must not hardcode C:\\Program Files"
        assert "C:/Program Files" not in content, "Must not hardcode C:/Program Files"

    def test_source_uses_dist_launcher_glob(self):
        content = read_iss()
        assert r"dist\launcher\*" in content, r"Source must reference dist\launcher\*"

    def test_source_has_recursesubdirs(self):
        content = read_iss()
        assert "recursesubdirs" in content, "Files entry must include recursesubdirs flag"

    def test_has_app_id(self):
        content = read_iss()
        assert "AppId=" in content, "Setup section must declare AppId"

    def test_privileges_required_set(self):
        content = read_iss()
        assert "PrivilegesRequired=" in content, "PrivilegesRequired must be declared"
        assert re.search(r"PrivilegesRequired=(admin|lowest)", content), (
            "PrivilegesRequired must be 'admin' or 'lowest'"
        )
