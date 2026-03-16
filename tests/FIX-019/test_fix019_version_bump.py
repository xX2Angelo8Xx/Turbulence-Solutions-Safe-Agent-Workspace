"""Tests for FIX-019: Bump Version to 1.0.3.

Verifies that all 5 version locations have been updated to 1.0.3 and that
all version strings are consistent with each other.
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths to files under test
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PY = REPO_ROOT / "src" / "launcher" / "config.py"
PYPROJECT = REPO_ROOT / "pyproject.toml"
SETUP_ISS = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
BUILD_APPIMAGE = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"

EXPECTED_VERSION = "1.0.3"


# ---------------------------------------------------------------------------
# AC1: config.py VERSION is "1.0.3"
# ---------------------------------------------------------------------------

class TestConfigVersion:
    def test_config_version_constant_is_1_0_3(self):
        """config.py VERSION constant must equal '1.0.3'."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("launcher.config", CONFIG_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.VERSION == EXPECTED_VERSION, (
            f"config.py VERSION is '{mod.VERSION}', expected '{EXPECTED_VERSION}'"
        )

    def test_config_py_contains_version_string(self):
        """config.py source file must contain VERSION: str = '1.0.3'."""
        content = CONFIG_PY.read_text(encoding="utf-8")
        assert f'VERSION: str = "{EXPECTED_VERSION}"' in content, (
            f"config.py does not contain VERSION: str = \"{EXPECTED_VERSION}\""
        )


# ---------------------------------------------------------------------------
# AC2: pyproject.toml version is "1.0.3"
# ---------------------------------------------------------------------------

class TestPyprojectVersion:
    def test_pyproject_version_is_1_0_3(self):
        """pyproject.toml [project] version must be '1.0.3'."""
        content = PYPROJECT.read_text(encoding="utf-8")
        assert f'version = "{EXPECTED_VERSION}"' in content, (
            f"pyproject.toml version is not '{EXPECTED_VERSION}'"
        )

    def test_pyproject_does_not_contain_old_version(self):
        """pyproject.toml must not still reference version 1.0.2."""
        content = PYPROJECT.read_text(encoding="utf-8")
        assert 'version = "1.0.2"' not in content, (
            "pyproject.toml still contains old version 1.0.2"
        )


# ---------------------------------------------------------------------------
# AC3: setup.iss MyAppVersion is "1.0.3"
# ---------------------------------------------------------------------------

class TestSetupIssVersion:
    def test_setup_iss_myappversion_is_1_0_3(self):
        """setup.iss #define MyAppVersion must be '1.0.3'."""
        content = SETUP_ISS.read_text(encoding="utf-8")
        assert f'MyAppVersion "{EXPECTED_VERSION}"' in content, (
            f"setup.iss MyAppVersion is not '{EXPECTED_VERSION}'"
        )

    def test_setup_iss_does_not_contain_old_version(self):
        """setup.iss must not still reference version 1.0.2."""
        content = SETUP_ISS.read_text(encoding="utf-8")
        assert 'MyAppVersion "1.0.2"' not in content, (
            "setup.iss still contains old MyAppVersion 1.0.2"
        )


# ---------------------------------------------------------------------------
# AC4: build_dmg.sh APP_VERSION is "1.0.3"
# ---------------------------------------------------------------------------

class TestBuildDmgVersion:
    def test_build_dmg_app_version_is_1_0_3(self):
        """build_dmg.sh APP_VERSION must be '1.0.3'."""
        content = BUILD_DMG.read_text(encoding="utf-8")
        assert f'APP_VERSION="{EXPECTED_VERSION}"' in content, (
            f"build_dmg.sh APP_VERSION is not '{EXPECTED_VERSION}'"
        )

    def test_build_dmg_does_not_contain_old_version(self):
        """build_dmg.sh must not still reference APP_VERSION 1.0.2."""
        content = BUILD_DMG.read_text(encoding="utf-8")
        assert 'APP_VERSION="1.0.2"' not in content, (
            "build_dmg.sh still contains old APP_VERSION 1.0.2"
        )


# ---------------------------------------------------------------------------
# AC5: build_appimage.sh APP_VERSION is "1.0.3"
# ---------------------------------------------------------------------------

class TestBuildAppimageVersion:
    def test_build_appimage_app_version_is_1_0_3(self):
        """build_appimage.sh APP_VERSION must be '1.0.3'."""
        content = BUILD_APPIMAGE.read_text(encoding="utf-8")
        assert f'APP_VERSION="{EXPECTED_VERSION}"' in content, (
            f"build_appimage.sh APP_VERSION is not '{EXPECTED_VERSION}'"
        )

    def test_build_appimage_does_not_contain_old_version(self):
        """build_appimage.sh must not still reference APP_VERSION 1.0.2."""
        content = BUILD_APPIMAGE.read_text(encoding="utf-8")
        assert 'APP_VERSION="1.0.2"' not in content, (
            "build_appimage.sh still contains old APP_VERSION 1.0.2"
        )


# ---------------------------------------------------------------------------
# AC6: All 5 version strings are identical (consistency check)
# ---------------------------------------------------------------------------

class TestVersionConsistency:
    def _get_config_version(self) -> str:
        content = CONFIG_PY.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("VERSION: str ="):
                return line.split('"')[1]
        raise ValueError("VERSION constant not found in config.py")

    def _get_pyproject_version(self) -> str:
        content = PYPROJECT.read_text(encoding="utf-8")
        in_project = False
        for line in content.splitlines():
            if line.strip() == "[project]":
                in_project = True
            elif in_project and line.startswith("version ="):
                return line.split('"')[1]
        raise ValueError("version field not found in [project] section of pyproject.toml")

    def _get_setup_iss_version(self) -> str:
        content = SETUP_ISS.read_text(encoding="utf-8")
        for line in content.splitlines():
            if "#define MyAppVersion" in line:
                return line.split('"')[1]
        raise ValueError("MyAppVersion not found in setup.iss")

    def _get_build_dmg_version(self) -> str:
        content = BUILD_DMG.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("APP_VERSION="):
                return line.split('"')[1]
        raise ValueError("APP_VERSION not found in build_dmg.sh")

    def _get_build_appimage_version(self) -> str:
        content = BUILD_APPIMAGE.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("APP_VERSION="):
                return line.split('"')[1]
        raise ValueError("APP_VERSION not found in build_appimage.sh")

    def test_all_five_versions_are_identical(self):
        """All 5 version references must be identical."""
        versions = {
            "config.py": self._get_config_version(),
            "pyproject.toml": self._get_pyproject_version(),
            "setup.iss": self._get_setup_iss_version(),
            "build_dmg.sh": self._get_build_dmg_version(),
            "build_appimage.sh": self._get_build_appimage_version(),
        }
        unique = set(versions.values())
        assert len(unique) == 1, (
            f"Version strings are inconsistent across files: {versions}"
        )

    def test_all_versions_equal_expected(self):
        """All 5 version references must equal '1.0.3'."""
        versions = {
            "config.py": self._get_config_version(),
            "pyproject.toml": self._get_pyproject_version(),
            "setup.iss": self._get_setup_iss_version(),
            "build_dmg.sh": self._get_build_dmg_version(),
            "build_appimage.sh": self._get_build_appimage_version(),
        }
        for source, version in versions.items():
            assert version == EXPECTED_VERSION, (
                f"{source} version is '{version}', expected '{EXPECTED_VERSION}'"
            )
