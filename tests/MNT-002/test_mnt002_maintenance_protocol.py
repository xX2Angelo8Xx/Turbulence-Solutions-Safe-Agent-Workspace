"""Tests for MNT-002: maintenance-protocol.md references action tracker."""
import os
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROTOCOL_PATH = os.path.join(REPO_ROOT, "docs", "work-rules", "maintenance-protocol.md")


def test_protocol_file_exists():
    """maintenance-protocol.md must exist."""
    assert os.path.isfile(PROTOCOL_PATH)


def test_protocol_has_step_zero():
    """maintenance-protocol.md must have a step 0 heading."""
    with open(PROTOCOL_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "### 0." in content, "Missing step 0 heading in maintenance-protocol.md"


def test_protocol_step_zero_references_action_tracker():
    """Step 0 must reference action-tracker.json."""
    with open(PROTOCOL_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "action-tracker.json" in content, (
        "maintenance-protocol.md must reference action-tracker.json"
    )


def test_step_zero_before_step_one():
    """Step 0 must appear before Step 1 in the file."""
    with open(PROTOCOL_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    pos_zero = content.find("### 0.")
    pos_one = content.find("### 1.")
    assert pos_zero >= 0, "Step 0 not found"
    assert pos_one >= 0, "Step 1 not found"
    assert pos_zero < pos_one, "Step 0 must appear before Step 1"


def test_step_zero_mentions_open_actions():
    """Step 0 must mention reviewing Open actions."""
    with open(PROTOCOL_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    # Find the step 0 section content (between ### 0. and ### 1.)
    match = re.search(r"### 0\..*?(?=### 1\.)", content, re.DOTALL)
    assert match, "Could not extract step 0 section"
    section = match.group(0)
    assert "Open" in section, "Step 0 must mention reviewing Open actions"
