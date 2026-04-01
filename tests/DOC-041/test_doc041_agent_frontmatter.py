"""
Tests for DOC-041: Verify all 7 agent frontmatter files have correct model and tools fields.
"""
import re
from pathlib import Path

AGENTS_DIR = Path(__file__).parent.parent.parent / "templates" / "agent-workbench" / ".github" / "agents"

AGENT_FILES = [
    "brainstormer.agent.md",
    "coordinator.agent.md",
    "planner.agent.md",
    "programmer.agent.md",
    "researcher.agent.md",
    "tester.agent.md",
    "workspace-cleaner.agent.md",
]

SPECIALIST_TOOLS = ["vscode/memory", "vscode/vscodeAPI", "vscode/askQuestions"]


def read_frontmatter(filename):
    path = AGENTS_DIR / filename
    content = path.read_text(encoding="utf-8")
    match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    assert match, f"No frontmatter found in {filename}"
    return match.group(1)


def test_all_agent_files_exist():
    for filename in AGENT_FILES:
        assert (AGENTS_DIR / filename).exists(), f"Missing agent file: {filename}"


def test_coordinator_model_two_model_fallback():
    frontmatter = read_frontmatter("coordinator.agent.md")
    assert "Claude Opus 4.6 (copilot)" in frontmatter, "coordinator must have Opus model"
    assert "Claude Sonnet 4.6 (copilot)" in frontmatter, "coordinator must have Sonnet fallback"


def test_planner_retains_opus():
    frontmatter = read_frontmatter("planner.agent.md")
    assert "Claude Opus 4.6 (copilot)" in frontmatter, "planner must use Opus"


def test_brainstormer_uses_sonnet():
    frontmatter = read_frontmatter("brainstormer.agent.md")
    assert "Claude Sonnet 4.6 (copilot)" in frontmatter, "brainstormer must use Sonnet"


def test_programmer_uses_sonnet():
    frontmatter = read_frontmatter("programmer.agent.md")
    assert "Claude Sonnet 4.6 (copilot)" in frontmatter, "programmer must use Sonnet"


def test_researcher_uses_sonnet():
    frontmatter = read_frontmatter("researcher.agent.md")
    assert "Claude Sonnet 4.6 (copilot)" in frontmatter, "researcher must use Sonnet"


def test_tester_uses_sonnet():
    frontmatter = read_frontmatter("tester.agent.md")
    assert "Claude Sonnet 4.6 (copilot)" in frontmatter, "tester must use Sonnet"


def test_workspace_cleaner_uses_sonnet():
    frontmatter = read_frontmatter("workspace-cleaner.agent.md")
    assert "Claude Sonnet 4.6 (copilot)" in frontmatter, "workspace-cleaner must use Sonnet"


def test_specialist_agents_have_expanded_tools():
    specialist_agents = [
        "brainstormer.agent.md",
        "planner.agent.md",
        "programmer.agent.md",
        "researcher.agent.md",
        "tester.agent.md",
        "workspace-cleaner.agent.md",
    ]
    for filename in specialist_agents:
        frontmatter = read_frontmatter(filename)
        for tool in SPECIALIST_TOOLS:
            assert tool in frontmatter, f"{filename} must have tool: {tool}"


def test_coordinator_model_array_format():
    frontmatter = read_frontmatter("coordinator.agent.md")
    assert re.search(r"model:\s*\[", frontmatter), "coordinator model must be array format"


def test_planner_tools_include_expected():
    frontmatter = read_frontmatter("planner.agent.md")
    assert "read" in frontmatter
    assert "edit" in frontmatter
    assert "search" in frontmatter
