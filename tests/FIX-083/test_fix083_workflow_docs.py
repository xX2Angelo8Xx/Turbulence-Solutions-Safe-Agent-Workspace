"""
FIX-083: Tests verifying workflow documentation updates.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUG_RULES = REPO_ROOT / "docs" / "work-rules" / "bug-tracking-rules.md"
AGENT_WORKFLOW = REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md"
MAINTENANCE_LOG = REPO_ROOT / "docs" / "maintenance" / "2026-03-30-maintenance.md"


# ---------------------------------------------------------------------------
# bug-tracking-rules.md
# ---------------------------------------------------------------------------

def test_bug_rules_no_verified_in_lifecycle_section():
    """bug-tracking-rules.md Status Lifecycle section must not contain 'Verified'."""
    content = BUG_RULES.read_text(encoding="utf-8")
    # Extract the Status Lifecycle section up to the next ## heading
    match = re.search(r"## Status Lifecycle\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    assert match, "Status Lifecycle section not found in bug-tracking-rules.md"
    lifecycle_section = match.group(1)
    assert "Verified" not in lifecycle_section, (
        "The word 'Verified' must not appear in the Status Lifecycle section"
    )


def test_bug_rules_exactly_four_status_definitions():
    """bug-tracking-rules.md must contain exactly 4 status definitions."""
    content = BUG_RULES.read_text(encoding="utf-8")
    match = re.search(r"## Status Lifecycle\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    assert match, "Status Lifecycle section not found in bug-tracking-rules.md"
    lifecycle_section = match.group(1)
    statuses = re.findall(r"^\- \*\*(\w[\w ]*?)\*\*", lifecycle_section, re.MULTILINE)
    assert statuses == ["Open", "In Progress", "Fixed", "Closed"], (
        f"Expected exactly 4 statuses [Open, In Progress, Fixed, Closed], got {statuses}"
    )


def test_bug_rules_closed_definition_updated():
    """The Closed status definition must mention Tester verification."""
    content = BUG_RULES.read_text(encoding="utf-8")
    assert "Fix verified by Tester" in content, (
        "Closed definition must include 'Fix verified by Tester'"
    )


def test_bug_rules_finalize_note_present():
    """bug-tracking-rules.md must contain the finalize_wp.py auto-close note."""
    content = BUG_RULES.read_text(encoding="utf-8")
    assert "finalize_wp.py" in content, (
        "bug-tracking-rules.md must reference finalize_wp.py auto-close behaviour"
    )
    assert "update_bug_status.py" in content, (
        "bug-tracking-rules.md must reference update_bug_status.py as backup"
    )


# ---------------------------------------------------------------------------
# agent-workflow.md
# ---------------------------------------------------------------------------

def test_agent_workflow_update_bug_status_in_mandatory_table():
    """agent-workflow.md mandatory scripts table must contain update_bug_status.py."""
    content = AGENT_WORKFLOW.read_text(encoding="utf-8")
    assert "update_bug_status.py" in content, (
        "agent-workflow.md must reference update_bug_status.py in the mandatory scripts table"
    )
    # Confirm it appears inside a table row
    assert re.search(r"\|\s*Update bug status\s*\|\s*`scripts/update_bug_status\.py`", content), (
        "Mandatory scripts table row for update_bug_status.py not found"
    )


def test_agent_workflow_finalization_has_nine_steps():
    """agent-workflow.md Post-Done Finalization section must list exactly 9 numbered steps."""
    content = AGENT_WORKFLOW.read_text(encoding="utf-8")
    # Find the finalization numbered list block
    match = re.search(
        r"The script performs \*\*all\*\* finalization steps automatically:(.*?)(?=\nUse `--dry-run`)",
        content,
        re.DOTALL,
    )
    assert match, "Finalization steps list not found in agent-workflow.md"
    steps_block = match.group(1)
    steps = re.findall(r"^\d+\.", steps_block, re.MULTILINE)
    assert len(steps) == 9, (
        f"Expected 9 finalization steps, found {len(steps)}: {steps}"
    )


def test_agent_workflow_step_9_is_state_file_deletion():
    """agent-workflow.md finalization step 9 must mention .finalization-state.json deletion."""
    content = AGENT_WORKFLOW.read_text(encoding="utf-8")
    assert re.search(
        r"9\.\s+Deletes\s+`docs/workpackages/<WP-ID>/\.finalization-state\.json`",
        content,
    ), "Step 9 about .finalization-state.json deletion not found"


def test_agent_workflow_post_finalization_references_fix_flag():
    """agent-workflow.md post-finalization sanity check must reference --full --fix flag."""
    content = AGENT_WORKFLOW.read_text(encoding="utf-8")
    assert "validate_workspace.py --full --fix" in content, (
        "Post-finalization sanity check must reference 'validate_workspace.py --full --fix'"
    )


def test_agent_workflow_tester_checklist_item8_references_update_bug_status():
    """Tester PASS checklist item 8 must reference update_bug_status.py."""
    content = AGENT_WORKFLOW.read_text(encoding="utf-8")
    # Find item 8 in the checklist
    match = re.search(r"8\.\s+For each bug in.*?update_bug_status\.py", content, re.DOTALL)
    assert match, (
        "Tester PASS checklist item 8 must reference update_bug_status.py"
    )


# ---------------------------------------------------------------------------
# 2026-03-30-maintenance.md
# ---------------------------------------------------------------------------

def test_maintenance_log_all_phases_complete():
    """2026-03-30-maintenance.md Status section must say 'All phases complete'."""
    content = MAINTENANCE_LOG.read_text(encoding="utf-8")
    assert "All phases complete" in content, (
        "Maintenance log must state 'All phases complete'"
    )


def test_maintenance_log_fix083_listed():
    """2026-03-30-maintenance.md must list FIX-083 as Done."""
    content = MAINTENANCE_LOG.read_text(encoding="utf-8")
    assert "FIX-083 (Done)" in content, (
        "Maintenance log must list FIX-083 as Done"
    )
