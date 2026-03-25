"""Tests for FIX-070: Version bump verification.

Verifies that all 5 version reference locations have been updated to 3.2.0.
Uses CURRENT_VERSION from tests/shared/version_utils.py (dynamically read
from src/launcher/config.py) so this test survives future version bumps.
"""

import re
from pathlib import Path

from tests.shared.version_utils import CURRENT_VERSION

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_config_py_version() -> None:
    """VERSION constant in src/launcher/config.py must equal CURRENT_VERSION."""
    config_path = REPO_ROOT / "src" / "launcher" / "config.py"
    assert config_path.exists(), f"config.py not found: {config_path}"

    content = config_path.read_text(encoding="utf-8")
    match = re.search(r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "VERSION constant not found in config.py"
    assert match.group(1) == CURRENT_VERSION, (
        f"config.py VERSION is '{match.group(1)}', expected '{CURRENT_VERSION}'"
    )


def test_pyproject_toml_version() -> None:
    """version field in pyproject.toml must equal CURRENT_VERSION."""
    toml_path = REPO_ROOT / "pyproject.toml"
    assert toml_path.exists(), f"pyproject.toml not found: {toml_path}"

    content = toml_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "version field not found in pyproject.toml"
    assert match.group(1) == CURRENT_VERSION, (
        f"pyproject.toml version is '{match.group(1)}', expected '{CURRENT_VERSION}'"
    )


def test_setup_iss_version() -> None:
    """MyAppVersion define in src/installer/windows/setup.iss must equal CURRENT_VERSION."""
    iss_path = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    assert iss_path.exists(), f"setup.iss not found: {iss_path}"

    content = iss_path.read_text(encoding="utf-8")
    match = re.search(r'^#define\s+MyAppVersion\s+"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "MyAppVersion define not found in setup.iss"
    assert match.group(1) == CURRENT_VERSION, (
        f"setup.iss MyAppVersion is '{match.group(1)}', expected '{CURRENT_VERSION}'"
    )


def test_build_dmg_sh_version() -> None:
    """APP_VERSION in src/installer/macos/build_dmg.sh must equal CURRENT_VERSION."""
    sh_path = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
    assert sh_path.exists(), f"build_dmg.sh not found: {sh_path}"

    content = sh_path.read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION="([^"]+)"', content, re.MULTILINE)
    assert match is not None, "APP_VERSION not found in build_dmg.sh"
    assert match.group(1) == CURRENT_VERSION, (
        f"build_dmg.sh APP_VERSION is '{match.group(1)}', expected '{CURRENT_VERSION}'"
    )


def test_build_appimage_sh_version() -> None:
    """APP_VERSION in src/installer/linux/build_appimage.sh must equal CURRENT_VERSION."""
    sh_path = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
    assert sh_path.exists(), f"build_appimage.sh not found: {sh_path}"

    content = sh_path.read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION="([^"]+)"', content, re.MULTILINE)
    assert match is not None, "APP_VERSION not found in build_appimage.sh"
    assert match.group(1) == CURRENT_VERSION, (
        f"build_appimage.sh APP_VERSION is '{match.group(1)}', expected '{CURRENT_VERSION}'"
    )


def test_all_versions_consistent() -> None:
    """All 5 version sources must agree on the same version string."""
    versions: dict[str, str] = {}

    config_path = REPO_ROOT / "src" / "launcher" / "config.py"
    m = re.search(
        r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"',
        config_path.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert m, "VERSION not found in config.py"
    versions["config.py"] = m.group(1)

    toml_path = REPO_ROOT / "pyproject.toml"
    m = re.search(r'^version\s*=\s*"([^"]+)"', toml_path.read_text(encoding="utf-8"), re.MULTILINE)
    assert m, "version not found in pyproject.toml"
    versions["pyproject.toml"] = m.group(1)

    iss_path = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    m = re.search(
        r'^#define\s+MyAppVersion\s+"([^"]+)"',
        iss_path.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert m, "MyAppVersion not found in setup.iss"
    versions["setup.iss"] = m.group(1)

    dmg_path = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
    m = re.search(r'^APP_VERSION="([^"]+)"', dmg_path.read_text(encoding="utf-8"), re.MULTILINE)
    assert m, "APP_VERSION not found in build_dmg.sh"
    versions["build_dmg.sh"] = m.group(1)

    appimage_path = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
    m = re.search(
        r'^APP_VERSION="([^"]+)"', appimage_path.read_text(encoding="utf-8"), re.MULTILINE
    )
    assert m, "APP_VERSION not found in build_appimage.sh"
    versions["build_appimage.sh"] = m.group(1)

    unique = set(versions.values())
    assert len(unique) == 1, (
        f"Version mismatch across sources: {versions}"
    )
    assert unique.pop() == CURRENT_VERSION, (
        f"All sources agree on '{unique}' but CURRENT_VERSION is '{CURRENT_VERSION}'"
    )


# ---------------------------------------------------------------------------
# Tester edge-case tests (added during review)
# ---------------------------------------------------------------------------

STALE_VERSION = "3.1.2"
_VERSION_FILES = [
    REPO_ROOT / "src" / "launcher" / "config.py",
    REPO_ROOT / "pyproject.toml",
    REPO_ROOT / "src" / "installer" / "windows" / "setup.iss",
    REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh",
    REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh",
]


def test_current_version_is_3_2_1() -> None:
    """CURRENT_VERSION (read from config.py) must equal the expected release version 3.2.1."""
    assert CURRENT_VERSION == "3.2.1", (
        f"Expected CURRENT_VERSION == '3.2.1', got '{CURRENT_VERSION}'"
    )


def test_no_stale_3_1_2_in_version_files() -> None:
    """None of the 5 canonical version files may still contain the old version 3.1.2."""
    stale_found: dict[str, list[int]] = {}
    for path in _VERSION_FILES:
        assert path.exists(), f"Version file not found: {path}"
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if STALE_VERSION in line:
                stale_found.setdefault(str(path.relative_to(REPO_ROOT)), []).append(lineno)
    assert not stale_found, (
        f"Stale version '{STALE_VERSION}' still found in: {stale_found}"
    )
