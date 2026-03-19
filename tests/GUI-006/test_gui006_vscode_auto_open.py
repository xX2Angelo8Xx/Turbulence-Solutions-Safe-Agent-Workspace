"""Tests for GUI-006: VS Code Auto-Open.

Covers all acceptance criteria from US-006:
  AC-1: UI has an "Open in VS Code" checkbox (existence check).
  AC-2: If checked, VS Code opens the new project folder on successful creation.
  AC-3: Checkbox is disabled/greyed out if VS Code is not detected.

Additional paths tested:
  - open_in_vscode NOT called when checkbox is unchecked.
  - open_in_vscode NOT called when project creation fails.
  - Checkbox stays enabled (default) when VS Code is detected.

All App tests run headlessly by replacing `customtkinter` with a MagicMock
in sys.modules before any launcher.gui module is imported.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Use the shared customtkinter mock installed by conftest.py.
# ---------------------------------------------------------------------------
_CTK_MOCK = sys.modules["customtkinter"]

from launcher.gui.app import App  # noqa: E402


# ---------------------------------------------------------------------------
# Helper – build a minimal App instance with independent widget mocks.
# ---------------------------------------------------------------------------

def _make_app(
    project_name: str = "my-project",
    template_display: str = "Coding",
    destination: str = "",
    vscode_path: str | None = "/usr/bin/code",
    vscode_checked: bool = True,
) -> App:
    """Return a fresh App with mocked widgets.

    `vscode_path` controls what `find_vscode` returns during `_build_ui`.
    `vscode_checked` controls the checkbox BooleanVar get() return value.
    """
    _CTK_MOCK.reset_mock()
    with patch("launcher.gui.app.find_vscode", return_value=vscode_path):
        app = App()

    # Replace shared mock widgets with independent ones.
    app.project_name_entry = MagicMock()
    app.project_name_entry.get.return_value = project_name
    app.project_type_dropdown = MagicMock()
    app.project_type_dropdown.get.return_value = template_display
    app.destination_entry = MagicMock()
    app.destination_entry.get.return_value = destination
    app.project_name_error_label = MagicMock()
    app.destination_error_label = MagicMock()
    app.open_in_vscode_var = MagicMock()
    app.open_in_vscode_var.get.return_value = vscode_checked
    app.open_in_vscode_checkbox = MagicMock()
    return app


# ---------------------------------------------------------------------------
# AC-1: Checkbox existence
# ---------------------------------------------------------------------------

class TestVSCodeCheckboxExists:
    def test_open_in_vscode_checkbox_attribute_exists(self):
        _CTK_MOCK.reset_mock()
        with patch("launcher.gui.app.find_vscode", return_value="/usr/bin/code"):
            app = App()
        assert hasattr(app, "open_in_vscode_checkbox")

    def test_open_in_vscode_var_attribute_exists(self):
        _CTK_MOCK.reset_mock()
        with patch("launcher.gui.app.find_vscode", return_value="/usr/bin/code"):
            app = App()
        assert hasattr(app, "open_in_vscode_var")


# ---------------------------------------------------------------------------
# AC-3: Checkbox disabled when VS Code is not found
# ---------------------------------------------------------------------------

class TestVSCodeCheckboxDisabledWhenNotFound:
    def test_checkbox_disabled_when_find_vscode_returns_none(self):
        """When find_vscode() returns None, the checkbox must be disabled."""
        _CTK_MOCK.reset_mock()
        with patch("launcher.gui.app.find_vscode", return_value=None) as mock_find:
            app = App()
        app.open_in_vscode_checkbox.configure.assert_any_call(state="disabled")

    def test_checkbox_var_set_false_when_find_vscode_returns_none(self):
        """When find_vscode() returns None, the checkbox BooleanVar is set to False."""
        _CTK_MOCK.reset_mock()
        with patch("launcher.gui.app.find_vscode", return_value=None):
            app = App()
        app.open_in_vscode_var.set.assert_called_with(False)

    def test_find_vscode_called_during_build_ui(self):
        """find_vscode must be called during UI construction."""
        _CTK_MOCK.reset_mock()
        with patch("launcher.gui.app.find_vscode", return_value=None) as mock_find:
            App()
        mock_find.assert_called_once()


# ---------------------------------------------------------------------------
# AC-3: Checkbox stays enabled when VS Code IS found
# ---------------------------------------------------------------------------

class TestVSCodeCheckboxEnabledWhenFound:
    def test_checkbox_not_disabled_when_find_vscode_returns_path(self):
        """When VS Code is found, the checkbox must NOT be configured to 'disabled'."""
        _CTK_MOCK.reset_mock()
        with patch("launcher.gui.app.find_vscode", return_value="/usr/bin/code"):
            app = App()
        disabled_calls = [
            c for c in app.open_in_vscode_checkbox.configure.call_args_list
            if c == ((), {"state": "disabled"})
        ]
        assert len(disabled_calls) == 0

    def test_var_not_forced_false_when_find_vscode_returns_path(self):
        """When VS Code is found, the BooleanVar must NOT be forced to False."""
        _CTK_MOCK.reset_mock()
        with patch("launcher.gui.app.find_vscode", return_value="/usr/bin/code"):
            app = App()
        false_calls = [
            c for c in app.open_in_vscode_var.set.call_args_list
            if c == ((False,), {})
        ]
        assert len(false_calls) == 0


# ---------------------------------------------------------------------------
# AC-2: open_in_vscode called on successful creation when checkbox is checked
# ---------------------------------------------------------------------------

class TestOpenInVSCodeCalledOnSuccess:
    def test_open_in_vscode_called_when_checked(self, tmp_path):
        """open_in_vscode must be called with the created path when checkbox is checked."""
        created = tmp_path / "my-project"
        app = _make_app(
            project_name="my-project",
            destination=str(tmp_path),
            vscode_checked=True,
        )
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=created), \
             patch("launcher.gui.app.messagebox"), \
             patch("launcher.gui.app.open_in_vscode") as mock_open:
            app._on_create_project()
        mock_open.assert_called_once_with(created)

    def test_open_in_vscode_called_with_correct_path(self, tmp_path):
        """open_in_vscode must receive the exact Path returned by create_project."""
        expected_path = tmp_path / "test-project"
        app = _make_app(
            project_name="test-project",
            destination=str(tmp_path),
            vscode_checked=True,
        )
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=expected_path), \
             patch("launcher.gui.app.messagebox"), \
             patch("launcher.gui.app.open_in_vscode") as mock_open:
            app._on_create_project()
        mock_open.assert_called_once_with(expected_path)


# ---------------------------------------------------------------------------
# open_in_vscode NOT called when checkbox is unchecked
# ---------------------------------------------------------------------------

class TestOpenInVSCodeNotCalledWhenUnchecked:
    def test_open_in_vscode_not_called_when_unchecked(self, tmp_path):
        """When the checkbox is unchecked, open_in_vscode must not be called."""
        created = tmp_path / "my-project"
        app = _make_app(
            project_name="my-project",
            destination=str(tmp_path),
            vscode_checked=False,
        )
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=created), \
             patch("launcher.gui.app.messagebox"), \
             patch("launcher.gui.app.open_in_vscode") as mock_open:
            app._on_create_project()
        mock_open.assert_not_called()


# ---------------------------------------------------------------------------
# open_in_vscode NOT called when project creation fails
# ---------------------------------------------------------------------------

class TestOpenInVSCodeNotCalledOnFailure:
    def test_not_called_when_create_project_raises(self, tmp_path):
        """If create_project raises, open_in_vscode must not be called."""
        app = _make_app(
            project_name="my-project",
            destination=str(tmp_path),
            vscode_checked=True,
        )
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", side_effect=OSError("disk full")), \
             patch("launcher.gui.app.messagebox"), \
             patch("launcher.gui.app.open_in_vscode") as mock_open:
            app._on_create_project()
        mock_open.assert_not_called()

    def test_not_called_when_name_validation_fails(self, tmp_path):
        """If name validation fails, open_in_vscode must not be called."""
        app = _make_app(
            project_name="",
            destination=str(tmp_path),
            vscode_checked=True,
        )
        with patch("launcher.gui.app.validate_folder_name", return_value=(False, "empty")), \
             patch("launcher.gui.app.open_in_vscode") as mock_open:
            app._on_create_project()
        mock_open.assert_not_called()

    def test_not_called_when_destination_validation_fails(self, tmp_path):
        """If destination validation fails, open_in_vscode must not be called."""
        app = _make_app(
            project_name="valid",
            destination="/nonexistent",
            vscode_checked=True,
        )
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(False, "bad path")), \
             patch("launcher.gui.app.open_in_vscode") as mock_open:
            app._on_create_project()
        mock_open.assert_not_called()

    def test_not_called_when_template_not_found(self, tmp_path):
        """If the template cannot be resolved, open_in_vscode must not be called."""
        app = _make_app(
            project_name="valid",
            destination=str(tmp_path),
            template_display="Unknown Template",
            vscode_checked=True,
        )
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.messagebox"), \
             patch("launcher.gui.app.open_in_vscode") as mock_open:
            app._on_create_project()
        mock_open.assert_not_called()
