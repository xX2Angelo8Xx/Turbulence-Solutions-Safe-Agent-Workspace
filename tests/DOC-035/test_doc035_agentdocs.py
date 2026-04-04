"""Tests for DOC-035: AgentDocs folder and integration."""

import os
import pytest

TEMPLATE_ROOT = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "templates", "agent-workbench"
)
AGENT_DOCS = os.path.join(TEMPLATE_ROOT, "Project", "AgentDocs")
AGENT_RULES = os.path.join(TEMPLATE_ROOT, "Project", "AgentDocs", "AGENT-RULES.md")
COPILOT_INSTRUCTIONS = os.path.join(TEMPLATE_ROOT, ".github", "instructions", "copilot-instructions.md")
WORKSPACE_README = os.path.join(TEMPLATE_ROOT, "README.md")


class TestAgentDocsFilesExist:
    def test_agentdocs_folder_exists(self):
        assert os.path.isdir(AGENT_DOCS)

    def test_readme_exists(self):
        assert os.path.isfile(os.path.join(AGENT_DOCS, "README.md"))

    def test_architecture_exists(self):
        assert os.path.isfile(os.path.join(AGENT_DOCS, "architecture.md"))

    def test_decisions_exists(self):
        assert os.path.isfile(os.path.join(AGENT_DOCS, "decisions.md"))

    def test_research_log_exists(self):
        assert os.path.isfile(os.path.join(AGENT_DOCS, "research-log.md"))

    def test_progress_exists(self):
        assert os.path.isfile(os.path.join(AGENT_DOCS, "progress.md"))

    def test_open_questions_exists(self):
        assert os.path.isfile(os.path.join(AGENT_DOCS, "open-questions.md"))


class TestAgentDocsReadmeContent:
    def setup_method(self):
        with open(os.path.join(AGENT_DOCS, "README.md"), encoding="utf-8") as f:
            self.content = f.read()

    def test_has_philosophy_heading(self):
        assert "Philosophy" in self.content

    def test_has_five_pillars(self):
        assert "5 Pillars" in self.content or "5 pillars" in self.content.lower()

    def test_mentions_progress_md(self):
        assert "progress.md" in self.content

    def test_has_standard_documents_table(self):
        assert "architecture.md" in self.content
        assert "decisions.md" in self.content
        assert "research-log.md" in self.content
        assert "open-questions.md" in self.content

    def test_has_rules_section(self):
        assert "Rules" in self.content


class TestAgentRulesUpdated:
    def setup_method(self):
        with open(AGENT_RULES, encoding="utf-8") as f:
            self.content = f.read()

    def test_has_agentdocs_section(self):
        assert "AgentDocs" in self.content

    def test_section_1a_exists(self):
        assert "1a." in self.content

    def test_mentions_progress_at_session_start(self):
        assert "session start" in self.content.lower() or "At session start" in self.content

    def test_mentions_agent_roles(self):
        assert "Planner" in self.content
        assert "Researcher" in self.content
        assert "Coordinator" in self.content

    def test_section_1a_before_section_2(self):
        idx_1a = self.content.find("1a.")
        idx_2 = self.content.find("## 2.")
        assert idx_1a < idx_2, "Section 1a must appear before section 2"


class TestCopilotInstructionsUpdated:
    def setup_method(self):
        with open(COPILOT_INSTRUCTIONS, encoding="utf-8") as f:
            self.content = f.read()

    def test_mentions_agentdocs_folder(self):
        assert "AgentDocs" in self.content

    def test_agentdocs_bullet_present(self):
        assert "shared knowledge base" in self.content

    def test_agentdocs_readme_referenced(self):
        assert "AgentDocs/README.md" in self.content


class TestWorkspaceReadmeUpdated:
    def setup_method(self):
        with open(WORKSPACE_README, encoding="utf-8") as f:
            self.content = f.read()

    def test_agentdocs_row_present(self):
        assert "AgentDocs" in self.content

    def test_agentdocs_described_as_knowledge_base(self):
        assert "knowledge base" in self.content.lower()

    def test_agentdocs_row_after_project_row(self):
        idx_project = self.content.find("{{PROJECT_NAME}}/`")
        idx_agentdocs = self.content.find("AgentDocs")
        assert idx_project < idx_agentdocs, "AgentDocs row must come after the PROJECT_NAME row"
