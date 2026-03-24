"""SAF-034 — Tests: Verify ts-python before workspace creation.

Covers:
1. verify_ts_python() returns (True, version) when shim runs successfully
2. verify_ts_python() returns (False, msg) when shim is not found on PATH
3. verify_ts_python() returns (False, msg) when shim returns non-zero exit code
4. verify_ts_python() returns (False, msg) on subprocess.TimeoutExpired
5. verify_ts_python() returns (False, msg) on FileNotFoundError
6. verify_ts_python() returns (False, msg) on OSError
7. Windows: shim directory candidate is tried first
8. Windows: falls back to PATH when shim dir has no ts-python.cmd
9. Unix: uses shutil.which("ts-python")
10. Unix: returns (False, ...) when ts-python not on PATH
11. app._on_create_project() blocks workspace creation when shim fails
12. app._on_create_project() shows error dialog with the standard message when shim fails
13. app._on_create_project() proceeds normally when shim passes
14. app._on_create_project() error dialog includes technical detail from verify_ts_python
15. verify_ts_python() never uses shell=True (security rule)
16. verify_ts_python() uses list args (not string) for subprocess.run
17. Windows: ts-python.cmd in shim dir takes precedence over PATH entry
18. Timeout message includes "30 seconds"
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _import_shim_config():
    import launcher.core.shim_config as sc
    return sc


# ---------------------------------------------------------------------------
# 1. Success: shim found on PATH and exits 0
# ---------------------------------------------------------------------------

def test_verify_ts_python_success_unix():
    """Returns (True, stripped stdout) when shim runs successfully."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.0 (default, ...)\n"
    mock_result.stderr = ""
    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()
    assert ok is True
    assert msg == "3.11.0 (default, ...)"


# ---------------------------------------------------------------------------
# 2. Shim not found on PATH
# ---------------------------------------------------------------------------

def test_verify_ts_python_not_found_on_path():
    """Returns (False, ...) when python-path.txt is not configured."""
    sc = _import_shim_config()
    with patch("launcher.core.shim_config.read_python_path", return_value=None), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value=None):
        ok, msg = sc.verify_ts_python()
    assert ok is False
    assert "not found" in msg.lower()


# ---------------------------------------------------------------------------
# 3. Non-zero exit code
# ---------------------------------------------------------------------------

def test_verify_ts_python_nonzero_exit():
    """Returns (False, ...) when shim exits with non-zero return code."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "some error"
    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result):
        ok, msg = sc.verify_ts_python()
    assert ok is False
    assert "1" in msg  # exit code present
    assert "some error" in msg


# ---------------------------------------------------------------------------
# 4. TimeoutExpired
# ---------------------------------------------------------------------------

def test_verify_ts_python_timeout():
    """Returns (False, ...) when subprocess times out."""
    sc = _import_shim_config()
    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="ts-python", timeout=5)):
        ok, msg = sc.verify_ts_python()
    assert ok is False
    assert "timed out" in msg.lower()


# ---------------------------------------------------------------------------
# 5. FileNotFoundError
# ---------------------------------------------------------------------------

def test_verify_ts_python_file_not_found():
    """Returns (False, ...) when the executable path doesn't exist at call time."""
    sc = _import_shim_config()
    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", side_effect=FileNotFoundError("no such file")):
        ok, msg = sc.verify_ts_python()
    assert ok is False
    assert "not found" in msg.lower()


# ---------------------------------------------------------------------------
# 6. OSError
# ---------------------------------------------------------------------------

def test_verify_ts_python_os_error():
    """Returns (False, ...) on generic OSError."""
    sc = _import_shim_config()
    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", side_effect=OSError("permission denied")):
        ok, msg = sc.verify_ts_python()
    assert ok is False
    assert "permission denied" in msg.lower()


# ---------------------------------------------------------------------------
# 7. Windows: shim directory candidate tried first
# ---------------------------------------------------------------------------

def test_verify_ts_python_windows_uses_shim_dir_when_exists(tmp_path):
    """On Windows, ts-python.cmd in shim dir is found during shim existence check."""
    sc = _import_shim_config()
    fake_cmd = tmp_path / "ts-python.cmd"
    fake_cmd.write_text("@echo off\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.12.0\n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Windows"), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    # FIX-050: verify_ts_python now invokes Python directly (no cmd.exe wrapper)
    args_used = mock_run.call_args[0][0]
    assert args_used[1] == "-c"
    assert "sys.version" in args_used[2]


# ---------------------------------------------------------------------------
# 8. Windows: falls back to PATH when shim dir has no ts-python.cmd
# ---------------------------------------------------------------------------

def test_verify_ts_python_windows_fallback_to_path(tmp_path):
    """On Windows, falls back to PATH when ts-python.cmd absent from shim dir."""
    sc = _import_shim_config()
    # tmp_path has no ts-python.cmd

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.5\n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Windows"), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("shutil.which", return_value="C:\\Windows\\ts-python.cmd"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    # FIX-050: verify_ts_python invokes Python directly, not the shim via cmd.exe
    args_used = mock_run.call_args[0][0]
    assert args_used[1] == "-c"
    assert "sys.version" in args_used[2]


# ---------------------------------------------------------------------------
# 9. Unix: uses shutil.which("ts-python")
# ---------------------------------------------------------------------------

def test_verify_ts_python_unix_uses_which():
    """On Unix, shutil.which('ts-python') is used to locate the shim."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.10.0\n"
    mock_result.stderr = ""

    captured_which_calls = []
    def _which(name, *a, **kw):
        captured_which_calls.append(name)
        if name == "ts-python":
            return "/opt/ts/bin/ts-python"
        return None

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", side_effect=_which), \
         patch("subprocess.run", return_value=mock_result):
        ok, msg = sc.verify_ts_python()

    assert ok is True
    assert "ts-python" in captured_which_calls


# ---------------------------------------------------------------------------
# 10. Unix: not found on PATH
# ---------------------------------------------------------------------------

def test_verify_ts_python_unix_not_on_path():
    """On Unix, returns (False, ...) when python-path.txt not configured."""
    sc = _import_shim_config()
    with patch("launcher.core.shim_config.read_python_path", return_value=None), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value=None):
        ok, msg = sc.verify_ts_python()
    assert ok is False
    assert "not found" in msg.lower()


# ---------------------------------------------------------------------------
# 11. app._on_create_project() blocks creation when shim fails
# ---------------------------------------------------------------------------

def test_on_create_project_blocked_when_shim_fails(tmp_path):
    """Workspace creation is aborted when verify_ts_python returns False."""
    import launcher.gui.app as app_module

    fake_dest = tmp_path / "dest"
    fake_dest.mkdir()

    instance = object.__new__(app_module.App)
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

    create_project_calls = []

    with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
         patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
         patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
         patch("launcher.gui.app.list_templates", return_value=["coding"]), \
         patch("launcher.gui.app._format_template_name", return_value="Coding"), \
         patch("launcher.gui.app.verify_ts_python", return_value=(False, "shim not found")), \
         patch("launcher.gui.app.create_project", side_effect=lambda *a, **kw: create_project_calls.append(a)) as mock_cp, \
         patch("launcher.gui.app.messagebox") as mock_mb:
        app_module.App._on_create_project(instance)

    assert mock_cp.call_count == 0, "create_project must NOT be called when shim fails"


# ---------------------------------------------------------------------------
# 12. Error dialog shown with standard message when shim fails
# ---------------------------------------------------------------------------

def test_on_create_project_shows_error_dialog_when_shim_fails(tmp_path):
    """messagebox.showerror is called with the standard user-friendly message."""
    import launcher.gui.app as app_module

    fake_dest = tmp_path / "dest"
    fake_dest.mkdir()

    instance = object.__new__(app_module.App)
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

    with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
         patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
         patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
         patch("launcher.gui.app.list_templates", return_value=["coding"]), \
         patch("launcher.gui.app._format_template_name", return_value="Coding"), \
         patch("launcher.gui.app.verify_ts_python", return_value=(False, "shim missing")), \
         patch("launcher.gui.app.create_project"), \
         patch("launcher.gui.app.messagebox") as mock_mb:
        app_module.App._on_create_project(instance)

    mock_mb.showerror.assert_called_once()
    _, error_msg = mock_mb.showerror.call_args[0]
    assert "bundled Python runtime is not accessible" in error_msg
    assert "Settings > Relocate Python Runtime" in error_msg


# ---------------------------------------------------------------------------
# 13. Proceeds normally when shim passes
# ---------------------------------------------------------------------------

def test_on_create_project_proceeds_when_shim_ok(tmp_path):
    """Workspace creation proceeds normally when verify_ts_python returns True."""
    import launcher.gui.app as app_module

    fake_dest = tmp_path / "dest"
    fake_dest.mkdir()
    fake_project = fake_dest / "TS-SAE-TestProject"

    instance = object.__new__(app_module.App)
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
    # GUI-020: _on_create_project reads counter config from these attributes.
    instance.counter_enabled_var = MagicMock()
    instance.counter_enabled_var.get.return_value = True
    instance.counter_threshold_var = MagicMock()
    instance.counter_threshold_var.get.return_value = "20"

    with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
         patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
         patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
         patch("launcher.gui.app.list_templates", return_value=["coding"]), \
         patch("launcher.gui.app._format_template_name", return_value="Coding"), \
         patch("launcher.gui.app.verify_ts_python", return_value=(True, "3.11.0")), \
         patch("launcher.gui.app.create_project", return_value=fake_project) as mock_cp, \
         patch("launcher.gui.app.messagebox"):
        app_module.App._on_create_project(instance)

    mock_cp.assert_called_once()


# ---------------------------------------------------------------------------
# 14. Error dialog includes technical detail
# ---------------------------------------------------------------------------

def test_on_create_project_error_dialog_includes_details(tmp_path):
    """The showerror message includes the technical detail from verify_ts_python."""
    import launcher.gui.app as app_module

    fake_dest = tmp_path / "dest"
    fake_dest.mkdir()

    instance = object.__new__(app_module.App)
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

    with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
         patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
         patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
         patch("launcher.gui.app.list_templates", return_value=["coding"]), \
         patch("launcher.gui.app._format_template_name", return_value="Coding"), \
         patch("launcher.gui.app.verify_ts_python", return_value=(False, "ts-python exited with code 127: command not found")), \
         patch("launcher.gui.app.create_project"), \
         patch("launcher.gui.app.messagebox") as mock_mb:
        app_module.App._on_create_project(instance)

    _, error_msg = mock_mb.showerror.call_args[0]
    assert "ts-python exited with code 127" in error_msg


# ---------------------------------------------------------------------------
# 15. Security: shell=True is never used
# ---------------------------------------------------------------------------

def test_verify_ts_python_never_uses_shell_true():
    """subprocess.run must never be called with shell=True."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.0\n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        sc.verify_ts_python()

    kwargs = mock_run.call_args[1]
    assert kwargs.get("shell") is not True, "shell=True must never be used"


# ---------------------------------------------------------------------------
# 16. Security: list args used (not string)
# ---------------------------------------------------------------------------

def test_verify_ts_python_uses_list_args():
    """subprocess.run must receive a list, never a bare string command."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.0\n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        sc.verify_ts_python()

    positional_args = mock_run.call_args[0][0]
    assert isinstance(positional_args, list), "subprocess.run must receive a list of args"
    assert len(positional_args) == 3
    assert positional_args[1] == "-c"
    assert "sys.version" in positional_args[2]


# ---------------------------------------------------------------------------
# 17. Windows: shim dir takes precedence over PATH
# ---------------------------------------------------------------------------

def test_verify_ts_python_windows_shim_dir_takes_precedence(tmp_path):
    """On Windows, shim dir ts-python.cmd is checked for existence even if PATH also has it."""
    sc = _import_shim_config()
    fake_cmd = tmp_path / "ts-python.cmd"
    fake_cmd.write_text("@echo off\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.12.0\n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    # Ensure PATH also reports a different path — shim dir must win for existence check.
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Windows"), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("shutil.which", return_value="C:\\different\\ts-python.cmd"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, _ = sc.verify_ts_python()

    assert ok is True
    # FIX-050: Python is invoked directly, not via cmd.exe /c shim
    args_used = mock_run.call_args[0][0]
    assert args_used[1] == "-c"
    assert "sys.version" in args_used[2]


# ---------------------------------------------------------------------------
# 18. Timeout message includes "30 seconds"
# ---------------------------------------------------------------------------

def test_verify_ts_python_timeout_message_mentions_30_seconds():
    """Timeout failure message must mention the 30-second timeout value."""
    sc = _import_shim_config()
    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="ts-python", timeout=30)):
        ok, msg = sc.verify_ts_python()
    assert ok is False
    assert "30" in msg
