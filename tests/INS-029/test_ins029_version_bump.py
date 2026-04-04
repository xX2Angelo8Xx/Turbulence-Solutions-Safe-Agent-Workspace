"""Tests for INS-029: Version bump to 3.2.4.

Verifies that all 5 canonical version files contain "3.2.4" and none
contain the stale version string "3.2.3".
"""

import re
from pathlib import Path

from tests.shared.version_utils import CURRENT_VERSION

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_VERSION = CURRENT_VERSION
STALE_VERSION = "3.2.3"

_VERSION_FILES = [
    REPO_ROOT / "src" / "launcher" / "config.py",
    REPO_ROOT / "pyproject.toml",
    REPO_ROOT / "src" / "installer" / "windows" / "setup.iss",
    REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh",
    REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh",
]


def test_config_py_version() -> None:
    """VERSION constant in src/launcher/config.py must be 3.2.4."""
    config_path = REPO_ROOT / "src" / "launcher" / "config.py"
    assert config_path.exists(), f"config.py not found: {config_path}"
    content = config_path.read_text(encoding="utf-8")
    match = re.search(r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "VERSION constant not found in config.py"
    assert match.group(1) == EXPECTED_VERSION, (
        f"config.py VERSION is {match.group(1)!r}, expected {EXPECTED_VERSION!r}"
    )


def test_pyproject_toml_version() -> None:
    """version field in pyproject.toml must be 3.2.4."""
    toml_path = REPO_ROOT / "pyproject.toml"
    assert toml_path.exists(), f"pyproject.toml not found: {toml_path}"
    content = toml_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "version field not found in pyproject.toml"
    assert match.group(1) == EXPECTED_VERSION, (
        f"pyproject.toml version is {match.group(1)!r}, expected {EXPECTED_VERSION!r}"
    )


def test_setup_iss_version() -> None:
    """MyAppVersion define in src/installer/windows/setup.iss must be 3.2.4."""
    iss_path = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    assert iss_path.exists(), f"setup.iss not found: {iss_path}"
    content = iss_path.read_text(encoding="utf-8")
    match = re.search(r'#define\s+MyAppVersion\s+"([^"]+)"', content)
    assert match is not None, "MyAppVersion define not found in setup.iss"
    assert match.group(1) == EXPECTED_VERSION, (
        f"setup.iss MyAppVersion is {match.group(1)!r}, expected {EXPECTED_VERSION!r}"
    )


def test_build_dmg_version() -> None:
    """APP_VERSION in src/installer/macos/build_dmg.sh must be 3.2.4."""
    dmg_path = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
    assert dmg_path.exists(), f"build_dmg.sh not found: {dmg_path}"
    content = dmg_path.read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "APP_VERSION not found in build_dmg.sh"
    assert match.group(1) == EXPECTED_VERSION, (
        f"build_dmg.sh APP_VERSION is {match.group(1)!r}, expected {EXPECTED_VERSION!r}"
    )


def test_build_appimage_version() -> None:
    """APP_VERSION in src/installer/linux/build_appimage.sh must be 3.2.4."""
    appimage_path = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
    assert appimage_path.exists(), f"build_appimage.sh not found: {appimage_path}"
    content = appimage_path.read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "APP_VERSION not found in build_appimage.sh"
    assert match.group(1) == EXPECTED_VERSION, (
        f"build_appimage.sh APP_VERSION is {match.group(1)!r}, expected {EXPECTED_VERSION!r}"
    )


def test_all_version_files_agree() -> None:
    """All 5 canonical version files must contain 3.2.4."""
    patterns = [
        (REPO_ROOT / "src" / "launcher" / "config.py",
         r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"'),
        (REPO_ROOT / "pyproject.toml",
         r'^version\s*=\s*"([^"]+)"'),
        (REPO_ROOT / "src" / "installer" / "windows" / "setup.iss",
         r'#define\s+MyAppVersion\s+"([^"]+)"'),
        (REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh",
         r'^APP_VERSION\s*=\s*"([^"]+)"'),
        (REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh",
         r'^APP_VERSION\s*=\s*"([^"]+)"'),
    ]
    versions_found: dict[str, str] = {}
    for path, pattern in patterns:
        content = path.read_text(encoding="utf-8")
        match = re.search(pattern, content, re.MULTILINE)
        assert match is not None, f"Version pattern not found in {path.name}"
        versions_found[path.name] = match.group(1)

    for filename, ver in versions_found.items():
        assert ver == EXPECTED_VERSION, (
            f"{filename} has version {ver!r}, expected {EXPECTED_VERSION!r}"
        )


def test_no_stale_version_in_config_py() -> None:
    """config.py must not contain the stale 3.2.3 version constant."""
    config_path = REPO_ROOT / "src" / "launcher" / "config.py"
    content = config_path.read_text(encoding="utf-8")
    match = re.search(r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None
    assert match.group(1) != STALE_VERSION, (
        "config.py VERSION still references stale 3.2.3"
    )


def test_no_stale_version_in_pyproject_toml() -> None:
    """pyproject.toml must not contain the stale 3.2.3 version field."""
    toml_path = REPO_ROOT / "pyproject.toml"
    content = toml_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None
    assert match.group(1) != STALE_VERSION, (
        "pyproject.toml version still references stale 3.2.3"
    )


def test_version_import_from_config() -> None:
    """Importing VERSION from launcher.config must yield '3.2.4'."""
    from launcher.config import VERSION  # type: ignore[import]
    assert VERSION == EXPECTED_VERSION, (
        f"launcher.config.VERSION is {VERSION!r}, expected {EXPECTED_VERSION!r}"
    )


def test_version_semver_format() -> None:
    """VERSION must follow semver MAJOR.MINOR.PATCH format."""
    pattern = re.compile(r"^\d+\.\d+\.\d+$")
    assert pattern.match(EXPECTED_VERSION), (
        f"{EXPECTED_VERSION!r} does not match semver format"
    )


def test_single_version_define_in_iss() -> None:
    """setup.iss must define MyAppVersion exactly once."""
    iss_path = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    content = iss_path.read_text(encoding="utf-8")
    matches = re.findall(r'#define\s+MyAppVersion\s+"[^"]+"', content)
    assert len(matches) == 1, (
        f"Expected 1 MyAppVersion define in setup.iss, found {len(matches)}"
    )
