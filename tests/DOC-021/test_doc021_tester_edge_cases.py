"""
Tester edge-case tests for DOC-021: tester.agent.md for Agent Workbench.

Additional tests beyond the Developer suite — covering frontmatter integrity,
persona quality, tool presence, and resilience edge cases.
"""
import pathlib
import yaml

AGENT_FILE = (
    pathlib.Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
    / ".github"
    / "agents"
    / "tester.agent.md"
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


def test_frontmatter_has_execute():
    """execute must be listed as a tool — tester must be able to run tests."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    tools = fm.get("tools", [])
    assert "execute" in tools, "execute not found in tools list — tester must be able to run tests"


def test_frontmatter_has_edit():
    """edit must be listed as a tool — tester must be able to write test files."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    tools = fm.get("tools", [])
    assert "edit" in tools, "edit not found in tools list — tester must be able to write test files"


def test_frontmatter_has_search():
    """search must be listed as a tool (deep codebase search capability)."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    tools = fm.get("tools", [])
    assert "search" in tools, "search not found in tools list"


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


def test_frontmatter_description_mentions_testing():
    """description field must reference the testing/quality nature of the agent."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    desc = str(fm.get("description", "")).lower()
    assert any(kw in desc for kw in ["test", "edge case", "validate", "quality", "behavior"]), (
        f"description does not mention testing/quality: {fm.get('description')!r}"
    )


# ---------------------------------------------------------------------------
# Body quality
# ---------------------------------------------------------------------------

def test_body_mentions_edge_cases():
    """Body must explicitly reference edge cases as part of the tester's focus."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    body_lower = body.lower()
    assert "edge case" in body_lower or "edge-case" in body_lower, (
        "Body must mention edge cases as a core part of the tester's role"
    )


def test_body_mentions_unit_tests():
    """Body must reference unit tests."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    body_lower = body.lower()
    assert "unit" in body_lower, "Body must mention unit tests"


def test_body_mentions_no_feature_implementation():
    """Body must state that the agent does not implement features."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    body_lower = body.lower()
    assert any(kw in body_lower for kw in ["not implement", "does not implement", "do not implement"]), (
        "Body must state that the tester does not implement features"
    )


def test_file_encoding_is_utf8():
    """File must be readable as UTF-8 without errors."""
    content = AGENT_FILE.read_bytes()
    decoded = content.decode("utf-8")
    assert len(decoded) > 0, "File decoded to empty string"
