"""FIX-123 — Tests verifying get_changed_files zone bypass is fixed.

FIX-117 added get_changed_files to _ALWAYS_ALLOW_TOOLS, claiming the tool
returns only file metadata. In reality it returns full diff content from ALL
zones including denied ones (BUG-208 / BUG-136 regression). FIX-123 reverts
this by removing the tool from _ALWAYS_ALLOW_TOOLS and routing it through
validate_get_changed_files() which denies when .git/ exists at workspace root.

Covers:
- get_changed_files is NOT in _ALWAYS_ALLOW_TOOLS (bypass removed)
- validate_get_changed_files() exists and is callable
- validate_get_changed_files() denies when .git/ is at workspace root
- validate_get_changed_files() allows when .git/ is inside project folder
- validate_get_changed_files() allows when no .git/ exists
- decide() routes get_changed_files to validate_get_changed_files()
- AGENT-RULES.md documents get_changed_files as Zone-checked
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
# _ALWAYS_ALLOW_TOOLS membership removed
# ---------------------------------------------------------------------------

class TestAlwaysAllowToolsMembership:
    def test_get_changed_files_not_in_always_allow(self):
        """FIX-123: get_changed_files must NOT be in _ALWAYS_ALLOW_TOOLS."""
        assert "get_changed_files" not in sg._ALWAYS_ALLOW_TOOLS, (
            "get_changed_files must not bypass zone checks via _ALWAYS_ALLOW_TOOLS"
        )

    def test_validate_get_changed_files_exists(self):
        """FIX-123: validate_get_changed_files() function must exist."""
        assert hasattr(sg, "validate_get_changed_files"), (
            "validate_get_changed_files() is required for zone-aware routing"
        )


# ---------------------------------------------------------------------------
# validate_get_changed_files() — direct unit tests
# ---------------------------------------------------------------------------

class TestValidateGetChangedFiles:
    def test_git_dir_at_workspace_root_is_denied(self, tmp_path):
        """deny when .git/ directory is at workspace root (BUG-208 fix)."""
        project_dir = tmp_path / "Project"
        project_dir.mkdir()
        (tmp_path / ".git").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        assert sg.validate_get_changed_files(ws_root) == "deny"

    def test_git_inside_project_folder_is_allowed(self, tmp_path):
        """allow when .git/ is inside the project folder (no workspace root exposure)."""
        project_dir = tmp_path / "Project"
        project_dir.mkdir()
        (project_dir / ".git").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        assert sg.validate_get_changed_files(ws_root) == "allow"

    def test_no_git_is_allowed(self, tmp_path):
        """allow when no .git/ exists (tool returns harmless 'no repo' message)."""
        (tmp_path / "Project").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        assert sg.validate_get_changed_files(ws_root) == "allow"


# ---------------------------------------------------------------------------
# decide() routing — integration tests
# ---------------------------------------------------------------------------

class TestDecideRoutesGetChangedFiles:
    def _payload(self) -> dict:
        return {"tool_name": "get_changed_files"}

    def test_decide_denies_when_git_at_workspace_root(self, tmp_path):
        """decide() denies get_changed_files when .git/ is at workspace root."""
        (tmp_path / "Project").mkdir()
        (tmp_path / ".git").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        assert sg.decide(self._payload(), ws_root) == "deny"

    def test_decide_allows_when_git_inside_project(self, tmp_path):
        """decide() allows get_changed_files when .git/ is inside the project folder."""
        project_dir = tmp_path / "Project"
        project_dir.mkdir()
        (project_dir / ".git").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        assert sg.decide(self._payload(), ws_root) == "allow"

    def test_decide_allows_when_no_git(self, tmp_path):
        """decide() allows get_changed_files when no .git/ exists."""
        (tmp_path / "Project").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        assert sg.decide(self._payload(), ws_root) == "allow"


# ---------------------------------------------------------------------------
# AGENT-RULES.md documentation
# ---------------------------------------------------------------------------

class TestAgentRulesDocumentation:
    def _agent_rules_path(self) -> Path:
        return (
            Path(__file__).parent.parent.parent
            / "templates"
            / "agent-workbench"
            / "Project"
            / "AgentDocs"
            / "AGENT-RULES.md"
        )

    def test_agent_rules_documents_get_changed_files(self):
        """FIX-123: AGENT-RULES.md must document get_changed_files."""
        content = self._agent_rules_path().read_text(encoding="utf-8")
        assert "get_changed_files" in content

    def test_agent_rules_marks_get_changed_files_as_zone_checked(self):
        """FIX-123: AGENT-RULES.md must mark get_changed_files as Zone-checked."""
        content = self._agent_rules_path().read_text(encoding="utf-8")
        for line in content.splitlines():
            if "get_changed_files" in line:
                assert "Zone-checked" in line, (
                    f"Expected 'Zone-checked' in get_changed_files row, got: {line!r}"
                )
                return
        pytest.fail("get_changed_files row not found in AGENT-RULES.md")
