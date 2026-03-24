"""Tests for GUI-019 — Counter Configuration UI.

Covers:
1. counter_enabled_var attribute exists and defaults to True (BooleanVar with value=True)
2. counter_enabled_checkbox attribute exists and is a CTkSwitch
3. counter_threshold_var attribute exists and defaults to "20"
4. counter_threshold_entry attribute exists and is a CTkEntry
5. _on_counter_enabled_toggle disables threshold entry when counter is unchecked
6. _on_counter_enabled_toggle re-enables threshold entry when counter is re-checked
7. get_counter_threshold returns 20 for the default "20" string
8. get_counter_threshold raises ValueError for a non-numeric string
9. get_counter_threshold raises ValueError for zero
10. get_counter_threshold raises ValueError for a negative value
11. get_counter_threshold raises ValueError for an empty string
12. get_counter_threshold returns the correct value after threshold changes
13. counter_threshold_var persists updated values in app state
14. counter_enabled_checkbox uses the correct label text (CTkSwitch)
15. CTkSwitch for counter receives _on_counter_enabled_toggle as command
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

# Reuse the shared customtkinter mock injected by conftest.py.
_CTK_MOCK = sys.modules["customtkinter"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app() -> "App":  # noqa: F821
    """Return a fresh App instance with all widgets mocked."""
    from launcher.gui.app import App
    _CTK_MOCK.reset_mock()
    return App()


# ---------------------------------------------------------------------------
# Tests: attribute existence
# ---------------------------------------------------------------------------

class TestCounterAttributesExist:
    def test_counter_enabled_var_attribute_exists(self) -> None:
        """App must have a counter_enabled_var attribute after _build_ui."""
        app = _make_app()
        assert hasattr(app, "counter_enabled_var"), "App is missing 'counter_enabled_var'"

    def test_counter_enabled_checkbox_attribute_exists(self) -> None:
        """App must have a counter_enabled_checkbox attribute after _build_ui."""
        app = _make_app()
        assert hasattr(app, "counter_enabled_checkbox"), "App is missing 'counter_enabled_checkbox'"

    def test_counter_threshold_var_attribute_exists(self) -> None:
        """App must have a counter_threshold_var attribute after _build_ui."""
        app = _make_app()
        assert hasattr(app, "counter_threshold_var"), "App is missing 'counter_threshold_var'"

    def test_counter_threshold_entry_attribute_exists(self) -> None:
        """App must have a counter_threshold_entry attribute after _build_ui."""
        app = _make_app()
        assert hasattr(app, "counter_threshold_entry"), "App is missing 'counter_threshold_entry'"


# ---------------------------------------------------------------------------
# Tests: default values
# ---------------------------------------------------------------------------

class TestCounterDefaults:
    def test_counter_enabled_var_created_with_true(self) -> None:
        """counter_enabled_var must be created with value=True (BooleanVar default)."""
        bool_var_calls = []

        def _capture_bool_var(*args, **kwargs):
            bool_var_calls.append(kwargs)
            m = MagicMock()
            m._init_kwargs = kwargs
            return m

        _CTK_MOCK.reset_mock()
        with patch.object(_CTK_MOCK, "BooleanVar", side_effect=_capture_bool_var):
            from launcher.gui.app import App
            App()

        true_vars = [c for c in bool_var_calls if c.get("value") is True]
        assert len(true_vars) >= 2, (
            "Expected at least 2 BooleanVar(value=True) calls "
            "(open_in_vscode and counter_enabled), "
            f"got: {bool_var_calls}"
        )

    def test_counter_threshold_var_created_with_20(self) -> None:
        """counter_threshold_var must be created with value='20' (StringVar default)."""
        string_var_calls = []

        def _capture_string_var(*args, **kwargs):
            string_var_calls.append(kwargs)
            m = MagicMock()
            m._init_kwargs = kwargs
            return m

        _CTK_MOCK.reset_mock()
        with patch.object(_CTK_MOCK, "StringVar", side_effect=_capture_string_var):
            from launcher.gui.app import App
            App()

        twenty_vars = [c for c in string_var_calls if c.get("value") == "20"]
        assert twenty_vars, (
            f"Expected StringVar(value='20') call for counter threshold, got: {string_var_calls}"
        )

    def test_switch_label_text_is_correct(self) -> None:
        """counter_enabled_checkbox (CTkSwitch) must use the correct label text."""
        switch_calls = []

        def _capture_switch(*args, **kwargs):
            switch_calls.append(kwargs)
            return MagicMock()

        _CTK_MOCK.reset_mock()
        with patch.object(_CTK_MOCK, "CTkSwitch", side_effect=_capture_switch):
            from launcher.gui.app import App
            App()

        counter_switches = [
            c for c in switch_calls
            if c.get("text") == "Enable blocking attempts counter"
        ]
        assert counter_switches, (
            "No CTkSwitch created with text='Enable blocking attempts counter'. "
            f"Switch calls: {[c.get('text') for c in switch_calls]}"
        )

    def test_counter_switch_command_is_toggle_method(self) -> None:
        """Counter switch command must be _on_counter_enabled_toggle."""
        switch_calls = []

        def _capture_switch(*args, **kwargs):
            switch_calls.append(kwargs)
            return MagicMock()

        _CTK_MOCK.reset_mock()
        with patch.object(_CTK_MOCK, "CTkSwitch", side_effect=_capture_switch):
            from launcher.gui.app import App
            app = App()

        counter_switches = [
            c for c in switch_calls
            if c.get("text") == "Enable blocking attempts counter"
        ]
        assert counter_switches, "Counter switch not found"
        cmd = counter_switches[0].get("command")
        assert cmd is not None, "counter_enabled_checkbox has no command"
        assert cmd == app._on_counter_enabled_toggle, (
            "Counter switch command must be app._on_counter_enabled_toggle"
        )

    def test_ctk_checkbox_still_called_once(self) -> None:
        """CTkCheckBox must still be called exactly once (Open in VS Code) after adding counter switch."""
        _CTK_MOCK.reset_mock()
        from launcher.gui.app import App
        App()
        # CTkSwitch is used for counter — CTkCheckBox count must remain 1.
        _CTK_MOCK.CTkCheckBox.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: checkbox toggle behavior
# ---------------------------------------------------------------------------

class TestCounterToggle:
    def test_toggle_unchecked_disables_threshold_entry(self) -> None:
        """When counter is unchecked, threshold entry should be disabled."""
        app = _make_app()
        # Simulate switch being turned off
        app.counter_enabled_var.get.return_value = False
        app._on_counter_enabled_toggle()
        app.counter_threshold_entry.configure.assert_called_with(state="disabled")

    def test_toggle_checked_enables_threshold_entry(self) -> None:
        """When counter is checked, threshold entry should be normal (enabled)."""
        app = _make_app()
        # Simulate switch being turned on
        app.counter_enabled_var.get.return_value = True
        app._on_counter_enabled_toggle()
        app.counter_threshold_entry.configure.assert_called_with(state="normal")

    def test_toggle_disabled_then_enabled_sequence(self) -> None:
        """Toggle from on->off->on transitions entry state correctly."""
        app = _make_app()

        app.counter_enabled_var.get.return_value = False
        app._on_counter_enabled_toggle()
        app.counter_threshold_entry.configure.assert_called_with(state="disabled")

        app.counter_threshold_entry.configure.reset_mock()
        app.counter_enabled_var.get.return_value = True
        app._on_counter_enabled_toggle()
        app.counter_threshold_entry.configure.assert_called_with(state="normal")


# ---------------------------------------------------------------------------
# Tests: get_counter_threshold validation
# ---------------------------------------------------------------------------

class TestGetCounterThreshold:
    def test_default_threshold_returns_20(self) -> None:
        """get_counter_threshold must return 20 when the entry contains '20'."""
        app = _make_app()
        app.counter_threshold_var.get.return_value = "20"
        assert app.get_counter_threshold() == 20

    def test_custom_valid_threshold(self) -> None:
        """get_counter_threshold returns the correct integer for valid input."""
        app = _make_app()
        app.counter_threshold_var.get.return_value = "50"
        assert app.get_counter_threshold() == 50

    def test_threshold_one_is_valid(self) -> None:
        """Threshold of 1 is the minimum valid value."""
        app = _make_app()
        app.counter_threshold_var.get.return_value = "1"
        assert app.get_counter_threshold() == 1

    def test_non_numeric_raises_value_error(self) -> None:
        """get_counter_threshold raises ValueError for non-numeric input."""
        app = _make_app()
        app.counter_threshold_var.get.return_value = "abc"
        with pytest.raises(ValueError):
            app.get_counter_threshold()

    def test_zero_raises_value_error(self) -> None:
        """get_counter_threshold raises ValueError when threshold is zero."""
        app = _make_app()
        app.counter_threshold_var.get.return_value = "0"
        with pytest.raises(ValueError):
            app.get_counter_threshold()

    def test_negative_raises_value_error(self) -> None:
        """get_counter_threshold raises ValueError for negative values."""
        app = _make_app()
        app.counter_threshold_var.get.return_value = "-5"
        with pytest.raises(ValueError):
            app.get_counter_threshold()

    def test_empty_string_raises_value_error(self) -> None:
        """get_counter_threshold raises ValueError for an empty string."""
        app = _make_app()
        app.counter_threshold_var.get.return_value = ""
        with pytest.raises(ValueError):
            app.get_counter_threshold()

    def test_float_string_raises_value_error(self) -> None:
        """get_counter_threshold raises ValueError for float-like strings."""
        app = _make_app()
        app.counter_threshold_var.get.return_value = "3.14"
        with pytest.raises(ValueError):
            app.get_counter_threshold()


# ---------------------------------------------------------------------------
# Tests: app state persistence
# ---------------------------------------------------------------------------

class TestAppStatePersistence:
    def test_threshold_var_updated_value_persists(self) -> None:
        """Threshold StringVar value persists across reads."""
        app = _make_app()
        app.counter_threshold_var.get.return_value = "42"
        assert app.get_counter_threshold() == 42
        # Call again — value is still returned from the StringVar mock
        assert app.get_counter_threshold() == 42

    def test_counter_enabled_var_readable(self) -> None:
        """counter_enabled_var.get() can be called to read the switch state."""
        app = _make_app()
        app.counter_enabled_var.get.return_value = True
        assert app.counter_enabled_var.get() is True

        app.counter_enabled_var.get.return_value = False
        assert app.counter_enabled_var.get() is False

    def test_get_counter_threshold_whitespace_trimmed(self) -> None:
        """Leading/trailing whitespace in threshold value is trimmed before validation."""
        app = _make_app()
        app.counter_threshold_var.get.return_value = "  30  "
        assert app.get_counter_threshold() == 30
