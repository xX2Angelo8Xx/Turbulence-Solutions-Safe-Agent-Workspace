"""FIX-117 — Tests verifying get_changed_files is unconditionally allowed.

Covers:
- get_changed_files is in _ALWAYS_ALLOW_TOOLS (unconditional allow)
- decide() returns 'allow' for get_changed_files regardless of .git/ placement
- validate_get_changed_files() function was removed (SAF-058 conditional logic gone)
- AGENT-RULES.md documents get_changed_files as Allowed
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"),
)

import security_gate as sg


# ---------------------------------------------------------------------------
# _ALWAYS_ALLOW_TOOLS membership
# ---------------------------------------------------------------------------

class TestAlwaysAllowToolsMembership:
    def test_get_changed_files_is_in_always_allow(self):
        """FIX-117: get_changed_files must be in _ALWAYS_ALLOW_TOOLS."""
        assert "get_changed_files" in sg._ALWAYS_ALLOW_TOOLS

    def test_validate_get_changed_files_removed(self):
        """FIX-117: validate_get_changed_files() function must not exist (dead code removed)."""
        assert not hasattr(sg, "validate_get_changed_files"), (
            "validate_get_changed_files() was removed in FIX-117; "
            "it should no longer be present in security_gate"
        )


# ---------------------------------------------------------------------------
# decide() — unconditional allow regardless of .git/ placement
# ---------------------------------------------------------------------------

class TestDecideGetChangedFiles:
    def _payload(self) -> dict:
        return {"tool_name": "get_changed_files"}

    def test_allowed_when_git_at_workspace_root(self, tmp_path):
        """FIX-117: decide() allows get_changed_files even when .git/ is at workspace root."""
        (tmp_path / "Project").mkdir()
        (tmp_path / ".git").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        result = sg.decide(self._payload(), ws_root)
        assert result == "allow"

    def test_allowed_when_git_inside_project(self, tmp_path):
        """decide() allows get_changed_files when .git/ is inside project folder."""
        project = tmp_path / "Project"
        project.mkdir()
        (project / ".git").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        result = sg.decide(self._payload(), ws_root)
        assert result == "allow"

    def test_allowed_when_no_git_dir(self, tmp_path):
        """decide() allows get_changed_files when no .git/ exists anywhere."""
        (tmp_path / "Project").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        result = sg.decide(self._payload(), ws_root)
        assert result == "allow"

    def test_allowed_with_empty_workspace(self, tmp_path):
        """decide() allows get_changed_files even with an empty workspace."""
        ws_root = str(tmp_path).replace("\\", "/")
        result = sg.decide(self._payload(), ws_root)
        assert result == "allow"

    def test_allowed_with_both_git_dirs(self, tmp_path):
        """decide() allows get_changed_files when .git/ exists at root AND inside project."""
        project = tmp_path / "Project"
        project.mkdir()
        (project / ".git").mkdir()
        (tmp_path / ".git").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        result = sg.decide(self._payload(), ws_root)
        assert result == "allow"


# ---------------------------------------------------------------------------
# AGENT-RULES.md documentation check
# ---------------------------------------------------------------------------

class TestAgentRulesDocumentation:
    def _agent_rules_path(self) -> Path:
        return (
            Path(__file__).parent.parent.parent
            / "templates"
            / "agent-workbench"
            / "Project"
            / "AGENT-RULES.md"
        )

    def test_agent_rules_documents_get_changed_files(self):
        """FIX-117: AGENT-RULES.md Tool Permission Matrix must document get_changed_files."""
        content = self._agent_rules_path().read_text(encoding="utf-8")
        assert "get_changed_files" in content, (
            "AGENT-RULES.md must document get_changed_files in the Tool Permission Matrix"
        )

    def test_agent_rules_marks_get_changed_files_as_allowed(self):
        """FIX-117: AGENT-RULES.md entry for get_changed_files must say 'Allowed'."""
        content = self._agent_rules_path().read_text(encoding="utf-8")
        # Find the line with get_changed_files and check it contains "Allowed"
        for line in content.splitlines():
            if "get_changed_files" in line:
                assert "Allowed" in line, (
                    f"Expected 'Allowed' in get_changed_files row, got: {line!r}"
                )
                return
        pytest.fail("get_changed_files row not found in AGENT-RULES.md")
