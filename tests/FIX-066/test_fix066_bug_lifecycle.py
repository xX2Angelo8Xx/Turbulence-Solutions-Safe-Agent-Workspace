"""Tests for FIX-066: Bug lifecycle automation in finalization.

Tests cover:
1. _cascade_bug_status() finds bug refs in dev-log.md and auto-closes them
2. _cascade_bug_status() respects dry-run mode
3. _cascade_bug_status() doesn't close already-Closed bugs
4. _check_bug_linkage() warns about unlinked bugs
5. _check_bug_status_enum() is already covered by FIX-065's _check_jsonl_structural()
"""

import json
import re
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bug_jsonl(tmp_path: Path, bugs: list) -> Path:
    """Create a minimal bugs.jsonl in tmp_path."""
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
    """Create the WP docs folder with optional dev-log.md and test-report.md."""
    wp_folder = tmp_path / "docs" / "workpackages" / wp_id
    wp_folder.mkdir(parents=True, exist_ok=True)
    if dev_log_content:
        (wp_folder / "dev-log.md").write_text(dev_log_content, encoding="utf-8")
    if test_report_content:
        (wp_folder / "test-report.md").write_text(test_report_content, encoding="utf-8")
    return wp_folder


def _read_bug_status(jsonl_path: Path, bug_id: str) -> dict:
    """Read a specific bug row from the JSONL."""
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                row = json.loads(line)
                if row.get("ID") == bug_id:
                    return row
    return {}


# ---------------------------------------------------------------------------
# Tests for _cascade_bug_status() — Phase 2 (dev-log/test-report scanning)
# ---------------------------------------------------------------------------

class TestCascadeBugStatusDocScanning:
    """Test the new Phase 2 logic in _cascade_bug_status()."""

    def test_auto_closes_bug_referenced_in_dev_log(self, tmp_path: Path) -> None:
        """Bug referenced in dev-log.md with Open status gets auto-closed."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-088", "Status": "Open", "Fixed In WP": ""},
        ])
        _make_wp_folder(tmp_path, "FIX-050",
                        dev_log_content="Fixed BUG-088 during this WP.")

        with patch("finalize_wp.REPO_ROOT", tmp_path), \
             patch("finalize_wp.BUG_JSONL", bug_jsonl):
            from finalize_wp import _cascade_bug_status
            _cascade_bug_status("FIX-050", dry_run=False)

        bug = _read_bug_status(bug_jsonl, "BUG-088")
        assert bug["Status"] == "Closed"
        assert bug["Fixed In WP"] == "FIX-050"

    def test_auto_closes_bug_referenced_in_test_report(self, tmp_path: Path) -> None:
        """Bug referenced in test-report.md with Open status gets auto-closed."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-089", "Status": "Open", "Fixed In WP": ""},
        ])
        _make_wp_folder(tmp_path, "FIX-050",
                        test_report_content="Verified fix for BUG-089.")

        with patch("finalize_wp.REPO_ROOT", tmp_path), \
             patch("finalize_wp.BUG_JSONL", bug_jsonl):
            from finalize_wp import _cascade_bug_status
            _cascade_bug_status("FIX-050", dry_run=False)

        bug = _read_bug_status(bug_jsonl, "BUG-089")
        assert bug["Status"] == "Closed"
        assert bug["Fixed In WP"] == "FIX-050"

    def test_auto_closes_in_progress_bug(self, tmp_path: Path) -> None:
        """Bug with In Progress status also gets auto-closed."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-090", "Status": "In Progress", "Fixed In WP": ""},
        ])
        _make_wp_folder(tmp_path, "FIX-050",
                        dev_log_content="Addressed BUG-090 here.")

        with patch("finalize_wp.REPO_ROOT", tmp_path), \
             patch("finalize_wp.BUG_JSONL", bug_jsonl):
            from finalize_wp import _cascade_bug_status
            _cascade_bug_status("FIX-050", dry_run=False)

        bug = _read_bug_status(bug_jsonl, "BUG-090")
        assert bug["Status"] == "Closed"

    def test_does_not_close_already_closed_bug(self, tmp_path: Path) -> None:
        """Bug already Closed is not modified."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-091", "Status": "Closed", "Fixed In WP": "FIX-040"},
        ])
        _make_wp_folder(tmp_path, "FIX-050",
                        dev_log_content="See BUG-091 for context.")

        with patch("finalize_wp.REPO_ROOT", tmp_path), \
             patch("finalize_wp.BUG_JSONL", bug_jsonl):
            from finalize_wp import _cascade_bug_status
            _cascade_bug_status("FIX-050", dry_run=False)

        bug = _read_bug_status(bug_jsonl, "BUG-091")
        assert bug["Status"] == "Closed"
        assert bug["Fixed In WP"] == "FIX-040"  # unchanged

    def test_does_not_close_verified_bug(self, tmp_path: Path) -> None:
        """Bug with Verified status is not modified."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-092", "Status": "Verified", "Fixed In WP": "FIX-040"},
        ])
        _make_wp_folder(tmp_path, "FIX-050",
                        dev_log_content="Related to BUG-092.")

        with patch("finalize_wp.REPO_ROOT", tmp_path), \
             patch("finalize_wp.BUG_JSONL", bug_jsonl):
            from finalize_wp import _cascade_bug_status
            _cascade_bug_status("FIX-050", dry_run=False)

        bug = _read_bug_status(bug_jsonl, "BUG-092")
        assert bug["Status"] == "Verified"

    def test_dry_run_does_not_modify(self, tmp_path: Path, capsys) -> None:
        """Dry-run mode prints message but doesn't modify bugs.jsonl."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-093", "Status": "Open", "Fixed In WP": ""},
        ])
        _make_wp_folder(tmp_path, "FIX-050",
                        dev_log_content="Fixed BUG-093 in this WP.")

        with patch("finalize_wp.REPO_ROOT", tmp_path), \
             patch("finalize_wp.BUG_JSONL", bug_jsonl):
            from finalize_wp import _cascade_bug_status
            _cascade_bug_status("FIX-050", dry_run=True)

        bug = _read_bug_status(bug_jsonl, "BUG-093")
        assert bug["Status"] == "Open"  # unchanged
        assert bug["Fixed In WP"] == ""  # unchanged

        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "BUG-093" in captured.out

    def test_preserves_existing_fixed_in_wp(self, tmp_path: Path) -> None:
        """If Fixed In WP is already set, don't overwrite it — just close."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-094", "Status": "Open", "Fixed In WP": "FIX-040"},
        ])
        _make_wp_folder(tmp_path, "FIX-050",
                        dev_log_content="Also see BUG-094.")

        with patch("finalize_wp.REPO_ROOT", tmp_path), \
             patch("finalize_wp.BUG_JSONL", bug_jsonl):
            from finalize_wp import _cascade_bug_status
            _cascade_bug_status("FIX-050", dry_run=False)

        bug = _read_bug_status(bug_jsonl, "BUG-094")
        assert bug["Status"] == "Closed"
        assert bug["Fixed In WP"] == "FIX-040"  # preserved original

    def test_no_crash_when_files_missing(self, tmp_path: Path) -> None:
        """Handles missing dev-log.md and test-report.md gracefully."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-095", "Status": "Open", "Fixed In WP": ""},
        ])
        # Don't create any WP folder files
        wp_folder = tmp_path / "docs" / "workpackages" / "FIX-050"
        wp_folder.mkdir(parents=True, exist_ok=True)

        with patch("finalize_wp.REPO_ROOT", tmp_path), \
             patch("finalize_wp.BUG_JSONL", bug_jsonl):
            from finalize_wp import _cascade_bug_status
            _cascade_bug_status("FIX-050", dry_run=False)

        bug = _read_bug_status(bug_jsonl, "BUG-095")
        assert bug["Status"] == "Open"  # unchanged — no references found

    def test_phase1_still_works(self, tmp_path: Path) -> None:
        """Phase 1 (exact Fixed In WP match) still closes bugs."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-096", "Status": "Open", "Fixed In WP": "FIX-050"},
        ])
        # No dev-log needed for Phase 1
        wp_folder = tmp_path / "docs" / "workpackages" / "FIX-050"
        wp_folder.mkdir(parents=True, exist_ok=True)

        with patch("finalize_wp.REPO_ROOT", tmp_path), \
             patch("finalize_wp.BUG_JSONL", bug_jsonl):
            from finalize_wp import _cascade_bug_status
            _cascade_bug_status("FIX-050", dry_run=False)

        bug = _read_bug_status(bug_jsonl, "BUG-096")
        assert bug["Status"] == "Closed"


# ---------------------------------------------------------------------------
# Tests for _check_bug_linkage()
# ---------------------------------------------------------------------------

class TestCheckBugLinkage:
    """Test the _check_bug_linkage() validator in validate_workspace.py."""

    def test_warns_about_unlinked_bug(self, tmp_path: Path) -> None:
        """Bug referenced in dev-log but Fixed In WP doesn't match raises warning."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-088", "Status": "Open", "Fixed In WP": ""},
        ])
        _make_wp_folder(tmp_path, "FIX-050",
                        dev_log_content="Fixed BUG-088 during this WP.")

        with patch("validate_workspace.REPO_ROOT", tmp_path), \
             patch("validate_workspace.BUG_JSONL", bug_jsonl):
            from validate_workspace import _check_bug_linkage, ValidationResult
            result = ValidationResult()
            _check_bug_linkage("FIX-050", result)

        assert len(result.warnings) == 1
        assert "BUG-088" in result.warnings[0]
        assert "FIX-050" in result.warnings[0]

    def test_no_warning_when_linked(self, tmp_path: Path) -> None:
        """Bug referenced in dev-log with correct Fixed In WP produces no warning."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-088", "Status": "Open", "Fixed In WP": "FIX-050"},
        ])
        _make_wp_folder(tmp_path, "FIX-050",
                        dev_log_content="Fixed BUG-088 during this WP.")

        with patch("validate_workspace.REPO_ROOT", tmp_path), \
             patch("validate_workspace.BUG_JSONL", bug_jsonl):
            from validate_workspace import _check_bug_linkage, ValidationResult
            result = ValidationResult()
            _check_bug_linkage("FIX-050", result)

        assert len(result.warnings) == 0

    def test_no_warning_when_no_bug_refs(self, tmp_path: Path) -> None:
        """No warnings when dev-log contains no BUG references."""
        _make_bug_jsonl(tmp_path, [])
        _make_wp_folder(tmp_path, "FIX-050",
                        dev_log_content="No bugs referenced here.")

        with patch("validate_workspace.REPO_ROOT", tmp_path):
            from validate_workspace import _check_bug_linkage, ValidationResult
            result = ValidationResult()
            _check_bug_linkage("FIX-050", result)

        assert len(result.warnings) == 0

    def test_warns_from_test_report(self, tmp_path: Path) -> None:
        """Bug referenced in test-report.md without linkage triggers warning."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-089", "Status": "Open", "Fixed In WP": ""},
        ])
        _make_wp_folder(tmp_path, "FIX-050",
                        test_report_content="Verified BUG-089 fix.")

        with patch("validate_workspace.REPO_ROOT", tmp_path), \
             patch("validate_workspace.BUG_JSONL", bug_jsonl):
            from validate_workspace import _check_bug_linkage, ValidationResult
            result = ValidationResult()
            _check_bug_linkage("FIX-050", result)

        assert len(result.warnings) == 1
        assert "BUG-089" in result.warnings[0]

    def test_handles_missing_files(self, tmp_path: Path) -> None:
        """No crash when dev-log.md and test-report.md don't exist."""
        wp_folder = tmp_path / "docs" / "workpackages" / "FIX-050"
        wp_folder.mkdir(parents=True, exist_ok=True)

        with patch("validate_workspace.REPO_ROOT", tmp_path):
            from validate_workspace import _check_bug_linkage, ValidationResult
            result = ValidationResult()
            _check_bug_linkage("FIX-050", result)

        assert len(result.warnings) == 0
        assert len(result.errors) == 0


# ---------------------------------------------------------------------------
# Tests for _check_csv_structural() bug status enum (FIX-065 coverage)
# ---------------------------------------------------------------------------

class TestBugStatusEnum:
    """Verify _check_bug_status_enum() catches invalid bug statuses."""

    def test_invalid_bug_status_caught(self, tmp_path: Path) -> None:
        """Non-standard bug status triggers a warning."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-100", "Status": "Wontfix"},
        ])

        with patch("validate_workspace.BUG_JSONL", bug_jsonl):
            from validate_workspace import _check_bug_status_enum, ValidationResult
            result = ValidationResult()
            _check_bug_status_enum(result)

        assert len(result.warnings) == 1
        assert "BUG-100" in result.warnings[0]
        assert "Wontfix" in result.warnings[0]

    def test_valid_bug_statuses_pass(self, tmp_path: Path) -> None:
        """Standard bug statuses don't produce warnings."""
        bug_jsonl = _make_bug_jsonl(tmp_path, [
            {"ID": "BUG-101", "Status": "Open"},
            {"ID": "BUG-102", "Status": "In Progress"},
            {"ID": "BUG-103", "Status": "Fixed"},
            {"ID": "BUG-104", "Status": "Verified"},
            {"ID": "BUG-105", "Status": "Closed"},
        ])

        with patch("validate_workspace.BUG_JSONL", bug_jsonl):
            from validate_workspace import _check_bug_status_enum, ValidationResult
            result = ValidationResult()
            _check_bug_status_enum(result)

        assert len(result.warnings) == 0
