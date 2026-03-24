"""Tests for GUI-020 — app._on_create_project passes counter config to create_project.

Covers:
  1. _on_create_project reads counter_enabled_var and passes it to create_project
  2. _on_create_project reads counter threshold and passes it to create_project
  3. When threshold entry has invalid value, fallback 20 is used
  4. counter_enabled=True is forwarded correctly (switch on)
  5. counter_enabled=False is forwarded correctly (switch off)
  6. Custom threshold value is forwarded correctly
  7. Both counter_enabled and counter_threshold appear together in the create_project call
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

_CTK_MOCK = sys.modules["customtkinter"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app() -> "App":  # noqa: F821
    """Return a fresh App instance with widgets mocked."""
    from launcher.gui.app import App
    _CTK_MOCK.reset_mock()
    return App()


def _trigger_create(app, *, enabled: bool, threshold_str: str, dest: str = "/some/dest") -> None:
    """Configure the app mock state and invoke _on_create_project.

    Patches validate_folder_name, validate_destination_path, check_duplicate_folder,
    list_templates, verify_ts_python, and create_project so no real I/O occurs.

    list_templates returns ["coding"]; _format_template_name("coding") == "Coding",
    so the dropdown must return "Coding" for the template-lookup to succeed.
    """
    app.project_name_entry.get.return_value = "TestProject"
    app.project_type_dropdown.get.return_value = "Coding"
    app.destination_entry.get.return_value = dest
    app.project_name_error_label.configure = MagicMock()
    app.destination_error_label.configure = MagicMock()
    app.counter_enabled_var.get.return_value = enabled
    app.counter_threshold_var.get.return_value = threshold_str


# ---------------------------------------------------------------------------
# Tests: counter_enabled is passed to create_project
# ---------------------------------------------------------------------------

class TestAppPassesCounterEnabled:
    def test_counter_enabled_true_forwarded(self) -> None:
        """When counter switch is ON, create_project must receive counter_enabled=True."""
        app = _make_app()
        _trigger_create(app, enabled=True, threshold_str="20")

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.verify_ts_python", return_value=(True, "ok")), \
             patch("launcher.gui.app.create_project", return_value=Path("/fake/path")) as mock_create:
            app._on_create_project()

        assert mock_create.called, "create_project was not called"
        _, kwargs = mock_create.call_args
        assert kwargs.get("counter_enabled") is True, (
            f"Expected counter_enabled=True, got: {kwargs.get('counter_enabled')}"
        )

    def test_counter_enabled_false_forwarded(self) -> None:
        """When counter switch is OFF, create_project must receive counter_enabled=False."""
        app = _make_app()
        _trigger_create(app, enabled=False, threshold_str="20")

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.verify_ts_python", return_value=(True, "ok")), \
             patch("launcher.gui.app.create_project", return_value=Path("/fake/path")) as mock_create:
            app._on_create_project()

        assert mock_create.called
        _, kwargs = mock_create.call_args
        assert kwargs.get("counter_enabled") is False


# ---------------------------------------------------------------------------
# Tests: counter_threshold is passed to create_project
# ---------------------------------------------------------------------------

class TestAppPassesCounterThreshold:
    def test_valid_threshold_forwarded(self) -> None:
        """A valid threshold string must be parsed and forwarded as an integer."""
        app = _make_app()
        _trigger_create(app, enabled=True, threshold_str="30")

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.verify_ts_python", return_value=(True, "ok")), \
             patch("launcher.gui.app.create_project", return_value=Path("/fake/path")) as mock_create:
            app._on_create_project()

        assert mock_create.called
        _, kwargs = mock_create.call_args
        assert kwargs.get("counter_threshold") == 30

    def test_invalid_threshold_falls_back_to_20(self) -> None:
        """When threshold entry holds an invalid value, fallback 20 must be used."""
        app = _make_app()
        _trigger_create(app, enabled=True, threshold_str="not-a-number")

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.verify_ts_python", return_value=(True, "ok")), \
             patch("launcher.gui.app.create_project", return_value=Path("/fake/path")) as mock_create:
            app._on_create_project()

        assert mock_create.called
        _, kwargs = mock_create.call_args
        assert kwargs.get("counter_threshold") == 20, (
            f"Expected fallback threshold 20, got: {kwargs.get('counter_threshold')}"
        )

    def test_threshold_custom_value_5_forwarded(self) -> None:
        """Threshold value 5 must be passed as integer 5 to create_project."""
        app = _make_app()
        _trigger_create(app, enabled=True, threshold_str="5")

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.verify_ts_python", return_value=(True, "ok")), \
             patch("launcher.gui.app.create_project", return_value=Path("/fake/path")) as mock_create:
            app._on_create_project()

        assert mock_create.called
        _, kwargs = mock_create.call_args
        assert kwargs.get("counter_threshold") == 5

    def test_both_counter_args_present_in_call(self) -> None:
        """create_project must be called with both counter_enabled and counter_threshold."""
        app = _make_app()
        _trigger_create(app, enabled=False, threshold_str="15")

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.verify_ts_python", return_value=(True, "ok")), \
             patch("launcher.gui.app.create_project", return_value=Path("/fake/path")) as mock_create:
            app._on_create_project()

        assert mock_create.called
        _, kwargs = mock_create.call_args
        assert "counter_enabled" in kwargs, "counter_enabled keyword arg missing from create_project call"
        assert "counter_threshold" in kwargs, "counter_threshold keyword arg missing from create_project call"
        assert kwargs["counter_enabled"] is False
        assert kwargs["counter_threshold"] == 15
