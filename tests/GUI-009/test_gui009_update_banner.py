"""Tests for GUI-009: Update Notification Banner.

Verifies that:
  1. An update_banner widget exists on the App instance.
  2. The banner is hidden on init (grid_remove called).
  3. _apply_update_result shows the banner correctly when update_available=True.
  4. _apply_update_result hides the banner on a silent no-update check.
  5. _apply_update_result shows "You''re up to date." on a manual no-update check.
  6. _run_update_check calls check_for_update(VERSION) and schedules on main thread.
  7. The background thread started on launch is a daemon thread.

Uses patch.dict on App''s actual __globals__ to ensure patches reach the correct
namespace regardless of test collection order and module re-imports.
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
import launcher.config as config  # noqa: E402

# App methods use __globals__ pointing to the module dict at import time.
# patch.dict on this dict ensures patches are visible to App''s methods even
# when sys.modules["launcher.gui.app"] has been replaced by a later test file.
_APP_GLOBALS = App._run_update_check.__globals__


@pytest.fixture(autouse=True)
def _mock_update_check():
    """Prevent real HTTP calls by patching check_for_update in App''s actual globals."""
    mock_check = MagicMock(return_value=(False, "0.1.0"))
    with patch.dict(_APP_GLOBALS, {"check_for_update": mock_check}):
        yield mock_check


def _fresh_app() -> App:
    _CTK_MOCK.reset_mock()
    return App()


# ---------------------------------------------------------------------------
# Banner widget existence
# ---------------------------------------------------------------------------

class TestUpdateBannerExists:
    def test_update_banner_attribute_exists(self):
        app = _fresh_app()
        assert hasattr(app, "update_banner")

    def test_update_banner_is_not_none(self):
        app = _fresh_app()
        assert app.update_banner is not None

    def test_update_banner_hidden_on_init(self):
        """grid_remove() must be called during _build_ui to hide the banner initially."""
        app = _fresh_app()
        app.update_banner.grid_remove.assert_called()


# ---------------------------------------------------------------------------
# _apply_update_result behaviour
# ---------------------------------------------------------------------------

class TestApplyUpdateResult:
    def test_shows_banner_when_update_available(self):
        app = _fresh_app()
        app.update_banner.reset_mock()
        app._apply_update_result(True, "1.2.3")
        app.update_banner.configure.assert_called_with(text="Update available: v1.2.3")
        app.update_banner.grid.assert_called()

    def test_hides_banner_on_silent_no_update(self):
        app = _fresh_app()
        app.update_banner.reset_mock()
        app._apply_update_result(False, "0.1.0", manual=False)
        app.update_banner.grid_remove.assert_called()

    def test_shows_up_to_date_on_manual_no_update(self):
        app = _fresh_app()
        app.update_banner.reset_mock()
        app._apply_update_result(False, "0.1.0", manual=True)
        text = app.update_banner.configure.call_args[1].get("text", "")
        assert "up to date" in text.lower()
        app.update_banner.grid.assert_called()

    def test_banner_text_contains_version_number(self):
        app = _fresh_app()
        app._apply_update_result(True, "2.0.0")
        text = app.update_banner.configure.call_args[1].get("text", "")
        assert "2.0.0" in text

    def test_update_shows_banner_regardless_of_manual_flag(self):
        """update_available=True must always show the banner, even when manual=True."""
        app = _fresh_app()
        app.update_banner.reset_mock()
        app._apply_update_result(True, "1.0.0", manual=True)
        app.update_banner.grid.assert_called()


# ---------------------------------------------------------------------------
# _run_update_check behaviour
# ---------------------------------------------------------------------------

class TestRunUpdateCheck:
    def test_calls_check_for_update_with_version(self):
        """_run_update_check must pass VERSION as the current_version argument."""
        mock_thread = MagicMock()
        mock_threading = MagicMock()
        mock_threading.Thread.return_value = mock_thread
        mock_check = MagicMock(return_value=(False, "0.1.0"))
        # Patch both threading (prevent __init__ background thread) and check_for_update.
        with patch.dict(_APP_GLOBALS, {"threading": mock_threading, "check_for_update": mock_check}):
            app = App()
            mock_check.reset_mock()
            app._run_update_check()
        mock_check.assert_called_once_with(config.VERSION)

    def test_schedules_result_on_main_thread(self):
        """_run_update_check must use _window.after(0, callable) to post to the main thread."""
        mock_threading = MagicMock()
        mock_threading.Thread.return_value = MagicMock()
        with patch.dict(_APP_GLOBALS, {"threading": mock_threading}):
            app = App()
        app._window.after.reset_mock()
        with patch.dict(_APP_GLOBALS, {"check_for_update": MagicMock(return_value=(False, "0.1.0"))}):
            app._run_update_check()
        app._window.after.assert_called_once()
        call_args = app._window.after.call_args[0]
        assert call_args[0] == 0
        assert callable(call_args[1])

    def test_background_thread_is_daemon(self):
        """The thread started in __init__ must have daemon=True."""
        mock_thread = MagicMock()
        mock_threading = MagicMock()
        mock_threading.Thread.return_value = mock_thread
        _CTK_MOCK.reset_mock()
        with patch.dict(_APP_GLOBALS, {"threading": mock_threading}):
            App()
        assert mock_threading.Thread.called, "threading.Thread was not called in App.__init__"
        assert mock_threading.Thread.call_args.kwargs.get("daemon") is True
        mock_thread.start.assert_called_once()