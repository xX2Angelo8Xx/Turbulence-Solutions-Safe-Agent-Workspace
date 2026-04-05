"""FIX-050 — Tester edge-case tests.

Edge cases beyond the Developer's 17 tests that probe boundary conditions,
platform-specific behavior, and correctness details.

Edge cases covered:
1.  read_python_path() with CRLF trailing whitespace — stripped to clean path
2.  read_python_path() with unicode characters in path — returned correctly
3.  read_python_path() with multiple consecutive spaces in path — preserved
4.  read_python_path() with whitespace-only content — returns None
5.  ts-python.cmd quotes the final invocation line: "!PYTHON_PATH!" %*
6.  ts-python.cmd has "@echo off" as its very first line
7.  ts-python.cmd CONFIG variable is set with quotes: set "CONFIG=..."
8.  verify_ts_python() passes stdin=subprocess.DEVNULL to subprocess.run
9.  verify_ts_python() passes timeout=30 to subprocess.run
10. verify_ts_python() non-zero exit code includes the numeric code in message
11. verify_ts_python() FileNotFoundError produces informative message (separate
    from the python_path.exists() pre-check)
12. verify_ts_python() on Linux uses shim name "ts-python" (no .cmd suffix)
13. verify_ts_python() on Linux falls back to shutil.which("ts-python")
14. verify_ts_python() stdout with multiple trailing newlines is stripped
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

CMD_SHIM = REPO_ROOT / "src" / "installer" / "shims" / "ts-python.cmd"


def _import_shim_config():
    import launcher.core.shim_config as sc
    return sc


# ---------------------------------------------------------------------------
# 1. read_python_path() strips CRLF (and other whitespace) from the path
# ---------------------------------------------------------------------------

def test_read_python_path_strips_crlf(tmp_path):
    """read_python_path() strips CRLF line endings from the stored path."""
    sc = _import_shim_config()
    config = tmp_path / "python-path.txt"
    config.write_bytes(b"C:\\Python311\\python.exe\r\n")
    with patch.object(sc, "get_python_path_config", return_value=config):
        result = sc.read_python_path()
    assert result == Path("C:\\Python311\\python.exe"), (
        "read_python_path() must strip CRLF to return the clean path."
    )


# ---------------------------------------------------------------------------
# 2. read_python_path() handles unicode characters in the path
# ---------------------------------------------------------------------------

def test_read_python_path_with_unicode_chars(tmp_path):
    """read_python_path() returns a Path with unicode characters intact."""
    sc = _import_shim_config()
    config = tmp_path / "python-path.txt"
    unicode_path = "C:\\Utilisateurs\\André\\python.exe"
    config.write_text(unicode_path, encoding="utf-8")
    with patch.object(sc, "get_python_path_config", return_value=config):
        result = sc.read_python_path()
    assert result == Path(unicode_path), (
        "read_python_path() must handle unicode characters in the Python path."
    )


# ---------------------------------------------------------------------------
# 3. read_python_path() preserves multiple consecutive spaces in path
# ---------------------------------------------------------------------------

def test_read_python_path_preserves_spaces_in_path(tmp_path):
    """read_python_path() preserves internal spaces in the Python path."""
    sc = _import_shim_config()
    config = tmp_path / "python-path.txt"
    # Path with multiple consecutive spaces (edge case)
    spaced_path = "C:\\Program Files (x86)\\Agent  Launcher\\python.exe"
    config.write_text(spaced_path + "\n", encoding="utf-8")
    with patch.object(sc, "get_python_path_config", return_value=config):
        result = sc.read_python_path()
    assert result == Path(spaced_path), (
        "read_python_path() should strip only leading/trailing whitespace, "
        "preserving internal spaces in the path."
    )


# ---------------------------------------------------------------------------
# 4. read_python_path() returns None for whitespace-only content
# ---------------------------------------------------------------------------

def test_read_python_path_whitespace_only_returns_none(tmp_path):
    """read_python_path() returns None if the file contains only whitespace."""
    sc = _import_shim_config()
    config = tmp_path / "python-path.txt"
    config.write_text("   \t\r\n   ", encoding="utf-8")
    with patch.object(sc, "get_python_path_config", return_value=config):
        result = sc.read_python_path()
    assert result is None, (
        "read_python_path() must return None for whitespace-only content "
        "to prevent using an empty path as a valid Python executable."
    )


# ---------------------------------------------------------------------------
# 5. ts-python.cmd: final invocation quotes !PYTHON_PATH!
# ---------------------------------------------------------------------------

def test_cmd_final_invocation_quotes_python_path():
    """ts-python.cmd must quote !PYTHON_PATH! in the final execution line."""
    content = CMD_SHIM.read_text(encoding="utf-8")
    assert '"!PYTHON_PATH!" %*' in content, (
        'ts-python.cmd final invocation must be \'\"!PYTHON_PATH!\" %%*\' '
        "with double-quoted !PYTHON_PATH! to handle paths containing spaces."
    )


# ---------------------------------------------------------------------------
# 6. ts-python.cmd first line is @echo off
# ---------------------------------------------------------------------------

def test_cmd_first_line_is_echo_off():
    """ts-python.cmd must start with '@echo off' to suppress command echoing."""
    content = CMD_SHIM.read_text(encoding="utf-8")
    first_line = content.splitlines()[0].strip().lower()
    assert first_line == "@echo off", (
        f"ts-python.cmd first line must be '@echo off', got {first_line!r}."
    )


# ---------------------------------------------------------------------------
# 7. ts-python.cmd CONFIG variable uses set "VAR=value" form
# ---------------------------------------------------------------------------

def test_cmd_config_set_uses_quoted_set_syntax():
    """ts-python.cmd sets CONFIG with set \"VAR=value\" form (handles paths with =)."""
    content = CMD_SHIM.read_text(encoding="utf-8")
    assert 'set "CONFIG=' in content, (
        "ts-python.cmd must use 'set \"CONFIG=...\"' syntax to correctly handle "
        "paths that may contain special characters."
    )


# ---------------------------------------------------------------------------
# 8. verify_ts_python() passes stdin=subprocess.DEVNULL
# ---------------------------------------------------------------------------

def test_verify_ts_python_passes_stdin_devnull(tmp_path):
    """verify_ts_python() must pass stdin=subprocess.DEVNULL to subprocess.run."""
    sc = _import_shim_config()
    fake_python = tmp_path / "python.exe"
    fake_python.write_text("fake")
    fake_shim = tmp_path / "ts-python.cmd"
    fake_shim.write_text("@echo off\n")
    fake_shim_unix = tmp_path / "ts-python"
    fake_shim_unix.write_text("#!/bin/sh\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9\n"
    mock_result.stderr = ""

    with patch.object(sc, "read_python_path", return_value=fake_python), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    kwargs = mock_run.call_args[1]
    assert kwargs.get("stdin") == subprocess.DEVNULL, (
        "verify_ts_python() must pass stdin=subprocess.DEVNULL to prevent "
        "the child process from inheriting the terminal's stdin."
    )


# ---------------------------------------------------------------------------
# 9. verify_ts_python() passes timeout=30 to subprocess.run
# ---------------------------------------------------------------------------

def test_verify_ts_python_passes_timeout_30(tmp_path):
    """verify_ts_python() must pass timeout=30 to subprocess.run."""
    sc = _import_shim_config()
    fake_python = tmp_path / "python.exe"
    fake_python.write_text("fake")
    fake_shim = tmp_path / "ts-python.cmd"
    fake_shim.write_text("@echo off\n")
    fake_shim_unix = tmp_path / "ts-python"
    fake_shim_unix.write_text("#!/bin/sh\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9\n"
    mock_result.stderr = ""

    with patch.object(sc, "read_python_path", return_value=fake_python), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    kwargs = mock_run.call_args[1]
    assert kwargs.get("timeout") == 30, (
        f"verify_ts_python() must pass timeout=30 to subprocess.run, "
        f"got timeout={kwargs.get('timeout')!r}."
    )


# ---------------------------------------------------------------------------
# 10. verify_ts_python() non-zero exit code includes the numeric code in message
# ---------------------------------------------------------------------------

def test_verify_ts_python_nonzero_exit_code_in_message(tmp_path):
    """Non-zero exit code is included in the failure message."""
    sc = _import_shim_config()
    fake_python = tmp_path / "python.exe"
    fake_python.write_text("fake")
    fake_shim = tmp_path / "ts-python.cmd"
    fake_shim.write_text("@echo off\n")
    fake_shim_unix = tmp_path / "ts-python"
    fake_shim_unix.write_text("#!/bin/sh\n")

    for code in [1, 2, 42, 127, 255]:
        mock_result = MagicMock()
        mock_result.returncode = code
        mock_result.stdout = ""
        mock_result.stderr = "some error"

        with patch.object(sc, "read_python_path", return_value=fake_python), \
             patch.object(sc, "get_shim_dir", return_value=tmp_path), \
             patch("subprocess.run", return_value=mock_result):
            ok, msg = sc.verify_ts_python()

        assert ok is False
        assert str(code) in msg, (
            f"Exit code {code} must appear in error message, got: {msg!r}"
        )


# ---------------------------------------------------------------------------
# 11. verify_ts_python() FileNotFoundError after the exists() pre-check
# ---------------------------------------------------------------------------

def test_verify_ts_python_file_not_found_after_precheck(tmp_path):
    """FileNotFoundError from subprocess.run (e.g., race condition) returns (False, ...)."""
    sc = _import_shim_config()
    fake_python = tmp_path / "python.exe"
    fake_python.write_text("fake")
    fake_shim = tmp_path / "ts-python.cmd"
    fake_shim.write_text("@echo off\n")
    fake_shim_unix = tmp_path / "ts-python"
    fake_shim_unix.write_text("#!/bin/sh\n")

    with patch.object(sc, "read_python_path", return_value=fake_python), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("subprocess.run", side_effect=FileNotFoundError("file not found")):
        ok, msg = sc.verify_ts_python()

    assert ok is False
    assert "not found" in msg.lower(), (
        "FileNotFoundError from subprocess.run must produce a 'not found' message."
    )


# ---------------------------------------------------------------------------
# 12. verify_ts_python() on Linux uses "ts-python" shim name (no .cmd)
# ---------------------------------------------------------------------------

def test_verify_ts_python_linux_shim_name_no_cmd_suffix(tmp_path):
    """On Linux, verify_ts_python() looks for 'ts-python', not 'ts-python.cmd'."""
    sc = _import_shim_config()
    fake_python = tmp_path / "python"
    fake_python.write_text("fake")

    # Create the Linux shim (ts-python, no .cmd extension)
    fake_shim = tmp_path / "ts-python"
    fake_shim.write_text("#!/bin/sh\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9\n"
    mock_result.stderr = ""

    with patch("platform.system", return_value="Linux"), \
         patch.object(sc, "read_python_path", return_value=fake_python), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("subprocess.run", return_value=mock_result):
        ok, msg = sc.verify_ts_python()

    assert ok is True, (
        "On Linux, ts-python (no .cmd) shim exists in shim dir — should succeed."
    )


# ---------------------------------------------------------------------------
# 13. verify_ts_python() on Linux falls back to shutil.which("ts-python")
# ---------------------------------------------------------------------------

def test_verify_ts_python_linux_uses_which_fallback(tmp_path):
    """On Linux, if shim dir has no ts-python, falls back to shutil.which."""
    sc = _import_shim_config()
    fake_python = tmp_path / "python"
    fake_python.write_text("fake")
    # No shim file in tmp_path — triggers fallback to shutil.which

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9\n"
    mock_result.stderr = ""

    with patch("platform.system", return_value="Linux"), \
         patch.object(sc, "read_python_path", return_value=fake_python), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result):
        ok, msg = sc.verify_ts_python()

    assert ok is True, (
        "On Linux, when shim is not in shim_dir but is on PATH via shutil.which, "
        "verify_ts_python() should succeed."
    )


# ---------------------------------------------------------------------------
# 14. verify_ts_python() strips multiple trailing newlines from stdout
# ---------------------------------------------------------------------------

def test_verify_ts_python_strips_multiple_trailing_newlines(tmp_path):
    """verify_ts_python() strips all trailing whitespace from subprocess stdout."""
    sc = _import_shim_config()
    fake_python = tmp_path / "python.exe"
    fake_python.write_text("fake")
    fake_shim = tmp_path / "ts-python.cmd"
    fake_shim.write_text("@echo off\n")
    fake_shim_unix = tmp_path / "ts-python"
    fake_shim_unix.write_text("#!/bin/sh\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9 (default, Mar 19 2026)\n\n\n"
    mock_result.stderr = ""

    with patch.object(sc, "read_python_path", return_value=fake_python), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("subprocess.run", return_value=mock_result):
        ok, msg = sc.verify_ts_python()

    assert ok is True
    assert msg == "3.11.9 (default, Mar 19 2026)", (
        f"verify_ts_python() must strip trailing newlines from stdout. Got: {msg!r}"
    )
