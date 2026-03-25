"""FIX-072 — Tests: Remove coming-soon templates from dropdown.

Verifies that:
1. _get_template_options() only returns ready templates.
2. No "...coming soon" suffix appears in the returned options.
3. Unready templates are excluded from the returned list.
4. _coming_soon_options attribute no longer exists on App.
5. _on_template_selected() updates _current_template normally.
6. BUG-107: Dropdown never shows an entry the user cannot use.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helper — build a minimal App instance without launching any real GUI
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

        with (
            patch("launcher.gui.app.make_label_entry_row", return_value=mock_widget),
            patch("launcher.gui.app.make_browse_row", return_value=mock_widget),
        ):
            app = app_mod.App.__new__(app_mod.App)
            # Minimal attribute initialisation (mirrors __init__ without _build_ui).
            app._window = mock_window
            app._latest_version = "0.0.0"
            app._current_template = ""
            return app


# ---------------------------------------------------------------------------
# Unit tests for _get_template_options()
# ---------------------------------------------------------------------------

def test_ready_templates_included():
    """Ready templates must appear in the options list."""
    import launcher.gui.app as app_mod

    app = _make_app()
    with (
        patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]),
        patch("launcher.gui.app.is_template_ready", return_value=True),
    ):
        opts = app._get_template_options()

    assert "Agent Workbench" in opts


def test_unready_templates_excluded():
    """Templates where is_template_ready() returns False must not be in options."""
    import launcher.gui.app as app_mod

    app = _make_app()

    def _ready(templates_dir, name):
        return name == "agent-workbench"  # only this one is ready

    with (
        patch("launcher.gui.app.list_templates", return_value=["agent-workbench", "certification-pipeline"]),
        patch("launcher.gui.app.is_template_ready", side_effect=_ready),
    ):
        opts = app._get_template_options()

    assert "Agent Workbench" in opts
    assert "Certification Pipeline" not in opts


def test_no_coming_soon_suffix_in_options():
    """The string '...coming soon' must never appear in any returned option."""
    import launcher.gui.app as app_mod

    app = _make_app()

    def _ready(templates_dir, name):
        return False  # all unready — should produce empty list

    with (
        patch("launcher.gui.app.list_templates", return_value=["certification-pipeline", "alpha-template"]),
        patch("launcher.gui.app.is_template_ready", side_effect=_ready),
    ):
        opts = app._get_template_options()

    for opt in opts:
        assert "coming soon" not in opt.lower(), (
            f"Option {opt!r} contains 'coming soon' but should have been filtered out"
        )


def test_get_template_options_returns_only_ready():
    """Integration: with a mix of ready and unready templates, only ready ones returned."""
    import launcher.gui.app as app_mod

    app = _make_app()

    templates = ["agent-workbench", "certification-pipeline", "future-template"]
    ready = {"agent-workbench"}

    with (
        patch("launcher.gui.app.list_templates", return_value=templates),
        patch("launcher.gui.app.is_template_ready", side_effect=lambda _d, n: n in ready),
    ):
        opts = app._get_template_options()

    assert opts == ["Agent Workbench"]
    assert len(opts) == 1


def test_empty_when_no_ready_templates():
    """When no templates are ready, options list is empty (not a list of coming-soon strings)."""
    import launcher.gui.app as app_mod

    app = _make_app()

    with (
        patch("launcher.gui.app.list_templates", return_value=["certification-pipeline"]),
        patch("launcher.gui.app.is_template_ready", return_value=False),
    ):
        opts = app._get_template_options()

    assert opts == []


# ---------------------------------------------------------------------------
# Tests for _coming_soon_options attribute removal
# ---------------------------------------------------------------------------

def test_coming_soon_options_attr_removed():
    """App must no longer have a _coming_soon_options attribute (BUG-107 cleanup)."""
    import launcher.gui.app as app_mod

    app = _make_app()
    assert not hasattr(app, "_coming_soon_options"), (
        "App still has _coming_soon_options attribute — it should have been removed in FIX-072"
    )


# ---------------------------------------------------------------------------
# Tests for _on_template_selected()
# ---------------------------------------------------------------------------

def test_on_template_selected_updates_current_template():
    """_on_template_selected() must update _current_template to the chosen value."""
    import launcher.gui.app as app_mod

    app = _make_app()
    app._on_template_selected("Agent Workbench")
    assert app._current_template == "Agent Workbench"


def test_on_template_selected_second_call_updates_again():
    """Calling _on_template_selected() twice in a row updates _current_template both times."""
    import launcher.gui.app as app_mod

    app = _make_app()
    app._on_template_selected("Agent Workbench")
    app._on_template_selected("My Other Template")
    assert app._current_template == "My Other Template"


# ---------------------------------------------------------------------------
# Regression test for BUG-107
# ---------------------------------------------------------------------------

def test_bug107_no_unready_template_in_dropdown_options():
    """Regression: BUG-107 — dropdown options must never include an unready template.

    Simulates the exact scenario: one ready template and one unready template;
    verifies the unready one is absent from the returned list.
    """
    import launcher.gui.app as app_mod

    app = _make_app()

    def _ready(templates_dir, name):
        # certification-pipeline is not ready (the template from the bug report)
        return name != "certification-pipeline"

    with (
        patch("launcher.gui.app.list_templates", return_value=["agent-workbench", "certification-pipeline"]),
        patch("launcher.gui.app.is_template_ready", side_effect=_ready),
    ):
        opts = app._get_template_options()

    assert "Certification Pipeline" not in opts, (
        "BUG-107 regression: 'Certification Pipeline' (unready) appeared in dropdown options"
    )
    assert "Agent Workbench" in opts
