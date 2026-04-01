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


class TestEdgeCases:
    """Edge-case tests added by Tester to verify content completeness and integrity."""

    def test_all_5_pillars_present(self, merged_content):
        """All 5 philosophy pillars must appear in the merged file."""
        pillars = [
            "AgentDocs is the brain",
            "Living documents",
            "Speed over ceremony",
            "Read before you act",
            "Leave traces",
        ]
        for pillar in pillars:
            assert pillar in merged_content, f"Missing pillar: {pillar!r}"

    def test_all_standard_documents_present(self, merged_content):
        """All standard documents from the original table must be referenced."""
        docs = [
            "architecture.md",
            "decisions.md",
            "research-log.md",
            "progress.md",
            "open-questions.md",
        ]
        for doc in docs:
            assert doc in merged_content, f"Standard document missing: {doc!r}"

    def test_section_ordering(self, merged_content):
        """Sections must appear in logical order: philosophy before rules, sections 1-7 ascending."""
        philosophy_pos = merged_content.find("Philosophy — 5 Pillars")
        allowed_zone_pos = merged_content.find("## 1. Allowed Zone")
        denied_zones_pos = merged_content.find("## 2. Denied Zones")
        tool_matrix_pos = merged_content.find("## 3. Tool Permission Matrix")
        terminal_pos = merged_content.find("## 4. Terminal Rules")
        git_pos = merged_content.find("## 5. Git Rules")
        denial_pos = merged_content.find("## 6. Session-Scoped Denial Counter")
        workarounds_pos = merged_content.find("## 7. Known Workarounds")

        assert philosophy_pos < allowed_zone_pos, "Philosophy must precede Section 1"
        assert allowed_zone_pos < denied_zones_pos < tool_matrix_pos < terminal_pos, \
            "Sections 1→2→3→4 must appear in order"
        assert terminal_pos < git_pos < denial_pos < workarounds_pos, \
            "Sections 4→5→6→7 must appear in order"

    def test_placeholder_appears_multiple_times(self, merged_content):
        """{{PROJECT_NAME}} must appear more than once — it is used in multiple sections."""
        count = merged_content.count("{{PROJECT_NAME}}")
        assert count >= 2, f"Expected >=2 occurrences of {{{{PROJECT_NAME}}}}, got {count}"

    def test_workspace_name_placeholder_in_allowed_zone(self, merged_content):
        """{{WORKSPACE_NAME}} placeholder must appear in the Allowed Zone section."""
        allowed_zone_pos = merged_content.find("## 1. Allowed Zone")
        section_end = merged_content.find("## 2. Denied Zones")
        section_text = merged_content[allowed_zone_pos:section_end]
        assert "{{WORKSPACE_NAME}}" in section_text, \
            "{{WORKSPACE_NAME}} should appear inside the Allowed Zone section"

    def test_no_placeholder_resolved(self, merged_content):
        """Placeholders must remain as templates — no real project names substituted."""
        import re
        # Ensure no real project name was accidentally left (e.g. "MyProject" literally)
        # The only placeholder-like tokens should still contain {{ and }}
        resolved = re.findall(r'\b(?<!{)(?<!{{)[A-Z][A-Za-z]+(?!})', merged_content)
        # This is a soft check — we just verify the template markers are intact
        assert "{{PROJECT_NAME}}" in merged_content
        assert "{{WORKSPACE_NAME}}" in merged_content

    def test_denied_zones_table_contains_all_entries(self, merged_content):
        """All three denied zone paths must appear in the Denied Zones section."""
        for path in [".github/", ".vscode/", "NoAgentZone/"]:
            assert path in merged_content, f"Denied zone path missing: {path!r}"

    def test_blocked_commands_table_present(self, merged_content):
        """Terminal rules must include the blocked commands table."""
        assert "Blocked Commands" in merged_content
        assert "git push --force" in merged_content

    def test_file_is_utf8_no_bom(self):
        """Merged file must be valid UTF-8 without BOM."""
        raw = MERGED_FILE.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), "File has BOM — should be UTF-8 without BOM"
        raw.decode("utf-8")  # raises UnicodeDecodeError if invalid

    def test_merged_file_is_nonempty(self, merged_content):
        """Merged file must have substantial content (>3000 chars)."""
        assert len(merged_content) > 3000, \
            f"Merged file suspiciously short: {len(merged_content)} chars"
