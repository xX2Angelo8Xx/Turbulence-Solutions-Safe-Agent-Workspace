"""Tests for FIX-074: Fix Project Type dropdown — remove Coding option, add disabled
Certification Pipeline Coming Soon entry, ensure only Agent Workbench is selectable.

All tests run headlessly using the customtkinter MagicMock already configured in
tests/conftest.py. No real GUI window is created.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# customtkinter is mocked by conftest.py before any launcher module is imported.
from launcher.gui.app import App, _COMING_SOON_LABEL


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app(extra_ready_templates: list[str] | None = None) -> App:
    """Return a fresh App instance with a controlled template directory.

    By default the template list contains only 'agent-workbench' as a ready
    template. Pass *extra_ready_templates* to inject additional ready template
    names (excluding 'certification-pipeline' which is always excluded).
    """
    ready = ["agent-workbench"] + (extra_ready_templates or [])

    def _list_templates(templates_dir: Path) -> list[str]:
        return sorted(ready + ["certification-pipeline"])

    def _is_template_ready(templates_dir: Path, name: str) -> bool:
        return name in ready

    with patch("launcher.gui.app.list_templates", side_effect=_list_templates), \
         patch("launcher.gui.app.is_template_ready", side_effect=_is_template_ready):
        return App()


def _get_configure_values(app: App) -> list[str]:
    """Return the last 'values' list passed to project_type_dropdown.configure()."""
    calls = app.project_type_dropdown.configure.call_args_list
    for call in reversed(calls):
        values = call.kwargs.get("values") or (call.args[0] if call.args else None)
        if values is not None:
            return list(values)
    return []


# ---------------------------------------------------------------------------
# Constant sanity check
# ---------------------------------------------------------------------------

class TestComingSoonConstant:
    def test_coming_soon_label_is_string(self):
        assert isinstance(_COMING_SOON_LABEL, str)

    def test_coming_soon_label_contains_certification_pipeline(self):
        assert "Certification Pipeline" in _COMING_SOON_LABEL

    def test_coming_soon_label_contains_coming_soon(self):
        assert "Coming Soon" in _COMING_SOON_LABEL


# ---------------------------------------------------------------------------
# Dropdown values — checked via configure() call on the widget
# ---------------------------------------------------------------------------

class TestDropdownContainsComingSoon:
    def test_coming_soon_is_in_dropdown_values(self):
        """The dropdown widget must include _COMING_SOON_LABEL after being configured."""
        app = _make_app()
        values = _get_configure_values(app)
        assert _COMING_SOON_LABEL in values

    def test_agent_workbench_is_in_dropdown_values(self):
        app = _make_app()
        values = _get_configure_values(app)
        assert "Agent Workbench" in values

    def test_coming_soon_is_last_in_dropdown_values(self):
        """The disabled coming-soon entry must be the last in the dropdown."""
        app = _make_app()
        values = _get_configure_values(app)
        assert values[-1] == _COMING_SOON_LABEL

    def test_coding_not_in_dropdown_values(self):
        """'Coding' must never appear — BUG-116 regression check."""
        def _list_no_coding(p: Path) -> list[str]:
            return ["agent-workbench", "certification-pipeline"]

        def _is_ready(p: Path, name: str) -> bool:
            return name == "agent-workbench"

        with patch("launcher.gui.app.list_templates", side_effect=_list_no_coding), \
             patch("launcher.gui.app.is_template_ready", side_effect=_is_ready):
            app = App()
        values = _get_configure_values(app)
        assert "Coding" not in values


# ---------------------------------------------------------------------------
# _get_template_options — must NOT include coming-soon label (FIX-072 compat)
# ---------------------------------------------------------------------------

class TestGetTemplateOptions:
    def test_agent_workbench_in_options(self):
        app = _make_app()
        options = app._get_template_options()
        assert "Agent Workbench" in options

    def test_coming_soon_not_in_get_template_options(self):
        """_get_template_options() must NOT include _COMING_SOON_LABEL directly.

        The label is added via configure() in _build_ui(), not by _get_template_options().
        This ensures compatibility with FIX-072 tests.
        """
        app = _make_app()
        options = app._get_template_options()
        assert _COMING_SOON_LABEL not in options

    def test_certification_pipeline_not_selectable(self):
        """certification-pipeline must not be in _get_template_options() even if ready."""
        def _list(p: Path) -> list[str]:
            return ["agent-workbench", "certification-pipeline"]

        def _ready(p: Path, name: str) -> bool:
            return True  # pretend both are ready

        with patch("launcher.gui.app.list_templates", side_effect=_list), \
             patch("launcher.gui.app.is_template_ready", side_effect=_ready):
            app = App()
            options = app._get_template_options()
        assert not any("Certification Pipeline" in o for o in options)

    def test_no_coming_soon_in_options_return_value(self):
        """_get_template_options() must never return any 'coming soon' text."""
        app = _make_app()
        options = app._get_template_options()
        assert not any("coming soon" in o.lower() for o in options)


# ---------------------------------------------------------------------------
# _on_template_selected
# ---------------------------------------------------------------------------

class TestOnTemplateSelected:
    def test_valid_template_selection_accepted(self):
        app = _make_app()
        app._on_template_selected("Agent Workbench")
        assert app._current_template == "Agent Workbench"

    def test_coming_soon_selection_reverts_current_template(self):
        """Selecting the coming-soon label must not change _current_template."""
        app = _make_app()
        previous = app._current_template
        app._on_template_selected(_COMING_SOON_LABEL)
        assert app._current_template == previous

    def test_coming_soon_selection_calls_dropdown_set(self):
        """The dropdown widget must be reset to the previous value on coming-soon select."""
        app = _make_app()
        app._current_template = "Agent Workbench"
        app._on_template_selected(_COMING_SOON_LABEL)
        app.project_type_dropdown.set.assert_called_with("Agent Workbench")

    def test_multiple_valid_selections_accepted(self):
        app = _make_app()
        app._on_template_selected("Agent Workbench")
        assert app._current_template == "Agent Workbench"
        app._on_template_selected("Agent Workbench")
        assert app._current_template == "Agent Workbench"


# ---------------------------------------------------------------------------
# _on_create_project — coming-soon guard
# ---------------------------------------------------------------------------

class TestCreateProjectComingSoonGuard:
    def test_create_project_rejects_coming_soon(self):
        """_on_create_project must bail out when coming-soon label is selected."""
        import tkinter.messagebox as msgbox

        app = _make_app()
        app.project_type_dropdown.get.return_value = _COMING_SOON_LABEL

        with patch.object(msgbox, "showinfo") as mock_info, \
             patch("launcher.gui.app.create_project") as mock_create:
            app._on_create_project()

        mock_info.assert_called_once()
        mock_create.assert_not_called()

    def test_create_project_does_not_fire_coming_soon_guard_for_valid_template(self):
        """_on_create_project must NOT trigger the coming-soon guard for Agent Workbench."""
        import tkinter.messagebox as msgbox

        app = _make_app()
        app.project_type_dropdown.get.return_value = "Agent Workbench"
        app.project_name_entry.get.return_value = ""  # validation fails first

        with patch.object(msgbox, "showinfo") as mock_info, \
             patch("launcher.gui.app.create_project") as mock_create:
            app._on_create_project()

        assert not any(
            call.args and "Not Available" in str(call.args[0])
            for call in mock_info.call_args_list
        )
        mock_create.assert_not_called()


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

class TestInitialState:
    def test_agent_workbench_is_default_template(self):
        """The default selected template must be Agent Workbench."""
        app = _make_app()
        assert app._current_template == "Agent Workbench"

    def test_coming_soon_is_not_default_template(self):
        app = _make_app()
        assert app._current_template != _COMING_SOON_LABEL