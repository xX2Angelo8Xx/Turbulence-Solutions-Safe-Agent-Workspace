"""
Tests for INS-019: ts-python shim and config system.

Covers:
- Shim file existence and content (ts-python.cmd, ts-python)
- Line endings (.cmd = CRLF, shell = LF)
- shim_config.py functions: get_config_dir, get_shim_dir, get_python_path_config,
  write_python_path, read_python_path, verify_shim
"""
import os
import platform
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent.parent
SHIMS_DIR = REPO_ROOT / "src" / "installer" / "shims"
WINDOWS_SHIM = SHIMS_DIR / "ts-python.cmd"
UNIX_SHIM = SHIMS_DIR / "ts-python"

# ---------------------------------------------------------------------------
# Shim file existence
# ---------------------------------------------------------------------------


def test_windows_shim_exists():
    assert WINDOWS_SHIM.exists(), f"Windows shim not found: {WINDOWS_SHIM}"


def test_unix_shim_exists():
    assert UNIX_SHIM.exists(), f"Unix shim not found: {UNIX_SHIM}"


def test_readme_exists():
    assert (SHIMS_DIR / "README.md").exists(), "shims/README.md not found"


# ---------------------------------------------------------------------------
# Windows shim content
# ---------------------------------------------------------------------------


def _read_cmd_raw() -> bytes:
    return WINDOWS_SHIM.read_bytes()


def _read_cmd_text() -> str:
    return WINDOWS_SHIM.read_text(encoding="utf-8")


def test_windows_shim_crlf_line_endings():
    raw = _read_cmd_raw()
    assert b"\r\n" in raw, "ts-python.cmd must use CRLF line endings"


def test_windows_shim_no_bare_lf():
    """No bare LF (LF not preceded by CR) outside of CRLF pairs."""
    raw = _read_cmd_raw()
    # Replace all CRLF, then check no LF remains
    stripped = raw.replace(b"\r\n", b"")
    assert b"\n" not in stripped, "ts-python.cmd must not contain bare LF"


def test_windows_shim_reads_config():
    text = _read_cmd_text()
    assert "LOCALAPPDATA" in text, "Windows shim must use %LOCALAPPDATA%"
    assert "python-path.txt" in text, "Windows shim must reference python-path.txt"
    assert "CONFIG" in text, "Windows shim must use a CONFIG variable"


def test_windows_shim_content_forwards_args():
    text = _read_cmd_text()
    assert "%*" in text, "Windows shim must forward all args with %*"


def test_windows_shim_missing_config_error():
    text = _read_cmd_text()
    # Must check if config file exists before proceeding
    assert "if not exist" in text.lower() or "if not exist" in text, \
        "Windows shim must check if config file exists"
    assert "exit /b 1" in text, "Windows shim must exit with code 1 on error"


def test_windows_shim_missing_python_error():
    text = _read_cmd_text()
    # Must check if python executable exists
    assert text.count("if not exist") >= 2, \
        "Windows shim must check both config file and python executable existence"


def test_windows_shim_has_setlocal():
    text = _read_cmd_text()
    assert "setlocal" in text.lower(), "Windows shim must use setlocal for variable isolation"


def test_windows_shim_error_to_stderr():
    text = _read_cmd_text()
    # >&2 or 1>&2 redirects to stderr
    assert ">&2" in text, "Windows shim error messages must be written to stderr"


def test_windows_shim_turbulence_config_path():
    text = _read_cmd_text()
    assert "TurbulenceSolutions" in text, \
        "Windows shim must reference TurbulenceSolutions config directory"


# ---------------------------------------------------------------------------
# Unix shim content
# ---------------------------------------------------------------------------


def _read_sh_raw() -> bytes:
    return UNIX_SHIM.read_bytes()


def _read_sh_text() -> str:
    return UNIX_SHIM.read_text(encoding="utf-8")


def test_unix_shim_lf_line_endings():
    raw = _read_sh_raw()
    assert b"\r\n" not in raw, "Unix shim must not have CRLF line endings"
    assert b"\n" in raw, "Unix shim must have LF line endings"


def test_unix_shim_shebang():
    text = _read_sh_text()
    assert text.startswith("#!/bin/sh"), \
        "Unix shim must start with #!/bin/sh shebang"


def test_unix_shim_reads_config():
    text = _read_sh_text()
    assert "python-path.txt" in text, "Unix shim must reference python-path.txt"
    assert "TurbulenceSolutions" in text, \
        "Unix shim must reference TurbulenceSolutions config directory"


def test_unix_shim_xdg_data_home():
    text = _read_sh_text()
    assert "XDG_DATA_HOME" in text, "Unix shim must respect XDG_DATA_HOME"


def test_unix_shim_exec_python():
    text = _read_sh_text()
    assert 'exec "$PYTHON_PATH"' in text or "exec" in text, \
        "Unix shim must exec the python process (replace shim process)"
    assert '"$@"' in text, "Unix shim must forward all args with $@"


def test_unix_shim_missing_config_error():
    text = _read_sh_text()
    assert '[ ! -f' in text or "! -f" in text, \
        "Unix shim must check if config file exists"
    assert "exit 1" in text, "Unix shim must exit with code 1 on error"


def test_unix_shim_missing_python_error():
    text = _read_sh_text()
    assert "! -x" in text or "[ ! -x" in text, \
        "Unix shim must check if python executable is executable"


def test_unix_shim_error_to_stderr():
    text = _read_sh_text()
    assert ">&2" in text, "Unix shim error messages must be written to stderr"


# ---------------------------------------------------------------------------
# shim_config.py — import
# ---------------------------------------------------------------------------


sys.path.insert(0, str(REPO_ROOT / "src"))
from launcher.core import shim_config  # noqa: E402


# ---------------------------------------------------------------------------
# get_config_dir()
# ---------------------------------------------------------------------------


def test_get_config_dir_windows():
    """On Windows (or mocked), uses LOCALAPPDATA."""
    fake_local = "/fake/AppData/Local"
    with patch.dict(os.environ, {"LOCALAPPDATA": fake_local}):
        with patch("launcher.core.shim_config.platform.system", return_value="Windows"):
            result = shim_config.get_config_dir()
    assert result == Path(fake_local) / "TurbulenceSolutions"


def test_get_config_dir_windows_fallback():
    """On Windows, falls back to home/AppData/Local when LOCALAPPDATA is absent."""
    env_without_localappdata = {
        k: v for k, v in os.environ.items() if k != "LOCALAPPDATA"
    }
    with patch.dict(os.environ, env_without_localappdata, clear=True):
        with patch("launcher.core.shim_config.platform.system", return_value="Windows"):
            with patch("launcher.core.shim_config.Path.home", return_value=Path("/home/user")):
                result = shim_config.get_config_dir()
    assert result == Path("/home/user") / "AppData" / "Local" / "TurbulenceSolutions"


def test_get_config_dir_unix_xdg():
    """On Linux/macOS, uses XDG_DATA_HOME when set."""
    fake_xdg = "/custom/data"
    with patch.dict(os.environ, {"XDG_DATA_HOME": fake_xdg}):
        with patch("launcher.core.shim_config.platform.system", return_value="Linux"):
            result = shim_config.get_config_dir()
    assert result == Path(fake_xdg) / "TurbulenceSolutions"


def test_get_config_dir_unix_fallback():
    """On Linux/macOS, falls back to ~/.local/share when XDG_DATA_HOME is absent."""
    env_without_xdg = {
        k: v for k, v in os.environ.items() if k != "XDG_DATA_HOME"
    }
    with patch.dict(os.environ, env_without_xdg, clear=True):
        with patch("launcher.core.shim_config.platform.system", return_value="Linux"):
            with patch("launcher.core.shim_config.Path.home", return_value=Path("/home/user")):
                result = shim_config.get_config_dir()
    assert result == Path("/home/user") / ".local" / "share" / "TurbulenceSolutions"


def test_get_config_dir_macos():
    """On macOS, uses the same XDG fallback path."""
    env_without_xdg = {
        k: v for k, v in os.environ.items() if k != "XDG_DATA_HOME"
    }
    with patch.dict(os.environ, env_without_xdg, clear=True):
        with patch("launcher.core.shim_config.platform.system", return_value="Darwin"):
            with patch("launcher.core.shim_config.Path.home", return_value=Path("/home/user")):
                result = shim_config.get_config_dir()
    assert result == Path("/home/user") / ".local" / "share" / "TurbulenceSolutions"


# ---------------------------------------------------------------------------
# get_shim_dir()
# ---------------------------------------------------------------------------


def test_get_shim_dir():
    """Shim dir is always config_dir / 'bin'."""
    with patch("launcher.core.shim_config.platform.system", return_value="Windows"):
        with patch.dict(os.environ, {"LOCALAPPDATA": "/fake/local"}):
            result = shim_config.get_shim_dir()
    assert result.name == "bin"
    assert result.parent.name == "TurbulenceSolutions"


# ---------------------------------------------------------------------------
# get_python_path_config()
# ---------------------------------------------------------------------------


def test_get_python_path_config():
    """Config file is always config_dir / 'python-path.txt'."""
    with patch("launcher.core.shim_config.platform.system", return_value="Windows"):
        with patch.dict(os.environ, {"LOCALAPPDATA": "/fake/local"}):
            result = shim_config.get_python_path_config()
    assert result.name == "python-path.txt"
    assert result.parent.name == "TurbulenceSolutions"


# ---------------------------------------------------------------------------
# write_python_path() and read_python_path()
# ---------------------------------------------------------------------------


def test_write_python_path_creates_file(tmp_path):
    """write_python_path() creates the config file with the exe path."""
    fake_exe = tmp_path / "python.exe"
    fake_exe.touch()

    config_file = tmp_path / "config" / "python-path.txt"
    with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
        shim_config.write_python_path(fake_exe)

    assert config_file.exists()
    assert config_file.read_text(encoding="utf-8") == str(fake_exe)


def test_write_python_path_creates_parent_dirs(tmp_path):
    """write_python_path() creates intermediate directories."""
    nested_config = tmp_path / "a" / "b" / "c" / "python-path.txt"
    fake_exe = Path("/some/python.exe")

    with patch("launcher.core.shim_config.get_python_path_config", return_value=nested_config):
        shim_config.write_python_path(fake_exe)

    assert nested_config.parent.is_dir()
    assert nested_config.exists()


def test_read_python_path_returns_path(tmp_path):
    """read_python_path() returns a Path when config file contains a path."""
    config_file = tmp_path / "python-path.txt"
    config_file.write_text("/some/python/bin/python3", encoding="utf-8")

    with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
        result = shim_config.read_python_path()

    assert result == Path("/some/python/bin/python3")


def test_read_python_path_strips_whitespace(tmp_path):
    """read_python_path() strips leading/trailing whitespace from the stored path."""
    config_file = tmp_path / "python-path.txt"
    config_file.write_text("  /some/python.exe  \n", encoding="utf-8")

    with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
        result = shim_config.read_python_path()

    assert result == Path("/some/python.exe")


def test_read_python_path_returns_none_missing(tmp_path):
    """read_python_path() returns None when config file does not exist."""
    config_file = tmp_path / "nonexistent" / "python-path.txt"

    with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
        result = shim_config.read_python_path()

    assert result is None


def test_read_python_path_returns_none_empty(tmp_path):
    """read_python_path() returns None when config file is empty."""
    config_file = tmp_path / "python-path.txt"
    config_file.write_text("", encoding="utf-8")

    with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
        result = shim_config.read_python_path()

    assert result is None


def test_read_python_path_returns_none_whitespace_only(tmp_path):
    """read_python_path() returns None when config file contains only whitespace."""
    config_file = tmp_path / "python-path.txt"
    config_file.write_text("   \n  \t  ", encoding="utf-8")

    with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
        result = shim_config.read_python_path()

    assert result is None


# ---------------------------------------------------------------------------
# verify_shim()
# ---------------------------------------------------------------------------


def test_verify_shim_ok(tmp_path):
    """verify_shim() returns (True, message) when config exists and exe exists."""
    fake_exe = tmp_path / "python.exe"
    fake_exe.touch()

    with patch("launcher.core.shim_config.read_python_path", return_value=fake_exe):
        ok, msg = shim_config.verify_shim()

    assert ok is True
    assert str(fake_exe) in msg


def test_verify_shim_no_config():
    """verify_shim() returns (False, message) when config is missing."""
    with patch("launcher.core.shim_config.read_python_path", return_value=None):
        ok, msg = shim_config.verify_shim()

    assert ok is False
    assert "not found" in msg.lower() or "configuration" in msg.lower()


def test_verify_shim_bad_path(tmp_path):
    """verify_shim() returns (False, message) when exe path does not exist."""
    nonexistent = tmp_path / "missing" / "python.exe"

    with patch("launcher.core.shim_config.read_python_path", return_value=nonexistent):
        ok, msg = shim_config.verify_shim()

    assert ok is False
    assert "not found" in msg.lower() or str(nonexistent) in msg


def test_verify_shim_returns_tuple():
    """verify_shim() always returns a 2-tuple of (bool, str)."""
    with patch("launcher.core.shim_config.read_python_path", return_value=None):
        result = shim_config.verify_shim()

    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], bool)
    assert isinstance(result[1], str)
