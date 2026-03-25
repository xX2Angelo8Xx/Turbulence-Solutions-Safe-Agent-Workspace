"""Edge-case tests for FIX-074 — added by Tester Agent.

Covers scenarios not addressed by the Developer's 19 core tests:
1. Coming-soon label is always last even with multiple ready templates.
2. If a 'coding' template directory were added and ready, it WOULD appear
   (known limitation documented in dev-log — this test makes it explicit).
3. The _on_create_project coming-soon guard fires before name/destination
   validation (guard ordering correctness).
4. Revert logic is safe when _current_template is falsy (empty string edge).
5. Security: _COMING_SOON_LABEL contains no path traversal or injection chars.
6. Idempotency: calling _on_create_project multiple times with coming-soon
   always blocks and never calls create_project.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from launcher.gui.app import App, _COMING_SOON_LABEL


# ---------------------------------------------------------------------------
# Reuse the same helper pattern as the Developer's test file
# ---------------------------------------------------------------------------

def _make_app(ready: list[str] | None = None, all_dirs: list[str] | None = None) -> App:
    """Return a headless App instance.

    *ready* — names of templates that are truly ready (default: ['agent-workbench']).
    *all_dirs* — names returned by list_templates (default: ready + ['certification-pipeline']).
    """
    if ready is None:
        ready = ["agent-workbench"]
    if all_dirs is None:
        all_dirs = sorted(ready + ["certification-pipeline"])

    def _list(p: Path) -> list[str]:
        return all_dirs

    def _is_ready(p: Path, name: str) -> bool:
        return name in ready

    with patch("launcher.gui.app.list_templates", side_effect=_list), \
         patch("launcher.gui.app.is_template_ready", side_effect=_is_ready):
        return App()


# ---------------------------------------------------------------------------
# 1. Coming-soon is always the last entry regardless of template count
# ---------------------------------------------------------------------------

class TestComingSoonAlwaysLast:
    def test_coming_soon_is_last_with_three_templates(self):
        """Coming-soon must be the final entry even when 3 real templates are present."""
        app = _make_app(
            ready=["agent-workbench", "alpha-tool", "beta-tool"],
            all_dirs=["agent-workbench", "alpha-tool", "beta-tool", "certification-pipeline"],
        )
        calls = app.project_type_dropdown.configure.call_args_list
        values = None
        for call in reversed(calls):
            v = call.kwargs.get("values") or (call.args[0] if call.args else None)
            if v is not None:
                values = list(v)
                break
        assert values is not None, "configure() was never called with 'values'"
        assert values[-1] == _COMING_SOON_LABEL

    def test_coming_soon_appears_exactly_once(self):
        """_COMING_SOON_LABEL must appear exactly once in the dropdown values."""
        app = _make_app(
            ready=["agent-workbench", "extra-tool"],
            all_dirs=["agent-workbench", "certification-pipeline", "extra-tool"],
        )
        calls = app.project_type_dropdown.configure.call_args_list
        values = []
        for call in reversed(calls):
            v = call.kwargs.get("values") or (call.args[0] if call.args else None)
            if v is not None:
                values = list(v)
                break
        count = values.count(_COMING_SOON_LABEL)
        assert count == 1, f"Expected 1 occurrence of coming-soon label, got {count}"


# ---------------------------------------------------------------------------
# 2. Known limitation — coding template NOT filtered by name
# ---------------------------------------------------------------------------

class TestCodingTemplateKnownLimitation:
    def test_coding_template_would_appear_if_directory_existed_and_was_ready(self):
        """Known limitation (documented in dev-log): the filter only excludes
        'certification-pipeline' by name, NOT 'coding'. If a 'coding' directory
        were added and marked ready it would appear as a selectable option.

        This test documents the current behaviour so it's explicit. If a future
        WP adds a 'coding' directory, this test will alert the developer that
        the filter must be updated.
        """
        ready = ["agent-workbench", "coding"]
        all_dirs = ["agent-workbench", "certification-pipeline", "coding"]

        def _list(p: Path) -> list[str]:
            return all_dirs

        def _is_ready(p: Path, name: str) -> bool:
            return name in ready

        # Keep patches active during the _get_template_options() call too
        with patch("launcher.gui.app.list_templates", side_effect=_list), \
             patch("launcher.gui.app.is_template_ready", side_effect=_is_ready):
            app = App()
            options = app._get_template_options()

        # "Coding" (title-cased) appears because no coding-specific exclusion exists
        coding_labels = [o for o in options if "coding" in o.lower()]
        assert len(coding_labels) >= 1, (
            "Known limitation: 'coding' template is NOT excluded by the current "
            "filter. If this assertion fails it means the filter was expanded "
            "— update this test accordingly."
        )


# ---------------------------------------------------------------------------
# 3. _on_create_project coming-soon guard fires before other validation
# ---------------------------------------------------------------------------

class TestCreateProjectGuardOrdering:
    def test_coming_soon_guard_fires_even_with_empty_project_name(self):
        """Coming-soon guard in _on_create_project must fire before name validation."""
        import tkinter.messagebox as msgbox

        app = _make_app()
        app.project_type_dropdown.get.return_value = _COMING_SOON_LABEL
        app.project_name_entry.get.return_value = ""  # would fail name validation
        app.destination_entry.get.return_value = ""

        with patch.object(msgbox, "showinfo") as mock_info, \
             patch("launcher.gui.app.create_project") as mock_create, \
             patch("launcher.gui.app.validate_folder_name", return_value=(False, "bad name")) as mock_validate:
            app._on_create_project()

        # Guard should fire — showinfo called, validate_folder_name NOT called
        mock_info.assert_called_once()
        mock_validate.assert_not_called()
        mock_create.assert_not_called()

    def test_coming_soon_guard_fires_even_with_empty_destination(self):
        """Coming-soon guard fires before destination validation too."""
        import tkinter.messagebox as msgbox

        app = _make_app()
        app.project_type_dropdown.get.return_value = _COMING_SOON_LABEL
        app.project_name_entry.get.return_value = "my-project"
        app.destination_entry.get.return_value = ""  # would fail destination check

        with patch.object(msgbox, "showinfo") as mock_info, \
             patch("launcher.gui.app.create_project") as mock_create:
            app._on_create_project()

        mock_info.assert_called_once()
        mock_create.assert_not_called()


# ---------------------------------------------------------------------------
# 4. Revert logic safe when _current_template is empty
# ---------------------------------------------------------------------------

class TestOnTemplateSelectedRevertEdgeCases:
    def test_revert_to_empty_string_when_current_template_not_set(self):
        """If _current_template is somehow empty when coming-soon is selected,
        the revert logic must still run without raising an exception."""
        app = _make_app()
        # Force an empty _current_template (edge condition)
        app._current_template = ""
        # Must not raise
        app._on_template_selected(_COMING_SOON_LABEL)
        # The dropdown set should have been called with ""
        app.project_type_dropdown.set.assert_called_with("")

    def test_revert_uses_current_template_at_time_of_call(self):
        """Revert must use the template value stored at the time of the call."""
        app = _make_app()
        app._current_template = "Agent Workbench"
        app._on_template_selected(_COMING_SOON_LABEL)
        app.project_type_dropdown.set.assert_called_with("Agent Workbench")


# ---------------------------------------------------------------------------
# 5. Security: _COMING_SOON_LABEL contains no injection/traversal characters
# ---------------------------------------------------------------------------

class TestComingSoonLabelSecurity:
    def test_label_has_no_path_traversal(self):
        """_COMING_SOON_LABEL must not contain path separators or directory-
        traversal sequences. Note: '...' ellipsis punctuation is allowed;
        only path-like '/../' or leading '..' are flagged.
        """
        assert "/" not in _COMING_SOON_LABEL
        assert "\\" not in _COMING_SOON_LABEL
        # Directory traversal uses '../' or '..\\' — bare '...' is punctuation
        assert "../" not in _COMING_SOON_LABEL
        assert "..\\" not in _COMING_SOON_LABEL

    def test_label_has_no_html_or_script_tags(self):
        """_COMING_SOON_LABEL must not contain HTML or script injection vectors."""
        assert "<" not in _COMING_SOON_LABEL
        assert ">" not in _COMING_SOON_LABEL

    def test_label_has_no_shell_metacharacters(self):
        """_COMING_SOON_LABEL must not contain shell metacharacters."""
        dangerous = {";", "|", "&", "$", "`", "{", "}"}
        for char in dangerous:
            assert char not in _COMING_SOON_LABEL, (
                f"_COMING_SOON_LABEL contains shell metacharacter: {char!r}"
            )


# ---------------------------------------------------------------------------
# 6. Idempotency: repeated coming-soon submissions always block
# ---------------------------------------------------------------------------

class TestCreateProjectIdempotency:
    def test_coming_soon_guard_idempotent_across_multiple_calls(self):
        """Calling _on_create_project with coming-soon three times must always
        block and each time show the info dialog."""
        import tkinter.messagebox as msgbox

        app = _make_app()
        app.project_type_dropdown.get.return_value = _COMING_SOON_LABEL

        with patch.object(msgbox, "showinfo") as mock_info, \
             patch("launcher.gui.app.create_project") as mock_create:
            app._on_create_project()
            app._on_create_project()
            app._on_create_project()

        assert mock_info.call_count == 3
        mock_create.assert_not_called()
