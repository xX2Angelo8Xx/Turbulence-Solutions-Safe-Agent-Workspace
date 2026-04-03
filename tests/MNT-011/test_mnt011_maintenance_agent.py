"""Tests for MNT-011: Fix Maintenance Agent Definition.

Verifies that the three targeted fixes in .github/agents/maintenance.agent.md
are present and correct:
  1. Stale path fix: templates/coding/ replaced by templates/agent-workbench/
  2. Action-tracker step added to Workflow section
  3. YAML description updated from 9-point to 12-point checklist
"""

import pathlib

AGENT_FILE = pathlib.Path(__file__).parents[2] / ".github" / "agents" / "maintenance.agent.md"


def _read_agent():
    return AGENT_FILE.read_text(encoding="utf-8")


def test_stale_path_removed():
    """templates/coding/ must not appear anywhere in the file."""
    content = _read_agent()
    assert "templates/coding/" not in content


def test_correct_path_present():
    """templates/agent-workbench/ must appear in the Constraints section."""
    content = _read_agent()
    assert "templates/agent-workbench/" in content


def test_action_tracker_step_present():
    """The mandatory action-tracker.json update step must be in the Workflow section."""
    content = _read_agent()
    assert "action-tracker.json" in content
    assert "ACT-NNN" in content


def test_twelve_point_checklist_in_description():
    """YAML description must reference '12-point maintenance checklist'."""
    content = _read_agent()
    assert "12-point maintenance checklist" in content


def test_nine_point_checklist_absent():
    """YAML description must NOT reference '9-point maintenance checklist'."""
    content = _read_agent()
    assert "9-point maintenance checklist" not in content
