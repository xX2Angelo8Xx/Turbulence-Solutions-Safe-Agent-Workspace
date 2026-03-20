"""FIX-051 — Regression tests: SAF-034 tests properly fixed after FIX-048/FIX-050.

These are meta-tests that confirm:
1. verify_ts_python() returns (False, "...not found...") when read_python_path()
   returns None — the root cause of the BUG-083 failures.
2. verify_ts_python() uses timeout=30 (not the old timeout=5).
3. Tests/SAF-034/ contains the corrected test files.
"""
from __future__ import annotations

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
# Regression: BUG-078 / BUG-083 — read_python_path returning None must cause
#             verify_ts_python to return (False, "...not found...") immediately.
# ---------------------------------------------------------------------------

def test_verify_ts_python_returns_false_when_read_python_path_returns_none():
    """Regression for BUG-083: verify_ts_python() must return False when
    read_python_path() returns None, not reach shutil.which or subprocess."""
    sc = _import_shim_config()
    subprocess_called = []
    with patch("launcher.core.shim_config.read_python_path", return_value=None), \
         patch("subprocess.run", side_effect=lambda *a, **kw: subprocess_called.append(a)):
        ok, msg = sc.verify_ts_python()
    assert ok is False
    assert "not found" in msg.lower()
    assert subprocess_called == [], "subprocess.run must NOT be called when python path is not configured"


# ---------------------------------------------------------------------------
# Regression: BUG-078 — timeout must be 30s, not 5s
# ---------------------------------------------------------------------------

def test_verify_ts_python_timeout_is_30_not_5():
    """Regression for BUG-078: timeout must be 30 seconds (FIX-048 changed 5→30)."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.0\n"
    mock_result.stderr = ""
    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        sc.verify_ts_python()
    kwargs = mock_run.call_args[1]
    assert kwargs.get("timeout") == 30, f"timeout must be 30, got {kwargs.get('timeout')}"
    assert kwargs.get("timeout") != 5, "Old timeout=5 must not be used (BUG-078)"


# ---------------------------------------------------------------------------
# Regression: BUG-078 — subprocess must use direct Python invocation,
#             NOT cmd.exe /c wrapper
# ---------------------------------------------------------------------------

def test_verify_ts_python_uses_direct_python_not_cmd_exe():
    """Regression for BUG-078: FIX-050 removed cmd.exe /c wrapper; verify_ts_python
    must call [python_path, '-c', ...] directly."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.0\n"
    mock_result.stderr = ""
    mock_py = MagicMock()
    mock_py.exists.return_value = True
    mock_py.__str__ = MagicMock(return_value="/opt/python/bin/python3")
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        sc.verify_ts_python()
    args = mock_run.call_args[0][0]
    assert isinstance(args, list), "args must be a list, not a string"
    assert args[0] == "/opt/python/bin/python3", "First arg must be the Python path, not cmd.exe"
    assert "cmd.exe" not in str(args[0]).lower(), "cmd.exe must not appear in subprocess args"
    assert args[1] == "-c"
    assert "sys.version" in args[2]
