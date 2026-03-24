"""Tests for GUI-011: Apply Company Color Theme.

Run headlessly by replacing customtkinter with a MagicMock before importing
any launcher module that depends on it.  No display connection is required.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, call

# ---------------------------------------------------------------------------
# customtkinter is already mocked by tests/conftest.py — reuse that mock.
# ---------------------------------------------------------------------------
_CTK_MOCK = sys.modules["customtkinter"]

from launcher.gui.app import App  # noqa: E402
from launcher.gui import components as gui_components  # noqa: E402


def _fresh_app() -> App:
    _CTK_MOCK.reset_mock()
    return App()


# ---------------------------------------------------------------------------
# Color constants
# ---------------------------------------------------------------------------

class TestColorConstants:
    def test_color_primary_exists(self):
        from launcher.config import COLOR_PRIMARY
        assert COLOR_PRIMARY == "#0A1D4E"

    def test_color_secondary_exists(self):
        from launcher.config import COLOR_SECONDARY
        assert COLOR_SECONDARY == "#5BC5F2"

    def test_color_text_exists(self):
        from launcher.config import COLOR_TEXT
        assert COLOR_TEXT == "#FFFFFF"

    def test_color_primary_is_string(self):
        from launcher.config import COLOR_PRIMARY
        assert isinstance(COLOR_PRIMARY, str)

    def test_color_secondary_is_string(self):
        from launcher.config import COLOR_SECONDARY
        assert isinstance(COLOR_SECONDARY, str)

    def test_color_text_is_string(self):
        from launcher.config import COLOR_TEXT
        assert isinstance(COLOR_TEXT, str)


# ---------------------------------------------------------------------------
# Window background color
# ---------------------------------------------------------------------------

class TestWindowBackground:
    def test_window_configure_called(self):
        app = _fresh_app()
        app._window.configure.assert_called_with(fg_color="#0A1D4E")

    def test_window_configure_uses_color_primary(self):
        from launcher.config import COLOR_PRIMARY
        app = _fresh_app()
        calls = app._window.configure.call_args_list
        fg_args = [c for c in calls if c.kwargs.get("fg_color") == COLOR_PRIMARY]
        assert len(fg_args) >= 1


# ---------------------------------------------------------------------------
# Create Project button colors
# ---------------------------------------------------------------------------

class TestCreateButtonColors:
    def test_create_button_fg_color(self):
        from launcher.config import COLOR_SECONDARY
        app = _fresh_app()
        kwargs = _CTK_MOCK.CTkButton.call_args_list
        create_calls = [c for c in kwargs if c.kwargs.get("text") == "Create Project"]
        assert len(create_calls) == 1
        assert create_calls[0].kwargs.get("fg_color") == COLOR_SECONDARY

    def test_create_button_text_color(self):
        from launcher.config import COLOR_TEXT
        app = _fresh_app()
        kwargs = _CTK_MOCK.CTkButton.call_args_list
        create_calls = [c for c in kwargs if c.kwargs.get("text") == "Create Project"]
        assert len(create_calls) == 1
        assert create_calls[0].kwargs.get("text_color") == COLOR_TEXT

    def test_create_button_hover_color_set(self):
        app = _fresh_app()
        kwargs = _CTK_MOCK.CTkButton.call_args_list
        create_calls = [c for c in kwargs if c.kwargs.get("text") == "Create Project"]
        assert len(create_calls) == 1
        assert "hover_color" in create_calls[0].kwargs


# ---------------------------------------------------------------------------
# Project type label color
# ---------------------------------------------------------------------------

class TestProjectTypeLabelColor:
    def test_project_type_label_text_color(self):
        from launcher.config import COLOR_TEXT
        app = _fresh_app()
        label_calls = _CTK_MOCK.CTkLabel.call_args_list
        project_type_calls = [
            c for c in label_calls
            if c.kwargs.get("text") == "Project Type:"
        ]
        assert len(project_type_calls) == 1
        assert project_type_calls[0].kwargs.get("text_color") == COLOR_TEXT


# ---------------------------------------------------------------------------
# Dropdown colors
# ---------------------------------------------------------------------------

class TestDropdownColors:
    def test_dropdown_fg_color(self):
        from launcher.config import COLOR_SECONDARY
        app = _fresh_app()
        calls = _CTK_MOCK.CTkOptionMenu.call_args_list
        assert len(calls) == 1
        assert calls[0].kwargs.get("fg_color") == COLOR_SECONDARY

    def test_dropdown_button_color(self):
        from launcher.config import COLOR_SECONDARY
        app = _fresh_app()
        calls = _CTK_MOCK.CTkOptionMenu.call_args_list
        assert len(calls) == 1
        assert calls[0].kwargs.get("button_color") == COLOR_SECONDARY


# ---------------------------------------------------------------------------
# Checkbox colors
# ---------------------------------------------------------------------------

class TestCheckboxColors:
    def test_checkbox_text_color(self):
        from launcher.config import COLOR_TEXT
        app = _fresh_app()
        calls = _CTK_MOCK.CTkCheckBox.call_args_list
        assert len(calls) == 2
        assert all(c.kwargs.get("text_color") == COLOR_TEXT for c in calls)

    def test_checkbox_fg_color(self):
        from launcher.config import COLOR_SECONDARY
        app = _fresh_app()
        calls = _CTK_MOCK.CTkCheckBox.call_args_list
        assert len(calls) == 2
        assert all(c.kwargs.get("fg_color") == COLOR_SECONDARY for c in calls)


# ---------------------------------------------------------------------------
# Components: labels use COLOR_TEXT
# ---------------------------------------------------------------------------

class TestComponentLabelColors:
    def test_make_label_entry_row_label_color(self):
        from launcher.config import COLOR_TEXT
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock()
        gui_components.make_label_entry_row(parent_mock, label_text="Test:", row=0)
        calls = _CTK_MOCK.CTkLabel.call_args_list
        assert any(c.kwargs.get("text_color") == COLOR_TEXT for c in calls)

    def test_make_browse_row_label_color(self):
        from launcher.config import COLOR_TEXT
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock()
        gui_components.make_browse_row(
            parent_mock, label_text="Path:", browse_command=lambda: None, row=0
        )
        calls = _CTK_MOCK.CTkLabel.call_args_list
        assert any(c.kwargs.get("text_color") == COLOR_TEXT for c in calls)


# ---------------------------------------------------------------------------
# Components: entries use COLOR_TEXT
# ---------------------------------------------------------------------------

class TestComponentEntryColors:
    def test_make_label_entry_row_entry_color(self):
        from launcher.config import COLOR_TEXT
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock()
        gui_components.make_label_entry_row(parent_mock, label_text="Test:", row=0)
        calls = _CTK_MOCK.CTkEntry.call_args_list
        assert any(c.kwargs.get("text_color") == COLOR_TEXT for c in calls)

    def test_make_browse_row_entry_color(self):
        from launcher.config import COLOR_TEXT
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock()
        gui_components.make_browse_row(
            parent_mock, label_text="Path:", browse_command=lambda: None, row=0
        )
        calls = _CTK_MOCK.CTkEntry.call_args_list
        assert any(c.kwargs.get("text_color") == COLOR_TEXT for c in calls)


# ---------------------------------------------------------------------------
# Components: Browse button uses brand colors
# ---------------------------------------------------------------------------

class TestComponentBrowseButtonColors:
    def test_browse_button_fg_color(self):
        from launcher.config import COLOR_SECONDARY
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock()
        gui_components.make_browse_row(
            parent_mock, label_text="Path:", browse_command=lambda: None, row=0
        )
        calls = _CTK_MOCK.CTkButton.call_args_list
        assert any(c.kwargs.get("fg_color") == COLOR_SECONDARY for c in calls)

    def test_browse_button_text_color(self):
        from launcher.config import COLOR_TEXT
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock()
        gui_components.make_browse_row(
            parent_mock, label_text="Path:", browse_command=lambda: None, row=0
        )
        calls = _CTK_MOCK.CTkButton.call_args_list
        assert any(c.kwargs.get("text_color") == COLOR_TEXT for c in calls)

    def test_browse_button_hover_color_set(self):
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock()
        gui_components.make_browse_row(
            parent_mock, label_text="Path:", browse_command=lambda: None, row=0
        )
        calls = _CTK_MOCK.CTkButton.call_args_list
        assert any("hover_color" in c.kwargs for c in calls)


# ---------------------------------------------------------------------------
# Edge-case tests added by Tester review
# ---------------------------------------------------------------------------

class TestEdgeCasesGui011:
    def test_color_primary_hex_format(self):
        """COLOR_PRIMARY must be a 7-character valid hex colour string."""
        from launcher.config import COLOR_PRIMARY
        assert COLOR_PRIMARY.startswith("#")
        assert len(COLOR_PRIMARY) == 7
        assert int(COLOR_PRIMARY[1:], 16) >= 0

    def test_color_secondary_hex_format(self):
        """COLOR_SECONDARY must be a 7-character valid hex colour string."""
        from launcher.config import COLOR_SECONDARY
        assert COLOR_SECONDARY.startswith("#")
        assert len(COLOR_SECONDARY) == 7
        assert int(COLOR_SECONDARY[1:], 16) >= 0

    def test_color_text_hex_format(self):
        """COLOR_TEXT must be a 7-character valid hex colour string."""
        from launcher.config import COLOR_TEXT
        assert COLOR_TEXT.startswith("#")
        assert len(COLOR_TEXT) == 7
        assert int(COLOR_TEXT[1:], 16) >= 0

    def test_window_is_non_resizable(self):
        """Window must be explicitly set non-resizable in both dimensions."""
        app = _fresh_app()
        app._window.resizable.assert_called_with(False, False)

    def test_window_title_is_app_name(self):
        """Window title must be set to the APP_NAME constant."""
        from launcher.config import APP_NAME
        app = _fresh_app()
        app._window.title.assert_called_with(APP_NAME)

    def test_error_labels_use_red_not_brand_color(self):
        """Inline validation-error labels use 'red', not a brand palette colour."""
        from launcher.config import COLOR_PRIMARY, COLOR_SECONDARY
        _CTK_MOCK.reset_mock()
        App()
        label_calls = _CTK_MOCK.CTkLabel.call_args_list
        red_calls = [c for c in label_calls if c.kwargs.get("text_color") == "red"]
        assert len(red_calls) >= 2
        for call_ in red_calls:
            tc = call_.kwargs.get("text_color")
            assert tc not in (COLOR_PRIMARY, COLOR_SECONDARY)
