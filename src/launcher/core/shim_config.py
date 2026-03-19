"""ts-python shim configuration helpers."""
import os
import platform
import shutil
import subprocess
from pathlib import Path


def get_config_dir() -> Path:
    """Return the platform-specific TurbulenceSolutions config directory."""
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA", "")
        if not base:
            base = str(Path.home() / "AppData" / "Local")
        return Path(base) / "TurbulenceSolutions"
    else:
        base = os.environ.get("XDG_DATA_HOME", "")
        if not base:
            base = str(Path.home() / ".local" / "share")
        return Path(base) / "TurbulenceSolutions"


def get_shim_dir() -> Path:
    """Return the shim bin directory."""
    return get_config_dir() / "bin"


def get_python_path_config() -> Path:
    """Return the path to python-path.txt."""
    return get_config_dir() / "python-path.txt"


def write_python_path(python_exe: Path) -> None:
    """Write the Python executable path to the config file."""
    config = get_python_path_config()
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(str(python_exe), encoding="utf-8")


def read_python_path() -> "Path | None":
    """Read the configured Python path. Returns None if not configured."""
    config = get_python_path_config()
    if not config.exists():
        return None
    text = config.read_text(encoding="utf-8").strip()
    if not text:
        return None
    return Path(text)


def verify_shim() -> "tuple[bool, str]":
    """Verify the ts-python shim is functional. Returns (ok, message)."""
    python_path = read_python_path()
    if python_path is None:
        return False, "Python path configuration not found"
    if not python_path.exists():
        return False, f"Python executable not found: {python_path}"
    return True, f"ts-python configured: {python_path}"


def verify_ts_python() -> "tuple[bool, str]":
    """Verify the ts-python shim by testing the configured Python runtime.

    Instead of invoking ts-python.cmd through cmd.exe /c (which has
    fragile quoting/parsing with paths containing spaces or special
    characters), this directly reads python-path.txt and calls the
    Python executable.  The shim file existence is verified separately.

    Returns ``(True, version_string)`` on success or
    ``(False, error_message)`` on failure.
    """
    # Step 1: Verify python-path.txt is configured and points to a real file.
    python_path = read_python_path()
    if python_path is None:
        return False, "Python path configuration not found."
    if not python_path.exists():
        return False, f"Python executable not found: {python_path}"

    # Step 2: Verify the shim script exists at the expected location.
    system = platform.system()
    if system == "Windows":
        shim_file = get_shim_dir() / "ts-python.cmd"
    else:
        shim_file = get_shim_dir() / "ts-python"
    if not shim_file.exists():
        # Also check PATH as fallback.
        found = shutil.which("ts-python.cmd") if system == "Windows" else shutil.which("ts-python")
        if found is None:
            return False, "ts-python shim not found on PATH or in shim directory."

    # Step 3: Execute the Python runtime directly (bypass cmd.exe entirely).
    try:
        result = subprocess.run(
            [str(python_path), "-c", "import sys; print(sys.version)"],
            capture_output=True,
            text=True,
            timeout=30,
            stdin=subprocess.DEVNULL,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        stderr = result.stderr.strip()
        return False, f"Python exited with code {result.returncode}: {stderr}"
    except subprocess.TimeoutExpired:
        return False, "Python runtime timed out after 30 seconds."
    except FileNotFoundError:
        return False, f"Python executable not found: {python_path}"
    except OSError as exc:
        return False, f"Failed to run Python runtime: {exc}"
