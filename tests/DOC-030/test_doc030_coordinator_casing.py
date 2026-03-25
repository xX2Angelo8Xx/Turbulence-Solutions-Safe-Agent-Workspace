"""
DOC-030 — Tests for coordinator.agent.md PascalCase agent name casing.

Verifies that all 10 agent names in the coordinator template use PascalCase
in the YAML frontmatter, delegation table, How You Work section, Persona
section, and What You Do Not Do section.
"""

import re
from pathlib import Path

COORDINATOR_PATH = Path(__file__).parent.parent.parent / (
    "templates/agent-workbench/.github/agents/coordinator.agent.md"
)

EXPECTED_AGENTS = [
    "Programmer",
    "Tester",
    "Brainstormer",
    "Researcher",
    "Scientist",
    "Criticist",
    "Planner",
    "Fixer",
    "Writer",
    "Prototyper",
]

LOWERCASE_AGENTS = [a.lower() for a in EXPECTED_AGENTS]


def _read_file() -> str:
    assert COORDINATOR_PATH.exists(), f"coordinator.agent.md not found at {COORDINATOR_PATH}"
    return COORDINATOR_PATH.read_text(encoding="utf-8")


def _get_frontmatter(content: str) -> str:
    """Extract the YAML frontmatter block (between the first two --- delimiters)."""
    lines = content.splitlines()
    in_front = False
    front_lines = []
    for line in lines:
        if line.strip() == "---":
            if not in_front:
                in_front = True
                continue
            else:
                break
        if in_front:
            front_lines.append(line)
    return "\n".join(front_lines)


def _get_body(content: str) -> str:
    """Extract the body (everything after the closing ---)."""
    parts = content.split("---", 2)
    return parts[2] if len(parts) >= 3 else content


class TestFrontmatterAgentsCasing:
    """Frontmatter agents: list must use PascalCase for all 10 agents."""

    def test_frontmatter_agents_line_exists(self):
        content = _read_file()
        front = _get_frontmatter(content)
        assert "agents:" in front, "No 'agents:' key found in YAML frontmatter"

    def test_frontmatter_all_10_agents_present(self):
        content = _read_file()
        front = _get_frontmatter(content)
        agents_line = next(
            (line for line in front.splitlines() if line.startswith("agents:")), None
        )
        assert agents_line is not None, "agents: line not found in frontmatter"
        for agent in EXPECTED_AGENTS:
            assert agent in agents_line, (
                f"Expected PascalCase agent '{agent}' not found in frontmatter agents list"
            )

    def test_frontmatter_no_lowercase_agents(self):
        content = _read_file()
        front = _get_frontmatter(content)
        agents_line = next(
            (line for line in front.splitlines() if line.startswith("agents:")), None
        )
        assert agents_line is not None
        for lc_agent in LOWERCASE_AGENTS:
            # Match the exact lowercase token (surrounded by non-alpha chars)
            pattern = rf"(?<![A-Za-z]){re.escape(lc_agent)}(?![A-Za-z])"
            assert not re.search(pattern, agents_line), (
                f"Lowercase agent name '{lc_agent}' found in frontmatter agents list"
            )


class TestBodyAtReferenceCasing:
    """All @agent references in the body must be PascalCase."""

    def test_all_10_at_refs_present_in_body(self):
        content = _read_file()
        body = _get_body(content)
        for agent in EXPECTED_AGENTS:
            assert f"@{agent}" in body, (
                f"Expected PascalCase reference '@{agent}' not found in document body"
            )

    def test_no_lowercase_at_refs_in_body(self):
        content = _read_file()
        body = _get_body(content)
        for lc_agent in LOWERCASE_AGENTS:
            assert f"@{lc_agent}" not in body, (
                f"Lowercase @-reference '@{lc_agent}' still present in document body"
            )


class TestDelegationTable:
    """Delegation table must map all 10 goal types to PascalCase @agents."""

    def test_delegation_table_all_agents(self):
        content = _read_file()
        body = _get_body(content)
        # Find the delegation table section
        assert "## Delegation Table" in body, "Delegation Table section not found"
        table_start = body.index("## Delegation Table")
        # Slice from the table heading to the next heading
        remaining = body[table_start:]
        next_heading = re.search(r"\n## ", remaining[3:])
        table_section = remaining[: next_heading.start() + 3] if next_heading else remaining
        for agent in EXPECTED_AGENTS:
            assert f"`@{agent}`" in table_section, (
                f"PascalCase '`@{agent}`' not found in Delegation Table"
            )

    def test_delegation_table_no_lowercase_agents(self):
        content = _read_file()
        body = _get_body(content)
        assert "## Delegation Table" in body
        table_start = body.index("## Delegation Table")
        remaining = body[table_start:]
        next_heading = re.search(r"\n## ", remaining[3:])
        table_section = remaining[: next_heading.start() + 3] if next_heading else remaining
        for lc_agent in LOWERCASE_AGENTS:
            assert f"`@{lc_agent}`" not in table_section, (
                f"Lowercase '`@{lc_agent}`' still present in Delegation Table"
            )


class TestPersonaSection:
    """Persona section must use PascalCase for @agent references."""

    def test_persona_planner_pascal(self):
        content = _read_file()
        body = _get_body(content)
        assert "## Persona" in body
        persona_start = body.index("## Persona")
        remaining = body[persona_start:]
        next_heading = re.search(r"\n## ", remaining[3:])
        persona_section = remaining[: next_heading.start() + 3] if next_heading else remaining
        assert "`@Planner`" in persona_section, "@Planner not found in Persona section"
        assert "`@planner`" not in persona_section, "Lowercase @planner still in Persona section"

    def test_persona_tester_pascal(self):
        content = _read_file()
        body = _get_body(content)
        assert "## Persona" in body
        persona_start = body.index("## Persona")
        remaining = body[persona_start:]
        next_heading = re.search(r"\n## ", remaining[3:])
        persona_section = remaining[: next_heading.start() + 3] if next_heading else remaining
        assert "`@Tester`" in persona_section, "@Tester not found in Persona section"
        assert "`@tester`" not in persona_section, "Lowercase @tester still in Persona section"

    def test_persona_criticist_pascal(self):
        content = _read_file()
        body = _get_body(content)
        assert "## Persona" in body
        persona_start = body.index("## Persona")
        remaining = body[persona_start:]
        next_heading = re.search(r"\n## ", remaining[3:])
        persona_section = remaining[: next_heading.start() + 3] if next_heading else remaining
        assert "`@Criticist`" in persona_section, "@Criticist not found in Persona section"
        assert "`@criticist`" not in persona_section, "Lowercase @criticist still in Persona section"


class TestWhatYouDoNotDo:
    """What You Do Not Do section must use PascalCase."""

    def test_what_you_do_not_do_programmer(self):
        content = _read_file()
        body = _get_body(content)
        assert "## What You Do Not Do" in body
        section_start = body.index("## What You Do Not Do")
        section = body[section_start:]
        assert "`@Programmer`" in section, "@Programmer not found in What You Do Not Do"
        assert "`@programmer`" not in section, "Lowercase @programmer in What You Do Not Do"

    def test_what_you_do_not_do_tester(self):
        content = _read_file()
        body = _get_body(content)
        assert "## What You Do Not Do" in body
        section_start = body.index("## What You Do Not Do")
        section = body[section_start:]
        assert "`@Tester`" in section, "@Tester not found in What You Do Not Do"
        assert "`@tester`" not in section, "Lowercase @tester in What You Do Not Do"

    def test_what_you_do_not_do_brainstormer(self):
        content = _read_file()
        body = _get_body(content)
        assert "## What You Do Not Do" in body
        section_start = body.index("## What You Do Not Do")
        section = body[section_start:]
        assert "`@Brainstormer`" in section, "@Brainstormer not found in What You Do Not Do"
        assert "`@brainstormer`" not in section, "Lowercase @brainstormer in What You Do Not Do"
