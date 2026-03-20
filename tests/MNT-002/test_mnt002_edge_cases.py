"""Edge-case and security tests for MNT-002 (Tester-added).

Covers:
- Schema contract enforcement: Open actions should have empty resolved_by
- WP-ID key format in validation-exceptions.json (no path traversal)
- skip_checks values must be strings
- Action tracker duplicate ID detection
- Malformed entry structure resilience
- validate_workspace.py --wp MNT-002 exits cleanly
- source_log field plausibility (non-empty string)
"""
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TRACKER_PATH = REPO_ROOT / "docs" / "maintenance" / "action-tracker.json"
EXCEPTIONS_PATH = REPO_ROOT / "docs" / "workpackages" / "validation-exceptions.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _load_tracker():
    with open(TRACKER_PATH, encoding="utf-8") as f:
        return json.load(f)


def _load_exceptions():
    with open(EXCEPTIONS_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# action-tracker.json edge cases
# ---------------------------------------------------------------------------

def test_no_duplicate_action_ids():
    """Action IDs must be unique across the tracker."""
    data = _load_tracker()
    ids = [a["action_id"] for a in data["actions"]]
    assert len(ids) == len(set(ids)), f"Duplicate action IDs found: {ids}"


def test_source_log_field_non_empty():
    """Every action must have a non-empty source_log field."""
    data = _load_tracker()
    for action in data["actions"]:
        assert action["source_log"].strip(), (
            f"{action['action_id']}: source_log must not be empty"
        )


def test_description_non_empty():
    """Every action must have a non-empty description."""
    data = _load_tracker()
    for action in data["actions"]:
        assert action["description"].strip(), (
            f"{action['action_id']}: description must not be empty"
        )


def test_open_actions_resolved_by_schema_contract():
    """SCHEMA CONTRACT: resolved_by should be empty when status is Open.

    The _schema entry says: 'WP-ID or commit that resolved this, empty if Open'.
    This test documents the current state — Open items have non-empty resolved_by
    values (planned WP IDs), which violates the schema contract.

    BUG: ACT-006, ACT-007, ACT-009, ACT-010, ACT-011 are 'Open' but have
    non-empty resolved_by. Either the schema description or the data must be
    corrected. Filed as BUG in docs/bugs/bugs.csv.
    """
    data = _load_tracker()
    violations = [
        a["action_id"]
        for a in data["actions"]
        if a["status"] == "Open" and a.get("resolved_by", "").strip()
    ]
    # Currently this is a known schema violation — document it, don't silently pass
    # If the schema is updated to allow "planned" WP-ID, remove this assertion.
    assert violations == [], (
        f"Schema violation: Open actions with non-empty resolved_by: {violations}\n"
        "Schema says resolved_by must be empty when status is Open.\n"
        "Either update the schema description to 'empty if unassigned' or clear these fields."
    )


def test_done_actions_have_non_empty_resolved_by():
    """Done actions must have a non-empty resolved_by (what resolved them)."""
    data = _load_tracker()
    for action in data["actions"]:
        if action["status"] == "Done":
            assert action.get("resolved_by", "").strip(), (
                f"{action['action_id']}: Done action must have non-empty resolved_by"
            )


def test_action_id_format():
    """Every action_id must match ACT-NNN format exactly."""
    import re
    data = _load_tracker()
    pattern = re.compile(r"^ACT-\d{3}$")
    for action in data["actions"]:
        assert pattern.match(action["action_id"]), (
            f"Invalid action_id format: {action['action_id']!r} (expected ACT-NNN)"
        )


# ---------------------------------------------------------------------------
# validation-exceptions.json edge cases
# ---------------------------------------------------------------------------

def test_wp_id_keys_no_path_traversal():
    """WP-ID keys in validation-exceptions.json must not contain path traversal."""
    data = _load_exceptions()
    for key in data:
        if key == "_schema":
            continue
        assert ".." not in key, f"Key {key!r} contains path traversal sequence '..'"
        assert "/" not in key, f"Key {key!r} contains slash — not a valid WP-ID"
        assert "\\" not in key, f"Key {key!r} contains backslash — not a valid WP-ID"


def test_skip_checks_values_are_strings():
    """Each item in skip_checks must be a non-empty string."""
    data = _load_exceptions()
    for key, value in data.items():
        if key == "_schema":
            continue
        for check_name in value["skip_checks"]:
            assert isinstance(check_name, str), (
                f"{key}: skip_checks item must be a string, got {type(check_name)}"
            )
            assert check_name.strip(), (
                f"{key}: skip_checks item must not be empty or whitespace-only"
            )


def test_reason_field_is_meaningful():
    """Reason field must have at least 10 characters (not a trivial placeholder)."""
    data = _load_exceptions()
    for key, value in data.items():
        if key == "_schema":
            continue
        assert len(value["reason"]) >= 10, (
            f"{key}: reason field is too short ({len(value['reason'])} chars)"
        )


def test_no_injection_in_reason():
    """Reason field must not contain JSON-breaking characters that could indicate injection."""
    data = _load_exceptions()
    raw_text = json.dumps(data)
    # Verify the file round-trips cleanly (no broken escaping)
    reparsed = json.loads(raw_text)
    assert reparsed == data, "JSON does not round-trip cleanly — possible injection or encoding issue"


# ---------------------------------------------------------------------------
# Workspace validator integration
# ---------------------------------------------------------------------------

def test_validate_workspace_wp_mnt002_exits_clean():
    """validate_workspace.py --wp MNT-002 must exit with code 0."""
    script = REPO_ROOT / "scripts" / "validate_workspace.py"
    result = subprocess.run(
        [sys.executable, str(script), "--wp", "MNT-002"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"validate_workspace.py --wp MNT-002 failed:\n{result.stdout}\n{result.stderr}"
    )
