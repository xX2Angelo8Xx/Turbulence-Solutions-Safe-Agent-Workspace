"""FIX-121 — Edge-case tests: Immediate button feedback on Create Project click.

These tests cover boundary conditions and scenarios not addressed by the
primary regression suite in test_fix121_button_feedback.py.

Covers:
1. COMING_SOON guard — _set_creation_ui_state is NOT called; no thread starts
2. Thread ALWAYS starts on valid name entry (new FIX-121 behaviour)
3. Counter threshold ValueError fallback to default of 20
4. Template-not-found path re-enables UI
5. Inline error labels are cleared at the start of each _create() run
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

REPO_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _get_coming_soon_label() -> str:
    """Import _COMING_SOON_LABEL from app module at runtime to avoid coupling."""
    import launcher.gui.app as app_module
    return app_module._COMING_SOON_LABEL


# ---------------------------------------------------------------------------
# Shared helpers
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
    instance.create_button = MagicMock()
    instance.browse_button = MagicMock()
    instance.create_progress_bar = MagicMock()
    instance.counter_enabled_var = MagicMock()
    instance.counter_enabled_var.get.return_value = True
    instance.counter_threshold_var = MagicMock()
    instance.counter_threshold_var.get.return_value = "20"
    instance.include_readmes_var = MagicMock()
    instance.include_readmes_var.get.return_value = True
    return instance


# ---------------------------------------------------------------------------
# 1. COMING_SOON guard — UI must stay enabled; thread must not start
# ---------------------------------------------------------------------------

def test_coming_soon_guard_does_not_disable_ui(tmp_path):
    """Selecting the COMING_SOON dropdown entry returns early — UI never disabled.

    The guard fires BEFORE _set_creation_ui_state(disabled=True), so the
    button should remain enabled and no thread should be launched.
    """
    import launcher.gui.app as app_module

    fake_dest = tmp_path / "dest"
    fake_dest.mkdir()
    instance = _make_instance(fake_dest)
    # Simulate COMING_SOON being selected
    instance.project_type_dropdown.get.return_value = _get_coming_soon_label()

    set_state_calls: list[bool] = []

    def _record_set_state(disabled: bool) -> None:
        set_state_calls.append(disabled)

    thread_started = []

    class _CapturingThread:
        def __init__(self, target=None, daemon=False, **kwargs):
            self._target = target
        def start(self):
            thread_started.append(True)
            if self._target:
                self._target()

    with patch.object(app_module.App, "_set_creation_ui_state", side_effect=_record_set_state), \
         patch("launcher.gui.app.threading.Thread", _CapturingThread), \
         patch("launcher.gui.app.messagebox"):
        app_module.App._on_create_project(instance)

    assert not set_state_calls, (
        "_set_creation_ui_state must NOT be called when COMING_SOON is selected"
    )
    assert not thread_started, "No thread must be started when COMING_SOON is selected"


# ---------------------------------------------------------------------------
# 2. Thread always starts (new FIX-121 behaviour — contrast to old pre-fix code)
# ---------------------------------------------------------------------------

def test_thread_starts_even_on_invalid_name(tmp_path):
    """After FIX-121, a thread is ALWAYS started regardless of name validity.

    Pre-fix: validation ran before the thread, so no thread started on failure.
    Post-fix: UI is disabled first, then validation runs INSIDE the thread.
    The thread therefore starts for every code path except COMING_SOON.

    This is the correct new behaviour. (Contrast: GUI-034 test
    test_on_create_project_no_thread_on_invalid_name tests the OLD behaviour
    and must be updated separately by the developer.)
    """
    import launcher.gui.app as app_module

    fake_dest = tmp_path / "dest"
    fake_dest.mkdir()
    instance = _make_instance(fake_dest)

    thread_starts = []

    class _TrackingThread:
        def __init__(self, target=None, daemon=False, **kwargs):
            self._target = target
        def start(self):
            thread_starts.append(True)
            if self._target:
                self._target()

    with patch("launcher.gui.app.validate_folder_name", return_value=(False, "Bad name")), \
         patch("launcher.gui.app.threading.Thread", _TrackingThread), \
         patch("launcher.gui.app.messagebox"):
        app_module.App._on_create_project(instance)

    assert len(thread_starts) == 1, (
        "After FIX-121, thread must start even when name validation will fail"
    )


# ---------------------------------------------------------------------------
# 3. Counter threshold ValueError fallback
# ---------------------------------------------------------------------------

def test_counter_threshold_value_error_falls_back_to_20(tmp_path):
    """When get_counter_threshold() raises ValueError, creation uses threshold=20.

    The _create() function catches ValueError from get_counter_threshold()
    and defaults to 20, ensuring creation is never blocked by bad input.
    """
    import launcher.gui.app as app_module

    fake_dest = tmp_path / "dest"
    fake_dest.mkdir()
    fake_project = fake_dest / "SAE-TestProject"
    instance = _make_instance(fake_dest)

    # Simulate an invalid (non-integer) threshold entry
    instance.counter_threshold_var.get.return_value = "not-a-number"

    captured_threshold: list[int] = []

    def _fake_create_project(*args, counter_threshold=20, **kwargs):
        captured_threshold.append(counter_threshold)
        return fake_project

    with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
         patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
         patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
         patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]), \
         patch("launcher.gui.app._format_template_name", return_value="Coding"), \
         patch("launcher.gui.app.verify_ts_python", return_value=(True, "3.11.0")), \
         patch("launcher.gui.app.threading.Thread", _SyncThread), \
         patch("launcher.gui.app.create_project", side_effect=_fake_create_project), \
         patch("launcher.gui.app.messagebox"):
        app_module.App._on_create_project(instance)

    assert captured_threshold == [20], (
        f"Expected threshold=20 fallback when ValueError raised; got {captured_threshold}"
    )


# ---------------------------------------------------------------------------
# 4. Template not found — UI is re-enabled
# ---------------------------------------------------------------------------

def test_ui_reenabled_on_template_not_found(tmp_path):
    """When no template matches the display name, UI is re-enabled."""
    import launcher.gui.app as app_module

    fake_dest = tmp_path / "dest"
    fake_dest.mkdir()
    instance = _make_instance(fake_dest)

    with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
         patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
         patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
         patch("launcher.gui.app.list_templates", return_value=[]), \
         patch("launcher.gui.app.threading.Thread", _SyncThread), \
         patch("launcher.gui.app.messagebox") as mock_mb:
        app_module.App._on_create_project(instance)

    enable_calls = [
        c for c in instance.create_button.configure.call_args_list
        if c == call(state="normal")
    ]
    assert len(enable_calls) >= 1, "create_button must be re-enabled after template-not-found"
    mock_mb.showerror.assert_called_once()


# ---------------------------------------------------------------------------
# 5. Inline error labels are cleared at start of each _create() run
# ---------------------------------------------------------------------------

def test_inline_errors_cleared_before_revalidation(tmp_path):
    """Inline error labels are reset to '' at the start of every _create() run.

    This prevents stale error messages from a previous failed attempt being
    visible if the user corrects their input and retries.
    """
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
         patch("launcher.gui.app.create_project", return_value=fake_project), \
         patch("launcher.gui.app.messagebox"):
        app_module.App._on_create_project(instance)

    name_clear = any(
        c == call(text="") for c in instance.project_name_error_label.configure.call_args_list
    )
    dest_clear = any(
        c == call(text="") for c in instance.destination_error_label.configure.call_args_list
    )
    assert name_clear, "project_name_error_label must be cleared (text='') at start of _create()"
    assert dest_clear, "destination_error_label must be cleared (text='') at start of _create()"
