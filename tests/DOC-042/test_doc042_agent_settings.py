"""
DOC-042: Tests verifying agent default model and tools settings
in templates/agent-workbench/.github/agents/
"""
import pathlib
import re

AGENTS_DIR = (
    pathlib.Path(__file__).parent.parent.parent
    / "templates"
    / "agent-workbench"
    / ".github"
    / "agents"
)

AGENT_FILES = {
    "brainstormer": AGENTS_DIR / "brainstormer.agent.md",
    "coordinator": AGENTS_DIR / "coordinator.agent.md",
    "planner": AGENTS_DIR / "planner.agent.md",
    "programmer": AGENTS_DIR / "programmer.agent.md",
    "researcher": AGENTS_DIR / "researcher.agent.md",
    "tester": AGENTS_DIR / "tester.agent.md",
    "workspace-cleaner": AGENTS_DIR / "workspace-cleaner.agent.md",
}

SONNET_AGENTS = ["brainstormer", "programmer", "researcher", "tester", "workspace-cleaner"]
OPUS_AGENTS = ["planner"]

COMMON_TOOLS = ["vscode/memory", "vscode/vscodeAPI", "vscode/askQuestions"]

EXPECTED_TOOLS = {
    "brainstormer": ["vscode/memory", "vscode/vscodeAPI", "vscode/askQuestions", "read", "agent", "edit", "search", "web/fetch", "browser"],
    "coordinator": ["read", "agent", "edit", "search"],
    "planner": ["vscode/memory", "vscode/vscodeAPI", "vscode/askQuestions", "read", "agent", "edit", "search"],
    "programmer": ["vscode/memory", "vscode/vscodeAPI", "vscode/askQuestions", "execute", "read", "agent", "edit", "search", "todo"],
    "researcher": ["vscode/memory", "vscode/vscodeAPI", "vscode/askQuestions", "read", "agent", "edit", "search", "web", "browser"],
    "tester": ["vscode/memory", "vscode/vscodeAPI", "vscode/askQuestions", "execute", "read", "edit", "search", "todo"],
    "workspace-cleaner": ["vscode/memory", "vscode/vscodeAPI", "vscode/askQuestions", "execute", "read", "agent", "edit", "search", "todo"],
}

COORDINATOR_AGENTS = ["Programmer", "Tester", "Brainstormer", "Researcher", "Planner", "Workspace-Cleaner"]


def _read_frontmatter(agent_name: str) -> str:
    """Read and return the YAML frontmatter block of an agent file."""
    content = AGENT_FILES[agent_name].read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert match, f"{agent_name}.agent.md: frontmatter block not found"
    return match.group(1)


# ── Existence tests ───────────────────────────────────────────────────────────

def test_brainstormer_file_exists():
    assert AGENT_FILES["brainstormer"].is_file()

def test_coordinator_file_exists():
    assert AGENT_FILES["coordinator"].is_file()

def test_planner_file_exists():
    assert AGENT_FILES["planner"].is_file()

def test_programmer_file_exists():
    assert AGENT_FILES["programmer"].is_file()

def test_researcher_file_exists():
    assert AGENT_FILES["researcher"].is_file()

def test_tester_file_exists():
    assert AGENT_FILES["tester"].is_file()

def test_workspace_cleaner_file_exists():
    assert AGENT_FILES["workspace-cleaner"].is_file()


# ── Model tests ───────────────────────────────────────────────────────────────

def test_sonnet_agents_use_sonnet_model():
    for name in SONNET_AGENTS:
        fm = _read_frontmatter(name)
        assert "Claude Sonnet 4.6 (copilot)" in fm, (
            f"{name}.agent.md should use Claude Sonnet 4.6, got: {fm}"
        )

def test_planner_uses_opus_model():
    fm = _read_frontmatter("planner")
    assert "Claude Opus 4.6 (copilot)" in fm, (
        f"planner.agent.md should retain Claude Opus 4.6, got: {fm}"
    )

def test_no_sonnet_agent_uses_opus():
    for name in SONNET_AGENTS:
        fm = _read_frontmatter(name)
        assert "Claude Opus" not in fm, (
            f"{name}.agent.md must not use Claude Opus, got: {fm}"
        )


# ── Tools tests ───────────────────────────────────────────────────────────────

def test_brainstormer_tools():
    fm = _read_frontmatter("brainstormer")
    for tool in EXPECTED_TOOLS["brainstormer"]:
        assert tool in fm, f"brainstormer.agent.md missing tool: {tool}"

def test_planner_tools():
    fm = _read_frontmatter("planner")
    for tool in EXPECTED_TOOLS["planner"]:
        assert tool in fm, f"planner.agent.md missing tool: {tool}"

def test_programmer_tools():
    fm = _read_frontmatter("programmer")
    for tool in EXPECTED_TOOLS["programmer"]:
        assert tool in fm, f"programmer.agent.md missing tool: {tool}"

def test_researcher_tools():
    fm = _read_frontmatter("researcher")
    for tool in EXPECTED_TOOLS["researcher"]:
        assert tool in fm, f"researcher.agent.md missing tool: {tool}"

def test_tester_tools():
    fm = _read_frontmatter("tester")
    for tool in EXPECTED_TOOLS["tester"]:
        assert tool in fm, f"tester.agent.md missing tool: {tool}"

def test_workspace_cleaner_tools():
    fm = _read_frontmatter("workspace-cleaner")
    for tool in EXPECTED_TOOLS["workspace-cleaner"]:
        assert tool in fm, f"workspace-cleaner.agent.md missing tool: {tool}"

def test_coordinator_tools():
    fm = _read_frontmatter("coordinator")
    for tool in EXPECTED_TOOLS["coordinator"]:
        assert tool in fm, f"coordinator.agent.md missing tool: {tool}"


# ── Coordinator agents field ──────────────────────────────────────────────────

def test_coordinator_has_agents_field():
    fm = _read_frontmatter("coordinator")
    assert "agents:" in fm, "coordinator.agent.md must have an agents: field"

def test_coordinator_lists_all_specialist_agents():
    fm = _read_frontmatter("coordinator")
    for specialist in COORDINATOR_AGENTS:
        assert specialist in fm, (
            f"coordinator.agent.md agents: field missing: {specialist}"
        )


# ── Workspace-Cleaner argument-hint ──────────────────────────────────────────

def test_workspace_cleaner_has_argument_hint():
    fm = _read_frontmatter("workspace-cleaner")
    assert "argument-hint" in fm, "workspace-cleaner.agent.md must have an argument-hint field"
