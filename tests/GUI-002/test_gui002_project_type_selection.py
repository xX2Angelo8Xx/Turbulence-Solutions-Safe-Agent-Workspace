"""Tests for GUI-002: Project Type Selection.

All tests run headlessly by replacing ``customtkinter`` with a MagicMock in
``sys.modules`` before the modules under test are imported.  No display
connection is attempted, so the suite runs on all platforms including
headless CI environments.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# customtkinter is already mocked by tests/conftest.py — reuse that mock.
# ---------------------------------------------------------------------------
_CTK_MOCK = sys.modules["customtkinter"]

from launcher.gui.app import App, _format_template_name  # noqa: E402
from launcher.core.project_creator import list_templates  # noqa: E402
import launcher.config as launcher_config  # noqa: E402

# Grab the actual globals dict where App._get_template_options looks up names.
# This avoids module-identity issues that arise when pytest collects multiple
# test files that each reimport launcher.gui.app.
_APP_GLOBALS = App._get_template_options.__globals__


def _mock_list_templates(names: list[str]):
    """Return a context manager that injects a fake list_templates into App''s module."""
    return patch.dict(_APP_GLOBALS, {"list_templates": MagicMock(return_value=names)})


# ---------------------------------------------------------------------------
# _format_template_name
# ---------------------------------------------------------------------------

class TestFormatTemplateName:
    def test_single_word_capitalised(self):
        assert _format_template_name("coding") == "Coding"

    def test_hyphenated_to_title_case(self):
        assert _format_template_name("certification-pipeline") == "Certification Pipeline"

    def test_underscore_separator(self):
        assert _format_template_name("data_science") == "Data Science"

    def test_mixed_hyphen_and_underscore(self):
        assert _format_template_name("my-data_project") == "My Data Project"

    def test_empty_string(self):
        assert _format_template_name("") == ""

    def test_already_title_case(self):
        # Already correct case is preserved.
        assert _format_template_name("Coding") == "Coding"

    def test_all_caps(self):
        assert _format_template_name("CODING") == "Coding"


# ---------------------------------------------------------------------------
# App._get_template_options — using mocked list_templates for isolation
# ---------------------------------------------------------------------------

class TestGetTemplateOptions:
    def _app(self) -> App:
        _CTK_MOCK.reset_mock()
        return App()

    def test_returns_list(self):
        with _mock_list_templates(["agent-workbench"]):
            assert isinstance(self._app()._get_template_options(), list)

    def test_with_two_subdirs(self):
        with _mock_list_templates(["agent-workbench", "certification-pipeline"]):
            result = self._app()._get_template_options()
        # coding is ready; creative-marketing only has README.md so gets ' ...coming soon'
        assert "Agent Workbench" in result
        assert any("Certification Pipeline" in entry for entry in result)

    def test_with_single_subdir(self):
        with _mock_list_templates(["agent-workbench"]):
            result = self._app()._get_template_options()
        assert result == ["Agent Workbench"]

    def test_empty_list_returns_empty_list(self):
        with _mock_list_templates([]):
            result = self._app()._get_template_options()
        assert result == []

    def test_files_are_not_included_only_dirs(self):
        # list_templates itself filters files; here we verify that _get_template_options
        # passes through exactly what list_templates returns (no extra filtering).
        with _mock_list_templates(["agent-workbench"]):
            result = self._app()._get_template_options()
        assert result == ["Agent Workbench"]

    def test_results_preserve_order_from_list_templates(self):
        with _mock_list_templates(["aaa-first", "mmm-middle", "zzz-last"]):
            result = self._app()._get_template_options()
        # Order must be preserved; fake names don't exist so they get ' ...coming soon'.
        display_names = [entry.replace(" ...coming soon", "") for entry in result]
        assert display_names == ["Aaa First", "Mmm Middle", "Zzz Last"]


# ---------------------------------------------------------------------------
# list_templates integration (tests on real temp dirs to verify filtering)
# ---------------------------------------------------------------------------

class TestListTemplatesIntegration:
    def test_returns_only_subdirectory_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            (tmpdir / "coding").mkdir()
            (tmpdir / "certification-pipeline").mkdir()
            result = list_templates(tmpdir)
        assert result == ["certification-pipeline", "coding"]

    def test_files_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            (tmpdir / "coding").mkdir()
            (tmpdir / "readme.txt").write_text("not a template")
            result = list_templates(tmpdir)
        assert result == ["coding"]

    def test_empty_dir_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = list_templates(Path(tmp))
        assert result == []

    def test_missing_dir_returns_empty_list(self):
        result = list_templates(Path("/nonexistent/path/does/not/exist"))
        assert result == []

    def test_results_are_sorted_alphabetically(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            (tmpdir / "zzz-last").mkdir()
            (tmpdir / "aaa-first").mkdir()
            result = list_templates(tmpdir)
        assert result == ["aaa-first", "zzz-last"]


# ---------------------------------------------------------------------------
# Dynamic loading integration tests
# ---------------------------------------------------------------------------

class TestDropdownDynamicLoading:
    def test_dropdown_created_with_values_from_get_template_options(self):
        """CTkOptionMenu must be called with the list returned by _get_template_options."""
        _CTK_MOCK.reset_mock()
        with _mock_list_templates(["agent-workbench", "certification-pipeline"]):
            App()
        call_kwargs = _CTK_MOCK.CTkOptionMenu.call_args
        values_arg = call_kwargs[1].get("values") or call_kwargs[0][1]
        assert "Agent Workbench" in values_arg
        # creative-marketing only has README.md → shown with coming-soon label
        assert any("Certification Pipeline" in v for v in values_arg)

    def test_adding_new_template_dir_changes_options(self):
        """A new subdirectory injected into list_templates output appears in options."""
        _CTK_MOCK.reset_mock()
        with _mock_list_templates(["agent-workbench"]):
            before = App()._get_template_options()
        assert before == ["Agent Workbench"]

        _CTK_MOCK.reset_mock()
        with _mock_list_templates(["agent-workbench", "data-science"]):
            after = App()._get_template_options()
        assert any("Data Science" in entry for entry in after)

    def test_dropdown_values_not_hardcoded(self):
        """With a custom list_templates result, dropdown changes — proving it is dynamic."""
        _CTK_MOCK.reset_mock()
        with _mock_list_templates(["my-custom-type"]):
            result = App()._get_template_options()
        # Custom name doesn't exist in real TEMPLATES_DIR → is_template_ready returns
        # False → displayed with coming-soon label; base name must still appear.
        assert any("My Custom Type" in entry for entry in result)


# ---------------------------------------------------------------------------
# Filesystem presence
# ---------------------------------------------------------------------------

class TestTemplateDirPresence:
    def test_creative_marketing_dir_exists(self):
        """templates/creative-marketing/ must exist in the repository."""
        templates_dir = launcher_config.TEMPLATES_DIR
        creative = templates_dir / "certification-pipeline"
        assert creative.is_dir(), (
            f"Expected templates/creative-marketing/ to exist at {creative}"
        )

    def test_coding_dir_exists(self):
        """templates/agent-workbench/ must exist in the repository."""
        templates_dir = launcher_config.TEMPLATES_DIR
        coding = templates_dir / "agent-workbench"
        assert coding.is_dir(), (
            f"Expected templates/coding/ to exist at {coding}"
        )

    def test_real_templates_dir_options_contain_coding(self):
        """_get_template_options() with the real templates dir includes ''Coding''."""
        _CTK_MOCK.reset_mock()
        result = App()._get_template_options()
        assert "Agent Workbench" in result

    def test_real_templates_dir_options_contain_creative_marketing(self):
        """_get_template_options() with the real templates dir includes a ''Creative Marketing'' entry."""
        _CTK_MOCK.reset_mock()
        result = App()._get_template_options()
        # creative-marketing only has README.md so it gets a ' ...coming soon' label.
        assert any("Certification Pipeline" in option for option in result)


# ---------------------------------------------------------------------------
# Tester edge-case additions (TST-506 – TST-511)
# ---------------------------------------------------------------------------

class TestTesterEdgeCases:
    """Additional edge-case tests added by the Tester Agent."""

    # --- _format_template_name edge cases ---

    def test_format_template_name_unicode_chars(self):
        """Unicode characters in dir names round-trip through the formatter."""
        # "café-design" → replace "-" → "café design" → .title() → "Café Design"
        result = _format_template_name("café-design")
        assert result == "Café Design"

    def test_format_template_name_numbers_prefix(self):
        """Digits followed by letters: '3' is non-cased so next letter is capitalised."""
        # "3d-modeling" → "3d modeling" → .title() → "3D Modeling"
        result = _format_template_name("3d-modeling")
        assert result == "3D Modeling"

    def test_format_template_name_only_hyphens(self):
        """A name consisting entirely of hyphens converts to spaces only."""
        result = _format_template_name("---")
        assert result == "   "

    def test_format_template_name_leading_dot(self):
        """Dotfile-style names: '.' is non-cased so the following letter is capitalised."""
        result = _format_template_name(".hidden")
        assert result == ".Hidden"

    # --- list_templates boundary/type-guard edge cases ---

    def test_list_templates_file_path_returns_empty_list(self):
        """Passing a Path that points to a file (not a dir) returns empty list."""
        with tempfile.NamedTemporaryFile() as tmp:
            result = list_templates(Path(tmp.name))
        assert result == []

    def test_list_templates_string_argument_returns_empty_list(self):
        """Passing a plain str instead of Path is rejected and returns empty list."""
        with tempfile.TemporaryDirectory() as tmp:
            result = list_templates(tmp)  # type: ignore[arg-type]
        assert result == []