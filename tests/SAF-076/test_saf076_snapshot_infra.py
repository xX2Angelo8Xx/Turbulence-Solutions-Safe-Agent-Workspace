"""Tests for SAF-076: Golden-File Snapshot Infrastructure.

Verifies that:
- tests/snapshots/README.md exists and contains the required sections.
- tests/snapshots/security_gate/test_snapshots.py exists with auto-discovery.
- All snapshot JSON files in tests/snapshots/security_gate/ are valid and well-formed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOTS_ROOT = REPO_ROOT / "tests" / "snapshots"
TOP_README = SNAPSHOTS_ROOT / "README.md"
SG_DIR = SNAPSHOTS_ROOT / "security_gate"
SG_TEST = SG_DIR / "test_snapshots.py"


# ---------------------------------------------------------------------------
# README existence and content
# ---------------------------------------------------------------------------

def test_top_level_readme_exists():
    """tests/snapshots/README.md must exist."""
    assert TOP_README.exists(), f"Missing: {TOP_README}"


def test_readme_contains_run_section():
    """README must document how to run snapshot tests."""
    text = TOP_README.read_text(encoding="utf-8")
    assert "pytest tests/snapshots/" in text, (
        "README does not document the pytest run command"
    )


def test_readme_contains_update_section():
    """README must document how to update snapshots."""
    text = TOP_README.read_text(encoding="utf-8")
    assert "update" in text.lower(), (
        "README does not contain an update section"
    )
    # Confirm manual-update approach is described (no magic flag required)
    assert "expected_decision" in text, (
        "README should show that updating means editing expected_decision in the JSON"
    )


def test_readme_contains_format_section():
    """README must describe the JSON snapshot file format."""
    text = TOP_README.read_text(encoding="utf-8")
    assert "expected_decision" in text, "README missing expected_decision field description"
    assert "description" in text, "README missing description field"
    assert "input" in text, "README missing input field"


def test_readme_contains_regression_guidance():
    """README must explain when a snapshot failure is a real regression."""
    text = TOP_README.read_text(encoding="utf-8")
    assert "regression" in text.lower(), (
        "README does not explain the regression vs intentional change distinction"
    )


# ---------------------------------------------------------------------------
# test_snapshots.py existence
# ---------------------------------------------------------------------------

def test_snapshot_test_file_exists():
    """tests/snapshots/security_gate/test_snapshots.py must exist."""
    assert SG_TEST.exists(), f"Missing: {SG_TEST}"


def test_snapshot_test_uses_auto_discovery():
    """test_snapshots.py must use glob-based auto-discovery of JSON files."""
    source = SG_TEST.read_text(encoding="utf-8")
    assert ".glob(" in source or "glob(" in source, (
        "test_snapshots.py does not appear to use glob-based auto-discovery"
    )


# ---------------------------------------------------------------------------
# Snapshot JSON validity
# ---------------------------------------------------------------------------

def _snapshot_files():
    return sorted(SG_DIR.glob("*.json"))


@pytest.mark.parametrize("snap_path", _snapshot_files(), ids=lambda p: p.stem)
def test_snapshot_files_are_valid_json(snap_path: Path):
    """Every *.json in security_gate/ must be parseable JSON."""
    try:
        data = json.loads(snap_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"{snap_path.name}: invalid JSON — {exc}")

    # Required fields
    assert "description" in data, f"{snap_path.name}: missing 'description'"
    assert "input" in data, f"{snap_path.name}: missing 'input'"
    assert "expected_decision" in data, f"{snap_path.name}: missing 'expected_decision'"
    assert data["expected_decision"] in ("allow", "deny"), (
        f"{snap_path.name}: expected_decision must be 'allow' or 'deny', "
        f"got {data['expected_decision']!r}"
    )
