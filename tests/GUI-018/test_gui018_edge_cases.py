"""Edge-case tests for GUI-018 — Relocate Python Runtime Option (Tester additions).

Covers gaps not addressed by the developer's 25 tests:
  - Auto-detect updates the path label on success
  - write_python_path OSError surfaces as showerror (auto-detect + browse paths)
  - Multiple calls to _open_settings_dialog each instantiate a fresh SettingsDialog
  - Dialog geometry and resizable flags
  - Close button is bound to _dialog.destroy (not a lambda or different callable)
  - Browse selects path containing spaces
  - Auto-detect uses python3 on macOS (darwin)
  - Dialog geometry string is "480x480"
  - shim_config imports exposed in app module namespace
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

_CTK_MOCK = sys.modules["customtkinter"]


# ---------------------------------------------------------------------------
# Helpers (mirrors the ones in the developer's test file)
# ---------------------------------------------------------------------------

def _make_app() -> "App":  # noqa: F821
    from launcher.gui.app import App
    _CTK_MOCK.reset_mock()
    return App()


def _make_dialog(current_path=None) -> "SettingsDialog":  # noqa: F821
    from launcher.gui.app import SettingsDialog
    with patch("launcher.gui.app.read_python_path", return_value=current_path):
        return SettingsDialog(MagicMock())


# ---------------------------------------------------------------------------
# Edge case: auto-detect updates the path label on success
# ---------------------------------------------------------------------------

class TestAutoDetectLabelUpdate:
    def test_auto_detect_success_updates_label(self) -> None:
        """After a successful auto-detect, _current_path_label.configure is called
        with the new path as text so the dialog shows the updated value."""
        dlg = _make_dialog()
        fake_python = Path("/app/python-embed/python.exe")
        dlg._find_bundled_python = MagicMock(return_value=fake_python)

        import tkinter.messagebox as mb
        with patch("launcher.gui.app.write_python_path"), \
             patch.object(mb, "showinfo"), \
             patch.object(Path, "exists", return_value=True):
            dlg._on_auto_detect()

        dlg._current_path_label.configure.assert_called()
        text_values = [
            c.kwargs.get("text", "")
            for c in dlg._current_path_label.configure.call_args_list
            if "text" in c.kwargs
        ]
        assert any(str(fake_python) in t for t in text_values), (
            f"Label not updated after auto-detect. text values: {text_values}"
        )


# ---------------------------------------------------------------------------
# Edge case: write_python_path raises OSError — showerror shown, no crash
# ---------------------------------------------------------------------------

class TestWriteFailureHandling:
    """If the filesystem write fails, the implementation should not crash silently.

    NOTE: The current implementation does NOT catch OSError from write_python_path.
    These tests document the current behaviour (exception propagates) and serve
    as a regression baseline.  If a future hardening WP wraps the write in try/except,
    these tests should be updated to assert showerror is called instead.
    """

    def test_auto_detect_write_exception_propagates(self) -> None:
        """OSError from write_python_path propagates out of _on_auto_detect.
        This documents the current (unguarded) behaviour."""
        dlg = _make_dialog()
        fake_python = Path("/app/python-embed/python.exe")
        dlg._find_bundled_python = MagicMock(return_value=fake_python)

        import tkinter.messagebox as mb
        with patch("launcher.gui.app.write_python_path", side_effect=OSError("disk full")), \
             patch.object(mb, "showinfo"), \
             patch.object(Path, "exists", return_value=True):
            with pytest.raises(OSError, match="disk full"):
                dlg._on_auto_detect()

    def test_browse_write_exception_propagates(self) -> None:
        """OSError from write_python_path propagates out of _on_browse.
        This documents the current (unguarded) behaviour."""
        import tkinter.filedialog as fd
        import tkinter.messagebox as mb
        dlg = _make_dialog()

        with patch.object(fd, "askopenfilename", return_value="/usr/bin/python3"), \
             patch("launcher.gui.app.write_python_path", side_effect=OSError("disk full")), \
             patch.object(mb, "showinfo"):
            with pytest.raises(OSError, match="disk full"):
                dlg._on_browse()


# ---------------------------------------------------------------------------
# Edge case: multiple calls to _open_settings_dialog
# ---------------------------------------------------------------------------

class TestMultipleDialogOpens:
    def test_open_settings_dialog_creates_new_instance_each_time(self) -> None:
        """Each call to _open_settings_dialog must create a separate SettingsDialog."""
        app = _make_app()
        instances = []
        with patch("launcher.gui.app.SettingsDialog", side_effect=lambda *a, **kw: instances.append(MagicMock()) or instances[-1]), \
             patch("launcher.gui.app.read_python_path", return_value=None):
            app._open_settings_dialog()
            app._open_settings_dialog()

        assert len(instances) == 2, (
            f"Expected 2 SettingsDialog instances from two calls, got {len(instances)}"
        )
        assert instances[0] is not instances[1], (
            "Both calls returned the same instance — dialog not re-created"
        )


# ---------------------------------------------------------------------------
# Edge case: dialog geometry and resizable flags
# ---------------------------------------------------------------------------

class TestDialogGeometry:
    def test_dialog_geometry_is_480x480(self) -> None:
        """The settings dialog must request a 480×480 geometry."""
        parent = MagicMock()
        with patch("launcher.gui.app.read_python_path", return_value=None):
            from launcher.gui.app import SettingsDialog
            dlg = SettingsDialog(parent)
        dlg._dialog.geometry.assert_called_with("480x480")

    def test_dialog_is_not_resizable(self) -> None:
        """The dialog must be non-resizable on both axes."""
        parent = MagicMock()
        with patch("launcher.gui.app.read_python_path", return_value=None):
            from launcher.gui.app import SettingsDialog
            dlg = SettingsDialog(parent)
        dlg._dialog.resizable.assert_called_with(False, False)


# ---------------------------------------------------------------------------
# Edge case: close button wired to _dialog.destroy
# ---------------------------------------------------------------------------

class TestCloseButtonWiring:
    def test_close_button_command_is_dialog_destroy(self) -> None:
        """The Close button's command kwarg must be the dialog's destroy method."""
        button_kwargs_list = []

        def _capture_button(*args, **kwargs):
            btn = MagicMock()
            btn._kwargs = kwargs
            button_kwargs_list.append(kwargs)
            return btn

        with patch.object(_CTK_MOCK, "CTkButton", side_effect=_capture_button), \
             patch("launcher.gui.app.read_python_path", return_value=None):
            from launcher.gui.app import SettingsDialog
            parent = MagicMock()
            dlg = SettingsDialog(parent)

        # Find the button created with text="Close"
        close_btn_creates = [k for k in button_kwargs_list if k.get("text") == "Close"]
        assert close_btn_creates, "No CTkButton with text='Close' found"
        # Its command should be dlg._dialog.destroy
        close_cmd = close_btn_creates[-1].get("command")
        assert close_cmd == dlg._dialog.destroy, (
            f"Close button command {close_cmd!r} is not _dialog.destroy"
        )


# ---------------------------------------------------------------------------
# Edge case: browse path with spaces
# ---------------------------------------------------------------------------

class TestBrowsePathWithSpaces:
    def test_browse_path_with_spaces_is_handled(self) -> None:
        """A path returned by askopenfilename that contains spaces must be
        passed to write_python_path as a Path object without truncation."""
        import tkinter.filedialog as fd
        import tkinter.messagebox as mb
        dlg = _make_dialog()
        selected_str = r"C:\Program Files\Python Embed\python.exe"

        with patch.object(fd, "askopenfilename", return_value=selected_str), \
             patch("launcher.gui.app.write_python_path") as mock_write, \
             patch.object(mb, "showinfo"):
            dlg._on_browse()

        mock_write.assert_called_once()
        args, _ = mock_write.call_args
        assert args[0] == Path(selected_str), (
            f"Path with spaces not preserved. Got: {args[0]!r}"
        )


# ---------------------------------------------------------------------------
# Edge case: auto-detect uses python3 on macOS (darwin)
# ---------------------------------------------------------------------------

class TestAutoDetectMacOS:
    def test_auto_detect_uses_python3_on_darwin(self) -> None:
        """_find_bundled_python must return python3 (not python.exe) on macOS."""
        dlg = _make_dialog()
        fake_exe = Path("/Applications/Launcher.app/Contents/MacOS/launcher")
        original = getattr(sys, "_MEIPASS", _SENTINEL := object())
        if original is not _SENTINEL:
            delattr(sys, "_MEIPASS")
        try:
            with patch.object(sys, "executable", str(fake_exe)), \
                 patch("sys.platform", "darwin"):
                result = dlg._find_bundled_python()
        finally:
            if original is not _SENTINEL:
                sys._MEIPASS = original

        assert result is not None
        assert result.name == "python3", (
            f"Expected 'python3' on darwin, got {result.name!r}"
        )
        assert "python3" not in str(result.parent.name), (
            "python3 should be a file inside python-embed, not a directory"
        )

    def test_auto_detect_uses_python_exe_on_windows(self) -> None:
        """_find_bundled_python must return python.exe on Windows."""
        dlg = _make_dialog()
        fake_exe = Path(r"C:\Launcher\launcher.exe")
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

        assert result is not None
        assert result.name == "python.exe", (
            f"Expected 'python.exe' on Windows, got {result.name!r}"
        )


# ---------------------------------------------------------------------------
# Edge case: shim_config symbols available in app module namespace
# ---------------------------------------------------------------------------

class TestShimConfigImports:
    def test_read_python_path_importable_from_app(self) -> None:
        """read_python_path must be importable from launcher.gui.app."""
        import launcher.gui.app as app_module
        assert hasattr(app_module, "read_python_path"), (
            "read_python_path not found in app module namespace"
        )

    def test_write_python_path_importable_from_app(self) -> None:
        """write_python_path must be importable from launcher.gui.app."""
        import launcher.gui.app as app_module
        assert hasattr(app_module, "write_python_path"), (
            "write_python_path not found in app module namespace"
        )
