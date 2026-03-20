"""Tests for MNT-002: validation-exceptions.json schema and content."""
import json
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXCEPTIONS_PATH = os.path.join(REPO_ROOT, "docs", "workpackages", "validation-exceptions.json")


@pytest.fixture
def exceptions_data():
    with open(EXCEPTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_file_exists():
    """validation-exceptions.json must exist."""
    assert os.path.isfile(EXCEPTIONS_PATH), f"Missing {EXCEPTIONS_PATH}"


def test_valid_json():
    """File must be valid JSON."""
    with open(EXCEPTIONS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)


def test_has_schema_key(exceptions_data):
    """Must contain _schema key describing the format."""
    assert "_schema" in exceptions_data
    assert isinstance(exceptions_data["_schema"], str)


def test_ins008_entry(exceptions_data):
    """INS-008 must be a registered exception with correct structure."""
    assert "INS-008" in exceptions_data
    entry = exceptions_data["INS-008"]
    assert "skip_checks" in entry
    assert isinstance(entry["skip_checks"], list)
    assert "reason" in entry
    assert isinstance(entry["reason"], str)
    assert len(entry["reason"]) > 0


def test_mnt001_entry(exceptions_data):
    """MNT-001 must be a registered exception with correct structure."""
    assert "MNT-001" in exceptions_data
    entry = exceptions_data["MNT-001"]
    assert "skip_checks" in entry
    assert isinstance(entry["skip_checks"], list)
    assert "reason" in entry
    assert isinstance(entry["reason"], str)
    assert len(entry["reason"]) > 0


def test_all_entries_have_required_fields(exceptions_data):
    """Every non-schema entry must have skip_checks (list) and reason (str)."""
    for key, value in exceptions_data.items():
        if key == "_schema":
            continue
        assert isinstance(value, dict), f"{key}: entry must be a dict"
        assert "skip_checks" in value, f"{key}: missing skip_checks"
        assert isinstance(value["skip_checks"], list), f"{key}: skip_checks must be list"
        assert "reason" in value, f"{key}: missing reason"
        assert isinstance(value["reason"], str), f"{key}: reason must be str"
