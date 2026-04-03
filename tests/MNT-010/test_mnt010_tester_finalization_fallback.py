"""
MNT-010: Tester Finalization Fallback

Verifies that tester.agent.md contains a 'Post-Done Finalization (No Orchestrator)'
section with all required elements to close gap C-06.
"""

import pathlib
import re

TESTER_AGENT_PATH = pathlib.Path(__file__).parents[2] / ".github" / "agents" / "tester.agent.md"


def _read_tester_agent() -> str:
    return TESTER_AGENT_PATH.read_text(encoding="utf-8")


class TestPostDoneFinalizationSectionExists:
    def test_section_heading_present(self):
        """Section heading must exist with exact expected title."""
        content = _read_tester_agent()
        assert "## Post-Done Finalization (No Orchestrator)" in content

    def test_section_appears_after_pre_done_checklist(self):
        """The new section must appear after the Pre-Done Checklist section."""
        content = _read_tester_agent()
        pre_done_pos = content.find("## Pre-Done Checklist")
        finalization_pos = content.find("## Post-Done Finalization (No Orchestrator)")
        assert pre_done_pos != -1, "Pre-Done Checklist section not found"
        assert finalization_pos != -1, "Post-Done Finalization section not found"
        assert finalization_pos > pre_done_pos, (
            "Post-Done Finalization section must appear after Pre-Done Checklist"
        )

    def test_section_appears_before_constraints(self):
        """The new section must appear before the Constraints section."""
        content = _read_tester_agent()
        finalization_pos = content.find("## Post-Done Finalization (No Orchestrator)")
        constraints_pos = content.find("## Constraints")
        assert finalization_pos != -1, "Post-Done Finalization section not found"
        assert constraints_pos != -1, "Constraints section not found"
        assert finalization_pos < constraints_pos, (
            "Post-Done Finalization section must appear before Constraints"
        )


class TestPostDoneFinalizationCommand:
    def test_finalize_wp_command_present(self):
        """The exact finalize_wp.py command must be present."""
        content = _read_tester_agent()
        assert "finalize_wp.py" in content, "finalize_wp.py command not found in tester.agent.md"

    def test_finalize_command_uses_venv(self):
        """The command must use the workspace .venv Python."""
        content = _read_tester_agent()
        assert ".venv\\Scripts\\python scripts/finalize_wp.py" in content

    def test_dry_run_option_mentioned(self):
        """The --dry-run option should be documented."""
        content = _read_tester_agent()
        assert "--dry-run" in content


class TestPostDoneFinalizationReference:
    def test_references_agent_workflow(self):
        """Section must reference agent-workflow.md."""
        content = _read_tester_agent()
        assert "agent-workflow.md" in content

    def test_references_post_done_finalization_in_workflow(self):
        """Section must reference the Post-Done Finalization clause in agent-workflow.md."""
        content = _read_tester_agent()
        assert "Post-Done Finalization" in content

    def test_quotes_or_references_orchestrator_clause(self):
        """Section must reference the 'Orchestrator (or the Tester if no Orchestrator is active)' clause."""
        content = _read_tester_agent()
        assert "no Orchestrator is active" in content


class TestOrchestratorResponsibilityNote:
    def test_orchestrator_responsibility_noted(self):
        """Section must note that when Orchestrator IS active, it owns finalization."""
        content = _read_tester_agent()
        assert "Orchestrator's responsibility" in content or "Orchestrator IS active" in content

    def test_no_orchestrator_flow_described(self):
        """Section must describe the direct User→Developer→Tester flow."""
        content = _read_tester_agent()
        # Check for either the arrow notation or a description of the flow
        has_flow = (
            "User→Developer→Tester" in content
            or "User->Developer->Tester" in content
            or "direct" in content
        )
        assert has_flow, "No-Orchestrator flow must be described in the section"


class TestExistingSectionsPreserved:
    def test_pre_done_checklist_intact(self):
        """The Pre-Done Checklist must still be present and complete."""
        content = _read_tester_agent()
        assert "## Pre-Done Checklist" in content
        assert "dev-log.md" in content
        assert "test-report.md" in content
        assert "validate_workspace.py" in content

    def test_constraints_section_intact(self):
        """The Constraints section must still be present."""
        content = _read_tester_agent()
        assert "## Constraints" in content
        assert "DO NOT" in content

    def test_edit_permissions_section_intact(self):
        """The Edit Permissions section must still be present."""
        content = _read_tester_agent()
        assert "## Edit Permissions" in content

    def test_workflow_section_intact(self):
        """The Workflow section must still be present."""
        content = _read_tester_agent()
        assert "## Workflow" in content

    def test_add_bug_mandate_preserved(self):
        """The add_bug.py mandate from MNT-009 must still be present."""
        content = _read_tester_agent()
        assert "add_bug.py" in content

    def test_escalation_handoff_preserved(self):
        """The escalation handoff from MNT-008 must still be present."""
        content = _read_tester_agent()
        assert "orchestrator" in content.lower()
