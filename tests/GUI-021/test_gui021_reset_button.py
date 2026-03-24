"""Tests for GUI-021 — Reset Agent Blocks button in SettingsDialog.

Covers:
1. reset_agent_blocks_button attribute exists on SettingsDialog after _build_ui
2. workspace_entry attribute exists on SettingsDialog after _build_ui
3. browse_workspace_button attribute exists on SettingsDialog after _build_ui
4. _browse_workspace populates workspace_entry when a folder is chosen
5. _browse_workspace is a no-op when the folder dialog is cancelled
6. _on_reset_agent_blocks shows error when no workspace is entered
7. _on_reset_agent_blocks shows error when workspace is only whitespace
8. _on_reset_agent_blocks shows error when workspace path is not a directory
9. _on_reset_agent_blocks resets state file and shows confirmation message
10. _on_reset_agent_blocks correctly clears session entries from the state file
11. _on_reset_agent_blocks handles a missing state file gracefully (shows confirmation)
12. _on_reset_agent_blocks shows error dialog on OSError during reset
13. _reset_hook_state returns (0, message) when file is missing
14. _reset_hook_state resets all session entries and returns correct count
15. _reset_hook_state handles corrupt state file (replaces with empty state)
16. _reset_hook_state does not remove non-session keys
17. _atomic_write_hook_state writes valid JSON
18. _atomic_write_hook_state leaves no leftover temp files
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_CTK_MOCK = sys.modules["customtkinter"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_settings_dialog() -> "SettingsDialog":  # noqa: F821
    """Return a fresh SettingsDialog instance with all widgets mocked."""
    from launcher.gui.app import SettingsDialog
    _CTK_MOCK.reset_mock()
    return SettingsDialog(MagicMock())


# ---------------------------------------------------------------------------
# Tests: attribute existence
# ---------------------------------------------------------------------------

class TestResetButtonAttributesExist:
    def test_reset_agent_blocks_button_exists(self) -> None:
        dialog = _make_settings_dialog()
        assert hasattr(dialog, "reset_agent_blocks_button"), (
            "SettingsDialog is missing 'reset_agent_blocks_button'"
        )

    def test_workspace_entry_exists(self) -> None:
        dialog = _make_settings_dialog()
        assert hasattr(dialog, "workspace_entry"), "SettingsDialog is missing 'workspace_entry'"

    def test_browse_workspace_button_exists(self) -> None:
        dialog = _make_settings_dialog()
        assert hasattr(dialog, "browse_workspace_button"), (
            "SettingsDialog is missing 'browse_workspace_button'"
        )


# ---------------------------------------------------------------------------
# Tests: _browse_workspace
# ---------------------------------------------------------------------------

class TestBrowseWorkspace:
    def test_browse_workspace_populates_entry(self) -> None:
        """_browse_workspace inserts the chosen folder into workspace_entry."""
        import tkinter.filedialog as fd
        dialog = _make_settings_dialog()
        # Reset the workspace_entry mock so call history starts clean.
        dialog.workspace_entry.reset_mock()
        with patch.object(fd, "askdirectory", return_value="/some/workspace"):
            dialog._browse_workspace()
        dialog.workspace_entry.delete.assert_called_once_with(0, "end")
        dialog.workspace_entry.insert.assert_called_once_with(0, "/some/workspace")

    def test_browse_workspace_no_op_on_cancel(self) -> None:
        """If the user cancels the dialog, workspace_entry is not modified."""
        import tkinter.filedialog as fd
        dialog = _make_settings_dialog()
        dialog.workspace_entry.reset_mock()
        with patch.object(fd, "askdirectory", return_value=""):
            dialog._browse_workspace()
        dialog.workspace_entry.delete.assert_not_called()
        dialog.workspace_entry.insert.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: _on_reset_agent_blocks — no workspace
# ---------------------------------------------------------------------------

class TestResetNoWorkspace:
    def test_shows_error_when_no_workspace_entered(self) -> None:
        """Clicking Reset with empty workspace_entry shows an error dialog."""
        import tkinter.messagebox as mb
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = ""
        with patch.object(mb, "showerror") as mock_err:
            dialog._on_reset_agent_blocks()
        mock_err.assert_called_once()
        title = mock_err.call_args[0][0]
        assert "No Workspace Selected" in title or "workspace" in title.lower()

    def test_shows_error_when_workspace_is_whitespace(self) -> None:
        """Clicking Reset with only spaces in workspace_entry shows an error."""
        import tkinter.messagebox as mb
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = "   "
        with patch.object(mb, "showerror") as mock_err:
            dialog._on_reset_agent_blocks()
        mock_err.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: _on_reset_agent_blocks — invalid workspace path
# ---------------------------------------------------------------------------

class TestResetInvalidWorkspace:
    def test_shows_error_when_path_is_not_a_directory(self) -> None:
        """An error is shown when the workspace path does not exist."""
        import tkinter.messagebox as mb
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = "/nonexistent/path/xyz"
        with patch.object(mb, "showerror") as mock_err:
            dialog._on_reset_agent_blocks()
        mock_err.assert_called_once()
        title = mock_err.call_args[0][0]
        assert "Invalid" in title or "workspace" in title.lower()


# ---------------------------------------------------------------------------
# Tests: _on_reset_agent_blocks — successful reset
# ---------------------------------------------------------------------------

class TestResetSuccess:
    def test_shows_confirmation_on_successful_reset(self, tmp_path: Path) -> None:
        """After a successful reset, a confirmation dialog is shown."""
        import tkinter.messagebox as mb
        scripts_dir = tmp_path / ".github" / "hooks" / "scripts"
        scripts_dir.mkdir(parents=True)
        state_file = scripts_dir / ".hook_state.json"
        state_file.write_text(
            json.dumps({"session-1": {"deny_count": 5, "blocked": True}}),
            encoding="utf-8",
        )
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)
        with patch.object(mb, "showinfo") as mock_info, \
             patch.object(mb, "showerror") as mock_err:
            dialog._on_reset_agent_blocks()
        mock_err.assert_not_called()
        mock_info.assert_called_once()
        msg = mock_info.call_args[0][1]
        assert "All session counters have been reset" in msg

    def test_state_file_is_empty_after_reset(self, tmp_path: Path) -> None:
        """After reset, the state file contains no session entries."""
        scripts_dir = tmp_path / ".github" / "hooks" / "scripts"
        scripts_dir.mkdir(parents=True)
        state_file = scripts_dir / ".hook_state.json"
        state_file.write_text(
            json.dumps({
                "session-1": {"deny_count": 3, "blocked": False},
                "session-2": {"deny_count": 21, "blocked": True},
            }),
            encoding="utf-8",
        )
        import tkinter.messagebox as mb
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)
        with patch.object(mb, "showinfo"), patch.object(mb, "showerror"):
            dialog._on_reset_agent_blocks()
        remaining = json.loads(state_file.read_text(encoding="utf-8"))
        assert not any(
            isinstance(v, dict) and "deny_count" in v for v in remaining.values()
        ), "Session entries should be cleared after reset"

    def test_handles_missing_state_file(self, tmp_path: Path) -> None:
        """If the state file doesn't exist, confirmation is still shown (nothing to reset)."""
        import tkinter.messagebox as mb
        (tmp_path / ".github" / "hooks" / "scripts").mkdir(parents=True)
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)
        with patch.object(mb, "showinfo") as mock_info, \
             patch.object(mb, "showerror") as mock_err:
            dialog._on_reset_agent_blocks()
        mock_err.assert_not_called()
        mock_info.assert_called_once()

    def test_handles_oserror_during_reset(self, tmp_path: Path) -> None:
        """An OS error during reset is caught and shown as an error dialog."""
        import tkinter.messagebox as mb
        from launcher.gui import app as app_module
        scripts_dir = tmp_path / ".github" / "hooks" / "scripts"
        scripts_dir.mkdir(parents=True)
        state_file = scripts_dir / ".hook_state.json"
        state_file.write_text(json.dumps({"s": {"deny_count": 1}}), encoding="utf-8")
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)
        with patch.object(app_module, "_reset_hook_state", side_effect=OSError("locked")):
            with patch.object(mb, "showerror") as mock_err, \
                 patch.object(mb, "showinfo") as mock_info:
                dialog._on_reset_agent_blocks()
        mock_info.assert_not_called()
        mock_err.assert_called_once()
        assert "Reset Failed" in mock_err.call_args[0][0]


# ---------------------------------------------------------------------------
# Tests: module-level _reset_hook_state
# ---------------------------------------------------------------------------

class TestResetHookState:
    def test_returns_zero_when_file_missing(self, tmp_path: Path) -> None:
        from launcher.gui.app import _reset_hook_state
        count, msg = _reset_hook_state(tmp_path / "missing.json")
        assert count == 0
        assert "No state file" in msg or "Nothing to reset" in msg

    def test_resets_all_session_entries_and_returns_count(self, tmp_path: Path) -> None:
        from launcher.gui.app import _reset_hook_state
        state_file = tmp_path / ".hook_state.json"
        state_file.write_text(
            json.dumps({
                "sess-a": {"deny_count": 2, "blocked": False},
                "sess-b": {"deny_count": 10, "blocked": True},
            }),
            encoding="utf-8",
        )
        count, msg = _reset_hook_state(state_file)
        assert count == 2
        remaining = json.loads(state_file.read_text(encoding="utf-8"))
        assert remaining == {}

    def test_handles_corrupt_state_file(self, tmp_path: Path) -> None:
        from launcher.gui.app import _reset_hook_state
        state_file = tmp_path / ".hook_state.json"
        state_file.write_text("{not valid json", encoding="utf-8")
        count, msg = _reset_hook_state(state_file)
        assert count == 0
        assert "corrupt" in msg.lower() or "Warning" in msg
        restored = json.loads(state_file.read_text(encoding="utf-8"))
        assert restored == {}

    def test_does_not_remove_non_session_keys(self, tmp_path: Path) -> None:
        from launcher.gui.app import _reset_hook_state
        state_file = tmp_path / ".hook_state.json"
        state_file.write_text(
            json.dumps({
                "session-1": {"deny_count": 5, "blocked": True},
                "metadata": {"version": 1},
            }),
            encoding="utf-8",
        )
        count, _msg = _reset_hook_state(state_file)
        assert count == 1
        remaining = json.loads(state_file.read_text(encoding="utf-8"))
        assert "metadata" in remaining
        assert "session-1" not in remaining


# ---------------------------------------------------------------------------
# Tests: _atomic_write_hook_state
# ---------------------------------------------------------------------------

class TestAtomicWriteHookState:
    def test_writes_valid_json(self, tmp_path: Path) -> None:
        from launcher.gui.app import _atomic_write_hook_state
        dest = tmp_path / "state.json"
        _atomic_write_hook_state(dest, {"key": "value"})
        data = json.loads(dest.read_text(encoding="utf-8"))
        assert data == {"key": "value"}

    def test_no_leftover_tmp_file(self, tmp_path: Path) -> None:
        from launcher.gui.app import _atomic_write_hook_state
        dest = tmp_path / "state.json"
        _atomic_write_hook_state(dest, {})
        tmp_files = list(tmp_path.glob(".hook_state_*.tmp"))
        assert tmp_files == [], "Temp file should be removed after atomic write"
