"""Tests for GUI-010: Check for Updates Button.

Verifies that:
  1. A check_updates_button widget exists on the App instance.
  2. The button is created with text='Check for Updates'.
  3. _on_check_for_updates disables the button and updates its text to 'Checking…'.
  4. _on_check_for_updates spawns a daemon thread.
  5. _finish_manual_check restores the button to its original state.
  6. _finish_manual_check shows the update banner when an update is found.
  7. _finish_manual_check shows "You're up to date." when no update is found.
  8. The inner _check closure calls check_for_update.

All tests run headlessly using a customtkinter MagicMock.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# customtkinter is already mocked by tests/conftest.py — reuse that mock.
# ---------------------------------------------------------------------------
_CTK_MOCK = sys.modules["customtkinter"]

from launcher.gui.app import App  # noqa: E402

# Use App's actual globals dict so patches reach the correct namespace regardless
# of which test file most recently re-imported launcher.gui.app.
_APP_GLOBALS = App._on_check_for_updates.__globals__


@pytest.fixture(autouse=True)
def _mock_update_check():
    """Prevent real HTTP calls by patching check_for_update in App's actual globals."""
    mock_check = MagicMock(return_value=(False, "0.1.0"))
    with patch.dict(_APP_GLOBALS, {"check_for_update": mock_check}):
        yield mock_check


def _fresh_app() -> App:
    _CTK_MOCK.reset_mock()
    return App()


# ---------------------------------------------------------------------------
# Button widget existence and creation
# ---------------------------------------------------------------------------

class TestCheckUpdatesButtonExists:
    def test_check_updates_button_attribute_exists(self):
        app = _fresh_app()
        assert hasattr(app, "check_updates_button")

    def test_check_updates_button_not_none(self):
        app = _fresh_app()
        assert app.check_updates_button is not None

    def test_check_updates_button_created_with_correct_text(self):
        """CTkButton must be called with text='Check for Updates' during _build_ui."""
        _CTK_MOCK.reset_mock()
        App()
        calls = _CTK_MOCK.CTkButton.call_args_list
        texts = [c[1].get("text", "") for c in calls if "text" in c[1]]
        assert "Check for Updates" in texts


# ---------------------------------------------------------------------------
# _on_check_for_updates behaviour
# ---------------------------------------------------------------------------

class TestOnCheckForUpdates:
    def test_disables_button_while_checking(self):
        """Button must be disabled immediately when _on_check_for_updates is called."""
        app = _fresh_app()
        mock_threading = MagicMock()
        mock_threading.Thread.return_value = MagicMock()
        with patch.dict(_APP_GLOBALS, {"threading": mock_threading}):
            app._on_check_for_updates()
        app.check_updates_button.configure.assert_any_call(state="disabled", text="Checking...")

    def test_spawns_daemon_thread(self):
        """The thread started by _on_check_for_updates must have daemon=True."""
        app = _fresh_app()
        mock_thread = MagicMock()
        mock_threading = MagicMock()
        mock_threading.Thread.return_value = mock_thread
        with patch.dict(_APP_GLOBALS, {"threading": mock_threading}):
            app._on_check_for_updates()
        assert mock_threading.Thread.call_args.kwargs.get("daemon") is True
        mock_thread.start.assert_called_once()

    def test_thread_target_calls_check_for_update(self):
        """The closure passed as thread target must call check_for_update."""
        app = _fresh_app()
        captured_target = None

        def capture(**kwargs):
            nonlocal captured_target
            captured_target = kwargs.get("target")
            return MagicMock()

        mock_threading = MagicMock()
        mock_threading.Thread.side_effect = capture
        mock_check = MagicMock(return_value=(False, "0.1.0"))
        with patch.dict(_APP_GLOBALS, {"threading": mock_threading, "check_for_update": mock_check}):
            app._on_check_for_updates()
            if captured_target is not None:
                captured_target()
        mock_check.assert_called()


# ---------------------------------------------------------------------------
# _finish_manual_check behaviour
# ---------------------------------------------------------------------------

class TestFinishManualCheck:
    def test_restores_button_state_and_text(self):
        app = _fresh_app()
        app._finish_manual_check(False, "0.1.0")
        app.check_updates_button.configure.assert_any_call(state="normal", text="Check for Updates")

    def test_shows_update_banner_when_update_found(self):
        app = _fresh_app()
        app.update_banner.reset_mock()
        app._finish_manual_check(True, "1.0.0")
        app.update_banner.configure.assert_called_with(text="Update available: v1.0.0")
        app.update_banner.grid.assert_called()

    def test_shows_up_to_date_when_no_update(self):
        app = _fresh_app()
        app.update_banner.reset_mock()
        app._finish_manual_check(False, "0.1.0")
        text = app.update_banner.configure.call_args[1].get("text", "")
        assert "up to date" in text.lower()
        app.update_banner.grid.assert_called()
