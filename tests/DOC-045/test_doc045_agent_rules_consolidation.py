"""Tests for DOC-045: Consolidate AGENT-RULES into AgentDocs folder.

Verifies that:
- templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md exists and contains
  all required sections from the three merged source files.
- templates/agent-workbench/Project/AGENT-RULES.md does NOT exist (deleted).
- templates/agent-workbench/Project/README.md does NOT exist (deleted).
- templates/agent-workbench/Project/AgentDocs/README.md does NOT exist (deleted).
"""

import pathlib

import pytest

TEMPLATE_ROOT = pathlib.Path(__file__).parents[2] / "templates" / "agent-workbench"
PROJECT_DIR = TEMPLATE_ROOT / "Project"
AGENTDOCS_DIR = PROJECT_DIR / "AgentDocs"
MERGED_FILE = AGENTDOCS_DIR / "AGENT-RULES.md"


@pytest.fixture(scope="module")
def merged_content():
    assert MERGED_FILE.exists(), f"Expected {MERGED_FILE} to exist"
    return MERGED_FILE.read_text(encoding="utf-8")


class TestMergedFileExists:
    def test_merged_file_exists(self):
        """AgentDocs/AGENT-RULES.md must exist in the template."""
        assert MERGED_FILE.exists(), (
            f"AgentDocs/AGENT-RULES.md not found at {MERGED_FILE}"
        )


class TestMergedFileContainsOriginalSections:
    """Verify all 7 sections from the original AGENT-RULES.md are present."""

    def test_contains_allowed_zone(self, merged_content):
        assert "## 1. Allowed Zone" in merged_content

    def test_contains_agentdocs_agent_rules(self, merged_content):
        assert "## 1a. AgentDocs" in merged_content

    def test_contains_denied_zones(self, merged_content):
        assert "## 2. Denied Zones" in merged_content

    def test_contains_tool_permission_matrix(self, merged_content):
        assert "## 3. Tool Permission Matrix" in merged_content

    def test_contains_terminal_rules(self, merged_content):
        assert "## 4. Terminal Rules" in merged_content

    def test_contains_git_rules(self, merged_content):
        assert "## 5. Git Rules" in merged_content

    def test_contains_denial_counter(self, merged_content):
        assert "## 6. Session-Scoped Denial Counter" in merged_content

    def test_contains_known_workarounds(self, merged_content):
        assert "## 7. Known Workarounds" in merged_content


class TestMergedFileContainsAgentDocsContent:
    """Verify AgentDocs philosophy and standard documents table are present."""

    def test_contains_agentdocs_section(self, merged_content):
        assert "AgentDocs — Central Knowledge Base" in merged_content

    def test_contains_philosophy_pillars(self, merged_content):
        assert "Philosophy — 5 Pillars" in merged_content

    def test_contains_pillar_1(self, merged_content):
        assert "AgentDocs is the brain" in merged_content

    def test_contains_pillar_4(self, merged_content):
        assert "Read before you act" in merged_content

    def test_contains_standard_documents_table(self, merged_content):
        assert "Standard Documents" in merged_content
        # Check for key entries in the standard documents table
        assert "architecture.md" in merged_content
        assert "progress.md" in merged_content

    def test_contains_read_first_directive(self, merged_content):
        """Root-level read-first directive must be present."""
        assert "Read this file at the start of every session" in merged_content


class TestPlaceholdersPreserved:
    def test_project_name_placeholder_present(self, merged_content):
        assert "{{PROJECT_NAME}}" in merged_content

    def test_workspace_name_placeholder_present(self, merged_content):
        assert "{{WORKSPACE_NAME}}" in merged_content


class TestDeletedFilesAbsent:
    def test_old_agent_rules_deleted(self):
        """Project/AGENT-RULES.md must NOT exist — it was deleted after merging."""
        old_path = PROJECT_DIR / "AGENT-RULES.md"
        assert not old_path.exists(), (
            f"Project/AGENT-RULES.md still exists at {old_path} — should have been deleted"
        )

    def test_old_project_readme_deleted(self):
        """Project/README.md must NOT exist — it was deleted after merging."""
        old_path = PROJECT_DIR / "README.md"
        assert not old_path.exists(), (
            f"Project/README.md still exists at {old_path} — should have been deleted"
        )

    def test_old_agentdocs_readme_deleted(self):
        """AgentDocs/README.md must NOT exist — it was deleted after merging."""
        old_path = AGENTDOCS_DIR / "README.md"
        assert not old_path.exists(), (
            f"AgentDocs/README.md still exists at {old_path} — should have been deleted"
        )
