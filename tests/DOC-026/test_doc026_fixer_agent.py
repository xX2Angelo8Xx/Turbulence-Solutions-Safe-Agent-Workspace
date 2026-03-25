"""
Tests for DOC-026: fixer.agent.md for Agent Workbench.

Verifies that:
- The file exists at the correct path
- It has valid YAML frontmatter
- All required frontmatter fields are present and non-empty
- The tools list contains all required tools (read, edit, search, execute)
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
    / "fixer.agent.md"
)

# Fixer has full toolset: read, edit, search, execute
REQUIRED_TOOLS = [
    "read",
    "edit",
    "search",
    "execute",
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
    """fixer.agent.md must exist at the specified path."""
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
    """Tools list must contain all required tool identifiers."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    tools = fm.get("tools", [])
    missing = [t for t in REQUIRED_TOOLS if t not in tools]
    assert not missing, f"Required tools missing from frontmatter: {missing}"


def test_frontmatter_model_present_and_non_empty():
    """'model' field must be present and non-empty."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    assert "model" in fm, "Frontmatter missing 'model' field"
    assert fm["model"] and str(fm["model"]).strip(), "'model' field is empty"


# ---------------------------------------------------------------------------
# Body / persona
# ---------------------------------------------------------------------------

def test_body_is_non_empty():
    """File body (after frontmatter) must contain persona description text."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    assert body.strip(), "File body (after frontmatter) is empty"


def test_body_references_agent_rules():
    """Body must reference AGENT-RULES.md so users know where zone rules are defined."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    assert "AGENT-RULES.md" in body, "Body does not reference AGENT-RULES.md"


def test_body_mentions_fixer_role():
    """Body must mention the fixer/debugger role."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    body_lower = body.lower()
    assert "fixer" in body_lower or "debug" in body_lower, (
        "Body does not mention 'fixer' or 'debug' role"
    )


def test_body_mentions_root_cause():
    """Body must mention root cause analysis as part of the persona."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    assert "root cause" in body.lower(), "Body does not mention 'root cause' analysis"


def test_body_uses_project_name_placeholder():
    """Body must use {{PROJECT_NAME}} placeholder."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    assert "{{PROJECT_NAME}}" in body, "Body does not use {{PROJECT_NAME}} placeholder"
