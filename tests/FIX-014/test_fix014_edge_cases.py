"""Edge-case tests for FIX-014: Bump Version to 1.0.1.

Covers scenarios beyond the Developer's baseline tests:
- get_display_version() fallback path
- Semver format validation
- Broader stale-version grep across src/ tree
- Version string is not empty / not whitespace
"""
import re
import sys
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PY = REPO_ROOT / "src" / "launcher" / "config.py"
PYPROJECT = REPO_ROOT / "pyproject.toml"
SETUP_ISS = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
BUILD_APPIMAGE = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
SRC_LAUNCHER_DIR = REPO_ROOT / "src" / "launcher"

EXPECTED_VERSION = "1.0.3"
OLD_VERSION = "1.0.0"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


# ---------------------------------------------------------------------------
# get_display_version() fallback path
# ---------------------------------------------------------------------------

class TestDisplayVersion:
    def _load_config(self):
        """Import config module fresh from disk."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("launcher.config_ev", CONFIG_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_get_display_version_fallback_when_package_not_installed(self):
        """When the package is not installed, get_display_version() must return VERSION."""
        # Patch importlib.metadata.version inside the config module to raise
        # PackageNotFoundError so the fallback branch is exercised.
        import importlib.metadata as meta
        from importlib.metadata import PackageNotFoundError as PNFE
        mod = self._load_config()
        with patch.object(meta, "version", side_effect=PNFE("not found")):
            result = mod.get_display_version()
        assert result == EXPECTED_VERSION, (
            f"get_display_version() fallback returned '{result}', expected '{EXPECTED_VERSION}'"
        )

    def test_get_display_version_returns_non_empty_string(self):
        """get_display_version() must always return a non-empty, non-whitespace string."""
        import importlib.metadata as meta
        from importlib.metadata import PackageNotFoundError as PNFE
        mod = self._load_config()
        # Test fallback path
        with patch.object(meta, "version", side_effect=PNFE("not found")):
            result = mod.get_display_version()
        assert isinstance(result, str), "get_display_version() must return a string"
        assert result.strip() != "", "get_display_version() must not return empty string"


# ---------------------------------------------------------------------------
# Semver format
# ---------------------------------------------------------------------------

class TestVersionFormat:
    def test_config_version_is_semver(self):
        """config.py VERSION must be a valid semver string (MAJOR.MINOR.PATCH)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("launcher.config_sv", CONFIG_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert SEMVER_RE.match(mod.VERSION), (
            f"config.py VERSION '{mod.VERSION}' is not valid semver (X.Y.Z)"
        )

    def test_pyproject_version_is_semver(self):
        """pyproject.toml version must be valid semver."""
        content = PYPROJECT.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("version = "):
                ver = line.split('"')[1]
                assert SEMVER_RE.match(ver), (
                    f"pyproject.toml version '{ver}' is not valid semver (X.Y.Z)"
                )
                return
        raise AssertionError("version field not found in pyproject.toml")

    def test_setup_iss_version_is_semver(self):
        """setup.iss MyAppVersion must be valid semver."""
        content = SETUP_ISS.read_text(encoding="utf-8")
        for line in content.splitlines():
            if "#define MyAppVersion" in line:
                ver = line.split('"')[1]
                assert SEMVER_RE.match(ver), (
                    f"setup.iss MyAppVersion '{ver}' is not valid semver (X.Y.Z)"
                )
                return
        raise AssertionError("MyAppVersion not found in setup.iss")

    def test_build_dmg_version_is_semver(self):
        """build_dmg.sh APP_VERSION must be valid semver."""
        content = BUILD_DMG.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("APP_VERSION="):
                ver = line.split('"')[1]
                assert SEMVER_RE.match(ver), (
                    f"build_dmg.sh APP_VERSION '{ver}' is not valid semver (X.Y.Z)"
                )
                return
        raise AssertionError("APP_VERSION not found in build_dmg.sh")

    def test_build_appimage_version_is_semver(self):
        """build_appimage.sh APP_VERSION must be valid semver."""
        content = BUILD_APPIMAGE.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("APP_VERSION="):
                ver = line.split('"')[1]
                assert SEMVER_RE.match(ver), (
                    f"build_appimage.sh APP_VERSION '{ver}' is not valid semver (X.Y.Z)"
                )
                return
        raise AssertionError("APP_VERSION not found in build_appimage.sh")


# ---------------------------------------------------------------------------
# Broad stale-version grep across src/launcher/ Python source
# ---------------------------------------------------------------------------

class TestNoStaleSourceReferences:
    def test_no_stale_version_in_config_py(self):
        """config.py must not contain the old version string '1.0.0' anywhere."""
        content = CONFIG_PY.read_text(encoding="utf-8")
        assert OLD_VERSION not in content, (
            f"config.py still contains stale version string '{OLD_VERSION}'"
        )

    def test_no_stale_version_in_pyproject(self):
        """pyproject.toml must not contain '1.0.0' anywhere."""
        content = PYPROJECT.read_text(encoding="utf-8")
        assert OLD_VERSION not in content, (
            f"pyproject.toml still contains stale version string '{OLD_VERSION}'"
        )

    def test_no_stale_version_in_setup_iss(self):
        """setup.iss must not contain '1.0.0' anywhere."""
        content = SETUP_ISS.read_text(encoding="utf-8")
        assert OLD_VERSION not in content, (
            f"setup.iss still contains stale version string '{OLD_VERSION}'"
        )

    def test_no_stale_version_in_build_dmg(self):
        """build_dmg.sh must not contain '1.0.0' anywhere."""
        content = BUILD_DMG.read_text(encoding="utf-8")
        assert OLD_VERSION not in content, (
            f"build_dmg.sh still contains stale version string '{OLD_VERSION}'"
        )

    def test_no_stale_version_in_build_appimage(self):
        """build_appimage.sh must not contain '1.0.0' anywhere."""
        content = BUILD_APPIMAGE.read_text(encoding="utf-8")
        assert OLD_VERSION not in content, (
            f"build_appimage.sh still contains stale version string '{OLD_VERSION}'"
        )

    def test_no_stale_version_across_launcher_python_sources(self):
        """No Python source file in src/launcher/ may contain '1.0.0'."""
        stale_files = []
        for py_file in SRC_LAUNCHER_DIR.rglob("*.py"):
            try:
                text = py_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if OLD_VERSION in text:
                stale_files.append(str(py_file.relative_to(REPO_ROOT)))
        assert not stale_files, (
            f"The following launcher Python files still contain '{OLD_VERSION}': "
            + ", ".join(stale_files)
        )
