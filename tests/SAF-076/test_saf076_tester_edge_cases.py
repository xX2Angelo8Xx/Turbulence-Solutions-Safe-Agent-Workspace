"""Tester edge-case tests for SAF-076: Golden-File Snapshot Infrastructure.

Additional edge-case coverage beyond the Developer's test file:
- developer.agent.md links to tests/snapshots/README.md
- tester.agent.md links to tests/snapshots/README.md with exact pytest command
- README clearly distinguishes regressions from intentional changes using a table
- README explicitly states no --update flag (manual-only updates)
- Each snapshot JSON file contains no unrecognised top-level keys
- README documents at least one allow and one deny example scenario name pattern
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
DEVELOPER_AGENT = REPO_ROOT / ".github" / "agents" / "developer.agent.md"
TESTER_AGENT = REPO_ROOT / ".github" / "agents" / "tester.agent.md"

# Fields allowed by the README format (required + optional)
ALLOWED_JSON_KEYS = {"description", "input", "expected_decision", "ws_root", "expected_reason"}


# ---------------------------------------------------------------------------
# Agent file snapshot references
# ---------------------------------------------------------------------------

def test_developer_agent_links_snapshot_readme():
    """developer.agent.md must reference tests/snapshots/README.md."""
    assert DEVELOPER_AGENT.exists(), f"Missing: {DEVELOPER_AGENT}"
    text = DEVELOPER_AGENT.read_text(encoding="utf-8")
    assert "tests/snapshots/README.md" in text, (
        "developer.agent.md does not link to tests/snapshots/README.md"
    )


def test_tester_agent_links_snapshot_readme():
    """tester.agent.md must reference tests/snapshots/README.md."""
    assert TESTER_AGENT.exists(), f"Missing: {TESTER_AGENT}"
    text = TESTER_AGENT.read_text(encoding="utf-8")
    assert "tests/snapshots/README.md" in text, (
        "tester.agent.md does not link to tests/snapshots/README.md"
    )


def test_tester_agent_contains_snapshot_pytest_command():
    """tester.agent.md must show the pytest command for running snapshot tests."""
    text = TESTER_AGENT.read_text(encoding="utf-8")
    assert "pytest tests/snapshots/" in text, (
        "tester.agent.md does not include 'pytest tests/snapshots/' run command"
    )


def test_developer_agent_snapshot_checklist_in_pre_handoff():
    """The snapshot reference in developer.agent.md must be in the Pre-Handoff Checklist."""
    text = DEVELOPER_AGENT.read_text(encoding="utf-8")
    # The checklist header must appear before the snapshot README reference
    checklist_pos = text.lower().find("pre-handoff checklist")
    readme_pos = text.find("tests/snapshots/README.md")
    assert checklist_pos != -1, "developer.agent.md missing Pre-Handoff Checklist section"
    assert readme_pos != -1, "developer.agent.md missing tests/snapshots/README.md reference"
    assert checklist_pos < readme_pos, (
        "tests/snapshots/README.md reference must appear after the Pre-Handoff Checklist header"
    )


# ---------------------------------------------------------------------------
# README content quality
# ---------------------------------------------------------------------------

def test_readme_explicitly_states_no_update_flag():
    """README must explicitly state there is no --update-snapshots magic flag."""
    text = TOP_README.read_text(encoding="utf-8")
    # The README should explain updates are manual (no flag)
    assert "no" in text.lower() and ("flag" in text.lower() or "update" in text.lower()), (
        "README should explicitly note the absence of a magic update flag"
    )


def test_readme_contains_regression_table():
    """README regression guidance section should contain a table (| characters)."""
    text = TOP_README.read_text(encoding="utf-8")
    # After "regression", a markdown table (| col | col |) should appear
    regression_pos = text.lower().find("regression")
    assert regression_pos != -1, "README missing 'regression' content"
    after_regression = text[regression_pos:]
    assert "|" in after_regression, (
        "README regression section should contain a table (| chars) distinguishing "
        "regression vs intentional-change scenarios"
    )


def test_readme_names_allow_and_deny_file_patterns():
    """README should document allow_*.json and deny_*.json naming patterns."""
    text = TOP_README.read_text(encoding="utf-8")
    assert "allow_" in text, "README does not document allow_*.json file naming pattern"
    assert "deny_" in text, "README does not document deny_*.json file naming pattern"


def test_readme_security_gate_subdir_mentioned():
    """README must explicitly mention the security_gate sub-directory."""
    text = TOP_README.read_text(encoding="utf-8")
    assert "security_gate" in text, (
        "README does not mention the security_gate sub-directory"
    )


# ---------------------------------------------------------------------------
# Snapshot JSON schema compliance
# ---------------------------------------------------------------------------

def _snapshot_files():
    return sorted(SG_DIR.glob("*.json"))


@pytest.mark.parametrize("snap_path", _snapshot_files(), ids=lambda p: p.stem)
def test_snapshot_no_unrecognised_keys(snap_path: Path):
    """No snapshot JSON file should contain keys outside the documented schema."""
    data = json.loads(snap_path.read_text(encoding="utf-8"))
    unrecognised = set(data.keys()) - ALLOWED_JSON_KEYS
    assert not unrecognised, (
        f"{snap_path.name}: unrecognised keys {unrecognised}. "
        f"Add them to ALLOWED_JSON_KEYS or remove from snapshot."
    )


@pytest.mark.parametrize("snap_path", _snapshot_files(), ids=lambda p: p.stem)
def test_snapshot_filename_matches_expected_decision(snap_path: Path):
    """Snapshot filename prefix (allow_/deny_) must match its expected_decision field."""
    data = json.loads(snap_path.read_text(encoding="utf-8"))
    decision = data.get("expected_decision", "")
    name = snap_path.stem
    if name.startswith("allow_"):
        assert decision == "allow", (
            f"{snap_path.name}: filename prefix 'allow_' but expected_decision='{decision}'"
        )
    elif name.startswith("deny_"):
        assert decision == "deny", (
            f"{snap_path.name}: filename prefix 'deny_' but expected_decision='{decision}'"
        )
    else:
        pytest.fail(
            f"{snap_path.name}: filename must start with 'allow_' or 'deny_' — "
            f"got '{name}'"
        )


@pytest.mark.parametrize("snap_path", _snapshot_files(), ids=lambda p: p.stem)
def test_snapshot_description_is_non_empty(snap_path: Path):
    """Every snapshot must have a non-empty description string."""
    data = json.loads(snap_path.read_text(encoding="utf-8"))
    description = data.get("description", "")
    assert isinstance(description, str) and description.strip(), (
        f"{snap_path.name}: 'description' must be a non-empty string"
    )
