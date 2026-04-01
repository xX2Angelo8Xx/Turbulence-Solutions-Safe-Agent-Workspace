"""
Edge-case tests for DOC-041: Additional coverage beyond developer tests.
Tests: model ordering, exclusivity, frontmatter structure integrity, coordinator tools.
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


def read_frontmatter(filename):
    path = AGENTS_DIR / filename
    content = path.read_text(encoding="utf-8")
    match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    assert match, f"No frontmatter found in {filename}"
    return match.group(1)


def test_coordinator_opus_listed_before_sonnet():
    """Opus must be the primary (first) model for coordinator — order matters."""
    frontmatter = read_frontmatter("coordinator.agent.md")
    # Extract the model line
    model_match = re.search(r"model:\s*\[(.*?)\]", frontmatter)
    assert model_match, "coordinator must have model array"
    model_values = model_match.group(1)
    opus_pos = model_values.find("Claude Opus 4.6")
    sonnet_pos = model_values.find("Claude Sonnet 4.6")
    assert opus_pos != -1, "Opus must be in coordinator model list"
    assert sonnet_pos != -1, "Sonnet must be in coordinator model list"
    assert opus_pos < sonnet_pos, "Opus must appear before Sonnet (primary model first)"


def test_planner_does_not_have_sonnet_model():
    """Planner is Opus-only — Sonnet should not be in its model field."""
    frontmatter = read_frontmatter("planner.agent.md")
    model_match = re.search(r"model:\s*\[(.*?)\]", frontmatter)
    assert model_match, "planner must have model array"
    model_values = model_match.group(1)
    assert "Claude Sonnet 4.6" not in model_values, "planner must NOT have Sonnet model"


def test_all_files_have_valid_frontmatter_delimiters():
    """Every agent file must open and close with ---."""
    for filename in AGENT_FILES:
        path = AGENTS_DIR / filename
        content = path.read_text(encoding="utf-8")
        assert content.startswith("---"), f"{filename}: frontmatter must start with ---"
        assert content.count("---") >= 2, f"{filename}: frontmatter must have opening and closing ---"


def test_all_files_have_description_field():
    """Every agent frontmatter must have a description field."""
    for filename in AGENT_FILES:
        frontmatter = read_frontmatter(filename)
        assert re.search(r"^description:", frontmatter, re.MULTILINE), \
            f"{filename}: must have a description field in frontmatter"


def test_coordinator_uses_vscode_tool_not_specialist():
    """Coordinator uses the broad `vscode` tool, not the specialist sub-tools."""
    frontmatter = read_frontmatter("coordinator.agent.md")
    tools_match = re.search(r"tools:\s*\[(.*?)\]", frontmatter)
    assert tools_match, "coordinator must have tools array"
    tool_values = tools_match.group(1)
    # coordinator should have 'vscode' as a standalone tool
    assert "vscode" in tool_values, "coordinator must have vscode tool"


def test_all_files_have_model_field():
    """Every agent file must have a model field in its frontmatter."""
    for filename in AGENT_FILES:
        frontmatter = read_frontmatter(filename)
        assert re.search(r"^model:", frontmatter, re.MULTILINE), \
            f"{filename}: must have a model field in frontmatter"


def test_all_files_have_tools_field():
    """Every agent file must have a tools field in its frontmatter."""
    for filename in AGENT_FILES:
        frontmatter = read_frontmatter(filename)
        assert re.search(r"^tools:", frontmatter, re.MULTILINE), \
            f"{filename}: must have a tools field in frontmatter"


def test_no_agent_uses_deprecated_model_name():
    """No agent should reference old/deprecated model names like 'gpt-4' or 'claude-3'."""
    deprecated = ["gpt-4", "claude-3", "claude-2", "Claude Opus 4.5", "Claude Sonnet 4.5"]
    for filename in AGENT_FILES:
        content = (AGENTS_DIR / filename).read_text(encoding="utf-8")
        for old_model in deprecated:
            assert old_model not in content, \
                f"{filename}: references deprecated model '{old_model}'"


def test_specialist_agents_model_is_single_sonnet():
    """Specialist agents (not coordinator/planner) should have exactly Sonnet — no other model."""
    specialist_agents = [
        "brainstormer.agent.md",
        "programmer.agent.md",
        "researcher.agent.md",
        "tester.agent.md",
        "workspace-cleaner.agent.md",
    ]
    for filename in specialist_agents:
        frontmatter = read_frontmatter(filename)
        model_match = re.search(r"model:\s*\[(.*?)\]", frontmatter)
        assert model_match, f"{filename} must have model array"
        model_values = model_match.group(1)
        assert "Claude Sonnet 4.6" in model_values, f"{filename} must have Sonnet"
        assert "Claude Opus" not in model_values, \
            f"{filename} must NOT have Opus (Sonnet-only agents)"
