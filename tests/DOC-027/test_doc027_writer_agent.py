"""
Tests for DOC-027: writer.agent.md for Agent Workbench.

Verifies that:
- The file exists at the correct path
- It has valid YAML frontmatter
- All required frontmatter fields are present and non-empty
- The tools list contains read, edit, and search tools (no terminal or web tools)
- The body contains a meaningful persona description
"""
import pathlib
import pytest
import yaml

AGENT_FILE = (
    pathlib.Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
    / ".github"
    / "agents"
    / "writer.agent.md"
)

# Writer has read + edit + search tools
REQUIRED_TOOLS = [
    "read_file",
    "create_file",
    "replace_string_in_file",
    "multi_replace_string_in_file",
    "file_search",
    "grep_search",
    "semantic_search",
]

# Terminal and web tools must NOT appear in the writer's tool list
FORBIDDEN_TOOLS = [
    "run_in_terminal",
    "edit_notebook_file",
    "run_notebook_cell",
    "fetch_webpage",
]


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) parsed from a markdown file with YAML frontmatter."""
    if not text.startswith("---"):
        return {}, text
    end = text.index("---", 3)
    yaml_block = text[3:end].strip()
    body = text[end + 3:].strip()
    return yaml.safe_load(yaml_block) or {}, body


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------

def test_file_exists():
    """writer.agent.md must exist at the specified path."""
    assert AGENT_FILE.exists(), f"File not found: {AGENT_FILE}"


def test_file_is_not_empty():
    """File must contain content."""
    assert AGENT_FILE.stat().st_size > 0, "File is empty"


# ---------------------------------------------------------------------------
# YAML frontmatter structure
# ---------------------------------------------------------------------------

def test_file_starts_with_frontmatter_delimiter():
    """File must open with a YAML frontmatter block (---)."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    assert content.startswith("---"), "File does not start with YAML frontmatter delimiter '---'"


def test_frontmatter_is_parseable():
    """YAML frontmatter must be valid YAML."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    assert isinstance(fm, dict), "Frontmatter did not parse to a dict"


def test_frontmatter_name_present_and_non_empty():
    """'name' field must be present and non-empty."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    assert "name" in fm, "Frontmatter missing 'name' field"
    assert fm["name"] and str(fm["name"]).strip(), "'name' field is empty"


def test_frontmatter_description_present_and_non_empty():
    """'description' field must be present and non-empty."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    assert "description" in fm, "Frontmatter missing 'description' field"
    assert fm["description"] and str(fm["description"]).strip(), "'description' field is empty"


def test_frontmatter_tools_is_list():
    """'tools' field must be a non-empty list."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    assert "tools" in fm, "Frontmatter missing 'tools' field"
    assert isinstance(fm["tools"], list), "'tools' field must be a list"
    assert len(fm["tools"]) > 0, "'tools' list is empty"


def test_frontmatter_required_tools_present():
    """Tools list must contain all required read/edit/search tool identifiers."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    tools = fm.get("tools", [])
    missing = [t for t in REQUIRED_TOOLS if t not in tools]
    assert not missing, f"Required tools missing from frontmatter: {missing}"


def test_frontmatter_forbidden_tools_absent():
    """Terminal and web tools must NOT appear in the writer's tools list."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    tools = fm.get("tools", [])
    present_forbidden = [t for t in FORBIDDEN_TOOLS if t in tools]
    assert not present_forbidden, (
        f"Forbidden terminal/web tools found in writer tools list: {present_forbidden}. "
        "The Writer writes documentation only and must not have terminal or web tools."
    )


def test_frontmatter_model_present_and_non_empty():
    """'model' field must be present and non-empty."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    assert "model" in fm, "Frontmatter missing 'model' field"
    assert fm["model"] and str(fm["model"]).strip(), "'model' field is empty"


# ---------------------------------------------------------------------------
# Body / persona
# ---------------------------------------------------------------------------

def test_body_is_non_trivial():
    """Body must contain substantial persona content (at least 100 characters)."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    assert len(body) >= 100, f"Body is too short ({len(body)} chars) — expected a meaningful persona description"


def test_body_mentions_writer_role():
    """Body must reference the agent's writing/documentation role."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    body_lower = body.lower()
    assert any(kw in body_lower for kw in ["writer", "documentation", "technical writer"]), (
        "Body must describe the writer persona"
    )


def test_body_mentions_documentation_types():
    """Body must mention the documentation types the writer creates."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    body_lower = body.lower()
    assert "readme" in body_lower, "Body must mention READMEs"
    assert "api" in body_lower, "Body must mention API docs"
    assert "changelog" in body_lower, "Body must mention changelogs"


def test_body_contains_zone_restrictions():
    """Body must include zone restrictions section."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    body_lower = body.lower()
    assert "zone restriction" in body_lower or "off-limits" in body_lower, (
        "Body must contain zone restrictions"
    )
    assert ".github/" in body, "Zone restrictions must mention .github/"
    assert "NoAgentZone/" in body, "Zone restrictions must mention NoAgentZone/"


def test_body_contains_project_placeholder():
    """Body must use {{PROJECT_NAME}} placeholder."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    assert "{{PROJECT_NAME}}" in content, "Body must use {{PROJECT_NAME}} placeholder"


def test_body_references_agent_rules():
    """Body must reference AGENT-RULES.md so users know where zone rules are defined."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    assert "AGENT-RULES.md" in body, "Body does not reference AGENT-RULES.md"
