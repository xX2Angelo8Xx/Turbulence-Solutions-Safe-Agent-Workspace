"""Edge-case tests for GUI-022 — Include README files checkbox.

Covers scenarios the Developer's tests did not exercise:

EC-1  get_setting raises during App init → exception propagates (not silently swallowed)
EC-2  get_setting returns truthy non-bool (1) → BooleanVar initialised True
EC-3  get_setting returns falsy non-bool (0) → BooleanVar initialised False
EC-4  get_setting returns None → BooleanVar initialised False (bool(None) == False)
EC-5  Rapid toggling: two toggle calls with alternating values each persist correctly
EC-6  set_setting raises in _on_include_readmes_toggle → exception propagates
EC-7  create_project kwarg value matches checkbox var exactly (no extra coercion)
EC-8  _on_include_readmes_toggle does NOT call create_project
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

_CTK_MOCK = sys.modules["customtkinter"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_app() -> "App":  # noqa: F821
    """Return a fresh App instance with CTK entirely mocked."""
    _CTK_MOCK.reset_mock()
    from launcher.gui.app import App
    return App()


# ---------------------------------------------------------------------------
# EC-1: get_setting raises during App init
# ---------------------------------------------------------------------------

class TestGetSettingRaises:
    def test_get_setting_raises_propagates_from_init(self) -> None:
        """If get_setting raises, App.__init__ must not silently absorb the error."""
        _CTK_MOCK.reset_mock()
        with patch("launcher.gui.app.get_setting", side_effect=RuntimeError("settings unavailable")):
            from launcher.gui.app import App
            with pytest.raises(RuntimeError, match="settings unavailable"):
                App()


# ---------------------------------------------------------------------------
# EC-2/EC-3/EC-4: Truthy/falsy non-bool values from get_setting
# ---------------------------------------------------------------------------

class TestGetSettingCoercion:
    def test_truthy_int_one_initialises_bool_var_true(self) -> None:
        """get_setting returning 1 must result in BooleanVar(value=True)."""
        bool_var_calls: list = []

        def _capture_bool_var(*args, **kwargs):
            bool_var_calls.append(kwargs)
            m = MagicMock()
            return m

        _CTK_MOCK.reset_mock()
        with patch.object(_CTK_MOCK, "BooleanVar", side_effect=_capture_bool_var), \
             patch("launcher.gui.app.get_setting", return_value=1):
            from launcher.gui.app import App
            App()

        true_calls = [c for c in bool_var_calls if c.get("value") is True]
        assert len(true_calls) >= 1, (
            f"Expected BooleanVar(value=True) for truthy int 1, got: {bool_var_calls}"
        )

    def test_falsy_int_zero_initialises_bool_var_false(self) -> None:
        """get_setting returning 0 must result in BooleanVar(value=False)."""
        bool_var_calls: list = []

        def _capture_bool_var(*args, **kwargs):
            bool_var_calls.append(kwargs)
            m = MagicMock()
            return m

        _CTK_MOCK.reset_mock()
        with patch.object(_CTK_MOCK, "BooleanVar", side_effect=_capture_bool_var), \
             patch("launcher.gui.app.get_setting", return_value=0):
            from launcher.gui.app import App
            App()

        false_calls = [c for c in bool_var_calls if c.get("value") is False]
        assert len(false_calls) >= 1, (
            f"Expected BooleanVar(value=False) for falsy int 0, got: {bool_var_calls}"
        )

    def test_none_from_settings_initialises_bool_var_false(self) -> None:
        """get_setting returning None must result in BooleanVar(value=False)."""
        bool_var_calls: list = []

        def _capture_bool_var(*args, **kwargs):
            bool_var_calls.append(kwargs)
            m = MagicMock()
            return m

        _CTK_MOCK.reset_mock()
        with patch.object(_CTK_MOCK, "BooleanVar", side_effect=_capture_bool_var), \
             patch("launcher.gui.app.get_setting", return_value=None):
            from launcher.gui.app import App
            App()

        false_calls = [c for c in bool_var_calls if c.get("value") is False]
        assert len(false_calls) >= 1, (
            f"Expected BooleanVar(value=False) for None, got: {bool_var_calls}"
        )


# ---------------------------------------------------------------------------
# EC-5: Rapid toggling
# ---------------------------------------------------------------------------

class TestRapidToggling:
    def test_two_toggles_each_call_set_setting(self) -> None:
        """Two consecutive toggle calls must each invoke set_setting with the current var state."""
        app = _fresh_app()

        set_calls: list = []

        def _record_set(key, value):
            set_calls.append((key, value))

        # First toggle → True
        app.include_readmes_var.get.return_value = True
        with patch("launcher.gui.app.set_setting", side_effect=_record_set):
            app._on_include_readmes_toggle()

        # Second toggle → False
        app.include_readmes_var.get.return_value = False
        with patch("launcher.gui.app.set_setting", side_effect=_record_set):
            app._on_include_readmes_toggle()

        assert set_calls == [
            ("include_readmes", True),
            ("include_readmes", False),
        ], f"Unexpected toggle persistence calls: {set_calls}"


# ---------------------------------------------------------------------------
# EC-6: set_setting raises in _on_include_readmes_toggle
# ---------------------------------------------------------------------------

class TestSetSettingRaises:
    def test_set_setting_exception_propagates_from_toggle(self) -> None:
        """If set_setting raises, _on_include_readmes_toggle must NOT silence the error."""
        app = _fresh_app()
        app.include_readmes_var.get.return_value = True
        with patch("launcher.gui.app.set_setting", side_effect=OSError("disk full")):
            with pytest.raises(OSError, match="disk full"):
                app._on_include_readmes_toggle()


# ---------------------------------------------------------------------------
# EC-7: create_project kwarg value is exact bool, not truthy-coerced
# ---------------------------------------------------------------------------

class TestCreateProjectValueIntegrity:
    def test_include_readmes_true_passed_as_exact_bool(self, tmp_path: Path) -> None:
        """The value forwarded to create_project must be the exact outcome of
        include_readmes_var.get() — no extra coercion or negation."""
        from launcher.gui.app import App

        _CTK_MOCK.reset_mock()
        app = App()
        app.project_name_entry = MagicMock()
        app.project_name_entry.get.return_value = "EdgeCaseProject"
        app.project_type_dropdown = MagicMock()
        app.project_type_dropdown.get.return_value = "Agent Workbench"
        app.destination_entry = MagicMock()
        app.destination_entry.get.return_value = str(tmp_path)
        app.project_name_error_label = MagicMock()
        app.destination_error_label = MagicMock()
        app.open_in_vscode_var = MagicMock()
        app.open_in_vscode_var.get.return_value = False
        app.include_readmes_var = MagicMock()
        app.include_readmes_var.get.return_value = True  # exact bool True
        app.counter_enabled_var = MagicMock()
        app.counter_enabled_var.get.return_value = True
        app.counter_threshold_var = MagicMock()
        app.counter_threshold_var.get.return_value = "20"

        created = tmp_path / "SAE-EdgeCaseProject"

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]), \
             patch("launcher.gui.app.create_project", return_value=created) as mock_create, \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()

        _, kwargs = mock_create.call_args
        assert kwargs.get("include_readmes") is True, (
            f"Expected include_readmes=True (exact bool), got: {kwargs.get('include_readmes')!r}"
        )


# ---------------------------------------------------------------------------
# EC-8: _on_include_readmes_toggle does NOT trigger project creation
# ---------------------------------------------------------------------------

class TestToggleDoesNotCreateProject:
    def test_toggle_does_not_call_create_project(self) -> None:
        """Toggling the checkbox must only persist the setting, never create a project."""
        app = _fresh_app()
        app.include_readmes_var.get.return_value = False

        with patch("launcher.gui.app.set_setting"), \
             patch("launcher.gui.app.create_project") as mock_create:
            app._on_include_readmes_toggle()

        mock_create.assert_not_called()
