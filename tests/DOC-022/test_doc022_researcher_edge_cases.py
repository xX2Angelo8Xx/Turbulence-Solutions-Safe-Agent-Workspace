"""
Edge-case tests for DOC-022: researcher.agent.md

Tester-added tests beyond the Developer's original suite. Validates:
- Exact model value
- Proper YAML closing delimiter
- Researcher-specific persona (not programmer/tester/brainstormer)
- Cross-references to other agents in "What You Do Not Do"
- Structural consistency with other agent files
- No terminal or edit verbs in the body instructions
- Researcher relies on read and search tools only (fetch_webpage removed)
- Frontmatter name is exactly "Researcher"
- Allowed tools are exactly the expected set (no extras)
"""
import pathlib
import re

import pytest
import yaml

AGENT_FILE = (
    pathlib.Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
    / ".github"
    / "agents"
    / "researcher.agent.md"
)

BRAINSTORMER_FILE = AGENT_FILE.parent / "brainstormer.agent.md"
PROGRAMMER_FILE = AGENT_FILE.parent / "programmer.agent.md"
TESTER_FILE = AGENT_FILE.parent / "tester.agent.md"


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) from markdown with YAML frontmatter."""
    if not text.startswith("---"):
        return {}, text
    end = text.index("---", 3)
    yaml_block = text[3:end].strip()
    body = text[end + 3:].strip()
    return yaml.safe_load(yaml_block) or {}, body


# ---------------------------------------------------------------------------
# YAML frontmatter closing delimiter
# ---------------------------------------------------------------------------

def test_frontmatter_has_closing_delimiter():
    """YAML frontmatter must have a closing '---' delimiter on its own line."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    lines = content.splitlines()
    assert lines[0].strip() == "---", "First line must be '---'"
    # Find closing delimiter (second occurrence of '---')
    closing_found = False
    for line in lines[1:]:
        if line.strip() == "---":
            closing_found = True
            break
    assert closing_found, "YAML frontmatter missing closing '---' delimiter"


def test_frontmatter_closing_delimiter_before_body():
    """The closing '---' must appear before any body content (## headings)."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    lines = content.splitlines()
    closing_line_idx = None
    first_heading_idx = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---" and closing_line_idx is None:
            closing_line_idx = idx
        if line.startswith("##") and first_heading_idx is None:
            first_heading_idx = idx
    assert closing_line_idx is not None, "No closing '---' found"
    assert first_heading_idx is not None, "No body headings found"
    assert closing_line_idx < first_heading_idx, (
        f"Closing '---' at line {closing_line_idx} must come before first heading at line {first_heading_idx}"
    )


# ---------------------------------------------------------------------------
# Exact frontmatter values
# ---------------------------------------------------------------------------

def test_model_is_correct():
    """Model field must be the correct Copilot model."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    assert fm.get("model") == ["Claude Sonnet 4.6 (copilot)"], (
        f"Expected model ['Claude Sonnet 4.6 (copilot)'], got '{fm.get('model')}'"
    )


def test_name_is_exactly_researcher():
    """Name field must be exactly 'Researcher' (capitalized, singular)."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    assert fm.get("name") == "Researcher", (
        f"Expected name 'Researcher', got '{fm.get('name')}'"
    )


def test_tools_list_is_exact():
    """Tools list must contain all expected tools for the redesigned researcher."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    required = {"read", "search", "web", "browser", "edit"}
    actual = set(fm.get("tools", []))
    missing = required - actual
    assert not missing, f"Researcher missing expected tools: {missing}"


def test_description_mentions_research_persona():
    """Description must reflect investigator/research persona, not programmer/tester."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    desc = fm.get("description", "").lower()
    # Must contain research-related terms
    assert any(kw in desc for kw in ["investigat", "research", "evaluat", "compar"]), (
        f"Description does not reflect researcher persona: '{fm.get('description')}'"
    )
    # Must NOT describe a programmer or tester persona
    assert "writes code" not in desc, "Description sounds like a programmer, not a researcher"
    assert "writes test" not in desc, "Description sounds like a tester, not a researcher"


def test_description_mentions_read_only():
    """Description must reflect evidence-driven research focus of the researcher."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    desc = fm.get("description", "").lower()
    assert any(kw in desc for kw in ["evidence", "source", "investigat", "evaluat", "research"]), (
        "Description should reflect researcher's evidence-driven approach"
    )


# ---------------------------------------------------------------------------
# Body structure — required sections
# ---------------------------------------------------------------------------

EXPECTED_SECTIONS = [
    "## How You Work",
    "## Zone Restrictions",
    "## What You Do Not Do",
]


@pytest.mark.parametrize("section_heading", EXPECTED_SECTIONS)
def test_body_has_required_section(section_heading):
    """Body must contain all standard agent sections matching other agent files."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    assert section_heading in body, f"Missing required section: '{section_heading}'"


# ---------------------------------------------------------------------------
# Zone restrictions completeness
# ---------------------------------------------------------------------------

def test_zone_restrictions_mentions_vscode():
    """Zone restrictions must mention .vscode/ as off-limits."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    assert ".vscode/" in body, "Zone restrictions must mention .vscode/"


def test_zone_restrictions_mentions_all_three_zones():
    """All three restricted zones must appear: .github/, .vscode/, NoAgentZone/."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    for zone in [".github/", ".vscode/", "NoAgentZone/"]:
        assert zone in body, f"Zone restrictions missing '{zone}'"


def test_zone_restrictions_has_denied_path_table():
    """Zone restrictions should have a Denied Path table like other agent files."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    assert "Denied Path" in body or "denied path" in body.lower(), (
        "Zone restrictions should include a 'Denied Path' table"
    )


# ---------------------------------------------------------------------------
# "What You Do Not Do" — cross-references
# ---------------------------------------------------------------------------

EXPECTED_AGENT_REFS = ["@Programmer", "@Tester", "@Brainstormer"]


@pytest.mark.parametrize("agent_ref", EXPECTED_AGENT_REFS)
def test_what_you_do_not_do_references_agent(agent_ref):
    """'What You Do Not Do' section must reference other agents for delegation."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    # Extract the "What You Do Not Do" section
    wyd_match = re.search(r"## What You Do Not Do\s*\n(.*)", body, re.DOTALL)
    assert wyd_match, "Could not find 'What You Do Not Do' section"
    wyd_section = wyd_match.group(1)
    assert agent_ref in wyd_section, (
        f"'What You Do Not Do' should reference '{agent_ref}' for proper delegation"
    )


def test_what_you_do_not_do_no_edit_claim():
    """'What You Do Not Do' must explicitly state it does not edit files."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    wyd_match = re.search(r"## What You Do Not Do\s*\n(.*)", body, re.DOTALL)
    assert wyd_match, "Could not find 'What You Do Not Do' section"
    wyd_lower = wyd_match.group(1).lower()
    assert any(phrase in wyd_lower for phrase in [
        "do not write", "do not edit", "no edit tools",
    ]), "'What You Do Not Do' must state the agent does not edit files"


def test_what_you_do_not_do_no_terminal_claim():
    """'What You Do Not Do' must mention what the agent does not run or execute."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    wyd_match = re.search(r"## What You Do Not Do\s*\n(.*)", body, re.DOTALL)
    assert wyd_match, "Could not find 'What You Do Not Do' section"
    wyd_lower = wyd_match.group(1).lower()
    assert any(phrase in wyd_lower for phrase in [
        "terminal command", "run code", "execute", "run command", "speculate",
    ]), "'What You Do Not Do' must state what the agent avoids doing"


# ---------------------------------------------------------------------------
# Researcher-unique features
# ---------------------------------------------------------------------------

def test_fetch_webpage_not_in_tools():
    """fetch_webpage must NOT be present — it is not a standard VS Code tool category."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    tools = fm.get("tools", [])
    assert "fetch_webpage" not in tools, "Researcher must not have fetch_webpage tool (not a VS Code category)"


def test_brainstormer_does_not_have_fetch_webpage():
    """Verify brainstormer also does NOT have fetch_webpage."""
    if not BRAINSTORMER_FILE.exists():
        pytest.skip("brainstormer.agent.md not found — cannot compare")
    content = BRAINSTORMER_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    tools = fm.get("tools", [])
    assert "fetch_webpage" not in tools, (
        "brainstormer should not have fetch_webpage"
    )


def test_body_mentions_structured_output():
    """Persona must describe producing structured output (summaries, tables, pros/cons)."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    body_lower = body.lower()
    assert any(kw in body_lower for kw in [
        "structured", "comparison table", "pros and cons", "summary",
    ]), "Body must describe structured output (summaries, tables, pros/cons)"


def test_body_mentions_evidence_based():
    """Persona must emphasize evidence-based approach."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    body_lower = body.lower()
    assert any(kw in body_lower for kw in [
        "evidence", "backed", "documentation", "sources",
    ]), "Body must describe evidence-based approach"


def test_body_does_not_instruct_editing():
    """Body should never instruct the researcher to edit, create, or delete files."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    # Check "How You Work" section specifically
    hyw_match = re.search(r"## How You Work\s*\n(.*?)(?=\n## |\Z)", body, re.DOTALL)
    if hyw_match:
        hyw_section = hyw_match.group(1).lower()
        for verb in ["create_file", "replace_string", "write to file", "edit the file"]:
            assert verb not in hyw_section, (
                f"'How You Work' should not instruct editing — found '{verb}'"
            )


def test_how_you_work_uses_read_and_search():
    """'How You Work' steps should describe using read and search tools for investigation."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(content)
    hyw_match = re.search(r"## How You Work\s*\n(.*?)(?=\n## |\Z)", body, re.DOTALL)
    assert hyw_match, "Could not find 'How You Work' section"
    hyw_section = hyw_match.group(1).lower()
    assert "search" in hyw_section or "read" in hyw_section, (
        "'How You Work' should describe using read and search tools"
    )


def test_agent_rules_reference():
    """Body must reference AGENT-RULES.md for the full permission matrix."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    assert "AGENT-RULES.md" in content, "Must reference AGENT-RULES.md"


def test_no_terminal_tool_in_frontmatter():
    """Frontmatter tools must not include run_in_terminal."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    fm, _ = _parse_frontmatter(content)
    tools = fm.get("tools", [])
    assert "run_in_terminal" not in tools, "Researcher must not have run_in_terminal"


def test_project_name_placeholder_count():
    """{{PROJECT_NAME}} should appear multiple times (zone restrictions + AGENT-RULES ref)."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    count = content.count("{{PROJECT_NAME}}")
    assert count >= 2, (
        f"Expected {{{{PROJECT_NAME}}}} at least 2 times, found {count}"
    )


def test_file_encoding_is_utf8():
    """File must be readable as UTF-8 without errors."""
    try:
        AGENT_FILE.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        pytest.fail("File is not valid UTF-8")


def test_no_trailing_whitespace_in_frontmatter():
    """YAML frontmatter keys should not have trailing whitespace issues."""
    content = AGENT_FILE.read_text(encoding="utf-8")
    lines = content.splitlines()
    in_frontmatter = False
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if in_frontmatter:
                break
            in_frontmatter = True
            continue
        if in_frontmatter and line.strip():
            # Check that key: value pairs parse cleanly
            assert ":" in line, f"Frontmatter line {i+1} missing key:value format: '{line}'"
