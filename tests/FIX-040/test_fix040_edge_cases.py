"""Edge-case tests for FIX-040 — Windows update restart and stale version label.

Supplement to the Developer's test_fix040_update_restart.py (12 tests).
These tests probe boundary conditions the Developer did not cover:
  - AST-level validation that Popen receives a list literal (not string)
  - Popen args list has exactly the expected 3 elements
  - No single [Run] entry carries both skip flags simultaneously
  - Exactly two Filename entries in [Run] (not one, not three)
  - _on_install_starting button text and state
  - _on_install_starting banner text and grid visibility
  - _on_install_starting is a method defined inside the App class
  - _on_install_starting is scheduled via .after(0, ...) for thread safety
  - Correct call ordering: _on_install_starting → time.sleep → apply_update
  - os module is actually imported in applier.py

All tests are static source/AST inspections — no subprocesses are spawned.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
APPLIER_PATH = REPO_ROOT / "src" / "launcher" / "core" / "applier.py"
SETUP_ISS_PATH = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
APP_PY_PATH = REPO_ROOT / "src" / "launcher" / "gui" / "app.py"


# ---------------------------------------------------------------------------
# Helper: find a named function definition within an AST node
# ---------------------------------------------------------------------------

def _find_func_source(source: str, func_name: str) -> str | None:
    """Return the source text of the first function with *func_name*, or None."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            lines = source.splitlines()[node.lineno - 1 : node.end_lineno]
            return "\n".join(lines)
    return None


# ---------------------------------------------------------------------------
# EC-1 — _apply_windows Popen first argument is a list literal (not a string)
# ---------------------------------------------------------------------------

def test_apply_windows_popen_first_arg_is_list():
    """Popen must receive a list literal as its first arg, not a bare string."""
    source = APPLIER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_apply_windows":
            for call in ast.walk(node):
                if (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "Popen"
                ):
                    assert call.args, "Popen must be called with at least one positional arg"
                    first_arg = call.args[0]
                    assert isinstance(first_arg, ast.List), (
                        "First argument to subprocess.Popen must be a list literal, "
                        "not a string — passing a string enables shell word-splitting."
                    )
                    return
    pytest.fail("No subprocess.Popen call found inside _apply_windows")


# ---------------------------------------------------------------------------
# EC-2 — _apply_windows Popen list has exactly 3 elements
# ---------------------------------------------------------------------------

def test_apply_windows_popen_args_exactly_three_elements():
    """Popen list must have exactly 3 elements: installer_path, /SILENT, /CLOSEAPPLICATIONS."""
    source = APPLIER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_apply_windows":
            for call in ast.walk(node):
                if (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "Popen"
                ):
                    first_arg = call.args[0]
                    if not isinstance(first_arg, ast.List):
                        pytest.fail("Popen first arg is not a list — see EC-1")
                    n = len(first_arg.elts)
                    assert n == 3, (
                        f"Popen args list must contain exactly 3 elements "
                        f"(installer, /SILENT, /CLOSEAPPLICATIONS), got {n}"
                    )
                    return
    pytest.fail("No subprocess.Popen call found inside _apply_windows")


# ---------------------------------------------------------------------------
# EC-3 — No single [Run] entry carries both skip flags at the same time
# ---------------------------------------------------------------------------

def test_setup_iss_no_entry_has_both_skip_flags():
    """A single [Run] Filename line must not carry both skipifsilent and skipifnotsilent.

    Having both on the same line would mean the entry is skipped in ALL modes, so
    the launcher would never relaunch — defeating the entire fix.
    """
    content = SETUP_ISS_PATH.read_text(encoding="utf-8")
    run_section = re.search(r"\[Run\](.*?)(\[|\Z)", content, re.DOTALL)
    assert run_section is not None, "[Run] section not found in setup.iss"
    run_body = run_section.group(1)
    for line in run_body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        if "skipifsilent" in stripped and "skipifnotsilent" in stripped:
            pytest.fail(
                f"A single [Run] line carries both skipifsilent and skipifnotsilent:\n  {line}"
            )


# ---------------------------------------------------------------------------
# EC-4 — [Run] section has exactly two Filename entries (not one, not three)
# ---------------------------------------------------------------------------

def test_setup_iss_exactly_two_run_filename_entries():
    """[Run] section must have exactly 2 active Filename entries: one for interactive, one for silent."""
    content = SETUP_ISS_PATH.read_text(encoding="utf-8")
    run_section = re.search(r"\[Run\](.*?)(\[|\Z)", content, re.DOTALL)
    assert run_section is not None, "[Run] section not found in setup.iss"
    run_body = run_section.group(1)
    filename_lines = [
        line for line in run_body.splitlines()
        if line.strip().startswith("Filename:") and not line.strip().startswith(";")
    ]
    assert len(filename_lines) == 2, (
        f"[Run] section must contain exactly 2 active Filename entries "
        f"(interactive + silent), found {len(filename_lines)}"
    )


# ---------------------------------------------------------------------------
# EC-5 — _on_install_starting sets button text to "Installing..." with state disabled
# ---------------------------------------------------------------------------

def test_on_install_starting_sets_button_installing_disabled():
    """_on_install_starting must configure button state=disabled and text='Installing...'."""
    source = APP_PY_PATH.read_text(encoding="utf-8")
    func_source = _find_func_source(source, "_on_install_starting")
    assert func_source is not None, "_on_install_starting not found in app.py"
    assert '"Installing..."' in func_source or "'Installing...'" in func_source, (
        "_on_install_starting must set download_install_button text to 'Installing...'"
    )
    assert 'state="disabled"' in func_source or "state='disabled'" in func_source, (
        "_on_install_starting must set button state to disabled"
    )


# ---------------------------------------------------------------------------
# EC-6 — _on_install_starting sets the banner text to the restart message
# ---------------------------------------------------------------------------

def test_on_install_starting_sets_restart_banner_text():
    """_on_install_starting must set update_banner text to 'Installing update... App will restart.'"""
    source = APP_PY_PATH.read_text(encoding="utf-8")
    func_source = _find_func_source(source, "_on_install_starting")
    assert func_source is not None, "_on_install_starting not found in app.py"
    assert "Installing update" in func_source, (
        "_on_install_starting banner text must include 'Installing update'"
    )
    assert "App will restart" in func_source, (
        "_on_install_starting banner text must include 'App will restart'"
    )


# ---------------------------------------------------------------------------
# EC-7 — _on_install_starting shows the banner (grid()) and does not hide it
# ---------------------------------------------------------------------------

def test_on_install_starting_shows_banner_not_hides():
    """_on_install_starting must call update_banner.grid() to make it visible.

    It must NOT call grid_remove(), which would hide the banner and prevent the
    user from seeing the 'App will restart' message.
    """
    source = APP_PY_PATH.read_text(encoding="utf-8")
    func_source = _find_func_source(source, "_on_install_starting")
    assert func_source is not None, "_on_install_starting not found in app.py"
    assert "update_banner.grid()" in func_source, (
        "_on_install_starting must call update_banner.grid() to show the banner"
    )
    assert "grid_remove()" not in func_source, (
        "_on_install_starting must not call grid_remove() — the banner must be visible"
    )


# ---------------------------------------------------------------------------
# EC-8 — _on_install_starting is a method of the App class (not a module-level function)
# ---------------------------------------------------------------------------

def test_on_install_starting_defined_inside_app_class():
    """_on_install_starting must be a method defined inside the App class."""
    source = APP_PY_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "App":
            for item in ast.walk(node):
                if isinstance(item, ast.FunctionDef) and item.name == "_on_install_starting":
                    return  # found — test passes
    pytest.fail("_on_install_starting is not defined as a method inside the App class")


# ---------------------------------------------------------------------------
# EC-9 — _on_install_starting is dispatched to the main thread via .after(0, ...)
# ---------------------------------------------------------------------------

def test_on_install_starting_dispatched_via_window_after():
    """_on_install_starting must be called via self._window.after(0, ...) not directly.

    Since _download_and_apply runs on a daemon thread, direct UI calls are not
    thread-safe.  .after(0, ...) schedules the call on the tkinter main loop.
    """
    source = APP_PY_PATH.read_text(encoding="utf-8")
    func_source = _find_func_source(source, "_download_and_apply")
    assert func_source is not None, "_download_and_apply not found in app.py"
    assert ".after(0, self._on_install_starting)" in func_source, (
        "_on_install_starting must be dispatched via self._window.after(0, ...) "
        "from the daemon thread — direct GUI calls from non-main threads are unsafe"
    )


# ---------------------------------------------------------------------------
# EC-10 — Ordering: _on_install_starting → time.sleep → apply_update
# ---------------------------------------------------------------------------

def test_download_and_apply_ordering_starting_sleep_apply():
    """Ordering in _download_and_apply must be: _on_install_starting → sleep → apply_update.

    The sleep allows the tkinter event loop to process the .after() callback so
    the 'Installing...' text is rendered BEFORE os._exit() terminates the process.
    """
    source = APP_PY_PATH.read_text(encoding="utf-8")
    func_source = _find_func_source(source, "_download_and_apply")
    assert func_source is not None, "_download_and_apply not found in app.py"
    pos_starting = func_source.find("_on_install_starting")
    pos_sleep = func_source.find("time.sleep")
    pos_apply = func_source.find("apply_update")
    assert pos_starting != -1, "_download_and_apply must reference _on_install_starting"
    assert pos_sleep != -1, "_download_and_apply must call time.sleep"
    assert pos_apply != -1, "_download_and_apply must call apply_update"
    assert pos_starting < pos_sleep, (
        "_on_install_starting must be scheduled BEFORE time.sleep"
    )
    assert pos_sleep < pos_apply, (
        "time.sleep must come BEFORE apply_update so the UI renders before exit"
    )


# ---------------------------------------------------------------------------
# EC-11 — applier.py imports os (prerequisite for os._exit)
# ---------------------------------------------------------------------------

def test_applier_imports_os_module():
    """applier.py must import the os module at module level.

    Without this import, os._exit(0) would raise NameError at runtime.
    """
    source = APPLIER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "os":
                    return
    pytest.fail(
        "applier.py does not import the os module — os._exit(0) would raise NameError at runtime"
    )
