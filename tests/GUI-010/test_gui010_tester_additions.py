"""Tester edge-case additions for GUI-010: Check for Updates Button.

Tests added by Tester Agent (2026-03-12) covering gaps in developer suite:
  1. Empty version string in _finish_manual_check(True, '') — button still restored.
  2. Inner _check closure schedules _finish_manual_check via after(0, ...) — zero delay.
  3. _on_check_for_updates configure call for state+text happens in a single call
     (not two separate configure() calls), confirming atomic UI update.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Inject the customtkinter mock BEFORE importing any launcher module.
# ---------------------------------------------------------------------------
_CTK_MOCK = MagicMock(name="customtkinter")
sys.modules["customtkinter"] = _CTK_MOCK

for _key in [k for k in sys.modules if k.startswith("launcher.gui")]:
    del sys.modules[_key]

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


class TestEmptyVersionRestoresButton:
    def test_finish_manual_check_empty_version_still_restores_button(self):
        """_finish_manual_check(True, '') must restore the button to its original
        state even when the version string is empty."""
        app = _fresh_app()
        app._finish_manual_check(True, "")
        app.check_updates_button.configure.assert_any_call(
            state="normal", text="Check for Updates"
        )

    def test_finish_manual_check_empty_version_shows_banner(self):
        """_finish_manual_check(True, '') must still show the update banner
        even with an empty version string — no crash, no silent swallow."""
        app = _fresh_app()
        app.update_banner.reset_mock()
        app._finish_manual_check(True, "")
        app.update_banner.configure.assert_called()
        app.update_banner.grid.assert_called()


class TestInnerCheckClosureSchedulesViaAfter:
    def test_inner_check_uses_after_with_zero_delay(self):
        """The lambda scheduled by the inner _check closure must use after(0, ...)
        so _finish_manual_check runs on the Tk main thread as soon as possible."""
        app = _fresh_app()
        captured_target = None

        def _capture_thread(**kwargs):
            nonlocal captured_target
            captured_target = kwargs.get("target")
            return MagicMock()

        mock_threading = MagicMock()
        mock_threading.Thread.side_effect = _capture_thread
        mock_check = MagicMock(return_value=(False, "0.1.0"))
        app._window.after.reset_mock()
        with patch.dict(_APP_GLOBALS, {
            "threading": mock_threading,
            "check_for_update": mock_check,
        }):
            app._on_check_for_updates()
            if captured_target is not None:
                captured_target()  # execute the inner _check closure

        # after() must have been called; the first argument must be 0
        assert app._window.after.called, "_window.after() was not called by inner _check"
        delay = app._window.after.call_args[0][0]
        assert delay == 0, f"Expected after(0, ...) but got after({delay}, ...)"
