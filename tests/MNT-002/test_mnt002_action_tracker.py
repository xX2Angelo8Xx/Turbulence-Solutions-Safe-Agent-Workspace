"""Tests for MNT-002: action-tracker.json schema and content."""
import json
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TRACKER_PATH = os.path.join(REPO_ROOT, "docs", "maintenance", "action-tracker.json")

VALID_STATUSES = {"Open", "Done", "Rejected"}
VALID_PRIORITIES = {"Warning", "Info"}


@pytest.fixture
def tracker_data():
    with open(TRACKER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_file_exists():
    """action-tracker.json must exist."""
    assert os.path.isfile(TRACKER_PATH), f"Missing {TRACKER_PATH}"


def test_valid_json():
    """File must be valid JSON."""
    with open(TRACKER_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)


def test_has_schema_key(tracker_data):
    """Must contain _schema key describing the format."""
    assert "_schema" in tracker_data
    schema = tracker_data["_schema"]
    assert isinstance(schema, dict)
    for field in ("action_id", "source_log", "description", "priority", "status", "resolved_by"):
        assert field in schema, f"_schema missing field: {field}"


def test_has_actions_array(tracker_data):
    """Must contain an 'actions' array."""
    assert "actions" in tracker_data
    assert isinstance(tracker_data["actions"], list)
    assert len(tracker_data["actions"]) > 0


def test_actions_have_required_fields(tracker_data):
    """Every action must have all required fields with correct types."""
    for action in tracker_data["actions"]:
        assert "action_id" in action, f"Missing action_id in {action}"
        assert "source_log" in action, f"Missing source_log in {action}"
        assert "description" in action, f"Missing description in {action}"
        assert "priority" in action, f"Missing priority in {action}"
        assert "status" in action, f"Missing status in {action}"
        assert "resolved_by" in action, f"Missing resolved_by in {action}"
        assert isinstance(action["action_id"], str)
        assert isinstance(action["description"], str)
        assert isinstance(action["status"], str)


def test_action_ids_are_sequential(tracker_data):
    """Action IDs must follow ACT-NNN format and be sequential."""
    actions = tracker_data["actions"]
    for i, action in enumerate(actions, start=1):
        expected_id = f"ACT-{i:03d}"
        assert action["action_id"] == expected_id, (
            f"Expected {expected_id}, got {action['action_id']}"
        )


def test_statuses_are_valid(tracker_data):
    """Every action status must be Open, Done, or Rejected."""
    for action in tracker_data["actions"]:
        assert action["status"] in VALID_STATUSES, (
            f"{action['action_id']}: invalid status '{action['status']}'"
        )


def test_priorities_are_valid(tracker_data):
    """Every action priority must be Warning or Info."""
    for action in tracker_data["actions"]:
        assert action["priority"] in VALID_PRIORITIES, (
            f"{action['action_id']}: invalid priority '{action['priority']}'"
        )


def test_initial_action_count(tracker_data):
    """Initial tracker should have 11 actions from 2026-03-20b maintenance log."""
    assert len(tracker_data["actions"]) == 11
