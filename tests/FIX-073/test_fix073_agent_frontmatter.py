"""
Tests for FIX-073: Fix template agent YAML frontmatter.

Verifies that:
- All 7 agent files use correct VS Code tool categories (not individual tool names)
- All 7 agent files have the correct model syntax
- No old individual tool names remain in any agent frontmatter
- Planner has vscode/askQuestions and edit tools
- README example shows correct tool category syntax
"""
import pathlib
import yaml

AGENTS_DIR = (
    pathlib.Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
    / ".github"
    / "agents"
)

AGENT_FILES = {
    "programmer": AGENTS_DIR / "programmer.agent.md",
    "brainstormer": AGENTS_DIR / "brainstormer.agent.md",
    "tester": AGENTS_DIR / "tester.agent.md",
    "researcher": AGENTS_DIR / "researcher.agent.md",
    "coordinator": AGENTS_DIR / "coordinator.agent.md",
    "planner": AGENTS_DIR / "planner.agent.md",
    "workspace-cleaner": AGENTS_DIR / "workspace-cleaner.agent.md",
}

EXPECTED_TOOLS = {
    "programmer": ["vscode/memory", "vscode/vscodeAPI", "vscode/askQuestions", "execute", "read", "agent", "edit", "search", "todo"],
    "brainstormer": ["vscode/memory", "vscode/vscodeAPI", "vscode/askQuestions", "read", "agent", "edit", "search", "web/fetch", "browser"],
    "tester": ["vscode/memory", "vscode/vscodeAPI", "vscode/askQuestions", "execute", "read", "edit", "search", "todo"],
    "researcher": ["vscode/memory", "vscode/vscodeAPI", "vscode/askQuestions", "read", "agent", "edit", "search", "web", "browser"],
    "coordinator": ["vscode", "execute", "read", "agent", "edit", "search", "web/githubRepo", "todo"],
    "planner": ["vscode/memory", "vscode/vscodeAPI", "vscode/askQuestions", "read", "agent", "edit", "search"],
    "workspace-cleaner": ["vscode/memory", "vscode/vscodeAPI", "vscode/askQuestions", "execute", "read", "agent", "edit", "search", "todo"],
}

SONNET_MODEL = ["Claude Sonnet 4.6 (copilot)"]
OPUS_MODEL = ["Claude Opus 4.6 (copilot)"]
COORDINATOR_MODEL = ["Claude Opus 4.6 (copilot)", "Claude Sonnet 4.6 (copilot)"]

# Old individual tool names that must NOT appear in any agent frontmatter
OLD_TOOL_NAMES = [
    "read_file",
    "create_file",
    "replace_string_in_file",
    "multi_replace_string_in_file",
    "file_search",
    "grep_search",
    "semantic_search",
    "run_in_terminal",
    "fetch_webpage",
]


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) from YAML-frontmatter markdown."""
    if not text.startswith("---"):
        return {}, text
    end = text.index("---", 3)
    yaml_block = text[3:end].strip()
    body = text[end + 3:].strip()
    return yaml.safe_load(yaml_block) or {}, body


# ---------------------------------------------------------------------------
# Tool list correctness per agent
# ---------------------------------------------------------------------------

def test_programmer_tools():
    """programmer.agent.md must have correct tool categories."""
    fm, _ = _parse_frontmatter(AGENT_FILES["programmer"].read_text(encoding="utf-8"))
    assert set(fm.get("tools", [])) == set(EXPECTED_TOOLS["programmer"]), (
        f"Programmer tools mismatch: {fm.get('tools')} != {EXPECTED_TOOLS['programmer']}"
    )


def test_brainstormer_tools():
    """brainstormer.agent.md must have correct tool categories."""
    fm, _ = _parse_frontmatter(AGENT_FILES["brainstormer"].read_text(encoding="utf-8"))
    assert set(fm.get("tools", [])) == set(EXPECTED_TOOLS["brainstormer"]), (
        f"Brainstormer tools mismatch: {fm.get('tools')} != {EXPECTED_TOOLS['brainstormer']}"
    )


def test_tester_tools():
    """tester.agent.md must have correct tool categories."""
    fm, _ = _parse_frontmatter(AGENT_FILES["tester"].read_text(encoding="utf-8"))
    assert set(fm.get("tools", [])) == set(EXPECTED_TOOLS["tester"]), (
        f"Tester tools mismatch: {fm.get('tools')} != {EXPECTED_TOOLS['tester']}"
    )


def test_researcher_tools():
    """researcher.agent.md must have correct tool categories (no fetch_webpage)."""
    fm, _ = _parse_frontmatter(AGENT_FILES["researcher"].read_text(encoding="utf-8"))
    assert set(fm.get("tools", [])) == set(EXPECTED_TOOLS["researcher"]), (
        f"Researcher tools mismatch: {fm.get('tools')} != {EXPECTED_TOOLS['researcher']}"
    )


def test_coordinator_tools():
    """coordinator.agent.md must have correct tool categories."""
    fm, _ = _parse_frontmatter(AGENT_FILES["coordinator"].read_text(encoding="utf-8"))
    assert set(fm.get("tools", [])) == set(EXPECTED_TOOLS["coordinator"]), (
        f"Coordinator tools mismatch: {fm.get('tools')} != {EXPECTED_TOOLS['coordinator']}"
    )


def test_planner_tools():
    """planner.agent.md must have correct tool categories including vscode/askQuestions and edit."""
    fm, _ = _parse_frontmatter(AGENT_FILES["planner"].read_text(encoding="utf-8"))
    assert set(fm.get("tools", [])) == set(EXPECTED_TOOLS["planner"]), (
        f"Planner tools mismatch: {fm.get('tools')} != {EXPECTED_TOOLS['planner']}"
    )


def test_workspace_cleaner_tools():
    """workspace-cleaner.agent.md must have correct tool categories."""
    fm, _ = _parse_frontmatter(AGENT_FILES["workspace-cleaner"].read_text(encoding="utf-8"))
    assert set(fm.get("tools", [])) == set(EXPECTED_TOOLS["workspace-cleaner"]), (
        f"Workspace-cleaner tools mismatch: {fm.get('tools')} != {EXPECTED_TOOLS['workspace-cleaner']}"
    )


# ---------------------------------------------------------------------------
# Model correctness per agent
# ---------------------------------------------------------------------------

def test_programmer_model():
    """programmer.agent.md must use Claude Sonnet 4.6 (copilot)."""
    fm, _ = _parse_frontmatter(AGENT_FILES["programmer"].read_text(encoding="utf-8"))
    assert fm.get("model") == SONNET_MODEL, f"Programmer model: {fm.get('model')}"


def test_brainstormer_model():
    """brainstormer.agent.md must use Claude Sonnet 4.6 (copilot)."""
    fm, _ = _parse_frontmatter(AGENT_FILES["brainstormer"].read_text(encoding="utf-8"))
    assert fm.get("model") == SONNET_MODEL, f"Brainstormer model: {fm.get('model')}"


def test_tester_model():
    """tester.agent.md must use Claude Sonnet 4.6 (copilot)."""
    fm, _ = _parse_frontmatter(AGENT_FILES["tester"].read_text(encoding="utf-8"))
    assert fm.get("model") == SONNET_MODEL, f"Tester model: {fm.get('model')}"


def test_researcher_model():
    """researcher.agent.md must use Claude Sonnet 4.6 (copilot)."""
    fm, _ = _parse_frontmatter(AGENT_FILES["researcher"].read_text(encoding="utf-8"))
    assert fm.get("model") == SONNET_MODEL, f"Researcher model: {fm.get('model')}"


def test_coordinator_model():
    """coordinator.agent.md must have both Opus and Sonnet models."""
    fm, _ = _parse_frontmatter(AGENT_FILES["coordinator"].read_text(encoding="utf-8"))
    assert fm.get("model") == COORDINATOR_MODEL, f"Coordinator model: {fm.get('model')}"


def test_planner_model():
    """planner.agent.md must use Claude Opus 4.6 (copilot)."""
    fm, _ = _parse_frontmatter(AGENT_FILES["planner"].read_text(encoding="utf-8"))
    assert fm.get("model") == OPUS_MODEL, f"Planner model: {fm.get('model')}"


def test_workspace_cleaner_model():
    """workspace-cleaner.agent.md must use Claude Sonnet 4.6 (copilot)."""
    fm, _ = _parse_frontmatter(AGENT_FILES["workspace-cleaner"].read_text(encoding="utf-8"))
    assert fm.get("model") == SONNET_MODEL, f"Workspace-cleaner model: {fm.get('model')}"


# ---------------------------------------------------------------------------
# No old individual tool names remain in any frontmatter
# ---------------------------------------------------------------------------

def test_no_old_tool_names_in_any_agent():
    """No old individual tool names should appear in any agent's frontmatter tools list."""
    for agent_name, agent_path in AGENT_FILES.items():
        fm, _ = _parse_frontmatter(agent_path.read_text(encoding="utf-8"))
        tools = fm.get("tools", [])
        old_found = [t for t in OLD_TOOL_NAMES if t in tools]
        assert not old_found, (
            f"{agent_name}.agent.md still has old tool names in frontmatter: {old_found}"
        )


def test_fetch_webpage_not_in_any_agent():
    """fetch_webpage must not appear in any agent's tools list."""
    for agent_name, agent_path in AGENT_FILES.items():
        fm, _ = _parse_frontmatter(agent_path.read_text(encoding="utf-8"))
        tools = fm.get("tools", [])
        assert "fetch_webpage" not in tools, (
            f"{agent_name}.agent.md still has fetch_webpage in tools"
        )


# ---------------------------------------------------------------------------
# Planner-specific requirements (BUG-109)
# ---------------------------------------------------------------------------

def test_planner_has_ask_tool():
    """Planner must have 'vscode/askQuestions' tool for clarifying questions (BUG-109)."""
    fm, _ = _parse_frontmatter(AGENT_FILES["planner"].read_text(encoding="utf-8"))
    assert "vscode/askQuestions" in fm.get("tools", []), "Planner must have 'vscode/askQuestions' tool"


def test_planner_has_edit_tool():
    """Planner must have 'edit' tool for creating plan.md (BUG-109)."""
    fm, _ = _parse_frontmatter(AGENT_FILES["planner"].read_text(encoding="utf-8"))
    assert "edit" in fm.get("tools", []), "Planner must have 'edit' tool"


def test_planner_body_mentions_plan_md():
    """Planner body must describe the ability to create plan.md files (BUG-109)."""
    _, body = _parse_frontmatter(AGENT_FILES["planner"].read_text(encoding="utf-8"))
    assert "plan.md" in body, "Planner body must mention plan.md capability"


def test_planner_body_mentions_ask_capability():
    """Planner body must describe asking clarifying questions (BUG-109)."""
    _, body = _parse_frontmatter(AGENT_FILES["planner"].read_text(encoding="utf-8"))
    body_lower = body.lower()
    assert "ask" in body_lower and ("clarif" in body_lower or "question" in body_lower), (
        "Planner body must describe ask/clarifying question capability"
    )


def test_planner_no_longer_says_no_edit_tools():
    """Planner body must not say 'You have no edit tools by design' (BUG-109 fix)."""
    _, body = _parse_frontmatter(AGENT_FILES["planner"].read_text(encoding="utf-8"))
    assert "no edit tools by design" not in body.lower(), (
        "Planner body still contains 'no edit tools by design' — this must be removed (BUG-109)"
    )


# ---------------------------------------------------------------------------
# README example syntax
# ---------------------------------------------------------------------------

def test_readme_example_uses_category_tools():
    """README.md example frontmatter must show VS Code tool categories, not individual names."""
    readme = (AGENTS_DIR / "README.md").read_text(encoding="utf-8")
    assert "tools: [read, edit, search]" in readme, (
        "README.md example must show 'tools: [read, edit, search]'"
    )


def test_readme_example_uses_correct_model():
    """README.md example frontmatter must show the correct Copilot model."""
    readme = (AGENTS_DIR / "README.md").read_text(encoding="utf-8")
    assert "Claude Sonnet 4.6 (copilot)" in readme, (
        "README.md example must reference 'Claude Sonnet 4.6 (copilot)'"
    )


def test_readme_no_old_model():
    """README.md example must not show the old claude-sonnet-4-5 model."""
    readme = (AGENTS_DIR / "README.md").read_text(encoding="utf-8")
    assert "claude-sonnet-4-5" not in readme, (
        "README.md example still references old model 'claude-sonnet-4-5'"
    )
