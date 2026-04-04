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
    "Planner",
    "Workspace-Cleaner",
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

    def test_frontmatter_all_6_agents_present(self):
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

    def test_all_6_at_refs_present_in_body(self):
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
        # Find the delegation section (## Core Loop or ## Delegation Table)
        section_name = "## Core Loop" if "## Core Loop" in body else "## Delegation Table"
        assert section_name in body, "Delegation/Core Loop section not found"
        table_start = body.index(section_name)
        # Slice from the section heading to the next heading
        remaining = body[table_start:]
        next_heading = re.search(r"\n## ", remaining[3:])
        table_section = remaining[: next_heading.start() + 3] if next_heading else remaining
        for agent in EXPECTED_AGENTS:
            assert f"`@{agent}`" in table_section, (
                f"PascalCase '`@{agent}`' not found in delegation section"
            )

    def test_delegation_table_no_lowercase_agents(self):
        content = _read_file()
        body = _get_body(content)
        section_name = "## Core Loop" if "## Core Loop" in body else "## Delegation Table"
        assert section_name in body
        table_start = body.index(section_name)
        remaining = body[table_start:]
        next_heading = re.search(r"\n## ", remaining[3:])
        table_section = remaining[: next_heading.start() + 3] if next_heading else remaining
        for lc_agent in LOWERCASE_AGENTS:
            assert f"`@{lc_agent}`" not in table_section, (
                f"Lowercase '`@{lc_agent}`' still present in delegation section"
            )


class TestPersonaSection:
    """Core Loop section must use PascalCase for @agent references."""

    def test_persona_planner_pascal(self):
        content = _read_file()
        body = _get_body(content)
        # Check Core Loop section (coordinator has no ## Persona section)
        section_name = "## Core Loop" if "## Core Loop" in body else "## Persona"
        if section_name not in body:
            pytest.skip(f"Section '{section_name}' not found")
        section_start = body.index(section_name)
        remaining = body[section_start:]
        next_heading = re.search(r"\n## ", remaining[3:])
        section = remaining[: next_heading.start() + 3] if next_heading else remaining
        assert "`@Planner`" in section, "@Planner not found in Core Loop section"
        assert "`@planner`" not in section, "Lowercase @planner still in Core Loop section"

    def test_persona_tester_pascal(self):
        content = _read_file()
        body = _get_body(content)
        section_name = "## Core Loop" if "## Core Loop" in body else "## Persona"
        if section_name not in body:
            pytest.skip(f"Section '{section_name}' not found")
        section_start = body.index(section_name)
        remaining = body[section_start:]
        next_heading = re.search(r"\n## ", remaining[3:])
        section = remaining[: next_heading.start() + 3] if next_heading else remaining
        assert "`@Tester`" in section, "@Tester not found in Core Loop section"
        assert "`@tester`" not in section, "Lowercase @tester still in Core Loop section"

    def test_persona_criticist_pascal(self):
        content = _read_file()
        body = _get_body(content)
        section_name = "## Core Loop" if "## Core Loop" in body else "## Persona"
        if section_name not in body:
            pytest.skip(f"Section '{section_name}' not found")
        section_start = body.index(section_name)
        remaining = body[section_start:]
        next_heading = re.search(r"\n## ", remaining[3:])
        section = remaining[: next_heading.start() + 3] if next_heading else remaining
        # @Criticist was removed; check @Workspace-Cleaner instead
        assert "`@Workspace-Cleaner`" in section, "@Workspace-Cleaner not found in Core Loop section"
        assert "`@criticist`" not in section, "Lowercase @criticist still present"


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
        # Check that @Programmer and @Tester are in section (brainstormer not in this section)
        assert "`@Programmer`" in section, "@Programmer not found in What You Do Not Do"
        assert "`@brainstormer`" not in section, "Lowercase @brainstormer in What You Do Not Do"
