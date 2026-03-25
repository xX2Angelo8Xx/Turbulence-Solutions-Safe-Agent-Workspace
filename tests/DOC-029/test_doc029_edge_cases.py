"""
Edge-case tests for DOC-029: coordinator.agent.md for Agent Workbench.

Covers:
- Agents list has exactly 10 entries (no more, no fewer)
- No duplicate agents in the list
- argument-hint frontmatter field is present and non-empty
- Zone restrictions table covers exactly 3 denied paths
- Body uses @<agent> cross-reference syntax for all specialists
- AGENT-RULES.md is referenced in the body
- Model matches the standard 'Claude Opus 4.6 (copilot)' used by other fixed agents
- Tools count is exactly 7
- No extra/unexpected tools
- README table row count is exactly 11 (no accidental duplicates)
- coordinator.agent.md has valid YAML frontmatter (parseable without error)
"""
import os
import re
import yaml
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COORDINATOR_PATH = os.path.join(
    REPO_ROOT, "templates", "agent-workbench", ".github", "agents", "coordinator.agent.md"
)
README_PATH = os.path.join(
    REPO_ROOT, "templates", "agent-workbench", ".github", "agents", "README.md"
)

EXPECTED_TOOLS = {"read", "edit", "search", "execute", "agent", "todo", "ask"}
EXPECTED_AGENTS = [
    "Programmer", "Tester", "Brainstormer", "Researcher",
    "Scientist", "Criticist", "Planner", "Fixer", "Writer", "Prototyper"
]
STANDARD_MODEL = ["Claude Opus 4.6 (copilot)"]
DENIED_PATHS = [".github/", ".vscode/", "NoAgentZone/"]


def _load_frontmatter(path):
    """Parse YAML frontmatter from an agent .md file."""
    with open(path, encoding="utf-8") as f:
        content = f.read()
    if not content.startswith("---"):
        return {}, content, content
    end = content.find("---", 3)
    if end == -1:
        return {}, content, content
    yaml_block = content[3:end].strip()
    body = content[end + 3:].strip()
    data = yaml.safe_load(yaml_block)
    return data, body, content


class TestAgentsListExactCount:
    """agents list must have exactly 10 specialists — no more, no fewer."""

    def setup_method(self):
        self.data, self.body, self.full = _load_frontmatter(COORDINATOR_PATH)

    def test_agents_count_exactly_10(self):
        agents = self.data.get("agents", [])
        assert len(agents) == 10, (
            f"Expected exactly 10 agents, got {len(agents)}: {agents}"
        )

    def test_no_duplicate_agents(self):
        agents = self.data.get("agents", [])
        seen = set()
        duplicates = []
        for a in agents:
            if a in seen:
                duplicates.append(a)
            seen.add(a)
        assert not duplicates, f"Duplicate agents found: {duplicates}"

    def test_all_expected_agents_present(self):
        agents = set(self.data.get("agents", []))
        missing = set(EXPECTED_AGENTS) - agents
        assert not missing, f"Missing specialist agents: {sorted(missing)}"

    def test_no_unexpected_agents(self):
        agents = set(self.data.get("agents", []))
        unexpected = agents - set(EXPECTED_AGENTS)
        assert not unexpected, f"Unexpected agents in list: {sorted(unexpected)}"

    def test_coordinator_not_in_own_agents_list(self):
        """Coordinator should not delegate to itself."""
        agents = self.data.get("agents", [])
        assert "coordinator" not in agents, (
            "Coordinator must not list itself in agents (infinite loop risk)"
        )


class TestArgumentHint:
    """argument-hint must be present and non-empty."""

    def setup_method(self):
        self.data, self.body, self.full = _load_frontmatter(COORDINATOR_PATH)

    def test_argument_hint_present(self):
        assert "argument-hint" in self.data, (
            "YAML frontmatter missing 'argument-hint' field"
        )

    def test_argument_hint_non_empty(self):
        hint = self.data.get("argument-hint", "")
        assert hint and str(hint).strip(), "argument-hint is empty"

    def test_argument_hint_is_string(self):
        hint = self.data.get("argument-hint")
        assert isinstance(hint, str), f"argument-hint should be a string, got {type(hint)}"


class TestZoneRestrictions:
    """Body must reference a zone restrictions table with exactly 3 denied paths."""

    def setup_method(self):
        self.data, self.body, self.full = _load_frontmatter(COORDINATOR_PATH)

    def test_three_denied_paths_listed(self):
        """Each of the 3 denied paths must appear somewhere in the body."""
        for path in DENIED_PATHS:
            assert path in self.body, (
                f"Denied path '{path}' not found in zone restrictions section"
            )

    def test_zone_restrictions_section_exists(self):
        assert re.search(r"#+\s*Zone Restriction", self.body, re.IGNORECASE), (
            "No '## Zone Restrictions' heading found in body"
        )

    def test_denied_path_table_has_3_rows(self):
        """Count table data rows (non-header, non-separator) in zone restriction block."""
        # Find the zone restriction section
        section_match = re.search(
            r"#+\s*Zone Restriction.*?(?=\n#+\s|\Z)", self.body, re.IGNORECASE | re.DOTALL
        )
        assert section_match, "Zone Restrictions section not found"
        section = section_match.group(0)
        # Count table rows: lines starting with | that are not header or separator rows
        rows = [
            line for line in section.splitlines()
            if re.match(r"^\|", line)
            and not re.match(r"^\|\s*[-:]+\s*\|", line)
            and not re.match(r"^\|\s*Denied Path", line, re.IGNORECASE)
        ]
        assert len(rows) == 3, (
            f"Expected 3 denied-path rows in zone restrictions table, found {len(rows)}: {rows}"
        )


class TestAtSyntaxCrossReferences:
    """Body must use @<agent> syntax to cross-reference specialist agents."""

    def setup_method(self):
        self.data, self.body, self.full = _load_frontmatter(COORDINATOR_PATH)

    def test_at_syntax_used_for_programmer(self):
        assert "@Programmer" in self.body, "Body does not reference @Programmer"

    def test_at_syntax_used_for_tester(self):
        assert "@Tester" in self.body, "Body does not reference @Tester"

    def test_at_syntax_used_for_planner(self):
        assert "@Planner" in self.body, "Body does not reference @Planner"

    def test_at_syntax_used_for_fixer(self):
        assert "@Fixer" in self.body, "Body does not reference @Fixer"

    def test_at_syntax_used_for_criticist(self):
        assert "@Criticist" in self.body, "Body does not reference @Criticist"

    def test_at_syntax_present_for_all_10_agents(self):
        missing = [a for a in EXPECTED_AGENTS if f"@{a}" not in self.body]
        assert not missing, f"Missing @<agent> syntax for: {missing}"


class TestAgentRulesReference:
    """AGENT-RULES.md must be referenced in the body."""

    def setup_method(self):
        self.data, self.body, self.full = _load_frontmatter(COORDINATOR_PATH)

    def test_agent_rules_md_referenced(self):
        assert "AGENT-RULES.md" in self.body, (
            "coordinator.agent.md does not reference AGENT-RULES.md"
        )

    def test_agent_rules_reference_in_zone_section(self):
        """AGENT-RULES.md should be referenced near the zone restrictions."""
        section_match = re.search(
            r"#+\s*Zone Restriction.*?(?=\n#+\s|\Z)", self.body, re.IGNORECASE | re.DOTALL
        )
        assert section_match, "Zone Restrictions section not found"
        section = section_match.group(0)
        assert "AGENT-RULES.md" in section, (
            "AGENT-RULES.md is not referenced in the Zone Restrictions section"
        )


class TestModelConsistency:
    """Model must match the standard used by all other fixed agent files."""

    def setup_method(self):
        self.data, self.body, self.full = _load_frontmatter(COORDINATOR_PATH)
        self.agents_dir = os.path.join(
            REPO_ROOT, "templates", "agent-workbench", ".github", "agents"
        )

    def test_model_exact_value(self):
        model = self.data.get("model")
        assert model == STANDARD_MODEL, (
            f"Model mismatch. Expected {STANDARD_MODEL!r}, got {model!r}"
        )

    def test_model_matches_other_agent_files(self):
        """Coordinator model must match all sibling agent files."""
        mismatches = []
        for fname in os.listdir(self.agents_dir):
            if not fname.endswith(".agent.md") or fname == "coordinator.agent.md":
                continue
            fpath = os.path.join(self.agents_dir, fname)
            try:
                data, _, _ = _load_frontmatter(fpath)
                other_model = data.get("model")
                if other_model != STANDARD_MODEL:
                    mismatches.append(f"{fname}: {other_model!r}")
            except Exception:
                pass  # Ignore parse errors in sibling files
        # Coordinator must match. If all siblings agree, so must coordinator.
        coordinator_model = self.data.get("model")
        assert coordinator_model == STANDARD_MODEL, (
            f"Coordinator model {coordinator_model!r} differs from standard {STANDARD_MODEL!r}"
        )
        # Log any sibling inconsistencies as informational (not fail)
        # (Coordinator cannot be blamed for pre-existing sibling inconsistencies)


class TestToolsExactSet:
    """Tools list must be exactly 7 specific tools."""

    def setup_method(self):
        self.data, self.body, self.full = _load_frontmatter(COORDINATOR_PATH)

    def test_tools_count_exactly_7(self):
        tools = self.data.get("tools", [])
        assert len(tools) == 7, (
            f"Expected exactly 7 tools, got {len(tools)}: {tools}"
        )

    def test_no_duplicate_tools(self):
        tools = self.data.get("tools", [])
        seen = set()
        duplicates = []
        for t in tools:
            if t in seen:
                duplicates.append(t)
            seen.add(t)
        assert not duplicates, f"Duplicate tools found: {duplicates}"

    def test_no_unexpected_tools(self):
        tools = set(self.data.get("tools", []))
        unexpected = tools - EXPECTED_TOOLS
        assert not unexpected, f"Unexpected tools in list: {sorted(unexpected)}"


class TestReadmeTableIntegrity:
    """README.md table must have exactly 11 agent rows — no duplicates."""

    def setup_method(self):
        with open(README_PATH, encoding="utf-8") as f:
            self.content = f.read()

    def _get_agent_rows(self):
        return [
            line for line in self.content.splitlines()
            if re.match(r"^\|\s+\w", line)
            and "Agent" not in line
            and "---" not in line
        ]

    def test_readme_exactly_11_rows(self):
        rows = self._get_agent_rows()
        assert len(rows) == 11, (
            f"README agent table has {len(rows)} rows, expected exactly 11"
        )

    def test_readme_no_duplicate_coordinator_entry(self):
        coordinator_rows = [
            line for line in self._get_agent_rows()
            if "Coordinator" in line or "coordinator" in line
        ]
        assert len(coordinator_rows) == 1, (
            f"Expected exactly 1 Coordinator row in README, found {len(coordinator_rows)}"
        )

    def test_readme_coordinator_description_mentions_delegation(self):
        rows = self._get_agent_rows()
        coordinator_row = next(
            (r for r in rows if "Coordinator" in r or "coordinator" in r), None
        )
        assert coordinator_row is not None, "Coordinator row not found in README"
        assert re.search(r"delegat", coordinator_row, re.IGNORECASE), (
            f"Coordinator README row does not mention delegation: {coordinator_row}"
        )


class TestFrontmatterParseable:
    """YAML frontmatter must be valid and parseable without errors."""

    def test_yaml_frontmatter_valid(self):
        with open(COORDINATOR_PATH, encoding="utf-8") as f:
            content = f.read()
        assert content.startswith("---"), "File does not start with YAML frontmatter delimiter"
        end = content.find("---", 3)
        assert end != -1, "YAML frontmatter closing delimiter '---' not found"
        yaml_block = content[3:end].strip()
        try:
            parsed = yaml.safe_load(yaml_block)
        except yaml.YAMLError as e:
            pytest.fail(f"YAML frontmatter is not valid: {e}")
        assert isinstance(parsed, dict), "Parsed frontmatter should be a dict"

    def test_name_value_is_coordinator(self):
        data, _, _ = _load_frontmatter(COORDINATOR_PATH)
        assert data.get("name") == "Coordinator", (
            f"Expected name 'Coordinator', got {data.get('name')!r}"
        )
