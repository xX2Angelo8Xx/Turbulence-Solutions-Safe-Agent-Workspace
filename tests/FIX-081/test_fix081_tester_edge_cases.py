"""Tester-added edge cases for FIX-081: Fix bug cascade logic in finalize_wp.py

These tests go beyond the Developer's suite to verify:
1. Phase 2 does NOT modify Verified bugs (Developer only tested Phase 1 Verified skip)
2. already_closed set prevents Phase 2 from re-processing a bug closed by Phase 1
3. Dry-run with dev-log present: both Phase 1 and Phase 2 produce output but call no updates
4. Phase 2 error path: partial failures return False, remaining bugs still processed
5. Mixing closed and open bugs: Closed bugs survive untouched when siblings are processed
"""

import sys
from pathlib import Path
from unittest.mock import patch, call

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import finalize_wp as fw


BUG_FIELDNAMES = ["ID", "Title", "Status", "Fixed In WP", "Priority", "Component"]


def _make_bug(bug_id: str, status: str, fixed_in: str = "") -> dict:
    return {
        "ID": bug_id,
        "Title": f"Test bug {bug_id}",
        "Status": status,
        "Fixed In WP": fixed_in,
        "Priority": "Medium",
        "Component": "test",
    }


def _patch_read_jsonl(bugs: list[dict]):
    """Return a repeatable read_jsonl side_effect that always yields the same list."""
    def _read(*args, **kwargs):
        return BUG_FIELDNAMES, [dict(b) for b in bugs]
    return _read


# ---------------------------------------------------------------------------
# Test 1: Phase 2 Verified bug is NOT closed
# ---------------------------------------------------------------------------

class TestPhase2VerifiedSkip:
    """Phase 2 must NOT close a bug with Status='Verified' even if referenced in dev-log."""

    def test_phase2_skips_verified_bug(self, tmp_path: Path):
        """'Verified' bugs are excluded from Phase 2 auto-closure (code path: status in ('Closed','Verified'))."""
        wp_folder = tmp_path / "docs" / "workpackages" / "WP-TSTR"
        wp_folder.mkdir(parents=True)
        (wp_folder / "dev-log.md").write_text("Fixed BUG-500 see details.", encoding="utf-8")

        bug = _make_bug("BUG-500", "Verified", fixed_in="")
        updated_values = []

        def _update_cell(path, id_col, id_val, col, val):
            updated_values.append((id_val, col, val))

        with (
            patch.object(fw, "read_jsonl", side_effect=_patch_read_jsonl([bug])),
            patch.object(fw, "update_cell", side_effect=_update_cell),
            patch.object(fw, "REPO_ROOT", tmp_path),
        ):
            result = fw._cascade_bug_status("WP-TSTR", dry_run=False)

        assert result is True, "No errors expected — nothing to process"
        assert updated_values == [], (
            f"Verified bug should not be touched; got updates: {updated_values}"
        )

    def test_phase2_skips_verified_bug_with_fixed_in_wp(self, tmp_path: Path):
        """Verified bug in dev-log AND with a different Fixed In WP is still skipped by Phase 2."""
        wp_folder = tmp_path / "docs" / "workpackages" / "WP-TSTR"
        wp_folder.mkdir(parents=True)
        (wp_folder / "dev-log.md").write_text("See BUG-501 for context.", encoding="utf-8")

        # Bug has Fixed In WP = "ANOTHER-WP" (not WP-TSTR) so Phase 1 won't touch it.
        # Bug is Verified — Phase 2 must also skip it.
        bug = _make_bug("BUG-501", "Verified", fixed_in="ANOTHER-WP")
        updated_values = []

        with (
            patch.object(fw, "read_jsonl", side_effect=_patch_read_jsonl([bug])),
            patch.object(fw, "update_cell", side_effect=lambda *a: updated_values.append(a)),
            patch.object(fw, "REPO_ROOT", tmp_path),
        ):
            fw._cascade_bug_status("WP-TSTR", dry_run=False)

        assert updated_values == [], f"Verified bug should not be modified; got: {updated_values}"


# ---------------------------------------------------------------------------
# Test 2: already_closed set prevents Phase 2 re-processing
# ---------------------------------------------------------------------------

class TestAlreadyClosedSetPreventsReprocessing:
    """Bug processed by Phase 1 must NOT be processed again by Phase 2."""

    def test_phase1_result_blocks_phase2(self, tmp_path: Path):
        """Bug found by both Phase 1 (Fixed In WP) and Phase 2 (dev-log ref) is
        only updated ONCE because already_closed set skips it in Phase 2.
        """
        wp_folder = tmp_path / "docs" / "workpackages" / "WP-BOTH"
        wp_folder.mkdir(parents=True)
        # dev-log references BUG-600 which is ALSO linked via Fixed In WP
        (wp_folder / "dev-log.md").write_text("This WP fixes BUG-600.", encoding="utf-8")

        bug = _make_bug("BUG-600", "Open", fixed_in="WP-BOTH")
        status_update_calls = []

        def _update_cell(path, id_col, id_val, col, val):
            if col == "Status":
                status_update_calls.append(id_val)

        with (
            patch.object(fw, "read_jsonl", side_effect=_patch_read_jsonl([bug])),
            patch.object(fw, "update_cell", side_effect=_update_cell),
            patch.object(fw, "REPO_ROOT", tmp_path),
        ):
            result = fw._cascade_bug_status("WP-BOTH", dry_run=False)

        assert result is True
        # update_cell("Status") must be called exactly ONCE — not twice
        assert status_update_calls.count("BUG-600") == 1, (
            f"BUG-600 Status should be updated exactly once; got calls: {status_update_calls}"
        )

    def test_phase1_error_allows_phase2_retry(self, tmp_path: Path):
        """If Phase 1 fails to close a bug, it is NOT added to already_closed,
        so Phase 2 may attempt it again (as a fallback).
        """
        wp_folder = tmp_path / "docs" / "workpackages" / "WP-RETRY"
        wp_folder.mkdir(parents=True)
        (wp_folder / "dev-log.md").write_text("Fixes BUG-601.", encoding="utf-8")

        bug = _make_bug("BUG-601", "Open", fixed_in="WP-RETRY")
        status_update_calls = []
        call_count = [0]

        def _update_cell(path, id_col, id_val, col, val):
            call_count[0] += 1
            if id_val == "BUG-601" and col == "Status" and call_count[0] == 1:
                raise OSError("Phase 1 simulated failure")
            if col == "Status":
                status_update_calls.append(id_val)

        with (
            patch.object(fw, "read_jsonl", side_effect=_patch_read_jsonl([bug])),
            patch.object(fw, "update_cell", side_effect=_update_cell),
            patch.object(fw, "REPO_ROOT", tmp_path),
        ):
            result = fw._cascade_bug_status("WP-RETRY", dry_run=False)

        # Phase 1 failed → all_succeeded = False → returns False
        assert result is False
        # Phase 2 retried and succeeded
        assert "BUG-601" in status_update_calls, (
            "Phase 2 should retry BUG-601 since Phase 1 failed to add it to already_closed"
        )


# ---------------------------------------------------------------------------
# Test 3: Dry-run with dev-log present (both Phase 1 and Phase 2)
# ---------------------------------------------------------------------------

class TestDryRunWithDevLog:
    """Dry-run must not call update_cell in either Phase 1 or Phase 2."""

    def test_dry_run_no_updates_phase1_and_phase2(self, tmp_path: Path):
        """With dry_run=True and both a Phase 1 match AND a Phase 2 dev-log match,
        update_cell is never called.
        """
        wp_folder = tmp_path / "docs" / "workpackages" / "WP-DRY2"
        wp_folder.mkdir(parents=True)
        (wp_folder / "dev-log.md").write_text(
            "Phase1 bug: BUG-700. Phase2 only bug: BUG-701.", encoding="utf-8"
        )

        bugs = [
            _make_bug("BUG-700", "Open", fixed_in="WP-DRY2"),   # Phase 1 match
            _make_bug("BUG-701", "Fixed", fixed_in=""),           # Phase 2 only
        ]

        with (
            patch.object(fw, "read_jsonl", side_effect=_patch_read_jsonl(bugs)),
            patch.object(fw, "update_cell") as mock_update,
            patch.object(fw, "REPO_ROOT", tmp_path),
        ):
            result = fw._cascade_bug_status("WP-DRY2", dry_run=True)

        assert result is True
        mock_update.assert_not_called()

    def test_dry_run_still_prevents_phase2_reprocess_via_already_closed(self, tmp_path: Path):
        """In dry-run, already_closed is still populated after Phase 1,
        so Phase 2 skips the same bug (no duplicate DRY RUN output causes infinite loop risk).
        """
        wp_folder = tmp_path / "docs" / "workpackages" / "WP-DRY3"
        wp_folder.mkdir(parents=True)
        (wp_folder / "dev-log.md").write_text("Fixes BUG-702 directly.", encoding="utf-8")

        bug = _make_bug("BUG-702", "Open", fixed_in="WP-DRY3")

        output_lines = []
        original_print = __builtins__["print"] if isinstance(__builtins__, dict) else print

        with (
            patch.object(fw, "read_jsonl", side_effect=_patch_read_jsonl([bug])),
            patch.object(fw, "update_cell") as mock_update,
            patch.object(fw, "REPO_ROOT", tmp_path),
            patch("builtins.print", side_effect=lambda *args: output_lines.append(" ".join(str(a) for a in args))),
        ):
            result = fw._cascade_bug_status("WP-DRY3", dry_run=True)

        assert result is True
        mock_update.assert_not_called()
        # BUG-702 should appear in DRY RUN output exactly ONCE — Phase 1 only
        dry_run_mentions = [l for l in output_lines if "BUG-702" in l]
        assert len(dry_run_mentions) == 1, (
            f"BUG-702 should appear exactly once in dry-run output (deduplicated); got: {dry_run_mentions}"
        )


# ---------------------------------------------------------------------------
# Test 4: No mutation on mixed-status bug batch
# ---------------------------------------------------------------------------

class TestMixedStatusBatch:
    """When processing multiple bugs, Closed bugs survive untouched."""

    def test_closed_bug_untouched_among_open_bugs(self):
        """Closed bug in Phase 1 batch is not re-closed while Open siblings are closed."""
        bugs = [
            _make_bug("BUG-800", "Open", fixed_in="WP-MIX"),
            _make_bug("BUG-801", "Closed", fixed_in="WP-MIX"),   # should be skipped
            _make_bug("BUG-802", "Fixed", fixed_in="WP-MIX"),
        ]
        status_updates = {}

        def _update_cell(path, id_col, id_val, col, val):
            if col == "Status":
                status_updates[id_val] = val

        with (
            patch.object(fw, "read_jsonl", side_effect=_patch_read_jsonl(bugs)),
            patch.object(fw, "update_cell", side_effect=_update_cell),
            patch.object(fw, "REPO_ROOT", REPO_ROOT / "tmp_nonexistent"),
        ):
            result = fw._cascade_bug_status("WP-MIX", dry_run=False)

        assert result is True
        assert status_updates.get("BUG-800") == "Closed"
        assert "BUG-801" not in status_updates, "Already-Closed bug must NOT be re-updated"
        assert status_updates.get("BUG-802") == "Closed"
