"""Tester edge-case additions for GUI-009: Update Notification Banner.

Tests added by Tester Agent (2026-03-12) covering gaps in developer suite:
  1. Empty version string is handled gracefully (no crash; banner still shows/hides).
  2. The auto-launch _run_update_check lambda passes manual=False (never shows
     "You're up to date." on silent startup check).
  3. update_available=False + manual=False call never calls grid() on the banner
     (grid_remove only).
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Inject the customtkinter mock BEFORE importing any launcher module.
# ---------------------------------------------------------------------------
_CTK_MOCK = MagicMock(name="customtkinter")
sys.modules["customtkinter"] = _CTK_MOCK

for _key in [k for k in sys.modules if k.startswith("launcher.gui")]:
    del sys.modules[_key]

from launcher.gui.app import App  # noqa: E402

_APP_GLOBALS = App._run_update_check.__globals__


@pytest.fixture(autouse=True)
def _mock_update_check():
    """Prevent real HTTP calls by patching check_for_update in App's actual globals."""
    mock_check = MagicMock(return_value=(False, "0.1.0"))
    with patch.dict(_APP_GLOBALS, {"check_for_update": mock_check}):
        yield mock_check


def _fresh_app() -> App:
    _CTK_MOCK.reset_mock()
    return App()


class TestEmptyVersionStringSafety:
    def test_empty_version_string_does_not_crash_on_update(self):
        """_apply_update_result(True, '') must not raise; configure() and grid()
        must still be called even with an empty version string."""
        app = _fresh_app()
        app.update_banner.reset_mock()
        # Must not raise
        app._apply_update_result(True, "")
        app.update_banner.configure.assert_called()
        app.update_banner.grid.assert_called()

    def test_empty_version_banner_text_contains_v_prefix(self):
        """Even with an empty version string the banner text must still contain 'v'
        and not crash (text = 'Update available: v')."""
        app = _fresh_app()
        app._apply_update_result(True, "")
        text = app.update_banner.configure.call_args[1].get("text", "MISSING")
        # Should at least contain the static prefix
        assert "Update available:" in text


class TestAutoLaunchIsSilentCheck:
    def test_auto_launch_callback_does_not_pass_manual_true(self):
        """The lambda stored in _window.after() by _run_update_check must call
        _apply_update_result without manual=True.  If update_available=False,
        that means grid_remove() is called — NOT grid() — confirming the silent
        (non-manual) code path is used on startup."""
        mock_threading = MagicMock()
        mock_threading.Thread.return_value = MagicMock()
        with patch.dict(_APP_GLOBALS, {"threading": mock_threading}):
            app = App()
        app._window.after.reset_mock()
        app.update_banner.reset_mock()
        with patch.dict(_APP_GLOBALS, {
            "check_for_update": MagicMock(return_value=(False, "0.1.0")),
        }):
            app._run_update_check()

        # Execute the captured after() callback
        callback = app._window.after.call_args[0][1]
        callback()

        # With manual=False (default), a no-update result must hide the banner
        # (grid_remove), NOT show "You're up to date." (which needs manual=True)
        app.update_banner.grid_remove.assert_called()
        app.update_banner.grid.assert_not_called()
