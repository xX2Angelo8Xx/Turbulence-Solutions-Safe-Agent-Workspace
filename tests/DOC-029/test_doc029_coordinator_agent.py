"""
Tests for DOC-029: coordinator.agent.md for Agent Workbench
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

EXPECTED_TOOLS = {"read", "edit", "search", "execute", "agent", "todo"}
EXPECTED_AGENTS = {
    "Programmer", "Tester", "Brainstormer", "Researcher",
    "Planner", "Workspace-Cleaner"
}


def _load_frontmatter(path):
    """Parse YAML frontmatter from an agent .md file."""
    with open(path, encoding="utf-8") as f:
        content = f.read()
    if not content.startswith("---"):
        return {}, content
    end = content.find("---", 3)
    if end == -1:
        return {}, content
    yaml_block = content[3:end].strip()
    body = content[end + 3:].strip()
    data = yaml.safe_load(yaml_block)
    return data, body


class TestCoordinatorFileExists:
    def test_file_exists(self):
        assert os.path.isfile(COORDINATOR_PATH), (
            f"coordinator.agent.md not found at {COORDINATOR_PATH}"
        )

    def test_file_non_empty(self):
        size = os.path.getsize(COORDINATOR_PATH)
        assert size > 0, "coordinator.agent.md is empty"


class TestCoordinatorFrontmatter:
    def setup_method(self):
        self.data, self.body = _load_frontmatter(COORDINATOR_PATH)

    def test_name_field_present(self):
        assert "name" in self.data, "YAML frontmatter missing 'name' field"

    def test_description_field_present(self):
        assert "description" in self.data, "YAML frontmatter missing 'description' field"
        assert self.data["description"], "'description' field is empty"

    def test_tools_field_present(self):
        assert "tools" in self.data, "YAML frontmatter missing 'tools' field"

    def test_agents_field_present(self):
        assert "agents" in self.data, "YAML frontmatter missing 'agents' field"

    def test_model_field_present(self):
        assert "model" in self.data, "YAML frontmatter missing 'model' field"


class TestCoordinatorTools:
    def setup_method(self):
        self.data, self.body = _load_frontmatter(COORDINATOR_PATH)

    def test_tools_is_list(self):
        assert isinstance(self.data.get("tools"), list), "'tools' must be a list"

    def test_all_expected_tools_present(self):
        tools = set(self.data.get("tools", []))
        missing = EXPECTED_TOOLS - tools
        assert not missing, f"Missing tools in coordinator: {missing}"


class TestCoordinatorAgents:
    def setup_method(self):
        self.data, self.body = _load_frontmatter(COORDINATOR_PATH)

    def test_agents_is_list(self):
        assert isinstance(self.data.get("agents"), list), "'agents' must be a list"

    def test_all_6_specialist_agents_present(self):
        agents = set(self.data.get("agents", []))
        missing = EXPECTED_AGENTS - agents
        assert not missing, f"Missing agents in coordinator: {missing}"


class TestCoordinatorModel:
    def setup_method(self):
        self.data, self.body = _load_frontmatter(COORDINATOR_PATH)

    def test_model_value(self):
        model = self.data.get("model")
        # Coordinator uses both Opus (planning) and Sonnet (execution)
        assert model is not None, "model field missing"
        model_str = str(model)
        assert "Opus" in model_str or "Sonnet" in model_str, (
            f"Expected a valid Copilot model, got {model!r}"
        )


class TestCoordinatorBody:
    def setup_method(self):
        self.data, self.body = _load_frontmatter(COORDINATOR_PATH)
        with open(COORDINATOR_PATH, encoding="utf-8") as f:
            self.full_content = f.read()

    def test_body_mentions_delegation(self):
        assert re.search(r"delegat", self.body, re.IGNORECASE), (
            "Body does not mention delegation"
        )

    def test_body_mentions_validation(self):
        assert re.search(r"validat", self.body, re.IGNORECASE), (
            "Body does not mention validation"
        )

    def test_body_mentions_zone_restrictions(self):
        assert re.search(r"zone restriction", self.body, re.IGNORECASE), (
            "Body does not mention zone restrictions"
        )

    def test_project_name_placeholder_present(self):
        assert "{{PROJECT_NAME}}" in self.full_content, (
            "coordinator.agent.md does not contain {{PROJECT_NAME}} placeholder"
        )


class TestReadmeUpdated:
    def test_readme_has_agent_rows(self):
        with open(README_PATH, encoding="utf-8") as f:
            content = f.read()
        # Count data rows in the agent table (lines with | ... | format, not header or separator)
        rows = [
            line for line in content.splitlines()
            if re.match(r"^\|", line)
            and re.search(r"agent\.md", line, re.IGNORECASE)
            and "---" not in line
        ]
        assert len(rows) >= 7, (
            f"README.md agent table has {len(rows)} agent rows, expected at least 7"
        )

    def test_readme_contains_coordinator(self):
        with open(README_PATH, encoding="utf-8") as f:
            content = f.read()
        assert "Coordinator" in content, "README.md does not mention Coordinator"

    def test_readme_contains_coordinator_file_ref(self):
        with open(README_PATH, encoding="utf-8") as f:
            content = f.read()
        assert "coordinator.agent.md" in content, (
            "README.md does not reference coordinator.agent.md"
        )
