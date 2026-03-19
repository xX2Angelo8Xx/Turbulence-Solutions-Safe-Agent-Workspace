"""Edge-case tests for FIX-020: Bump Version to 2.0.0 — Tester additions.

Covers:
- Semantic version format (MAJOR.MINOR.PATCH) validation in all 5 locations
- Cross-file version consistency (all 5 locations agree)
- Major component is exactly 2, minor and patch are exactly 0 (major-bump contract)
- No stale intermediate versions (1.0.0, 1.0.1, 1.0.2) in version assignment lines
- config.py VERSION module import returns the expected version string
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_VERSION: str = re.search(
    r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"',
    (REPO_ROOT / "src" / "launcher" / "config.py").read_text(encoding="utf-8"),
    re.MULTILINE,
).group(1)
_ver_parts = EXPECTED_VERSION.split(".")
EXPECTED_MAJOR = int(_ver_parts[0])
EXPECTED_MINOR = int(_ver_parts[1])
EXPECTED_PATCH = int(_ver_parts[2])
del _ver_parts
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Stale versions that must NOT appear anywhere in version-assignment lines
STALE_VERSIONS = ["1.0.0", "1.0.1", "1.0.2", "1.0.3", "2.0.1", "2.1.0", "2.1.3"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read(rel_path: str) -> str:
    p = REPO_ROOT / rel_path
    assert p.exists(), f"File not found: {p}"
    return p.read_text(encoding="utf-8")


def _extract_config_version() -> str:
    content = _read("src/launcher/config.py")
    m = re.search(r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert m, "VERSION constant not found in config.py"
    return m.group(1)


def _extract_pyproject_version() -> str:
    content = _read("pyproject.toml")
    m = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert m, "version field not found in pyproject.toml"
    return m.group(1)


def _extract_setup_iss_version() -> str:
    content = _read("src/installer/windows/setup.iss")
    m = re.search(r'^#define\s+MyAppVersion\s+"([^"]+)"', content, re.MULTILINE)
    assert m, "MyAppVersion not found in setup.iss"
    return m.group(1)


def _extract_dmg_version() -> str:
    content = _read("src/installer/macos/build_dmg.sh")
    m = re.search(r'^APP_VERSION="([^"]+)"', content, re.MULTILINE)
    assert m, "APP_VERSION not found in build_dmg.sh"
    return m.group(1)


def _extract_appimage_version() -> str:
    content = _read("src/installer/linux/build_appimage.sh")
    m = re.search(r'^APP_VERSION="([^"]+)"', content, re.MULTILINE)
    assert m, "APP_VERSION not found in build_appimage.sh"
    return m.group(1)


def _all_versions() -> dict:
    return {
        "config.py": _extract_config_version(),
        "pyproject.toml": _extract_pyproject_version(),
        "setup.iss": _extract_setup_iss_version(),
        "build_dmg.sh": _extract_dmg_version(),
        "build_appimage.sh": _extract_appimage_version(),
    }


# ---------------------------------------------------------------------------
# Semantic version format tests
# ---------------------------------------------------------------------------

def test_config_py_version_is_semver() -> None:
    """VERSION in config.py must match MAJOR.MINOR.PATCH semantic version format."""
    v = _extract_config_version()
    assert SEMVER_RE.match(v), f"config.py VERSION '{v}' is not valid semver"


def test_pyproject_toml_version_is_semver() -> None:
    """version in pyproject.toml must match MAJOR.MINOR.PATCH format."""
    v = _extract_pyproject_version()
    assert SEMVER_RE.match(v), f"pyproject.toml version '{v}' is not valid semver"


def test_setup_iss_version_is_semver() -> None:
    """MyAppVersion in setup.iss must match MAJOR.MINOR.PATCH format."""
    v = _extract_setup_iss_version()
    assert SEMVER_RE.match(v), f"setup.iss MyAppVersion '{v}' is not valid semver"


def test_build_dmg_sh_version_is_semver() -> None:
    """APP_VERSION in build_dmg.sh must match MAJOR.MINOR.PATCH format."""
    v = _extract_dmg_version()
    assert SEMVER_RE.match(v), f"build_dmg.sh APP_VERSION '{v}' is not valid semver"


def test_build_appimage_sh_version_is_semver() -> None:
    """APP_VERSION in build_appimage.sh must match MAJOR.MINOR.PATCH format."""
    v = _extract_appimage_version()
    assert SEMVER_RE.match(v), f"build_appimage.sh APP_VERSION '{v}' is not valid semver"


# ---------------------------------------------------------------------------
# Cross-file consistency
# ---------------------------------------------------------------------------

def test_all_five_locations_are_consistent() -> None:
    """All 5 version locations must agree on the same version string."""
    versions = _all_versions()
    unique = set(versions.values())
    assert len(unique) == 1, (
        "Version mismatch across files: " + ", ".join(f"{k}={v}" for k, v in versions.items())
    )


# ---------------------------------------------------------------------------
# Major-bump component validation
# ---------------------------------------------------------------------------

def test_version_major_component_is_2() -> None:
    """This is a major bump to 2.x.x — major component must be exactly 2."""
    versions = _all_versions()
    for name, v in versions.items():
        major = int(v.split(".")[0])
        assert major == EXPECTED_MAJOR, (
            f"{name}: major={major}, expected {EXPECTED_MAJOR}"
        )


def test_version_minor_component_is_0() -> None:
    """Major bump resets minor to 0 in all locations."""
    versions = _all_versions()
    for name, v in versions.items():
        minor = int(v.split(".")[1])
        assert minor == EXPECTED_MINOR, (
            f"{name}: minor={minor}, expected {EXPECTED_MINOR}"
        )


def test_version_patch_component_is_0() -> None:
    """Major bump resets patch to 0 in all locations."""
    versions = _all_versions()
    for name, v in versions.items():
        patch = int(v.split(".")[2])
        assert patch == EXPECTED_PATCH, (
            f"{name}: patch={patch}, expected {EXPECTED_PATCH}"
        )


# ---------------------------------------------------------------------------
# No stale intermediate versions
# ---------------------------------------------------------------------------

def test_no_stale_version_in_config_py() -> None:
    """config.py must not contain any stale version string in its VERSION line."""
    content = _read("src/launcher/config.py")
    for stale in STALE_VERSIONS:
        version_lines = [
            line for line in content.splitlines()
            if stale in line and "VERSION" in line
        ]
        assert not version_lines, (
            f"Stale version '{stale}' found in config.py VERSION line: {version_lines}"
        )


def test_no_stale_version_in_pyproject_toml() -> None:
    """pyproject.toml must not contain any stale version string in its version line."""
    content = _read("pyproject.toml")
    for stale in STALE_VERSIONS:
        version_lines = [
            line for line in content.splitlines()
            if stale in line and line.strip().startswith("version")
        ]
        assert not version_lines, (
            f"Stale version '{stale}' found in pyproject.toml version line: {version_lines}"
        )


def test_no_stale_version_in_setup_iss() -> None:
    """setup.iss must not contain any stale version string in MyAppVersion define."""
    content = _read("src/installer/windows/setup.iss")
    for stale in STALE_VERSIONS:
        version_lines = [
            line for line in content.splitlines()
            if stale in line and "MyAppVersion" in line
        ]
        assert not version_lines, (
            f"Stale version '{stale}' found in setup.iss MyAppVersion line: {version_lines}"
        )


def test_no_stale_version_in_build_dmg_sh() -> None:
    """build_dmg.sh must not contain any stale version in the APP_VERSION assignment."""
    content = _read("src/installer/macos/build_dmg.sh")
    for stale in STALE_VERSIONS:
        version_lines = [
            line for line in content.splitlines()
            if stale in line and line.strip().startswith("APP_VERSION=")
        ]
        assert not version_lines, (
            f"Stale version '{stale}' found in build_dmg.sh APP_VERSION line: {version_lines}"
        )


def test_no_stale_version_in_build_appimage_sh() -> None:
    """build_appimage.sh must not contain any stale version in the APP_VERSION assignment."""
    content = _read("src/installer/linux/build_appimage.sh")
    for stale in STALE_VERSIONS:
        version_lines = [
            line for line in content.splitlines()
            if stale in line and line.strip().startswith("APP_VERSION=")
        ]
        assert not version_lines, (
            f"Stale version '{stale}' found in build_appimage.sh APP_VERSION line: {version_lines}"
        )


# ---------------------------------------------------------------------------
# config.py module import sanity check
# ---------------------------------------------------------------------------

def test_config_module_version_importable() -> None:
    """config.py VERSION is importable as a Python attribute and returns 2.0.0."""
    import importlib.util
    config_path = REPO_ROOT / "src" / "launcher" / "config.py"
    spec = importlib.util.spec_from_file_location("launcher.config_fix020", config_path)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    assert hasattr(mod, "VERSION"), "config module has no VERSION attribute"
    assert mod.VERSION == EXPECTED_VERSION, (
        f"config.VERSION = '{mod.VERSION}', expected '{EXPECTED_VERSION}'"
    )
