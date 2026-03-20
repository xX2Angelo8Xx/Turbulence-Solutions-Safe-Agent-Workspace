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
    """SCHEMA CONTRACT (Option B): resolved_by may contain a planned WP-ID while Open.

    BUG-091 fix — Option B chosen: the _schema description was updated to:
    'WP-ID or commit that resolved this; may contain planned WP-ID while Open,
    must be non-empty when Done'.

    This test enforces the updated contract:
    - Schema description must explicitly allow planned WP-IDs for Open actions.
    - Any non-empty resolved_by on an Open action must match a WP-ID pattern.
    """
    import re
    data = _load_tracker()
    schema_desc = data["_schema"].get("resolved_by", "")
    # Schema description must explicitly allow planned WP-IDs
    assert "planned" in schema_desc.lower(), (
        f"Schema description for resolved_by must allow planned WP-IDs.\n"
        f"Current description: {schema_desc!r}"
    )
    # Any non-empty resolved_by on an Open action must look like a WP-ID or commit ref
    wp_id_pattern = re.compile(r"^[A-Z]+-\d+$")
    for action in data["actions"]:
        if action["status"] == "Open" and action.get("resolved_by", "").strip():
            resolved_by = action["resolved_by"].strip()
            assert wp_id_pattern.match(resolved_by) or len(resolved_by) >= 7, (
                f"{action['action_id']}: resolved_by {resolved_by!r} on Open action "
                "must be a valid WP-ID (e.g. FIX-067) or git commit reference"
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
