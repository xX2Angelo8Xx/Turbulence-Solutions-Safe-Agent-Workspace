"""
Regression tests for FIX-103: Bulk-fix agent specification tests.

Verifies that the stale DOC-category test assertions have been corrected
to match the current 7-agent Agent Workbench roster and file structure.
"""
import pathlib
import re

TEMPLATE_ROOT = (
    pathlib.Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
)
AGENTS_DIR = TEMPLATE_ROOT / ".github" / "agents"
AGENTDOCS_DIR = TEMPLATE_ROOT / "Project" / "AgentDocs"

CURRENT_AGENTS = [
    "brainstormer", "coordinator", "planner", "programmer",
    "researcher", "tester", "workspace-cleaner"
]
REMOVED_AGENTS = [
    "scientist", "criticist", "fixer", "writer", "prototyper", "tidyup"
]


def test_current_seven_agents_exist():
    """All 7 current agent files must exist."""
    for name in CURRENT_AGENTS:
        path = AGENTS_DIR / f"{name}.agent.md"
        assert path.exists(), f"Missing agent file: {path}"


def test_removed_agents_do_not_exist():
    """Removed agent files must not exist (they were deleted in the redesign)."""
    for name in REMOVED_AGENTS:
        path = AGENTS_DIR / f"{name}.agent.md"
        assert not path.exists(), f"Removed agent still exists: {path}"


def test_agents_readme_exists():
    """agents/README.md must exist (was restored as part of redesign)."""
    readme = AGENTS_DIR / "README.md"
    assert readme.exists(), f"agents/README.md missing: {readme}"


def test_agentdocs_readme_exists():
    """Project/AgentDocs/README.md must exist."""
    readme = AGENTDOCS_DIR / "README.md"
    assert readme.exists(), f"AgentDocs/README.md missing: {readme}"


def test_agent_rules_in_agentdocs():
    """AGENT-RULES.md must be in Project/AgentDocs/ (not Project/)."""
    correct_path = AGENTDOCS_DIR / "AGENT-RULES.md"
    old_path = TEMPLATE_ROOT / "Project" / "AGENT-RULES.md"
    assert correct_path.exists(), f"AGENT-RULES.md missing from AgentDocs: {correct_path}"
    assert not old_path.exists(), f"AGENT-RULES.md still at old location: {old_path}"


def test_coordinator_has_six_agents():
    """coordinator.agent.md agents: list must have exactly 6 agents."""
    import yaml
    content = (AGENTS_DIR / "coordinator.agent.md").read_text(encoding="utf-8")
    end = content.find("---", 3)
    fm = yaml.safe_load(content[3:end].strip())
    agents = fm.get("agents", [])
    assert len(agents) == 6, f"Expected 6 agents, got {len(agents)}: {agents}"


def test_workspace_cleaner_replaces_tidyup():
    """workspace-cleaner.agent.md replaces tidyup.agent.md."""
    assert (AGENTS_DIR / "workspace-cleaner.agent.md").exists()
    assert not (AGENTS_DIR / "tidyup.agent.md").exists()


def test_no_stale_deleted_agent_refs_in_coordinator():
    """coordinator.agent.md must not reference removed agents."""
    content = (AGENTS_DIR / "coordinator.agent.md").read_text(encoding="utf-8")
    for deleted in ["Scientist", "Criticist", "Fixer", "Writer", "Prototyper", "Tidyup"]:
        assert deleted not in content, (
            f"coordinator.agent.md still references deleted agent '{deleted}'"
        )


def test_agents_readme_has_customization_guidance():
    """agents/README.md must contain customization guidance."""
    content = (AGENTS_DIR / "README.md").read_text(encoding="utf-8")
    assert "customiz" in content.lower() or "custom agent" in content.lower()
    unique_refs = set(re.findall(r"[\w-]+\.agent\.md", content))
    assert len(unique_refs) == 7, (
        f"README must reference exactly 7 .agent.md files, found {len(unique_refs)}: {sorted(unique_refs)}"
    )
