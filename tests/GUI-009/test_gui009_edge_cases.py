"""Edge-case tests for GUI-009: Update Notification Banner.

Covers scenarios the Developer tests did not include:
  - Network/error path: check_for_update returns (False, current) -> banner stays hidden
  - Banner toggles correctly from visible to hidden and back
  - Banner text updates when version changes between calls
  - Pre-release version strings appear in the banner
  - after() is always called with delay=0 for immediate main-thread dispatch
  - _run_update_check does not raise even if check_for_update returns an error tuple
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
import launcher.config as config  # noqa: E402

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


# ---------------------------------------------------------------------------
# Network error / silent failure handling
# ---------------------------------------------------------------------------

class TestNetworkErrorHandling:
    def test_network_error_keeps_banner_hidden(self):
        """If check_for_update returns (False, version) (error/no-update), banner must
        stay hidden on a silent (non-manual) call."""
        app = _fresh_app()
        app.update_banner.reset_mock()
        app._apply_update_result(False, config.VERSION, manual=False)
        app.update_banner.grid_remove.assert_called()
        app.update_banner.grid.assert_not_called()

    def test_run_update_check_does_not_raise_on_false_result(self):
        """_run_update_check must complete without raising even when check_for_update
        returns (False, current_version)."""
        app = _fresh_app()
        app._window.after.reset_mock()
        with patch.dict(_APP_GLOBALS, {"check_for_update": MagicMock(return_value=(False, "0.1.0"))}):
            app._run_update_check()  # must not raise
        assert app._window.after.called

    def test_run_update_check_posts_result_even_on_no_update(self):
        """_run_update_check must always call _window.after() regardless of whether
        an update was found."""
        app = _fresh_app()
        app._window.after.reset_mock()
        with patch.dict(_APP_GLOBALS, {"check_for_update": MagicMock(return_value=(False, "0.1.0"))}):
            app._run_update_check()
        app._window.after.assert_called_once()


# ---------------------------------------------------------------------------
# Banner toggling
# ---------------------------------------------------------------------------

class TestBannerToggling:
    def test_banner_shown_then_hidden_on_silent_no_update(self):
        """After the banner is shown (update available), a subsequent silent no-update
        call must hide it again."""
        app = _fresh_app()
        app._apply_update_result(True, "2.0.0")
        app.update_banner.reset_mock()
        app._apply_update_result(False, "0.1.0", manual=False)
        app.update_banner.grid_remove.assert_called()

    def test_banner_text_updates_on_new_version_number(self):
        """Calling _apply_update_result twice with different versions must update the
        banner text each time."""
        app = _fresh_app()
        app._apply_update_result(True, "1.0.0")
        first_text = app.update_banner.configure.call_args[1].get("text", "")
        app._apply_update_result(True, "2.0.0")
        second_text = app.update_banner.configure.call_args[1].get("text", "")
        assert "1.0.0" in first_text
        assert "2.0.0" in second_text
        assert first_text != second_text

    def test_manual_up_to_date_replaced_by_subsequent_update(self):
        """If 'You're up to date.' is displayed and then a new update is found,
        the banner must switch to showing the update message."""
        app = _fresh_app()
        app._apply_update_result(False, "0.1.0", manual=True)
        up_to_date_text = app.update_banner.configure.call_args[1].get("text", "")
        assert "up to date" in up_to_date_text.lower()
        app.update_banner.reset_mock()
        app._apply_update_result(True, "1.5.0")
        update_text = app.update_banner.configure.call_args[1].get("text", "")
        assert "1.5.0" in update_text
        app.update_banner.grid.assert_called()

    def test_silent_no_update_after_manual_up_to_date_hides_banner(self):
        """A silent check that returns no-update must hide the banner even if
        'You're up to date.' was previously showing."""
        app = _fresh_app()
        app._apply_update_result(False, "0.1.0", manual=True)  # shows "up to date"
        app.update_banner.reset_mock()
        app._apply_update_result(False, "0.1.0", manual=False)  # silent: must hide
        app.update_banner.grid_remove.assert_called()


# ---------------------------------------------------------------------------
# Version string formatting
# ---------------------------------------------------------------------------

class TestVersionStringFormatting:
    def test_pre_release_version_appears_in_banner(self):
        """A pre-release version string ('1.0.0-beta') must appear verbatim in the
        banner text."""
        app = _fresh_app()
        app._apply_update_result(True, "1.0.0-beta")
        text = app.update_banner.configure.call_args[1].get("text", "")
        assert "1.0.0-beta" in text

    def test_banner_text_starts_with_update_available(self):
        """Banner text must start with 'Update available:' when an update is found."""
        app = _fresh_app()
        app._apply_update_result(True, "3.0.0")
        text = app.update_banner.configure.call_args[1].get("text", "")
        assert text.startswith("Update available:")

    def test_banner_includes_v_prefix_before_version(self):
        """Banner text must include 'v' before the version number."""
        app = _fresh_app()
        app._apply_update_result(True, "1.2.3")
        text = app.update_banner.configure.call_args[1].get("text", "")
        assert "v1.2.3" in text


# ---------------------------------------------------------------------------
# Thread safety: after() call guarantees
# ---------------------------------------------------------------------------

class TestThreadSafetyGuarantees:
    def test_after_callback_uses_zero_delay(self):
        """_run_update_check must call _window.after(0, ...) so the result is dispatched
        to the main Tk thread as soon as possible without blocking the UI."""
        mock_threading = MagicMock()
        mock_threading.Thread.return_value = MagicMock()
        with patch.dict(_APP_GLOBALS, {"threading": mock_threading}):
            app = App()
        app._window.after.reset_mock()
        with patch.dict(_APP_GLOBALS, {"check_for_update": MagicMock(return_value=(True, "9.9.9"))}):
            app._run_update_check()
        call_args = app._window.after.call_args[0]
        assert call_args[0] == 0, "after() must be called with delay=0"

    def test_after_receives_callable(self):
        """The second argument passed to _window.after() must be callable."""
        mock_threading = MagicMock()
        mock_threading.Thread.return_value = MagicMock()
        with patch.dict(_APP_GLOBALS, {"threading": mock_threading}):
            app = App()
        app._window.after.reset_mock()
        with patch.dict(_APP_GLOBALS, {"check_for_update": MagicMock(return_value=(False, "0.1.0"))}):
            app._run_update_check()
        callback = app._window.after.call_args[0][1]
        assert callable(callback), "Second argument to after() must be a callable"

    def test_after_callback_triggers_apply_update_result(self):
        """Invoking the callback passed to after() must call _apply_update_result."""
        mock_threading = MagicMock()
        mock_threading.Thread.return_value = MagicMock()
        with patch.dict(_APP_GLOBALS, {"threading": mock_threading}):
            app = App()
        app._window.after.reset_mock()
        app.update_banner.reset_mock()
        with patch.dict(_APP_GLOBALS, {"check_for_update": MagicMock(return_value=(True, "5.0.0"))}):
            app._run_update_check()
        # Execute the callback that was passed to after()
        callback = app._window.after.call_args[0][1]
        callback()
        # Now _apply_update_result should have been called, showing the banner
        update_text = app.update_banner.configure.call_args[1].get("text", "")
        assert "5.0.0" in update_text
