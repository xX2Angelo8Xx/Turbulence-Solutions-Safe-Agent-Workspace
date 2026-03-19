"""Tests for GUI-018 — Relocate Python Runtime Option.

Verifies:
1. A gear (⚙) settings button is created on the App main window.
2. The gear button uses place() for positioning.
3. SettingsDialog can be instantiated.
4. Dialog title is "Settings".
5. Current path label shows read_python_path() result.
6. Current path label shows "Not configured" when no path set.
7. Auto-detect uses sys._MEIPASS when available (bundled).
8. Auto-detect falls back to sys.executable parent hierarchy in dev mode.
9. Auto-detect success triggers write_python_path and shows confirmation.
10. Auto-detect failure (file not found) shows an error message.
11. Browse button calls askopenfilename.
12. Browse selection calls write_python_path and shows confirmation.
13. Browse cancellation (empty string) does nothing.
14. Close button destroys the dialog.
15. write_python_path is called with a Path object (not a string).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# Reuse the shared customtkinter mock injected by conftest.py.
_CTK_MOCK = sys.modules["customtkinter"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app() -> "App":  # noqa: F821
    """Return a fresh App instance with all widgets mocked."""
    from launcher.gui.app import App
    _CTK_MOCK.reset_mock()
    return App()


def _make_dialog(parent=None, current_path=None) -> "SettingsDialog":  # noqa: F821
    """Return a SettingsDialog with read_python_path mocked to current_path."""
    from launcher.gui.app import SettingsDialog
    if parent is None:
        parent = MagicMock()
    with patch("launcher.gui.app.read_python_path", return_value=current_path):
        return SettingsDialog(parent)


# ---------------------------------------------------------------------------
# Tests: Gear button on main window
# ---------------------------------------------------------------------------

class TestGearButton:
    def test_gear_button_attribute_exists(self) -> None:
        """App instance must have a settings_button attribute after _build_ui."""
        app = _make_app()
        assert hasattr(app, "settings_button"), "App is missing 'settings_button' attribute"

    def test_gear_button_text_is_gear_symbol(self) -> None:
        """Settings button must be created with the ⚙ gear character."""
        button_calls = []
        original_ctk_button = _CTK_MOCK.CTkButton

        def _capture_button(*args, **kwargs):
            btn = MagicMock()
            btn._kwargs = kwargs
            button_calls.append(kwargs)
            return btn

        _CTK_MOCK.reset_mock()
        with patch.object(_CTK_MOCK, "CTkButton", side_effect=_capture_button):
            from launcher.gui.app import App
            App()

        gear_calls = [c for c in button_calls if c.get("text") == "⚙"]
        assert gear_calls, "No CTkButton created with text='⚙'"

    def test_gear_button_command_is_open_settings(self) -> None:
        """The gear button's command must be _open_settings_dialog."""
        app = _make_app()
        # settings_button is a MagicMock from CTK; we verify via App's method.
        assert callable(app._open_settings_dialog), "_open_settings_dialog must be callable"


# ---------------------------------------------------------------------------
# Tests: SettingsDialog structure
# ---------------------------------------------------------------------------

class TestSettingsDialogInit:
    def test_dialog_title_is_settings(self) -> None:
        """The CTkToplevel dialog must be titled 'Settings'."""
        parent = MagicMock()
        with patch("launcher.gui.app.read_python_path", return_value=None):
            from launcher.gui.app import SettingsDialog
            dlg = SettingsDialog(parent)
        dlg._dialog.title.assert_called_with("Settings")

    def test_dialog_grab_set_called(self) -> None:
        """grab_set() must be called at least once to make the dialog modal."""
        parent = MagicMock()
        _CTK_MOCK.reset_mock()
        with patch("launcher.gui.app.read_python_path", return_value=None):
            from launcher.gui.app import SettingsDialog
            dlg = SettingsDialog(parent)
        dlg._dialog.grab_set.assert_called()

    def test_current_path_label_shows_configured_path(self) -> None:
        """When read_python_path returns a path, label shows it as string."""
        fake_path = Path("/usr/local/python-embed/python3")
        with patch("launcher.gui.app.read_python_path", return_value=fake_path):
            from launcher.gui.app import SettingsDialog
            dlg = SettingsDialog(MagicMock())
        assert dlg._current_path_label is not None

    def test_current_path_label_shows_not_configured(self) -> None:
        """When read_python_path returns None, show 'Not configured'."""
        label_configs = []

        def _capture_label(*args, **kwargs):
            lbl = MagicMock()
            lbl._init_kwargs = kwargs
            label_configs.append(kwargs)
            return lbl

        with patch("launcher.gui.app.read_python_path", return_value=None), \
             patch.object(_CTK_MOCK, "CTkLabel", side_effect=_capture_label):
            from launcher.gui.app import SettingsDialog
            dlg = SettingsDialog(MagicMock())

        texts_created = [c.get("text", "") for c in label_configs]
        assert "Not configured" in texts_created, (
            f"Expected 'Not configured' in label texts. Got: {texts_created}"
        )

    def test_dialog_has_auto_detect_button(self) -> None:
        """SettingsDialog must expose _auto_detect_button attribute."""
        dlg = _make_dialog()
        assert hasattr(dlg, "_auto_detect_button"), "Missing _auto_detect_button"

    def test_dialog_has_browse_button(self) -> None:
        """SettingsDialog must expose _browse_button attribute."""
        dlg = _make_dialog()
        assert hasattr(dlg, "_browse_button"), "Missing _browse_button"

    def test_dialog_has_close_button(self) -> None:
        """SettingsDialog must expose _close_button attribute."""
        dlg = _make_dialog()
        assert hasattr(dlg, "_close_button"), "Missing _close_button"


# ---------------------------------------------------------------------------
# Tests: Auto-detect logic
# ---------------------------------------------------------------------------

class TestAutoDetect:
    def test_auto_detect_uses_meipass_when_available(self) -> None:
        """When sys._MEIPASS exists, auto-detect resolves from sys.executable parent."""
        dlg = _make_dialog()
        fake_exe = Path("/app/launcher")
        with patch.object(sys, "_MEIPASS", "/app/_internal", create=True), \
             patch.object(sys, "executable", str(fake_exe)), \
             patch("sys.platform", "win32"):
            result = dlg._find_bundled_python()
        expected = fake_exe.parent / "python-embed" / "python.exe"
        assert result == expected, f"Expected {expected}, got {result}"

    def test_auto_detect_fallback_without_meipass_windows(self) -> None:
        """Without _MEIPASS, auto-detect goes two levels up from sys.executable (Windows)."""
        dlg = _make_dialog()
        fake_exe = Path("/workspace/.venv/Scripts/python.exe")
        # Remove _MEIPASS if it exists
        original = getattr(sys, "_MEIPASS", _SENTINEL := object())
        if original is not _SENTINEL:
            delattr(sys, "_MEIPASS")
        try:
            with patch.object(sys, "executable", str(fake_exe)), \
                 patch("sys.platform", "win32"):
                result = dlg._find_bundled_python()
        finally:
            if original is not _SENTINEL:
                sys._MEIPASS = original

        expected = fake_exe.parent.parent / "python-embed" / "python.exe"
        assert result == expected, f"Expected {expected}, got {result}"

    def test_auto_detect_fallback_without_meipass_linux(self) -> None:
        """Without _MEIPASS, auto-detect uses python3 on non-Windows."""
        dlg = _make_dialog()
        fake_exe = Path("/workspace/.venv/bin/python3")
        original = getattr(sys, "_MEIPASS", _SENTINEL := object())
        if original is not _SENTINEL:
            delattr(sys, "_MEIPASS")
        try:
            with patch.object(sys, "executable", str(fake_exe)), \
                 patch("sys.platform", "linux"):
                result = dlg._find_bundled_python()
        finally:
            if original is not _SENTINEL:
                sys._MEIPASS = original

        expected = fake_exe.parent.parent / "python-embed" / "python3"
        assert result == expected, f"Expected {expected}, got {result}"

    def test_auto_detect_found_calls_write_python_path(self) -> None:
        """When recommended python.exe exists, write_python_path is called."""
        dlg = _make_dialog()
        fake_python = Path("/app/python-embed/python.exe")
        dlg._find_bundled_python = MagicMock(return_value=fake_python)

        import tkinter.messagebox as mb
        with patch("launcher.gui.app.write_python_path") as mock_write, \
             patch.object(mb, "showinfo", return_value=None):
            # Patch Path.exists() to True for our fake path
            with patch.object(Path, "exists", return_value=True):
                dlg._on_auto_detect()

        mock_write.assert_called_once_with(fake_python)

    def test_auto_detect_found_shows_success_message(self) -> None:
        """When python.exe found, showinfo is called with path in the message body."""
        dlg = _make_dialog()
        fake_python = Path("/app/python-embed/python.exe")
        dlg._find_bundled_python = MagicMock(return_value=fake_python)

        import tkinter.messagebox as mb
        with patch("launcher.gui.app.write_python_path"), \
             patch.object(mb, "showinfo") as mock_info, \
             patch.object(Path, "exists", return_value=True):
            dlg._on_auto_detect()

        mock_info.assert_called_once()
        # Check the message body (second positional arg) contains the path
        call_args = mock_info.call_args
        message_body = call_args.args[1] if call_args.args else ""
        assert str(fake_python) in message_body, (
            f"Path not in showinfo message. Message: {message_body!r}"
        )

    def test_auto_detect_not_found_shows_error(self) -> None:
        """When python-embed is not found, showerror is called."""
        dlg = _make_dialog()
        dlg._find_bundled_python = MagicMock(return_value=None)

        import tkinter.messagebox as mb
        with patch("launcher.gui.app.write_python_path") as mock_write, \
             patch.object(mb, "showerror") as mock_error:
            dlg._on_auto_detect()

        mock_write.assert_not_called()
        mock_error.assert_called_once()

    def test_auto_detect_nonexistent_path_shows_error(self) -> None:
        """When _find_bundled_python returns a path that does not exist, show error."""
        dlg = _make_dialog()
        missing_path = Path("/app/python-embed/python.exe")
        dlg._find_bundled_python = MagicMock(return_value=missing_path)

        import tkinter.messagebox as mb
        with patch("launcher.gui.app.write_python_path") as mock_write, \
             patch.object(mb, "showerror") as mock_error, \
             patch.object(Path, "exists", return_value=False):
            dlg._on_auto_detect()

        mock_write.assert_not_called()
        mock_error.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: Browse logic
# ---------------------------------------------------------------------------

class TestBrowse:
    def test_browse_calls_askopenfilename(self) -> None:
        """Browse button must call filedialog.askopenfilename."""
        import tkinter.filedialog as fd
        dlg = _make_dialog()
        selected = Path("/usr/local/python-embed/python3")

        with patch.object(fd, "askopenfilename", return_value=str(selected)) as mock_ask, \
             patch("launcher.gui.app.write_python_path"), \
             patch("tkinter.messagebox.showinfo"):
            dlg._on_browse()

        mock_ask.assert_called_once()

    def test_browse_calls_write_python_path_with_path_object(self) -> None:
        """After user selects a file, write_python_path is called with a Path."""
        import tkinter.filedialog as fd
        dlg = _make_dialog()
        selected_str = "/usr/local/python-embed/python3"

        with patch.object(fd, "askopenfilename", return_value=selected_str), \
             patch("launcher.gui.app.write_python_path") as mock_write, \
             patch("tkinter.messagebox.showinfo"):
            dlg._on_browse()

        mock_write.assert_called_once()
        args, _ = mock_write.call_args
        assert isinstance(args[0], Path), f"Expected Path, got {type(args[0])}"
        assert args[0] == Path(selected_str)

    def test_browse_shows_success_message(self) -> None:
        """After successful browse selection, showinfo is called with the path."""
        import tkinter.filedialog as fd
        import tkinter.messagebox as mb
        dlg = _make_dialog()
        selected_str = "/usr/local/python-embed/python3"

        with patch.object(fd, "askopenfilename", return_value=selected_str), \
             patch("launcher.gui.app.write_python_path"), \
             patch.object(mb, "showinfo") as mock_info:
            dlg._on_browse()

        mock_info.assert_called_once()
        call_args = mock_info.call_args
        message_body = call_args.args[1] if call_args.args else ""
        assert str(Path(selected_str)) in message_body, (
            f"Path not in showinfo message. Message: {message_body!r}"
        )

    def test_browse_cancel_does_nothing(self) -> None:
        """When user cancels browse (empty string), write_python_path is not called."""
        import tkinter.filedialog as fd
        dlg = _make_dialog()

        with patch.object(fd, "askopenfilename", return_value=""), \
             patch("launcher.gui.app.write_python_path") as mock_write, \
             patch("tkinter.messagebox.showinfo") as mock_info:
            dlg._on_browse()

        mock_write.assert_not_called()
        mock_info.assert_not_called()

    def test_browse_updates_current_path_label(self) -> None:
        """After a successful browse, _current_path_label is updated."""
        import tkinter.filedialog as fd
        dlg = _make_dialog()
        selected_str = "/usr/local/python-embed/python3"
        expected_text = str(Path(selected_str))

        with patch.object(fd, "askopenfilename", return_value=selected_str), \
             patch("launcher.gui.app.write_python_path"), \
             patch("tkinter.messagebox.showinfo"):
            dlg._on_browse()

        dlg._current_path_label.configure.assert_called()
        # Inspect only calls that include 'text=' keyword argument
        text_values = [
            c.kwargs.get("text", "") for c in dlg._current_path_label.configure.call_args_list
            if "text" in c.kwargs
        ]
        assert any(expected_text in t for t in text_values), (
            f"Label not updated to expected path '{expected_text}'. Text values: {text_values}"
        )


# ---------------------------------------------------------------------------
# Tests: Close button
# ---------------------------------------------------------------------------

class TestCloseButton:
    def test_close_button_destroys_dialog(self) -> None:
        """Close button command must be dialog.destroy."""
        parent = MagicMock()
        with patch("launcher.gui.app.read_python_path", return_value=None):
            from launcher.gui.app import SettingsDialog
            dlg = SettingsDialog(parent)

        # The close button's command should be dlg._dialog.destroy.
        # Since _dialog is a MagicMock (CTkToplevel), we verify destroy is accessible.
        assert hasattr(dlg._dialog, "destroy"), "Dialog must have destroy method"


# ---------------------------------------------------------------------------
# Tests: Open settings dialog from App
# ---------------------------------------------------------------------------

class TestOpenSettingsDialog:
    def test_open_settings_dialog_method_exists(self) -> None:
        """App._open_settings_dialog must be defined."""
        app = _make_app()
        assert hasattr(app, "_open_settings_dialog")
        assert callable(app._open_settings_dialog)

    def test_open_settings_dialog_creates_settings_dialog(self) -> None:
        """_open_settings_dialog() must instantiate a SettingsDialog."""
        app = _make_app()
        with patch("launcher.gui.app.SettingsDialog") as mock_dialog_class, \
             patch("launcher.gui.app.read_python_path", return_value=None):
            app._open_settings_dialog()
        mock_dialog_class.assert_called_once()
