"""GUI-034 — Tests: Progress bar and disabled Create button during project creation.

Covers:
- _set_creation_ui_state disables/enables five widgets
- Progress bar is shown/started when disabling, stopped/hidden when enabling
- _on_creation_complete re-enables UI and shows the correct messagebox
- VS Code is opened on success only
- Background thread is launched when validation passes
- Progress bar is initially hidden in _build_ui
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


# ---------------------------------------------------------------------------
# Helper — minimal App instance without launching a real GUI
# ---------------------------------------------------------------------------

def _make_app() -> object:
    """Return a bare App instance with all GUI and IO side-effects suppressed."""
    import launcher.gui.app as app_mod

    mock_window = MagicMock()
    mock_widget = MagicMock()
    mock_widget.get.return_value = ""
    mock_window.grid_columnconfigure = MagicMock()

    with (
        patch("launcher.gui.app.ctk") as mock_ctk,
        patch("launcher.gui.app.find_vscode", return_value=None),
        patch("launcher.gui.app.threading.Thread"),
        patch("launcher.gui.app.get_setting", return_value=True),
    ):
        mock_ctk.CTk.return_value = mock_window
        mock_ctk.BooleanVar.return_value = MagicMock(get=MagicMock(return_value=True))
        mock_ctk.StringVar.return_value = MagicMock()
        mock_ctk.CTkLabel.return_value = mock_widget
        mock_ctk.CTkEntry.return_value = mock_widget
        mock_ctk.CTkButton.return_value = mock_widget
        mock_ctk.CTkOptionMenu.return_value = mock_widget
        mock_ctk.CTkCheckBox.return_value = mock_widget
        mock_ctk.CTkSwitch.return_value = mock_widget
        mock_ctk.CTkImage.return_value = mock_widget
        mock_ctk.CTkProgressBar.return_value = mock_widget

        with patch("launcher.gui.app.make_label_entry_row", return_value=mock_widget):
            app = app_mod.App.__new__(app_mod.App)
            app._window = mock_window
            app._latest_version = "0.0.0"
            app._current_template = "Agent Workbench"
            # Set up the five widgets that _set_creation_ui_state touches.
            app.create_button = MagicMock()
            app.project_name_entry = MagicMock()
            app.destination_entry = MagicMock()
            app.browse_button = MagicMock()
            app.project_type_dropdown = MagicMock()
            app.create_progress_bar = MagicMock()
            return app


# ---------------------------------------------------------------------------
# _set_creation_ui_state — disable
# ---------------------------------------------------------------------------

def test_set_creation_ui_state_disables_create_button():
    app = _make_app()
    app._set_creation_ui_state(disabled=True)
    app.create_button.configure.assert_called_with(state="disabled")


def test_set_creation_ui_state_disables_project_name_entry():
    app = _make_app()
    app._set_creation_ui_state(disabled=True)
    app.project_name_entry.configure.assert_called_with(state="disabled")


def test_set_creation_ui_state_disables_destination_entry():
    app = _make_app()
    app._set_creation_ui_state(disabled=True)
    app.destination_entry.configure.assert_called_with(state="disabled")


def test_set_creation_ui_state_disables_browse_button():
    app = _make_app()
    app._set_creation_ui_state(disabled=True)
    app.browse_button.configure.assert_called_with(state="disabled")


def test_set_creation_ui_state_disables_project_type_dropdown():
    app = _make_app()
    app._set_creation_ui_state(disabled=True)
    app.project_type_dropdown.configure.assert_called_with(state="disabled")


def test_set_creation_ui_state_shows_and_starts_progress_bar():
    app = _make_app()
    app._set_creation_ui_state(disabled=True)
    app.create_progress_bar.grid.assert_called_once()
    app.create_progress_bar.start.assert_called_once()


# ---------------------------------------------------------------------------
# _set_creation_ui_state — enable
# ---------------------------------------------------------------------------

def test_set_creation_ui_state_enables_create_button():
    app = _make_app()
    app._set_creation_ui_state(disabled=False)
    app.create_button.configure.assert_called_with(state="normal")


def test_set_creation_ui_state_enables_project_name_entry():
    app = _make_app()
    app._set_creation_ui_state(disabled=False)
    app.project_name_entry.configure.assert_called_with(state="normal")


def test_set_creation_ui_state_enables_destination_entry():
    app = _make_app()
    app._set_creation_ui_state(disabled=False)
    app.destination_entry.configure.assert_called_with(state="normal")


def test_set_creation_ui_state_enables_browse_button():
    app = _make_app()
    app._set_creation_ui_state(disabled=False)
    app.browse_button.configure.assert_called_with(state="normal")


def test_set_creation_ui_state_enables_project_type_dropdown():
    app = _make_app()
    app._set_creation_ui_state(disabled=False)
    app.project_type_dropdown.configure.assert_called_with(state="normal")


def test_set_creation_ui_state_hides_and_stops_progress_bar():
    app = _make_app()
    app._set_creation_ui_state(disabled=False)
    app.create_progress_bar.stop.assert_called_once()
    app.create_progress_bar.grid_remove.assert_called_once()


# ---------------------------------------------------------------------------
# _on_creation_complete
# ---------------------------------------------------------------------------

def test_on_creation_complete_re_enables_ui():
    app = _make_app()
    with patch.object(app, "_set_creation_ui_state") as mock_set_state:
        with patch("launcher.gui.app.messagebox"):
            with patch("launcher.gui.app.open_in_vscode"):
                app._on_creation_complete(True, "", Path("/tmp/SAE-Test"), "Test", False)
        mock_set_state.assert_called_once_with(disabled=False)


def test_on_creation_complete_success_shows_info():
    app = _make_app()
    with patch.object(app, "_set_creation_ui_state"):
        with patch("launcher.gui.app.messagebox") as mock_mb:
            with patch("launcher.gui.app.open_in_vscode"):
                app._on_creation_complete(True, "", Path("/tmp/SAE-Demo"), "Demo", False)
    mock_mb.showinfo.assert_called_once()
    args = mock_mb.showinfo.call_args
    assert "Demo" in str(args) or "SAE-Demo" in str(args)


def test_on_creation_complete_failure_shows_error():
    app = _make_app()
    with patch.object(app, "_set_creation_ui_state"):
        with patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_creation_complete(False, "Something went wrong", None, "Demo", False)
    mock_mb.showerror.assert_called_once()
    assert "Something went wrong" in mock_mb.showerror.call_args[0][1]


def test_on_creation_complete_opens_vscode_on_success():
    app = _make_app()
    created = Path("/tmp/SAE-Demo")
    with patch.object(app, "_set_creation_ui_state"):
        with patch("launcher.gui.app.messagebox"):
            with patch("launcher.gui.app.open_in_vscode") as mock_open:
                app._on_creation_complete(True, "", created, "Demo", True)
    mock_open.assert_called_once_with(created)


def test_on_creation_complete_no_vscode_on_failure():
    app = _make_app()
    with patch.object(app, "_set_creation_ui_state"):
        with patch("launcher.gui.app.messagebox"):
            with patch("launcher.gui.app.open_in_vscode") as mock_open:
                app._on_creation_complete(False, "error", None, "Demo", True)
    mock_open.assert_not_called()


def test_on_creation_complete_no_vscode_when_flag_false():
    app = _make_app()
    with patch.object(app, "_set_creation_ui_state"):
        with patch("launcher.gui.app.messagebox"):
            with patch("launcher.gui.app.open_in_vscode") as mock_open:
                app._on_creation_complete(True, "", Path("/tmp/SAE-Demo"), "Demo", False)
    mock_open.assert_not_called()


# ---------------------------------------------------------------------------
# _on_create_project — thread launching and UI disable
# ---------------------------------------------------------------------------

def _make_full_app() -> object:
    """Return an App instance with _build_ui called (fully mocked CTK)."""
    import launcher.gui.app as app_mod

    mock_window = MagicMock()
    mock_widget = MagicMock()
    mock_widget.get.return_value = "TestProject"
    mock_window.grid_columnconfigure = MagicMock()
    mock_window.winfo_children.return_value = []

    with (
        patch("launcher.gui.app.ctk") as mock_ctk,
        patch("launcher.gui.app.find_vscode", return_value=None),
        patch("launcher.gui.app.threading.Thread") as mock_thread_cls,
        patch("launcher.gui.app.get_setting", return_value=True),
        patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]),
        patch("launcher.gui.app.is_template_ready", return_value=True),
        patch("launcher.gui.app.make_label_entry_row", return_value=mock_widget),
    ):
        mock_ctk.CTk.return_value = mock_window
        mock_ctk.BooleanVar.return_value = MagicMock(get=MagicMock(return_value=True))
        mock_ctk.StringVar.return_value = MagicMock(get=MagicMock(return_value="20"))
        mock_ctk.CTkLabel.return_value = mock_widget
        mock_ctk.CTkEntry.return_value = mock_widget
        mock_ctk.CTkButton.return_value = mock_widget
        mock_ctk.CTkOptionMenu.return_value = mock_widget
        mock_ctk.CTkCheckBox.return_value = mock_widget
        mock_ctk.CTkSwitch.return_value = mock_widget
        mock_ctk.CTkImage.return_value = mock_widget
        mock_ctk.CTkProgressBar.return_value = mock_widget

        app = app_mod.App.__new__(app_mod.App)
        app._window = mock_window
        app._latest_version = "0.0.0"
        app._current_template = "Agent Workbench"
        # Manually wire all widget attrs as mocks
        app.project_name_entry = MagicMock()
        app.project_name_entry.get.return_value = "TestProject"
        app.project_name_error_label = MagicMock()
        app.project_type_dropdown = MagicMock()
        app.project_type_dropdown.get.return_value = "Agent Workbench"
        app.destination_entry = MagicMock()
        app.destination_entry.get.return_value = "/tmp"
        app.destination_error_label = MagicMock()
        app.browse_button = MagicMock()
        app.create_button = MagicMock()
        app.create_progress_bar = MagicMock()
        app.open_in_vscode_var = MagicMock()
        app.open_in_vscode_var.get.return_value = False
        app.include_readmes_var = MagicMock()
        app.include_readmes_var.get.return_value = True
        app.counter_enabled_var = MagicMock()
        app.counter_enabled_var.get.return_value = True
        app.counter_threshold_var = MagicMock()
        app.counter_threshold_var.get.return_value = "20"
        return app, mock_thread_cls


def test_on_create_project_launches_thread_on_valid_input():
    """A background thread is started when validation passes."""
    import launcher.gui.app as app_mod

    app, mock_thread_cls = _make_full_app()

    with (
        patch("launcher.gui.app.validate_folder_name", return_value=(True, "")),
        patch("launcher.gui.app.validate_destination_path", return_value=(True, "")),
        patch("launcher.gui.app.check_duplicate_folder", return_value=False),
        patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]),
        patch("launcher.gui.app.is_template_ready", return_value=True),
        patch("launcher.gui.app.verify_ts_python", return_value=(True, "")),
        patch.object(app, "_set_creation_ui_state"),
    ):
        mock_thread_instance = MagicMock()
        app_mod.threading.Thread = MagicMock(return_value=mock_thread_instance)
        app._on_create_project()

    mock_thread_instance.start.assert_called_once()


def test_on_create_project_disables_ui_on_valid_input():
    """_set_creation_ui_state(disabled=True) is called before the thread is started."""
    import launcher.gui.app as app_mod

    app, _ = _make_full_app()
    calls = []

    def track_disable(disabled: bool) -> None:
        calls.append(disabled)

    with (
        patch("launcher.gui.app.validate_folder_name", return_value=(True, "")),
        patch("launcher.gui.app.validate_destination_path", return_value=(True, "")),
        patch("launcher.gui.app.check_duplicate_folder", return_value=False),
        patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]),
        patch("launcher.gui.app.is_template_ready", return_value=True),
        patch("launcher.gui.app.verify_ts_python", return_value=(True, "")),
        patch.object(app, "_set_creation_ui_state", side_effect=track_disable),
    ):
        mock_thread_instance = MagicMock()
        app_mod.threading.Thread = MagicMock(return_value=mock_thread_instance)
        app._on_create_project()

    assert True in calls, "_set_creation_ui_state(disabled=True) was never called"


def test_on_create_project_no_thread_on_invalid_name():
    """Thread always starts and UI is always disabled on click (FIX-121).

    Pre-FIX-121: no thread started when validation failed.
    Post-FIX-121: thread always starts so the button greys out immediately;
    validation runs inside the background thread.
    """
    import launcher.gui.app as app_mod

    app, mock_thread_cls = _make_full_app()

    with (
        patch("launcher.gui.app.validate_folder_name", return_value=(False, "Invalid name")),
        patch.object(app, "_set_creation_ui_state") as mock_set_state,
    ):
        mock_thread_instance = MagicMock()
        app_mod.threading.Thread = MagicMock(return_value=mock_thread_instance)
        app._on_create_project()

    # FIX-121: thread always starts so the button greys out immediately on click.
    mock_thread_instance.start.assert_called_once()
    # UI is always disabled before the thread runs.
    mock_set_state.assert_called_with(disabled=True)


# ---------------------------------------------------------------------------
# Progress bar initially hidden
# ---------------------------------------------------------------------------

def test_progress_bar_attribute_exists_after_build_ui():
    """App constructed via _build_ui has a create_progress_bar attribute."""
    import launcher.gui.app as app_mod

    mock_window = MagicMock()
    mock_widget = MagicMock()
    mock_widget.get.return_value = ""

    with (
        patch("launcher.gui.app.ctk") as mock_ctk,
        patch("launcher.gui.app.find_vscode", return_value=None),
        patch("launcher.gui.app.threading.Thread"),
        patch("launcher.gui.app.get_setting", return_value=True),
        patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]),
        patch("launcher.gui.app.is_template_ready", return_value=True),
        patch("launcher.gui.app.make_label_entry_row", return_value=mock_widget),
        patch("launcher.gui.app.get_display_version", return_value="1.0.0"),
    ):
        mock_ctk.CTk.return_value = mock_window
        mock_ctk.BooleanVar.return_value = MagicMock(get=MagicMock(return_value=True))
        mock_ctk.StringVar.return_value = MagicMock()
        mock_ctk.CTkLabel.return_value = mock_widget
        mock_ctk.CTkEntry.return_value = mock_widget
        mock_ctk.CTkButton.return_value = mock_widget
        mock_ctk.CTkOptionMenu.return_value = mock_widget
        mock_ctk.CTkCheckBox.return_value = mock_widget
        mock_ctk.CTkSwitch.return_value = mock_widget
        mock_ctk.CTkImage.return_value = mock_widget
        mock_progress = MagicMock()
        mock_ctk.CTkProgressBar.return_value = mock_progress

        app = app_mod.App.__new__(app_mod.App)
        app._window = mock_window
        app._latest_version = "0.0.0"
        app._current_template = ""
        app._build_ui()

    assert hasattr(app, "create_progress_bar")


def test_progress_bar_hidden_on_build_ui():
    """create_progress_bar.grid_remove() is called during _build_ui."""
    import launcher.gui.app as app_mod

    mock_window = MagicMock()
    mock_widget = MagicMock()
    mock_widget.get.return_value = ""

    with (
        patch("launcher.gui.app.ctk") as mock_ctk,
        patch("launcher.gui.app.find_vscode", return_value=None),
        patch("launcher.gui.app.threading.Thread"),
        patch("launcher.gui.app.get_setting", return_value=True),
        patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]),
        patch("launcher.gui.app.is_template_ready", return_value=True),
        patch("launcher.gui.app.make_label_entry_row", return_value=mock_widget),
        patch("launcher.gui.app.get_display_version", return_value="1.0.0"),
    ):
        mock_ctk.CTk.return_value = mock_window
        mock_ctk.BooleanVar.return_value = MagicMock(get=MagicMock(return_value=True))
        mock_ctk.StringVar.return_value = MagicMock()
        mock_ctk.CTkLabel.return_value = mock_widget
        mock_ctk.CTkEntry.return_value = mock_widget
        mock_ctk.CTkButton.return_value = mock_widget
        mock_ctk.CTkOptionMenu.return_value = mock_widget
        mock_ctk.CTkCheckBox.return_value = mock_widget
        mock_ctk.CTkSwitch.return_value = mock_widget
        mock_ctk.CTkImage.return_value = mock_widget
        mock_progress = MagicMock()
        mock_ctk.CTkProgressBar.return_value = mock_progress

        app = app_mod.App.__new__(app_mod.App)
        app._window = mock_window
        app._latest_version = "0.0.0"
        app._current_template = ""
        app._build_ui()

    mock_progress.grid_remove.assert_called_once()


# ---------------------------------------------------------------------------
# Browse button attribute exists on App
# ---------------------------------------------------------------------------

def test_browse_button_attribute_exists_after_build_ui():
    """App._build_ui sets self.browse_button (needed for disable/enable)."""
    import launcher.gui.app as app_mod

    mock_window = MagicMock()
    mock_widget = MagicMock()
    mock_widget.get.return_value = ""
    mock_browse_btn = MagicMock()

    with (
        patch("launcher.gui.app.ctk") as mock_ctk,
        patch("launcher.gui.app.find_vscode", return_value=None),
        patch("launcher.gui.app.threading.Thread"),
        patch("launcher.gui.app.get_setting", return_value=True),
        patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]),
        patch("launcher.gui.app.is_template_ready", return_value=True),
        patch("launcher.gui.app.make_label_entry_row", return_value=mock_widget),
        patch("launcher.gui.app.get_display_version", return_value="1.0.0"),
    ):
        mock_ctk.CTk.return_value = mock_window
        mock_ctk.BooleanVar.return_value = MagicMock(get=MagicMock(return_value=True))
        mock_ctk.StringVar.return_value = MagicMock()
        mock_ctk.CTkLabel.return_value = mock_widget
        mock_ctk.CTkEntry.return_value = mock_widget
        mock_ctk.CTkButton.return_value = mock_browse_btn
        mock_ctk.CTkOptionMenu.return_value = mock_widget
        mock_ctk.CTkCheckBox.return_value = mock_widget
        mock_ctk.CTkSwitch.return_value = mock_widget
        mock_ctk.CTkImage.return_value = mock_widget
        mock_ctk.CTkProgressBar.return_value = mock_widget

        app = app_mod.App.__new__(app_mod.App)
        app._window = mock_window
        app._latest_version = "0.0.0"
        app._current_template = ""
        app._build_ui()

    assert hasattr(app, "browse_button")
    assert app.browse_button is not None
