"""Tests for FIX-049: Fix version test regression pattern.

Verifies that:
1. tests/shared/version_utils.py exists and exports CURRENT_VERSION
2. CURRENT_VERSION dynamically matches src/launcher/config.py
3. CURRENT_VERSION is a valid semver string
4. The formerly-failing test files no longer hardcode the old version strings
"""
import importlib
import importlib.util
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PY = REPO_ROOT / "src" / "launcher" / "config.py"
SHARED_UTILS = REPO_ROOT / "tests" / "shared" / "version_utils.py"


def _read_config_version() -> str:
    text = CONFIG_PY.read_text(encoding="utf-8")
    match = re.search(r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match, "VERSION constant not found in config.py"
    return match.group(1)


class TestSharedVersionUtils:
    def test_shared_version_utils_exists(self):
        assert SHARED_UTILS.exists(), f"tests/shared/version_utils.py not found at {SHARED_UTILS}"

    def test_shared_init_exists(self):
        assert (REPO_ROOT / "tests" / "shared" / "__init__.py").exists(), \
            "tests/shared/__init__.py not found"

    def test_current_version_matches_config_py(self):
        sys.path.insert(0, str(REPO_ROOT))
        try:
            spec = importlib.util.spec_from_file_location("version_utils", SHARED_UTILS)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            config_ver = _read_config_version()
            assert mod.CURRENT_VERSION == config_ver, (
                f"version_utils.CURRENT_VERSION={mod.CURRENT_VERSION!r} "
                f"but config.py has {config_ver!r}"
            )
        finally:
            if str(REPO_ROOT) in sys.path:
                sys.path.remove(str(REPO_ROOT))

    def test_current_version_is_semver(self):
        version = _read_config_version()
        assert re.match(r"^\d+\.\d+\.\d+$", version), (
            f"CURRENT_VERSION {version!r} is not a valid semver (X.Y.Z)"
        )

    def test_current_version_is_not_empty(self):
        version = _read_config_version()
        assert version.strip() != "", "CURRENT_VERSION must not be empty"


class TestNoHardcodedStaleVersions:
    """Verify that the formerly-failing test files no longer hardcode stale version strings."""

    def _check_no_literal_assignment(self, filepath: Path, bad_versions: list):
        content = filepath.read_text(encoding="utf-8")
        for ver in bad_versions:
            pattern = f'EXPECTED_VERSION = "{ver}"'
            assert pattern not in content, (
                f"{filepath.name} still contains hardcoded: {pattern!r}"
            )

    def test_fix014_version_bump_no_hardcoded(self):
        self._check_no_literal_assignment(
            REPO_ROOT / "tests/FIX-014/test_fix014_version_bump.py",
            ["3.0.0", "2.0.1", "1.0.3"]
        )

    def test_fix014_edge_cases_no_hardcoded(self):
        self._check_no_literal_assignment(
            REPO_ROOT / "tests/FIX-014/test_fix014_edge_cases.py",
            ["3.0.0", "2.0.1", "1.0.3"]
        )

    def test_fix017_version_bump_no_hardcoded(self):
        self._check_no_literal_assignment(
            REPO_ROOT / "tests/FIX-017/test_fix017_version_bump.py",
            ["3.0.0", "2.0.1"]
        )

    def test_fix017_edge_cases_no_hardcoded(self):
        self._check_no_literal_assignment(
            REPO_ROOT / "tests/FIX-017/test_fix017_edge_cases.py",
            ["2.0.1", "3.0.0"]
        )

    def test_fix019_no_hardcoded(self):
        self._check_no_literal_assignment(
            REPO_ROOT / "tests/FIX-019/test_fix019_version_bump.py",
            ["3.0.0", "2.0.1"]
        )

    def test_fix020_no_hardcoded(self):
        self._check_no_literal_assignment(
            REPO_ROOT / "tests/FIX-020/test_fix020_version_bump.py",
            ["3.0.0", "2.0.1"]
        )

    def test_fix030_no_hardcoded(self):
        self._check_no_literal_assignment(
            REPO_ROOT / "tests/FIX-030/test_fix030_version_bump.py",
            ["3.0.0", "2.0.1"]
        )

    def test_fix036_no_hardcoded(self):
        self._check_no_literal_assignment(
            REPO_ROOT / "tests/FIX-036/test_fix036_version_consistency.py",
            ["3.0.0", "2.0.1"]
        )

    def test_fix045_no_hardcoded(self):
        self._check_no_literal_assignment(
            REPO_ROOT / "tests/FIX-045/test_fix045_version_consistency.py",
            ["3.0.0", "2.0.1"]
        )

    def test_ins005_no_hardcoded_2_0_1(self):
        content = (REPO_ROOT / "tests/INS-005/test_ins005_setup_iss.py").read_text(encoding="utf-8")
        assert "'MyAppVersion \"2.0.1\"'" not in content, \
            "INS-005 still hardcodes '2.0.1' in MyAppVersion assertion"

    def test_ins006_no_hardcoded_2_0_1(self):
        content = (REPO_ROOT / "tests/INS-006/test_ins006_build_dmg.py").read_text(encoding="utf-8")
        # "2.0.1" should not appear in the assert line
        for line in content.splitlines():
            if "assert" in line and "2.0.1" in line:
                assert False, f"INS-006 still hardcodes '2.0.1' in assertion: {line.strip()!r}"

    def test_ins007_no_hardcoded_2_0_1(self):
        content = (REPO_ROOT / "tests/INS-007/test_ins007_build_appimage.py").read_text(encoding="utf-8")
        for line in content.splitlines():
            if "assert" in line and "2.0.1" in line:
                assert False, f"INS-007 still hardcodes '2.0.1' in assertion: {line.strip()!r}"

    def test_fix010_no_hardcoded_2_0_1(self):
        content = (REPO_ROOT / "tests/FIX-010/test_fix010_cicd_pipeline.py").read_text(encoding="utf-8")
        for line in content.splitlines():
            if "assert" in line and "2.0.1" in line:
                assert False, f"FIX-010 still hardcodes '2.0.1' in assertion: {line.strip()!r}"
