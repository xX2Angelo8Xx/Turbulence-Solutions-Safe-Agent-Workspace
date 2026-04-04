"""Tester-added edge-case tests for FIX-082.

Covers:
- update_bug_status.py with --status "In Progress" (space in value)
- update_bug_status.py idempotent (Closed → Closed)
- --fix does NOT run when --wp is specified (pre-commit safety)
- --fix no-op: returns 0 and prints "Applied 0 fix(es)."
- validation-exceptions.json with unknown WP ID (silently ignored)
- Path traversal: apply_fixes() only deletes from docs/workpackages/
- Security: CSV-injection characters rejected via argparse choices
- Unicode bug IDs and titles handled without crash
"""
import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import update_bug_status as ubs
import validate_workspace as vw

# ---------------------------------------------------------------------------
# Helpers (mirrors those in developer tests)
# ---------------------------------------------------------------------------

BUG_FIELDNAMES = [
    "ID", "Title", "Status", "Severity", "Reported By", "Description",
    "Steps to Reproduce", "Expected Behaviour", "Actual Behaviour",
    "Fixed In WP", "Comments",
]

WP_FIELDNAMES = ["ID", "Title", "Description", "Status", "Assigned To",
                  "Acceptance Criteria", "Notes", "Dependencies", "Type",
                  "User Story", "Comments"]


def _make_bug(bug_id: str, status: str, fixed_in: str = "") -> dict:
    return {
        "ID": bug_id,
        "Title": f"Test bug {bug_id}",
        "Status": status,
        "Severity": "Medium",
        "Reported By": "Tester",
        "Description": "desc",
        "Steps to Reproduce": "steps",
        "Expected Behaviour": "expected",
        "Actual Behaviour": "actual",
        "Fixed In WP": fixed_in,
        "Comments": "",
    }


def _make_wp(wp_id: str, status: str) -> dict:
    return {k: "" for k in WP_FIELDNAMES} | {"ID": wp_id, "Status": status}


def _mock_read_jsonl(bugs: list[dict]):
    def _read(path, **kwargs):
        return BUG_FIELDNAMES, [dict(b) for b in bugs]
    return _read


def _mock_read_jsonl_factory(wps=None, bugs=None):
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
# update_bug_status.py edge cases
# ---------------------------------------------------------------------------

class TestUpdateBugStatusEdgeCases:

    def test_in_progress_status_with_space_accepted(self):
        """'In Progress' (two words) is accepted as a valid status."""
        bug = _make_bug("BUG-010", "Open")
        updated_cells = []

        with (
            patch.object(ubs, "read_jsonl", side_effect=_mock_read_jsonl([bug])),
            patch.object(ubs, "update_cell",
                         side_effect=lambda *a, **kw: updated_cells.append((a[2], a[4]))),
            patch("sys.argv", ["update_bug_status.py", "BUG-010", "--status", "In Progress"]),
        ):
            rc = ubs.main()

        assert rc == 0
        assert ("BUG-010", "In Progress") in updated_cells

    def test_idempotent_closed_to_closed(self):
        """Setting a Closed bug to Closed again succeeds without error."""
        bug = _make_bug("BUG-020", "Closed")
        updated_cells = []

        with (
            patch.object(ubs, "read_jsonl", side_effect=_mock_read_jsonl([bug])),
            patch.object(ubs, "update_cell",
                         side_effect=lambda *a, **kw: updated_cells.append((a[2], a[4]))),
            patch("sys.argv", ["update_bug_status.py", "BUG-020", "--status", "Closed"]),
        ):
            rc = ubs.main()

        assert rc == 0
        assert ("BUG-020", "Closed") in updated_cells

    def test_idempotent_prints_before_after_even_if_same(self, capsys):
        """Idempotent update still prints the status transition message."""
        bug = _make_bug("BUG-030", "Closed")

        with (
            patch.object(ubs, "read_jsonl", side_effect=_mock_read_jsonl([bug])),
            patch.object(ubs, "update_cell"),
            patch("sys.argv", ["update_bug_status.py", "BUG-030", "--status", "Closed"]),
        ):
            rc = ubs.main()

        captured = capsys.readouterr()
        assert rc == 0
        assert "BUG-030" in captured.out
        assert "→" in captured.out

    def test_csv_injection_characters_rejected_in_status(self):
        """Status value with CSV-injection characters is rejected by argparse choices."""
        with patch("sys.argv", ["update_bug_status.py", "BUG-001", "--status", "Closed,=cmd()"]):
            with pytest.raises(SystemExit) as exc_info:
                ubs.main()
        assert exc_info.value.code != 0

    def test_unicode_bug_id_not_found_does_not_crash(self, capsys):
        """Non-ASCII bug ID (not in CSV) returns exit code 1 without crashing."""
        bug = _make_bug("BUG-001", "Open")

        with (
            patch.object(ubs, "read_jsonl", side_effect=_mock_read_jsonl([bug])),
            patch("sys.argv", ["update_bug_status.py", "BUG-\u00e9\u00e0\u00fc", "--status", "Closed"]),
        ):
            rc = ubs.main()

        assert rc == 1

    def test_bug_id_with_leading_whitespace_stripped_and_matched(self, capsys):
        """Bug ID arg with leading/trailing spaces is stripped → matches correctly."""
        bug = _make_bug("BUG-001", "Open")
        updated_cells = []

        with (
            patch.object(ubs, "read_jsonl", side_effect=_mock_read_jsonl([bug])),
            patch.object(ubs, "update_cell",
                         side_effect=lambda *a, **kw: updated_cells.append((a[2], a[4]))),
            patch("sys.argv", ["update_bug_status.py", "  BUG-001  ", "--status", "Closed"]),
        ):
            # strip() in the script normalises "  BUG-001  " → "BUG-001" → found
            rc = ubs.main()

        assert rc == 0
        assert ("BUG-001", "Closed") in updated_cells


# ---------------------------------------------------------------------------
# validate_workspace.py --fix edge cases
# ---------------------------------------------------------------------------

class TestValidateFixEdgeCases:

    def test_fix_flag_with_wp_exits_code_1(self, capsys):
        """--fix with --wp prints error and exits 1 (pre-commit safety guard)."""
        with patch("sys.argv", ["validate_workspace.py", "--wp", "FIX-001", "--fix"]):
            rc = vw.main()

        assert rc == 1
        captured = capsys.readouterr()
        assert "ERROR" in captured.err or "error" in captured.err.lower()

    def test_fix_flag_with_wp_does_not_call_apply_fixes(self, capsys):
        """When --fix is rejected due to --wp, apply_fixes() is never called."""
        with (
            patch("sys.argv", ["validate_workspace.py", "--wp", "FIX-001", "--fix"]),
            patch.object(vw, "apply_fixes") as mock_apply,
        ):
            vw.main()

        mock_apply.assert_not_called()

    def test_fix_noop_prints_applied_zero(self, capsys, tmp_path):
        """--fix with nothing to fix prints 'Applied 0 fix(es).' and exits cleanly."""
        wp = _make_wp("FIX-TEST", "Done")
        bug = _make_bug("BUG-TEST", "Closed", fixed_in="FIX-TEST")

        with (
            patch("sys.argv", ["validate_workspace.py", "--full", "--fix"]),
            patch.object(vw, "apply_fixes", return_value=0) as mock_apply,
            patch.object(vw, "validate_full"),
        ):
            rc = vw.main()

        mock_apply.assert_called_once()
        captured = capsys.readouterr()
        assert "Applied 0 fix(es)." in captured.out

    def test_path_traversal_fix_only_touches_workpackages_dir(self, tmp_path):
        """apply_fixes() only deletes files under docs/workpackages/, not elsewhere."""
        wp = _make_wp("FIX-001", "Done")

        # Create an orphaned state file in the workpackages dir
        wp_dir = tmp_path / "docs" / "workpackages" / "FIX-001"
        wp_dir.mkdir(parents=True)
        legit_state = wp_dir / ".finalization-state.json"
        legit_state.write_text('{"state": "done"}', encoding="utf-8")

        # Create a decoy file OUTSIDE the workpackages dir
        outside_dir = tmp_path / "docs" / "outside"
        outside_dir.mkdir(parents=True)
        outside_file = outside_dir / ".finalization-state.json"
        outside_file.write_text('{"state": "done"}', encoding="utf-8")

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

        # Only the file in workpackages/ was touched
        assert not legit_state.exists(), "Orphaned state file in workpackages/ should be deleted"
        assert outside_file.exists(), "File outside workpackages/ must NOT be touched"
        assert fixes == 1

    def test_fix_does_not_close_open_bugs_without_fixed_status(self):
        """apply_fixes() does NOT close bugs that are 'Open' even if their WP is Done."""
        wp = _make_wp("FIX-001", "Done")
        bug = _make_bug("BUG-001", "Open", fixed_in="FIX-001")
        updated_cells = []

        with (
            patch.object(vw, "read_jsonl", side_effect=_mock_read_jsonl_factory(wps=[wp], bugs=[bug])),
            patch.object(vw, "update_cell",
                         side_effect=lambda *a, **kw: updated_cells.append((a[2], a[4]))),
            patch.object(vw, "REPO_ROOT", Path("/nonexistent/tmp")),
        ):
            vw.apply_fixes()

        assert ("BUG-001", "Closed") not in updated_cells

    def test_fix_does_not_close_verified_bugs(self):
        """apply_fixes() does NOT change 'Verified' bugs — only 'Fixed' ones."""
        wp = _make_wp("FIX-001", "Done")
        bug = _make_bug("BUG-001", "Verified", fixed_in="FIX-001")
        updated_cells = []

        with (
            patch.object(vw, "read_jsonl", side_effect=_mock_read_jsonl_factory(wps=[wp], bugs=[bug])),
            patch.object(vw, "update_cell",
                         side_effect=lambda *a, **kw: updated_cells.append((a[2], a[4]))),
            patch.object(vw, "REPO_ROOT", Path("/nonexistent/tmp")),
        ):
            vw.apply_fixes()

        assert ("BUG-001", "Closed") not in updated_cells


# ---------------------------------------------------------------------------
# validation-exceptions.json edge cases
# ---------------------------------------------------------------------------

class TestExceptionsJsonEdgeCases:

    def test_unknown_wp_id_in_exceptions_is_silently_ignored(self, tmp_path):
        """Unknown WP IDs in exceptions.json don't cause errors in validation."""
        exc_data = {
            "TOTALLY-UNKNOWN-WP": {"skip_checks": ["test-report"], "reason": "Does not exist"},
        }
        exc_file = tmp_path / "validation-exceptions.json"
        exc_file.write_text(json.dumps(exc_data), encoding="utf-8")

        with patch.object(vw, "EXCEPTIONS_JSON", exc_file):
            loaded = vw._load_exceptions()

        # Contains the unknown WP entry without error
        assert "TOTALLY-UNKNOWN-WP" in loaded

        # Validation of a real WP not in exceptions still works
        wp_folder = tmp_path / "docs" / "workpackages" / "FIX-001"
        wp_folder.mkdir(parents=True)
        (wp_folder / "dev-log.md").write_text("# dev log", encoding="utf-8")

        result = vw.ValidationResult()
        with patch.object(vw, "REPO_ROOT", tmp_path):
            vw._check_wp_artifacts("FIX-001", "Done", "", result, loaded)

        # FIX-001 is NOT in exceptions → both artifacts missing → errors expected
        assert any("test-report" in e for e in result.errors)

    def test_exceptions_json_with_empty_object_returns_empty(self, tmp_path):
        """Empty JSON object {} yields no exceptions (no entries)."""
        exc_file = tmp_path / "validation-exceptions.json"
        exc_file.write_text("{}", encoding="utf-8")

        with patch.object(vw, "EXCEPTIONS_JSON", exc_file):
            loaded = vw._load_exceptions()

        assert loaded == {}

    def test_exceptions_json_underscore_keys_filtered(self, tmp_path):
        """Keys starting with _ (schema metadata) are removed from the loaded dict."""
        exc_data = {
            "_schema": "https://example.com/schema",
            "_version": "1.0",
            "INS-008": {"skip_checks": ["test-report"], "reason": "Enabler WP"},
        }
        exc_file = tmp_path / "validation-exceptions.json"
        exc_file.write_text(json.dumps(exc_data), encoding="utf-8")

        with patch.object(vw, "EXCEPTIONS_JSON", exc_file):
            loaded = vw._load_exceptions()

        assert "_schema" not in loaded
        assert "_version" not in loaded
        assert "INS-008" in loaded

    def test_exceptions_json_read_permission_error_returns_empty(self, tmp_path):
        """An OSError while reading exceptions.json returns {} (graceful degradation)."""
        exc_file = tmp_path / "validation-exceptions.json"
        exc_file.write_text('{"MNT-001": {}}', encoding="utf-8")

        with (
            patch.object(vw, "EXCEPTIONS_JSON", exc_file),
            patch("pathlib.Path.read_text", side_effect=OSError("Permission denied")),
        ):
            loaded = vw._load_exceptions()

        assert loaded == {}
