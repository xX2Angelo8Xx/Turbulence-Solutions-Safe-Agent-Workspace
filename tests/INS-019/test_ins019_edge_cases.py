"""
Edge-case and security tests for INS-019: ts-python shim and config system.

Added by Tester Agent, 2026-03-19.

Covers:
- Security: path traversal in config, command injection vectors, quoted execution
- Encoding: UTF-8 BOM (fail-closed), CRLF stripping, non-ASCII paths
- Boundary: empty env vars, very long paths, embedded newlines (fail-closed)
- Integration: write/read roundtrip, overwrite existing
- Robustness: PermissionError propagation (fail-closed)
- Return type guarantees: get_config_dir, get_python_path_config always return Path
- Shim content: $HOME fallback, ${XDG_DATA_HOME:-...} expression
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SHIMS_DIR = REPO_ROOT / "src" / "installer" / "shims"
WINDOWS_SHIM = SHIMS_DIR / "ts-python.cmd"
UNIX_SHIM = SHIMS_DIR / "ts-python"

sys.path.insert(0, str(REPO_ROOT / "src"))
from launcher.core import shim_config  # noqa: E402


# ---------------------------------------------------------------------------
# Security: path traversal in config content
# ---------------------------------------------------------------------------


def test_read_python_path_traversal_returned_as_is(tmp_path):
    """read_python_path() returns path traversal strings without sanitization.

    This documents the security boundary: the installer must write a safe path.
    The function itself is transparent — the caller (verify_shim) validates
    existence, and a traversal path will not exist, giving fail-closed behaviour.
    """
    config_file = tmp_path / "python-path.txt"
    config_file.write_text("../../../etc/shadow", encoding="utf-8")

    with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
        result = shim_config.read_python_path()

    # The raw path string is returned — caller must validate
    assert result == Path("../../../etc/shadow")


def test_verify_shim_traversal_path_returns_false():
    """verify_shim() safely returns False when the configured path doesn't exist.

    Even if python-path.txt contains a traversal-like string, verify_shim()
    returns (False, msg) as long as the target file doesn't exist — fail-closed.
    """
    nonexistent = Path("../../../etc/shadow")

    with patch("launcher.core.shim_config.read_python_path", return_value=nonexistent):
        ok, msg = shim_config.verify_shim()

    assert ok is False
    assert "not found" in msg.lower() or str(nonexistent) in msg


def test_verify_shim_existence_only_check(tmp_path):
    """verify_shim() performs existence check only — authenticating the path is
    the installer's responsibility. Any existing file passes.
    """
    # Simulate an arbitrary file (not a real Python interpreter) stored in config
    arbitrary_file = tmp_path / "some_file.txt"
    arbitrary_file.touch()

    with patch("launcher.core.shim_config.read_python_path", return_value=arbitrary_file):
        ok, msg = shim_config.verify_shim()

    # verify_shim is intentionally an existence-only check — installer is responsible
    assert ok is True


# ---------------------------------------------------------------------------
# Security: shim command injection protection
# ---------------------------------------------------------------------------


def test_windows_shim_python_path_is_quoted():
    """Windows shim invokes the Python executable inside double quotes.

    %PYTHON_PATH% must be double-quoted to handle spaces and special characters
    in the path without enabling command injection.
    """
    text = WINDOWS_SHIM.read_text(encoding="utf-8")
    assert '"%PYTHON_PATH%"' in text, (
        "Windows shim must invoke Python path with double quotes "
        "to handle spaces and prevent injection"
    )


def test_unix_shim_python_path_is_double_quoted():
    """Unix shim uses double-quoted $PYTHON_PATH (prevents word splitting and glob expansion)."""
    text = UNIX_SHIM.read_text(encoding="utf-8")
    assert '"$PYTHON_PATH"' in text, (
        'Unix shim must use "$PYTHON_PATH" (double-quoted) to prevent word splitting'
    )


def test_unix_shim_args_double_quoted():
    """Unix shim forwards arguments with "$@" to preserve argument boundaries."""
    text = UNIX_SHIM.read_text(encoding="utf-8")
    assert '"$@"' in text, (
        'Unix shim must use "$@" not bare $@ to preserve per-argument boundaries'
    )


# ---------------------------------------------------------------------------
# Encoding: CRLF in python-path.txt
# ---------------------------------------------------------------------------


def test_read_python_path_crlf_stripped(tmp_path):
    """read_python_path() strips CRLF from config content (e.g., file written on Windows)."""
    config_file = tmp_path / "python-path.txt"
    # Write with CRLF line endings (as would happen on Windows editors)
    config_file.write_bytes(b"C:\\Python311\\python.exe\r\n")

    with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
        result = shim_config.read_python_path()

    assert result is not None
    assert "\r" not in str(result), "Carriage return must be stripped from config path"
    assert str(result) == "C:\\Python311\\python.exe"


# ---------------------------------------------------------------------------
# Encoding: UTF-8 BOM in python-path.txt
# ---------------------------------------------------------------------------


def test_read_python_path_bom_causes_fail_closed(tmp_path):
    """UTF-8 BOM in python-path.txt is not stripped, causing verify_shim to fail safely.

    Python's read_text(encoding='utf-8') does NOT strip UTF-8 BOM (U+FEFF).
    The resulting path is prefixed with \\ufeff and will never exist on the
    filesystem — this is correct fail-closed behaviour.
    """
    config_file = tmp_path / "python-path.txt"
    # Write UTF-8 BOM followed by a path
    config_file.write_bytes(b"\xef\xbb\xbf/usr/bin/python3")

    with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
        result = shim_config.read_python_path()

    # The BOM-prefixed path will not exist on the filesystem
    assert result is not None
    assert not result.exists(), (
        "BOM-prefixed path must not exist (ensuring fail-closed security behaviour)"
    )


# ---------------------------------------------------------------------------
# Encoding: Non-ASCII (Unicode) path in config
# ---------------------------------------------------------------------------


def test_read_python_path_unicode_path(tmp_path):
    """read_python_path() correctly decodes paths containing non-ASCII characters."""
    unicode_path = "/home/üser/python-embed/python3"
    config_file = tmp_path / "python-path.txt"
    config_file.write_text(unicode_path, encoding="utf-8")

    with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
        result = shim_config.read_python_path()

    assert result == Path(unicode_path)


# ---------------------------------------------------------------------------
# Boundary: embedded newline in config (fail-closed)
# ---------------------------------------------------------------------------


def test_read_python_path_embedded_newline_safe(tmp_path):
    """An embedded newline in python-path.txt produces a path that doesn't exist.

    strip() removes only leading/trailing whitespace.  An embedded newline
    inside the path string is preserved, making the resulting path invalid on
    the filesystem — the shim correctly fails closed.
    """
    config_file = tmp_path / "python-path.txt"
    # Simulate a corrupted two-line config file
    config_file.write_text(
        "/path/to/python3\n/injected/extra/line", encoding="utf-8"
    )

    with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
        result = shim_config.read_python_path()

    # The embedded newline is NOT removed by strip()
    assert result is not None
    # The corrupted path will not exist → verify_shim returns False (fail-closed)
    with patch("launcher.core.shim_config.read_python_path", return_value=result):
        ok, _ = shim_config.verify_shim()
    assert ok is False


# ---------------------------------------------------------------------------
# Boundary: empty environment variables fall back correctly
# ---------------------------------------------------------------------------


def test_get_config_dir_windows_empty_localappdata():
    """get_config_dir() uses fallback when LOCALAPPDATA is present but empty."""
    with patch.dict(os.environ, {"LOCALAPPDATA": ""}):
        with patch("launcher.core.shim_config.platform.system", return_value="Windows"):
            with patch(
                "launcher.core.shim_config.Path.home", return_value=Path("/home/user")
            ):
                result = shim_config.get_config_dir()

    # Empty string is falsy → falls back to home/AppData/Local
    assert result == Path("/home/user") / "AppData" / "Local" / "TurbulenceSolutions"


def test_get_config_dir_unix_empty_xdg_data_home():
    """get_config_dir() uses fallback when XDG_DATA_HOME is present but empty."""
    with patch.dict(os.environ, {"XDG_DATA_HOME": ""}):
        with patch("launcher.core.shim_config.platform.system", return_value="Linux"):
            with patch(
                "launcher.core.shim_config.Path.home", return_value=Path("/home/user")
            ):
                result = shim_config.get_config_dir()

    # Empty string is falsy → falls back to home/.local/share
    assert result == Path("/home/user") / ".local" / "share" / "TurbulenceSolutions"


# ---------------------------------------------------------------------------
# Boundary: very long path in config
# ---------------------------------------------------------------------------


def test_read_python_path_very_long_path(tmp_path):
    """read_python_path() handles paths with long segments without error."""
    long_segment = "p" * 200  # 200-char segment, well under 260-char Windows MAX_PATH
    long_path = f"/usr/local/{long_segment}/python3"
    config_file = tmp_path / "python-path.txt"
    config_file.write_text(long_path, encoding="utf-8")

    with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
        result = shim_config.read_python_path()

    assert result == Path(long_path)
    # Verify the full segment length is preserved (path comparison normalises separators)
    assert long_segment in str(result)


# ---------------------------------------------------------------------------
# Integration: write/read roundtrip
# ---------------------------------------------------------------------------


def test_write_read_roundtrip(tmp_path):
    """write_python_path() followed by read_python_path() reproduces the original path."""
    config_file = tmp_path / "config" / "python-path.txt"
    python_exe = Path("/usr/local/bin/python3")

    with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
        shim_config.write_python_path(python_exe)
        result = shim_config.read_python_path()

    assert result == python_exe


def test_write_python_path_overwrites_existing(tmp_path):
    """write_python_path() replaces the content of an existing config file."""
    config_file = tmp_path / "python-path.txt"
    config_file.write_text("/old/python.exe", encoding="utf-8")

    new_exe = Path("/new/python.exe")
    with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
        shim_config.write_python_path(new_exe)

    assert config_file.read_text(encoding="utf-8") == str(new_exe)
    assert "old" not in config_file.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Robustness: PermissionError propagates (fail-closed)
# ---------------------------------------------------------------------------


def test_read_python_path_propagates_permission_error(tmp_path):
    """read_python_path() lets PermissionError propagate (fail-closed behaviour).

    When the config file exists but cannot be read, the exception bubbles up
    so the caller knows the shim is in an error state rather than silently
    appearing unconfigured.
    """
    config_file = tmp_path / "python-path.txt"
    config_file.write_text("/some/python.exe", encoding="utf-8")

    with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
        # Patch Path.read_text globally — exists() (uses stat) is not affected
        with patch("pathlib.Path.read_text", side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                shim_config.read_python_path()


# ---------------------------------------------------------------------------
# Return type guarantees
# ---------------------------------------------------------------------------


def test_get_config_dir_returns_path_object_windows():
    """get_config_dir() always returns a Path object (not a str) on Windows."""
    with patch.dict(os.environ, {"LOCALAPPDATA": "C:\\Users\\test\\AppData\\Local"}):
        with patch("launcher.core.shim_config.platform.system", return_value="Windows"):
            result = shim_config.get_config_dir()
    assert isinstance(result, Path)


def test_get_config_dir_returns_path_object_unix():
    """get_config_dir() always returns a Path object (not a str) on Unix."""
    with patch.dict(os.environ, {"XDG_DATA_HOME": "/custom/data"}):
        with patch("launcher.core.shim_config.platform.system", return_value="Linux"):
            result = shim_config.get_config_dir()
    assert isinstance(result, Path)


def test_get_python_path_config_returns_path_object():
    """get_python_path_config() returns a Path object, not a str."""
    with patch("launcher.core.shim_config.platform.system", return_value="Windows"):
        with patch.dict(os.environ, {"LOCALAPPDATA": "/fake/local"}):
            result = shim_config.get_python_path_config()
    assert isinstance(result, Path)


# ---------------------------------------------------------------------------
# Shim content: Unix $HOME fallback and XDG expression
# ---------------------------------------------------------------------------


def test_unix_shim_home_variable_in_fallback():
    """Unix shim uses $HOME as the base of the XDG_DATA_HOME fallback."""
    text = UNIX_SHIM.read_text(encoding="utf-8")
    assert "$HOME" in text, (
        "Unix shim must reference $HOME as fallback for XDG_DATA_HOME"
    )


def test_unix_shim_xdg_default_value_expression():
    """Unix shim uses the POSIX default-value parameter expression ${VAR:-default}."""
    text = UNIX_SHIM.read_text(encoding="utf-8")
    assert "${XDG_DATA_HOME:-" in text, (
        "Unix shim must use POSIX ${XDG_DATA_HOME:-fallback} syntax"
    )
