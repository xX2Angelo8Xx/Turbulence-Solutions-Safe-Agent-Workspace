"""
Tester edge-case tests for DOC-019: programmer.agent.md for Agent Workbench.

Additional tests beyond the Developer suite — covering frontmatter integrity,
persona quality, tool completeness, and resilience edge cases.
"""
import pathlib
import yaml

AGENT_FILE = (
    pathlib.Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
    / ".github"
    / "agents"
    / "programmer.agent.md"
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


def test_frontmatter_tools_contains_file_search():
    """file_search must be listed as a tool (search capability requirement)."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    tools = fm.get("tools", [])
    assert "file_search" in tools, "file_search not found in tools list"


def test_frontmatter_tools_contains_multi_replace():
    """multi_replace_string_in_file must be listed (bulk-edit capability)."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    tools = fm.get("tools", [])
    assert "multi_replace_string_in_file" in tools, (
        "multi_replace_string_in_file not found in tools list — "
        "bulk-edit capability is required per dev-log decision"
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


# ---------------------------------------------------------------------------
# Persona quality
# ---------------------------------------------------------------------------

def test_body_mentions_implementation():
    """Persona body must describe implementation as the primary role."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    assert "implement" in body.lower(), (
        "Body does not mention 'implement' — programmer persona must focus on implementation"
    )


def test_body_mentions_refactoring():
    """Persona body must address refactoring per WP acceptance criteria."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    assert "refactor" in body.lower(), (
        "Body does not mention 'refactor' — refactoring is a required capability per WP description"
    )


def test_body_describes_zone_restrictions():
    """Body must describe zone/path restrictions so agents know where they can operate."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    # Must mention at least one of the known restricted paths
    denied_zones = [".github", ".vscode", "NoAgentZone"]
    mentioned = [zone for zone in denied_zones if zone in body]
    assert mentioned, (
        f"Body does not reference any denied zones ({denied_zones}); "
        "zone restrictions must be documented in the agent persona"
    )


def test_body_does_not_contain_interactive_constructs():
    """Body must not instruct agents to request user input (non-interactive requirement)."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    forbidden_phrases = ["ask the user", "prompt the user", "wait for input", "request approval"]
    found = [p for p in forbidden_phrases if p.lower() in body.lower()]
    assert not found, (
        f"Body contains interactive-mode instruction(s): {found}. "
        "Agents must operate autonomously without user prompts."
    )


# ---------------------------------------------------------------------------
# File encoding and integrity
# ---------------------------------------------------------------------------

def test_file_is_valid_utf8():
    """File must be readable as valid UTF-8 without errors."""
    try:
        AGENT_FILE.read_text(encoding="utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise AssertionError(f"File is not valid UTF-8: {exc}") from exc


def test_file_has_no_trailing_crlf_issues():
    """File should use LF or CRLF consistently — no mixed line endings that break YAML."""
    raw = AGENT_FILE.read_bytes()
    cr_count = raw.count(b"\r\n")
    bare_cr_count = raw.count(b"\r") - cr_count  # \r not part of \r\n
    assert bare_cr_count == 0, (
        f"File contains {bare_cr_count} bare CR characters — mixed line endings detected"
    )


def test_frontmatter_does_not_duplicate_opening_delimiter():
    """YAML block must have exactly two '---' markers: one opening, one closing."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    lines = content.splitlines()
    delimiter_positions = [i for i, line in enumerate(lines) if line.strip() == "---"]
    assert len(delimiter_positions) >= 2, "Less than 2 '---' delimiters found"
    # The first two delimiters should be close together (within the frontmatter block)
    opening = delimiter_positions[0]
    closing = delimiter_positions[1]
    assert closing - opening <= 20, (
        f"Frontmatter block spans {closing - opening} lines — unusually large; "
        "check for extra '---' delimiters in the body"
    )
