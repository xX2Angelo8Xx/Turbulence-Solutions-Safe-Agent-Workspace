"""Tests for FIX-040: Fix Windows update restart and stale version label.

Covers BUG-073 (stale version label) and BUG-074 (no restart after update).
All tests are static inspections — no subprocesses are launched.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APPLIER_PATH = REPO_ROOT / "src" / "launcher" / "core" / "applier.py"
SETUP_ISS_PATH = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
APP_PY_PATH = REPO_ROOT / "src" / "launcher" / "gui" / "app.py"


# ---------------------------------------------------------------------------
# Test 1 — _apply_windows uses os._exit(0) not sys.exit(0)
# ---------------------------------------------------------------------------

def test_apply_windows_uses_os_exit():
    """_apply_windows must call os._exit(0) to terminate from any thread."""
    source = APPLIER_PATH.read_text(encoding="utf-8")
    # Extract only the _apply_windows function body for targeted checks
    tree = ast.parse(source)
    func_source = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_apply_windows":
            func_lines = source.splitlines()[node.lineno - 1 : node.end_lineno]
            func_source = "\n".join(func_lines)
            break
    assert func_source is not None, "_apply_windows not found in applier.py"
    assert "os._exit(0)" in func_source, "_apply_windows must use os._exit(0)"


# ---------------------------------------------------------------------------
# Test 2 — _apply_windows does NOT use sys.exit
# ---------------------------------------------------------------------------

def test_apply_windows_no_sys_exit():
    """sys.exit in _apply_windows fails to terminate from a daemon thread."""
    source = APPLIER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    func_source = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_apply_windows":
            func_lines = source.splitlines()[node.lineno - 1 : node.end_lineno]
            func_source = "\n".join(func_lines)
            break
    assert func_source is not None, "_apply_windows not found in applier.py"
    # Strip comment lines before checking — the explanatory comment may reference
    # sys.exit, but no actual call should exist.
    non_comment_lines = [
        line for line in func_source.splitlines()
        if not line.lstrip().startswith("#")
    ]
    non_comment_source = "\n".join(non_comment_lines)
    assert "sys.exit" not in non_comment_source, "_apply_windows must not call sys.exit()"


# ---------------------------------------------------------------------------
# Test 3 — _apply_windows uses subprocess.Popen with list args, no shell=True
# ---------------------------------------------------------------------------

def test_apply_windows_popen_list_no_shell():
    """_apply_windows must use a list for Popen args and shell=False."""
    source = APPLIER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    func_source = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_apply_windows":
            func_lines = source.splitlines()[node.lineno - 1 : node.end_lineno]
            func_source = "\n".join(func_lines)
            break
    assert func_source is not None
    assert "subprocess.Popen" in func_source
    assert "shell=True" not in func_source
    assert "shell=False" in func_source


# ---------------------------------------------------------------------------
# Test 4 — _apply_windows passes /SILENT and /CLOSEAPPLICATIONS
# ---------------------------------------------------------------------------

def test_apply_windows_correct_flags():
    """Installer must be called with /SILENT and /CLOSEAPPLICATIONS."""
    source = APPLIER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    func_source = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_apply_windows":
            func_lines = source.splitlines()[node.lineno - 1 : node.end_lineno]
            func_source = "\n".join(func_lines)
            break
    assert func_source is not None
    assert '"/SILENT"' in func_source or "'/SILENT'" in func_source
    assert '"/CLOSEAPPLICATIONS"' in func_source or "'/CLOSEAPPLICATIONS'" in func_source


# ---------------------------------------------------------------------------
# Test 5 — setup.iss [Run] has postinstall/skipifsilent entry for interactive
# ---------------------------------------------------------------------------

def test_setup_iss_has_postinstall_skipifsilent_entry():
    """Interactive-install [Run] entry must keep postinstall and skipifsilent."""
    content = SETUP_ISS_PATH.read_text(encoding="utf-8")
    # Find the [Run] section
    run_section = re.search(r"\[Run\](.*?)(\[|\Z)", content, re.DOTALL)
    assert run_section is not None, "[Run] section not found in setup.iss"
    run_body = run_section.group(1)
    assert "postinstall" in run_body, "[Run] must have a postinstall entry"
    assert "skipifsilent" in run_body, "[Run] must have skipifsilent for interactive"


# ---------------------------------------------------------------------------
# Test 6 — setup.iss [Run] has a second entry with skipifnotsilent
# ---------------------------------------------------------------------------

def test_setup_iss_has_skipifnotsilent_entry():
    """Silent-install [Run] entry must have skipifnotsilent so it only runs in /SILENT mode."""
    content = SETUP_ISS_PATH.read_text(encoding="utf-8")
    run_section = re.search(r"\[Run\](.*?)(\[|\Z)", content, re.DOTALL)
    assert run_section is not None, "[Run] section not found in setup.iss"
    run_body = run_section.group(1)
    assert "skipifnotsilent" in run_body, "[Run] must have a skipifnotsilent entry for silent relaunch"


# ---------------------------------------------------------------------------
# Test 7 — setup.iss silent entry launches the app executable
# ---------------------------------------------------------------------------

def test_setup_iss_silent_entry_launches_exe():
    """Silent [Run] entry must reference {app}\\{#MyAppExeName}."""
    content = SETUP_ISS_PATH.read_text(encoding="utf-8")
    run_section = re.search(r"\[Run\](.*?)(\[|\Z)", content, re.DOTALL)
    assert run_section is not None
    run_body = run_section.group(1)
    # Find the line(s) with skipifnotsilent
    silent_lines = [
        line for line in run_body.splitlines()
        if "skipifnotsilent" in line
    ]
    assert silent_lines, "No skipifnotsilent line found in [Run]"
    for line in silent_lines:
        assert "{app}" in line and "MyAppExeName" in line, (
            "Silent relaunch entry must reference {app}\\{#MyAppExeName}"
        )


# ---------------------------------------------------------------------------
# Test 8 — setup.iss silent entry has nowait flag
# ---------------------------------------------------------------------------

def test_setup_iss_silent_entry_has_nowait():
    """Silent [Run] entry must have the nowait flag."""
    content = SETUP_ISS_PATH.read_text(encoding="utf-8")
    run_section = re.search(r"\[Run\](.*?)(\[|\Z)", content, re.DOTALL)
    assert run_section is not None
    run_body = run_section.group(1)
    silent_lines = [
        line for line in run_body.splitlines()
        if "skipifnotsilent" in line
    ]
    assert silent_lines, "No skipifnotsilent line found in [Run]"
    for line in silent_lines:
        assert "nowait" in line, "Silent relaunch entry must have nowait flag"


# ---------------------------------------------------------------------------
# Test 9 — app.py _download_and_apply updates UI before apply_update
# ---------------------------------------------------------------------------

def test_app_ui_update_before_apply_update():
    """_download_and_apply must call _on_install_starting before apply_update."""
    source = APP_PY_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    # Find _download_and_apply nested inside _on_install_update
    func_source = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_download_and_apply":
            func_lines = source.splitlines()[node.lineno - 1 : node.end_lineno]
            func_source = "\n".join(func_lines)
            break

    assert func_source is not None, "_download_and_apply not found in app.py"

    # _on_install_starting must appear before apply_update
    pos_starting = func_source.find("_on_install_starting")
    pos_apply = func_source.find("apply_update")
    assert pos_starting != -1, "_download_and_apply must call _on_install_starting"
    assert pos_apply != -1, "_download_and_apply must call apply_update"
    assert pos_starting < pos_apply, (
        "_on_install_starting must be called BEFORE apply_update in _download_and_apply"
    )


# ---------------------------------------------------------------------------
# Test 10 — no shell=True anywhere in applier.py (security regression)
# ---------------------------------------------------------------------------

def test_applier_no_shell_true_anywhere():
    """applier.py must never pass shell=True to any subprocess call."""
    source = APPLIER_PATH.read_text(encoding="utf-8")
    assert "shell=True" not in source, "applier.py must not use shell=True anywhere"


# ---------------------------------------------------------------------------
# Test 11 — _apply_macos still uses sys.exit (no regression)
# ---------------------------------------------------------------------------

def test_apply_macos_unchanged():
    """_apply_macos must NOT be changed to os._exit — sys.exit is correct there."""
    source = APPLIER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    func_source = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_apply_macos":
            func_lines = source.splitlines()[node.lineno - 1 : node.end_lineno]
            func_source = "\n".join(func_lines)
            break
    assert func_source is not None, "_apply_macos not found in applier.py"
    assert "sys.exit(0)" in func_source, "_apply_macos must still use sys.exit(0)"
    assert "os._exit" not in func_source, "_apply_macos must not be changed to os._exit"


# ---------------------------------------------------------------------------
# Test 12 — _apply_linux unchanged (no regression)
# ---------------------------------------------------------------------------

def test_apply_linux_unchanged():
    """_apply_linux must use os.execv and not call os._exit (no regression)."""
    source = APPLIER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    func_source = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_apply_linux":
            func_lines = source.splitlines()[node.lineno - 1 : node.end_lineno]
            func_source = "\n".join(func_lines)
            break
    assert func_source is not None, "_apply_linux not found in applier.py"
    assert "os.execv" in func_source, "_apply_linux must still use os.execv"
    assert "os._exit" not in func_source, "_apply_linux must not be changed to os._exit"
