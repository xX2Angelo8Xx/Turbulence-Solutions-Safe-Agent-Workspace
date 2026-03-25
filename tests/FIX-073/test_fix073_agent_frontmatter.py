"""
Tests for FIX-073: Fix template agent YAML frontmatter.

Verifies that:
- All 10 agent files use correct VS Code tool categories (not individual tool names)
- All 10 agent files have the correct model syntax
- No old individual tool names remain in any agent frontmatter
- Planner has ask and edit tools
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
    "scientist": AGENTS_DIR / "scientist.agent.md",
    "criticist": AGENTS_DIR / "criticist.agent.md",
    "planner": AGENTS_DIR / "planner.agent.md",
    "fixer": AGENTS_DIR / "fixer.agent.md",
    "writer": AGENTS_DIR / "writer.agent.md",
    "prototyper": AGENTS_DIR / "prototyper.agent.md",
}

EXPECTED_TOOLS = {
    "programmer": ["read", "edit", "search", "execute"],
    "brainstormer": ["read", "search"],
    "tester": ["read", "edit", "search", "execute"],
    "researcher": ["read", "search"],
    "scientist": ["read", "edit", "search", "execute"],
    "criticist": ["read", "search"],
    "planner": ["read", "search", "ask", "edit"],
    "fixer": ["read", "edit", "search", "execute"],
    "writer": ["read", "edit", "search"],
    "prototyper": ["read", "edit", "search", "execute"],
}

CORRECT_MODEL = ["Claude Opus 4.6 (copilot)"]

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


def test_scientist_tools():
    """scientist.agent.md must have correct tool categories."""
    fm, _ = _parse_frontmatter(AGENT_FILES["scientist"].read_text(encoding="utf-8"))
    assert set(fm.get("tools", [])) == set(EXPECTED_TOOLS["scientist"]), (
        f"Scientist tools mismatch: {fm.get('tools')} != {EXPECTED_TOOLS['scientist']}"
    )


def test_criticist_tools():
    """criticist.agent.md must have correct tool categories."""
    fm, _ = _parse_frontmatter(AGENT_FILES["criticist"].read_text(encoding="utf-8"))
    assert set(fm.get("tools", [])) == set(EXPECTED_TOOLS["criticist"]), (
        f"Criticist tools mismatch: {fm.get('tools')} != {EXPECTED_TOOLS['criticist']}"
    )


def test_planner_tools():
    """planner.agent.md must have correct tool categories including ask and edit."""
    fm, _ = _parse_frontmatter(AGENT_FILES["planner"].read_text(encoding="utf-8"))
    assert set(fm.get("tools", [])) == set(EXPECTED_TOOLS["planner"]), (
        f"Planner tools mismatch: {fm.get('tools')} != {EXPECTED_TOOLS['planner']}"
    )


def test_fixer_tools():
    """fixer.agent.md must have correct tool categories."""
    fm, _ = _parse_frontmatter(AGENT_FILES["fixer"].read_text(encoding="utf-8"))
    assert set(fm.get("tools", [])) == set(EXPECTED_TOOLS["fixer"]), (
        f"Fixer tools mismatch: {fm.get('tools')} != {EXPECTED_TOOLS['fixer']}"
    )


def test_writer_tools():
    """writer.agent.md must have correct tool categories (no execute)."""
    fm, _ = _parse_frontmatter(AGENT_FILES["writer"].read_text(encoding="utf-8"))
    assert set(fm.get("tools", [])) == set(EXPECTED_TOOLS["writer"]), (
        f"Writer tools mismatch: {fm.get('tools')} != {EXPECTED_TOOLS['writer']}"
    )


def test_prototyper_tools():
    """prototyper.agent.md must have correct tool categories."""
    fm, _ = _parse_frontmatter(AGENT_FILES["prototyper"].read_text(encoding="utf-8"))
    assert set(fm.get("tools", [])) == set(EXPECTED_TOOLS["prototyper"]), (
        f"Prototyper tools mismatch: {fm.get('tools')} != {EXPECTED_TOOLS['prototyper']}"
    )


# ---------------------------------------------------------------------------
# Model correctness per agent
# ---------------------------------------------------------------------------

def test_programmer_model():
    """programmer.agent.md must have correct model."""
    fm, _ = _parse_frontmatter(AGENT_FILES["programmer"].read_text(encoding="utf-8"))
    assert fm.get("model") == CORRECT_MODEL, f"Programmer model: {fm.get('model')}"


def test_brainstormer_model():
    """brainstormer.agent.md must have correct model."""
    fm, _ = _parse_frontmatter(AGENT_FILES["brainstormer"].read_text(encoding="utf-8"))
    assert fm.get("model") == CORRECT_MODEL, f"Brainstormer model: {fm.get('model')}"


def test_tester_model():
    """tester.agent.md must have correct model."""
    fm, _ = _parse_frontmatter(AGENT_FILES["tester"].read_text(encoding="utf-8"))
    assert fm.get("model") == CORRECT_MODEL, f"Tester model: {fm.get('model')}"


def test_researcher_model():
    """researcher.agent.md must have correct model."""
    fm, _ = _parse_frontmatter(AGENT_FILES["researcher"].read_text(encoding="utf-8"))
    assert fm.get("model") == CORRECT_MODEL, f"Researcher model: {fm.get('model')}"


def test_scientist_model():
    """scientist.agent.md must have correct model."""
    fm, _ = _parse_frontmatter(AGENT_FILES["scientist"].read_text(encoding="utf-8"))
    assert fm.get("model") == CORRECT_MODEL, f"Scientist model: {fm.get('model')}"


def test_criticist_model():
    """criticist.agent.md must have correct model."""
    fm, _ = _parse_frontmatter(AGENT_FILES["criticist"].read_text(encoding="utf-8"))
    assert fm.get("model") == CORRECT_MODEL, f"Criticist model: {fm.get('model')}"


def test_planner_model():
    """planner.agent.md must have correct model."""
    fm, _ = _parse_frontmatter(AGENT_FILES["planner"].read_text(encoding="utf-8"))
    assert fm.get("model") == CORRECT_MODEL, f"Planner model: {fm.get('model')}"


def test_fixer_model():
    """fixer.agent.md must have correct model."""
    fm, _ = _parse_frontmatter(AGENT_FILES["fixer"].read_text(encoding="utf-8"))
    assert fm.get("model") == CORRECT_MODEL, f"Fixer model: {fm.get('model')}"


def test_writer_model():
    """writer.agent.md must have correct model."""
    fm, _ = _parse_frontmatter(AGENT_FILES["writer"].read_text(encoding="utf-8"))
    assert fm.get("model") == CORRECT_MODEL, f"Writer model: {fm.get('model')}"


def test_prototyper_model():
    """prototyper.agent.md must have correct model."""
    fm, _ = _parse_frontmatter(AGENT_FILES["prototyper"].read_text(encoding="utf-8"))
    assert fm.get("model") == CORRECT_MODEL, f"Prototyper model: {fm.get('model')}"


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
    """Planner must have 'ask' tool for clarifying questions (BUG-109)."""
    fm, _ = _parse_frontmatter(AGENT_FILES["planner"].read_text(encoding="utf-8"))
    assert "ask" in fm.get("tools", []), "Planner must have 'ask' tool"


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
    assert "tools: [read, edit, search, execute]" in readme, (
        "README.md example must show 'tools: [read, edit, search, execute]'"
    )


def test_readme_example_uses_correct_model():
    """README.md example frontmatter must show the correct Copilot model."""
    readme = (AGENTS_DIR / "README.md").read_text(encoding="utf-8")
    assert "Claude Opus 4.6 (copilot)" in readme, (
        "README.md example must reference 'Claude Opus 4.6 (copilot)'"
    )


def test_readme_no_old_model():
    """README.md example must not show the old claude-sonnet-4-5 model."""
    readme = (AGENTS_DIR / "README.md").read_text(encoding="utf-8")
    assert "claude-sonnet-4-5" not in readme, (
        "README.md example still references old model 'claude-sonnet-4-5'"
    )
