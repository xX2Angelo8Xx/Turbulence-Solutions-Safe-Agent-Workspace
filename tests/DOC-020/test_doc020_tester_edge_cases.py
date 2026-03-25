"""
Tester edge-case tests for DOC-020: brainstormer.agent.md for Agent Workbench.

Additional tests beyond the Developer suite — covering frontmatter integrity,
persona quality, tool restrictions, and resilience edge cases.
"""
import pathlib
import yaml

AGENT_FILE = (
    pathlib.Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
    / ".github"
    / "agents"
    / "brainstormer.agent.md"
)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) from a YAML-frontmatter markdown file."""
    if not text.startswith("---"):
        return {}, text
    end = text.index("---", 3)
    yaml_block = text[3:end].strip()
    body = text[end + 3:].strip()
    return yaml.safe_load(yaml_block) or {}, body


# ---------------------------------------------------------------------------
# Frontmatter completeness
# ---------------------------------------------------------------------------

def test_frontmatter_has_closing_delimiter():
    """Frontmatter block must be properly closed with a second --- delimiter."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    lines = content.splitlines()
    assert lines[0].strip() == "---", "First line must be '---'"
    closing_count = sum(1 for line in lines[1:] if line.strip() == "---")
    assert closing_count >= 1, "No closing '---' frontmatter delimiter found"


def test_frontmatter_tools_has_semantic_search():
    """semantic_search must be listed as a tool (deep search capability)."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    tools = fm.get("tools", [])
    assert "semantic_search" in tools, "semantic_search not found in tools list"


def test_frontmatter_no_create_file_tool():
    """create_file must NOT be in the tools list — brainstormer never creates files."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    tools = fm.get("tools", [])
    assert "create_file" not in tools, (
        "create_file found in tools list — brainstormer is ideation-only and must not create files"
    )


def test_frontmatter_no_run_in_terminal_tool():
    """run_in_terminal must NOT be in the tools list — brainstormer does not execute code."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    tools = fm.get("tools", [])
    assert "run_in_terminal" not in tools, (
        "run_in_terminal found in tools list — brainstormer must not execute commands"
    )


def test_frontmatter_model_is_not_placeholder():
    """model field must not contain an unfilled placeholder like {{...}}."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    model = str(fm.get("model", ""))
    assert "{{" not in model and "}}" not in model, (
        f"model field contains an unfilled placeholder: {model!r}"
    )


def test_frontmatter_name_has_no_placeholder():
    """name field must not contain an unfilled placeholder."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    name = str(fm.get("name", ""))
    assert "{{" not in name, f"name field contains unfilled placeholder: {name!r}"


def test_frontmatter_description_mentions_ideation():
    """description field must reference the ideation/exploration nature of the agent."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    desc = str(fm.get("description", "")).lower()
    assert any(kw in desc for kw in ["idea", "explore", "trade-off", "approach", "brainstorm", "ideation"]), (
        f"description does not mention ideation/exploration: {fm.get('description')!r}"
    )


# ---------------------------------------------------------------------------
# Body quality
# ---------------------------------------------------------------------------

def test_body_mentions_no_edit_constraint():
    """Body must explicitly acknowledge the no-edit / ideation-only constraint."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    body_lower = body.lower()
    assert any(kw in body_lower for kw in ["no edit", "not write", "not implement", "no code", "does not write", "do not write"]), (
        "Body must state that the agent does not write or edit code"
    )


def test_body_mentions_multiple_approaches():
    """Body must describe generating multiple approaches or options."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    body_lower = body.lower()
    assert any(kw in body_lower for kw in ["multiple", "approach", "option", "alternative"]), (
        "Body must describe generating multiple approaches/options"
    )


def test_body_mentions_tradeoffs():
    """Body must mention trade-offs as part of the brainstormer's analysis method."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    body_lower = body.lower()
    assert "trade-off" in body_lower or "tradeoff" in body_lower or "trade off" in body_lower, (
        "Body must mention trade-offs as part of the brainstorming approach"
    )


def test_file_encoding_is_utf8():
    """File must be readable as UTF-8 without errors."""
    content = AGENT_FILE.read_bytes()
    decoded = content.decode("utf-8")
    assert len(decoded) > 0, "File decoded to empty string"
