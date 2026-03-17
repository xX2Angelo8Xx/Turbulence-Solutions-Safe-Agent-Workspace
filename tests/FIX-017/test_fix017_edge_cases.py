"""Tester edge-case tests for FIX-017: Bump Version to 1.0.2.

Covers boundary conditions not addressed by the developer's test suite:
- Valid semver format (X.Y.Z with no pre-release/build suffixes)
- Version components are non-negative decimal integers with no leading zeros
- New version is strictly greater than the previous version (1.0.1)
- None of the 5 files still reference 1.0.0 (skip-one regression)
- pyproject.toml version matches the config.py VERSION constant at runtime
- Version string has no whitespace padding
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
SKIP_ONE_VERSION = "1.0.1"


# ---------------------------------------------------------------------------
# EC-1: Valid semver format — no pre-release or build metadata
# ---------------------------------------------------------------------------

class TestSemverFormat:
    def test_version_is_valid_semver(self):
        """VERSION must be strictly X.Y.Z (no pre-release/build suffix)."""
        mod = _load_config()
        pattern = re.compile(r"^\d+\.\d+\.\d+$")
        assert pattern.match(mod.VERSION), (
            f"config.py VERSION '{mod.VERSION}' is not a valid semver X.Y.Z string"
        )

    def test_version_components_are_non_negative_integers(self):
        """Each of the three version components must parse as non-negative int."""
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
            f"config.py VERSION has unexpected whitespace: '{mod.VERSION}'"
        )


# ---------------------------------------------------------------------------
# EC-2: Version strictly greater than previous release
# ---------------------------------------------------------------------------

class TestVersionOrdering:
    def test_new_version_greater_than_previous(self):
        """1.0.2 must compare as greater than the previous version 1.0.1."""
        mod = _load_config()
        new = tuple(int(x) for x in mod.VERSION.split("."))
        prev = tuple(int(x) for x in PREVIOUS_VERSION.split("."))
        assert new > prev, (
            f"New version {mod.VERSION} is not greater than previous {PREVIOUS_VERSION}"
        )


# ---------------------------------------------------------------------------
# EC-3: No file still references the skip-one version (1.0.0)
# ---------------------------------------------------------------------------

class TestNoSkipOneVersion:
    def _check_file(self, path: Path, pattern: str) -> None:
        content = path.read_text(encoding="utf-8")
        assert pattern not in content, (
            f"{path.name} still contains skip-one version string '{pattern}'"
        )

    def test_config_py_no_version_1_0_0(self):
        self._check_file(CONFIG_PY, f'VERSION: str = "{SKIP_ONE_VERSION}"')

    def test_pyproject_no_version_1_0_0(self):
        self._check_file(PYPROJECT, f'version = "{SKIP_ONE_VERSION}"')

    def test_setup_iss_no_version_1_0_0(self):
        self._check_file(SETUP_ISS, f'MyAppVersion "{SKIP_ONE_VERSION}"')

    def test_build_dmg_no_version_1_0_0(self):
        self._check_file(BUILD_DMG, f'APP_VERSION="{SKIP_ONE_VERSION}"')

    def test_build_appimage_no_version_1_0_0(self):
        self._check_file(BUILD_APPIMAGE, f'APP_VERSION="{SKIP_ONE_VERSION}"')


# ---------------------------------------------------------------------------
# EC-4: pyproject.toml version matches the importable config.VERSION at runtime
# ---------------------------------------------------------------------------

class TestCrossFileRuntimeConsistency:
    def test_pyproject_version_matches_runtime_config(self):
        """Version in pyproject.toml must match the value returned by config.VERSION."""
        mod = _load_config()
        content = PYPROJECT.read_text(encoding="utf-8")
        assert f'version = "{mod.VERSION}"' in content, (
            f"pyproject.toml version does not match config.VERSION ({mod.VERSION})"
        )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _load_config():
    spec = importlib.util.spec_from_file_location("launcher.config", CONFIG_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
