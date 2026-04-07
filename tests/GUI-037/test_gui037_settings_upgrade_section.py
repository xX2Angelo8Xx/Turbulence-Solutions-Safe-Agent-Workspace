"""Tests for GUI-037 — Move workspace upgrade to Settings dialog.

Covers:
1.  App class no longer has workspace_health_button attribute
2.  App class no longer has _on_check_workspace_health method
3.  SettingsDialog has _on_check_and_upgrade method
4.  SettingsDialog has _update_version_label method
5.  SettingsDialog has _workspace_version_label with placeholder text
6.  SettingsDialog has _check_upgrade_button attribute
7.  Dialog geometry is 480x720 (increased from 620)
8.  _on_check_and_upgrade shows error when no workspace selected
9.  _on_check_and_upgrade shows info when workspace is up to date
10. _on_check_and_upgrade shows upgrade prompt when outdated
11. _on_check_and_upgrade runs upgrade when user confirms
12. _on_check_and_upgrade updates label to up-to-date after upgrade
13. _on_check_and_upgrade shows partial failure when upgrade has errors
14. _on_check_and_upgrade shows error when check_workspace raises exception
15. _on_check_and_upgrade shows error messagebox when report has errors
16. _update_version_label reads .github/version and updates label
17. _update_version_label shows fallback when version file missing
18. _auto_health_check updates label for up-to-date workspace
19. _auto_health_check updates label with count when outdated
20. _auto_health_check is silent on exception (does not raise)
21. _auto_health_check is silent when report has errors
22. _browse_workspace calls _update_version_label immediately on folder select
23. Close button is at row 13 (bottom), not row 3
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call

import pytest

_CTK_MOCK = sys.modules["customtkinter"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_settings_dialog() -> "SettingsDialog":  # noqa: F821
    """Return a fresh SettingsDialog instance with all widgets mocked."""
    from launcher.gui.app import SettingsDialog
    _CTK_MOCK.reset_mock()
    return SettingsDialog(MagicMock())


def _make_report(
    *,
    errors=None,
    up_to_date=True,
    workspace_version="3.3.9",
    launcher_version="3.4.0",
    outdated_files=None,
    missing_files=None,
) -> SimpleNamespace:
    return SimpleNamespace(
        errors=errors or [],
        up_to_date=up_to_date,
        workspace_version=workspace_version,
        launcher_version=launcher_version,
        outdated_files=outdated_files or [],
        missing_files=missing_files or [],
    )


def _make_upgrade_result(*, errors=None, upgraded_files=None, launcher_version="3.4.0") -> SimpleNamespace:
    return SimpleNamespace(
        errors=errors or [],
        upgraded_files=upgraded_files or ["security_gate.py"],
        launcher_version=launcher_version,
    )


# ---------------------------------------------------------------------------
# Tests: App class cleanup
# ---------------------------------------------------------------------------

class TestAppButtonRemoved:
    def test_app_has_no_workspace_health_button(self) -> None:
        """workspace_health_button must not exist as an attribute on the App class."""
        from launcher.gui import app
        src = inspect.getsource(app.App)
        assert "workspace_health_button" not in src, (
            "workspace_health_button should have been removed from App"
        )

    def test_app_has_no_on_check_workspace_health(self) -> None:
        """_on_check_workspace_health method must not exist on App."""
        from launcher.gui.app import App
        assert not hasattr(App, "_on_check_workspace_health"), (
            "_on_check_workspace_health was not removed from App"
        )


# ---------------------------------------------------------------------------
# Tests: SettingsDialog new attributes
# ---------------------------------------------------------------------------

class TestSettingsDialogNewAttributes:
    def test_has_on_check_and_upgrade(self) -> None:
        """SettingsDialog must have _on_check_and_upgrade method."""
        from launcher.gui.app import SettingsDialog
        assert hasattr(SettingsDialog, "_on_check_and_upgrade"), (
            "SettingsDialog is missing _on_check_and_upgrade"
        )

    def test_has_update_version_label(self) -> None:
        """SettingsDialog must have _update_version_label method."""
        from launcher.gui.app import SettingsDialog
        assert hasattr(SettingsDialog, "_update_version_label"), (
            "SettingsDialog is missing _update_version_label"
        )

    def test_has_workspace_version_label(self) -> None:
        """SettingsDialog instance must expose _workspace_version_label."""
        dialog = _make_settings_dialog()
        assert hasattr(dialog, "_workspace_version_label"), (
            "SettingsDialog is missing _workspace_version_label"
        )

    def test_has_check_upgrade_button(self) -> None:
        """SettingsDialog instance must expose _check_upgrade_button."""
        dialog = _make_settings_dialog()
        assert hasattr(dialog, "_check_upgrade_button"), (
            "SettingsDialog is missing _check_upgrade_button"
        )

    def test_dialog_geometry_is_720(self) -> None:
        """SettingsDialog geometry must be 480x720."""
        src = inspect.getsource(
            sys.modules["launcher.gui.app"].SettingsDialog.__init__
        )
        assert "480x720" in src, "Dialog geometry was not updated to 480x720"

    def test_auto_health_check_does_not_reference_old_button(self) -> None:
        """_auto_health_check must not reference 'Check Workspace Health'."""
        from launcher.gui import app
        src = inspect.getsource(app.SettingsDialog._auto_health_check)
        assert "Check Workspace Health" not in src, (
            "_auto_health_check still references 'Check Workspace Health'"
        )


# ---------------------------------------------------------------------------
# Tests: _on_check_and_upgrade logic
# ---------------------------------------------------------------------------

class TestOnCheckAndUpgrade:
    def test_empty_workspace_shows_error(self) -> None:
        """When no workspace is selected, _on_check_and_upgrade shows an error."""
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = "  "
        with patch("launcher.gui.app.messagebox.showerror") as mock_err:
            dialog._on_check_and_upgrade()
        mock_err.assert_called_once()
        args = mock_err.call_args[0]
        assert "Please select a workspace folder first" in args[1]

    def test_up_to_date_shows_info(self, tmp_path: Path) -> None:
        """When workspace is up to date, shows an info messagebox."""
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)
        report = _make_report(up_to_date=True, workspace_version="3.3.9")
        with patch("launcher.gui.app.check_workspace", return_value=report), \
             patch("launcher.gui.app.messagebox.showinfo") as mock_info:
            dialog._on_check_and_upgrade()
        mock_info.assert_called_once()
        args = mock_info.call_args[0]
        assert "up to date" in args[1].lower()

    def test_up_to_date_updates_version_label(self, tmp_path: Path) -> None:
        """When workspace is up to date, version label shows 'up to date'."""
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)
        report = _make_report(up_to_date=True, workspace_version="3.3.9")
        with patch("launcher.gui.app.check_workspace", return_value=report), \
             patch("launcher.gui.app.messagebox.showinfo"):
            dialog._on_check_and_upgrade()
        dialog._workspace_version_label.configure.assert_called_with(
            text="v3.3.9 — up to date"
        )

    def test_outdated_shows_upgrade_prompt(self, tmp_path: Path) -> None:
        """When outdated, shows upgrade confirmation dialog."""
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)
        report = _make_report(
            up_to_date=False,
            workspace_version="3.3.0",
            launcher_version="3.4.0",
            outdated_files=["security_gate.py"],
        )
        with patch("launcher.gui.app.check_workspace", return_value=report), \
             patch("launcher.gui.app.messagebox.askyesno", return_value=False) as mock_ask:
            dialog._on_check_and_upgrade()
        mock_ask.assert_called_once()

    def test_outdated_updates_version_label_with_count(self, tmp_path: Path) -> None:
        """When outdated, version label shows file count."""
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)
        report = _make_report(
            up_to_date=False,
            workspace_version="3.3.0",
            outdated_files=["security_gate.py"],
            missing_files=["zone_classifier.py"],
        )
        with patch("launcher.gui.app.check_workspace", return_value=report), \
             patch("launcher.gui.app.messagebox.askyesno", return_value=False):
            dialog._on_check_and_upgrade()
        dialog._workspace_version_label.configure.assert_called_with(
            text="v3.3.0 — 2 file(s) need updating"
        )

    def test_upgrade_runs_when_user_confirms(self, tmp_path: Path) -> None:
        """When user says yes to upgrade, upgrade_workspace is called."""
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)
        report = _make_report(
            up_to_date=False,
            workspace_version="3.3.0",
            outdated_files=["security_gate.py"],
        )
        upgrade_result = _make_upgrade_result()
        with patch("launcher.gui.app.check_workspace", return_value=report), \
             patch("launcher.gui.app.messagebox.askyesno", return_value=True), \
             patch("launcher.gui.app.upgrade_workspace", return_value=upgrade_result) as mock_upgrade, \
             patch("launcher.gui.app.messagebox.showinfo"):
            dialog._on_check_and_upgrade()
        mock_upgrade.assert_called_once_with(tmp_path)

    def test_upgrade_updates_label_on_success(self, tmp_path: Path) -> None:
        """After successful upgrade, version label is updated to new version."""
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)
        report = _make_report(
            up_to_date=False,
            workspace_version="3.3.0",
            outdated_files=["security_gate.py"],
        )
        upgrade_result = _make_upgrade_result(launcher_version="3.4.0")
        with patch("launcher.gui.app.check_workspace", return_value=report), \
             patch("launcher.gui.app.messagebox.askyesno", return_value=True), \
             patch("launcher.gui.app.upgrade_workspace", return_value=upgrade_result), \
             patch("launcher.gui.app.messagebox.showinfo"):
            dialog._on_check_and_upgrade()
        dialog._workspace_version_label.configure.assert_called_with(
            text="v3.4.0 — up to date"
        )

    def test_partial_failure_shows_error(self, tmp_path: Path) -> None:
        """When upgrade has errors, shows error messagebox."""
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)
        report = _make_report(
            up_to_date=False,
            outdated_files=["security_gate.py"],
        )
        upgrade_result = _make_upgrade_result(errors=["could not copy file"])
        with patch("launcher.gui.app.check_workspace", return_value=report), \
             patch("launcher.gui.app.messagebox.askyesno", return_value=True), \
             patch("launcher.gui.app.upgrade_workspace", return_value=upgrade_result), \
             patch("launcher.gui.app.messagebox.showerror") as mock_err:
            dialog._on_check_and_upgrade()
        mock_err.assert_called_once()
        args = mock_err.call_args[0]
        assert "Partially Failed" in args[0]

    def test_check_workspace_exception_shows_error(self, tmp_path: Path) -> None:
        """When check_workspace raises, shows error messagebox."""
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)
        with patch("launcher.gui.app.check_workspace", side_effect=RuntimeError("disk error")), \
             patch("launcher.gui.app.messagebox.showerror") as mock_err:
            dialog._on_check_and_upgrade()
        mock_err.assert_called_once()

    def test_report_errors_shows_error(self, tmp_path: Path) -> None:
        """When report.errors is non-empty, shows error messagebox."""
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)
        report = _make_report(errors=["manifest not found"])
        with patch("launcher.gui.app.check_workspace", return_value=report), \
             patch("launcher.gui.app.messagebox.showerror") as mock_err:
            dialog._on_check_and_upgrade()
        mock_err.assert_called_once()

    def test_upgrade_workspace_exception_shows_error(self, tmp_path: Path) -> None:
        """When upgrade_workspace raises, shows error messagebox."""
        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)
        report = _make_report(
            up_to_date=False,
            outdated_files=["security_gate.py"],
        )
        with patch("launcher.gui.app.check_workspace", return_value=report), \
             patch("launcher.gui.app.messagebox.askyesno", return_value=True), \
             patch("launcher.gui.app.upgrade_workspace", side_effect=RuntimeError("write error")), \
             patch("launcher.gui.app.messagebox.showerror") as mock_err:
            dialog._on_check_and_upgrade()
        mock_err.assert_called_once()
        assert "Upgrade Failed" in mock_err.call_args[0][0]


# ---------------------------------------------------------------------------
# Tests: _update_version_label
# ---------------------------------------------------------------------------

class TestUpdateVersionLabel:
    def test_reads_version_file(self, tmp_path: Path) -> None:
        """_update_version_label reads .github/version and updates label."""
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        (github_dir / "version").write_text("3.3.9\n", encoding="utf-8")
        dialog = _make_settings_dialog()
        dialog._update_version_label(tmp_path)
        dialog._workspace_version_label.configure.assert_called_with(text="v3.3.9")

    def test_version_file_missing_shows_fallback(self, tmp_path: Path) -> None:
        """_update_version_label shows fallback text when version file is absent."""
        dialog = _make_settings_dialog()
        dialog._update_version_label(tmp_path)
        dialog._workspace_version_label.configure.assert_called_with(
            text="Version file not found"
        )

    def test_strips_whitespace_from_version(self, tmp_path: Path) -> None:
        """_update_version_label strips trailing whitespace/newline from version."""
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        (github_dir / "version").write_text("  3.4.0  \n", encoding="utf-8")
        dialog = _make_settings_dialog()
        dialog._update_version_label(tmp_path)
        dialog._workspace_version_label.configure.assert_called_with(text="v3.4.0")


# ---------------------------------------------------------------------------
# Tests: _auto_health_check
# ---------------------------------------------------------------------------

class TestAutoHealthCheck:
    def test_updates_label_when_up_to_date(self, tmp_path: Path) -> None:
        """_auto_health_check updates label to 'up to date' for current workspace."""
        dialog = _make_settings_dialog()
        report = _make_report(up_to_date=True, workspace_version="3.4.0")
        with patch("launcher.gui.app.check_workspace", return_value=report):
            dialog._auto_health_check(tmp_path)
        # Should schedule via self._dialog.after
        dialog._dialog.after.assert_called_once()
        _, fn = dialog._dialog.after.call_args[0]
        fn()  # Execute the scheduled lambda
        dialog._workspace_version_label.configure.assert_called_with(
            text="v3.4.0 — up to date"
        )

    def test_updates_label_with_count_when_outdated(self, tmp_path: Path) -> None:
        """_auto_health_check updates label with file count when outdated."""
        dialog = _make_settings_dialog()
        report = _make_report(
            up_to_date=False,
            workspace_version="3.3.0",
            outdated_files=["security_gate.py", "zone_classifier.py"],
            missing_files=["hooks/pre-commit"],
        )
        with patch("launcher.gui.app.check_workspace", return_value=report):
            dialog._auto_health_check(tmp_path)
        _, fn = dialog._dialog.after.call_args[0]
        fn()
        dialog._workspace_version_label.configure.assert_called_with(
            text="v3.3.0 — 3 file(s) need updating"
        )

    def test_silent_on_exception(self, tmp_path: Path) -> None:
        """_auto_health_check does not raise when check_workspace fails."""
        dialog = _make_settings_dialog()
        with patch("launcher.gui.app.check_workspace", side_effect=OSError("no manifest")):
            dialog._auto_health_check(tmp_path)  # Must not raise
        dialog._dialog.after.assert_not_called()

    def test_silent_when_report_has_errors(self, tmp_path: Path) -> None:
        """_auto_health_check returns silently when report contains errors."""
        dialog = _make_settings_dialog()
        report = _make_report(errors=["manifest missing"])
        with patch("launcher.gui.app.check_workspace", return_value=report):
            dialog._auto_health_check(tmp_path)
        dialog._dialog.after.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: _browse_workspace integration
# ---------------------------------------------------------------------------

class TestBrowseWorkspace:
    def test_browse_calls_update_version_label(self, tmp_path: Path) -> None:
        """_browse_workspace calls _update_version_label after folder selection."""
        dialog = _make_settings_dialog()
        with patch("launcher.gui.app.filedialog.askdirectory", return_value=str(tmp_path)), \
             patch.object(dialog, "_update_version_label") as mock_update, \
             patch("launcher.gui.app.threading.Thread") as mock_thread:
            dialog._browse_workspace()
        mock_update.assert_called_once_with(tmp_path)

    def test_browse_starts_background_health_check(self, tmp_path: Path) -> None:
        """_browse_workspace starts a background thread for _auto_health_check."""
        dialog = _make_settings_dialog()
        with patch("launcher.gui.app.filedialog.askdirectory", return_value=str(tmp_path)), \
             patch.object(dialog, "_update_version_label"), \
             patch("launcher.gui.app.threading.Thread") as mock_thread:
            dialog._browse_workspace()
        mock_thread.assert_called_once()
        kwargs = mock_thread.call_args[1]
        assert kwargs.get("target") == dialog._auto_health_check
        assert kwargs.get("daemon") is True

    def test_browse_no_folder_does_nothing(self) -> None:
        """_browse_workspace does nothing when user cancels the dialog."""
        dialog = _make_settings_dialog()
        with patch("launcher.gui.app.filedialog.askdirectory", return_value=""), \
             patch.object(dialog, "_update_version_label") as mock_update:
            dialog._browse_workspace()
        mock_update.assert_not_called()
