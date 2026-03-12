"""Tests for GUI-012: UI Spacing and Visual Hierarchy.

All tests run headlessly by replacing `customtkinter` with a MagicMock in
``sys.modules`` before the modules under test are imported.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, call

# ---------------------------------------------------------------------------
# Inject the customtkinter mock BEFORE importing any launcher module.
# ---------------------------------------------------------------------------
_CTK_MOCK = MagicMock(name="customtkinter")
sys.modules["customtkinter"] = _CTK_MOCK

for _key in [k for k in sys.modules if k.startswith("launcher.gui")]:
    del sys.modules[_key]

from launcher.gui.app import App  # noqa: E402
from launcher.gui import components as gui_components  # noqa: E402


def _fresh_app() -> App:
    _CTK_MOCK.reset_mock()
    return App()


# ---------------------------------------------------------------------------
# Window height accommodates all rows
# ---------------------------------------------------------------------------

class TestWindowHeight:
    def test_window_height_at_least_400(self):
        app = _fresh_app()
        geometry_call = app._window.geometry.call_args[0][0]
        height = int(geometry_call.split("x")[1])
        assert height >= 400

    def test_window_height_is_440(self):
        app = _fresh_app()
        geometry_call = app._window.geometry.call_args[0][0]
        assert "440" in geometry_call


# ---------------------------------------------------------------------------
# Padding on main widget rows >= 10
# ---------------------------------------------------------------------------

class TestMainWidgetPadding:
    def test_create_button_padx_at_least_10(self):
        _CTK_MOCK.reset_mock()
        App()
        btn_instance = _CTK_MOCK.CTkButton.return_value
        grid_calls = btn_instance.grid.call_args_list
        create_calls = [
            c for c in _CTK_MOCK.CTkButton.call_args_list
            if c.kwargs.get("text") == "Create Project"
        ]
        assert len(create_calls) == 1
        create_btn_mock = _CTK_MOCK.CTkButton.return_value
        grid_call = create_btn_mock.grid.call_args
        padx = grid_call.kwargs.get("padx", 0)
        if isinstance(padx, tuple):
            assert all(v >= 10 for v in padx)
        else:
            assert padx >= 10

    def test_create_button_pady_at_least_10(self):
        _CTK_MOCK.reset_mock()
        App()
        create_btn_mock = _CTK_MOCK.CTkButton.return_value
        grid_call = create_btn_mock.grid.call_args
        pady = grid_call.kwargs.get("pady", 0)
        if isinstance(pady, tuple):
            assert any(v >= 10 for v in pady)
        else:
            assert pady >= 10

    def test_checkbox_padx_at_least_10(self):
        _CTK_MOCK.reset_mock()
        App()
        checkbox_instance = _CTK_MOCK.CTkCheckBox.return_value
        grid_call = checkbox_instance.grid.call_args
        padx = grid_call.kwargs.get("padx", 0)
        if isinstance(padx, tuple):
            assert all(v >= 10 for v in padx)
        else:
            assert padx >= 10

    def test_checkbox_pady_at_least_10(self):
        _CTK_MOCK.reset_mock()
        App()
        checkbox_instance = _CTK_MOCK.CTkCheckBox.return_value
        grid_call = checkbox_instance.grid.call_args
        pady = grid_call.kwargs.get("pady", 0)
        if isinstance(pady, tuple):
            assert any(v >= 10 for v in pady)
        else:
            assert pady >= 10


# ---------------------------------------------------------------------------
# Create button stretches full width (columnspan=3, sticky="ew")
# ---------------------------------------------------------------------------

class TestCreateButtonLayout:
    def test_create_button_columnspan_3(self):
        _CTK_MOCK.reset_mock()
        App()
        create_btn_mock = _CTK_MOCK.CTkButton.return_value
        grid_call = create_btn_mock.grid.call_args
        assert grid_call.kwargs.get("columnspan") == 3

    def test_create_button_sticky_ew(self):
        _CTK_MOCK.reset_mock()
        App()
        create_btn_mock = _CTK_MOCK.CTkButton.return_value
        grid_call = create_btn_mock.grid.call_args
        assert "ew" in str(grid_call.kwargs.get("sticky", ""))

    def test_create_button_height_at_least_36(self):
        _CTK_MOCK.reset_mock()
        App()
        create_calls = [
            c for c in _CTK_MOCK.CTkButton.call_args_list
            if c.kwargs.get("text") == "Create Project"
        ]
        assert len(create_calls) == 1
        assert create_calls[0].kwargs.get("height", 0) >= 36


# ---------------------------------------------------------------------------
# Components: consistent generous padding >= 10
# ---------------------------------------------------------------------------

class TestComponentPadding:
    def test_make_label_entry_row_label_padx(self):
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock()
        gui_components.make_label_entry_row(parent_mock, label_text="Test:", row=0)
        label_instance = _CTK_MOCK.CTkLabel.return_value
        grid_call = label_instance.grid.call_args
        padx = grid_call.kwargs.get("padx", 0)
        left = padx[0] if isinstance(padx, tuple) else padx
        assert left >= 10

    def test_make_label_entry_row_label_pady(self):
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock()
        gui_components.make_label_entry_row(parent_mock, label_text="Test:", row=0)
        label_instance = _CTK_MOCK.CTkLabel.return_value
        grid_call = label_instance.grid.call_args
        pady = grid_call.kwargs.get("pady", 0)
        val = pady[0] if isinstance(pady, tuple) else pady
        assert val >= 10

    def test_make_browse_row_browse_button_padx(self):
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock()
        gui_components.make_browse_row(
            parent_mock, label_text="Path:", browse_command=lambda: None, row=0
        )
        browse_btn = _CTK_MOCK.CTkButton.return_value
        grid_call = browse_btn.grid.call_args
        padx = grid_call.kwargs.get("padx", 0)
        right = padx[1] if isinstance(padx, tuple) else padx
        assert right >= 10

    def test_make_browse_row_pady(self):
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock()
        gui_components.make_browse_row(
            parent_mock, label_text="Path:", browse_command=lambda: None, row=0
        )
        browse_btn = _CTK_MOCK.CTkButton.return_value
        grid_call = browse_btn.grid.call_args
        pady = grid_call.kwargs.get("pady", 0)
        val = pady[0] if isinstance(pady, tuple) else pady
        assert val >= 10


# ---------------------------------------------------------------------------
# Edge-case tests added by Tester review
# ---------------------------------------------------------------------------

class TestEdgeCasesGui012:
    def test_window_width_is_580(self):
        """Window geometry must specify exactly 580 pixels wide."""
        app = _fresh_app()
        geometry_call = app._window.geometry.call_args[0][0]
        width = int(geometry_call.split("x")[0])
        assert width == 580

    def test_window_not_resizable(self):
        """Window must be non-resizable in both dimensions."""
        app = _fresh_app()
        app._window.resizable.assert_called_with(False, False)

    def test_make_label_entry_row_entry_pady(self):
        """CTkEntry in make_label_entry_row must have pady >= 10."""
        _CTK_MOCK.reset_mock()
        parent_mock = MagicMock()
        gui_components.make_label_entry_row(parent_mock, label_text="Test:", row=0)
        entry_instance = _CTK_MOCK.CTkEntry.return_value
        grid_call = entry_instance.grid.call_args
        pady = grid_call.kwargs.get("pady", 0)
        val = pady[0] if isinstance(pady, tuple) else pady
        assert val >= 10

    def test_dropdown_pady_at_least_10(self):
        """Project type dropdown must have pady >= 10."""
        _CTK_MOCK.reset_mock()
        App()
        dropdown_instance = _CTK_MOCK.CTkOptionMenu.return_value
        grid_call = dropdown_instance.grid.call_args
        pady = grid_call.kwargs.get("pady", 0)
        val = pady[0] if isinstance(pady, tuple) else pady
        assert val >= 10
