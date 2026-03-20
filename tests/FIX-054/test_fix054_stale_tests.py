"""FIX-054 — Regression tests: verify FIX-048 tests pass after FIX-050 changes.

FIX-050 removed the cmd.exe /c wrapper from verify_ts_python(). These tests
confirm the function uses direct Python invocation and that all FIX-048 tests
remain passing.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _import_shim_config():
    import launcher.core.shim_config as sc
    return sc


# ---------------------------------------------------------------------------
# Regression: verify_ts_python does NOT use cmd.exe
# ---------------------------------------------------------------------------

def test_verify_ts_python_no_cmd_exe():
    """verify_ts_python must not invoke cmd.exe (removed in FIX-050)."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9\n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Windows"), \
         patch("launcher.core.shim_config.get_shim_dir", return_value=Path("nonexistent_dir")), \
         patch("shutil.which", return_value="C:\\bin\\ts-python.cmd"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    args_used = mock_run.call_args[0][0]
    assert args_used[0] != "cmd.exe", "cmd.exe wrapper must not be used (removed in FIX-050)"


# ---------------------------------------------------------------------------
# Regression: verify_ts_python calls read_python_path()
# ---------------------------------------------------------------------------

def test_verify_ts_python_uses_read_python_path():
    """verify_ts_python must call read_python_path() (new first step in FIX-050)."""
    sc = _import_shim_config()
    with patch("launcher.core.shim_config.read_python_path", return_value=None) as mock_rpp:
        ok, msg = sc.verify_ts_python()

    mock_rpp.assert_called_once()
    assert ok is False
    assert "not found" in msg.lower()


# ---------------------------------------------------------------------------
# Regression: timeout is 30, not 5
# ---------------------------------------------------------------------------

def test_verify_ts_python_timeout_30():
    """verify_ts_python must use timeout=30 (bumped from 5 in FIX-048)."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9\n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("launcher.core.shim_config.get_shim_dir", return_value=Path("nonexistent_dir")), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        sc.verify_ts_python()

    kwargs = mock_run.call_args[1]
    assert kwargs.get("timeout") == 30, "timeout must be 30 (not 5)"


# ---------------------------------------------------------------------------
# Regression: direct Python invocation format
# ---------------------------------------------------------------------------

def test_verify_ts_python_direct_invocation():
    """verify_ts_python must invoke [python_path, '-c', 'import sys; print(sys.version)']."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9\n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("launcher.core.shim_config.get_shim_dir", return_value=Path("nonexistent_dir")), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, _ = sc.verify_ts_python()

    assert ok is True
    args_used = mock_run.call_args[0][0]
    assert args_used[1] == "-c", "second arg must be '-c'"
    assert "sys.version" in args_used[2], "command must print sys.version"
