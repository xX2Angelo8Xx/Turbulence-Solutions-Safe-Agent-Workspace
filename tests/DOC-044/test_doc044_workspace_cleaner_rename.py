"""
DOC-044: Tests verifying the Tidyup → Workspace-Cleaner rename in the agent-workbench template.
"""

import re
from pathlib import Path

AGENTS_DIR = Path(__file__).parents[2] / "templates" / "agent-workbench" / ".github" / "agents"
CLEANER_FILE = AGENTS_DIR / "workspace-cleaner.agent.md"
TIDYUP_FILE = AGENTS_DIR / "tidyup.agent.md"
COORDINATOR_FILE = AGENTS_DIR / "coordinator.agent.md"
AGENT_RULES_FILE = (
    Path(__file__).parents[2]
    / "templates" / "agent-workbench" / "Project" / "AgentDocs" / "AGENT-RULES.md"
)
TEMPLATE_ROOT = Path(__file__).parents[2] / "templates" / "agent-workbench"


def test_workspace_cleaner_file_exists():
    """workspace-cleaner.agent.md must exist in the agents directory."""
    assert CLEANER_FILE.exists(), f"Missing: {CLEANER_FILE}"


def test_tidyup_file_does_not_exist():
    """tidyup.agent.md must NOT exist after the rename."""
    assert not TIDYUP_FILE.exists(), f"File should no longer exist: {TIDYUP_FILE}"


def test_workspace_cleaner_name_field():
    """workspace-cleaner.agent.md must have name: Workspace-Cleaner in frontmatter."""
    content = CLEANER_FILE.read_text(encoding="utf-8")
    assert re.search(r"^name:\s*Workspace-Cleaner\s*$", content, re.MULTILINE), (
        "name field in workspace-cleaner.agent.md must be 'Workspace-Cleaner'"
    )


def test_coordinator_agents_list_contains_workspace_cleaner():
    """coordinator.agent.md agents: frontmatter list must include Workspace-Cleaner."""
    content = COORDINATOR_FILE.read_text(encoding="utf-8")
    # Match the agents: [...] frontmatter list
    assert "Workspace-Cleaner" in content, (
        "coordinator.agent.md agents list must contain 'Workspace-Cleaner'"
    )


def test_coordinator_agents_list_does_not_contain_tidyup():
    """coordinator.agent.md agents: frontmatter list must NOT contain Tidyup."""
    content = COORDINATOR_FILE.read_text(encoding="utf-8")
    # Only check frontmatter section (before second ---)
    frontmatter_end = content.find("---", 3)
    frontmatter = content[:frontmatter_end]
    assert "Tidyup" not in frontmatter, (
        "coordinator.agent.md agents frontmatter must not contain 'Tidyup'"
    )


def test_coordinator_body_references_workspace_cleaner():
    """coordinator.agent.md body must reference @Workspace-Cleaner."""
    content = COORDINATOR_FILE.read_text(encoding="utf-8")
    assert "@Workspace-Cleaner" in content, (
        "coordinator.agent.md body must contain '@Workspace-Cleaner'"
    )


def test_coordinator_body_does_not_reference_tidyup():
    """coordinator.agent.md body must NOT reference @Tidyup."""
    content = COORDINATOR_FILE.read_text(encoding="utf-8")
    assert "@Tidyup" not in content, (
        "coordinator.agent.md body must not contain '@Tidyup'"
    )


def test_agent_rules_references_workspace_cleaner():
    """AGENT-RULES.md must reference Workspace-Cleaner in agent-to-doc mapping."""
    content = AGENT_RULES_FILE.read_text(encoding="utf-8")
    assert "Workspace-Cleaner" in content, (
        "AGENT-RULES.md must contain 'Workspace-Cleaner'"
    )


def test_agent_rules_does_not_reference_tidyup():
    """AGENT-RULES.md must NOT reference Tidyup."""
    content = AGENT_RULES_FILE.read_text(encoding="utf-8")
    assert "Tidyup" not in content, (
        "AGENT-RULES.md must not contain 'Tidyup'"
    )


def test_no_tidyup_references_in_any_agent_file():
    """No agent .md file in the template should contain 'Tidyup'."""
    tidyup_found = []
    for md_file in TEMPLATE_ROOT.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        if "Tidyup" in text:
            tidyup_found.append(str(md_file.relative_to(TEMPLATE_ROOT)))
    assert not tidyup_found, (
        f"'Tidyup' still referenced in: {tidyup_found}"
    )
