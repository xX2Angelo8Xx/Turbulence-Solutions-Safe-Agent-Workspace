"""FIX-048 — Tests: Fix ts-python shim timeout and bump version to 3.0.1.

Covers:
1. Windows .cmd shim: subprocess.run is called with ["cmd.exe", "/c", shim_exe, ...]
2. Windows non-.cmd shim: no cmd.exe wrapper is used
3. stdin=subprocess.DEVNULL is always passed to subprocess.run
4. timeout= argument passed to subprocess.run is 30
5. TimeoutExpired error message says "30 seconds" (not "5 seconds")
6. Existing success behavior: (True, version_string) returned on exit code 0
7. Existing failure behavior: (False, msg) on non-zero exit code
8. Existing not-found behavior: (False, msg) when shim not on PATH
9. Windows: .cmd shim in shim dir takes priority over PATH
10. Windows: fallback .cmd from PATH also uses cmd.exe wrapper
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _import_shim_config():
    import launcher.core.shim_config as sc
    return sc


# ---------------------------------------------------------------------------
# 1. Windows .cmd shim: invoked via cmd.exe /c
# ---------------------------------------------------------------------------

def test_windows_cmd_uses_cmd_exe_wrapper(tmp_path):
    """On Windows, a .cmd shim is invoked via ['cmd.exe', '/c', shim, ...]."""
    sc = _import_shim_config()
    fake_cmd = tmp_path / "ts-python.cmd"
    fake_cmd.write_text("@echo off\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9\n"
    mock_result.stderr = ""

    with patch("platform.system", return_value="Windows"), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    args_used = mock_run.call_args[0][0]
    assert args_used[0] == "cmd.exe"
    assert args_used[1] == "/c"
    assert args_used[2] == str(fake_cmd)
    assert args_used[3] == "-c"


# ---------------------------------------------------------------------------
# 2. Windows non-.cmd shim: no cmd.exe wrapper
# ---------------------------------------------------------------------------

def test_windows_non_cmd_no_wrapper(tmp_path):
    """On Windows, a non-.cmd shim is NOT wrapped in cmd.exe /c."""
    sc = _import_shim_config()
    # No ts-python.cmd in shim dir — fallback to PATH returns a non-.cmd path
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9\n"
    mock_result.stderr = ""

    with patch("platform.system", return_value="Windows"), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    args_used = mock_run.call_args[0][0]
    assert args_used[0] != "cmd.exe"
    assert args_used[0] == "/usr/local/bin/ts-python"


# ---------------------------------------------------------------------------
# 3. stdin=subprocess.DEVNULL always passed
# ---------------------------------------------------------------------------

def test_uses_stdin_devnull():
    """subprocess.run is always called with stdin=subprocess.DEVNULL."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9\n"
    mock_result.stderr = ""

    with patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    kwargs = mock_run.call_args[1]
    assert kwargs.get("stdin") == subprocess.DEVNULL


# ---------------------------------------------------------------------------
# 4. timeout= argument is 30
# ---------------------------------------------------------------------------

def test_timeout_is_30():
    """subprocess.run is called with timeout=30."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9\n"
    mock_result.stderr = ""

    with patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        sc.verify_ts_python()

    kwargs = mock_run.call_args[1]
    assert kwargs.get("timeout") == 30


# ---------------------------------------------------------------------------
# 5. TimeoutExpired message says "30 seconds", not "5 seconds"
# ---------------------------------------------------------------------------

def test_timeout_error_message_says_30_seconds():
    """TimeoutExpired returns a message mentioning '30 seconds'."""
    sc = _import_shim_config()

    with patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="ts-python", timeout=30)):
        ok, msg = sc.verify_ts_python()

    assert ok is False
    assert "30 seconds" in msg
    assert "5 seconds" not in msg


# ---------------------------------------------------------------------------
# 6. Existing success behavior
# ---------------------------------------------------------------------------

def test_success_returns_true():
    """(True, stripped_stdout) is returned on exit code 0."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9 (default, ...)\n"
    mock_result.stderr = ""

    with patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result):
        ok, msg = sc.verify_ts_python()

    assert ok is True
    assert msg == "3.11.9 (default, ...)"


# ---------------------------------------------------------------------------
# 7. Existing failure behavior: non-zero exit
# ---------------------------------------------------------------------------

def test_nonzero_exit_returns_false():
    """(False, msg containing exit code) on non-zero exit."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 2
    mock_result.stdout = ""
    mock_result.stderr = "critical error"

    with patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result):
        ok, msg = sc.verify_ts_python()

    assert ok is False
    assert "2" in msg
    assert "critical error" in msg


# ---------------------------------------------------------------------------
# 8. Shim not found on PATH
# ---------------------------------------------------------------------------

def test_shim_not_found_returns_false():
    """(False, msg) when shutil.which returns None."""
    sc = _import_shim_config()

    with patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value=None):
        ok, msg = sc.verify_ts_python()

    assert ok is False
    assert "not found" in msg.lower()


# ---------------------------------------------------------------------------
# 9. Windows: .cmd in shim dir takes priority over PATH
# ---------------------------------------------------------------------------

def test_windows_shim_dir_used_first(tmp_path):
    """On Windows, ts-python.cmd in shim dir is preferred over PATH."""
    sc = _import_shim_config()
    fake_cmd = tmp_path / "ts-python.cmd"
    fake_cmd.write_text("@echo off\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.12.0\n"
    mock_result.stderr = ""

    with patch("platform.system", return_value="Windows"), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("shutil.which", return_value="C:\\Windows\\ts-python.cmd"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    # cmd.exe /c <shim_dir_path> should be used, not the PATH one
    args_used = mock_run.call_args[0][0]
    assert args_used[0] == "cmd.exe"
    assert args_used[2] == str(fake_cmd)


# ---------------------------------------------------------------------------
# 10. Windows: fallback .cmd from PATH also gets cmd.exe wrapper
# ---------------------------------------------------------------------------

def test_windows_fallback_to_path_cmd_wrapper(tmp_path):
    """On Windows, a .cmd from PATH fallback also uses cmd.exe /c."""
    sc = _import_shim_config()
    # No ts-python.cmd in shim dir (tmp_path is empty)

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.5\n"
    mock_result.stderr = ""

    with patch("platform.system", return_value="Windows"), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("shutil.which", return_value="C:\\Users\\User\\AppData\\Local\\TurbulenceSolutions\\bin\\ts-python.cmd"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    args_used = mock_run.call_args[0][0]
    assert args_used[0] == "cmd.exe"
    assert args_used[1] == "/c"
    assert args_used[2].endswith(".cmd")
