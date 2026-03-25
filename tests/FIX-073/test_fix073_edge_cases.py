"""
Edge-case tests for FIX-073: Fix template agent YAML frontmatter.

Covers scenarios not addressed by the Developer's original test:
- Old model string anywhere in any agent file (full file scan)
- fetch_webpage in any agent body text (not just frontmatter)
- tools value is a YAML list type, not a string
- No YAML frontmatter key count surprises (exactly 4 keys)
- All 10 agent FILES actually exist on disk
- No individual old tool names appear anywhere in planner body text
- Researcher body doesn't mention fetch_webpage at all
- Model value is a list (not parsed as plain string)
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

OLD_INDIVIDUAL_TOOL_NAMES = [
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
# All agent files must exist on disk
# ---------------------------------------------------------------------------

def test_all_agent_files_exist():
    """All 10 agent .md files must exist on disk."""
    for name, path in AGENT_FILES.items():
        assert path.exists(), f"{name}.agent.md not found at {path}"


# ---------------------------------------------------------------------------
# Old model string must not appear anywhere in any agent file (full content)
# ---------------------------------------------------------------------------

def test_old_model_not_in_any_file_content():
    """'claude-sonnet-4-5' must not appear anywhere (frontmatter or body) in any agent file."""
    for name, path in AGENT_FILES.items():
        content = path.read_text(encoding="utf-8")
        assert "claude-sonnet-4-5" not in content, (
            f"{name}.agent.md still contains 'claude-sonnet-4-5' somewhere in the file"
        )


# ---------------------------------------------------------------------------
# fetch_webpage must not appear in any agent file body text either
# ---------------------------------------------------------------------------

def test_fetch_webpage_not_in_researcher_body():
    """researcher.agent.md body must not mention fetch_webpage anywhere."""
    _, body = _parse_frontmatter(AGENT_FILES["researcher"].read_text(encoding="utf-8"))
    assert "fetch_webpage" not in body, (
        "researcher.agent.md body still references fetch_webpage"
    )


def test_fetch_webpage_not_in_any_agent_body():
    """No agent body must mention fetch_webpage anywhere."""
    for name, path in AGENT_FILES.items():
        _, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
        assert "fetch_webpage" not in body, (
            f"{name}.agent.md body still references fetch_webpage"
        )


# ---------------------------------------------------------------------------
# tools frontmatter value must be a Python list (YAML list), not a string
# ---------------------------------------------------------------------------

def test_tools_is_list_in_all_agents():
    """tools frontmatter must be parsed as a Python list, not a string."""
    for name, path in AGENT_FILES.items():
        fm, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
        tools = fm.get("tools")
        assert isinstance(tools, list), (
            f"{name}.agent.md 'tools' is not a YAML list: got {type(tools).__name__}"
        )


# ---------------------------------------------------------------------------
# model frontmatter value must be a Python list (YAML list), not a plain string
# ---------------------------------------------------------------------------

def test_model_is_list_in_all_agents():
    """model frontmatter must be parsed as a Python list, not a plain string."""
    for name, path in AGENT_FILES.items():
        fm, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
        model = fm.get("model")
        assert isinstance(model, list), (
            f"{name}.agent.md 'model' is not a YAML list: got {type(model).__name__} — "
            f"value: {model!r}"
        )


# ---------------------------------------------------------------------------
# Frontmatter must have exactly 4 keys: name, description, tools, model
# ---------------------------------------------------------------------------

def test_frontmatter_has_exactly_four_keys():
    """All agent frontmatters must have exactly name, description, tools, model."""
    expected_keys = {"name", "description", "tools", "model"}
    for name, path in AGENT_FILES.items():
        fm, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
        assert set(fm.keys()) == expected_keys, (
            f"{name}.agent.md frontmatter keys mismatch: "
            f"got {set(fm.keys())} expected {expected_keys}"
        )


# ---------------------------------------------------------------------------
# No old individual tool names appear in planner body (the planner body was
# rewritten — it should not still reference read_file, grep_search, etc.)
# ---------------------------------------------------------------------------

def test_no_old_tool_names_in_planner_body():
    """planner.agent.md body must not mention any old individual tool names."""
    _, body = _parse_frontmatter(AGENT_FILES["planner"].read_text(encoding="utf-8"))
    for old_tool in OLD_INDIVIDUAL_TOOL_NAMES:
        assert old_tool not in body, (
            f"planner.agent.md body still references old tool name '{old_tool}'"
        )


# ---------------------------------------------------------------------------
# No agent has an empty tools list
# ---------------------------------------------------------------------------

def test_no_agent_has_empty_tools_list():
    """Every agent must have at least one tool — no empty tools lists."""
    for name, path in AGENT_FILES.items():
        fm, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
        tools = fm.get("tools", [])
        assert len(tools) > 0, (
            f"{name}.agent.md has an empty tools list"
        )


# ---------------------------------------------------------------------------
# All tool values are non-empty strings (not None or integers)
# ---------------------------------------------------------------------------

def test_all_tool_values_are_non_empty_strings():
    """Every tool entry in every agent frontmatter must be a non-empty string."""
    for name, path in AGENT_FILES.items():
        fm, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
        tools = fm.get("tools", [])
        for tool in tools:
            assert isinstance(tool, str) and len(tool) > 0, (
                f"{name}.agent.md has an invalid tool entry: {tool!r}"
            )


# ---------------------------------------------------------------------------
# README must not reference old model anywhere (not just in example block)
# ---------------------------------------------------------------------------

def test_readme_no_old_model_anywhere():
    """README.md must not contain 'claude-sonnet-4-5' anywhere."""
    readme = (AGENTS_DIR / "README.md").read_text(encoding="utf-8")
    assert "claude-sonnet-4-5" not in readme, (
        "README.md still references old model 'claude-sonnet-4-5'"
    )
