"""FIX-072 — Tester edge-case tests: Remove coming-soon templates from dropdown.

Additional tests beyond the Developer's suite, focusing on boundary conditions,
error paths, and integration scenarios.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helper — minimal App instance, same pattern as Developer's tests
# ---------------------------------------------------------------------------

def _make_app() -> object:
    """Return an App instance with all GUI and IO side-effects suppressed."""
    import launcher.gui.app as app_mod

    mock_window = MagicMock()
    mock_widget = MagicMock()
    mock_widget.get.return_value = ""
    mock_window.grid_columnconfigure = MagicMock()

    with (
        patch("launcher.gui.app.ctk") as mock_ctk,
        patch("launcher.gui.app.find_vscode", return_value=None),
        patch("launcher.gui.app.threading.Thread"),
        patch("launcher.gui.app.get_setting", return_value=True),
    ):
        mock_ctk.CTk.return_value = mock_window
        mock_ctk.BooleanVar.return_value = MagicMock(get=MagicMock(return_value=True))
        mock_ctk.StringVar.return_value = MagicMock()
        mock_ctk.CTkLabel.return_value = mock_widget
        mock_ctk.CTkEntry.return_value = mock_widget
        mock_ctk.CTkButton.return_value = mock_widget
        mock_ctk.CTkOptionMenu.return_value = mock_widget
        mock_ctk.CTkCheckBox.return_value = mock_widget
        mock_ctk.CTkSwitch.return_value = mock_widget
        mock_ctk.CTkImage.return_value = mock_widget

        with patch("launcher.gui.app.make_label_entry_row", return_value=mock_widget):
            app = app_mod.App.__new__(app_mod.App)
            app._window = mock_window
            app._latest_version = "0.0.0"
            app._current_template = ""
            return app


# ---------------------------------------------------------------------------
# Edge case: duplicate template names from list_templates
# ---------------------------------------------------------------------------

def test_duplicate_template_names_preserved_in_order():
    """If list_templates returns duplicates (both ready), both appear — no silent dedup."""
    import launcher.gui.app as app_mod

    app = _make_app()
    with (
        patch("launcher.gui.app.list_templates", return_value=["agent-workbench", "agent-workbench"]),
        patch("launcher.gui.app.is_template_ready", return_value=True),
    ):
        opts = app._get_template_options()

    # Both duplicates should pass through (list_templates is responsible for dedup)
    assert opts.count("Agent Workbench") == 2


# ---------------------------------------------------------------------------
# Edge case: _on_template_selected with empty string
# ---------------------------------------------------------------------------

def test_on_template_selected_with_empty_string():
    """_on_template_selected('') must set _current_template to '' without crashing."""
    app = _make_app()
    app._current_template = "Agent Workbench"
    app._on_template_selected("")
    assert app._current_template == ""


# ---------------------------------------------------------------------------
# Edge case: is_template_ready raises RuntimeError for one template
# ---------------------------------------------------------------------------

def test_get_template_options_propagates_is_ready_exception():
    """If is_template_ready raises, _get_template_options must not swallow the exception."""
    app = _make_app()

    def _boom(templates_dir, name):
        raise RuntimeError("disk read error")

    with (
        patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]),
        patch("launcher.gui.app.is_template_ready", side_effect=_boom),
    ):
        with pytest.raises(RuntimeError, match="disk read error"):
            app._get_template_options()


# ---------------------------------------------------------------------------
# Edge case: list_templates raises an exception
# ---------------------------------------------------------------------------

def test_get_template_options_propagates_list_templates_exception():
    """If list_templates raises, _get_template_options must propagate it immediately."""
    app = _make_app()

    with patch("launcher.gui.app.list_templates", side_effect=OSError("no disk")):
        with pytest.raises(OSError, match="no disk"):
            app._get_template_options()


# ---------------------------------------------------------------------------
# Edge case: _get_template_options() preserves order of ready templates
# ---------------------------------------------------------------------------

def test_get_template_options_preserves_ready_order():
    """Ready templates must appear in the same order list_templates returns them."""
    app = _make_app()

    templates = ["zzz-last", "aaa-first", "mmm-middle"]
    with (
        patch("launcher.gui.app.list_templates", return_value=templates),
        patch("launcher.gui.app.is_template_ready", return_value=True),
    ):
        opts = app._get_template_options()

    assert opts == ["Zzz Last", "Aaa First", "Mmm Middle"]


# ---------------------------------------------------------------------------
# Edge case: single template, ready — not affected by is_ready returning True
# ---------------------------------------------------------------------------

def test_single_ready_template_returned_as_single_element_list():
    """Exactly one ready template → list of exactly one display name."""
    app = _make_app()
    with (
        patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]),
        patch("launcher.gui.app.is_template_ready", return_value=True),
    ):
        opts = app._get_template_options()

    assert len(opts) == 1
    assert opts[0] == "Agent Workbench"


# ---------------------------------------------------------------------------
# Edge case: large number of templates — only ready ones returned
# ---------------------------------------------------------------------------

def test_large_template_list_only_ready_returned():
    """With many templates and only a few ready, exactly the ready ones are returned."""
    app = _make_app()

    templates = [f"template-{i:02d}" for i in range(20)]
    ready_set = {"template-03", "template-07", "template-19"}

    with (
        patch("launcher.gui.app.list_templates", return_value=templates),
        patch("launcher.gui.app.is_template_ready", side_effect=lambda _d, n: n in ready_set),
    ):
        opts = app._get_template_options()

    assert len(opts) == 3
    assert "Template 03" in opts
    assert "Template 07" in opts
    assert "Template 19" in opts
    # Make sure none of the non-ready ones are present
    for i in range(20):
        name = f"Template {i:02d}"
        if f"template-{i:02d}" not in ready_set:
            assert name not in opts


# ---------------------------------------------------------------------------
# Regression: no "_coming_soon_options" attribute at class level
# ---------------------------------------------------------------------------

def test_no_coming_soon_options_class_attribute():
    """The _coming_soon_options class-level attribute must not exist on the App class."""
    import launcher.gui.app as app_mod

    assert not hasattr(app_mod.App, "_coming_soon_options"), (
        "App class still has a _coming_soon_options class attribute"
    )
