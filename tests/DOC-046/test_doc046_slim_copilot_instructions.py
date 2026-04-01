"""Tests for DOC-046: Slim copilot-instructions and update references."""
import pathlib
import re

TEMPLATE_ROOT = pathlib.Path(__file__).resolve().parents[2] / "templates" / "agent-workbench"
COPILOT_INSTRUCTIONS = TEMPLATE_ROOT / ".github" / "instructions" / "copilot-instructions.md"
AGENTS_DIR = TEMPLATE_ROOT / ".github" / "agents"
README = TEMPLATE_ROOT / "README.md"

AGENT_FILES = [
    "brainstormer.agent.md",
    "coordinator.agent.md",
    "planner.agent.md",
    "programmer.agent.md",
    "researcher.agent.md",
    "tester.agent.md",
    "workspace-cleaner.agent.md",
]


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def test_copilot_instructions_exists():
    assert COPILOT_INSTRUCTIONS.exists(), "copilot-instructions.md must exist"


def test_copilot_instructions_references_agentdocs_agent_rules():
    content = _read(COPILOT_INSTRUCTIONS)
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "copilot-instructions.md must reference AgentDocs/AGENT-RULES.md"
    )


def test_copilot_instructions_no_old_agent_rules_path():
    content = _read(COPILOT_INSTRUCTIONS)
    # Must not contain the old direct path (without AgentDocs/)
    # Pattern: PROJECT_NAME}}/AGENT-RULES.md but NOT AgentDocs/AGENT-RULES.md
    old_pattern = re.compile(r"\{\{PROJECT_NAME\}\}/AGENT-RULES\.md")
    assert not old_pattern.search(content), (
        "copilot-instructions.md must not contain the old "
        "{{PROJECT_NAME}}/AGENT-RULES.md path (without AgentDocs/)"
    )


def test_copilot_instructions_is_concise():
    lines = _read(COPILOT_INSTRUCTIONS).splitlines()
    assert len(lines) < 60, (
        f"copilot-instructions.md must be fewer than 60 lines, got {len(lines)}"
    )


def test_coordinator_agent_references_agentdocs():
    content = _read(AGENTS_DIR / "coordinator.agent.md")
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "coordinator.agent.md must reference AgentDocs/AGENT-RULES.md"
    )


def test_planner_agent_references_agentdocs():
    content = _read(AGENTS_DIR / "planner.agent.md")
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "planner.agent.md must reference AgentDocs/AGENT-RULES.md"
    )


def test_all_agent_files_reference_agentdocs():
    for filename in AGENT_FILES:
        path = AGENTS_DIR / filename
        assert path.exists(), f"{filename} must exist"
        content = _read(path)
        assert "AgentDocs/AGENT-RULES.md" in content, (
            f"{filename} must reference AgentDocs/AGENT-RULES.md"
        )


def test_all_agent_files_no_old_agent_rules_path():
    old_pattern = re.compile(r"\{\{PROJECT_NAME\}\}/AGENT-RULES\.md")
    for filename in AGENT_FILES:
        content = _read(AGENTS_DIR / filename)
        assert not old_pattern.search(content), (
            f"{filename} must not contain old {{{{PROJECT_NAME}}}}/AGENT-RULES.md path"
        )


def test_readme_references_agentdocs_agent_rules():
    content = _read(README)
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "README.md must reference AgentDocs/AGENT-RULES.md"
    )


def test_readme_no_old_agent_rules_path():
    content = _read(README)
    old_pattern = re.compile(r"\{\{PROJECT_NAME\}\}/AGENT-RULES\.md")
    assert not old_pattern.search(content), (
        "README.md must not contain the old {{PROJECT_NAME}}/AGENT-RULES.md path"
    )
