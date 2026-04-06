"""Tests for GUI-036 — Uninstall Application button in SettingsDialog.

Covers:
1.  _uninstall_button attribute exists after _build_ui
2.  _find_uninstaller returns None on non-Windows platform
3.  _find_uninstaller returns path when unins000.exe exists (Windows)
4.  _find_uninstaller returns None when unins000.exe is absent (Windows)
5.  _on_uninstall shows confirmation dialog on Windows with uninstaller present
6.  _on_uninstall does nothing when user cancels confirmation
7.  _on_uninstall runs subprocess.Popen then sys.exit(0) on Windows confirm
8.  _on_uninstall shows error when uninstaller vanishes between check and click
9.  _on_uninstall shows instructions dialog on non-Windows
10. Button state is "disabled" when _find_uninstaller returns None
11. Button state is "normal" when _find_uninstaller returns a path
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

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

class TestUninstallButtonAttributeExists:
    def test_uninstall_button_exists(self) -> None:
        """SettingsDialog must expose _uninstall_button after _build_ui."""
        dialog = _make_settings_dialog()
        assert hasattr(dialog, "_uninstall_button"), (
            "SettingsDialog is missing '_uninstall_button'"
        )


# ---------------------------------------------------------------------------
# Tests: _find_uninstaller
# ---------------------------------------------------------------------------

class TestFindUninstaller:
    def test_returns_none_on_non_windows(self) -> None:
        """_find_uninstaller returns None on non-Windows platforms."""
        dialog = _make_settings_dialog()
        with patch.object(sys, "platform", "linux"):
            result = dialog._find_uninstaller()
        assert result is None

    def test_returns_none_on_macos(self) -> None:
        """_find_uninstaller returns None on macOS."""
        dialog = _make_settings_dialog()
        with patch.object(sys, "platform", "darwin"):
            result = dialog._find_uninstaller()
        assert result is None

    def test_returns_path_when_exe_exists_windows(self, tmp_path: Path) -> None:
        """_find_uninstaller returns the unins000.exe path when it exists (Windows)."""
        uninstaller = tmp_path / "unins000.exe"
        uninstaller.touch()
        dialog = _make_settings_dialog()
        with patch.object(sys, "platform", "win32"), \
             patch.object(sys, "executable", str(tmp_path / "launcher.exe")):
            result = dialog._find_uninstaller()
        assert result == uninstaller

    def test_returns_none_when_exe_missing_windows(self, tmp_path: Path) -> None:
        """_find_uninstaller returns None when unins000.exe is absent (Windows)."""
        dialog = _make_settings_dialog()
        with patch.object(sys, "platform", "win32"), \
             patch.object(sys, "executable", str(tmp_path / "launcher.exe")):
            result = dialog._find_uninstaller()
        assert result is None


# ---------------------------------------------------------------------------
# Tests: _on_uninstall — Windows path
# ---------------------------------------------------------------------------

class TestOnUninstallWindows:
    def test_confirmation_dialog_is_shown(self, tmp_path: Path) -> None:
        """_on_uninstall asks for confirmation before launching uninstaller."""
        import tkinter.messagebox as mb
        uninstaller = tmp_path / "unins000.exe"
        uninstaller.touch()
        dialog = _make_settings_dialog()
        with patch.object(sys, "platform", "win32"), \
             patch.object(sys, "executable", str(tmp_path / "launcher.exe")), \
             patch.object(mb, "askyesno", return_value=False) as mock_ask:
            dialog._on_uninstall()
        mock_ask.assert_called_once()
        title, message = mock_ask.call_args[0]
        assert "uninstall" in title.lower() or "confirm" in title.lower()

    def test_no_action_when_cancelled(self, tmp_path: Path) -> None:
        """_on_uninstall does NOT call Popen or sys.exit when user cancels."""
        import tkinter.messagebox as mb
        uninstaller = tmp_path / "unins000.exe"
        uninstaller.touch()
        dialog = _make_settings_dialog()
        with patch.object(sys, "platform", "win32"), \
             patch.object(sys, "executable", str(tmp_path / "launcher.exe")), \
             patch.object(mb, "askyesno", return_value=False), \
             patch("launcher.gui.app.subprocess.Popen") as mock_popen, \
             patch("launcher.gui.app.sys.exit") as mock_exit:
            dialog._on_uninstall()
        mock_popen.assert_not_called()
        mock_exit.assert_not_called()

    def test_popen_and_exit_called_on_confirm(self, tmp_path: Path) -> None:
        """_on_uninstall calls Popen with uninstaller path and sys.exit(0) on confirm."""
        import tkinter.messagebox as mb
        uninstaller = tmp_path / "unins000.exe"
        uninstaller.touch()
        dialog = _make_settings_dialog()
        with patch.object(sys, "platform", "win32"), \
             patch.object(sys, "executable", str(tmp_path / "launcher.exe")), \
             patch.object(mb, "askyesno", return_value=True), \
             patch("launcher.gui.app.subprocess.Popen") as mock_popen, \
             patch("launcher.gui.app.sys.exit") as mock_exit:
            dialog._on_uninstall()
        mock_popen.assert_called_once_with([str(uninstaller)])
        mock_exit.assert_called_once_with(0)

    def test_error_shown_when_uninstaller_missing_at_click(self, tmp_path: Path) -> None:
        """_on_uninstall shows error if unins000.exe is not found when button clicked."""
        import tkinter.messagebox as mb
        dialog = _make_settings_dialog()
        with patch.object(sys, "platform", "win32"), \
             patch.object(sys, "executable", str(tmp_path / "launcher.exe")), \
             patch.object(mb, "showerror") as mock_err, \
             patch("launcher.gui.app.subprocess.Popen") as mock_popen, \
             patch("launcher.gui.app.sys.exit") as mock_exit:
            dialog._on_uninstall()
        mock_err.assert_called_once()
        mock_popen.assert_not_called()
        mock_exit.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: _on_uninstall — non-Windows path
# ---------------------------------------------------------------------------

class TestOnUninstallNonWindows:
    def test_shows_instructions_on_linux(self) -> None:
        """_on_uninstall shows manual instructions on Linux."""
        import tkinter.messagebox as mb
        dialog = _make_settings_dialog()
        with patch.object(sys, "platform", "linux"), \
             patch.object(mb, "showinfo") as mock_info, \
             patch("launcher.gui.app.subprocess.Popen") as mock_popen, \
             patch("launcher.gui.app.sys.exit") as mock_exit:
            dialog._on_uninstall()
        mock_info.assert_called_once()
        mock_popen.assert_not_called()
        mock_exit.assert_not_called()

    def test_shows_instructions_on_macos(self) -> None:
        """_on_uninstall shows manual instructions on macOS."""
        import tkinter.messagebox as mb
        dialog = _make_settings_dialog()
        with patch.object(sys, "platform", "darwin"), \
             patch.object(mb, "showinfo") as mock_info:
            dialog._on_uninstall()
        mock_info.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: button state
# ---------------------------------------------------------------------------

class TestButtonState:
    def test_button_disabled_when_no_uninstaller(self, tmp_path: Path) -> None:
        """_uninstall_button state is 'disabled' when unins000.exe is absent."""
        # Patch _find_uninstaller to return None to simulate dev/source mode.
        with patch("launcher.gui.app.SettingsDialog._find_uninstaller", return_value=None):
            dialog = _make_settings_dialog()
        # CTkButton is mocked — capture the kwargs passed to its constructor.
        ctk_button_calls = _CTK_MOCK.CTkButton.call_args_list
        # Find the call for the uninstall button (fg_color="#CC3333")
        uninstall_call = next(
            (c for c in ctk_button_calls if c.kwargs.get("fg_color") == "#CC3333"),
            None,
        )
        assert uninstall_call is not None, "No CTkButton call with fg_color='#CC3333' found"
        assert uninstall_call.kwargs.get("state") == "disabled", (
            f"Expected state='disabled', got {uninstall_call.kwargs.get('state')!r}"
        )

    def test_button_enabled_when_uninstaller_found(self, tmp_path: Path) -> None:
        """_uninstall_button state is 'normal' when unins000.exe exists."""
        fake_path = tmp_path / "unins000.exe"
        fake_path.touch()
        with patch("launcher.gui.app.SettingsDialog._find_uninstaller", return_value=fake_path):
            dialog = _make_settings_dialog()
        ctk_button_calls = _CTK_MOCK.CTkButton.call_args_list
        uninstall_call = next(
            (c for c in ctk_button_calls if c.kwargs.get("fg_color") == "#CC3333"),
            None,
        )
        assert uninstall_call is not None, "No CTkButton call with fg_color='#CC3333' found"
        assert uninstall_call.kwargs.get("state") == "normal", (
            f"Expected state='normal', got {uninstall_call.kwargs.get('state')!r}"
        )
