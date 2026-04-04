"""Tests for FIX-090: Verify version string 3.3.1 in all 5 required locations."""

from pathlib import Path

from tests.shared.version_utils import CURRENT_VERSION

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_config_py_version():
    config = REPO_ROOT / "src" / "launcher" / "config.py"
    content = config.read_text(encoding="utf-8")
    assert f'VERSION: str = "{CURRENT_VERSION}"' in content, f"config.py must contain VERSION = '{CURRENT_VERSION}'"


def test_pyproject_toml_version():
    pyproject = REPO_ROOT / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")
    assert f'version = "{CURRENT_VERSION}"' in content, f"pyproject.toml must contain version = '{CURRENT_VERSION}'"


def test_setup_iss_version():
    setup_iss = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    content = setup_iss.read_text(encoding="utf-8")
    assert f'#define MyAppVersion "{CURRENT_VERSION}"' in content, f"setup.iss must contain MyAppVersion '{CURRENT_VERSION}'"


def test_build_dmg_sh_version():
    build_dmg = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
    content = build_dmg.read_text(encoding="utf-8")
    assert f'APP_VERSION="{CURRENT_VERSION}"' in content, f"build_dmg.sh must contain APP_VERSION='{CURRENT_VERSION}'"


def test_build_appimage_sh_version():
    build_appimage = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
    content = build_appimage.read_text(encoding="utf-8")
    assert f'APP_VERSION="{CURRENT_VERSION}"' in content, f"build_appimage.sh must contain APP_VERSION='{CURRENT_VERSION}'"


def test_no_old_version_in_config_py():
    config = REPO_ROOT / "src" / "launcher" / "config.py"
    content = config.read_text(encoding="utf-8")
    assert 'VERSION: str = "3.3.0"' not in content, "config.py must not contain old version 3.3.0"


def test_no_old_version_in_pyproject():
    pyproject = REPO_ROOT / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")
    assert 'version = "3.3.0"' not in content, "pyproject.toml must not contain old version 3.3.0"


def test_no_old_version_in_setup_iss():
    setup_iss = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    content = setup_iss.read_text(encoding="utf-8")
    assert '#define MyAppVersion "3.3.0"' not in content, "setup.iss must not contain old version 3.3.0"


def test_no_old_version_in_build_dmg():
    build_dmg = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
    content = build_dmg.read_text(encoding="utf-8")
    assert 'APP_VERSION="3.3.0"' not in content, "build_dmg.sh must not contain old version 3.3.0"


def test_no_old_version_in_build_appimage():
    build_appimage = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
    content = build_appimage.read_text(encoding="utf-8")
    assert 'APP_VERSION="3.3.0"' not in content, "build_appimage.sh must not contain old version 3.3.0"
