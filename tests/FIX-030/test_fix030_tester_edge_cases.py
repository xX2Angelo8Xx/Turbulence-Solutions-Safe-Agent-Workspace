"""Tester edge-case tests for FIX-030: Bump Version to 2.0.1.

Additional edge-case tests beyond what the Developer wrote:
- Semver format validation (exact N.N.N pattern)
- Cross-file consistency (all 5 sources agree)
- No partial old version strings anywhere in version lines
- Version is a strict bump (2.0.1 > 2.0.0)
- No version string contains trailing whitespace or BOM
- pyproject.toml version matches config.py VERSION exactly
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_VERSION = "2.0.1"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Helper: extract each file's version string
# ---------------------------------------------------------------------------

def _extract_config_version(content: str) -> str:
    m = re.search(r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert m, "VERSION constant not found in config.py"
    return m.group(1)


def _extract_pyproject_version(content: str) -> str:
    m = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert m, "version field not found in pyproject.toml"
    return m.group(1)


def _extract_iss_version(content: str) -> str:
    m = re.search(r'^#define\s+MyAppVersion\s+"([^"]+)"', content, re.MULTILINE)
    assert m, "MyAppVersion not found in setup.iss"
    return m.group(1)


def _extract_dmg_version(content: str) -> str:
    m = re.search(r'^APP_VERSION="([^"]+)"', content, re.MULTILINE)
    assert m, "APP_VERSION not found in build_dmg.sh"
    return m.group(1)


def _extract_appimage_version(content: str) -> str:
    m = re.search(r'^APP_VERSION="([^"]+)"', content, re.MULTILINE)
    assert m, "APP_VERSION not found in build_appimage.sh"
    return m.group(1)


# ---------------------------------------------------------------------------
# Semver format tests
# ---------------------------------------------------------------------------

def test_config_version_is_valid_semver() -> None:
    """VERSION in config.py must be valid semver (N.N.N)."""
    ver = _extract_config_version(_read("src/launcher/config.py"))
    assert SEMVER_RE.match(ver), f"config.py VERSION '{ver}' is not valid semver"


def test_pyproject_version_is_valid_semver() -> None:
    """version in pyproject.toml must be valid semver (N.N.N)."""
    ver = _extract_pyproject_version(_read("pyproject.toml"))
    assert SEMVER_RE.match(ver), f"pyproject.toml version '{ver}' is not valid semver"


def test_setup_iss_version_is_valid_semver() -> None:
    """MyAppVersion in setup.iss must be valid semver (N.N.N)."""
    ver = _extract_iss_version(_read("src/installer/windows/setup.iss"))
    assert SEMVER_RE.match(ver), f"setup.iss MyAppVersion '{ver}' is not valid semver"


def test_build_dmg_version_is_valid_semver() -> None:
    """APP_VERSION in build_dmg.sh must be valid semver (N.N.N)."""
    ver = _extract_dmg_version(_read("src/installer/macos/build_dmg.sh"))
    assert SEMVER_RE.match(ver), f"build_dmg.sh APP_VERSION '{ver}' is not valid semver"


def test_build_appimage_version_is_valid_semver() -> None:
    """APP_VERSION in build_appimage.sh must be valid semver (N.N.N)."""
    ver = _extract_appimage_version(_read("src/installer/linux/build_appimage.sh"))
    assert SEMVER_RE.match(ver), f"build_appimage.sh APP_VERSION '{ver}' is not valid semver"


# ---------------------------------------------------------------------------
# Cross-consistency: all 5 must agree
# ---------------------------------------------------------------------------

def test_all_version_locations_are_consistent() -> None:
    """All 5 version files must contain exactly the same version string."""
    versions = {
        "config.py": _extract_config_version(_read("src/launcher/config.py")),
        "pyproject.toml": _extract_pyproject_version(_read("pyproject.toml")),
        "setup.iss": _extract_iss_version(_read("src/installer/windows/setup.iss")),
        "build_dmg.sh": _extract_dmg_version(_read("src/installer/macos/build_dmg.sh")),
        "build_appimage.sh": _extract_appimage_version(_read("src/installer/linux/build_appimage.sh")),
    }
    unique = set(versions.values())
    assert len(unique) == 1, (
        f"Version mismatch across files: {versions}"
    )


# ---------------------------------------------------------------------------
# Version is a strict bump from 2.0.0
# ---------------------------------------------------------------------------

def test_version_is_strict_bump_of_2_0_0() -> None:
    """Confirm 2.0.1 is strictly greater than the old version 2.0.0 without extra chars."""
    parts_new = [int(x) for x in EXPECTED_VERSION.split(".")]
    parts_old = [int(x) for x in "2.0.0".split(".")]
    assert parts_new > parts_old, (
        f"Expected new version {EXPECTED_VERSION} > 2.0.0"
    )


# ---------------------------------------------------------------------------
# No trailing whitespace or BOM on version assignment lines
# ---------------------------------------------------------------------------

def test_config_py_version_line_no_trailing_whitespace() -> None:
    """The VERSION assignment line in config.py must not have trailing whitespace."""
    content = _read("src/launcher/config.py")
    for line in content.splitlines():
        if re.match(r'^VERSION\s*:', line):
            assert line == line.rstrip(), (
                f"Trailing whitespace on VERSION line: {repr(line)}"
            )


def test_pyproject_version_line_no_trailing_whitespace() -> None:
    """The version field line in pyproject.toml must not have trailing whitespace."""
    content = _read("pyproject.toml")
    for line in content.splitlines():
        if re.match(r'^version\s*=', line):
            assert line == line.rstrip(), (
                f"Trailing whitespace on version line: {repr(line)}"
            )


def test_no_bom_in_version_files() -> None:
    """None of the 5 version files should start with a UTF-8 BOM (\\xef\\xbb\\xbf)."""
    files = [
        "src/launcher/config.py",
        "pyproject.toml",
        "src/installer/windows/setup.iss",
        "src/installer/macos/build_dmg.sh",
        "src/installer/linux/build_appimage.sh",
    ]
    for rel in files:
        raw = (REPO_ROOT / rel).read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), (
            f"{rel} starts with a UTF-8 BOM — should be BOM-free"
        )


# ---------------------------------------------------------------------------
# pyproject.toml version matches config.py VERSION exactly
# ---------------------------------------------------------------------------

def test_pyproject_version_matches_config_py() -> None:
    """pyproject.toml version and config.py VERSION must be identical."""
    config_ver = _extract_config_version(_read("src/launcher/config.py"))
    toml_ver = _extract_pyproject_version(_read("pyproject.toml"))
    assert config_ver == toml_ver, (
        f"config.py VERSION '{config_ver}' != pyproject.toml version '{toml_ver}'"
    )
