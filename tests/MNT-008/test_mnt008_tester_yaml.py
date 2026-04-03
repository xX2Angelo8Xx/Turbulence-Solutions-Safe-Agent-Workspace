"""
MNT-008: Tests for tester.agent.md YAML frontmatter.
Verifies agents: [orchestrator] and handoffs: escalation block are present.
"""
import re
import pathlib

AGENT_FILE = pathlib.Path(__file__).parents[2] / ".github" / "agents" / "tester.agent.md"


def _parse_frontmatter(text: str) -> str:
    """Extract raw YAML frontmatter text (between the two --- delimiters)."""
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert match, "tester.agent.md does not contain valid YAML frontmatter"
    return match.group(1)


def _load_frontmatter() -> str:
    content = AGENT_FILE.read_text(encoding="utf-8")
    return _parse_frontmatter(content)


def test_agents_field_exists():
    fm = _load_frontmatter()
    assert "agents:" in fm, "YAML frontmatter is missing the 'agents:' field"


def test_agents_contains_orchestrator():
    fm = _load_frontmatter()
    match = re.search(r"agents:\s*\[([^\]]+)\]", fm)
    assert match, "agents: field is not in inline list format [...]"
    items = [item.strip() for item in match.group(1).split(",")]
    assert "orchestrator" in items, f"agents list does not contain 'orchestrator': {items}"


def test_handoffs_field_exists():
    fm = _load_frontmatter()
    assert "handoffs:" in fm, "YAML frontmatter is missing the 'handoffs:' block"


def test_handoffs_targets_orchestrator():
    fm = _load_frontmatter()
    assert "agent: orchestrator" in fm, (
        "handoffs: block does not contain 'agent: orchestrator'"
    )


def test_handoffs_has_nonempty_prompt():
    fm = _load_frontmatter()
    match = re.search(r'prompt:\s*"([^"]+)"', fm)
    assert match, "handoffs: block does not contain a quoted 'prompt:' field"
    assert len(match.group(1).strip()) > 20, "handoffs prompt is too short to be meaningful"


def test_handoffs_has_send_true():
    fm = _load_frontmatter()
    assert "send: true" in fm, "handoffs: block is missing 'send: true'"


def test_file_is_valid_utf8():
    content = AGENT_FILE.read_text(encoding="utf-8")
    assert len(content) > 0, "tester.agent.md is empty"
