"""Tests for DOC-018: Create agents/ directory in Agent Workbench template."""
import os
import pytest

TEMPLATE_ROOT = os.path.join(
    os.path.dirname(__file__), "..", "..", "templates", "agent-workbench"
)
AGENTS_DIR = os.path.join(TEMPLATE_ROOT, ".github", "agents")
AGENTS_README = os.path.join(AGENTS_DIR, "README.md")
COPILOT_INSTRUCTIONS = os.path.join(
    TEMPLATE_ROOT, ".github", "instructions", "copilot-instructions.md"
)
AGENT_RULES = os.path.join(TEMPLATE_ROOT, "Project", "AgentDocs", "AGENT-RULES.md")

EXPECTED_AGENTS = [
    "programmer",
    "brainstormer",
    "tester",
    "researcher",
    "planner",
    "coordinator",
    "workspace-cleaner",
]


def test_agents_directory_exists():
    """agents/ directory must exist inside .github/."""
    assert os.path.isdir(AGENTS_DIR), f"Expected directory: {AGENTS_DIR}"


def test_agents_readme_exists():
    """README.md must be present in agents/ directory."""
    assert os.path.isfile(AGENTS_README), f"Expected file: {AGENTS_README}"


def test_agents_readme_mentions_all_agents():
    """README.md must mention every agent in the expected roster."""
    with open(AGENTS_README, encoding="utf-8") as f:
        content = f.read().lower()
    for agent in EXPECTED_AGENTS:
        assert agent in content, f"README.md missing agent: {agent}"


def test_agents_readme_contains_customization_instructions():
    """README.md must include customization guidance."""
    with open(AGENTS_README, encoding="utf-8") as f:
        content = f.read()
    assert "customize" in content.lower() or "customiz" in content.lower(), (
        "README.md must contain customization instructions"
    )
    assert ".agent.md" in content, "README.md must reference .agent.md file format"


def test_copilot_instructions_references_agents():
    """copilot-instructions.md must reference the agents/ directory."""
    with open(COPILOT_INSTRUCTIONS, encoding="utf-8") as f:
        content = f.read()
    assert ".github/agents" in content or "agents/" in content, (
        "copilot-instructions.md must reference agents/ directory"
    )


def test_agent_rules_has_available_agents_section():
    """AGENT-RULES.md must have a section documenting available agent personas."""
    with open(AGENT_RULES, encoding="utf-8") as f:
        content = f.read()
    assert "Workspace-Cleaner" in content or "workspace-cleaner" in content.lower() or "1a" in content, (
        "AGENT-RULES.md must contain a section listing agent personas"
    )


def test_agent_rules_lists_all_agents():
    """AGENT-RULES.md must mention all current agents by name."""
    with open(AGENT_RULES, encoding="utf-8") as f:
        content = f.read().lower()
    for agent in EXPECTED_AGENTS:
        assert agent in content, f"AGENT-RULES.md missing agent: {agent}"
