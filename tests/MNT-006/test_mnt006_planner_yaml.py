"""
MNT-006: Tests for planner.agent.md YAML frontmatter.
Verifies all required YAML fields are present and correctly populated.
"""
import re
import pathlib

AGENT_FILE = pathlib.Path(__file__).parents[2] / ".github" / "agents" / "planner.agent.md"


def _load_content() -> str:
    assert AGENT_FILE.exists(), f"planner.agent.md not found at {AGENT_FILE}"
    return AGENT_FILE.read_text(encoding="utf-8")


def _parse_frontmatter(content: str) -> str:
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert match, "planner.agent.md does not contain valid YAML frontmatter (--- delimiters)"
    return match.group(1)


def test_file_exists():
    assert AGENT_FILE.exists(), "planner.agent.md does not exist in .github/agents/"


def test_file_is_valid_utf8():
    content = _load_content()
    assert len(content) > 0, "planner.agent.md is empty"


def test_frontmatter_name_is_planner():
    fm = _parse_frontmatter(_load_content())
    match = re.search(r"^name:\s*(\S+)", fm, re.MULTILINE)
    assert match, "YAML frontmatter is missing 'name:' field"
    assert match.group(1) == "planner", f"name should be 'planner', got '{match.group(1)}'"


def test_frontmatter_has_description():
    fm = _parse_frontmatter(_load_content())
    assert "description:" in fm, "YAML frontmatter is missing 'description:' field"
    match = re.search(r'description:\s*"([^"]+)"', fm)
    assert match, "description field should be a non-empty quoted string"
    assert len(match.group(1).strip()) > 20, "description is too short to be meaningful"


def test_frontmatter_has_tools():
    fm = _parse_frontmatter(_load_content())
    assert "tools:" in fm, "YAML frontmatter is missing 'tools:' field"


def test_frontmatter_tools_contains_required():
    fm = _parse_frontmatter(_load_content())
    match = re.search(r"tools:\s*\[([^\]]+)\]", fm)
    assert match, "tools: field is not in inline list format [...]"
    tools = [t.strip() for t in match.group(1).split(",")]
    for required in ("read", "search", "agent"):
        assert required in tools, f"tools list is missing required tool: '{required}'"


def test_frontmatter_agents_field_exists():
    fm = _parse_frontmatter(_load_content())
    assert "agents:" in fm, "YAML frontmatter is missing 'agents:' field"


def test_frontmatter_agents_contains_orchestrator():
    fm = _parse_frontmatter(_load_content())
    match = re.search(r"agents:\s*\[([^\]]+)\]", fm)
    assert match, "agents: field is not in inline list format [...]"
    items = [item.strip() for item in match.group(1).split(",")]
    assert "orchestrator" in items, f"agents list does not contain 'orchestrator': {items}"


def test_frontmatter_agents_contains_story_writer():
    fm = _parse_frontmatter(_load_content())
    match = re.search(r"agents:\s*\[([^\]]+)\]", fm)
    assert match, "agents: field is not in inline list format [...]"
    items = [item.strip() for item in match.group(1).split(",")]
    assert "story-writer" in items, f"agents list does not contain 'story-writer': {items}"


def test_frontmatter_has_model():
    fm = _parse_frontmatter(_load_content())
    assert "model:" in fm, "YAML frontmatter is missing 'model:' field"


def test_frontmatter_model_contains_claude():
    fm = _parse_frontmatter(_load_content())
    assert "Claude" in fm, "model field does not reference Claude"
    assert "Opus" in fm, "model field does not reference Opus tier"


def test_frontmatter_has_argument_hint():
    fm = _parse_frontmatter(_load_content())
    assert "argument-hint:" in fm, "YAML frontmatter is missing 'argument-hint:' field"


def test_frontmatter_has_handoffs():
    fm = _parse_frontmatter(_load_content())
    assert "handoffs:" in fm, "YAML frontmatter is missing 'handoffs:' block"


def test_frontmatter_handoffs_targets_orchestrator():
    fm = _parse_frontmatter(_load_content())
    assert "agent: orchestrator" in fm, (
        "handoffs: block does not contain 'agent: orchestrator'"
    )


def test_frontmatter_handoffs_has_nonempty_prompt():
    fm = _parse_frontmatter(_load_content())
    match = re.search(r'prompt:\s*"([^"]+)"', fm, re.DOTALL)
    assert match, "handoffs: block does not contain a quoted 'prompt:' field"
    assert len(match.group(1).strip()) > 20, "handoffs prompt is too short to be meaningful"


def test_frontmatter_handoffs_has_send_true():
    fm = _parse_frontmatter(_load_content())
    assert "send: true" in fm, "handoffs: block is missing 'send: true'"
