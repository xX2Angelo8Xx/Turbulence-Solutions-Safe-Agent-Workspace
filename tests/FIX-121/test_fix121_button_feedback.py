"""FIX-121 — Regression tests: Immediate button feedback on Create Project click.

Verifies that _set_creation_ui_state(disabled=True) is called before any
validation, so the button greys out and progress bar starts immediately on
click (BUG-206 fix).

Covers:
1. UI is disabled before validation runs
2. UI re-enables when name validation fails (inline error shown)
3. UI re-enables when destination validation fails (inline error shown)
4. UI re-enables when duplicate folder check fails (inline error shown)
5. UI re-enables when verify_ts_python fails (error dialog shown)
6. Error dialog contains the shim failure message
7. Full success flow: create_project is called and UI re-enables via _on_creation_complete
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

REPO_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _SyncThread:
    """Drop-in for threading.Thread that runs the target synchronously."""
    def __init__(self, target=None, daemon=False, **kwargs):
        self._target = target

    def start(self) -> None:
        if self._target:
            self._target()


def _make_instance(fake_dest: Path) -> object:
    """Build a minimal bare App instance with all required widget mocks."""
    import launcher.gui.app as app_module

    mock_window = MagicMock()
    mock_window.after.side_effect = lambda ms, cb: cb()

    instance = object.__new__(app_module.App)
    instance._window = mock_window
    instance.project_name_entry = MagicMock()
    instance.project_name_entry.get.return_value = "TestProject"
    instance.project_type_dropdown = MagicMock()
    instance.project_type_dropdown.get.return_value = "Coding"
    instance.destination_entry = MagicMock()
    instance.destination_entry.get.return_value = str(fake_dest)
    instance.project_name_error_label = MagicMock()
    instance.destination_error_label = MagicMock()
    instance.open_in_vscode_var = MagicMock()
    instance.open_in_vscode_var.get.return_value = False
    instance._coming_soon_options = set()
    instance._current_template = "Coding"
    # Widgets controlled by _set_creation_ui_state (GUI-034 / FIX-121).
    instance.create_button = MagicMock()
    instance.browse_button = MagicMock()
    instance.create_progress_bar = MagicMock()
    # Counter config attributes (GUI-020 / SAF-036).
    instance.counter_enabled_var = MagicMock()
    instance.counter_enabled_var.get.return_value = True
    instance.counter_threshold_var = MagicMock()
    instance.counter_threshold_var.get.return_value = "20"
    instance.include_readmes_var = MagicMock()
    instance.include_readmes_var.get.return_value = True
    return instance


# ---------------------------------------------------------------------------
# 1. UI is disabled before validation runs (regression: BUG-206)
# ---------------------------------------------------------------------------

def test_ui_disabled_before_validation(tmp_path):
    """_set_creation_ui_state(disabled=True) must be called before validation.

    BUG-206: previously the UI was only disabled after verify_ts_python(),
    causing a 1-2 second freeze. After FIX-121 the button greys out immediately.
    """
    import launcher.gui.app as app_module

    fake_dest = tmp_path / "dest"
    fake_dest.mkdir()
    instance = _make_instance(fake_dest)

    call_order: list[str] = []

    def _record_ui_disable(disabled: bool) -> None:
        if disabled:
            call_order.append("ui_disabled")

    def _record_validation(*_a, **_kw):
        call_order.append("validation")
        return (True, "")

    with patch.object(app_module.App, "_set_creation_ui_state", side_effect=_record_ui_disable), \
         patch("launcher.gui.app.validate_folder_name", side_effect=_record_validation), \
         patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
         patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
         patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]), \
         patch("launcher.gui.app._format_template_name", return_value="Coding"), \
         patch("launcher.gui.app.verify_ts_python", return_value=(True, "3.11.0")), \
         patch("launcher.gui.app.threading.Thread", _SyncThread), \
         patch("launcher.gui.app.create_project", return_value=fake_dest / "SAE-TestProject"), \
         patch("launcher.gui.app.messagebox"):
        app_module.App._on_create_project(instance)

    assert "ui_disabled" in call_order, "_set_creation_ui_state(disabled=True) was never called"
    assert "validation" in call_order, "validate_folder_name was never called"
    ui_idx = call_order.index("ui_disabled")
    val_idx = call_order.index("validation")
    assert ui_idx < val_idx, (
        f"UI must be disabled (index {ui_idx}) BEFORE validation runs (index {val_idx})"
    )


# ---------------------------------------------------------------------------
# 2. UI re-enables on invalid name
# ---------------------------------------------------------------------------

def test_ui_reenabled_on_invalid_name(tmp_path):
    """When name validation fails, UI is re-enabled and inline error is shown."""
    import launcher.gui.app as app_module

    fake_dest = tmp_path / "dest"
    fake_dest.mkdir()
    instance = _make_instance(fake_dest)

    with patch("launcher.gui.app.validate_folder_name", return_value=(False, "Invalid name")), \
         patch("launcher.gui.app.threading.Thread", _SyncThread), \
         patch("launcher.gui.app.messagebox"):
        app_module.App._on_create_project(instance)

    # Inline error displayed.
    instance.project_name_error_label.configure.assert_called_with(text="Invalid name")
    # UI re-enabled: create_button state set to "normal".
    disable_calls = [c for c in instance.create_button.configure.call_args_list
                     if c == call(state="disabled")]
    enable_calls = [c for c in instance.create_button.configure.call_args_list
                    if c == call(state="normal")]
    assert len(disable_calls) >= 1, "create_button must be disabled initially"
    assert len(enable_calls) >= 1, "create_button must be re-enabled after failure"


# ---------------------------------------------------------------------------
# 3. UI re-enables on invalid destination
# ---------------------------------------------------------------------------

def test_ui_reenabled_on_invalid_dest(tmp_path):
    """When destination validation fails, UI is re-enabled and inline error is shown."""
    import launcher.gui.app as app_module

    fake_dest = tmp_path / "dest"
    fake_dest.mkdir()
    instance = _make_instance(fake_dest)

    with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
         patch("launcher.gui.app.validate_destination_path", return_value=(False, "Bad path")), \
         patch("launcher.gui.app.threading.Thread", _SyncThread), \
         patch("launcher.gui.app.messagebox"):
        app_module.App._on_create_project(instance)

    instance.destination_error_label.configure.assert_called_with(text="Bad path")
    enable_calls = [c for c in instance.create_button.configure.call_args_list
                    if c == call(state="normal")]
    assert len(enable_calls) >= 1, "create_button must be re-enabled after dest failure"


# ---------------------------------------------------------------------------
# 4. UI re-enables on duplicate folder
# ---------------------------------------------------------------------------

def test_ui_reenabled_on_duplicate_folder(tmp_path):
    """When duplicate folder check fails, UI is re-enabled and inline error is shown."""
    import launcher.gui.app as app_module

    fake_dest = tmp_path / "dest"
    fake_dest.mkdir()
    instance = _make_instance(fake_dest)

    with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
         patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
         patch("launcher.gui.app.check_duplicate_folder", return_value=True), \
         patch("launcher.gui.app.threading.Thread", _SyncThread), \
         patch("launcher.gui.app.messagebox"):
        app_module.App._on_create_project(instance)

    name_err_calls = [
        c for c in instance.project_name_error_label.configure.call_args_list
        if "already exists" in str(c)
    ]
    assert len(name_err_calls) >= 1, "Duplicate folder inline error must be shown"
    enable_calls = [c for c in instance.create_button.configure.call_args_list
                    if c == call(state="normal")]
    assert len(enable_calls) >= 1, "create_button must be re-enabled after duplicate"


# ---------------------------------------------------------------------------
# 5. UI re-enables on shim failure
# ---------------------------------------------------------------------------

def test_ui_reenabled_on_shim_failure(tmp_path):
    """When verify_ts_python fails, UI is re-enabled."""
    import launcher.gui.app as app_module

    fake_dest = tmp_path / "dest"
    fake_dest.mkdir()
    instance = _make_instance(fake_dest)

    with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
         patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
         patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
         patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]), \
         patch("launcher.gui.app._format_template_name", return_value="Coding"), \
         patch("launcher.gui.app.verify_ts_python", return_value=(False, "shim gone")), \
         patch("launcher.gui.app.threading.Thread", _SyncThread), \
         patch("launcher.gui.app.messagebox"):
        app_module.App._on_create_project(instance)

    enable_calls = [c for c in instance.create_button.configure.call_args_list
                    if c == call(state="normal")]
    assert len(enable_calls) >= 1, "create_button must be re-enabled after shim failure"


# ---------------------------------------------------------------------------
# 6. Error dialog shown on shim failure
# ---------------------------------------------------------------------------

def test_error_message_shown_on_shim_failure(tmp_path):
    """messagebox.showerror is called with the correct message when shim fails."""
    import launcher.gui.app as app_module

    fake_dest = tmp_path / "dest"
    fake_dest.mkdir()
    instance = _make_instance(fake_dest)

    with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
         patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
         patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
         patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]), \
         patch("launcher.gui.app._format_template_name", return_value="Coding"), \
         patch("launcher.gui.app.verify_ts_python", return_value=(False, "shim detail msg")), \
         patch("launcher.gui.app.threading.Thread", _SyncThread), \
         patch("launcher.gui.app.messagebox") as mock_mb:
        app_module.App._on_create_project(instance)

    mock_mb.showerror.assert_called_once()
    _, error_msg = mock_mb.showerror.call_args[0]
    assert "bundled Python runtime is not accessible" in error_msg
    assert "shim detail msg" in error_msg


# ---------------------------------------------------------------------------
# 7. Successful creation proceeds end-to-end
# ---------------------------------------------------------------------------

def test_create_proceeds_on_valid_inputs(tmp_path):
    """create_project is called and success dialog shown when all inputs are valid."""
    import launcher.gui.app as app_module

    fake_dest = tmp_path / "dest"
    fake_dest.mkdir()
    fake_project = fake_dest / "SAE-TestProject"
    instance = _make_instance(fake_dest)

    with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
         patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
         patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
         patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]), \
         patch("launcher.gui.app._format_template_name", return_value="Coding"), \
         patch("launcher.gui.app.verify_ts_python", return_value=(True, "3.11.0")), \
         patch("launcher.gui.app.threading.Thread", _SyncThread), \
         patch("launcher.gui.app.create_project", return_value=fake_project) as mock_cp, \
         patch("launcher.gui.app.messagebox") as mock_mb:
        app_module.App._on_create_project(instance)

    mock_cp.assert_called_once()
    mock_mb.showinfo.assert_called_once()
    _, success_msg = mock_mb.showinfo.call_args[0]
    assert "TestProject" in success_msg
