"""FIX-050 — Tests: Fix ts-python.cmd parsing and verify_ts_python robustness.

Covers:
1. ts-python.cmd uses setlocal EnableDelayedExpansion
2. ts-python.cmd uses !PYTHON_PATH! (not %PYTHON_PATH%) inside if blocks
3. ts-python.cmd has "if not defined PYTHON_PATH" guard for empty-file case
4. ts-python.cmd does NOT use bare %PYTHON_PATH% inside if ( ) blocks
5. verify_ts_python() calls python executable directly (no cmd.exe in args)
6. verify_ts_python() returns (True, version_string) on success
7. verify_ts_python() returns (False, msg) when python-path.txt is missing
8. verify_ts_python() returns (False, msg) when python exe does not exist
9. verify_ts_python() returns (False, msg) when shim missing and not on PATH
10. verify_ts_python() timeout message contains "30 seconds"
11. verify_ts_python() handles OSError gracefully
12. verify_ts_python() handles python_path with spaces and parentheses
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

CMD_SHIM = REPO_ROOT / "src" / "installer" / "shims" / "ts-python.cmd"

from tests.shared.version_utils import CURRENT_VERSION  # noqa: E402


def _import_shim_config():
    import launcher.core.shim_config as sc
    return sc


# ---------------------------------------------------------------------------
# 1. ts-python.cmd uses setlocal EnableDelayedExpansion
# ---------------------------------------------------------------------------

def test_cmd_uses_delayed_expansion():
    """ts-python.cmd must use 'setlocal EnableDelayedExpansion'."""
    content = CMD_SHIM.read_text(encoding="utf-8")
    assert "EnableDelayedExpansion" in content, (
        "ts-python.cmd must use 'setlocal EnableDelayedExpansion' to prevent "
        "parse-time expansion of %PYTHON_PATH% inside if ( ) blocks."
    )


# ---------------------------------------------------------------------------
# 2. ts-python.cmd uses !PYTHON_PATH! inside if blocks (delayed expansion)
# ---------------------------------------------------------------------------

def test_cmd_uses_exclamation_var_syntax():
    """ts-python.cmd must use !PYTHON_PATH! (delayed expansion) inside if blocks."""
    content = CMD_SHIM.read_text(encoding="utf-8")
    assert "!PYTHON_PATH!" in content, (
        "ts-python.cmd must reference PYTHON_PATH via !PYTHON_PATH! (delayed "
        "expansion) inside if ( ) blocks, not %PYTHON_PATH%."
    )


# ---------------------------------------------------------------------------
# 3. ts-python.cmd has "if not defined PYTHON_PATH" guard
# ---------------------------------------------------------------------------

def test_cmd_has_not_defined_check():
    """ts-python.cmd must contain 'if not defined PYTHON_PATH' for empty-file guard."""
    content = CMD_SHIM.read_text(encoding="utf-8")
    assert "if not defined PYTHON_PATH" in content, (
        "ts-python.cmd must guard against an empty python-path.txt by checking "
        "'if not defined PYTHON_PATH'."
    )


# ---------------------------------------------------------------------------
# 4. ts-python.cmd does NOT use bare %PYTHON_PATH% inside if blocks
# ---------------------------------------------------------------------------

def test_cmd_no_bare_percent_in_if_blocks():
    """ts-python.cmd must not use %PYTHON_PATH% inside if ( ) blocks.

    The old pattern 'if not exist \"%PYTHON_PATH%\"' caused parse-time
    expansion failures for paths with spaces.  The new code must use
    !PYTHON_PATH! exclusively for all references inside blocks.
    """
    content = CMD_SHIM.read_text(encoding="utf-8")
    # %PYTHON_PATH% must not appear inside any if ( ) block.
    # We check by asserting the literal pattern is absent from the conditional
    # branches (everything between the first 'set /p' and the final invocation).
    # The safe reference 'set /p PYTHON_PATH=<...' is fine — it sets the var.
    # Only the if-block usage must use ! not %.
    lines = content.splitlines()
    for line in lines:
        stripped = line.strip().lower()
        # Any line starting with 'if' that references %PYTHON_PATH% is the bug.
        if stripped.startswith("if") and "%python_path%" in stripped:
            pytest.fail(
                f"ts-python.cmd uses bare %%PYTHON_PATH%% inside an if statement: {line!r}\n"
                "Must use !PYTHON_PATH! instead to avoid parse-time expansion."
            )


# ---------------------------------------------------------------------------
# 5. verify_ts_python() calls python executable directly (no cmd.exe)
# ---------------------------------------------------------------------------

def test_verify_calls_python_directly_not_cmd_exe(tmp_path):
    """verify_ts_python() must invoke python_path directly, not via cmd.exe /c."""
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
    args_used = mock_run.call_args[0][0]
    assert args_used[0] == str(fake_python), (
        f"First argument to subprocess.run must be the python path, not {args_used[0]!r}."
    )
    assert "cmd.exe" not in args_used, (
        "verify_ts_python() must NOT use cmd.exe — it must call python directly."
    )


# ---------------------------------------------------------------------------
# 6. verify_ts_python() returns (True, version_string) on success
# ---------------------------------------------------------------------------

def test_verify_success_valid_config(tmp_path):
    """Returns (True, stripped_stdout) when python-path.txt is valid and python works."""
    sc = _import_shim_config()

    fake_python = tmp_path / "python.exe"
    fake_python.write_text("fake")

    fake_shim = tmp_path / "ts-python.cmd"
    fake_shim.write_text("@echo off\n")
    fake_shim_unix = tmp_path / "ts-python"
    fake_shim_unix.write_text("#!/bin/sh\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9 (default, Mar 19 2026)\n"
    mock_result.stderr = ""

    with patch.object(sc, "read_python_path", return_value=fake_python), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("subprocess.run", return_value=mock_result):
        ok, msg = sc.verify_ts_python()

    assert ok is True
    assert msg == "3.11.9 (default, Mar 19 2026)"


# ---------------------------------------------------------------------------
# 7. verify_ts_python() returns (False, ...) when python-path.txt is missing
# ---------------------------------------------------------------------------

def test_verify_fails_config_missing():
    """Returns (False, ...) when read_python_path() returns None."""
    sc = _import_shim_config()

    with patch.object(sc, "read_python_path", return_value=None):
        ok, msg = sc.verify_ts_python()

    assert ok is False
    assert "not found" in msg.lower() or "configuration" in msg.lower()


# ---------------------------------------------------------------------------
# 8. verify_ts_python() returns (False, ...) when python exe does not exist
# ---------------------------------------------------------------------------

def test_verify_fails_python_not_found(tmp_path):
    """Returns (False, ...) when python_path.exists() is False."""
    sc = _import_shim_config()

    nonexistent = tmp_path / "python.exe"
    # Do NOT create the file — it must not exist.

    with patch.object(sc, "read_python_path", return_value=nonexistent):
        ok, msg = sc.verify_ts_python()

    assert ok is False
    assert "not found" in msg.lower()


# ---------------------------------------------------------------------------
# 9. verify_ts_python() returns (False, ...) when shim missing and not on PATH
# ---------------------------------------------------------------------------

def test_verify_fails_shim_missing_and_not_on_path(tmp_path):
    """Returns (False, ...) when shim file absent from dir and PATH."""
    sc = _import_shim_config()

    fake_python = tmp_path / "python.exe"
    fake_python.write_text("fake")
    # No ts-python.cmd in tmp_path.

    with patch.object(sc, "read_python_path", return_value=fake_python), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("shutil.which", return_value=None):
        ok, msg = sc.verify_ts_python()

    assert ok is False
    assert "not found" in msg.lower()


# ---------------------------------------------------------------------------
# 10. verify_ts_python() timeout message contains "30 seconds"
# ---------------------------------------------------------------------------

def test_verify_timeout_says_30_seconds(tmp_path):
    """TimeoutExpired produces a message containing '30 seconds'."""
    sc = _import_shim_config()

    fake_python = tmp_path / "python.exe"
    fake_python.write_text("fake")

    fake_shim = tmp_path / "ts-python.cmd"
    fake_shim.write_text("@echo off\n")
    fake_shim_unix = tmp_path / "ts-python"
    fake_shim_unix.write_text("#!/bin/sh\n")

    with patch.object(sc, "read_python_path", return_value=fake_python), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(
             cmd=str(fake_python), timeout=30
         )):
        ok, msg = sc.verify_ts_python()

    assert ok is False
    assert "30 seconds" in msg
    assert "5 seconds" not in msg


# ---------------------------------------------------------------------------
# 11. verify_ts_python() handles OSError gracefully
# ---------------------------------------------------------------------------

def test_verify_handles_os_error(tmp_path):
    """Returns (False, ...) on OSError without raising."""
    sc = _import_shim_config()

    fake_python = tmp_path / "python.exe"
    fake_python.write_text("fake")

    fake_shim = tmp_path / "ts-python.cmd"
    fake_shim.write_text("@echo off\n")
    fake_shim_unix = tmp_path / "ts-python"
    fake_shim_unix.write_text("#!/bin/sh\n")

    with patch.object(sc, "read_python_path", return_value=fake_python), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("subprocess.run", side_effect=OSError("access denied")):
        ok, msg = sc.verify_ts_python()

    assert ok is False
    assert "access denied" in msg.lower()


# ---------------------------------------------------------------------------
# 12. verify_ts_python() handles python_path with spaces and parentheses
# ---------------------------------------------------------------------------

def test_verify_path_with_spaces_and_parens(tmp_path):
    """subprocess.run receives the full path with spaces/parens as a list arg."""
    sc = _import_shim_config()

    # Simulate a path like "C:\Program Files (x86)\Agent Environment Launcher\..."
    spaced_dir = tmp_path / "Program Files (x86)" / "Agent Environment Launcher"
    spaced_dir.mkdir(parents=True)
    fake_python = spaced_dir / "python.exe"
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
    args_used = mock_run.call_args[0][0]
    # The path with spaces and parentheses must arrive intact as a single list entry.
    assert args_used[0] == str(fake_python)
    assert " " in args_used[0], "Path should contain spaces."
    assert "(x86)" in args_used[0], "Path should contain parentheses."


# ---------------------------------------------------------------------------
# Version: dynamic (sourced from CURRENT_VERSION)
# ---------------------------------------------------------------------------

def test_config_py_version():
    """src/launcher/config.py must declare the current version."""
    content = (REPO_ROOT / "src" / "launcher" / "config.py").read_text(encoding="utf-8")
    match = re.search(r'^VERSION\s*:\s*str\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    assert match, "VERSION constant not found in config.py"
    assert match.group(1) == CURRENT_VERSION, (
        f"Expected {CURRENT_VERSION!r} but config.py has {match.group(1)!r}."
    )


def test_pyproject_toml_version():
    """pyproject.toml version must match current version."""
    content = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{CURRENT_VERSION}"' in content


def test_setup_iss_version():
    """setup.iss MyAppVersion must match current version."""
    content = (REPO_ROOT / "src" / "installer" / "windows" / "setup.iss").read_text(encoding="utf-8")
    assert f'#define MyAppVersion "{CURRENT_VERSION}"' in content


def test_build_dmg_sh_version():
    """build_dmg.sh APP_VERSION must match current version."""
    content = (REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh").read_text(encoding="utf-8")
    assert f'APP_VERSION="{CURRENT_VERSION}"' in content


def test_build_appimage_sh_version():
    """build_appimage.sh APP_VERSION must match current version."""
    content = (REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh").read_text(encoding="utf-8")
    assert f'APP_VERSION="{CURRENT_VERSION}"' in content
