"""Tests for FIX-020: Bump Version to 2.0.0.

Verifies that all 5 version reference locations have been updated from 1.0.3 to 2.0.0.
"""

import re
import sys
from pathlib import Path

# Resolve repo root relative to this test file (tests/FIX-020/ -> repo root)
REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_VERSION = "2.0.0"
OLD_VERSION = "1.0.3"


def test_config_py_version() -> None:
    """VERSION constant in src/launcher/config.py must be 2.0.0."""
    # Import via path manipulation to avoid package install requirement
    config_path = REPO_ROOT / "src" / "launcher" / "config.py"
    assert config_path.exists(), f"config.py not found: {config_path}"

    content = config_path.read_text(encoding="utf-8")
    match = re.search(r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "VERSION constant not found in config.py"
    assert match.group(1) == EXPECTED_VERSION, (
        f"config.py VERSION is '{match.group(1)}', expected '{EXPECTED_VERSION}'"
    )


def test_pyproject_toml_version() -> None:
    """version field in pyproject.toml must be 2.0.0."""
    toml_path = REPO_ROOT / "pyproject.toml"
    assert toml_path.exists(), f"pyproject.toml not found: {toml_path}"

    content = toml_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "version field not found in pyproject.toml"
    assert match.group(1) == EXPECTED_VERSION, (
        f"pyproject.toml version is '{match.group(1)}', expected '{EXPECTED_VERSION}'"
    )


def test_setup_iss_version() -> None:
    """MyAppVersion define in src/installer/windows/setup.iss must be 2.0.0."""
    iss_path = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    assert iss_path.exists(), f"setup.iss not found: {iss_path}"

    content = iss_path.read_text(encoding="utf-8")
    match = re.search(r'^#define\s+MyAppVersion\s+"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "MyAppVersion define not found in setup.iss"
    assert match.group(1) == EXPECTED_VERSION, (
        f"setup.iss MyAppVersion is '{match.group(1)}', expected '{EXPECTED_VERSION}'"
    )


def test_build_dmg_sh_version() -> None:
    """APP_VERSION in src/installer/macos/build_dmg.sh must be 2.0.0."""
    sh_path = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
    assert sh_path.exists(), f"build_dmg.sh not found: {sh_path}"

    content = sh_path.read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION="([^"]+)"', content, re.MULTILINE)
    assert match is not None, "APP_VERSION not found in build_dmg.sh"
    assert match.group(1) == EXPECTED_VERSION, (
        f"build_dmg.sh APP_VERSION is '{match.group(1)}', expected '{EXPECTED_VERSION}'"
    )


def test_build_appimage_sh_version() -> None:
    """APP_VERSION in src/installer/linux/build_appimage.sh must be 2.0.0."""
    sh_path = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
    assert sh_path.exists(), f"build_appimage.sh not found: {sh_path}"

    content = sh_path.read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION="([^"]+)"', content, re.MULTILINE)
    assert match is not None, "APP_VERSION not found in build_appimage.sh"
    assert match.group(1) == EXPECTED_VERSION, (
        f"build_appimage.sh APP_VERSION is '{match.group(1)}', expected '{EXPECTED_VERSION}'"
    )


def test_no_old_version_in_version_files() -> None:
    """None of the 5 version files should still contain the old version 1.0.3."""
    files = [
        REPO_ROOT / "src" / "launcher" / "config.py",
        REPO_ROOT / "pyproject.toml",
        REPO_ROOT / "src" / "installer" / "windows" / "setup.iss",
        REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh",
        REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh",
    ]
    for file_path in files:
        assert file_path.exists(), f"File not found: {file_path}"
        content = file_path.read_text(encoding="utf-8")
        # Check only version-assignment lines, not comments or docs referencing old version
        version_lines = [
            line for line in content.splitlines()
            if OLD_VERSION in line
            and not line.strip().startswith("#")
            and not line.strip().startswith("//")
        ]
        assert not version_lines, (
            f"Old version '{OLD_VERSION}' still present in {file_path.name}: "
            + str(version_lines)
        )
