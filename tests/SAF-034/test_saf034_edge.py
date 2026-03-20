"""SAF-034 — Tester-added edge-case tests.

Additional coverage beyond the Developer's 18 tests, targeting:
- macOS (Darwin) platform detection
- Windows PATH fallback exhaustion
- subprocess timeout kwarg boundary
- Empty stdout on success path
- Error dialog title verification
- Security: strictly no user-controlled input in subprocess args
- Non-zero exit with empty stderr (no crash)
- macOS full success path (integration)
- Conftest autouse mock intercepting verify_ts_python in normal app flow
- Shim path with spaces handled correctly (list args)
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
# EC-01: macOS (Darwin) uses shutil.which("ts-python") like Linux
# ---------------------------------------------------------------------------

def test_verify_ts_python_macos_uses_which():
    """On macOS (Darwin), shutil.which('ts-python') is called (Unix code path)."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.8 (default, darwin)\n"
    mock_result.stderr = ""

    captured_which_calls = []

    def _which(name, *a, **kw):
        captured_which_calls.append(name)
        if name == "ts-python":
            return "/usr/local/bin/ts-python"
        return None

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Darwin"), \
         patch("shutil.which", side_effect=_which), \
         patch("subprocess.run", return_value=mock_result):
        ok, msg = sc.verify_ts_python()

    assert ok is True
    assert "ts-python" in captured_which_calls
    assert "ts-python.cmd" not in captured_which_calls, \
        "macOS must not query ts-python.cmd (Windows-only)"


# ---------------------------------------------------------------------------
# EC-02: Windows — both PATH lookups fail (ts-python.cmd and ts-python)
# ---------------------------------------------------------------------------

def test_verify_ts_python_windows_both_path_lookups_fail(tmp_path):
    """On Windows, if python-path.txt is not configured,
    verify_ts_python returns (False, 'not found ...')."""
    sc = _import_shim_config()

    with patch("launcher.core.shim_config.read_python_path", return_value=None), \
         patch("platform.system", return_value="Windows"), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("shutil.which", return_value=None):
        ok, msg = sc.verify_ts_python()

    assert ok is False
    assert "not found" in msg.lower()


# ---------------------------------------------------------------------------
# EC-03: subprocess.run receives timeout=5 kwarg (boundary check)
# ---------------------------------------------------------------------------

def test_verify_ts_python_passes_timeout_30_to_subprocess():
    """subprocess.run must be called with timeout=30 (exactly)."""
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
    assert kwargs.get("timeout") == 30, \
        f"Expected timeout=30, got timeout={kwargs.get('timeout')}"


# ---------------------------------------------------------------------------
# EC-04: Empty stdout on success path — returns (True, "")
# ---------------------------------------------------------------------------

def test_verify_ts_python_empty_stdout_on_success():
    """returncode 0 with empty stdout → (True, '') — no crash, empty string."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result):
        ok, msg = sc.verify_ts_python()

    assert ok is True
    assert msg == ""


# ---------------------------------------------------------------------------
# EC-05: Error dialog title is "Python Runtime Unavailable"
# ---------------------------------------------------------------------------

def test_on_create_project_error_dialog_title(tmp_path):
    """The showerror title must be 'Python Runtime Unavailable'."""
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

    title, _ = mock_mb.showerror.call_args[0]
    assert title == "Python Runtime Unavailable"


# ---------------------------------------------------------------------------
# EC-06: Security — subprocess args contain NO user-controlled input
# ---------------------------------------------------------------------------

def test_verify_ts_python_subprocess_args_are_static():
    """The command list passed to subprocess.run must be exactly:
    [python_exe, '-c', 'import sys; print(sys.version)'].
    No user input flows through the subprocess arguments."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.0\n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    mock_py.__str__ = MagicMock(return_value="/usr/local/bin/python3")
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        sc.verify_ts_python()

    args = mock_run.call_args[0][0]
    assert args[0] == "/usr/local/bin/python3"
    assert args[1] == "-c"
    assert args[2] == "import sys; print(sys.version)"
    assert len(args) == 3, "Extra args would indicate injection risk"


# ---------------------------------------------------------------------------
# EC-07: Non-zero exit with empty stderr — message includes exit code, no crash
# ---------------------------------------------------------------------------

def test_verify_ts_python_nonzero_exit_empty_stderr():
    """When returncode != 0 and stderr is empty, message still includes exit code."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 127
    mock_result.stdout = ""
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result):
        ok, msg = sc.verify_ts_python()

    assert ok is False
    assert "127" in msg


# ---------------------------------------------------------------------------
# EC-08: macOS full success path — verify output from Darwin platform
# ---------------------------------------------------------------------------

def test_verify_ts_python_macos_full_success():
    """Full success path on macOS: (True, stripped_version_string) returned."""
    sc = _import_shim_config()
    version_line = "3.12.1 (default, Jan 1 2025, 00:00:00) [Clang 15]"
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = version_line + "\n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Darwin"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result):
        ok, msg = sc.verify_ts_python()

    assert ok is True
    assert msg == version_line  # trailing newline stripped


# ---------------------------------------------------------------------------
# EC-09: Shim path with spaces handled correctly (list args, not string)
# ---------------------------------------------------------------------------

def test_verify_ts_python_shim_path_with_spaces(tmp_path):
    """A python path containing spaces must be passed as a list element,
    NOT as a string split on spaces (which would break the call)."""
    sc = _import_shim_config()
    spaced_dir = tmp_path / "path with spaces"
    spaced_dir.mkdir()
    fake_cmd = spaced_dir / "ts-python.cmd"
    fake_cmd.write_text("@echo off\n")
    fake_python = spaced_dir / "python.exe"
    fake_python.write_text("")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.0\n"
    mock_result.stderr = ""

    with patch("launcher.core.shim_config.read_python_path", return_value=fake_python), \
         patch("platform.system", return_value="Windows"), \
         patch.object(sc, "get_shim_dir", return_value=spaced_dir), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, _ = sc.verify_ts_python()

    assert ok is True
    args = mock_run.call_args[0][0]
    # FIX-050: Python is invoked directly; path with spaces is at index 0
    assert args[0] == str(fake_python)
    assert " " in args[0], "Path should contain spaces to prove list-arg safety"


# ---------------------------------------------------------------------------
# EC-10: Windows success returns version string from stdout (not raw object)
# ---------------------------------------------------------------------------

def test_verify_ts_python_windows_returns_stripped_version(tmp_path):
    """On Windows (shim dir path), the returned version string is stdout.strip()."""
    sc = _import_shim_config()
    fake_cmd = tmp_path / "ts-python.cmd"
    fake_cmd.write_text("@echo off\n")
    fake_python = tmp_path / "python.exe"
    fake_python.write_text("")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "  3.11.9 (tags/v3.11.9:8eb12b9, Jun  2 2024)  \n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Windows"), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("subprocess.run", return_value=mock_result):
        ok, msg = sc.verify_ts_python()

    assert ok is True
    assert msg == "3.11.9 (tags/v3.11.9:8eb12b9, Jun  2 2024)"


# ---------------------------------------------------------------------------
# EC-11: conftest autouse mock prevents test contamination in normal app tests
# ---------------------------------------------------------------------------

def test_conftest_autouse_mock_blocks_real_shim_execution():
    """The conftest autouse fixture must return (True, '3.11.0 (mocked)') so
    that all other GUI tests are not aborted by a missing ts-python shim."""
    import launcher.gui.app as app_module
    # Call via a minimal wrapper to observe the conftest mock in effect.
    # In the test environment (no real ts-python), the autouse patch must
    # intercept the call and return the mocked value.
    result = app_module.verify_ts_python()
    assert result == (True, "3.11.0 (mocked)"), \
        "conftest autouse fixture should have intercepted verify_ts_python"


# ---------------------------------------------------------------------------
# EC-12: python_path is configured but executable doesn't exist on disk
# ---------------------------------------------------------------------------

def test_verify_ts_python_python_path_exists_false():
    """When read_python_path() returns a Path but exists() is False,
    verify_ts_python returns (False, 'Python executable not found: ...')."""
    sc = _import_shim_config()
    mock_py = MagicMock()
    mock_py.exists.return_value = False
    mock_py.__str__ = MagicMock(return_value="/configured/but/missing/python3")
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"):
        ok, msg = sc.verify_ts_python()
    assert ok is False
    assert "not found" in msg.lower()


# ---------------------------------------------------------------------------
# EC-13: Shim missing from shim dir AND not on PATH (Unix)
# ---------------------------------------------------------------------------

def test_verify_ts_python_unix_shim_missing_everywhere(tmp_path):
    """On Unix, if the shim file is absent from shim dir AND shutil.which
    returns None, verify_ts_python returns (False, 'ts-python shim not found ...')."""
    sc = _import_shim_config()
    # tmp_path has no ts-python file
    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("shutil.which", return_value=None):
        ok, msg = sc.verify_ts_python()
    assert ok is False
    assert "not found" in msg.lower()


# ---------------------------------------------------------------------------
# EC-14: Shim missing from shim dir AND not on PATH (Windows)
# ---------------------------------------------------------------------------

def test_verify_ts_python_windows_shim_missing_everywhere(tmp_path):
    """On Windows, if ts-python.cmd is absent from shim dir AND shutil.which
    returns None, verify_ts_python returns (False, 'ts-python shim not found ...')."""
    sc = _import_shim_config()
    # tmp_path has no ts-python.cmd
    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Windows"), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("shutil.which", return_value=None):
        ok, msg = sc.verify_ts_python()
    assert ok is False
    assert "not found" in msg.lower()
