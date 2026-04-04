"""Tests for FIX-099: validate_workspace.py artifact checks extended to Review WPs."""

import sys
from pathlib import Path

import pytest

# Make sure the scripts package is importable
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_workspace import ValidationResult, _check_wp_artifacts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_wp_tree(tmp_path: Path, *, has_devlog: bool, has_tests: bool, has_test_report: bool) -> Path:
    """Create a minimal fake WP directory tree under tmp_path."""
    wp_id = "TST-000"
    wp_folder = tmp_path / "docs" / "workpackages" / wp_id
    wp_folder.mkdir(parents=True)
    test_dir = tmp_path / "tests" / wp_id
    test_dir.mkdir(parents=True)

    if has_devlog:
        (wp_folder / "dev-log.md").write_text("# dev log", encoding="utf-8")
    if has_test_report:
        (wp_folder / "test-report.md").write_text("# test report", encoding="utf-8")
    if has_tests:
        (test_dir / "test_sample.py").write_text("def test_dummy(): pass", encoding="utf-8")

    return tmp_path


# ---------------------------------------------------------------------------
# Patch REPO_ROOT so the function resolves paths inside tmp_path
# ---------------------------------------------------------------------------

import validate_workspace as vw


def _run_check(monkeypatch, tmp_path, *, status: str, has_devlog: bool, has_tests: bool,
               has_test_report: bool, exceptions: dict | None = None):
    """Run _check_wp_artifacts against a fake repo rooted at tmp_path."""
    _make_wp_tree(tmp_path, has_devlog=has_devlog, has_tests=has_tests,
                  has_test_report=has_test_report)
    monkeypatch.setattr(vw, "REPO_ROOT", tmp_path)
    result = ValidationResult()
    _check_wp_artifacts("TST-000", status, "", result, exceptions or {})
    return result


# ---------------------------------------------------------------------------
# Review WP tests
# ---------------------------------------------------------------------------

def test_review_wp_missing_devlog_raises_error(tmp_path, monkeypatch):
    """A Review WP without dev-log.md must trigger an ERROR."""
    result = _run_check(monkeypatch, tmp_path, status="Review",
                        has_devlog=False, has_tests=True, has_test_report=False)
    assert any("dev-log.md" in e for e in result.errors), (
        f"Expected missing dev-log.md error, got errors={result.errors}"
    )


def test_review_wp_missing_tests_dir_raises_error(tmp_path, monkeypatch):
    """A Review WP without a tests/ directory must trigger an ERROR."""
    _make_wp_tree(tmp_path, has_devlog=True, has_tests=False, has_test_report=False)
    # Remove the tests directory entirely to simulate the missing-dir scenario
    import shutil
    shutil.rmtree(tmp_path / "tests" / "TST-000")
    monkeypatch.setattr(vw, "REPO_ROOT", tmp_path)
    result = ValidationResult()
    _check_wp_artifacts("TST-000", "Review", "", result, {})
    assert any("missing tests/TST-000" in e for e in result.errors), (
        f"Expected missing tests dir error, got errors={result.errors}"
    )


def test_review_wp_missing_test_py_raises_error(tmp_path, monkeypatch):
    """A Review WP with tests/ dir but no test_*.py must trigger an ERROR."""
    _make_wp_tree(tmp_path, has_devlog=True, has_tests=False, has_test_report=False)
    # tests dir exists (created by _make_wp_tree) but contains no test_*.py
    monkeypatch.setattr(vw, "REPO_ROOT", tmp_path)
    result = ValidationResult()
    _check_wp_artifacts("TST-000", "Review", "", result, {})
    assert any("no test_*.py" in e for e in result.errors), (
        f"Expected no test_*.py error, got errors={result.errors}"
    )


def test_review_wp_missing_test_report_no_error(tmp_path, monkeypatch):
    """A Review WP without test-report.md must NOT trigger an error (Tester creates it)."""
    result = _run_check(monkeypatch, tmp_path, status="Review",
                        has_devlog=True, has_tests=True, has_test_report=False)
    assert not any("test-report" in e for e in result.errors), (
        f"Unexpected test-report error for Review WP: errors={result.errors}"
    )


def test_review_wp_all_artifacts_present_no_error(tmp_path, monkeypatch):
    """A Review WP with dev-log.md and test_*.py must produce no errors."""
    result = _run_check(monkeypatch, tmp_path, status="Review",
                        has_devlog=True, has_tests=True, has_test_report=False)
    assert result.ok, f"Expected no errors, got: {result.errors}"


# ---------------------------------------------------------------------------
# Regression guard — Done WP behaviour unchanged
# ---------------------------------------------------------------------------

def test_done_wp_still_requires_test_report(tmp_path, monkeypatch):
    """A Done WP without test-report.md must still trigger an ERROR (regression guard)."""
    result = _run_check(monkeypatch, tmp_path, status="Done",
                        has_devlog=True, has_tests=True, has_test_report=False)
    assert any("test-report" in e for e in result.errors), (
        f"Expected test-report error for Done WP, got errors={result.errors}"
    )


def test_done_wp_missing_devlog_raises_error(tmp_path, monkeypatch):
    """A Done WP without dev-log.md must trigger an ERROR (regression guard)."""
    result = _run_check(monkeypatch, tmp_path, status="Done",
                        has_devlog=False, has_tests=True, has_test_report=True)
    assert any("dev-log.md" in e for e in result.errors), (
        f"Expected missing dev-log.md error for Done WP, got errors={result.errors}"
    )


def test_open_wp_not_checked(tmp_path, monkeypatch):
    """An Open WP should not be checked for artifacts at all."""
    # No files created — if the check ran it would error
    monkeypatch.setattr(vw, "REPO_ROOT", tmp_path)
    result = ValidationResult()
    _check_wp_artifacts("TST-000", "Open", "", result, {})
    assert result.ok, f"Open WP should not trigger errors, got: {result.errors}"


def test_in_progress_wp_not_checked(tmp_path, monkeypatch):
    """An In Progress WP should not be checked for artifacts."""
    monkeypatch.setattr(vw, "REPO_ROOT", tmp_path)
    result = ValidationResult()
    _check_wp_artifacts("TST-000", "In Progress", "", result, {})
    assert result.ok, f"In Progress WP should not trigger errors, got: {result.errors}"


# ---------------------------------------------------------------------------
# Tester edge-case additions
# ---------------------------------------------------------------------------

def test_review_wp_decomposed_comment_skipped(tmp_path, monkeypatch):
    """A Review WP whose comments contain 'decomposed' is skipped entirely."""
    # No artifact files created — if the check ran it would error
    monkeypatch.setattr(vw, "REPO_ROOT", tmp_path)
    result = ValidationResult()
    _check_wp_artifacts("TST-000", "Review", "decomposed into sub-WPs", result, {})
    assert result.ok, f"Decomposed Review WP should be skipped, got: {result.errors}"


def test_review_wp_tmp_file_raises_error(tmp_path, monkeypatch):
    """A Review WP with a tmp_ file in tests/ must trigger an ERROR."""
    _make_wp_tree(tmp_path, has_devlog=True, has_tests=True, has_test_report=False)
    (tmp_path / "tests" / "TST-000" / "tmp_scratch.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(vw, "REPO_ROOT", tmp_path)
    result = ValidationResult()
    _check_wp_artifacts("TST-000", "Review", "", result, {})
    assert any("tmp_" in e for e in result.errors), (
        f"Expected leftover tmp_ error, got errors={result.errors}"
    )


def test_review_wp_exception_skip_test_folder(tmp_path, monkeypatch):
    """A Review WP with skip_checks=[test-folder] must not error on missing tests/."""
    _make_wp_tree(tmp_path, has_devlog=True, has_tests=False, has_test_report=False)
    import shutil
    shutil.rmtree(tmp_path / "tests" / "TST-000")
    monkeypatch.setattr(vw, "REPO_ROOT", tmp_path)
    result = ValidationResult()
    exceptions = {"TST-000": {"skip_checks": ["test-folder"]}}
    _check_wp_artifacts("TST-000", "Review", "", result, exceptions)
    assert not any("tests/" in e for e in result.errors), (
        f"Excepted test-folder check should be skipped, got: {result.errors}"
    )
