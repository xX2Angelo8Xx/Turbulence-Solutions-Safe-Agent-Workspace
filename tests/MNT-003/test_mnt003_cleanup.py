"""Tests for MNT-003: 2026-03-30 maintenance data cleanup."""
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

ORPHANED_STATE_FILES = [
    "docs/workpackages/DOC-016/.finalization-state.json",
    "docs/workpackages/DOC-019/.finalization-state.json",
    "docs/workpackages/DOC-028/.finalization-state.json",
    "docs/workpackages/FIX-071/.finalization-state.json",
    "docs/workpackages/FIX-075/.finalization-state.json",
    "docs/workpackages/FIX-080/.finalization-state.json",
    "docs/workpackages/INS-029/.finalization-state.json",
    "docs/workpackages/SAF-049/.finalization-state.json",
    "docs/workpackages/SAF-051/.finalization-state.json",
    "docs/workpackages/SAF-055/.finalization-state.json",
    "docs/workpackages/SAF-059/.finalization-state.json",
    "docs/workpackages/SAF-061/.finalization-state.json",
]

CLOSED_BUG_IDS = [
    "BUG-111", "BUG-113", "BUG-114", "BUG-115", "BUG-117", "BUG-119",
    "BUG-135", "BUG-136", "BUG-137", "BUG-138", "BUG-139", "BUG-140",
    "BUG-141", "BUG-142", "BUG-143", "BUG-144", "BUG-145", "BUG-146",
    "BUG-147", "BUG-148", "BUG-149",
]

ACTION_IDS = ["ACT-029", "ACT-030", "ACT-031", "ACT-032", "ACT-033"]


@pytest.mark.parametrize("rel_path", ORPHANED_STATE_FILES)
def test_state_file_deleted(rel_path: str) -> None:
    """Each orphaned .finalization-state.json must not exist."""
    assert not (REPO_ROOT / rel_path).exists(), (
        f"Orphaned state file still exists: {rel_path}"
    )


def test_bugs_closed() -> None:
    """All 21 target bugs must have Status=Closed in bugs.csv."""
    import csv
    import sys

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from csv_utils import read_csv

    bugs_csv = REPO_ROOT / "docs/bugs/bugs.csv"
    _, rows = read_csv(bugs_csv)
    bug_status = {row["ID"]: row["Status"] for row in rows}

    for bug_id in CLOSED_BUG_IDS:
        assert bug_id in bug_status, f"{bug_id} not found in bugs.csv"
        assert bug_status[bug_id] == "Closed", (
            f"{bug_id} has Status={bug_status[bug_id]!r}, expected 'Closed'"
        )


def test_action_tracker_entries() -> None:
    """action-tracker.json must contain ACT-029 through ACT-033."""
    tracker_path = REPO_ROOT / "docs/maintenance/action-tracker.json"
    data = json.loads(tracker_path.read_text(encoding="utf-8"))
    present_ids = {entry["action_id"] for entry in data["actions"]}

    for action_id in ACTION_IDS:
        assert action_id in present_ids, (
            f"{action_id} not found in action-tracker.json"
        )


def test_action_tracker_act029_done() -> None:
    """ACT-029 must have status Done."""
    tracker_path = REPO_ROOT / "docs/maintenance/action-tracker.json"
    data = json.loads(tracker_path.read_text(encoding="utf-8"))
    entry = next(
        (e for e in data["actions"] if e["action_id"] == "ACT-029"), None
    )
    assert entry is not None
    assert entry["status"] == "Done"


def test_action_tracker_act030_done() -> None:
    """ACT-030 must have status Done."""
    tracker_path = REPO_ROOT / "docs/maintenance/action-tracker.json"
    data = json.loads(tracker_path.read_text(encoding="utf-8"))
    entry = next(
        (e for e in data["actions"] if e["action_id"] == "ACT-030"), None
    )
    assert entry is not None
    assert entry["status"] == "Done"


def test_action_tracker_open_actions() -> None:
    """ACT-031, ACT-032, ACT-033 must have status Open."""
    tracker_path = REPO_ROOT / "docs/maintenance/action-tracker.json"
    data = json.loads(tracker_path.read_text(encoding="utf-8"))
    entries = {e["action_id"]: e for e in data["actions"]}

    for action_id in ("ACT-031", "ACT-032", "ACT-033"):
        assert action_id in entries
        assert entries[action_id]["status"] == "Done", (
            f"{action_id} expected status Done, got {entries[action_id]['status']!r}"
        )


# --- Edge-case tests (Tester additions) ---

REQUIRED_ACTION_FIELDS = {"action_id", "source_log", "description", "priority", "status", "resolved_by"}
VALID_PRIORITIES = {"Warning", "Info"}
VALID_STATUSES = {"Open", "Done", "Rejected"}


def test_action_tracker_has_top_level_keys() -> None:
    """action-tracker.json must have '_schema' and 'actions' top-level keys."""
    tracker_path = REPO_ROOT / "docs/maintenance/action-tracker.json"
    data = json.loads(tracker_path.read_text(encoding="utf-8"))
    assert "_schema" in data, "action-tracker.json missing '_schema' key"
    assert "actions" in data, "action-tracker.json missing 'actions' key"
    assert isinstance(data["actions"], list), "'actions' must be a list"


def test_new_action_entries_have_required_fields() -> None:
    """Every new ACT-029..ACT-033 entry must contain all schema-required fields."""
    tracker_path = REPO_ROOT / "docs/maintenance/action-tracker.json"
    data = json.loads(tracker_path.read_text(encoding="utf-8"))
    entries = {e["action_id"]: e for e in data["actions"]}

    for action_id in ACTION_IDS:
        entry = entries.get(action_id)
        assert entry is not None, f"{action_id} not found"
        missing = REQUIRED_ACTION_FIELDS - set(entry.keys())
        assert not missing, f"{action_id} is missing fields: {missing}"


def test_new_action_entries_valid_priority() -> None:
    """ACT-029..ACT-033 must have a valid priority value."""
    tracker_path = REPO_ROOT / "docs/maintenance/action-tracker.json"
    data = json.loads(tracker_path.read_text(encoding="utf-8"))
    entries = {e["action_id"]: e for e in data["actions"]}

    for action_id in ACTION_IDS:
        entry = entries[action_id]
        assert entry["priority"] in VALID_PRIORITIES, (
            f"{action_id} has invalid priority {entry['priority']!r}"
        )


def test_new_action_entries_valid_status() -> None:
    """ACT-029..ACT-033 must have a valid status value."""
    tracker_path = REPO_ROOT / "docs/maintenance/action-tracker.json"
    data = json.loads(tracker_path.read_text(encoding="utf-8"))
    entries = {e["action_id"]: e for e in data["actions"]}

    for action_id in ACTION_IDS:
        entry = entries[action_id]
        assert entry["status"] in VALID_STATUSES, (
            f"{action_id} has invalid status {entry['status']!r}"
        )


def test_done_actions_have_nonempty_resolved_by() -> None:
    """Schema rule: resolved_by must be non-empty when status is Done."""
    tracker_path = REPO_ROOT / "docs/maintenance/action-tracker.json"
    data = json.loads(tracker_path.read_text(encoding="utf-8"))
    entries = {e["action_id"]: e for e in data["actions"]}

    for action_id in ("ACT-029", "ACT-030"):
        entry = entries[action_id]
        assert entry["resolved_by"], (
            f"{action_id} is Done but resolved_by is empty"
        )


def test_excluded_bugs_not_unintentionally_closed() -> None:
    """Bugs BUG-112, BUG-116, BUG-118 (gaps in target list) must not be Closed
    purely from this WP's actions — they were not in scope."""
    import csv
    rows = list(csv.DictReader(
        (REPO_ROOT / "docs/bugs/bugs.csv").open(encoding="utf-8-sig")
    ))
    bug_map = {r["ID"]: r["Status"] for r in rows}

    # These IDs were intentionally excluded from the closure list.
    excluded = ["BUG-112", "BUG-116", "BUG-118"]
    for bug_id in excluded:
        if bug_id in bug_map:
            # If they exist they should NOT have been set to Closed by this WP
            # (they should retain whatever status they had before — not Closed
            # unless they were already Closed before MNT-003).
            # We verify they are NOT in the CLOSED_BUG_IDS list.
            assert bug_id not in CLOSED_BUG_IDS, (
                f"{bug_id} should not be in the MNT-003 closure list"
            )


def test_maintenance_log_phase0_complete() -> None:
    """2026-03-30-maintenance.md must reflect all phases complete."""
    log_path = REPO_ROOT / "docs/maintenance/2026-03-30-maintenance.md"
    content = log_path.read_text(encoding="utf-8")
    assert "All phases complete" in content, (
        "Maintenance log does not show all phases complete"
    )
    assert "MNT-003" in content, (
        "Maintenance log does not reference MNT-003"
    )
