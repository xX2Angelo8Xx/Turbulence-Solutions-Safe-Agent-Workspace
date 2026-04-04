"""Tests for MNT-024: Reset regression baseline and verify CI green."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
BASELINE_FILE = REPO_ROOT / "tests" / "regression-baseline.json"


def _load_baseline():
    return json.loads(BASELINE_FILE.read_text(encoding="utf-8"))


def test_baseline_file_exists():
    """regression-baseline.json must exist."""
    assert BASELINE_FILE.exists(), "tests/regression-baseline.json not found"


def test_baseline_count_matches_entries():
    """_count must equal the actual number of entries in known_failures."""
    data = _load_baseline()
    declared = data["_count"]
    actual = len(data["known_failures"])
    assert declared == actual, (
        f"_count ({declared}) does not match len(known_failures) ({actual})"
    )


def test_baseline_count_reduced_from_original():
    """_count must be significantly below the pre-MNT-024 baseline of 147."""
    data = _load_baseline()
    assert data["_count"] < 100, (
        f"Baseline count {data['_count']} is still >= 100; "
        "MNT-024 targeted a substantial reduction from 147"
    )


def test_baseline_updated_field_present():
    """_updated field must be present."""
    data = _load_baseline()
    assert "_updated" in data, "_updated field missing from baseline"


def test_baseline_updated_after_previous_reset():
    """_updated must be later than the previous reset date (2026-04-04)."""
    data = _load_baseline()
    assert data["_updated"] > "2026-04-04", (
        f"_updated ({data['_updated']!r}) is not after the previous reset date 2026-04-04"
    )


def test_all_entries_have_reason():
    """Every known_failures entry must have a non-empty 'reason' key."""
    data = _load_baseline()
    missing = [k for k, v in data["known_failures"].items() if not v.get("reason")]
    assert not missing, f"Entries without reason: {missing}"


def test_no_entry_uses_generic_reason():
    """No entry should use the old generic 'pre-existing failure' reason text."""
    data = _load_baseline()
    generic = [
        k for k, v in data["known_failures"].items()
        if "pre-existing failure" in v.get("reason", "")
    ]
    assert not generic, (
        f"{len(generic)} entries still use the generic 'pre-existing failure' reason. "
        "Each entry must have a specific, actionable reason."
    )


def test_baseline_is_valid_json():
    """regression-baseline.json must be valid JSON with expected top-level keys."""
    data = _load_baseline()
    for key in ("_count", "_updated", "known_failures"):
        assert key in data, f"Missing top-level key: {key}"
    assert isinstance(data["known_failures"], dict), "known_failures must be a dict"
