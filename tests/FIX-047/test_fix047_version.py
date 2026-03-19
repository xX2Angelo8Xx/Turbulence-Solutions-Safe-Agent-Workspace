"""Tests for FIX-047 — Bump version to 3.0.0 (updated to 3.0.1 by FIX-048).

Verifies that all 5 canonical version locations contain "3.0.1"
and no longer contain "2.1.3".
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

CONFIG_PY = REPO_ROOT / "src" / "launcher" / "config.py"
PYPROJECT_TOML = REPO_ROOT / "pyproject.toml"
SETUP_ISS = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
BUILD_APPIMAGE = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"

TARGET_VERSION = "3.0.1"
OLD_VERSION = "2.1.3"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ── New version present ──────────────────────────────────────────────────────

def test_config_py_version():
    assert TARGET_VERSION in _read(CONFIG_PY)


def test_pyproject_toml_version():
    assert TARGET_VERSION in _read(PYPROJECT_TOML)


def test_setup_iss_version():
    assert TARGET_VERSION in _read(SETUP_ISS)


def test_build_dmg_sh_version():
    assert TARGET_VERSION in _read(BUILD_DMG)


def test_build_appimage_sh_version():
    assert TARGET_VERSION in _read(BUILD_APPIMAGE)


# ── Old version absent ───────────────────────────────────────────────────────

def test_no_old_version_config_py():
    assert OLD_VERSION not in _read(CONFIG_PY)


def test_no_old_version_pyproject():
    assert OLD_VERSION not in _read(PYPROJECT_TOML)


def test_no_old_version_setup_iss():
    assert OLD_VERSION not in _read(SETUP_ISS)


def test_no_old_version_build_dmg():
    assert OLD_VERSION not in _read(BUILD_DMG)


def test_no_old_version_build_appimage():
    assert OLD_VERSION not in _read(BUILD_APPIMAGE)


# ── Cross-file consistency ───────────────────────────────────────────────────

def test_version_consistency():
    """All 5 files must declare the same version."""
    import re

    def extract(path: Path, pattern: str) -> str:
        match = re.search(pattern, _read(path))
        assert match, f"Version pattern not found in {path.name}"
        return match.group(1)

    v_config = extract(CONFIG_PY, r'VERSION\s*:\s*str\s*=\s*"([^"]+)"')
    v_pyproject = extract(PYPROJECT_TOML, r'(?m)^version\s*=\s*"([^"]+)"')
    v_iss = extract(SETUP_ISS, r'#define\s+MyAppVersion\s+"([^"]+)"')
    v_dmg = extract(BUILD_DMG, r'(?m)^APP_VERSION="([^"]+)"')
    v_appimage = extract(BUILD_APPIMAGE, r'(?m)^APP_VERSION="([^"]+)"')

    versions = {
        "config.py": v_config,
        "pyproject.toml": v_pyproject,
        "setup.iss": v_iss,
        "build_dmg.sh": v_dmg,
        "build_appimage.sh": v_appimage,
    }
    unique = set(versions.values())
    assert len(unique) == 1, f"Version mismatch across files: {versions}"
    assert unique.pop() == TARGET_VERSION
