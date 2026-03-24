"""Tests for GUI-001: Main Window Layout.

All tests run headlessly by replacing `customtkinter` with a MagicMock in
``sys.modules`` before the modules under test are imported.  No display
connection is attempted, so the suite runs on all platforms including
headless CI environments.
"""

from __future__ import annotations

import importlib
import sys
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# customtkinter is already mocked by tests/conftest.py — reuse that mock.
# ---------------------------------------------------------------------------
_CTK_MOCK = sys.modules["customtkinter"]

from launcher.gui.app import App  # noqa: E402
from launcher.gui import components as gui_components  # noqa: E402
import launcher.main as launcher_main  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_app() -> App:
    """Reset the CTK mock and return a new App instance."""
    _CTK_MOCK.reset_mock()
    return App()


# ---------------------------------------------------------------------------
# Module / class structure
# ---------------------------------------------------------------------------

class TestAppClassStructure:
    def test_app_class_is_importable(self):
        assert App is not None

    def test_app_has_run_method(self):
        assert callable(getattr(App, "run", None))

    def test_app_has_browse_method(self):
        assert callable(getattr(App, "_browse_destination", None))

    def test_app_has_on_create_method(self):
        assert callable(getattr(App, "_on_create_project", None))


# ---------------------------------------------------------------------------
# Window configuration
# ---------------------------------------------------------------------------

class TestWindowConfiguration:
    def test_ctk_window_created(self):
        _CTK_MOCK.reset_mock()
        App()
        _CTK_MOCK.CTk.assert_called_once()

    def test_window_title_set(self):
        from launcher.config import APP_NAME
        app = _fresh_app()
        app._window.title.assert_called_once_with(APP_NAME)

    def test_window_geometry_called(self):
        app = _fresh_app()
        app._window.geometry.assert_called_once()
        # Geometry string must be "WxH" format
        args = app._window.geometry.call_args[0]
        assert len(args) == 1
        assert "x" in args[0]

    def test_appearance_mode_set_to_dark(self):
        _CTK_MOCK.reset_mock()
        App()
        _CTK_MOCK.set_appearance_mode.assert_called_once_with("dark")

    def test_color_theme_set_to_blue(self):
        _CTK_MOCK.reset_mock()
        App()
        _CTK_MOCK.set_default_color_theme.assert_called_once_with("blue")


# ---------------------------------------------------------------------------
# Widget presence — verify each of the 5 required widgets is created
# ---------------------------------------------------------------------------

class TestRequiredWidgets:
    def test_project_name_entry_created(self):
        """CTkEntry must be called for the project name field."""
        _CTK_MOCK.reset_mock()
        App()
        assert _CTK_MOCK.CTkEntry.call_count >= 1

    def test_destination_entry_created(self):
        """CTkEntry must be called for the destination path field."""
        _CTK_MOCK.reset_mock()
        App()
        # make_label_entry_row + make_browse_row each produce one CTkEntry.
        assert _CTK_MOCK.CTkEntry.call_count >= 2

    def test_project_type_dropdown_created(self):
        """CTkOptionMenu must be created exactly once."""
        _CTK_MOCK.reset_mock()
        App()
        _CTK_MOCK.CTkOptionMenu.assert_called_once()

    def test_browse_button_created(self):
        """CTkButton for Browse must be present (make_browse_row creates it)."""
        _CTK_MOCK.reset_mock()
        App()
        # At minimum: Browse button + Create Project button = 2
        assert _CTK_MOCK.CTkButton.call_count >= 2

    def test_create_project_button_created(self):
        """CTkButton for Create Project must be present."""
        _CTK_MOCK.reset_mock()
        App()
        # Verify "Create Project" text was passed to one of the CTkButton calls.
        button_texts = [
            str(c)
            for c in _CTK_MOCK.CTkButton.call_args_list
        ]
        assert any("Create Project" in str(c) for c in _CTK_MOCK.CTkButton.call_args_list)

    def test_open_in_vscode_checkbox_created(self):
        """CTkCheckBox must be created at least twice (Open in VS Code + Include README files)."""
        _CTK_MOCK.reset_mock()
        App()
        assert _CTK_MOCK.CTkCheckBox.call_count >= 2

    def test_open_in_vscode_checkbox_text(self):
        """CTkCheckBox must carry the label 'Open in VS Code'."""
        _CTK_MOCK.reset_mock()
        App()
        calls = _CTK_MOCK.CTkCheckBox.call_args_list
        assert any("Open in VS Code" in str(c) for c in calls)

    def test_project_name_entry_is_accessible_as_attribute(self):
        app = _fresh_app()
        assert hasattr(app, "project_name_entry")

    def test_destination_entry_is_accessible_as_attribute(self):
        app = _fresh_app()
        assert hasattr(app, "destination_entry")

    def test_project_type_dropdown_is_accessible_as_attribute(self):
        app = _fresh_app()
        assert hasattr(app, "project_type_dropdown")

    def test_browse_button_not_directly_stored(self):
        """Browse button is embedded in make_browse_row; App does not need to
        store it as an attribute, but the grid call must have happened."""
        _CTK_MOCK.reset_mock()
        App()
        # CTkButton().grid() must have been called at least twice
        btn_instance = _CTK_MOCK.CTkButton.return_value
        assert btn_instance.grid.call_count >= 2

    def test_open_in_vscode_checkbox_is_accessible_as_attribute(self):
        app = _fresh_app()
        assert hasattr(app, "open_in_vscode_checkbox")

    def test_create_button_is_accessible_as_attribute(self):
        app = _fresh_app()
        assert hasattr(app, "create_button")


# ---------------------------------------------------------------------------
# Browse destination logic
# ---------------------------------------------------------------------------

class TestBrowseDestination:
    def test_browse_sets_destination_entry(self):
        """_browse_destination populates the destination entry when a path is chosen."""
        app = _fresh_app()
        # Reset call tracking on the shared entry mock so counts are clean.
        app.destination_entry.reset_mock()
        with patch("launcher.gui.app.filedialog.askdirectory", return_value="/tmp/myproject"):
            app._browse_destination()
        app.destination_entry.delete.assert_called_once_with(0, "end")
        app.destination_entry.insert.assert_called_once_with(0, "/tmp/myproject")

    def test_browse_noop_on_cancel(self):
        """_browse_destination does nothing when the dialog is cancelled (empty string)."""
        app = _fresh_app()
        app.destination_entry.reset_mock()
        with patch("launcher.gui.app.filedialog.askdirectory", return_value=""):
            app._browse_destination()
        app.destination_entry.delete.assert_not_called()
        app.destination_entry.insert.assert_not_called()

    def test_browse_noop_on_none(self):
        """_browse_destination does nothing when the dialog is cancelled (None)."""
        app = _fresh_app()
        app.destination_entry.reset_mock()
        with patch("launcher.gui.app.filedialog.askdirectory", return_value=None):
            app._browse_destination()
        app.destination_entry.delete.assert_not_called()
        app.destination_entry.insert.assert_not_called()

    def test_browse_dialog_title(self):
        """filedialog.askdirectory must be called with an informative title."""
        app = _fresh_app()
        with patch("launcher.gui.app.filedialog.askdirectory", return_value="") as mock_dialog:
            app._browse_destination()
        mock_dialog.assert_called_once()
        _, kwargs = mock_dialog.call_args
        assert "title" in kwargs


# ---------------------------------------------------------------------------
# run() delegates to mainloop
# ---------------------------------------------------------------------------

class TestRun:
    def test_run_calls_mainloop(self):
        app = _fresh_app()
        app.run()
        app._window.mainloop.assert_called_once()


# ---------------------------------------------------------------------------
# components module
# ---------------------------------------------------------------------------

class TestComponents:
    def test_make_label_entry_row_returns_entry(self):
        """make_label_entry_row must return the CTkEntry it creates."""
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock(name="parent")
        result = gui_components.make_label_entry_row(parent_mock, "Label:", row=0)
        assert result is _CTK_MOCK.CTkEntry.return_value

    def test_make_label_entry_row_creates_label(self):
        """make_label_entry_row must create exactly one CTkLabel."""
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock(name="parent")
        gui_components.make_label_entry_row(parent_mock, "Label:", row=0)
        _CTK_MOCK.CTkLabel.assert_called_once()

    def test_make_browse_row_returns_entry(self):
        """make_browse_row must return the CTkEntry it creates."""
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock(name="parent")
        result = gui_components.make_browse_row(
            parent_mock, "Dest:", browse_command=lambda: None, row=0
        )
        assert result is _CTK_MOCK.CTkEntry.return_value

    def test_make_browse_row_creates_button(self):
        """make_browse_row must create exactly one CTkButton (the Browse button)."""
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock(name="parent")
        gui_components.make_browse_row(
            parent_mock, "Dest:", browse_command=lambda: None, row=0
        )
        _CTK_MOCK.CTkButton.assert_called_once()

    def test_make_browse_row_wires_command(self):
        """Browse button must be wired to the provided command callback."""
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock(name="parent")
        sentinel = lambda: None  # noqa: E731
        gui_components.make_browse_row(parent_mock, "Dest:", browse_command=sentinel, row=0)
        _, kwargs = _CTK_MOCK.CTkButton.call_args
        assert kwargs.get("command") is sentinel


# ---------------------------------------------------------------------------
# main() integration
# ---------------------------------------------------------------------------

class TestMainIntegration:
    def test_main_creates_app_and_calls_run(self):
        """launcher.main.main() must instantiate App and call run().

        PYTEST_CURRENT_TEST is unset for this test so the headless guard does
        not short-circuit the call.  We also patch App so no real window opens.
        """
        with patch("launcher.gui.app.App") as MockApp, \
             patch.dict("os.environ", {}, clear=False) as _env:
            # Remove the sentinel so the headless guard does not fire.
            import os
            os.environ.pop("PYTEST_CURRENT_TEST", None)
            mock_instance = MagicMock()
            MockApp.return_value = mock_instance
            launcher_main.main()
        MockApp.assert_called_once()
        mock_instance.run.assert_called_once()
