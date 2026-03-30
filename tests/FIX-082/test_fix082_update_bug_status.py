"""Tests for FIX-082: update_bug_status.py script.

Tests cover:
- Successfully changes bug status from Fixed to Closed
- Prints correct before/after message
- Rejects invalid status value
- Errors on non-existent bug ID
- Accepts all 4 valid statuses: Open, In Progress, Fixed, Closed
"""
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import update_bug_status as ubs

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BUG_FIELDNAMES = [
    "ID", "Title", "Status", "Severity", "Reported By", "Description",
    "Steps to Reproduce", "Expected Behaviour", "Actual Behaviour",
    "Fixed In WP", "Comments",
]


def _make_bug(bug_id: str, status: str) -> dict:
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
        "Fixed In WP": "",
        "Comments": "",
    }


def _mock_read_csv(bugs: list[dict]):
    def _read(path, **kwargs):
        return BUG_FIELDNAMES, [dict(b) for b in bugs]
    return _read


# ---------------------------------------------------------------------------
# Status change tests
# ---------------------------------------------------------------------------

class TestUpdateBugStatus:

    def test_changes_status_from_fixed_to_closed(self):
        """Successfully updates bug status from Fixed to Closed."""
        bug = _make_bug("BUG-001", "Fixed")
        updated_rows = []

        with (
            patch.object(ubs, "read_csv", side_effect=_mock_read_csv([bug])),
            patch.object(ubs, "update_cell", side_effect=lambda *a, **kw: updated_rows.append((a[2], a[4]))),
        ):
            rc = ubs.main.__wrapped__() if hasattr(ubs.main, "__wrapped__") else None
            # Use argv patching
            with patch("sys.argv", ["update_bug_status.py", "BUG-001", "--status", "Closed"]):
                rc = ubs.main()

        assert rc == 0
        assert ("BUG-001", "Closed") in updated_rows

    def test_prints_before_after_message(self, capsys):
        """Prints before → after status message on success."""
        bug = _make_bug("BUG-001", "Fixed")

        with (
            patch.object(ubs, "read_csv", side_effect=_mock_read_csv([bug])),
            patch.object(ubs, "update_cell"),
            patch("sys.argv", ["update_bug_status.py", "BUG-001", "--status", "Closed"]),
        ):
            ubs.main()

        captured = capsys.readouterr()
        assert "BUG-001" in captured.out
        assert "Fixed" in captured.out
        assert "Closed" in captured.out
        assert "→" in captured.out

    def test_rejects_invalid_status(self, capsys):
        """Exits with error for invalid status value."""
        with patch("sys.argv", ["update_bug_status.py", "BUG-001", "--status", "Invalid"]):
            with pytest.raises(SystemExit) as exc_info:
                ubs.main()
        assert exc_info.value.code != 0

    def test_errors_on_nonexistent_bug_id(self, capsys):
        """Returns error code when bug ID is not found."""
        bug = _make_bug("BUG-001", "Fixed")

        with (
            patch.object(ubs, "read_csv", side_effect=_mock_read_csv([bug])),
            patch("sys.argv", ["update_bug_status.py", "BUG-999", "--status", "Closed"]),
        ):
            rc = ubs.main()

        assert rc == 1
        captured = capsys.readouterr()
        assert "BUG-999" in captured.err

    def test_accepts_status_open(self):
        """Accepts 'Open' as a valid status."""
        bug = _make_bug("BUG-002", "In Progress")
        updated_rows = []

        with (
            patch.object(ubs, "read_csv", side_effect=_mock_read_csv([bug])),
            patch.object(ubs, "update_cell", side_effect=lambda *a, **kw: updated_rows.append((a[2], a[4]))),
            patch("sys.argv", ["update_bug_status.py", "BUG-002", "--status", "Open"]),
        ):
            rc = ubs.main()

        assert rc == 0
        assert ("BUG-002", "Open") in updated_rows

    def test_accepts_status_in_progress(self):
        """Accepts 'In Progress' as a valid status."""
        bug = _make_bug("BUG-003", "Open")
        updated_rows = []

        with (
            patch.object(ubs, "read_csv", side_effect=_mock_read_csv([bug])),
            patch.object(ubs, "update_cell", side_effect=lambda *a, **kw: updated_rows.append((a[2], a[4]))),
            patch("sys.argv", ["update_bug_status.py", "BUG-003", "--status", "In Progress"]),
        ):
            rc = ubs.main()

        assert rc == 0
        assert ("BUG-003", "In Progress") in updated_rows

    def test_accepts_status_fixed(self):
        """Accepts 'Fixed' as a valid status."""
        bug = _make_bug("BUG-004", "In Progress")
        updated_rows = []

        with (
            patch.object(ubs, "read_csv", side_effect=_mock_read_csv([bug])),
            patch.object(ubs, "update_cell", side_effect=lambda *a, **kw: updated_rows.append((a[2], a[4]))),
            patch("sys.argv", ["update_bug_status.py", "BUG-004", "--status", "Fixed"]),
        ):
            rc = ubs.main()

        assert rc == 0
        assert ("BUG-004", "Fixed") in updated_rows

    def test_accepts_status_closed(self):
        """Accepts 'Closed' as a valid status."""
        bug = _make_bug("BUG-005", "Fixed")
        updated_rows = []

        with (
            patch.object(ubs, "read_csv", side_effect=_mock_read_csv([bug])),
            patch.object(ubs, "update_cell", side_effect=lambda *a, **kw: updated_rows.append((a[2], a[4]))),
            patch("sys.argv", ["update_bug_status.py", "BUG-005", "--status", "Closed"]),
        ):
            rc = ubs.main()

        assert rc == 0
        assert ("BUG-005", "Closed") in updated_rows
