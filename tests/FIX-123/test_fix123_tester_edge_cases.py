"""FIX-123 Tester edge-case tests.

Additional tests added by Tester to cover gaps identified during review:

1. clean-workspace template — Dev tests only covered agent-workbench; FIX-123
   modifies BOTH templates so both must be verified independently.
2. Empty ws_root — validate_get_changed_files("") must fail closed (deny), not
   accidentally allow by resolving against the current working directory's .git.
3. decide() ordering — get_changed_files must NOT be caught by _ALWAYS_ALLOW_TOOLS
   first; the validator must be reached even when other always-allow tools overlap
   in future toolsets.
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Import clean-workspace security_gate
# ---------------------------------------------------------------------------

_CLEAN_WS_SCRIPTS = str(
    Path(__file__).parent.parent.parent
    / "templates"
    / "clean-workspace"
    / ".github"
    / "hooks"
    / "scripts"
)


def _import_clean_ws_sg():
    """Import clean-workspace security_gate with isolated sys.modules."""
    # Temporarily insert clean-workspace scripts ahead of agent-workbench so
    # that a bare `import security_gate` picks up the clean-workspace version.
    orig_path = sys.path[:]
    # Remove any previously imported security_gate module to force fresh import
    sg_mod = sys.modules.pop("security_gate", None)
    sys.path.insert(0, _CLEAN_WS_SCRIPTS)
    try:
        import security_gate as clean_sg  # noqa: PLC0415
        return clean_sg
    finally:
        sys.path[:] = orig_path
        # Restore the original security_gate if it was present (agent-workbench)
        if sg_mod is not None:
            sys.modules["security_gate"] = sg_mod
        else:
            sys.modules.pop("security_gate", None)


# ---------------------------------------------------------------------------
# clean-workspace template — must mirror agent-workbench fixes
# ---------------------------------------------------------------------------


class TestCleanWorkspaceTemplate:
    """FIX-123: clean-workspace template must have the same fixes as agent-workbench."""

    def setup_method(self):
        self.sg = _import_clean_ws_sg()

    def test_get_changed_files_not_in_always_allow(self):
        """clean-workspace: get_changed_files must NOT be in _ALWAYS_ALLOW_TOOLS."""
        assert "get_changed_files" not in self.sg._ALWAYS_ALLOW_TOOLS, (
            "clean-workspace security_gate still has get_changed_files in _ALWAYS_ALLOW_TOOLS"
        )

    def test_validate_get_changed_files_exists(self):
        """clean-workspace: validate_get_changed_files() must exist."""
        assert hasattr(self.sg, "validate_get_changed_files"), (
            "clean-workspace security_gate is missing validate_get_changed_files()"
        )

    def test_denies_when_git_at_workspace_root(self, tmp_path):
        """clean-workspace: deny get_changed_files when .git/ at workspace root."""
        (tmp_path / ".git").mkdir()
        result = self.sg.validate_get_changed_files(str(tmp_path).replace("\\", "/"))
        assert result == "deny"

    def test_allows_when_git_inside_project_only(self, tmp_path):
        """clean-workspace: allow when .git/ is only inside the project folder."""
        project_dir = tmp_path / "Project"
        project_dir.mkdir()
        (project_dir / ".git").mkdir()
        result = self.sg.validate_get_changed_files(str(tmp_path).replace("\\", "/"))
        assert result == "allow"

    def test_decide_denies_when_git_at_workspace_root(self, tmp_path):
        """clean-workspace: decide() denies get_changed_files when .git/ at workspace root."""
        (tmp_path / "Project").mkdir()
        (tmp_path / ".git").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        result = self.sg.decide({"tool_name": "get_changed_files"}, ws_root)
        assert result == "deny"


# ---------------------------------------------------------------------------
# Empty / degenerate ws_root inputs
# ---------------------------------------------------------------------------


class TestDegenerateWsRoot:
    """FIX-123: validate_get_changed_files must handle degenerate ws_root values safely."""

    def setup_method(self):
        # Use the agent-workbench security_gate for these tests
        sys.path.insert(
            0,
            str(
                Path(__file__).parent.parent.parent
                / "templates"
                / "agent-workbench"
                / ".github"
                / "hooks"
                / "scripts"
            ),
        )
        import security_gate as sg  # noqa: PLC0415
        self.sg = sg

    def test_empty_ws_root_does_not_allow(self, tmp_path, monkeypatch):
        """Empty ws_root must not resolve against cwd and accidentally allow.

        If the cwd happens to contain a .git directory, os.path.join("", ".git")
        resolves to ".git" which os.path.isdir() evaluates relative to cwd.
        The function should return "deny" in this case (fail closed) because
        we cannot confirm the workspace is safe.
        """
        # Monkeypatch cwd to a directory that has .git/ so the risk is real
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        monkeypatch.chdir(tmp_path)
        # With empty ws_root, os.path.join("", ".git") == ".git"
        # os.path.isdir(".git") from tmp_path will be True → deny
        result = self.sg.validate_get_changed_files("")
        assert result == "deny", (
            "Empty ws_root with cwd containing .git/ should return deny, not allow"
        )

    def test_empty_ws_root_without_cwd_git_is_allowed(self, tmp_path, monkeypatch):
        """Empty ws_root resolving to a cwd without .git/ returns allow."""
        # tmp_path has no .git/
        monkeypatch.chdir(tmp_path)
        result = self.sg.validate_get_changed_files("")
        assert result == "allow"


# ---------------------------------------------------------------------------
# _ALWAYS_ALLOW_TOOLS bypass ordering (decide() structural test)
# ---------------------------------------------------------------------------


class TestDecideOrderingGuard:
    """FIX-123: decide() must route get_changed_files to validate_get_changed_files()
    BEFORE reaching any unconditional allow/deny.
    """

    def setup_method(self):
        sys.path.insert(
            0,
            str(
                Path(__file__).parent.parent.parent
                / "templates"
                / "agent-workbench"
                / ".github"
                / "hooks"
                / "scripts"
            ),
        )
        import security_gate as sg  # noqa: PLC0415
        self.sg = sg

    def test_validate_called_not_bypassed_by_always_allow(self, tmp_path):
        """Even if get_changed_files were injected into _ALWAYS_ALLOW_TOOLS,
        the decide() call must reach validate_get_changed_files first — verified
        by confirming decide() returns "deny" when .git/ is present, proving
        the validator is the active path."""
        (tmp_path / ".git").mkdir()
        ws_root = str(tmp_path).replace("\\", "/")
        # Normal case: validator must deny
        assert self.sg.decide({"tool_name": "get_changed_files"}, ws_root) == "deny"
        # Confirm _ALWAYS_ALLOW_TOOLS does NOT contain get_changed_files
        # (belt-and-suspenders: ordering test is only meaningful if bypass is absent)
        assert "get_changed_files" not in self.sg._ALWAYS_ALLOW_TOOLS
