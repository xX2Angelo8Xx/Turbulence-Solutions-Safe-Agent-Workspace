"""
DOC-052 — Add generate_manifest.py to Mandatory Scripts

Verifies that:
1. agent-workflow.md Mandatory Script Usage table includes a row for generate_manifest.py
   with 'Developer' as who uses it.
2. developer.agent.md Pre-Handoff Checklist contains the generate_manifest.py reminder.
3. scripts/generate_manifest.py exists in the repository.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_WORKFLOW = REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md"
DEVELOPER_AGENT = REPO_ROOT / ".github" / "agents" / "developer.agent.md"
GENERATE_MANIFEST_SCRIPT = REPO_ROOT / "scripts" / "generate_manifest.py"


def _get_mandatory_table_rows(text: str) -> list[str]:
    """Return lines that are table rows inside the Mandatory Script Usage section."""
    in_section = False
    rows = []
    for line in text.splitlines():
        if "## Mandatory Script Usage" in line:
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            if line.startswith("|") and not line.startswith("|-"):
                rows.append(line)
    return rows


class TestAgentWorkflowTable:
    def test_mandatory_script_table_has_generate_manifest_row(self):
        """agent-workflow.md must have a 'generate_manifest.py' row in the mandatory table."""
        text = AGENT_WORKFLOW.read_text(encoding="utf-8")
        rows = _get_mandatory_table_rows(text)
        matching = [r for r in rows if "generate_manifest.py" in r]
        assert matching, (
            "agent-workflow.md Mandatory Script Usage table is missing a row "
            "for 'generate_manifest.py'"
        )

    def test_generate_manifest_row_lists_developer_as_user(self):
        """The generate_manifest.py row must list 'Developer' as the user."""
        text = AGENT_WORKFLOW.read_text(encoding="utf-8")
        rows = _get_mandatory_table_rows(text)
        matching = [r for r in rows if "generate_manifest.py" in r]
        assert matching, "No generate_manifest.py row found in Mandatory Script Usage table"
        row = matching[0]
        assert "Developer" in row, (
            f"generate_manifest.py row does not list 'Developer' as user. Row: {row!r}"
        )

    def test_generate_manifest_row_mentions_template_changes(self):
        """The generate_manifest.py row or surrounding text must reference template files."""
        text = AGENT_WORKFLOW.read_text(encoding="utf-8")
        # The row itself or the surrounding section should mention templates
        assert "generate_manifest.py" in text, (
            "generate_manifest.py not mentioned anywhere in agent-workflow.md"
        )
        # Check the row contains or is near the word 'template' or 'manifest'
        rows = _get_mandatory_table_rows(text)
        matching = [r for r in rows if "generate_manifest.py" in r]
        row = matching[0]
        assert re.search(r"manifest|template|Regenerate", row, re.IGNORECASE), (
            f"generate_manifest.py row does not mention manifest/template context. Row: {row!r}"
        )


class TestDeveloperAgentChecklist:
    def test_developer_agent_checklist_has_generate_manifest_item(self):
        """developer.agent.md Pre-Handoff Checklist must contain a generate_manifest.py item."""
        text = DEVELOPER_AGENT.read_text(encoding="utf-8")
        assert "generate_manifest.py" in text, (
            "developer.agent.md does not mention generate_manifest.py"
        )

    def test_developer_agent_checklist_item_is_conditional(self):
        """The generate_manifest.py checklist item should be conditional (only for template changes)."""
        text = DEVELOPER_AGENT.read_text(encoding="utf-8")
        lines = text.splitlines()
        matching = [l for l in lines if "generate_manifest.py" in l]
        assert matching, "No generate_manifest.py line found in developer.agent.md"
        item_line = matching[0]
        # Must be a checklist item
        assert "- [ ]" in item_line, (
            f"generate_manifest.py line is not a checklist item: {item_line!r}"
        )
        # Must be conditional (starts with "If")
        assert re.search(r"\bIf\b", item_line), (
            f"generate_manifest.py checklist item is not conditional (missing 'If'): {item_line!r}"
        )

    def test_developer_agent_checklist_item_references_templates_dir(self):
        """The checklist item must reference templates/agent-workbench/ directory."""
        text = DEVELOPER_AGENT.read_text(encoding="utf-8")
        lines = text.splitlines()
        matching = [l for l in lines if "generate_manifest.py" in l]
        assert matching, "No generate_manifest.py line found in developer.agent.md"
        item_line = matching[0]
        assert "templates/agent-workbench/" in item_line, (
            f"Checklist item does not reference templates/agent-workbench/: {item_line!r}"
        )

    def test_developer_agent_checklist_item_references_manifest_json(self):
        """The checklist item must mention MANIFEST.json as the output."""
        text = DEVELOPER_AGENT.read_text(encoding="utf-8")
        lines = text.splitlines()
        matching = [l for l in lines if "generate_manifest.py" in l]
        assert matching, "No generate_manifest.py line found in developer.agent.md"
        item_line = matching[0]
        assert "MANIFEST.json" in item_line, (
            f"Checklist item does not mention MANIFEST.json: {item_line!r}"
        )


class TestScriptExists:
    def test_generate_manifest_script_exists(self):
        """scripts/generate_manifest.py must exist in the repository."""
        assert GENERATE_MANIFEST_SCRIPT.exists(), (
            f"scripts/generate_manifest.py not found at {GENERATE_MANIFEST_SCRIPT}"
        )

    def test_generate_manifest_script_is_a_file(self):
        """scripts/generate_manifest.py must be a regular file (not a directory)."""
        assert GENERATE_MANIFEST_SCRIPT.is_file(), (
            f"scripts/generate_manifest.py is not a file: {GENERATE_MANIFEST_SCRIPT}"
        )
