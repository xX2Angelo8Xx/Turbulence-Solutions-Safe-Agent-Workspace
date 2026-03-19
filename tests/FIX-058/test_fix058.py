"""Tests for FIX-058: Bump version to 3.0.3.

Verifies that all 5 version locations contain the current version string
as reported by tests/shared/version_utils.CURRENT_VERSION.
"""
import re
from pathlib import Path

import pytest

from tests.shared.version_utils import CURRENT_VERSION

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestVersionBump:
    def test_config_py_version(self):
        text = (REPO_ROOT / "src" / "launcher" / "config.py").read_text(encoding="utf-8")
        match = re.search(r'^VERSION\s*:\s*str\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        assert match, "VERSION constant not found in config.py"
        assert match.group(1) == CURRENT_VERSION, (
            f"config.py has {match.group(1)!r}, expected {CURRENT_VERSION!r}"
        )

    def test_pyproject_toml_version(self):
        text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        assert match, "version field not found in pyproject.toml"
        assert match.group(1) == CURRENT_VERSION, (
            f"pyproject.toml has {match.group(1)!r}, expected {CURRENT_VERSION!r}"
        )

    def test_setup_iss_version(self):
        text = (REPO_ROOT / "src" / "installer" / "windows" / "setup.iss").read_text(encoding="utf-8")
        match = re.search(r'#define\s+MyAppVersion\s+"([^"]+)"', text)
        assert match, "MyAppVersion not found in setup.iss"
        assert match.group(1) == CURRENT_VERSION, (
            f"setup.iss has {match.group(1)!r}, expected {CURRENT_VERSION!r}"
        )

    def test_build_dmg_sh_version(self):
        text = (REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh").read_text(encoding="utf-8")
        match = re.search(r'^APP_VERSION="([^"]+)"', text, re.MULTILINE)
        assert match, "APP_VERSION not found in build_dmg.sh"
        assert match.group(1) == CURRENT_VERSION, (
            f"build_dmg.sh has {match.group(1)!r}, expected {CURRENT_VERSION!r}"
        )

    def test_build_appimage_sh_version(self):
        text = (REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh").read_text(encoding="utf-8")
        match = re.search(r'^APP_VERSION="([^"]+)"', text, re.MULTILINE)
        assert match, "APP_VERSION not found in build_appimage.sh"
        assert match.group(1) == CURRENT_VERSION, (
            f"build_appimage.sh has {match.group(1)!r}, expected {CURRENT_VERSION!r}"
        )
