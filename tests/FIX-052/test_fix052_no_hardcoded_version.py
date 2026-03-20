"""Tests for FIX-052 — Regression guard: FIX-047 tests must not hardcode version strings.

Verifies that tests/FIX-047/test_fix047_version.py:
  1. Does not contain any hardcoded version literal (e.g. "3.0.0").
  2. Imports CURRENT_VERSION from the shared version_utils module.

This guards against future edits accidentally re-introducing hardcoded versions.
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIX047_TEST_FILE = REPO_ROOT / "tests" / "FIX-047" / "test_fix047_version.py"


def _read_source() -> str:
    return FIX047_TEST_FILE.read_text(encoding="utf-8")


def test_no_hardcoded_300_in_fix047_test():
    """The FIX-047 test file must not contain the hardcoded string '3.0.0'."""
    source = _read_source()
    assert "3.0.0" not in source, (
        "tests/FIX-047/test_fix047_version.py still contains hardcoded '3.0.0'. "
        "Use CURRENT_VERSION from tests/shared/version_utils.py instead."
    )


def test_fix047_imports_version_utils():
    """The FIX-047 test file must import from version_utils."""
    source = _read_source()
    assert "version_utils" in source, (
        "tests/FIX-047/test_fix047_version.py does not import from version_utils. "
        "Dynamic versioning must be used."
    )
    assert "CURRENT_VERSION" in source, (
        "tests/FIX-047/test_fix047_version.py does not use CURRENT_VERSION from version_utils."
    )


def test_fix047_tests_all_pass():
    """All FIX-047 tests must pass (integration check)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/FIX-047/", "-v", "--tb=short"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"FIX-047 tests failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "11 passed" in result.stdout, (
        f"Expected 11 passed tests in FIX-047, got:\n{result.stdout}"
    )
