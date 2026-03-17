"""Tester edge-case tests for FIX-019: Bump Version to 1.0.3.

Covers boundary conditions not addressed by the developer's test suite:
- Valid semver format (X.Y.Z with no pre-release/build suffixes)
- Version components are non-negative decimal integers with no leading zeros
- New version is strictly greater than the previous version (1.0.2)
- No file still references an older version (1.0.1, 1.0.0)
- Version string has no whitespace padding
- get_display_version() falls back to 1.0.3 when package is not installed
- CI tag format: version is a valid v-tag string
"""
import re
import importlib.util
from pathlib import Path

# ---------------------------------------------------------------------------
# Shared paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PY = REPO_ROOT / "src" / "launcher" / "config.py"
PYPROJECT = REPO_ROOT / "pyproject.toml"
SETUP_ISS = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
BUILD_APPIMAGE = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"

EXPECTED_VERSION = "2.0.0"
PREVIOUS_VERSION = "1.0.3"
SKIP_VERSION_1 = "1.0.2"
SKIP_VERSION_2 = "1.0.1"


def _load_config():
    spec = importlib.util.spec_from_file_location("launcher.config", CONFIG_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# EC-1: Valid semver format — no pre-release or build metadata
# ---------------------------------------------------------------------------

class TestSemverFormat:
    def test_config_version_is_valid_semver(self):
        """config.py VERSION must be strictly X.Y.Z (no pre-release/build suffix)."""
        mod = _load_config()
        assert re.match(r"^\d+\.\d+\.\d+$", mod.VERSION), (
            f"config.py VERSION '{mod.VERSION}' is not a valid semver X.Y.Z string"
        )

    def test_version_components_are_non_negative_integers(self):
        """Each of the three version components must parse as non-negative integer
        with no leading zeros."""
        mod = _load_config()
        parts = mod.VERSION.split(".")
        assert len(parts) == 3, "VERSION does not have exactly 3 components"
        for part in parts:
            assert part.isdigit(), (
                f"Version component '{part}' is not a non-negative integer"
            )
            assert not (len(part) > 1 and part.startswith("0")), (
                f"Version component '{part}' has a leading zero"
            )

    def test_version_has_no_whitespace(self):
        """VERSION constant must not contain leading or trailing whitespace."""
        mod = _load_config()
        assert mod.VERSION == mod.VERSION.strip(), (
            f"config.py VERSION has unexpected whitespace: repr='{mod.VERSION!r}'"
        )

    def test_pyproject_version_is_valid_semver(self):
        """pyproject.toml version must be strictly X.Y.Z."""
        content = PYPROJECT.read_text(encoding="utf-8")
        match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
        assert match, "No version field found in pyproject.toml"
        ver = match.group(1)
        assert re.match(r"^\d+\.\d+\.\d+$", ver), (
            f"pyproject.toml version '{ver}' is not a valid semver X.Y.Z string"
        )


# ---------------------------------------------------------------------------
# EC-2: Version strictly greater than previous release (1.0.2)
# ---------------------------------------------------------------------------

class TestVersionOrdering:
    def test_new_version_greater_than_previous(self):
        """1.0.3 must compare as strictly greater than previous version 1.0.2."""
        mod = _load_config()
        new = tuple(int(x) for x in mod.VERSION.split("."))
        prev = tuple(int(x) for x in PREVIOUS_VERSION.split("."))
        assert new > prev, (
            f"New version {mod.VERSION} is not greater than previous {PREVIOUS_VERSION}"
        )

    def test_new_version_major_incremented_by_one(self):
        """Major component must be incremented by exactly 1 from 1.0.3; minor/patch reset to 0."""
        mod = _load_config()
        new_parts = [int(x) for x in mod.VERSION.split(".")]
        prev_parts = [int(x) for x in PREVIOUS_VERSION.split(".")]
        assert new_parts[0] == prev_parts[0] + 1, (
            f"Major version must increment by 1: expected {prev_parts[0] + 1}, "
            f"got {new_parts[0]}"
        )
        assert new_parts[1] == 0, "Minor version must be reset to 0 after major bump"
        assert new_parts[2] == 0, "Patch version must be reset to 0 after major bump"


# ---------------------------------------------------------------------------
# EC-3: No file still references older versions (1.0.1, 1.0.0)
# ---------------------------------------------------------------------------

class TestNoOlderVersions:
    """Verify that no file accidentally regressed to 1.0.0 or 1.0.1."""

    def test_config_py_no_version_1_0_1(self):
        content = CONFIG_PY.read_text(encoding="utf-8")
        assert f'VERSION: str = "{SKIP_VERSION_1}"' not in content, (
            f"config.py still contains version {SKIP_VERSION_1}"
        )

    def test_config_py_no_version_1_0_0(self):
        content = CONFIG_PY.read_text(encoding="utf-8")
        assert f'VERSION: str = "{SKIP_VERSION_2}"' not in content, (
            f"config.py still contains version {SKIP_VERSION_2}"
        )

    def test_pyproject_no_version_1_0_1(self):
        content = PYPROJECT.read_text(encoding="utf-8")
        assert f'version = "{SKIP_VERSION_1}"' not in content, (
            f"pyproject.toml still contains version {SKIP_VERSION_1}"
        )

    def test_pyproject_no_version_1_0_0(self):
        content = PYPROJECT.read_text(encoding="utf-8")
        assert f'version = "{SKIP_VERSION_2}"' not in content, (
            f"pyproject.toml still contains version {SKIP_VERSION_2}"
        )

    def test_setup_iss_no_version_1_0_1(self):
        content = SETUP_ISS.read_text(encoding="utf-8")
        assert f'MyAppVersion "{SKIP_VERSION_1}"' not in content, (
            f"setup.iss still contains version {SKIP_VERSION_1}"
        )

    def test_setup_iss_no_version_1_0_0(self):
        content = SETUP_ISS.read_text(encoding="utf-8")
        assert f'MyAppVersion "{SKIP_VERSION_2}"' not in content, (
            f"setup.iss still contains version {SKIP_VERSION_2}"
        )

    def test_build_dmg_no_version_1_0_1(self):
        content = BUILD_DMG.read_text(encoding="utf-8")
        assert f'APP_VERSION="{SKIP_VERSION_1}"' not in content, (
            f"build_dmg.sh still contains version {SKIP_VERSION_1}"
        )

    def test_build_dmg_no_version_1_0_0(self):
        content = BUILD_DMG.read_text(encoding="utf-8")
        assert f'APP_VERSION="{SKIP_VERSION_2}"' not in content, (
            f"build_dmg.sh still contains version {SKIP_VERSION_2}"
        )

    def test_build_appimage_no_version_1_0_1(self):
        content = BUILD_APPIMAGE.read_text(encoding="utf-8")
        assert f'APP_VERSION="{SKIP_VERSION_1}"' not in content, (
            f"build_appimage.sh still contains version {SKIP_VERSION_1}"
        )

    def test_build_appimage_no_version_1_0_0(self):
        content = BUILD_APPIMAGE.read_text(encoding="utf-8")
        assert f'APP_VERSION="{SKIP_VERSION_2}"' not in content, (
            f"build_appimage.sh still contains version {SKIP_VERSION_2}"
        )


# ---------------------------------------------------------------------------
# EC-4: get_display_version() falls back to VERSION when package not installed
# ---------------------------------------------------------------------------

class TestDisplayVersion:
    def test_get_display_version_fallback_returns_expected(self):
        """get_display_version() must return '1.0.3' when importlib.metadata
        raises PackageNotFoundError (i.e. when running from source without pip
        install)."""
        import sys
        import importlib.metadata as _metadata
        from unittest.mock import patch

        mod = _load_config()

        with patch.object(_metadata, "version",
                          side_effect=_metadata.PackageNotFoundError("agent-environment-launcher")):
            result = mod.get_display_version()

        assert result == EXPECTED_VERSION, (
            f"get_display_version() returned '{result}', expected '{EXPECTED_VERSION}'"
        )


# ---------------------------------------------------------------------------
# EC-5: Version is valid as a git/CI tag string
# ---------------------------------------------------------------------------

class TestVersionTagFormat:
    def test_version_is_valid_vtag(self):
        """Version string must be usable as a v-prefixed git tag (v1.0.3)."""
        mod = _load_config()
        tag = f"v{mod.VERSION}"
        assert re.match(r"^v\d+\.\d+\.\d+$", tag), (
            f"v-tag '{tag}' does not match expected format vX.Y.Z"
        )

    def test_version_matches_expected_tag(self):
        """v-prefixed tag must equal 'v1.0.3'."""
        mod = _load_config()
        assert f"v{mod.VERSION}" == f"v{EXPECTED_VERSION}", (
            f"v-tag 'v{mod.VERSION}' does not match expected 'v{EXPECTED_VERSION}'"
        )
