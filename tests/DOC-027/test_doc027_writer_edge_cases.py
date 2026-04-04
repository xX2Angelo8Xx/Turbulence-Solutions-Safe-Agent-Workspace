import pytest
pytestmark = pytest.mark.skip(reason="writer.agent.md was removed in the Agent Workbench redesign")

"""
Edge-case tests for DOC-027: writer.agent.md — Tester Agent.

Covers:
- Exact name value ('Writer'), exact model value ('claude-sonnet-4-5')
- Exact tool count (7), no duplicates, no extra tools
- Forbidden tools verified individually (execute, fetch_webpage)
- All 5 required body sections present
- All 3 zone restrictions present (.github/, .vscode/, NoAgentZone/)
- Agent cross-references (@programmer, @tester, etc.)
- {{PROJECT_NAME}} appears ≥2 times
- AGENT-RULES.md referenced
- Documentation language keywords (README, API doc, changelog, comments, documentation)
- No accidental terminal/execute verbs
- YAML frontmatter has exactly 4 keys
- Body line count is substantial
- No trailing whitespace in frontmatter values
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
    / "writer.agent.md"
)


def _parse(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) from YAML-frontmatter markdown."""
    assert text.startswith("---"), "Missing opening frontmatter delimiter"
    end = text.index("---", 3)
    fm = yaml.safe_load(text[3:end].strip()) or {}
    body = text[end + 3:].strip()
    return fm, body


@pytest.fixture()
def content():
    return AGENT_FILE.read_text(encoding="utf-8")


@pytest.fixture()
def frontmatter(content):
    fm, _ = _parse(content)
    return fm


@pytest.fixture()
def body(content):
    _, b = _parse(content)
    return b


# ── Exact frontmatter values ──────────────────────────────────────────────

class TestFrontmatterExactValues:
    """Verify exact frontmatter field values per acceptance criteria."""

    def test_name_is_writer(self, frontmatter):
        """Name must be exactly 'Writer'."""
        assert frontmatter["name"] == "Writer", (
            f"Expected name='Writer', got '{frontmatter['name']}'"
        )

    def test_model_is_correct(self, frontmatter):
        """Model must be the correct Copilot model."""
        assert frontmatter["model"] == ["Claude Opus 4.6 (copilot)"], (
            f"Expected model=['Claude Opus 4.6 (copilot)'], got '{frontmatter['model']}'"
        )

    def test_frontmatter_has_exactly_four_keys(self, frontmatter):
        """Frontmatter should have exactly name, description, tools, model."""
        expected_keys = {"name", "description", "tools", "model"}
        assert set(frontmatter.keys()) == expected_keys, (
            f"Unexpected frontmatter keys: {set(frontmatter.keys()) - expected_keys}"
        )

    def test_name_no_leading_trailing_whitespace(self, frontmatter):
        """Name value must not have leading/trailing whitespace."""
        assert frontmatter["name"] == str(frontmatter["name"]).strip()

    def test_model_no_leading_trailing_whitespace(self, frontmatter):
        """Model value must not have leading/trailing whitespace in its string elements."""
        model = frontmatter["model"]
        if isinstance(model, list):
            for item in model:
                assert str(item) == str(item).strip()
        else:
            assert str(model) == str(model).strip()


# ── Tool list edge cases ──────────────────────────────────────────────────

EXPECTED_TOOLS = sorted([
    "read",
    "edit",
    "search",
])


class TestToolList:
    """Verify the tools list is exactly correct — no more, no less."""

    def test_tool_count_is_three(self, frontmatter):
        """Writer must have exactly 3 tools."""
        tools = frontmatter.get("tools", [])
        assert len(tools) == 3, (
            f"Expected 3 tools, got {len(tools)}: {tools}"
        )

    def test_no_duplicate_tools(self, frontmatter):
        """No tool should appear more than once."""
        tools = frontmatter.get("tools", [])
        assert len(tools) == len(set(tools)), (
            f"Duplicate tools found: {[t for t in tools if tools.count(t) > 1]}"
        )

    def test_exact_tool_set(self, frontmatter):
        """Tools must match the expected set exactly."""
        tools = sorted(frontmatter.get("tools", []))
        assert tools == EXPECTED_TOOLS, (
            f"Tools mismatch.\n  Expected: {EXPECTED_TOOLS}\n  Got:      {tools}"
        )

    def test_no_execute_tool(self, frontmatter):
        """execute must NOT be in tools — Writer never runs commands."""
        tools = frontmatter.get("tools", [])
        assert "execute" not in tools

    def test_no_fetch_webpage(self, frontmatter):
        """fetch_webpage must NOT be in tools — Writer has no web access."""
        tools = frontmatter.get("tools", [])
        assert "fetch_webpage" not in tools

    def test_no_notebook_tools(self, frontmatter):
        """No notebook-related tools for a documentation writer."""
        tools = frontmatter.get("tools", [])
        notebook_tools = [t for t in tools if "notebook" in t.lower()]
        assert not notebook_tools, f"Notebook tools found: {notebook_tools}"

    def test_all_tools_are_strings(self, frontmatter):
        """Every tool entry must be a string."""
        tools = frontmatter.get("tools", [])
        non_str = [t for t in tools if not isinstance(t, str)]
        assert not non_str, f"Non-string tools: {non_str}"


# ── Body sections ─────────────────────────────────────────────────────────

class TestBodySections:
    """Writer agent must have all 5 required sections."""

    REQUIRED_HEADINGS = [
        "Role",
        "Persona",
        "How You Work",
        "Zone Restrictions",
        "What You Do Not Do",
    ]

    @pytest.mark.parametrize("heading", REQUIRED_HEADINGS)
    def test_section_present(self, body, heading):
        """Each required section heading must appear in the body."""
        pattern = rf"^##\s+{re.escape(heading)}"
        assert re.search(pattern, body, re.MULTILINE), (
            f"Missing required section: '## {heading}'"
        )

    def test_all_five_sections(self, body):
        """All 5 sections must be present (belt-and-suspenders count check)."""
        h2_headings = re.findall(r"^## .+", body, re.MULTILINE)
        assert len(h2_headings) >= 5, (
            f"Expected ≥5 H2 sections, found {len(h2_headings)}: {h2_headings}"
        )


# ── Zone restrictions ─────────────────────────────────────────────────────

class TestZoneRestrictions:
    """All three forbidden zones must be listed."""

    FORBIDDEN_ZONES = [".github/", ".vscode/", "NoAgentZone/"]

    @pytest.mark.parametrize("zone", FORBIDDEN_ZONES)
    def test_zone_mentioned(self, body, zone):
        """Each forbidden zone must be explicitly mentioned."""
        assert zone in body, f"Zone restriction missing: {zone}"

    def test_three_zones_total(self, body):
        """Exactly 3 zones must be restricted."""
        count = sum(1 for z in self.FORBIDDEN_ZONES if z in body)
        assert count == 3, f"Expected 3 zone restrictions, found {count}"


# ── Agent cross-references ────────────────────────────────────────────────

class TestAgentCrossReferences:
    """Writer should reference other agents it delegates to / defers from."""

    def test_references_programmer(self, body):
        """Writer must reference @programmer (code writing is programmer's job)."""
        assert "@programmer" in body.lower() or "programmer" in body.lower()

    def test_references_tester(self, body):
        """Writer must reference @tester (test writing is tester's job)."""
        assert "@tester" in body.lower() or "tester" in body.lower()

    def test_references_brainstormer(self, body):
        assert "@brainstormer" in body.lower() or "brainstormer" in body.lower()

    def test_references_fixer(self, body):
        assert "@fixer" in body.lower() or "fixer" in body.lower()

    def test_references_planner(self, body):
        assert "@planner" in body.lower() or "planner" in body.lower()


# ── Template placeholder ──────────────────────────────────────────────────

class TestProjectPlaceholder:
    """{{PROJECT_NAME}} must appear at least twice."""

    def test_placeholder_count_gte_2(self, content):
        count = content.count("{{PROJECT_NAME}}")
        assert count >= 2, (
            f"{{{{PROJECT_NAME}}}} appears {count} time(s), expected ≥2"
        )


# ── AGENT-RULES.md reference ─────────────────────────────────────────────

class TestAgentRulesReference:
    """AGENT-RULES.md must be referenced in the body."""

    def test_agent_rules_referenced(self, body):
        assert "AGENT-RULES.md" in body, "Body must reference AGENT-RULES.md"

    def test_agent_rules_in_zone_section(self, content):
        """AGENT-RULES.md reference should be near the zone restrictions section."""
        zone_idx = content.lower().find("zone restriction")
        rules_idx = content.find("AGENT-RULES.md")
        assert zone_idx != -1 and rules_idx != -1, (
            "Both zone restrictions section and AGENT-RULES.md must exist"
        )
        # AGENT-RULES.md reference should appear after zone restrictions heading
        assert rules_idx > zone_idx, (
            "AGENT-RULES.md reference should appear in/after the Zone Restrictions section"
        )


# ── Documentation language keywords ──────────────────────────────────────

class TestDocumentationLanguage:
    """Body must mention the documentation types the Writer handles."""

    @pytest.mark.parametrize("keyword", [
        "readme", "api", "changelog", "comment", "documentation",
    ])
    def test_doc_keyword_present(self, body, keyword):
        """Every documentation type keyword must appear."""
        assert keyword in body.lower(), (
            f"Documentation keyword '{keyword}' not found in body"
        )


# ── Negative: no terminal/execute language ────────────────────────────────

class TestNoTerminalLanguage:
    """Writer should not claim it can run or execute things in its body."""

    def test_does_not_claim_execution(self, body):
        """Body should disclaim execution, not claim it."""
        lower = body.lower()
        # These phrases should only appear in negation context
        for phrase in ["you run code", "run commands", "execute code"]:
            if phrase in lower:
                # Verify it's in a negation context ("do not", "don't", "not")
                idx = lower.index(phrase)
                context = lower[max(0, idx - 30):idx]
                assert any(neg in context for neg in ["not", "don't", "no "]), (
                    f"Phrase '{phrase}' appears without negation at position {idx}"
                )


# ── Structural quality ────────────────────────────────────────────────────

class TestStructuralQuality:
    """General structural quality checks."""

    def test_body_line_count(self, body):
        """Body should have at least 20 lines of content."""
        lines = [l for l in body.splitlines() if l.strip()]
        assert len(lines) >= 20, (
            f"Body has only {len(lines)} non-empty lines, expected ≥20"
        )

    def test_frontmatter_closes_properly(self, content):
        """Frontmatter must have exactly two '---' delimiters."""
        parts = content.split("---")
        # parts[0] should be empty, parts[1] is YAML, parts[2:] is body
        assert len(parts) >= 3, "Frontmatter missing closing delimiter"

    def test_no_empty_frontmatter_values(self, frontmatter):
        """No frontmatter value should be None or empty string."""
        for key, value in frontmatter.items():
            assert value is not None, f"Frontmatter key '{key}' is None"
            if isinstance(value, str):
                assert value.strip(), f"Frontmatter key '{key}' is empty string"
            elif isinstance(value, list):
                assert len(value) > 0, f"Frontmatter key '{key}' is empty list"

    def test_description_is_meaningful(self, frontmatter):
        """Description must be at least 20 characters."""
        desc = str(frontmatter.get("description", ""))
        assert len(desc) >= 20, (
            f"Description too short ({len(desc)} chars): '{desc}'"
        )

    def test_file_encoding_utf8(self):
        """File must be readable as UTF-8."""
        AGENT_FILE.read_text(encoding="utf-8")  # raises on encoding error
