"""Edge-case tests for GUI-010: Check for Updates Button.

Covers scenarios the Developer tests did not include:
  - Double-click prevention: button is disabled before the thread starts
  - Button text changes to 'Checking...' immediately on click
  - Button is restored in BOTH the update-found and no-update paths
  - _finish_manual_check always passes manual=True to _apply_update_result
  - The spawned thread has daemon=True (verified via _APP_GLOBALS patching)
  - No permanent lock-out: button re-enabled after _finish_manual_check

All patches use patch.dict(_APP_GLOBALS, ...) which directly modifies the
module's global dict — the reliable approach for this test architecture.
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
# Double-click prevention
# ---------------------------------------------------------------------------

class TestDoubleClickPrevention:
    def test_button_state_disabled_before_thread_starts(self):
        """Button must be set to 'disabled' as the FIRST action in
        _on_check_for_updates, before threading.Thread() is called.
        This prevents a rapid second click from spawning a parallel check."""
        app = _fresh_app()
        app.check_updates_button.reset_mock()
        mock_threading = MagicMock()
        mock_threading.Thread.return_value = MagicMock()
        with patch.dict(_APP_GLOBALS, {"threading": mock_threading}):
            app._on_check_for_updates()
        configure_calls = app.check_updates_button.configure.call_args_list
        assert len(configure_calls) >= 1, "configure() must be called on the button"
        first_call_kwargs = configure_calls[0][1]
        assert first_call_kwargs.get("state") == "disabled", (
            "Button must be disabled as first action in _on_check_for_updates"
        )

    def test_checking_text_set_on_button_during_check(self):
        """Button text must change to 'Checking...' while the check is running."""
        app = _fresh_app()
        app.check_updates_button.reset_mock()
        mock_threading = MagicMock()
        mock_threading.Thread.return_value = MagicMock()
        with patch.dict(_APP_GLOBALS, {"threading": mock_threading}):
            app._on_check_for_updates()
        all_texts = [
            c[1].get("text") for c in app.check_updates_button.configure.call_args_list
            if "text" in c[1]
        ]
        assert "Checking..." in all_texts, (
            "Button text must include 'Checking...' while the check is running"
        )

    def test_button_not_permanently_locked_after_finish(self):
        """After _finish_manual_check is called, the button must be re-enabled.
        Ensures no permanent lock-out scenario."""
        app = _fresh_app()
        app._finish_manual_check(False, "0.1.0")
        all_states = [
            c[1].get("state") for c in app.check_updates_button.configure.call_args_list
            if "state" in c[1]
        ]
        assert "normal" in all_states, (
            "Button must be re-enabled after _finish_manual_check completes"
        )


# ---------------------------------------------------------------------------
# Button restoration in all outcome paths
# ---------------------------------------------------------------------------

class TestButtonRestoration:
    def test_button_restored_to_original_text_after_update_found(self):
        """Button text must return to 'Check for Updates' after a manual check
        that finds an update."""
        app = _fresh_app()
        app._finish_manual_check(True, "1.0.0")
        app.check_updates_button.configure.assert_any_call(
            state="normal", text="Check for Updates"
        )

    def test_button_restored_to_original_text_after_no_update(self):
        """Button text must return to 'Check for Updates' after a manual check
        that finds no update."""
        app = _fresh_app()
        app._finish_manual_check(False, "0.1.0")
        app.check_updates_button.configure.assert_any_call(
            state="normal", text="Check for Updates"
        )

    def test_button_restored_with_multi_word_version(self):
        """Button restoration must work regardless of the version string returned."""
        app = _fresh_app()
        app._finish_manual_check(False, "99.99.99")
        app.check_updates_button.configure.assert_any_call(
            state="normal", text="Check for Updates"
        )


# ---------------------------------------------------------------------------
# manual=True propagation through _finish_manual_check
# ---------------------------------------------------------------------------

class TestManualFlagPropagation:
    def test_finish_manual_check_with_no_update_shows_up_to_date(self):
        """_finish_manual_check must display 'You're up to date.' when no update is
        available — confirming that manual=True is propagated to _apply_update_result."""
        app = _fresh_app()
        app.update_banner.reset_mock()
        app._finish_manual_check(False, "0.1.0")
        text = app.update_banner.configure.call_args[1].get("text", "")
        assert "up to date" in text.lower(), (
            "_finish_manual_check must show 'up to date' message, not hide the banner"
        )
        app.update_banner.grid.assert_called()

    def test_finish_manual_check_with_update_shows_version(self):
        """_finish_manual_check with update_available=True must show the update
        version in the banner."""
        app = _fresh_app()
        app.update_banner.reset_mock()
        app._finish_manual_check(True, "8.0.0")
        text = app.update_banner.configure.call_args[1].get("text", "")
        assert "8.0.0" in text


# ---------------------------------------------------------------------------
# Thread daemon flag (using _APP_GLOBALS for reliable patching)
# ---------------------------------------------------------------------------

class TestManualCheckThreadDaemon:
    def test_thread_started_by_on_check_is_daemon(self):
        """The thread created inside _on_check_for_updates must have daemon=True,
        so it does not block application shutdown."""
        app = _fresh_app()
        mock_thread = MagicMock()
        mock_threading = MagicMock()
        mock_threading.Thread.return_value = mock_thread
        with patch.dict(_APP_GLOBALS, {"threading": mock_threading}):
            app._on_check_for_updates()
        thread_kwargs = mock_threading.Thread.call_args.kwargs
        assert thread_kwargs.get("daemon") is True, (
            "Manual check thread must be a daemon thread"
        )
        mock_thread.start.assert_called_once()

    def test_thread_target_is_callable(self):
        """The target function passed to Thread() must be callable."""
        app = _fresh_app()
        mock_threading = MagicMock()
        mock_threading.Thread.return_value = MagicMock()
        with patch.dict(_APP_GLOBALS, {"threading": mock_threading}):
            app._on_check_for_updates()
        target = mock_threading.Thread.call_args.kwargs.get("target")
        assert callable(target), "Thread target must be a callable"
