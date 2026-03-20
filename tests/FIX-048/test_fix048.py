"""FIX-048 — Tests: Fix ts-python shim timeout and bump version to 3.0.1.

Updated for FIX-050: cmd.exe /c wrapper removed; Python is invoked directly.

Covers:
1. Windows .cmd shim existence is still checked (Python invoked directly)
2. Windows non-.cmd: Python invoked directly
3. stdin=subprocess.DEVNULL is always passed to subprocess.run
4. timeout= argument passed to subprocess.run is 30
5. TimeoutExpired error message says "30 seconds" (not "5 seconds")
6. Existing success behavior: (True, version_string) returned on exit code 0
7. Existing failure behavior: (False, msg) on non-zero exit code
8. Existing not-found behavior: (False, msg) when python-path.txt not configured
9. Windows: .cmd shim in shim dir is checked for existence first
10. Windows: fallback to PATH when shim dir empty
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

import re as _re
_CURRENT_VERSION: str = _re.search(
    r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"',
    (REPO_ROOT / "src" / "launcher" / "config.py").read_text(encoding="utf-8"),
    _re.MULTILINE,
).group(1)
del _re


def _import_shim_config():
    import launcher.core.shim_config as sc
    return sc


# ---------------------------------------------------------------------------
# 1. Windows .cmd shim: invoked via cmd.exe /c
# ---------------------------------------------------------------------------

def test_windows_cmd_uses_cmd_exe_wrapper(tmp_path):
    """On Windows, verify_ts_python invokes Python directly (cmd.exe wrapper
    was removed in FIX-050). The shim .cmd file existence is still checked."""
    sc = _import_shim_config()
    fake_cmd = tmp_path / "ts-python.cmd"
    fake_cmd.write_text("@echo off\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9\n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Windows"), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    args_used = mock_run.call_args[0][0]
    # FIX-050: Python invoked directly, not via cmd.exe /c
    assert args_used[1] == "-c"
    assert "sys.version" in args_used[2]


# ---------------------------------------------------------------------------
# 2. Windows non-.cmd shim: no cmd.exe wrapper
# ---------------------------------------------------------------------------

def test_windows_non_cmd_no_wrapper(tmp_path):
    """On Windows, verify_ts_python uses direct Python invocation (no cmd.exe)."""
    sc = _import_shim_config()
    # No ts-python.cmd in shim dir — fallback to PATH returns a non-.cmd path
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9\n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Windows"), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    args_used = mock_run.call_args[0][0]
    assert args_used[0] != "cmd.exe"
    # FIX-050: invokes the configured python directly
    assert args_used[1] == "-c"


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

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
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

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
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

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
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

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
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

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
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
    """(False, msg) when python-path.txt is not configured."""
    sc = _import_shim_config()

    with patch("launcher.core.shim_config.read_python_path", return_value=None), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value=None):
        ok, msg = sc.verify_ts_python()

    assert ok is False
    assert "not found" in msg.lower()


# ---------------------------------------------------------------------------
# 9. Windows: .cmd in shim dir takes priority over PATH
# ---------------------------------------------------------------------------

def test_windows_shim_dir_used_first(tmp_path):
    """On Windows, ts-python.cmd in shim dir is checked for existence first."""
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
         patch("shutil.which", return_value="C:\\Windows\\ts-python.cmd"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    # FIX-050: Python invoked directly, not via cmd.exe /c shim
    args_used = mock_run.call_args[0][0]
    assert args_used[1] == "-c"
    assert "sys.version" in args_used[2]


# ---------------------------------------------------------------------------
# 10. Windows: fallback .cmd from PATH also gets cmd.exe wrapper
# ---------------------------------------------------------------------------

def test_windows_fallback_to_path_cmd_wrapper(tmp_path):
    """On Windows, fallback to PATH when shim dir empty; Python invoked directly."""
    sc = _import_shim_config()
    # No ts-python.cmd in shim dir (tmp_path is empty)

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.5\n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Windows"), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("shutil.which", return_value="C:\\Users\\User\\AppData\\Local\\TurbulenceSolutions\\bin\\ts-python.cmd"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    # FIX-050: Python invoked directly, not via cmd.exe /c
    args_used = mock_run.call_args[0][0]
    assert args_used[1] == "-c"
    assert "sys.version" in args_used[2]


# ---------------------------------------------------------------------------
# TESTER EDGE CASES — added by Tester Agent during review
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 11. Version bump — all 5 version locations contain the current version
# ---------------------------------------------------------------------------

def test_version_config_py():
    """src/launcher/config.py VERSION constant matches the current version."""
    config_py = REPO_ROOT / "src" / "launcher" / "config.py"
    assert config_py.exists(), "config.py not found"
    content = config_py.read_text(encoding="utf-8")
    assert _CURRENT_VERSION in content, f"config.py must contain version {_CURRENT_VERSION}"


def test_version_pyproject_toml():
    """pyproject.toml version field matches the current version."""
    pyproject = REPO_ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found"
    content = pyproject.read_text(encoding="utf-8")
    assert f'version = "{_CURRENT_VERSION}"' in content, f"pyproject.toml must contain version {_CURRENT_VERSION}"


def test_version_setup_iss():
    """src/installer/windows/setup.iss MyAppVersion matches the current version."""
    setup_iss = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    assert setup_iss.exists(), "setup.iss not found"
    content = setup_iss.read_text(encoding="utf-8")
    assert _CURRENT_VERSION in content, f"setup.iss must contain version {_CURRENT_VERSION}"


def test_version_build_dmg_sh():
    """src/installer/macos/build_dmg.sh APP_VERSION matches the current version."""
    build_dmg = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
    assert build_dmg.exists(), "build_dmg.sh not found"
    content = build_dmg.read_text(encoding="utf-8")
    assert _CURRENT_VERSION in content, f"build_dmg.sh must contain version {_CURRENT_VERSION}"


def test_version_build_appimage_sh():
    """src/installer/linux/build_appimage.sh APP_VERSION matches the current version."""
    build_appimage = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
    assert build_appimage.exists(), "build_appimage.sh not found"
    content = build_appimage.read_text(encoding="utf-8")
    assert _CURRENT_VERSION in content, f"build_appimage.sh must contain version {_CURRENT_VERSION}"


def test_version_consistency_all_five_locations():
    """All 5 version locations agree on the current version (no location left on old version)."""
    import re
    version_target = _CURRENT_VERSION

    # config.py: VERSION: str = "x.y.z"  (has type annotation)
    config_py = REPO_ROOT / "src" / "launcher" / "config.py"
    m = re.search(r'VERSION(?::\s*\w+)?\s*=\s*"([^"]+)"', config_py.read_text(encoding="utf-8"))
    assert m and m.group(1) == version_target, f"config.py VERSION={m.group(1) if m else 'not found'}"

    # pyproject.toml: version = "x.y.z"
    pyproject = REPO_ROOT / "pyproject.toml"
    m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"), re.MULTILINE)
    assert m and m.group(1) == version_target, f"pyproject.toml version={m.group(1) if m else 'not found'}"

    # setup.iss: #define MyAppVersion "x.y.z"
    setup_iss = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    m = re.search(r'MyAppVersion\s+"([^"]+)"', setup_iss.read_text(encoding="utf-8"))
    assert m and m.group(1) == version_target, f"setup.iss MyAppVersion={m.group(1) if m else 'not found'}"

    # build_dmg.sh: APP_VERSION="x.y.z"
    build_dmg = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
    m = re.search(r'APP_VERSION="([^"]+)"', build_dmg.read_text(encoding="utf-8"))
    assert m and m.group(1) == version_target, f"build_dmg.sh APP_VERSION={m.group(1) if m else 'not found'}"

    # build_appimage.sh: APP_VERSION="x.y.z"
    build_appimage = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
    m = re.search(r'APP_VERSION="([^"]+)"', build_appimage.read_text(encoding="utf-8"))
    assert m and m.group(1) == version_target, f"build_appimage.sh APP_VERSION={m.group(1) if m else 'not found'}"


# ---------------------------------------------------------------------------
# 12. FileNotFoundError from subprocess.run is handled
# ---------------------------------------------------------------------------

def test_file_not_found_error_handled():
    """FileNotFoundError raised by subprocess.run is caught and returns (False, msg)."""
    sc = _import_shim_config()

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", side_effect=FileNotFoundError("ts-python not found")):
        ok, msg = sc.verify_ts_python()

    assert ok is False
    assert "not found" in msg.lower() or "ts-python" in msg.lower()


# ---------------------------------------------------------------------------
# 13. OSError from subprocess.run is handled
# ---------------------------------------------------------------------------

def test_oserror_handled():
    """OSError raised by subprocess.run is caught and returns (False, msg)."""
    sc = _import_shim_config()

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Linux"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", side_effect=OSError("[Errno 8] Exec format error")):
        ok, msg = sc.verify_ts_python()

    assert ok is False
    assert "ts-python" in msg.lower() or "failed" in msg.lower()


# ---------------------------------------------------------------------------
# 14. macOS uses no cmd.exe wrapper (same as Linux path)
# ---------------------------------------------------------------------------

def test_macos_no_cmd_wrapper():
    """On macOS (Darwin), verify_ts_python invokes Python directly."""
    sc = _import_shim_config()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9\n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Darwin"), \
         patch("shutil.which", return_value="/usr/local/bin/ts-python"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    args_used = mock_run.call_args[0][0]
    assert args_used[0] != "cmd.exe", "macOS must NOT use cmd.exe wrapper"
    # FIX-050: direct Python invocation
    assert args_used[1] == "-c"
    assert "sys.version" in args_used[2]


# ---------------------------------------------------------------------------
# 15. Windows stdin=DEVNULL is passed even when cmd.exe wrapper is used
# ---------------------------------------------------------------------------

def test_windows_cmd_wrapper_also_uses_stdin_devnull(tmp_path):
    """On Windows, stdin=DEVNULL must be passed to subprocess.run."""
    sc = _import_shim_config()
    fake_cmd = tmp_path / "ts-python.cmd"
    fake_cmd.write_text("@echo off\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "3.11.9\n"
    mock_result.stderr = ""

    mock_py = MagicMock()
    mock_py.exists.return_value = True
    with patch("launcher.core.shim_config.read_python_path", return_value=mock_py), \
         patch("platform.system", return_value="Windows"), \
         patch.object(sc, "get_shim_dir", return_value=tmp_path), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        ok, msg = sc.verify_ts_python()

    assert ok is True
    kwargs = mock_run.call_args[1]
    assert kwargs.get("stdin") == subprocess.DEVNULL, \
        "stdin=DEVNULL must be set on Windows"


# ---------------------------------------------------------------------------
# 16. CI workflow: Python embeddable download step is uncommented
# ---------------------------------------------------------------------------

def test_ci_python_embed_step_is_active():
    """The Python embeddable download step in release.yml is NOT commented out."""
    release_yml = REPO_ROOT / ".github" / "workflows" / "release.yml"
    assert release_yml.exists(), ".github/workflows/release.yml not found"
    content = release_yml.read_text(encoding="utf-8")
    # The step should contain the version variable and download URL, not commented out
    assert 'python-embed.zip' in content, \
        "Python embeddable download step (python-embed.zip) not found in release.yml"
    # Verify the key download command is not commented out (the step name must be present)
    assert 'Download Python embeddable distribution' in content, \
        "Python embeddable download step name not found in release.yml"
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if 'python-embed.zip' in line:
            # The line containing the zip file should not be commented out
            stripped = line.lstrip()
            assert not stripped.startswith('#'), \
                f"Python embed download step appears to be commented out at line {i+1}: {line!r}"
            break
