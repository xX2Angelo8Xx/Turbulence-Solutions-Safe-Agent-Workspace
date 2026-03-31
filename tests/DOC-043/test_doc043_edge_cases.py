"""
Edge-case tests for DOC-043: Add Plan.md system to agent-workbench template
Written by Tester Agent — verifies correctness, consistency, and completeness.
"""

import os
import re
import pytest

TEMPLATE_ROOT = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "templates", "agent-workbench"
)

PLANNER_MD = os.path.join(TEMPLATE_ROOT, ".github", "agents", "planner.agent.md")
COORDINATOR_MD = os.path.join(TEMPLATE_ROOT, ".github", "agents", "coordinator.agent.md")
TIDYUP_MD = os.path.join(TEMPLATE_ROOT, ".github", "agents", "tidyup.agent.md")
AGENTDOCS_README = os.path.join(TEMPLATE_ROOT, "Project", "AgentDocs", "README.md")
AGENT_RULES = os.path.join(TEMPLATE_ROOT, "Project", "AGENT-RULES.md")
PLAN_MD = os.path.join(TEMPLATE_ROOT, "Project", "AgentDocs", "plan.md")


# ---------------------------------------------------------------------------
# Placeholder integrity — {{PROJECT_NAME}} must not have been silently removed
# ---------------------------------------------------------------------------

def test_planner_has_project_name_placeholder():
    """planner.agent.md must still contain {{PROJECT_NAME}} placeholder."""
    with open(PLANNER_MD, encoding="utf-8") as f:
        content = f.read()
    assert "{{PROJECT_NAME}}" in content, \
        "planner.agent.md is missing {{PROJECT_NAME}} placeholder — it may have been corrupted"


def test_coordinator_has_project_name_placeholder():
    """coordinator.agent.md must still contain {{PROJECT_NAME}} placeholder."""
    with open(COORDINATOR_MD, encoding="utf-8") as f:
        content = f.read()
    assert "{{PROJECT_NAME}}" in content, \
        "coordinator.agent.md is missing {{PROJECT_NAME}} placeholder — it may have been corrupted"


def test_tidyup_has_project_name_placeholder():
    """tidyup.agent.md must still contain {{PROJECT_NAME}} placeholder."""
    with open(TIDYUP_MD, encoding="utf-8") as f:
        content = f.read()
    assert "{{PROJECT_NAME}}" in content, \
        "tidyup.agent.md is missing {{PROJECT_NAME}} placeholder — it may have been corrupted"


def test_agent_rules_has_project_name_placeholder():
    """AGENT-RULES.md must still contain {{PROJECT_NAME}} placeholder."""
    with open(AGENT_RULES, encoding="utf-8") as f:
        content = f.read()
    assert "{{PROJECT_NAME}}" in content, \
        "AGENT-RULES.md is missing {{PROJECT_NAME}} placeholder — it may have been corrupted"


# ---------------------------------------------------------------------------
# plan.md template — structural completeness
# ---------------------------------------------------------------------------

def test_plan_md_tasks_table_has_required_columns():
    """plan.md Tasks table must have Task, Owner, Depends On, and Done? columns."""
    with open(PLAN_MD, encoding="utf-8") as f:
        content = f.read()
    # Find the header row of the table
    assert "Task" in content, "plan.md tasks table missing 'Task' column"
    assert "Owner" in content, "plan.md tasks table missing 'Owner' column"
    assert "Depends On" in content, "plan.md tasks table missing 'Depends On' column"
    assert "Done?" in content, "plan.md tasks table missing 'Done?' column"


def test_plan_md_tasks_table_is_markdown_table():
    """plan.md Tasks section must contain a properly formatted markdown table."""
    with open(PLAN_MD, encoding="utf-8") as f:
        content = f.read()
    # A markdown table has lines with | ... | ... |
    table_lines = [line for line in content.splitlines() if line.strip().startswith("|")]
    assert len(table_lines) >= 3, \
        "plan.md does not contain a markdown table (need header, separator, and at least one row)"


def test_plan_md_has_status_field():
    """plan.md header must include a Status field for lifecycle tracking."""
    with open(PLAN_MD, encoding="utf-8") as f:
        content = f.read()
    assert "Status:" in content, \
        "plan.md is missing a Status field (Draft / Active / Complete)"


def test_plan_md_status_options_listed():
    """plan.md status field must list Draft, Active, and Complete as options."""
    with open(PLAN_MD, encoding="utf-8") as f:
        content = f.read()
    assert "Draft" in content and "Active" in content and "Complete" in content, \
        "plan.md Status field should enumerate Draft, Active, Complete options"


def test_plan_md_all_four_sections_present():
    """plan.md must have exactly the 4 required sections as H2 headings."""
    with open(PLAN_MD, encoding="utf-8") as f:
        content = f.read()
    h2_sections = re.findall(r"^## (.+)", content, re.MULTILINE)
    required = {"Goal", "Tasks", "Acceptance Criteria", "Notes"}
    missing = required - set(h2_sections)
    assert not missing, f"plan.md is missing H2 section(s): {missing}"


# ---------------------------------------------------------------------------
# planner.agent.md — naming convention completeness
# ---------------------------------------------------------------------------

def test_planner_mentions_both_plan_md_and_plan_topic():
    """planner.agent.md must mention both 'plan.md' and 'plan-<topic>.md' naming forms."""
    with open(PLANNER_MD, encoding="utf-8") as f:
        content = f.read()
    assert "plan.md" in content, \
        "planner.agent.md does not mention 'plan.md' (the initial plan filename)"
    assert re.search(r"plan-\w+\.md|plan-<topic>\.md", content), \
        "planner.agent.md does not show a 'plan-<topic>.md' naming example"


def test_planner_primary_output_is_plan_file():
    """planner.agent.md must state that writing a plan file is the primary output."""
    with open(PLANNER_MD, encoding="utf-8") as f:
        content = f.read()
    # The primary output instruction appears in "How You Work"
    assert "primary output" in content.lower() or "write" in content.lower(), \
        "planner.agent.md does not establish plan file writing as primary output"


# ---------------------------------------------------------------------------
# coordinator.agent.md — plan file reading path
# ---------------------------------------------------------------------------

def test_coordinator_plan_reading_tied_to_progress_md():
    """coordinator.agent.md must link plan file discovery to progress.md."""
    with open(COORDINATOR_MD, encoding="utf-8") as f:
        content = f.read()
    # The Core Loop step should mention progress.md AND plan file together
    assert "progress.md" in content, \
        "coordinator.agent.md does not reference progress.md at all"
    # Ensure they appear in proximity (within 500 chars of each other)
    prog_idx = content.find("progress.md")
    plan_idx = content.lower().find("plan")
    assert abs(prog_idx - plan_idx) < 500, \
        "coordinator.agent.md mentions progress.md and plan files but not in close proximity"


def test_coordinator_step_2_reads_plan_file():
    """coordinator.agent.md Core Loop step 2 must explicitly read an active plan file."""
    with open(COORDINATOR_MD, encoding="utf-8") as f:
        content = f.read()
    # Step 2 was the newly added step — check it references "active plan"
    assert "active plan" in content.lower(), \
        "coordinator.agent.md does not mention 'active plan' in its Core Loop"


# ---------------------------------------------------------------------------
# AGENT-RULES.md section 1a — all 6 agents still present
# ---------------------------------------------------------------------------

def test_agent_rules_section_1a_lists_all_six_agents():
    """AGENT-RULES.md section 1a must list all 6 agents: Planner, Researcher, Brainstormer, Programmer, Tester, Coordinator."""
    with open(AGENT_RULES, encoding="utf-8") as f:
        content = f.read()
    required_agents = ["Planner", "Researcher", "Brainstormer", "Programmer", "Tester", "Coordinator"]
    missing = [a for a in required_agents if a not in content]
    assert not missing, \
        f"AGENT-RULES.md section 1a is missing agent(s): {missing}"


def test_agent_rules_section_1a_exists():
    """AGENT-RULES.md must contain a section 1a (AgentDocs sub-section)."""
    with open(AGENT_RULES, encoding="utf-8") as f:
        content = f.read()
    assert "## 1a" in content or "1a." in content or "### 1a" in content or "1a. AgentDocs" in content or "## 1a. AgentDocs" in content or "AgentDocs — Central Knowledge Base" in content, \
        "AGENT-RULES.md does not contain section 1a"


# ---------------------------------------------------------------------------
# AgentDocs/README.md — exception rule for plan files
# ---------------------------------------------------------------------------

def test_readme_rules_section_has_exception_for_plan_files():
    """AgentDocs/README.md Rules section must call out the plan file exception explicitly."""
    with open(AGENTDOCS_README, encoding="utf-8") as f:
        content = f.read()
    # The rule should contain "except" AND "plan"
    rules_section = content[content.lower().find("## rules"):] if "## rules" in content.lower() else content
    assert "except" in rules_section.lower() and "plan" in rules_section.lower(), \
        "AgentDocs/README.md Rules section does not state the exception for plan files"


def test_readme_standard_documents_table_has_plan_row():
    """AgentDocs/README.md Standard Documents table must include a plan.md / plan-*.md row."""
    with open(AGENTDOCS_README, encoding="utf-8") as f:
        content = f.read()
    # The table row should have plan.md AND plan-*.md
    assert "plan.md" in content and "plan-" in content, \
        "AgentDocs/README.md Standard Documents table is missing the plan.md / plan-*.md row"


# ---------------------------------------------------------------------------
# Cross-file consistency — all 3 agent files reference plan files coherently
# ---------------------------------------------------------------------------

def test_planner_and_readme_use_consistent_naming():
    """planner.agent.md and AgentDocs/README.md must use the same plan file naming pattern."""
    with open(PLANNER_MD, encoding="utf-8") as f:
        planner = f.read()
    with open(AGENTDOCS_README, encoding="utf-8") as f:
        readme = f.read()
    # Both should mention plan-*.md style sub-plans
    assert "plan-" in planner and "plan-" in readme, \
        "planner.agent.md and AgentDocs/README.md use inconsistent plan file naming"


def test_agent_rules_and_readme_consistent_plan_exception():
    """AGENT-RULES.md and AgentDocs/README.md must both allow Planner to create plan files."""
    with open(AGENT_RULES, encoding="utf-8") as f:
        rules = f.read()
    with open(AGENTDOCS_README, encoding="utf-8") as f:
        readme = f.read()
    # Both should mention the plan file exception
    assert "plan" in rules.lower() and "planner" in rules.lower(), \
        "AGENT-RULES.md does not connect Planner to plan files"
    assert "plan" in readme.lower() and "planner" in readme.lower(), \
        "AgentDocs/README.md does not connect Planner to plan files"
