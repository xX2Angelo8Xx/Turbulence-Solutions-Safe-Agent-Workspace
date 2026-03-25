"""
Tester-agent additional edge-case tests for DOC-021.

Covers scenarios the Developer tests did not address:
- tools list has no duplicates
- body mentions integration tests (WP requires "unit and integration tests")
- zone restriction section mentions the three hard-denied paths
- frontmatter description field contains no unfilled placeholders
- file has no lone CRLF that would corrupt YAML parsing on Unix hosts
- name field is a meaningful test-related value (not a generic "Agent" catchall)
"""
import pathlib
import re
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
    if not text.startswith("---"):
        return {}, text
    end = text.index("---", 3)
    yaml_block = text[3:end].strip()
    body = text[end + 3:].strip()
    return yaml.safe_load(yaml_block) or {}, body


# ---------------------------------------------------------------------------
# Tools-list integrity
# ---------------------------------------------------------------------------

def test_tools_list_has_no_duplicates():
    """tools list must not contain duplicate entries."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    tools = fm.get("tools", [])
    assert len(tools) == len(set(tools)), (
        f"Duplicate entries in tools list: {[t for t in tools if tools.count(t) > 1]}"
    )


# ---------------------------------------------------------------------------
# Body completeness
# ---------------------------------------------------------------------------

def test_body_mentions_integration_tests():
    """Body must reference integration tests — WP requires writing both unit and integration tests."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    assert "integration" in body.lower(), (
        "Body must mention integration tests — WP goal includes unit AND integration tests"
    )


def test_body_mentions_zone_restrictions():
    """Zone restriction section must mention all three hard-denied directories."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    for denied_path in [".github/", ".vscode/", "NoAgentZone/"]:
        assert denied_path in body, (
            f"Zone restrictions section must list '{denied_path}' as off-limits"
        )


def test_body_mentions_agent_rules():
    """Body must reference AGENT-RULES.md as the permission matrix (convention from other agents)."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    assert "AGENT-RULES.md" in body, (
        "Body must reference AGENT-RULES.md for the permission matrix"
    )


# ---------------------------------------------------------------------------
# Frontmatter value cleanliness
# ---------------------------------------------------------------------------

def test_frontmatter_description_no_placeholder():
    """description field must not contain unfilled {{...}} placeholders."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    desc = str(fm.get("description", ""))
    assert "{{" not in desc and "}}" not in desc, (
        f"description contains an unfilled placeholder: {desc!r}"
    )


def test_frontmatter_name_is_test_related():
    """name field should be a meaningful tester-related identifier, not a generic 'Agent'."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    name = str(fm.get("name", "")).lower()
    assert name != "agent", "name field must be more specific than the generic 'Agent'"
    # Must relate to testing role
    assert any(kw in name for kw in ["test", "qa", "quality", "tester"]), (
        f"name field ({fm.get('name')!r}) should reflect a test/QA role"
    )


# ---------------------------------------------------------------------------
# Encoding and line-ending safety
# ---------------------------------------------------------------------------

def test_file_no_mixed_line_endings():
    """
    File must not mix CRLF and bare-LF line endings.
    Mixed line endings cause inconsistent YAML parsing across platforms.
    All-CRLF or all-LF are both acceptable; a mix is not.
    """
    raw = AGENT_FILE.read_bytes()
    crlf_count = raw.count(b"\r\n")
    # After removing CRLF, any remaining \r would be bare CR; remaining \n are bare LF
    lf_only_count = raw.replace(b"\r\n", b"").count(b"\n")
    assert not (crlf_count > 0 and lf_only_count > 0), (
        f"File mixes CRLF and LF line endings ({crlf_count} CRLF, {lf_only_count} bare LF) — "
        "use consistent line endings throughout the file"
    )


def test_file_no_null_bytes():
    """File must contain no null bytes — would indicate binary corruption."""
    raw = AGENT_FILE.read_bytes()
    assert b"\x00" not in raw, "File contains null bytes — possible binary corruption"


# ---------------------------------------------------------------------------
# Consistency with sibling agents
# ---------------------------------------------------------------------------

def test_tester_agent_is_alongside_other_agents():
    """tester.agent.md must exist in the same directory as programmer.agent.md and brainstormer.agent.md."""
    agents_dir = AGENT_FILE.parent
    for sibling in ["programmer.agent.md", "brainstormer.agent.md"]:
        assert (agents_dir / sibling).exists(), (
            f"Expected sibling agent file '{sibling}' not found next to tester.agent.md"
        )
