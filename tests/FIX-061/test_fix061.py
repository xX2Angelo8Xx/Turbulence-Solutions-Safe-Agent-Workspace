"""Tests for FIX-061: Bump version to 3.1.0.

Verifies that all 5 version locations contain the current version string
as reported by tests/shared/version_utils.CURRENT_VERSION.
"""
import re
from pathlib import Path

import pytest

from tests.shared.version_utils import CURRENT_VERSION

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestVersionBump:
    def test_config_py_version(self):
        text = (REPO_ROOT / "src" / "launcher" / "config.py").read_text(encoding="utf-8")
        match = re.search(r'^VERSION\s*:\s*str\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        assert match, "VERSION constant not found in config.py"
        assert match.group(1) == CURRENT_VERSION, (
            f"config.py has {match.group(1)!r}, expected {CURRENT_VERSION!r}"
        )

    def test_pyproject_toml_version(self):
        text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        assert match, "version field not found in pyproject.toml"
        assert match.group(1) == CURRENT_VERSION, (
            f"pyproject.toml has {match.group(1)!r}, expected {CURRENT_VERSION!r}"
        )

    def test_setup_iss_version(self):
        text = (REPO_ROOT / "src" / "installer" / "windows" / "setup.iss").read_text(encoding="utf-8")
        match = re.search(r'#define\s+MyAppVersion\s+"([^"]+)"', text)
        assert match, "MyAppVersion not found in setup.iss"
        assert match.group(1) == CURRENT_VERSION, (
            f"setup.iss has {match.group(1)!r}, expected {CURRENT_VERSION!r}"
        )

    def test_build_dmg_sh_version(self):
        text = (REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh").read_text(encoding="utf-8")
        match = re.search(r'^APP_VERSION="([^"]+)"', text, re.MULTILINE)
        assert match, "APP_VERSION not found in build_dmg.sh"
        assert match.group(1) == CURRENT_VERSION, (
            f"build_dmg.sh has {match.group(1)!r}, expected {CURRENT_VERSION!r}"
        )

    def test_build_appimage_sh_version(self):
        text = (REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh").read_text(encoding="utf-8")
        match = re.search(r'^APP_VERSION="([^"]+)"', text, re.MULTILINE)
        assert match, "APP_VERSION not found in build_appimage.sh"
        assert match.group(1) == CURRENT_VERSION, (
            f"build_appimage.sh has {match.group(1)!r}, expected {CURRENT_VERSION!r}"
        )


class TestVersionEdgeCases:
    """Edge-case and consistency tests added by Tester Agent."""

    def _read_all_versions(self):
        """Return a dict of source → version string for all 5 canonical locations."""
        versions = {}

        text = (REPO_ROOT / "src" / "launcher" / "config.py").read_text(encoding="utf-8")
        m = re.search(r'^VERSION\s*:\s*str\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        versions["config.py"] = m.group(1) if m else None

        text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        m = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        versions["pyproject.toml"] = m.group(1) if m else None

        text = (REPO_ROOT / "src" / "installer" / "windows" / "setup.iss").read_text(encoding="utf-8")
        m = re.search(r'#define\s+MyAppVersion\s+"([^"]+)"', text)
        versions["setup.iss"] = m.group(1) if m else None

        text = (REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh").read_text(encoding="utf-8")
        m = re.search(r'^APP_VERSION="([^"]+)"', text, re.MULTILINE)
        versions["build_dmg.sh"] = m.group(1) if m else None

        text = (REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh").read_text(encoding="utf-8")
        m = re.search(r'^APP_VERSION="([^"]+)"', text, re.MULTILINE)
        versions["build_appimage.sh"] = m.group(1) if m else None

        return versions

    def test_version_semver_format(self):
        """CURRENT_VERSION must be a valid semantic version (MAJOR.MINOR.PATCH)."""
        assert re.fullmatch(r'\d+\.\d+\.\d+', CURRENT_VERSION), (
            f"CURRENT_VERSION {CURRENT_VERSION!r} is not a valid semver X.Y.Z string"
        )

    def test_all_five_files_consistent(self):
        """All 5 canonical version locations must contain exactly the same version string."""
        versions = self._read_all_versions()
        unique = set(versions.values())
        assert len(unique) == 1, (
            f"Version mismatch across files: {versions}"
        )
        assert unique.pop() == CURRENT_VERSION, (
            f"All files agree but value differs from CURRENT_VERSION ({CURRENT_VERSION!r}): {versions}"
        )

    def test_version_greater_than_predecessor(self):
        """The current version must be strictly greater than the previous release (3.0.3)."""
        from packaging.version import Version
        prev = Version("3.0.3")
        curr = Version(CURRENT_VERSION)
        assert curr > prev, (
            f"CURRENT_VERSION {CURRENT_VERSION!r} is not newer than predecessor 3.0.3"
        )

    def test_no_old_version_in_source_files(self):
        """None of the 5 version source files should reference the old version 3.0.3."""
        old_version = "3.0.3"
        source_files = [
            REPO_ROOT / "src" / "launcher" / "config.py",
            REPO_ROOT / "pyproject.toml",
            REPO_ROOT / "src" / "installer" / "windows" / "setup.iss",
            REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh",
            REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh",
        ]
        for f in source_files:
            text = f.read_text(encoding="utf-8")
            assert old_version not in text, (
                f"{f.name} still contains old version string {old_version!r}"
            )
