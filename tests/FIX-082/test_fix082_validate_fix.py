"""Tests for FIX-082: validate_workspace.py --fix flag and exceptions.json support.

Tests cover:
- --fix deletes orphaned .finalization-state.json for Done WPs
- --fix closes Fixed bugs with Done WP
- --fix and --wp together produces an error
- --fix without orphans or Fixed bugs is a no-op
- validation-exceptions.json is loaded and applied correctly
- WPs in exceptions.json skip the correct checks
"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_workspace as vw

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WP_FIELDNAMES = ["ID", "Title", "Description", "Status", "Assigned To",
                  "Acceptance Criteria", "Notes", "Dependencies", "Type",
                  "User Story", "Comments"]

BUG_FIELDNAMES = ["ID", "Title", "Status", "Severity", "Reported By",
                  "Description", "Steps to Reproduce", "Expected Behaviour",
                  "Actual Behaviour", "Fixed In WP", "Comments"]


def _make_wp(wp_id: str, status: str, comments: str = "") -> dict:
    return {k: "" for k in WP_FIELDNAMES} | {"ID": wp_id, "Status": status, "Comments": comments}


def _make_bug(bug_id: str, status: str, fixed_in: str = "") -> dict:
    return {k: "" for k in BUG_FIELDNAMES} | {
        "ID": bug_id, "Status": status, "Fixed In WP": fixed_in
    }


def _mock_read_jsonl_factory(wps=None, bugs=None):
    """Return a read_csv mock that dispatches based on the path."""
    wps = wps or []
    bugs = bugs or []

    def _read(path, **kwargs):
        p = str(path)
        if "workpackages.jsonl" in p:
            return WP_FIELDNAMES, [dict(w) for w in wps]
        if "bugs.jsonl" in p:
            return BUG_FIELDNAMES, [dict(b) for b in bugs]
        return [], []

    return _read


# ---------------------------------------------------------------------------
# apply_fixes tests
# ---------------------------------------------------------------------------

class TestApplyFixes:

    def test_deletes_orphaned_state_file_for_done_wp(self, tmp_path):
        """--fix removes .finalization-state.json when WP is Done."""
        wp = _make_wp("FIX-001", "Done")

        # Create the orphaned file
        wp_dir = tmp_path / "docs" / "workpackages" / "FIX-001"
        wp_dir.mkdir(parents=True)
        state_file = wp_dir / ".finalization-state.json"
        state_file.write_text('{"state": "done"}', encoding="utf-8")

        # Create the JSONL file so WP_JSONL.exists() returns True
        wp_jsonl = tmp_path / "docs" / "workpackages" / "workpackages.jsonl"
        wp_jsonl.parent.mkdir(parents=True, exist_ok=True)
        wp_jsonl.touch()

        with (
            patch.object(vw, "read_jsonl", side_effect=_mock_read_jsonl_factory(wps=[wp])),
            patch.object(vw, "REPO_ROOT", tmp_path),
            patch.object(vw, "WP_JSONL", wp_jsonl),
            patch.object(vw, "BUG_JSONL", tmp_path / "docs" / "bugs" / "bugs.jsonl"),
        ):
            fixes = vw.apply_fixes()

        assert fixes == 1
        assert not state_file.exists()

    def test_closes_fixed_bug_with_done_wp(self):
        """--fix sets Fixed bug to Closed when Fixed In WP is Done."""
        wp = _make_wp("FIX-001", "Done")
        bug = _make_bug("BUG-001", "Fixed", fixed_in="FIX-001")
        updated_cells = []

        with (
            patch.object(vw, "read_jsonl", side_effect=_mock_read_jsonl_factory(wps=[wp], bugs=[bug])),
            patch.object(vw, "update_cell", side_effect=lambda *a, **kw: updated_cells.append((a[2], a[4]))),
            patch.object(vw, "REPO_ROOT", Path("/nonexistent/tmp")),
        ):
            # Glob returns no state files since path doesn't exist
            fixes = vw.apply_fixes()

        assert ("BUG-001", "Closed") in updated_cells
        assert fixes >= 1

    def test_skips_open_bug_that_is_not_fixed(self):
        """--fix does NOT close Open bugs (only Fixed ones)."""
        wp = _make_wp("FIX-001", "Done")
        bug = _make_bug("BUG-002", "Open", fixed_in="FIX-001")
        updated_cells = []

        with (
            patch.object(vw, "read_jsonl", side_effect=_mock_read_jsonl_factory(wps=[wp], bugs=[bug])),
            patch.object(vw, "update_cell", side_effect=lambda *a, **kw: updated_cells.append((a[2], a[4]))),
            patch.object(vw, "REPO_ROOT", Path("/nonexistent/tmp")),
        ):
            fixes = vw.apply_fixes()

        assert ("BUG-002", "Closed") not in updated_cells

    def test_noop_when_no_orphans_or_fixed_bugs(self):
        """--fix returns 0 when there is nothing to fix."""
        wp = _make_wp("FIX-001", "Done")
        bug = _make_bug("BUG-001", "Closed", fixed_in="FIX-001")

        with (
            patch.object(vw, "read_jsonl", side_effect=_mock_read_jsonl_factory(wps=[wp], bugs=[bug])),
            patch.object(vw, "update_cell"),
            patch.object(vw, "REPO_ROOT", Path("/nonexistent/tmp")),
        ):
            fixes = vw.apply_fixes()

        assert fixes == 0

    def test_fix_and_wp_together_produces_error(self, capsys):
        """--fix combined with --wp prints an error and exits with code 1."""
        with (
            patch("sys.argv", ["validate_workspace.py", "--wp", "FIX-001", "--fix"]),
        ):
            rc = vw.main()

        assert rc == 1
        captured = capsys.readouterr()
        assert "ERROR" in captured.err or "error" in captured.err.lower()


# ---------------------------------------------------------------------------
# validation-exceptions.json tests
# ---------------------------------------------------------------------------

class TestValidationExceptions:

    def test_exceptions_json_is_loaded(self, tmp_path):
        """_load_exceptions returns entries from validation-exceptions.json."""
        exc_data = {
            "_schema": "ignored",
            "MNT-001": {"skip_checks": ["test-report", "test-folder"], "reason": "Maintenance"},
        }
        exc_file = tmp_path / "validation-exceptions.json"
        exc_file.write_text(json.dumps(exc_data), encoding="utf-8")

        with patch.object(vw, "EXCEPTIONS_JSON", exc_file):
            loaded = vw._load_exceptions()

        assert "MNT-001" in loaded
        assert "_schema" not in loaded
        assert "test-report" in loaded["MNT-001"]["skip_checks"]

    def test_exceptions_json_missing_returns_empty(self, tmp_path):
        """_load_exceptions returns {} when file does not exist."""
        with patch.object(vw, "EXCEPTIONS_JSON", tmp_path / "nonexistent.json"):
            loaded = vw._load_exceptions()

        assert loaded == {}

    def test_exceptions_json_invalid_json_returns_empty(self, tmp_path):
        """_load_exceptions returns {} when file contains invalid JSON."""
        exc_file = tmp_path / "validation-exceptions.json"
        exc_file.write_text("not valid json {{", encoding="utf-8")

        with patch.object(vw, "EXCEPTIONS_JSON", exc_file):
            loaded = vw._load_exceptions()

        assert loaded == {}

    def test_wp_in_exceptions_skips_test_report_check(self, tmp_path):
        """WPs with test-report in skip_checks do not raise error for missing test-report.md."""
        wp_folder = tmp_path / "docs" / "workpackages" / "MNT-001"
        wp_folder.mkdir(parents=True)
        dev_log = wp_folder / "dev-log.md"
        dev_log.write_text("# dev log", encoding="utf-8")
        # No test-report.md — should be skipped by exception

        exceptions = {"MNT-001": {"skip_checks": ["test-report", "test-folder"]}}

        result = vw.ValidationResult()
        vw._check_wp_artifacts("MNT-001", "Done", "", result, exceptions)

        error_msgs = " ".join(result.errors)
        assert "test-report.md" not in error_msgs

    def test_wp_in_exceptions_skips_test_folder_check(self, tmp_path):
        """WPs with test-folder in skip_checks do not raise error for missing test dir."""
        wp_folder = tmp_path / "docs" / "workpackages" / "MNT-001"
        wp_folder.mkdir(parents=True)
        dev_log = wp_folder / "dev-log.md"
        dev_log.write_text("# dev log", encoding="utf-8")
        # No tests/MNT-001/ dir — should be skipped

        exceptions = {"MNT-001": {"skip_checks": ["test-report", "test-folder"]}}

        with patch.object(vw, "REPO_ROOT", tmp_path):
            result = vw.ValidationResult()
            vw._check_wp_artifacts("MNT-001", "Done", "", result, exceptions)

        error_msgs = " ".join(result.errors)
        assert "missing tests/" not in error_msgs

    def test_wp_not_in_exceptions_does_require_test_artifacts(self, tmp_path):
        """WPs not in exceptions.json do require test-report.md and test dir."""
        wp_folder = tmp_path / "docs" / "workpackages" / "FIX-001"
        wp_folder.mkdir(parents=True)
        dev_log = wp_folder / "dev-log.md"
        dev_log.write_text("# dev log", encoding="utf-8")
        # No test-report.md or tests dir

        exceptions = {}

        with patch.object(vw, "REPO_ROOT", tmp_path):
            result = vw.ValidationResult()
            vw._check_wp_artifacts("FIX-001", "Done", "", result, exceptions)

        assert any("test-report" in e for e in result.errors)
        assert any("tests/" in e for e in result.errors)
