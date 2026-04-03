"""Configure pytest so that src/ is on sys.path for all tests.

This is required for the src-layout: packages live under src/ and are not
installed during development unless `pip install -e .` has been run
(deferred to INS-002).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from unittest.mock import MagicMock, patch

try:
    import tkinter.filedialog
    import tkinter.messagebox
    _HAS_TK = True
except ImportError:
    import types
    _tk_mock = MagicMock()
    tkinter = types.ModuleType("tkinter")
    tkinter.filedialog = MagicMock()
    tkinter.messagebox = MagicMock()
    sys.modules.setdefault("tkinter", _tk_mock)
    sys.modules["tkinter.filedialog"] = tkinter.filedialog
    sys.modules["tkinter.messagebox"] = tkinter.messagebox
    _HAS_TK = False

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

sys.modules["customtkinter"] = MagicMock(name="customtkinter")

_VSCODE_CMDS = frozenset({"code", "code-insiders"})


@pytest.fixture(autouse=True)
def _prevent_vscode_launch():
    """Prevent any test from accidentally launching real VS Code instances.

    Patches both the source module and the import binding in app.py so that
    no code path can reach the real subprocess.Popen call.
    """
    with patch("launcher.core.vscode.open_in_vscode", return_value=False), \
         patch("launcher.gui.app.open_in_vscode", return_value=False):
        yield


@pytest.fixture(autouse=True)
def _prevent_gui_popups():
    """Prevent real popup dialogs from appearing during tests.

    Patches tkinter.messagebox and tkinter.filedialog functions so that no
    real OS-level dialog boxes can appear during the test run.
    """
    with patch.object(tkinter.messagebox, "showinfo", return_value=None), \
         patch.object(tkinter.messagebox, "showerror", return_value=None), \
         patch.object(tkinter.messagebox, "showwarning", return_value=None), \
         patch.object(tkinter.messagebox, "askyesno", return_value=False), \
         patch.object(tkinter.filedialog, "askdirectory", return_value=""), \
         patch.object(tkinter.filedialog, "askopenfilename", return_value=""):
        yield


@pytest.fixture(autouse=True)
def _prevent_background_updates():
    """Prevent real HTTP calls to the GitHub Releases API during tests.

    Only patches the app.py local binding — NOT the source module.
    INS-009 tests directly test check_for_update and need the real function.
    """
    with patch("launcher.gui.app.check_for_update", return_value=(False, "0.0.0")):
        yield


@pytest.fixture(autouse=True)
def _mock_verify_ts_python():
    """Prevent real ts-python execution during tests (SAF-034).

    Only patches the app.py local binding so that _on_create_project() does
    not abort due to a missing ts-python shim in the test environment.
    SAF-034 tests override this fixture locally with their own patch values.
    """
    with patch("launcher.gui.app.verify_ts_python", return_value=(True, "3.11.0 (mocked)")):
        yield


@pytest.fixture(autouse=True)
def _prevent_vscode_detection():
    """Prevent shutil.which from finding a real VS Code installation.

    Defense layer 2: even if the open_in_vscode mock is bypassed (e.g. via
    module reimport), find_vscode() returns None and Popen is never reached.
    """
    original_which = shutil.which

    def _guarded_which(name, *args, **kwargs):
        if name in _VSCODE_CMDS:
            return None
        return original_which(name, *args, **kwargs)

    with patch("shutil.which", side_effect=_guarded_which):
        yield


@pytest.fixture(autouse=True)
def _subprocess_popen_sentinel():
    """Last-resort guard: raise if any code tries to Popen VS Code.

    Defense layer 3: if both open_in_vscode and shutil.which guards fail,
    this catches the actual subprocess.Popen call and raises RuntimeError
    instead of spawning a process. Non-VS-Code Popen calls pass through.
    """
    _real_popen = subprocess.Popen

    def _guarded_popen(args, *a, **kw):
        if isinstance(args, (list, tuple)) and args:
            cmd = str(args[0]).lower()
            if (
                cmd in _VSCODE_CMDS
                or cmd.endswith(os.sep + "code")
                or cmd.endswith(os.sep + "code-insiders")
                or "visual studio code" in cmd
            ):
                raise RuntimeError(
                    f"SAFETY VIOLATION: subprocess.Popen attempted to launch VS Code "
                    f"with args {args!r}. This means all higher-level guards failed. "
                    f"Report this as a critical bug."
                )
        elif isinstance(args, str):
            first = args.strip().lower().split()[0] if args.strip() else ""
            if first in _VSCODE_CMDS:
                raise RuntimeError(
                    f"SAFETY VIOLATION: subprocess.Popen attempted to launch VS Code."
                )
        return _real_popen(args, *a, **kw)

    with patch("subprocess.Popen", side_effect=_guarded_popen):
        yield


_SG_SCRIPTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "templates", "agent-workbench",
                 ".github", "hooks", "scripts")
)
_HOOK_STATE_PATH = os.path.join(_SG_SCRIPTS_DIR, ".hook_state.json")


@pytest.fixture(autouse=True)
def _prevent_hook_state_writes():
    """Prevent security_gate from writing .hook_state.json to the template directory.

    SAF-035 adds a session denial counter that persists state to disk.
    Without this fixture, any test calling security_gate.main() would write
    .hook_state.json into templates/coding/.github/hooks/scripts/, polluting
    the shipping template and making tests non-deterministic.

    In-process calls are intercepted by mocking _load_state, _save_state, and
    _get_session_id.  Subprocess calls (e.g. SAF-001 integration tests) cannot
    be intercepted, so we also delete .hook_state.json after each test as a
    safety net.
    """
    if _SG_SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, _SG_SCRIPTS_DIR)
    try:
        import security_gate
        _default_counter_cfg = {
            "counter_enabled": True,
            "lockout_threshold": 20,
        }
        with patch.object(security_gate, "_load_state", return_value={}), \
             patch.object(security_gate, "_save_state", return_value=None), \
             patch.object(security_gate, "_get_session_id", return_value=("test-fixture-session", {})), \
             patch.object(security_gate, "_load_counter_config", return_value=dict(_default_counter_cfg)):
            yield
    except (ImportError, ModuleNotFoundError):
        yield
    # Cleanup: remove .hook_state.json if created by a subprocess call
    try:
        if os.path.isfile(_HOOK_STATE_PATH):
            os.unlink(_HOOK_STATE_PATH)
    except OSError:
        pass
