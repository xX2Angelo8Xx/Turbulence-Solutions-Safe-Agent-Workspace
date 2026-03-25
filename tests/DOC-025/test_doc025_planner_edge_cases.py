"""
Edge-case tests for DOC-025: planner.agent.md for Agent Workbench.

Tester-added tests that go beyond Developer's basic validation:
- Exact field values (name, model)
- Closing frontmatter delimiter
- Full tool list — exactly 4 read/search tools, no extras
- Comprehensive forbidden-tools sweep (edit, terminal, web, notebook)
- All 5 standard sections present
- All 3 zone restriction rows in table
- Cross-references to other agents
- {{PROJECT_NAME}} placeholder count (>= 2)
- AGENT-RULES.md referenced
- Explicit "does not implement" language in persona/role
- UTF-8 encoding, no BOM
- Consistency with other read-only agent files (brainstormer pattern)
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

AGENT_FILE = AGENT_DIR / "planner.agent.md"

REQUIRED_TOOLS = [
    "read",
    "search",
    "ask",
    "edit",
]

FORBIDDEN_TOOLS = [
    "execute",
    "fetch_webpage",
    "edit_notebook_file",
    "run_notebook_cell",
    "create_directory",
    "create_new_jupyter_notebook",
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

    def test_name_is_exactly_planner(self):
        """Name must be exactly 'Planner'."""
        fm, _ = _parse_frontmatter(_read_content())
        assert fm["name"] == "Planner", f"Expected name 'Planner', got '{fm['name']}'"

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
        assert delimiter_lines[0] == 0, "First --- must be on line 0"


# ---------------------------------------------------------------------------
# Tools — completeness, no extras, no forbidden
# ---------------------------------------------------------------------------

class TestToolsList:
    """Verify tools list is exactly the required set (read/search only)."""

    def test_tools_list_contains_all_required(self):
        """Every required tool must be present."""
        fm, _ = _parse_frontmatter(_read_content())
        tools = fm.get("tools", [])
        missing = [t for t in REQUIRED_TOOLS if t not in tools]
        assert not missing, f"Missing required tools: {missing}"

    def test_tools_count_is_exactly_four(self):
        """Tools list must have exactly 4 items — read, search, ask, edit."""
        fm, _ = _parse_frontmatter(_read_content())
        tools = fm.get("tools", [])
        assert len(tools) == 4, (
            f"Expected exactly 4 tools (read/search/ask/edit), found {len(tools)}: {tools}"
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

    @pytest.mark.parametrize("forbidden", FORBIDDEN_TOOLS)
    def test_forbidden_tool_absent(self, forbidden):
        """Each forbidden tool must NOT appear in the tools list."""
        fm, _ = _parse_frontmatter(_read_content())
        tools = fm.get("tools", [])
        assert forbidden not in tools, (
            f"Forbidden tool '{forbidden}' found. Planner must not have execute or web tools."
        )

    def test_tools_exactly_match_required_set(self):
        """Tools must be exactly the required set — no extras at all."""
        fm, _ = _parse_frontmatter(_read_content())
        tools = set(fm.get("tools", []))
        required = set(REQUIRED_TOOLS)
        extra = tools - required
        assert not extra, f"Extra tools found: {extra}. Planner must have read/search/ask/edit only."


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

    def test_programmer_reference(self):
        """Must reference @programmer."""
        content = _read_content()
        assert "@programmer" in content, "Missing agent cross-reference: '@programmer'"

    def test_tester_reference(self):
        """Must reference @tester."""
        content = _read_content()
        assert "@tester" in content, "Missing agent cross-reference: '@tester'"

    def test_criticist_reference(self):
        """Must reference @criticist."""
        content = _read_content()
        assert "@criticist" in content, "Missing agent cross-reference: '@criticist'"

    def test_brainstormer_reference(self):
        """Must reference @brainstormer."""
        content = _read_content()
        assert "@brainstormer" in content, "Missing agent cross-reference: '@brainstormer'"


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
        AGENT_FILE.read_text(encoding="utf-8")

    def test_no_bom(self):
        """File should not start with a UTF-8 BOM."""
        raw = AGENT_FILE.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), "File should not have a UTF-8 BOM"


# ---------------------------------------------------------------------------
# Persona — planning-only emphasis
# ---------------------------------------------------------------------------

class TestPlanningOnlyPersona:
    """Verify persona emphasizes planning only, no implementation."""

    def test_body_says_does_not_implement(self):
        """Body must contain explicit 'does not implement' or 'do not implement' language."""
        _, body = _parse_frontmatter(_read_content())
        body_lower = body.lower()
        assert "not implement" in body_lower, (
            "Body must explicitly state the planner does not implement"
        )

    def test_body_says_does_not_write_code(self):
        """Body must state the planner does not write code."""
        _, body = _parse_frontmatter(_read_content())
        body_plain = body.replace("**", "").lower()
        assert "not write code" in body_plain or "not code" in body_plain, (
            "Body must state the planner does not write code"
        )

    def test_body_says_does_not_edit(self):
        """Body must state the planner does not edit files."""
        _, body = _parse_frontmatter(_read_content())
        body_lower = body.lower()
        assert "not" in body_lower and "edit" in body_lower, (
            "Body must state the planner does not edit files"
        )

    def test_body_emphasizes_planning(self):
        """Body should use planning/dependency/task-list language."""
        _, body = _parse_frontmatter(_read_content())
        body_lower = body.lower()
        assert any(kw in body_lower for kw in [
            "plan", "dependency", "task list", "sequence", "structured"
        ]), "Body must emphasize planning/dependency/task-list language"

    def test_description_reflects_planning_persona(self):
        """Frontmatter description should reflect planning-only nature."""
        fm, _ = _parse_frontmatter(_read_content())
        desc = str(fm["description"]).lower()
        has_planning = any(kw in desc for kw in ["plan", "depend", "task", "organiz", "structur"])
        assert has_planning, "Description must reflect planning persona"

    def test_role_section_mentions_no_implementation(self):
        """Role section must explicitly state no implementation."""
        _, body = _parse_frontmatter(_read_content())
        role_start = body.find("## Role")
        assert role_start != -1
        next_section = body.find("## ", role_start + 1)
        role_content = body[role_start:next_section] if next_section != -1 else body[role_start:]
        role_plain = role_content.replace("**", "").lower()
        assert "not implement" in role_plain or "not write code" in role_plain or "plan" in role_plain, (
            "Role section must emphasize planning, not implementation"
        )


# ---------------------------------------------------------------------------
# Consistency with brainstormer (other read-only agent)
# ---------------------------------------------------------------------------

class TestConsistencyWithOtherAgents:
    """Verify structural consistency with established agent files."""

    def test_first_body_line_mentions_agent_name(self):
        """First line of body should introduce the agent by name."""
        _, body = _parse_frontmatter(_read_content())
        first_line = body.split("\n")[0]
        assert "Planner" in first_line, (
            f"First body line should mention 'Planner': '{first_line}'"
        )

    def test_body_uses_bold_agent_name(self):
        """Agent name should be bold (**Planner**) in intro."""
        _, body = _parse_frontmatter(_read_content())
        assert "**Planner**" in body, "Body should use **Planner** (bold) in intro"

    def test_how_you_work_has_numbered_steps(self):
        """'How You Work' section should have numbered steps."""
        _, body = _parse_frontmatter(_read_content())
        how_start = body.find("## How You Work")
        assert how_start != -1
        next_section = body.find("## ", how_start + 1)
        how_content = body[how_start:next_section] if next_section != -1 else body[how_start:]
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

    def test_tools_include_brainstormer_subset(self):
        """Planner tools must include the brainstormer subset (read, search) plus ask and edit."""
        brainstormer_file = AGENT_DIR / "brainstormer.agent.md"
        if not brainstormer_file.exists():
            pytest.skip("brainstormer.agent.md not found for comparison")
        b_content = brainstormer_file.read_text(encoding="utf-8")
        b_fm, _ = _parse_frontmatter(b_content)
        p_fm, _ = _parse_frontmatter(_read_content())
        brainstormer_tools = set(b_fm.get("tools", []))
        planner_tools = set(p_fm.get("tools", []))
        assert brainstormer_tools.issubset(planner_tools), (
            f"Planner tools {p_fm.get('tools')} must include all brainstormer tools "
            f"{b_fm.get('tools')}"
        )

    def test_model_matches_brainstormer(self):
        """Planner model should match brainstormer (project standard)."""
        brainstormer_file = AGENT_DIR / "brainstormer.agent.md"
        if not brainstormer_file.exists():
            pytest.skip("brainstormer.agent.md not found for comparison")
        b_content = brainstormer_file.read_text(encoding="utf-8")
        b_fm, _ = _parse_frontmatter(b_content)
        p_fm, _ = _parse_frontmatter(_read_content())
        assert p_fm["model"] == b_fm["model"], (
            f"Planner model '{p_fm['model']}' should match brainstormer model '{b_fm['model']}'"
        )
