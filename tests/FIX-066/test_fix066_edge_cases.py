"""Edge-case tests for FIX-066: Bug lifecycle automation — tester-added.

Covers gaps identified during review:
1. Bug with 'Fixed' status in dev-log (should be skipped)
2. Non-existent bug ID referenced in dev-log (should not crash)
3. Bug referenced in both dev-log and test-report (dedup — closed once)
4. Multiple bugs in same document
5. Phase 1 + Phase 2 overlap (bug matched by both — processed once)
6. _check_bug_linkage: bug with Fixed In WP set to a different (non-substring) WP
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))


# ---------------------------------------------------------------------------
# Helpers (duplicated here so this file can run standalone)
# ---------------------------------------------------------------------------

def _make_bug_jsonl(tmp_path: Path, bugs: list) -> Path:
    fieldnames = ["ID", "Title", "Status", "Severity", "Reported By",
                  "Description", "Steps to Reproduce", "Expected Behaviour",
                  "Actual Behaviour", "Fixed In WP", "Comments"]
    jsonl_path = tmp_path / "docs" / "bugs" / "bugs.jsonl"
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for bug in bugs:
            row = {fn: "" for fn in fieldnames}
            row.update(bug)
            f.write(json.dumps(row) + "\n")
    return jsonl_path


def _make_wp_folder(tmp_path: Path, wp_id: str,
                    dev_log_content: str = "", test_report_content: str = "") -> Path:
    wp_folder = tmp_path / "docs" / "workpackages" / wp_id
    wp_folder.mkdir(parents=True, exist_ok=True)
    if dev_log_content:
        (wp_folder / "dev-log.md").write_text(dev_log_content, encoding="utf-8")
    if test_report_content:
        (wp_folder / "test-report.md").write_text(test_report_content, encoding="utf-8")
    return wp_folder


def _read_bug_row(jsonl_path: Path, bug_id: str) -> dict:
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                row = json.loads(line)
                if row.get("ID") == bug_id:
                    return row
    return {}


# ---------------------------------------------------------------------------
# Edge cases for _cascade_bug_status() Phase 2
# ---------------------------------------------------------------------------

class TestCascadeBugStatusEdgeCases:

    def test_fixed_status_bug_is_closed(self, tmp_path: Path) -> None:
        """Bug with 'Fixed' status referenced in dev-log IS auto-closed.

        FIX-081 corrected the Phase 2 filter to include 'Fixed' status.
        An already-set Fixed In WP is preserved; status becomes Closed.
        """
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-110", "Status": "Fixed", "Fixed In WP": "FIX-040"},
        ])
        _make_wp_folder(tmp_path, "FIX-050",
                        dev_log_content="Related work: see BUG-110.")

        with patch("finalize_wp.REPO_ROOT", tmp_path), \
             patch("finalize_wp.BUG_JSONL", bug_jsonl):
            from finalize_wp import _cascade_bug_status
            _cascade_bug_status("FIX-050", dry_run=False)

        bug = _read_bug_row(bug_jsonl, "BUG-110")
        assert bug["Status"] == "Closed"         # FIX-081: Fixed bugs are now closed
        assert bug["Fixed In WP"] == "FIX-040"   # existing Fixed In WP preserved

    def test_nonexistent_bug_id_in_dev_log_no_crash(self, tmp_path: Path) -> None:
        """Dev-log references a bug ID that doesn't exist — must not raise."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [])  # empty bugs.csv
        _make_wp_folder(tmp_path, "FIX-050",
                        dev_log_content="References BUG-999 which was once seen.")

        with patch("finalize_wp.REPO_ROOT", tmp_path), \
             patch("finalize_wp.BUG_JSONL", bug_jsonl):
            from finalize_wp import _cascade_bug_status
            # Should not raise
            _cascade_bug_status("FIX-050", dry_run=False)

    def test_bug_in_both_dev_log_and_test_report_closed_once(self, tmp_path: Path) -> None:
        """Same bug in both files is de-duplicated by the set and closed exactly once."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-111", "Status": "Open", "Fixed In WP": ""},
        ])
        _make_wp_folder(
            tmp_path, "FIX-050",
            dev_log_content="Fixed BUG-111 here.",
            test_report_content="Confirmed BUG-111 resolved.",
        )

        with patch("finalize_wp.REPO_ROOT", tmp_path), \
             patch("finalize_wp.BUG_JSONL", bug_jsonl):
            from finalize_wp import _cascade_bug_status
            _cascade_bug_status("FIX-050", dry_run=False)

        bug = _read_bug_row(bug_jsonl, "BUG-111")
        assert bug["Status"] == "Closed"
        assert bug["Fixed In WP"] == "FIX-050"

        # Verify no duplicate rows introduced
        with open(bug_jsonl, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        bug_rows = [r for r in rows if r["ID"] == "BUG-111"]
        assert len(bug_rows) == 1, "Bug ID should not be duplicated in JSONL"

    def test_multiple_bugs_in_dev_log_all_closed(self, tmp_path: Path) -> None:
        """Multiple bug references in dev-log are all auto-closed."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-120", "Status": "Open", "Fixed In WP": ""},
            {"ID": "BUG-121", "Status": "In Progress", "Fixed In WP": ""},
            {"ID": "BUG-122", "Status": "Open", "Fixed In WP": ""},
        ])
        _make_wp_folder(
            tmp_path, "FIX-050",
            dev_log_content="Resolved BUG-120, BUG-121, and BUG-122 in this WP.",
        )

        with patch("finalize_wp.REPO_ROOT", tmp_path), \
             patch("finalize_wp.BUG_JSONL", bug_jsonl):
            from finalize_wp import _cascade_bug_status
            _cascade_bug_status("FIX-050", dry_run=False)

        for bug_id in ("BUG-120", "BUG-121", "BUG-122"):
            bug = _read_bug_row(bug_jsonl, bug_id)
            assert bug["Status"] == "Closed", f"{bug_id} should be Closed"
            assert bug["Fixed In WP"] == "FIX-050"

    def test_phase1_and_phase2_overlap_bug_closed_once(self, tmp_path: Path) -> None:
        """Bug matched by Phase 1 (Fixed In WP) AND referenced in dev-log.

        The already_closed set prevents Phase 2 from re-processing the same bug.
        """
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-130", "Status": "Open", "Fixed In WP": "FIX-050"},
        ])
        _make_wp_folder(
            tmp_path, "FIX-050",
            dev_log_content="This WP addresses BUG-130 directly.",
        )

        with patch("finalize_wp.REPO_ROOT", tmp_path), \
             patch("finalize_wp.BUG_JSONL", bug_jsonl):
            from finalize_wp import _cascade_bug_status
            _cascade_bug_status("FIX-050", dry_run=False)

        bug = _read_bug_row(bug_jsonl, "BUG-130")
        assert bug["Status"] == "Closed"
        assert bug["Fixed In WP"] == "FIX-050"

        # Confirm no double-entry in JSONL
        with open(bug_jsonl, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        assert len([r for r in rows if r["ID"] == "BUG-130"]) == 1

    def test_empty_bug_status_is_skipped(self, tmp_path: Path) -> None:
        """Bug with empty Status is skipped (neither Open nor In Progress)."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-140", "Status": "", "Fixed In WP": ""},
        ])
        _make_wp_folder(tmp_path, "FIX-050",
                        dev_log_content="See BUG-140.")

        with patch("finalize_wp.REPO_ROOT", tmp_path), \
             patch("finalize_wp.BUG_JSONL", bug_jsonl):
            from finalize_wp import _cascade_bug_status
            _cascade_bug_status("FIX-050", dry_run=False)

        bug = _read_bug_row(bug_jsonl, "BUG-140")
        # Empty status is not "Open" or "In Progress" — should not be touched
        assert bug["Status"] == ""


# ---------------------------------------------------------------------------
# Edge cases for _check_bug_linkage()
# ---------------------------------------------------------------------------

class TestCheckBugLinkageEdgeCases:

    def test_no_warning_when_fixed_in_wp_is_different_non_substring(self, tmp_path: Path) -> None:
        """Bug linked to a completely different WP ID still triggers a warning."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-088", "Status": "Open", "Fixed In WP": "FIX-099"},
        ])
        _make_wp_folder(tmp_path, "FIX-050",
                        dev_log_content="Fixed BUG-088 during this WP.")

        with patch("validate_workspace.REPO_ROOT", tmp_path), \
             patch("validate_workspace.BUG_JSONL", bug_jsonl):
            from validate_workspace import _check_bug_linkage, ValidationResult
            result = ValidationResult()
            _check_bug_linkage("FIX-050", result)

        # FIX-099 != FIX-050, and "FIX-050" not in "FIX-099" → should warn
        assert len(result.warnings) == 1
        assert "BUG-088" in result.warnings[0]

    def test_multiple_bugs_referenced_some_linked_some_not(self, tmp_path: Path) -> None:
        """Only unlinked bugs produce warnings; linked ones are silent."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-200", "Status": "Open", "Fixed In WP": "FIX-050"},  # linked
            {"ID": "BUG-201", "Status": "Open", "Fixed In WP": ""},          # unlinked
        ])
        _make_wp_folder(tmp_path, "FIX-050",
                        dev_log_content="Addresses BUG-200 and BUG-201.")

        with patch("validate_workspace.REPO_ROOT", tmp_path), \
             patch("validate_workspace.BUG_JSONL", bug_jsonl):
            from validate_workspace import _check_bug_linkage, ValidationResult
            result = ValidationResult()
            _check_bug_linkage("FIX-050", result)

        # Only the unlinked BUG-201 should generate a warning
        assert len(result.warnings) == 1
        assert "BUG-201" in result.warnings[0]
        assert "BUG-200" not in result.warnings[0]

    def test_nonexistent_bug_referenced_in_dev_log_no_crash(self, tmp_path: Path) -> None:
        """_check_bug_linkage gracefully handles a bug ID not in bugs.csv."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [])  # empty
        _make_wp_folder(tmp_path, "FIX-050",
                        dev_log_content="References BUG-999 which is unknown.")

        with patch("validate_workspace.REPO_ROOT", tmp_path), \
             patch("validate_workspace.BUG_JSONL", bug_jsonl):
            from validate_workspace import _check_bug_linkage, ValidationResult
            result = ValidationResult()
            _check_bug_linkage("FIX-050", result)

        # No bug entry found → no warning (can't validate what doesn't exist)
        assert len(result.warnings) == 0
        assert len(result.errors) == 0


# ---------------------------------------------------------------------------
# Edge cases for _check_bug_status_enum()
# ---------------------------------------------------------------------------

class TestBugStatusEnumEdgeCases:

    def test_empty_status_is_not_flagged(self, tmp_path: Path) -> None:
        """Bug with empty Status is not flagged (only non-empty invalid values are)."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-300", "Status": ""},
        ])

        with patch("validate_workspace.BUG_JSONL", bug_jsonl):
            from validate_workspace import _check_bug_status_enum, ValidationResult
            result = ValidationResult()
            _check_bug_status_enum(result)

        # Empty status passes through (no warning)
        assert len(result.warnings) == 0

    def test_multiple_invalid_statuses_all_flagged(self, tmp_path: Path) -> None:
        """Multiple non-standard bug statuses are all individually warned."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-301", "Status": "Wontfix"},
            {"ID": "BUG-302", "Status": "Duplicate"},
            {"ID": "BUG-303", "Status": "Open"},  # valid
        ])

        with patch("validate_workspace.BUG_JSONL", bug_jsonl):
            from validate_workspace import _check_bug_status_enum, ValidationResult
            result = ValidationResult()
            _check_bug_status_enum(result)

        assert len(result.warnings) == 2
        warned_ids = " ".join(result.warnings)
        assert "BUG-301" in warned_ids
        assert "BUG-302" in warned_ids
        assert "BUG-303" not in warned_ids  # valid, must not appear
