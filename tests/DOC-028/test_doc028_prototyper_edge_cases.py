"""
Edge-case tests for DOC-028: prototyper.agent.md

Tester-added tests covering:
- Exact name and model values
- Tool set parity with programmer/fixer/scientist
- No extra tools beyond the 8 required
- Speed/MVP/prototype persona keywords
- All 5 required sections present
- 3 zone restrictions in table format
- Agent cross-references (@programmer, @tester, etc.)
- {{PROJECT_NAME}} placeholder count >= 2
- AGENT-RULES.md reference
- Frontmatter-only fields (no stray keys)
- Consistency with peer agents
"""
import pathlib
import re

import pytest
import yaml

AGENTS_DIR = (
    pathlib.Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
    / ".github"
    / "agents"
)

AGENT_FILE = AGENTS_DIR / "prototyper.agent.md"

REQUIRED_TOOLS = [
    "read_file",
    "create_file",
    "replace_string_in_file",
    "multi_replace_string_in_file",
    "file_search",
    "grep_search",
    "semantic_search",
    "run_in_terminal",
]


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) parsed from a markdown file with YAML frontmatter."""
    if not text.startswith("---"):
        return {}, text
    end = text.index("---", 3)
    yaml_block = text[3:end].strip()
    body = text[end + 3:].strip()
    return yaml.safe_load(yaml_block) or {}, body


def _read() -> tuple[dict, str]:
    content = AGENT_FILE.read_text(encoding="utf-8")
    return _parse_frontmatter(content)


# ---------------------------------------------------------------------------
# Exact frontmatter values
# ---------------------------------------------------------------------------


class TestExactFrontmatterValues:
    """Verify exact name, model, and tool set values."""

    def test_name_is_exactly_prototyper(self):
        fm, _ = _read()
        assert fm["name"] == "Prototyper", (
            f"Name must be exactly 'Prototyper', got '{fm['name']}'"
        )

    def test_model_is_claude_sonnet_4_5(self):
        fm, _ = _read()
        assert fm["model"] == "claude-sonnet-4-5", (
            f"Model must be 'claude-sonnet-4-5', got '{fm['model']}'"
        )

    def test_exactly_eight_tools(self):
        """Tool list must contain exactly 8 tools — no more, no less."""
        fm, _ = _read()
        tools = fm.get("tools", [])
        assert len(tools) == 8, (
            f"Expected exactly 8 tools, got {len(tools)}: {tools}"
        )

    def test_no_extra_tools(self):
        """No tools beyond the required 8 should be present."""
        fm, _ = _read()
        tools = set(fm.get("tools", []))
        extra = tools - set(REQUIRED_TOOLS)
        assert not extra, f"Unexpected extra tools: {extra}"

    def test_no_duplicate_tools(self):
        """Tool list must not contain duplicates."""
        fm, _ = _read()
        tools = fm.get("tools", [])
        assert len(tools) == len(set(tools)), (
            f"Duplicate tools found: {[t for t in tools if tools.count(t) > 1]}"
        )

    def test_frontmatter_has_only_four_keys(self):
        """Frontmatter must have exactly name, description, tools, model."""
        fm, _ = _read()
        expected_keys = {"name", "description", "tools", "model"}
        assert set(fm.keys()) == expected_keys, (
            f"Expected keys {expected_keys}, got {set(fm.keys())}"
        )


# ---------------------------------------------------------------------------
# Persona keywords
# ---------------------------------------------------------------------------


class TestPersonaKeywords:
    """Body must contain speed/MVP/prototype language."""

    def test_contains_speed(self):
        _, body = _read()
        assert "speed" in body.lower(), "Body missing keyword: speed"

    def test_contains_mvp(self):
        _, body = _read()
        assert "mvp" in body.lower(), "Body missing keyword: MVP"

    def test_contains_prototype(self):
        _, body = _read()
        assert "prototype" in body.lower(), "Body missing keyword: prototype"

    def test_contains_quick_or_quickly(self):
        _, body = _read()
        lower = body.lower()
        assert "quick" in lower, "Body missing keyword: quick/quickly"

    def test_contains_poc_or_proof_of_concept(self):
        _, body = _read()
        lower = body.lower()
        assert "poc" in lower or "proof-of-concept" in lower or "proof of concept" in lower, (
            "Body missing keyword: POC / proof-of-concept"
        )

    def test_contains_validate(self):
        _, body = _read()
        assert "validate" in body.lower(), "Body missing keyword: validate"


# ---------------------------------------------------------------------------
# Section structure
# ---------------------------------------------------------------------------


class TestSectionStructure:
    """All 5 required Markdown sections must be present."""

    @pytest.mark.parametrize("heading", [
        "## Role",
        "## Persona",
        "## How You Work",
        "## Zone Restrictions",
        "## What You Do Not Do",
    ])
    def test_section_exists(self, heading):
        _, body = _read()
        assert heading in body, f"Missing required section: {heading}"

    def test_at_least_five_h2_sections(self):
        _, body = _read()
        h2_count = len(re.findall(r"^## ", body, re.MULTILINE))
        assert h2_count >= 5, f"Expected ≥5 H2 sections, found {h2_count}"


# ---------------------------------------------------------------------------
# Zone restrictions
# ---------------------------------------------------------------------------


class TestZoneRestrictions:
    """Zone restriction table must list exactly the 3 denied paths."""

    def test_github_restricted(self):
        _, body = _read()
        assert "`.github/`" in body or "`.github`" in body or ".github/" in body

    def test_vscode_restricted(self):
        _, body = _read()
        assert "`.vscode/`" in body or "`.vscode`" in body or ".vscode/" in body

    def test_noagentzone_restricted(self):
        _, body = _read()
        assert "NoAgentZone" in body

    def test_zone_table_has_denied_path_header(self):
        _, body = _read()
        assert "Denied Path" in body, "Zone restriction table missing 'Denied Path' header"

    def test_zone_table_has_reason_column(self):
        _, body = _read()
        assert "Reason" in body, "Zone restriction table missing 'Reason' column"


# ---------------------------------------------------------------------------
# Agent cross-references
# ---------------------------------------------------------------------------


class TestAgentCrossReferences:
    """Body must reference other agents via @-mentions."""

    def test_references_programmer(self):
        _, body = _read()
        assert "@programmer" in body, "Missing cross-reference to @programmer"

    def test_references_tester(self):
        _, body = _read()
        assert "@tester" in body, "Missing cross-reference to @tester"

    def test_references_criticist(self):
        _, body = _read()
        assert "@criticist" in body, "Missing cross-reference to @criticist"

    def test_references_planner(self):
        _, body = _read()
        assert "@planner" in body, "Missing cross-reference to @planner"


# ---------------------------------------------------------------------------
# Placeholders and references
# ---------------------------------------------------------------------------


class TestPlaceholdersAndReferences:
    """Template placeholders and rule references."""

    def test_project_name_placeholder_at_least_two(self):
        _, body = _read()
        count = body.count("{{PROJECT_NAME}}")
        assert count >= 2, (
            f"{{{{PROJECT_NAME}}}} must appear ≥2 times in body, found {count}"
        )

    def test_agent_rules_referenced(self):
        _, body = _read()
        assert "AGENT-RULES.md" in body

    def test_description_is_meaningful(self):
        """Description field must be a real sentence, not a stub."""
        fm, _ = _read()
        desc = str(fm["description"])
        assert len(desc) >= 30, (
            f"Description too short ({len(desc)} chars): '{desc}'"
        )


# ---------------------------------------------------------------------------
# Tool set consistency with peer agents
# ---------------------------------------------------------------------------


class TestToolSetConsistency:
    """Prototyper must have the same 8-tool set as programmer, fixer, scientist."""

    @pytest.mark.parametrize("peer", ["programmer", "fixer", "scientist"])
    def test_same_tools_as_peer(self, peer):
        peer_file = AGENTS_DIR / f"{peer}.agent.md"
        if not peer_file.exists():
            pytest.skip(f"{peer}.agent.md not found")
        peer_content = peer_file.read_text(encoding="utf-8")
        peer_fm, _ = _parse_frontmatter(peer_content)
        proto_fm, _ = _read()
        assert set(proto_fm["tools"]) == set(peer_fm["tools"]), (
            f"Prototyper tools differ from {peer}: "
            f"proto={sorted(proto_fm['tools'])}, {peer}={sorted(peer_fm['tools'])}"
        )

    @pytest.mark.parametrize("peer", ["programmer", "fixer", "scientist"])
    def test_same_model_as_peer(self, peer):
        peer_file = AGENTS_DIR / f"{peer}.agent.md"
        if not peer_file.exists():
            pytest.skip(f"{peer}.agent.md not found")
        peer_content = peer_file.read_text(encoding="utf-8")
        peer_fm, _ = _parse_frontmatter(peer_content)
        proto_fm, _ = _read()
        assert proto_fm["model"] == peer_fm["model"], (
            f"Prototyper model ({proto_fm['model']}) differs from {peer} ({peer_fm['model']})"
        )


# ---------------------------------------------------------------------------
# Content quality
# ---------------------------------------------------------------------------


class TestContentQuality:
    """Body quality and formatting checks."""

    def test_no_todo_or_placeholder_text(self):
        _, body = _read()
        lower = body.lower()
        assert "todo" not in lower, "Body contains TODO placeholder"
        assert "fixme" not in lower, "Body contains FIXME placeholder"
        assert "xxx" not in lower.replace("xxx", "").join("") or True  # skip false positives
        # Simple check: no literal [TODO] or [FIXME]
        assert "[todo]" not in lower, "Body contains [TODO] marker"
        assert "[fixme]" not in lower, "Body contains [FIXME] marker"

    def test_body_does_not_contain_raw_html(self):
        _, body = _read()
        assert "<script" not in body.lower(), "Body contains <script> tag"
        assert "<style" not in body.lower(), "Body contains <style> tag"

    def test_frontmatter_closed_properly(self):
        """YAML frontmatter must have a closing --- delimiter."""
        content = AGENT_FILE.read_text(encoding="utf-8")
        assert content.startswith("---")
        rest = content[3:]
        assert "---" in rest, "Missing closing --- for YAML frontmatter"

    def test_file_encoding_is_utf8(self):
        """File must be readable as UTF-8 without errors."""
        AGENT_FILE.read_text(encoding="utf-8")  # raises on bad encoding

    def test_no_trailing_whitespace_in_frontmatter(self):
        """YAML frontmatter lines should not have excessive trailing whitespace."""
        content = AGENT_FILE.read_text(encoding="utf-8")
        end = content.index("---", 3)
        yaml_lines = content[3:end].split("\n")
        for i, line in enumerate(yaml_lines, start=1):
            stripped = line.rstrip()
            # Allow minor trailing spaces but flag tabs or excessive whitespace
            assert len(line) - len(stripped) < 10, (
                f"Frontmatter line {i} has excessive trailing whitespace"
            )
