"""SAF-058 — Tests for get_changed_files conditional .git/ placement check.

Covers:
- get_changed_files with .git/ at workspace root → denied
- get_changed_files with .git/ inside project folder → allowed
- get_changed_files with no .git/ anywhere → allowed
- get_changed_files is NOT in _ALWAYS_ALLOW_TOOLS
- OSError during .git/ check → denied (fail-closed)
- decide() routes get_changed_files to validate_get_changed_files()
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure the scripts directory is importable
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"),
)

import security_gate as sg
import zone_classifier as zc


# ---------------------------------------------------------------------------
# _ALWAYS_ALLOW_TOOLS membership check
# ---------------------------------------------------------------------------

class TestAlwaysAllowToolsMembership:
    def test_get_changed_files_not_in_always_allow(self):
        """SAF-058: get_changed_files must NOT be in _ALWAYS_ALLOW_TOOLS."""
        assert "get_changed_files" not in sg._ALWAYS_ALLOW_TOOLS


# ---------------------------------------------------------------------------
# validate_get_changed_files() — direct function tests
# ---------------------------------------------------------------------------

class TestValidateGetChangedFiles:
    def test_git_at_workspace_root_is_denied(self, tmp_path):
        """When .git/ exists at workspace root, deny (exposes denied-zone files)."""
        project_dir = tmp_path / "Project"
        project_dir.mkdir()
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        result = sg.validate_get_changed_files(ws_root)
        assert result == "deny"

    def test_git_inside_project_folder_is_allowed(self, tmp_path):
        """When .git/ exists inside project folder (not at workspace root), allow."""
        project_dir = tmp_path / "Project"
        project_dir.mkdir()
        git_dir = project_dir / ".git"
        git_dir.mkdir()
        # No .git/ at workspace root
        ws_root = str(tmp_path).replace("\\", "/")
        result = sg.validate_get_changed_files(ws_root)
        assert result == "allow"

    def test_no_git_anywhere_is_allowed(self, tmp_path):
        """When no .git/ exists anywhere, allow (tool gives harmless 'no repo' message)."""
        project_dir = tmp_path / "Project"
        project_dir.mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        result = sg.validate_get_changed_files(ws_root)
        assert result == "allow"

    def test_no_project_folder_no_git_is_allowed(self, tmp_path):
        """When no project folder exists and no .git/ exists, allow."""
        # tmp_path is empty — no subdirectories at all
        ws_root = str(tmp_path).replace("\\", "/")
        result = sg.validate_get_changed_files(ws_root)
        assert result == "allow"

    def test_os_error_fails_closed(self):
        """On OSError when checking for .git/, fail closed → deny."""
        with patch("os.path.isdir", side_effect=OSError("permission denied")):
            result = sg.validate_get_changed_files("/some/workspace")
        assert result == "deny"

    def test_git_at_root_takes_priority_over_project_git(self, tmp_path):
        """When .git/ exists at workspace root AND inside project folder, deny (root takes priority)."""
        project_dir = tmp_path / "Project"
        project_dir.mkdir()
        (project_dir / ".git").mkdir()
        (tmp_path / ".git").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        result = sg.validate_get_changed_files(ws_root)
        assert result == "deny"


# ---------------------------------------------------------------------------
# decide() routing — integration tests via decide()
# ---------------------------------------------------------------------------

class TestDecideRoutesGetChangedFiles:
    def _make_payload(self) -> dict:
        return {"tool_name": "get_changed_files"}

    def test_decide_denies_when_git_at_workspace_root(self, tmp_path):
        """decide() denies get_changed_files when .git/ is at workspace root."""
        project_dir = tmp_path / "Project"
        project_dir.mkdir()
        (tmp_path / ".git").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        result = sg.decide(self._make_payload(), ws_root)
        assert result == "deny"

    def test_decide_allows_when_git_inside_project(self, tmp_path):
        """decide() allows get_changed_files when .git/ is inside the project folder."""
        project_dir = tmp_path / "Project"
        project_dir.mkdir()
        (project_dir / ".git").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        result = sg.decide(self._make_payload(), ws_root)
        assert result == "allow"

    def test_decide_allows_when_no_git(self, tmp_path):
        """decide() allows get_changed_files when no .git/ exists."""
        project_dir = tmp_path / "Project"
        project_dir.mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        result = sg.decide(self._make_payload(), ws_root)
        assert result == "allow"
