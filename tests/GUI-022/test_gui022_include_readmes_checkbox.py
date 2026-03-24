"""Tests for GUI-022 — Include README files checkbox in the launcher.

Covers:
1. include_readmes_checkbox attribute exists on App after _build_ui
2. include_readmes_var attribute exists on App after _build_ui
3. Checkbox BooleanVar is created with value=True by default
4. Checkbox restores True when get_setting returns True
5. Checkbox restores False when get_setting returns False
6. _on_include_readmes_toggle persists True via set_setting
7. _on_include_readmes_toggle persists False via set_setting
8. _on_create_project passes include_readmes=True to create_project
9. _on_create_project passes include_readmes=False to create_project
10. create_project() accepts include_readmes parameter without raising
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

_CTK_MOCK = sys.modules["customtkinter"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app() -> "App":  # noqa: F821
    """Return a fresh App instance with all widgets mocked."""
    from launcher.gui.app import App
    _CTK_MOCK.reset_mock()
    return App()


def _make_app_with_include_readmes(include_readmes: bool, project_name: str = "Demo",
                                   destination: str = "/tmp", template: str = "Coding") -> "App":  # noqa: F821
    """Return an App with all controls wired up for _on_create_project testing."""
    from launcher.gui.app import App
    _CTK_MOCK.reset_mock()
    app = App()
    app.project_name_entry = MagicMock()
    app.project_name_entry.get.return_value = project_name
    app.project_type_dropdown = MagicMock()
    app.project_type_dropdown.get.return_value = template
    app.destination_entry = MagicMock()
    app.destination_entry.get.return_value = destination
    app.project_name_error_label = MagicMock()
    app.destination_error_label = MagicMock()
    app.open_in_vscode_var = MagicMock()
    app.open_in_vscode_var.get.return_value = False
    app.include_readmes_var = MagicMock()
    app.include_readmes_var.get.return_value = include_readmes
    app.counter_enabled_var = MagicMock()
    app.counter_enabled_var.get.return_value = True
    app.counter_threshold_var = MagicMock()
    app.counter_threshold_var.get.return_value = "20"
    return app


# ---------------------------------------------------------------------------
# Tests: attribute existence
# ---------------------------------------------------------------------------

class TestIncludeReadmesAttributes:
    def test_include_readmes_checkbox_attribute_exists(self) -> None:
        """App must have an include_readmes_checkbox attribute after _build_ui."""
        app = _make_app()
        assert hasattr(app, "include_readmes_checkbox"), (
            "App is missing 'include_readmes_checkbox'"
        )

    def test_include_readmes_var_attribute_exists(self) -> None:
        """App must have an include_readmes_var attribute after _build_ui."""
        app = _make_app()
        assert hasattr(app, "include_readmes_var"), (
            "App is missing 'include_readmes_var'"
        )


# ---------------------------------------------------------------------------
# Tests: default value and settings restore
# ---------------------------------------------------------------------------

class TestIncludeReadmesDefaults:
    def test_include_readmes_var_defaults_to_true(self) -> None:
        """include_readmes_var must be created with value=True when settings returns True."""
        bool_var_calls: list = []

        def _capture_bool_var(*args, **kwargs):
            bool_var_calls.append(kwargs)
            m = MagicMock()
            m._init_kwargs = kwargs
            return m

        _CTK_MOCK.reset_mock()
        with patch.object(_CTK_MOCK, "BooleanVar", side_effect=_capture_bool_var), \
             patch("launcher.gui.app.get_setting", return_value=True):
            from launcher.gui.app import App
            App()

        # At least one BooleanVar must have been created with value=True
        true_calls = [c for c in bool_var_calls if c.get("value") is True]
        assert len(true_calls) >= 1, (
            f"Expected at least one BooleanVar(value=True) call, got: {bool_var_calls}"
        )

    def test_include_readmes_var_restored_false_from_settings(self) -> None:
        """include_readmes_var must be created with value=False when settings returns False."""
        bool_var_calls: list = []

        def _capture_bool_var(*args, **kwargs):
            bool_var_calls.append(kwargs)
            m = MagicMock()
            m._init_kwargs = kwargs
            return m

        _CTK_MOCK.reset_mock()
        with patch.object(_CTK_MOCK, "BooleanVar", side_effect=_capture_bool_var), \
             patch("launcher.gui.app.get_setting", return_value=False):
            from launcher.gui.app import App
            App()

        # One BooleanVar must have been created with value=False
        false_calls = [c for c in bool_var_calls if c.get("value") is False]
        assert len(false_calls) >= 1, (
            f"Expected at least one BooleanVar(value=False) call, got: {bool_var_calls}"
        )

    def test_get_setting_called_with_include_readmes_key(self) -> None:
        """App.__init__ must call get_setting('include_readmes', True) during build."""
        _CTK_MOCK.reset_mock()
        with patch("launcher.gui.app.get_setting", return_value=True) as mock_get:
            from launcher.gui.app import App
            App()
        # Verify that get_setting was called with 'include_readmes' as first arg.
        include_readmes_calls = [
            c for c in mock_get.call_args_list
            if c.args and c.args[0] == "include_readmes"
        ]
        assert len(include_readmes_calls) >= 1, (
            f"get_setting('include_readmes', ...) was not called. "
            f"All calls: {mock_get.call_args_list}"
        )


# ---------------------------------------------------------------------------
# Tests: _on_include_readmes_toggle persists state
# ---------------------------------------------------------------------------

class TestIncludeReadmesTogglePersistence:
    def test_toggle_to_true_calls_set_setting_with_true(self) -> None:
        """_on_include_readmes_toggle must call set_setting('include_readmes', True)."""
        app = _make_app()
        app.include_readmes_var.get.return_value = True
        with patch("launcher.gui.app.set_setting") as mock_set:
            app._on_include_readmes_toggle()
        mock_set.assert_called_once_with("include_readmes", True)

    def test_toggle_to_false_calls_set_setting_with_false(self) -> None:
        """_on_include_readmes_toggle must call set_setting('include_readmes', False)."""
        app = _make_app()
        app.include_readmes_var.get.return_value = False
        with patch("launcher.gui.app.set_setting") as mock_set:
            app._on_include_readmes_toggle()
        mock_set.assert_called_once_with("include_readmes", False)


# ---------------------------------------------------------------------------
# Tests: _on_create_project passes include_readmes to create_project
# ---------------------------------------------------------------------------

class TestCreateProjectReceivesIncludeReadmes:
    def test_create_project_receives_include_readmes_true(self, tmp_path: Path) -> None:
        """_on_create_project must pass include_readmes=True to create_project."""
        app = _make_app_with_include_readmes(
            include_readmes=True,
            project_name="DemoProject",
            destination=str(tmp_path),
            template="Coding",
        )
        created = tmp_path / "TS-SAE-DemoProject"

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=created) as mock_create, \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()

        assert mock_create.called, "create_project was not called"
        _, kwargs = mock_create.call_args
        assert "include_readmes" in kwargs, (
            f"include_readmes kwarg missing from create_project call. "
            f"kwargs={kwargs}"
        )
        assert kwargs["include_readmes"] is True

    def test_create_project_receives_include_readmes_false(self, tmp_path: Path) -> None:
        """_on_create_project must pass include_readmes=False to create_project."""
        app = _make_app_with_include_readmes(
            include_readmes=False,
            project_name="DemoProject",
            destination=str(tmp_path),
            template="Coding",
        )
        created = tmp_path / "TS-SAE-DemoProject"

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=created) as mock_create, \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()

        assert mock_create.called, "create_project was not called"
        _, kwargs = mock_create.call_args
        assert "include_readmes" in kwargs, (
            f"include_readmes kwarg missing from create_project call. "
            f"kwargs={kwargs}"
        )
        assert kwargs["include_readmes"] is False


# ---------------------------------------------------------------------------
# Tests: create_project() stub parameter (project_creator.py)
# ---------------------------------------------------------------------------

class TestCreateProjectStubParam:
    def test_create_project_accepts_include_readmes_true(self, tmp_path: Path) -> None:
        """create_project() must accept include_readmes=True without raising."""
        from launcher.core.project_creator import create_project

        template_dir = tmp_path / "template"
        template_dir.mkdir()
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        result = create_project(
            template_dir, dest_dir, "MyProject", include_readmes=True
        )
        assert result.name == "TS-SAE-MyProject"

    def test_create_project_accepts_include_readmes_false(self, tmp_path: Path) -> None:
        """create_project() must accept include_readmes=False without raising."""
        from launcher.core.project_creator import create_project

        template_dir = tmp_path / "template2"
        template_dir.mkdir()
        dest_dir = tmp_path / "dest2"
        dest_dir.mkdir()

        # include_readmes=False is accepted; actual deletion is INS-023's scope.
        result = create_project(
            template_dir, dest_dir, "MyProject2", include_readmes=False
        )
        assert result.name == "TS-SAE-MyProject2"

    def test_create_project_include_readmes_default_is_true(self, tmp_path: Path) -> None:
        """create_project() default for include_readmes must be True."""
        import inspect
        from launcher.core.project_creator import create_project

        sig = inspect.signature(create_project)
        param = sig.parameters.get("include_readmes")
        assert param is not None, "create_project must have an include_readmes parameter"
        assert param.default is True, (
            f"include_readmes default must be True, got: {param.default}"
        )
