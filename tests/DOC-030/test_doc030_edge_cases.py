"""
DOC-030 — Tester edge-case tests for coordinator.agent.md PascalCase fix.

These tests go beyond the developer's suite and cover:
  - Full-file scan (frontmatter + body) for stray lowercase @-refs
  - No duplicate agents in frontmatter agents list
  - Exactly 10 agents — no extras, no omissions
  - No merge conflict markers (sanity guard)
  - How You Work step-4 bullet list contains all 10 PascalCase refs
  - Mixed/ALLCAPS casing variants absent
  - Frontmatter agents list is a proper inline YAML array (not multi-line)
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
ALLCAPS_AGENTS = [a.upper() for a in EXPECTED_AGENTS]


def _read_file() -> str:
    assert COORDINATOR_PATH.exists(), f"coordinator.agent.md not found at {COORDINATOR_PATH}"
    return COORDINATOR_PATH.read_text(encoding="utf-8")


def _get_frontmatter(content: str) -> str:
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
    parts = content.split("---", 2)
    return parts[2] if len(parts) >= 3 else content


def _get_agents_from_frontmatter(front: str) -> list[str]:
    """Parse the inline YAML array from the agents: line."""
    agents_line = next(
        (line for line in front.splitlines() if line.startswith("agents:")), None
    )
    if agents_line is None:
        return []
    # Extract content between [ and ]
    match = re.search(r"\[([^\]]*)\]", agents_line)
    if not match:
        return []
    items = [item.strip() for item in match.group(1).split(",")]
    return items


class TestFullFileLowercaseScan:
    """Scan the ENTIRE file (frontmatter + body) for stray lowercase @-refs."""

    def test_no_at_lowercase_anywhere_in_full_file(self):
        """No @lowercase agent reference must exist anywhere in the file."""
        content = _read_file()
        for lc_agent in LOWERCASE_AGENTS:
            assert f"@{lc_agent}" not in content, (
                f"Stray lowercase '@{lc_agent}' found somewhere in the full file "
                f"(including frontmatter, description, or model fields)"
            )

    def test_no_at_allcaps_anywhere_in_full_file(self):
        """No ALLCAPS @AGENT variant should exist — only PascalCase is valid."""
        content = _read_file()
        for caps_agent in ALLCAPS_AGENTS:
            assert f"@{caps_agent}" not in content, (
                f"ALLCAPS variant '@{caps_agent}' found in file — only PascalCase is valid"
            )


class TestFrontmatterAgentListIntegrity:
    """Structural integrity checks on the agents: list in the YAML frontmatter."""

    def test_frontmatter_agents_is_inline_array(self):
        """The agents: value must be an inline YAML array [...], not multi-line."""
        content = _read_file()
        front = _get_frontmatter(content)
        agents_line = next(
            (line for line in front.splitlines() if line.startswith("agents:")), None
        )
        assert agents_line is not None, "agents: line not found in frontmatter"
        assert "[" in agents_line and "]" in agents_line, (
            "agents: value must be an inline YAML array [...] on a single line"
        )

    def test_frontmatter_exactly_10_agents(self):
        """There must be exactly 10 agents in the frontmatter, no more, no less."""
        content = _read_file()
        front = _get_frontmatter(content)
        agents = _get_agents_from_frontmatter(front)
        assert len(agents) == 10, (
            f"Expected exactly 10 agents in frontmatter, found {len(agents)}: {agents}"
        )

    def test_frontmatter_no_duplicate_agents(self):
        """No agent should appear twice in the frontmatter agents list."""
        content = _read_file()
        front = _get_frontmatter(content)
        agents = _get_agents_from_frontmatter(front)
        seen = set()
        duplicates = []
        for agent in agents:
            if agent in seen:
                duplicates.append(agent)
            seen.add(agent)
        assert not duplicates, (
            f"Duplicate agents found in frontmatter agents list: {duplicates}"
        )

    def test_frontmatter_agents_match_expected_set(self):
        """The frontmatter agents list must contain exactly the 10 expected PascalCase names."""
        content = _read_file()
        front = _get_frontmatter(content)
        agents = _get_agents_from_frontmatter(front)
        assert set(agents) == set(EXPECTED_AGENTS), (
            f"Frontmatter agents list mismatch.\n"
            f"  Expected: {sorted(EXPECTED_AGENTS)}\n"
            f"  Got:      {sorted(agents)}"
        )


class TestHowYouWorkSection:
    """How You Work step 4 bullet list must contain all 10 PascalCase @-refs with backticks."""

    def test_how_you_work_section_exists(self):
        content = _read_file()
        body = _get_body(content)
        assert "## How You Work" in body, "Section '## How You Work' not found in body"

    def test_how_you_work_all_10_backtick_refs(self):
        """Step 4 in How You Work must have all 10 agents as `@Agent` references."""
        content = _read_file()
        body = _get_body(content)
        assert "## How You Work" in body
        section_start = body.index("## How You Work")
        remaining = body[section_start:]
        next_heading = re.search(r"\n## ", remaining[3:])
        section = remaining[: next_heading.start() + 3] if next_heading else remaining
        for agent in EXPECTED_AGENTS:
            assert f"`@{agent}`" in section, (
                f"PascalCase '`@{agent}`' not found in How You Work section"
            )

    def test_how_you_work_no_lowercase_backtick_refs(self):
        """How You Work section must have zero lowercase `@agent` backtick refs."""
        content = _read_file()
        body = _get_body(content)
        assert "## How You Work" in body
        section_start = body.index("## How You Work")
        remaining = body[section_start:]
        next_heading = re.search(r"\n## ", remaining[3:])
        section = remaining[: next_heading.start() + 3] if next_heading else remaining
        for lc_agent in LOWERCASE_AGENTS:
            assert f"`@{lc_agent}`" not in section, (
                f"Lowercase '`@{lc_agent}`' still present in How You Work section"
            )


class TestFileSanity:
    """Sanity checks on the coordinator.agent.md file itself."""

    def test_no_merge_conflict_markers(self):
        """File must not contain git merge conflict markers."""
        content = _read_file()
        for marker in ["<<<<<<< ", "=======\n", ">>>>>>> "]:
            assert marker not in content, (
                f"Git merge conflict marker '{marker.strip()}' found in coordinator.agent.md"
            )

    def test_file_is_valid_utf8(self):
        """File must be decodable as UTF-8 (no binary corruption)."""
        raw = COORDINATOR_PATH.read_bytes()
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AssertionError(
                f"coordinator.agent.md is not valid UTF-8: {exc}"
            ) from exc

    def test_frontmatter_present_and_closed(self):
        """File must have a properly opened and closed YAML frontmatter block."""
        content = _read_file()
        # Should start with ---
        assert content.startswith("---\n") or content.startswith("---\r\n"), (
            "File does not start with YAML frontmatter delimiter '---'"
        )
        # Should have at least two --- delimiters
        delimiter_count = content.count("\n---\n") + content.count("\n---\r\n")
        assert delimiter_count >= 1, (
            "Frontmatter closing delimiter '---' not found — frontmatter is not properly closed"
        )

    def test_no_trailing_whitespace_on_agent_names(self):
        """Agent names in frontmatter must not have leading/trailing whitespace."""
        content = _read_file()
        front = _get_frontmatter(content)
        agents = _get_agents_from_frontmatter(front)
        for agent in agents:
            assert agent == agent.strip(), (
                f"Agent name '{agent}' has leading or trailing whitespace in frontmatter"
            )
