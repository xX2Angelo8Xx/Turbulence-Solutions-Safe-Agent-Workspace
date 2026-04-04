"""
Tests for DOC-043: Add Plan.md system to agent-workbench template
"""

import os
import pytest

TEMPLATE_ROOT = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "templates", "agent-workbench"
)

PLANNER_MD = os.path.join(TEMPLATE_ROOT, ".github", "agents", "planner.agent.md")
COORDINATOR_MD = os.path.join(TEMPLATE_ROOT, ".github", "agents", "coordinator.agent.md")
TIDYUP_MD = os.path.join(TEMPLATE_ROOT, ".github", "agents", "workspace-cleaner.agent.md")
AGENTDOCS_README = os.path.join(TEMPLATE_ROOT, "Project", "AgentDocs", "README.md")
AGENT_RULES = os.path.join(TEMPLATE_ROOT, "Project", "AgentDocs", "AGENT-RULES.md")
PLAN_MD = os.path.join(TEMPLATE_ROOT, "Project", "AgentDocs", "plan.md")


# ---------------------------------------------------------------------------
# plan.md template file
# ---------------------------------------------------------------------------

def test_plan_md_exists():
    """plan.md template file must exist in AgentDocs/."""
    assert os.path.isfile(PLAN_MD), f"plan.md not found at {PLAN_MD}"


def test_plan_md_has_goal_section():
    """plan.md must have a ## Goal section."""
    with open(PLAN_MD, encoding="utf-8") as f:
        content = f.read()
    assert "## Goal" in content, "plan.md is missing '## Goal' section"


def test_plan_md_has_tasks_section():
    """plan.md must have a ## Tasks section."""
    with open(PLAN_MD, encoding="utf-8") as f:
        content = f.read()
    assert "## Tasks" in content, "plan.md is missing '## Tasks' section"


def test_plan_md_has_acceptance_criteria():
    """plan.md must have a ## Acceptance Criteria section."""
    with open(PLAN_MD, encoding="utf-8") as f:
        content = f.read()
    assert "## Acceptance Criteria" in content, "plan.md is missing '## Acceptance Criteria' section"


def test_plan_md_has_notes_section():
    """plan.md must have a ## Notes section."""
    with open(PLAN_MD, encoding="utf-8") as f:
        content = f.read()
    assert "## Notes" in content, "plan.md is missing '## Notes' section"


# ---------------------------------------------------------------------------
# planner.agent.md
# ---------------------------------------------------------------------------

def test_planner_mentions_plan_file_writing():
    """planner.agent.md must mention writing a plan file as primary output."""
    with open(PLANNER_MD, encoding="utf-8") as f:
        content = f.read()
    assert "plan file" in content.lower(), \
        "planner.agent.md does not mention writing a plan file"


def test_planner_mentions_naming_convention():
    """planner.agent.md must describe the naming convention (plan.md / plan-<topic>.md)."""
    with open(PLANNER_MD, encoding="utf-8") as f:
        content = f.read()
    assert "plan-" in content, \
        "planner.agent.md does not describe the plan-<topic>.md naming convention"
    assert "Plan File Naming Convention" in content, \
        "planner.agent.md is missing 'Plan File Naming Convention' heading"


def test_planner_checks_existing_plans():
    """planner.agent.md must tell the agent to check for existing plan files first."""
    with open(PLANNER_MD, encoding="utf-8") as f:
        content = f.read()
    assert "existing plan" in content.lower(), \
        "planner.agent.md does not instruct checking for existing plan files"


# ---------------------------------------------------------------------------
# coordinator.agent.md
# ---------------------------------------------------------------------------

def test_coordinator_mentions_plan_file_execution():
    """coordinator.agent.md must mention executing plan files by name."""
    with open(COORDINATOR_MD, encoding="utf-8") as f:
        content = f.read()
    assert "plan-featureXY.md" in content or "plan file" in content.lower(), \
        "coordinator.agent.md does not mention executing plan files"


def test_coordinator_reads_active_plan():
    """coordinator.agent.md must mention reading the active plan from progress.md."""
    with open(COORDINATOR_MD, encoding="utf-8") as f:
        content = f.read()
    assert "active plan" in content.lower(), \
        "coordinator.agent.md does not mention reading the active plan file"


def test_coordinator_references_plan_in_progress():
    """coordinator.agent.md must mention updating progress.md to reference the active plan."""
    with open(COORDINATOR_MD, encoding="utf-8") as f:
        content = f.read()
    assert "progress.md" in content and "plan" in content.lower(), \
        "coordinator.agent.md does not connect progress.md to plan file reference"


# ---------------------------------------------------------------------------
# tidyup.agent.md
# ---------------------------------------------------------------------------

def test_workspace_cleaner_has_plan_file_section():
    """workspace-cleaner.agent.md must have a '### Plan files' audit section."""
    with open(TIDYUP_MD, encoding="utf-8") as f:
        content = f.read()
    assert "### Plan files" in content, \
        "workspace-cleaner.agent.md is missing '### Plan files' audit section"


def test_workspace_cleaner_checks_plan_completion():
    """workspace-cleaner.agent.md plan audit must check for completed plans."""
    with open(TIDYUP_MD, encoding="utf-8") as f:
        content = f.read()
    assert "completed" in content.lower() or "archiv" in content.lower(), \
        "workspace-cleaner.agent.md plan section does not mention checking for completed plans"


# ---------------------------------------------------------------------------
# AgentDocs/README.md
# ---------------------------------------------------------------------------

def test_readme_has_plan_file_row():
    """AgentDocs/README.md must include a table row for plan.md / plan-*.md."""
    with open(AGENTDOCS_README, encoding="utf-8") as f:
        content = f.read()
    assert "plan.md" in content, \
        "AgentDocs/README.md is missing a row for plan.md"


def test_readme_allows_plan_file_creation():
    """AgentDocs/README.md must explicitly allow Planner to create plan files."""
    with open(AGENTDOCS_README, encoding="utf-8") as f:
        content = f.read()
    assert "plan" in content.lower() and "except" in content.lower(), \
        "AgentDocs/README.md does not note the exception allowing plan file creation"


# ---------------------------------------------------------------------------
# AGENT-RULES.md
# ---------------------------------------------------------------------------

def test_agent_rules_maps_planner_to_plan_files():
    """AGENT-RULES.md must map Planner to plan files in the AgentDocs section."""
    with open(AGENT_RULES, encoding="utf-8") as f:
        content = f.read()
    assert "plan files" in content.lower() or "plan-*.md" in content, \
        "AGENT-RULES.md does not map Planner to plan files"


def test_agent_rules_coordinator_references_plan():
    """AGENT-RULES.md must mention Coordinator references active plan file."""
    with open(AGENT_RULES, encoding="utf-8") as f:
        content = f.read()
    assert "active plan" in content.lower(), \
        "AGENT-RULES.md does not note that Coordinator references the active plan file"


def test_agent_rules_tidyup_includes_plan_files():
    """AGENT-RULES.md must note that Tidyup audits plan files."""
    with open(AGENT_RULES, encoding="utf-8") as f:
        content = f.read()
    assert "including plan files" in content.lower() or (
        "tidyup" in content.lower() and "plan" in content.lower()
    ), "AGENT-RULES.md does not note that Tidyup audits plan files"
