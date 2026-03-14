"""Tests for GUI-014: Grey Out Unfinished Templates with Coming Soon.

Verifies that:
  1. is_template_ready() returns True for a directory with multiple files.
  2. is_template_ready() returns False for a directory with only README.md.
  3. is_template_ready() returns False for a non-existent directory.
  4. _get_template_options() appends ' ...coming soon' to unready templates.
  5. _get_template_options() does NOT append ' ...coming soon' to ready templates.
  6. The default selected template is the first ready one.
  7. Selecting a coming-soon option reverts to the previous valid selection.
  8. The _coming_soon_options set contains only unready template display names.
  9. _on_create_project uses self._current_template (not dropdown.get()).
 10. is_template_ready() returns False for directory with only README.md (case-insensitive not required - exact README.md).
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# customtkinter is already mocked by tests/conftest.py — reuse that mock.
# ---------------------------------------------------------------------------
_CTK_MOCK = sys.modules["customtkinter"]

from launcher.core.project_creator import is_template_ready, list_templates  # noqa: E402
from launcher.gui.app import App  # noqa: E402

_APP_GLOBALS = App._on_template_selected.__globals__


def _fresh_app() -> App:
    _CTK_MOCK.reset_mock()
    return App()


# ---------------------------------------------------------------------------
# Unit tests for is_template_ready()
# ---------------------------------------------------------------------------

class TestIsTemplateReady:
    def test_ready_when_directory_has_multiple_files(self, tmp_path: Path):
        """A directory with more than README.md is considered ready."""
        (tmp_path / "coding").mkdir()
        (tmp_path / "coding" / "README.md").write_text("# Coding")
        (tmp_path / "coding" / "app.py").write_text("# app")
        assert is_template_ready(tmp_path, "coding") is True

    def test_not_ready_when_only_readme(self, tmp_path: Path):
        """A directory containing only README.md is NOT ready."""
        (tmp_path / "creative-marketing").mkdir()
        (tmp_path / "creative-marketing" / "README.md").write_text("# Coming soon")
        assert is_template_ready(tmp_path, "creative-marketing") is False

    def test_not_ready_for_nonexistent_directory(self, tmp_path: Path):
        """A non-existent template name returns False."""
        assert is_template_ready(tmp_path, "does-not-exist") is False

    def test_ready_when_directory_has_single_non_readme_file(self, tmp_path: Path):
        """A directory with a single file that is not README.md is ready."""
        (tmp_path / "minimal").mkdir()
        (tmp_path / "minimal" / "main.py").write_text("# main")
        assert is_template_ready(tmp_path, "minimal") is True

    def test_not_ready_for_empty_directory(self, tmp_path: Path):
        """An empty template directory is NOT ready (no content at all)."""
        (tmp_path / "empty").mkdir()
        assert is_template_ready(tmp_path, "empty") is False

    def test_ready_when_only_subdirectory_present(self, tmp_path: Path):
        """A directory containing a subdirectory (and no files) is ready."""
        (tmp_path / "structured").mkdir()
        (tmp_path / "structured" / "src").mkdir()
        assert is_template_ready(tmp_path, "structured") is True

    def test_not_ready_with_readme_only_case_exact(self, tmp_path: Path):
        """Only a file named exactly 'README.md' triggers not-ready; other names are ready."""
        (tmp_path / "other").mkdir()
        (tmp_path / "other" / "readme.md").write_text("lower case")
        # 'readme.md' != 'README.md', so this single file is treated as ready
        assert is_template_ready(tmp_path, "other") is True


# ---------------------------------------------------------------------------
# Unit tests for _get_template_options() via App instance
# ---------------------------------------------------------------------------

class TestGetTemplateOptions:
    def test_coming_soon_label_appended_to_unready(self, tmp_path: Path):
        """Unready templates get ' ...coming soon' in their display name."""
        (tmp_path / "coding").mkdir()
        (tmp_path / "coding" / "app.py").write_text("")
        (tmp_path / "creative-marketing").mkdir()
        (tmp_path / "creative-marketing" / "README.md").write_text("")

        with patch.dict(_APP_GLOBALS, {"TEMPLATES_DIR": tmp_path}):
            app = _fresh_app()
            options = app._get_template_options()

        assert any("coming soon" in o for o in options)
        assert "Creative Marketing ...coming soon" in options

    def test_ready_template_has_no_coming_soon_label(self, tmp_path: Path):
        """Ready templates must NOT have ' ...coming soon' appended."""
        (tmp_path / "coding").mkdir()
        (tmp_path / "coding" / "app.py").write_text("")

        with patch.dict(_APP_GLOBALS, {"TEMPLATES_DIR": tmp_path}):
            app = _fresh_app()
            options = app._get_template_options()

        assert all("coming soon" not in o for o in options)

    def test_returns_both_ready_and_coming_soon(self, tmp_path: Path):
        """Both kinds of templates appear in the options list."""
        (tmp_path / "coding").mkdir()
        (tmp_path / "coding" / "app.py").write_text("")
        (tmp_path / "creative-marketing").mkdir()
        (tmp_path / "creative-marketing" / "README.md").write_text("")

        with patch.dict(_APP_GLOBALS, {"TEMPLATES_DIR": tmp_path}):
            app = _fresh_app()
            options = app._get_template_options()
            coming_soon = app._coming_soon_options

        assert len(options) == 2
        assert len(coming_soon) == 1
        assert "Coding" in options

    def test_coming_soon_set_contains_only_unready_display_names(self, tmp_path: Path):
        """The returned coming_soon set contains only the unready entries."""
        (tmp_path / "coding").mkdir()
        (tmp_path / "coding" / "app.py").write_text("")
        (tmp_path / "creative-marketing").mkdir()
        (tmp_path / "creative-marketing" / "README.md").write_text("")

        with patch.dict(_APP_GLOBALS, {"TEMPLATES_DIR": tmp_path}):
            app = _fresh_app()
            options, coming_soon = app._get_template_options()

        assert "Creative Marketing ...coming soon" in coming_soon
        assert "Coding" not in coming_soon


# ---------------------------------------------------------------------------
# Tests for App dropdown behaviour
# ---------------------------------------------------------------------------

class TestDropdownDefaultSelection:
    def test_default_template_is_first_ready_option(self, tmp_path: Path):
        """App._current_template should be set to the first ready template."""
        (tmp_path / "coding").mkdir()
        (tmp_path / "coding" / "app.py").write_text("")
        (tmp_path / "creative-marketing").mkdir()
        (tmp_path / "creative-marketing" / "README.md").write_text("")

        with patch.dict(_APP_GLOBALS, {"TEMPLATES_DIR": tmp_path}):
            app = _fresh_app()

        assert app._current_template == "Coding"

    def test_default_does_not_select_coming_soon(self, tmp_path: Path):
        """The default selection must never be a coming-soon item."""
        (tmp_path / "coding").mkdir()
        (tmp_path / "coding" / "app.py").write_text("")
        (tmp_path / "creative-marketing").mkdir()
        (tmp_path / "creative-marketing" / "README.md").write_text("")

        with patch.dict(_APP_GLOBALS, {"TEMPLATES_DIR": tmp_path}):
            app = _fresh_app()

        assert app._current_template not in app._coming_soon_options

    def test_coming_soon_options_set_populated(self, tmp_path: Path):
        """App._coming_soon_options should contain the coming-soon display names."""
        (tmp_path / "coding").mkdir()
        (tmp_path / "coding" / "app.py").write_text("")
        (tmp_path / "creative-marketing").mkdir()
        (tmp_path / "creative-marketing" / "README.md").write_text("")

        with patch.dict(_APP_GLOBALS, {"TEMPLATES_DIR": tmp_path}):
            app = _fresh_app()

        assert "Creative Marketing ...coming soon" in app._coming_soon_options


class TestOnTemplateSelected:
    def test_revert_on_coming_soon_selection(self, tmp_path: Path):
        """Selecting a coming-soon option must revert the dropdown to _current_template."""
        (tmp_path / "coding").mkdir()
        (tmp_path / "coding" / "app.py").write_text("")
        (tmp_path / "creative-marketing").mkdir()
        (tmp_path / "creative-marketing" / "README.md").write_text("")

        with patch.dict(_APP_GLOBALS, {"TEMPLATES_DIR": tmp_path}):
            app = _fresh_app()

        previous = app._current_template  # "Coding"
        app._on_template_selected("Creative Marketing ...coming soon")

        # _current_template must not have changed
        assert app._current_template == previous
        # The dropdown must have been set back to the previous value
        app.project_type_dropdown.set.assert_called_with(previous)

    def test_valid_selection_updates_current_template(self, tmp_path: Path):
        """Selecting a ready template updates _current_template."""
        (tmp_path / "alpha").mkdir()
        (tmp_path / "alpha" / "file.py").write_text("")
        (tmp_path / "beta").mkdir()
        (tmp_path / "beta" / "file.py").write_text("")

        with patch.dict(_APP_GLOBALS, {"TEMPLATES_DIR": tmp_path}):
            app = _fresh_app()

        app._on_template_selected("Beta")
        assert app._current_template == "Beta"

    def test_coming_soon_selection_does_not_update_current_template(self, tmp_path: Path):
        """Selecting a coming-soon option must NOT update _current_template."""
        (tmp_path / "coding").mkdir()
        (tmp_path / "coding" / "app.py").write_text("")
        (tmp_path / "draft").mkdir()
        (tmp_path / "draft" / "README.md").write_text("")

        with patch.dict(_APP_GLOBALS, {"TEMPLATES_DIR": tmp_path}):
            app = _fresh_app()

        original = app._current_template
        app._on_template_selected("Draft ...coming soon")
        assert app._current_template == original


# ---------------------------------------------------------------------------
# Integration: _on_create_project uses _current_template
# ---------------------------------------------------------------------------

class TestCreateProjectUsesCurrentTemplate:
    def test_on_create_project_uses_current_template(self, tmp_path: Path):
        """_on_create_project must use the validated template — never a coming-soon entry."""
        (tmp_path / "coding").mkdir()
        (tmp_path / "coding" / "app.py").write_text("# coding template")
        dest = tmp_path / "dest"
        dest.mkdir()

        with patch.dict(_APP_GLOBALS, {"TEMPLATES_DIR": tmp_path}):
            _CTK_MOCK.reset_mock()
            app = App()

        # Replace shared mock widgets with independent instances (following GUI-005 pattern).
        app.project_name_entry = MagicMock()
        app.project_name_entry.get.return_value = "my-project"
        app.destination_entry = MagicMock()
        app.destination_entry.get.return_value = str(dest)
        app.project_name_error_label = MagicMock()
        app.destination_error_label = MagicMock()
        # Simulate dropdown returning the current (ready) template name.
        app.project_type_dropdown = MagicMock()
        app.project_type_dropdown.get.return_value = app._current_template  # "Coding"

        # _current_template should be "Coding" because coding is ready.
        assert app._current_template == "Coding"

        mock_create = MagicMock(return_value=dest / "my-project")
        # Keep TEMPLATES_DIR patched during the call so the reverse-lookup finds "coding".
        with patch.dict(_APP_GLOBALS, {"TEMPLATES_DIR": tmp_path, "create_project": mock_create}), \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()

        mock_create.assert_called_once()
        called_template_path = mock_create.call_args[0][0]
        assert called_template_path == tmp_path / "coding"
