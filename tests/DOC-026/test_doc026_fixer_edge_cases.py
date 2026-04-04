import pytest
pytestmark = pytest.mark.skip(reason="fixer.agent.md was removed in the Agent Workbench redesign")

"""
Edge-case tests for DOC-026: fixer.agent.md for Agent Workbench.

Tester-added tests that go beyond the Developer's baseline validation:
- Exact name and model values
- Full 8-tool set with no extras or forbidden tools
- Debugging/fix language throughout persona
- All 5 required body sections
- Zone restriction table with 3 denied paths
- Agent cross-references (@programmer, @tester, etc.)
- {{PROJECT_NAME}} placeholder count
- Structural consistency with programmer.agent.md
- No stale/forbidden content
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

FIXER_FILE = AGENT_DIR / "fixer.agent.md"
PROGRAMMER_FILE = AGENT_DIR / "programmer.agent.md"

REQUIRED_TOOLS = sorted([
    "read",
    "edit",
    "search",
    "execute",
])

FORBIDDEN_TOOLS = [
    "fetch_webpage",
    "fetch_url",
    "http_request",
    "curl",
    "wget",
]


def _parse(path: pathlib.Path) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) from a YAML-frontmatter markdown file."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    end = text.index("---", 3)
    fm = yaml.safe_load(text[3:end].strip()) or {}
    body = text[end + 3:].strip()
    return fm, body


# ---------------------------------------------------------------------------
# Exact frontmatter values
# ---------------------------------------------------------------------------

class TestFrontmatterExactValues:
    """Verify exact expected values in YAML frontmatter."""

    def test_name_is_exactly_fixer(self):
        """Name must be exactly 'Fixer' (case-sensitive)."""
        fm, _ = _parse(FIXER_FILE)
        assert fm["name"] == "Fixer", f"Expected name 'Fixer', got '{fm['name']}'"

    def test_model_is_correct(self):
        """Model must be the correct Copilot model."""
        fm, _ = _parse(FIXER_FILE)
        assert fm["model"] == ["Claude Opus 4.6 (copilot)"], (
            f"Expected model ['Claude Opus 4.6 (copilot)'], got '{fm['model']}'"
        )

    def test_tools_count_is_exactly_4(self):
        """Tools list must have exactly 4 entries — no more, no less."""
        fm, _ = _parse(FIXER_FILE)
        assert len(fm["tools"]) == 4, (
            f"Expected 4 tools, got {len(fm['tools'])}: {fm['tools']}"
        )

    def test_tools_exact_set(self):
        """Tools must be exactly the required 8-tool set."""
        fm, _ = _parse(FIXER_FILE)
        assert sorted(fm["tools"]) == REQUIRED_TOOLS, (
            f"Tool mismatch.\n  Expected: {REQUIRED_TOOLS}\n  Got: {sorted(fm['tools'])}"
        )

    def test_no_forbidden_tools(self):
        """No forbidden/network tools may appear in the tools list."""
        fm, _ = _parse(FIXER_FILE)
        found = [t for t in FORBIDDEN_TOOLS if t in fm["tools"]]
        assert not found, f"Forbidden tools found in tools list: {found}"

    def test_description_mentions_debug_or_root_cause(self):
        """Description field should mention debugging or root cause analysis."""
        fm, _ = _parse(FIXER_FILE)
        desc = fm["description"].lower()
        assert "debug" in desc or "root cause" in desc, (
            "Description should mention debugging or root cause analysis"
        )


# ---------------------------------------------------------------------------
# Body sections
# ---------------------------------------------------------------------------

class TestBodySections:
    """Verify all 5 required sections exist in the body."""

    REQUIRED_SECTIONS = [
        "## Role",
        "## Persona",
        "## How You Work",
        "## Zone Restrictions",
        "## What You Do Not Do",
    ]

    @pytest.mark.parametrize("heading", REQUIRED_SECTIONS)
    def test_section_present(self, heading):
        """Each required section heading must appear in the body."""
        _, body = _parse(FIXER_FILE)
        assert heading in body, f"Missing section: {heading}"

    def test_all_five_sections_present(self):
        """All 5 sections must be present (aggregate check)."""
        _, body = _parse(FIXER_FILE)
        missing = [h for h in self.REQUIRED_SECTIONS if h not in body]
        assert not missing, f"Missing sections: {missing}"

    def test_no_extra_h2_sections(self):
        """Only the 5 expected H2 sections should exist."""
        _, body = _parse(FIXER_FILE)
        h2_headings = re.findall(r"^## .+", body, re.MULTILINE)
        allowed = {s.strip() for s in self.REQUIRED_SECTIONS}
        extras = [h for h in h2_headings if h.strip() not in allowed]
        assert not extras, f"Unexpected H2 sections found: {extras}"


# ---------------------------------------------------------------------------
# Zone restrictions
# ---------------------------------------------------------------------------

class TestZoneRestrictions:
    """Verify zone restriction table has all 3 denied paths."""

    DENIED_PATHS = [".github/", ".vscode/", "NoAgentZone/"]

    @pytest.mark.parametrize("path", DENIED_PATHS)
    def test_denied_path_present(self, path):
        """Each denied path must appear in the Zone Restrictions section."""
        _, body = _parse(FIXER_FILE)
        assert path in body, f"Zone restriction table missing denied path: {path}"

    def test_all_three_denied_paths(self):
        """All 3 denied paths must be present (aggregate check)."""
        _, body = _parse(FIXER_FILE)
        missing = [p for p in self.DENIED_PATHS if p not in body]
        assert not missing, f"Missing denied paths: {missing}"


# ---------------------------------------------------------------------------
# Debugging / fix language in persona
# ---------------------------------------------------------------------------

class TestDebuggingLanguage:
    """Verify the persona uses appropriate debugging and fix language."""

    DEBUG_TERMS = ["root cause", "trace", "diagnose", "fix", "debug", "error", "isolat"]

    def test_root_cause_mentioned(self):
        _, body = _parse(FIXER_FILE)
        assert "root cause" in body.lower()

    def test_trace_mentioned(self):
        _, body = _parse(FIXER_FILE)
        assert "trace" in body.lower()

    def test_fix_mentioned(self):
        _, body = _parse(FIXER_FILE)
        assert "fix" in body.lower()

    def test_debug_mentioned(self):
        _, body = _parse(FIXER_FILE)
        assert "debug" in body.lower()

    def test_multiple_debug_terms_present(self):
        """At least 5 of the 7 debugging terms must appear in the body."""
        _, body = _parse(FIXER_FILE)
        body_lower = body.lower()
        found = [t for t in self.DEBUG_TERMS if t in body_lower]
        assert len(found) >= 5, (
            f"Expected ≥5 debugging terms, found {len(found)}: {found}"
        )


# ---------------------------------------------------------------------------
# Agent cross-references
# ---------------------------------------------------------------------------

class TestAgentCrossReferences:
    """Verify the 'What You Do Not Do' section references other agents."""

    EXPECTED_REFS = ["@programmer", "@tester", "@brainstormer", "@criticist", "@planner"]

    def test_what_you_do_not_do_has_agent_refs(self):
        """Section must mention at least 3 other agent roles."""
        _, body = _parse(FIXER_FILE)
        found = [ref for ref in self.EXPECTED_REFS if ref in body]
        assert len(found) >= 3, (
            f"Expected ≥3 agent cross-references, found {len(found)}: {found}"
        )

    @pytest.mark.parametrize("ref", EXPECTED_REFS)
    def test_individual_agent_ref(self, ref):
        """Each expected agent cross-reference should be present."""
        _, body = _parse(FIXER_FILE)
        assert ref in body, f"Missing agent cross-reference: {ref}"


# ---------------------------------------------------------------------------
# {{PROJECT_NAME}} placeholder
# ---------------------------------------------------------------------------

class TestProjectNamePlaceholder:
    """Verify {{PROJECT_NAME}} is used consistently."""

    def test_placeholder_in_body_at_least_twice(self):
        """{{PROJECT_NAME}} must appear at least 2 times in the body."""
        _, body = _parse(FIXER_FILE)
        count = body.count("{{PROJECT_NAME}}")
        assert count >= 2, (
            f"Expected {{{{PROJECT_NAME}}}} ≥2 times in body, found {count}"
        )

    def test_no_hardcoded_project_name(self):
        """Body should not contain a hardcoded project name instead of the placeholder."""
        _, body = _parse(FIXER_FILE)
        # Should not have a literal project folder reference without the placeholder
        assert "agent-environment-launcher" not in body.lower(), (
            "Body contains hardcoded project name instead of {{PROJECT_NAME}} placeholder"
        )


# ---------------------------------------------------------------------------
# AGENT-RULES.md reference
# ---------------------------------------------------------------------------

class TestAgentRulesReference:
    """Verify AGENT-RULES.md is properly referenced."""

    def test_agent_rules_referenced(self):
        """AGENT-RULES.md must be referenced in the body."""
        _, body = _parse(FIXER_FILE)
        assert "AGENT-RULES.md" in body

    def test_agent_rules_with_project_name(self):
        """AGENT-RULES.md reference should use {{PROJECT_NAME}} prefix."""
        _, body = _parse(FIXER_FILE)
        assert "{{PROJECT_NAME}}/AGENT-RULES.md" in body, (
            "AGENT-RULES.md should be referenced as {{PROJECT_NAME}}/AGENT-RULES.md"
        )


# ---------------------------------------------------------------------------
# Structural consistency with programmer.agent.md
# ---------------------------------------------------------------------------

class TestConsistencyWithProgrammer:
    """Verify fixer.agent.md is structurally consistent with programmer.agent.md."""

    def test_programmer_file_exists(self):
        """programmer.agent.md must exist for comparison."""
        assert PROGRAMMER_FILE.exists(), "programmer.agent.md not found for comparison"

    def test_same_tool_set(self):
        """Fixer and Programmer must have the same tool set."""
        fm_fixer, _ = _parse(FIXER_FILE)
        fm_prog, _ = _parse(PROGRAMMER_FILE)
        assert sorted(fm_fixer["tools"]) == sorted(fm_prog["tools"]), (
            f"Tool mismatch with programmer.\n"
            f"  Fixer: {sorted(fm_fixer['tools'])}\n"
            f"  Programmer: {sorted(fm_prog['tools'])}"
        )

    def test_same_model(self):
        """Fixer and Programmer must use the same model."""
        fm_fixer, _ = _parse(FIXER_FILE)
        fm_prog, _ = _parse(PROGRAMMER_FILE)
        assert fm_fixer["model"] == fm_prog["model"], (
            f"Model mismatch: fixer={fm_fixer['model']}, programmer={fm_prog['model']}"
        )

    def test_same_section_headings(self):
        """Both agents should have the same set of H2 section headings
        (excluding agent-specific sections like Refactoring)."""
        _, body_fixer = _parse(FIXER_FILE)
        _, body_prog = _parse(PROGRAMMER_FILE)
        common_required = {"## Role", "## Persona", "## How You Work",
                           "## Zone Restrictions", "## What You Do Not Do"}
        fixer_h2 = set(re.findall(r"^## .+", body_fixer, re.MULTILINE))
        prog_h2 = set(re.findall(r"^## .+", body_prog, re.MULTILINE))
        assert common_required.issubset(fixer_h2), (
            f"Fixer missing common sections: {common_required - fixer_h2}"
        )
        assert common_required.issubset(prog_h2), (
            f"Programmer missing common sections: {common_required - prog_h2}"
        )

    def test_same_zone_restrictions(self):
        """Both agents must deny the same 3 paths."""
        _, body_fixer = _parse(FIXER_FILE)
        _, body_prog = _parse(PROGRAMMER_FILE)
        for path in [".github/", ".vscode/", "NoAgentZone/"]:
            assert path in body_fixer, f"Fixer missing zone: {path}"
            assert path in body_prog, f"Programmer missing zone: {path}"


# ---------------------------------------------------------------------------
# Negative / no-stale-content checks
# ---------------------------------------------------------------------------

class TestNoStaleContent:
    """Ensure no incorrect or stale content leaked in."""

    def test_no_scientist_references_in_name(self):
        """Frontmatter name must not reference 'Scientist'."""
        fm, _ = _parse(FIXER_FILE)
        assert "scientist" not in fm["name"].lower()

    def test_no_tester_references_in_name(self):
        """Frontmatter name must not reference 'Tester'."""
        fm, _ = _parse(FIXER_FILE)
        assert "tester" not in fm["name"].lower()

    def test_no_duplicate_tools(self):
        """Tools list must not contain duplicates."""
        fm, _ = _parse(FIXER_FILE)
        tools = fm["tools"]
        assert len(tools) == len(set(tools)), f"Duplicate tools detected: {tools}"

    def test_body_does_not_claim_to_build_features(self):
        """Fixer persona should explicitly disclaim building new features."""
        _, body = _parse(FIXER_FILE)
        assert "do not build new features" in body.lower() or "not build new features" in body.lower(), (
            "Fixer should disclaim building new features"
        )

    def test_frontmatter_no_extra_fields(self):
        """Frontmatter should only contain the 4 expected fields."""
        fm, _ = _parse(FIXER_FILE)
        expected = {"name", "description", "tools", "model"}
        extras = set(fm.keys()) - expected
        assert not extras, f"Unexpected frontmatter fields: {extras}"
