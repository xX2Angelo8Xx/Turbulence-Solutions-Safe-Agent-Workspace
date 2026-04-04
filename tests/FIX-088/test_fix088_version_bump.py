"""Tests for FIX-088: Verify all version strings are bumped to 3.2.6."""

import re
from pathlib import Path

from tests.shared.version_utils import CURRENT_VERSION

REPO_ROOT = Path(__file__).parent.parent.parent
EXPECTED_VERSION = CURRENT_VERSION


def test_config_py_version():
    """config.py must declare VERSION = '3.2.6'."""
    config_file = REPO_ROOT / "src" / "launcher" / "config.py"
    content = config_file.read_text(encoding="utf-8")
    assert f'VERSION: str = "{EXPECTED_VERSION}"' in content, (
        f"Expected VERSION = '{EXPECTED_VERSION}' in config.py, got:\n{content}"
    )


def test_pyproject_toml_version():
    """pyproject.toml must declare version = '3.2.6'."""
    toml_file = REPO_ROOT / "pyproject.toml"
    content = toml_file.read_text(encoding="utf-8")
    assert f'version = "{EXPECTED_VERSION}"' in content, (
        f"Expected version = '{EXPECTED_VERSION}' in pyproject.toml"
    )


def test_setup_iss_version():
    """setup.iss must declare MyAppVersion '3.2.6'."""
    iss_file = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    content = iss_file.read_text(encoding="utf-8")
    assert f'#define MyAppVersion "{EXPECTED_VERSION}"' in content, (
        f"Expected MyAppVersion '{EXPECTED_VERSION}' in setup.iss"
    )


def test_build_dmg_version():
    """build_dmg.sh must declare APP_VERSION='3.2.6'."""
    dmg_file = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
    content = dmg_file.read_text(encoding="utf-8")
    assert f'APP_VERSION="{EXPECTED_VERSION}"' in content, (
        f"Expected APP_VERSION='{EXPECTED_VERSION}' in build_dmg.sh"
    )


def test_all_versions_consistent():
    """All 4 version strings must agree on 3.2.6 — no stragglers."""
    config_content = (REPO_ROOT / "src" / "launcher" / "config.py").read_text(encoding="utf-8")
    toml_content = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    iss_content = (REPO_ROOT / "src" / "installer" / "windows" / "setup.iss").read_text(encoding="utf-8")
    dmg_content = (REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh").read_text(encoding="utf-8")

    config_match = re.search(r'VERSION:\s*str\s*=\s*"([^"]+)"', config_content)
    toml_match = re.search(r'^version\s*=\s*"([^"]+)"', toml_content, re.MULTILINE)
    iss_match = re.search(r'#define MyAppVersion\s*"([^"]+)"', iss_content)
    dmg_match = re.search(r'^APP_VERSION="([^"]+)"', dmg_content, re.MULTILINE)

    assert config_match, "VERSION not found in config.py"
    assert toml_match, "version not found in pyproject.toml"
    assert iss_match, "MyAppVersion not found in setup.iss"
    assert dmg_match, "APP_VERSION not found in build_dmg.sh"

    versions = {
        "config.py": config_match.group(1),
        "pyproject.toml": toml_match.group(1),
        "setup.iss": iss_match.group(1),
        "build_dmg.sh": dmg_match.group(1),
    }

    for filename, version in versions.items():
        assert version == EXPECTED_VERSION, (
            f"{filename} has version '{version}', expected '{EXPECTED_VERSION}'"
        )
