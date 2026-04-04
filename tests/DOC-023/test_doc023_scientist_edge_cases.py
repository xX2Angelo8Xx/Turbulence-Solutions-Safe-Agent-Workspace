import pytest
pytestmark = pytest.mark.skip(reason="scientist.agent.md was removed in the Agent Workbench redesign")

"""
Edge-case tests for DOC-023: scientist.agent.md for Agent Workbench.

Tester-added tests that go beyond Developer's basic validation:
- Exact field values (name, model)
- Closing frontmatter delimiter
- Full tool list (no extras, no missing)
- All 5 standard sections present
- All 3 zone restriction rows in table
- Cross-references to other agents
- {{PROJECT_NAME}} placeholder count
- AGENT-RULES.md reference
- UTF-8 encoding
- Consistency with other agent files
- No trailing whitespace in frontmatter fields
"""
import pathlib
import re

import pytest
import yaml

AGENT_DIR = (
    pathlib.Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
    / ".github"
    / "agents"
)

AGENT_FILE = AGENT_DIR / "scientist.agent.md"

REQUIRED_TOOLS = [
    "read",
    "edit",
    "search",
    "execute",
]


def _read_content() -> str:
    return AGENT_FILE.read_text(encoding="utf-8")


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) from YAML frontmatter markdown."""
    assert text.startswith("---"), "Missing opening frontmatter delimiter"
    end = text.index("---", 3)
    yaml_block = text[3:end].strip()
    body = text[end + 3:].strip()
    return yaml.safe_load(yaml_block) or {}, body


# ---------------------------------------------------------------------------
# Frontmatter — exact values
# ---------------------------------------------------------------------------

class TestFrontmatterExactValues:
    """Verify exact required values in YAML frontmatter."""

    def test_name_is_exactly_scientist(self):
        """Name must be exactly 'Scientist'."""
        fm, _ = _parse_frontmatter(_read_content())
        assert fm["name"] == "Scientist", f"Expected name 'Scientist', got '{fm['name']}'"

    def test_model_is_correct(self):
        """Model must be the correct Copilot model."""
        fm, _ = _parse_frontmatter(_read_content())
        assert fm["model"] == ["Claude Opus 4.6 (copilot)"], (
            f"Expected model ['Claude Opus 4.6 (copilot)'], got '{fm['model']}'"
        )

    def test_name_has_no_leading_trailing_whitespace(self):
        """Name must not have leading/trailing whitespace."""
        fm, _ = _parse_frontmatter(_read_content())
        assert str(fm["name"]) == str(fm["name"]).strip()

    def test_model_has_no_leading_trailing_whitespace(self):
        """Model must not have leading/trailing whitespace."""
        fm, _ = _parse_frontmatter(_read_content())
        assert str(fm["model"]) == str(fm["model"]).strip()

    def test_description_has_no_leading_trailing_whitespace(self):
        """Description must not have leading/trailing whitespace."""
        fm, _ = _parse_frontmatter(_read_content())
        assert str(fm["description"]) == str(fm["description"]).strip()


# ---------------------------------------------------------------------------
# Frontmatter — delimiter
# ---------------------------------------------------------------------------

class TestFrontmatterDelimiters:
    """Verify YAML frontmatter opening and closing delimiters."""

    def test_closing_frontmatter_delimiter_present(self):
        """File must have a closing --- delimiter for YAML frontmatter."""
        content = _read_content()
        # Must start with --- and have a second --- after it
        assert content.startswith("---"), "Missing opening ---"
        rest = content[3:]
        assert "---" in rest, "Missing closing --- delimiter"

    def test_frontmatter_block_is_between_two_delimiters(self):
        """Frontmatter must be enclosed between exactly two --- lines."""
        content = _read_content()
        lines = content.split("\n")
        delimiter_lines = [i for i, line in enumerate(lines) if line.strip() == "---"]
        assert len(delimiter_lines) >= 2, (
            f"Expected at least 2 '---' delimiter lines, found {len(delimiter_lines)}"
        )
        # First delimiter must be at line 0
        assert delimiter_lines[0] == 0, "First --- must be on line 0"


# ---------------------------------------------------------------------------
# Tools — completeness and no extras
# ---------------------------------------------------------------------------

class TestToolsList:
    """Verify tools list is exactly the required set."""

    def test_tools_list_contains_all_required(self):
        """Every required tool must be present."""
        fm, _ = _parse_frontmatter(_read_content())
        tools = fm.get("tools", [])
        missing = [t for t in REQUIRED_TOOLS if t not in tools]
        assert not missing, f"Missing required tools: {missing}"

    def test_tools_count_matches(self):
        """Tools list must have exactly 4 items (read, edit, search, execute)."""
        fm, _ = _parse_frontmatter(_read_content())
        tools = fm.get("tools", [])
        assert len(tools) == 4, (
            f"Expected 4 tools, found {len(tools)}: {tools}"
        )

    def test_no_duplicate_tools(self):
        """Tools list must not have duplicates."""
        fm, _ = _parse_frontmatter(_read_content())
        tools = fm.get("tools", [])
        assert len(tools) == len(set(tools)), f"Duplicate tools found: {tools}"

    def test_tools_are_strings(self):
        """Every tool in the list must be a string."""
        fm, _ = _parse_frontmatter(_read_content())
        for tool in fm.get("tools", []):
            assert isinstance(tool, str), f"Tool '{tool}' is not a string"


# ---------------------------------------------------------------------------
# Body — 5 standard sections
# ---------------------------------------------------------------------------

class TestStandardSections:
    """Verify all 5 standard sections are present in the body."""

    REQUIRED_SECTIONS = [
        "## Role",
        "## Persona",
        "## How You Work",
        "## Zone Restrictions",
        "## What You Do Not Do",
    ]

    @pytest.mark.parametrize("section", REQUIRED_SECTIONS)
    def test_section_present(self, section):
        """Each standard section heading must appear in the body."""
        _, body = _parse_frontmatter(_read_content())
        assert section in body, f"Missing required section: '{section}'"

    def test_all_five_sections_present(self):
        """All 5 standard sections must exist."""
        _, body = _parse_frontmatter(_read_content())
        missing = [s for s in self.REQUIRED_SECTIONS if s not in body]
        assert not missing, f"Missing sections: {missing}"


# ---------------------------------------------------------------------------
# Zone Restrictions — 3 denied paths in table
# ---------------------------------------------------------------------------

class TestZoneRestrictions:
    """Verify all 3 zone restriction rows are in the table."""

    DENIED_PATHS = [".github/", ".vscode/", "NoAgentZone/"]

    @pytest.mark.parametrize("path", DENIED_PATHS)
    def test_denied_path_in_table(self, path):
        """Each denied path must appear in the zone restrictions."""
        _, body = _parse_frontmatter(_read_content())
        assert path in body, f"Zone restrictions missing denied path: '{path}'"

    def test_zone_table_has_header(self):
        """Zone restrictions must have a markdown table with headers."""
        _, body = _parse_frontmatter(_read_content())
        assert "Denied Path" in body or "denied path" in body.lower(), (
            "Zone restrictions table must have 'Denied Path' header"
        )
        assert "Reason" in body, "Zone restrictions table must have 'Reason' header"

    def test_all_three_denied_paths_present(self):
        """All 3 denied paths must be present."""
        _, body = _parse_frontmatter(_read_content())
        missing = [p for p in self.DENIED_PATHS if p not in body]
        assert not missing, f"Missing denied paths: {missing}"


# ---------------------------------------------------------------------------
# Cross-references to other agents
# ---------------------------------------------------------------------------

class TestCrossReferences:
    """Verify references to other agents via @ mentions."""

    REQUIRED_REFS = ["@programmer", "@tester", "@brainstormer", "@criticist", "@planner"]

    @pytest.mark.parametrize("ref", REQUIRED_REFS)
    def test_agent_reference_present(self, ref):
        """Each required agent cross-reference must appear."""
        content = _read_content()
        assert ref in content, f"Missing agent cross-reference: '{ref}'"

    def test_all_cross_references_present(self):
        """All 5 required agent refs must be present."""
        content = _read_content()
        missing = [r for r in self.REQUIRED_REFS if r not in content]
        assert not missing, f"Missing cross-references: {missing}"


# ---------------------------------------------------------------------------
# {{PROJECT_NAME}} placeholder count
# ---------------------------------------------------------------------------

class TestProjectNamePlaceholder:
    """Verify {{PROJECT_NAME}} usage."""

    def test_placeholder_appears_at_least_twice(self):
        """{{PROJECT_NAME}} must appear at least 2 times."""
        content = _read_content()
        count = content.count("{{PROJECT_NAME}}")
        assert count >= 2, (
            f"{{{{PROJECT_NAME}}}} appears {count} time(s), expected >= 2"
        )

    def test_placeholder_not_misspelled(self):
        """No common misspellings of the placeholder."""
        content = _read_content()
        for variant in ["{{project_name}}", "{{Project_Name}}", "{{ PROJECT_NAME }}"]:
            assert variant not in content, f"Misspelled placeholder found: '{variant}'"
        # Check for single-brace {PROJECT_NAME} that is NOT part of {{PROJECT_NAME}}
        import re
        single_brace = re.findall(r"(?<!\{)\{PROJECT_NAME\}(?!\})", content)
        assert not single_brace, "Found single-brace {PROJECT_NAME} (should be double-brace)"


# ---------------------------------------------------------------------------
# AGENT-RULES.md reference
# ---------------------------------------------------------------------------

class TestAgentRulesReference:
    """Verify the file references AGENT-RULES.md."""

    def test_agent_rules_referenced(self):
        """Body must reference AGENT-RULES.md."""
        content = _read_content()
        assert "AGENT-RULES.md" in content, "File must reference AGENT-RULES.md"


# ---------------------------------------------------------------------------
# UTF-8 encoding
# ---------------------------------------------------------------------------

class TestEncoding:
    """Verify file is valid UTF-8."""

    def test_file_is_valid_utf8(self):
        """File must be readable as UTF-8 without errors."""
        AGENT_FILE.read_text(encoding="utf-8")  # will raise on invalid UTF-8

    def test_no_bom(self):
        """File should not start with a UTF-8 BOM."""
        raw = AGENT_FILE.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), "File should not have a UTF-8 BOM"


# ---------------------------------------------------------------------------
# Persona content keywords
# ---------------------------------------------------------------------------

class TestPersonaContent:
    """Verify persona reflects scientist character."""

    PERSONA_KEYWORDS = ["hypothesis", "evidence", "data", "experiment", "analytical"]

    @pytest.mark.parametrize("keyword", PERSONA_KEYWORDS)
    def test_persona_keyword_present(self, keyword):
        """Key scientist persona words must appear in the body."""
        _, body = _parse_frontmatter(_read_content())
        assert keyword in body.lower(), (
            f"Persona missing keyword: '{keyword}'"
        )

    def test_description_reflects_persona(self):
        """Frontmatter description must mention scientific work."""
        fm, _ = _parse_frontmatter(_read_content())
        desc = str(fm["description"]).lower()
        has_keyword = any(
            kw in desc for kw in ["experiment", "benchmark", "hypothesis", "evidence", "data"]
        )
        assert has_keyword, "Frontmatter description must reflect scientist persona"


# ---------------------------------------------------------------------------
# Consistency with other agent files
# ---------------------------------------------------------------------------

class TestConsistencyWithOtherAgents:
    """Verify structural consistency with established agent files."""

    def test_first_body_line_mentions_agent_name(self):
        """First line of body should introduce the agent by name (like other agents)."""
        _, body = _parse_frontmatter(_read_content())
        first_line = body.split("\n")[0]
        assert "Scientist" in first_line, (
            f"First body line should mention 'Scientist': '{first_line}'"
        )

    def test_body_uses_bold_agent_name(self):
        """Agent name should be bold (**Scientist**) in intro like other agents."""
        _, body = _parse_frontmatter(_read_content())
        assert "**Scientist**" in body, "Body should use **Scientist** (bold) in intro"

    def test_how_you_work_has_numbered_steps(self):
        """'How You Work' section should have numbered steps."""
        _, body = _parse_frontmatter(_read_content())
        how_section_start = body.find("## How You Work")
        assert how_section_start != -1
        # Get content until next ## section
        next_section = body.find("## ", how_section_start + 1)
        how_content = body[how_section_start:next_section] if next_section != -1 else body[how_section_start:]
        assert re.search(r"^\d+\.", how_content, re.MULTILINE), (
            "'How You Work' section must contain numbered steps"
        )

    def test_what_you_do_not_do_has_bullet_points(self):
        """'What You Do Not Do' section should have bullet points."""
        _, body = _parse_frontmatter(_read_content())
        section_start = body.find("## What You Do Not Do")
        assert section_start != -1
        section_content = body[section_start:]
        assert re.search(r"^- ", section_content, re.MULTILINE), (
            "'What You Do Not Do' section must contain bullet points"
        )

    def test_file_ends_with_newline(self):
        """File should end with a single newline (standard convention)."""
        content = _read_content()
        assert content.endswith("\n"), "File should end with a newline"
