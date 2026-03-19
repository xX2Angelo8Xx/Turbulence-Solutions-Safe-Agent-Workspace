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
    """Verify the ts-python shim by actually executing it.

    Runs ``ts-python -c "import sys; print(sys.version)"`` via subprocess
    with a 30-second timeout. Returns ``(True, version_string)`` on success
    or ``(False, error_message)`` on failure.

    On Windows, prefers ``ts-python.cmd`` from the configured shim directory,
    then falls back to a PATH lookup. ``.cmd`` files are invoked via
    ``cmd.exe /c`` to prevent hangs from stdin inheritance and to ensure
    correct interpretation on Windows ARM under x64 emulation.
    On Unix/macOS, looks for ``ts-python`` on PATH. Never uses ``shell=True``.
    """
    system = platform.system()
    shim_exe: "str | None" = None
    use_cmd_wrapper = False

    if system == "Windows":
        # Prefer ts-python.cmd in the configured shim directory.
        candidate = get_shim_dir() / "ts-python.cmd"
        if candidate.exists():
            shim_exe = str(candidate)
        else:
            # Fall back to PATH lookup.
            shim_exe = shutil.which("ts-python.cmd") or shutil.which("ts-python")
        # .cmd files must be invoked via cmd.exe /c to prevent hangs on
        # Windows ARM (x64 emulation) and stdin inheritance issues.
        if shim_exe is not None and shim_exe.lower().endswith(".cmd"):
            use_cmd_wrapper = True
    else:
        shim_exe = shutil.which("ts-python")

    if shim_exe is None:
        return False, "ts-python shim not found on PATH or in shim directory."

    if use_cmd_wrapper:
        cmd_args = ["cmd.exe", "/c", shim_exe, "-c", "import sys; print(sys.version)"]
    else:
        cmd_args = [shim_exe, "-c", "import sys; print(sys.version)"]

    try:
        result = subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            timeout=30,
            stdin=subprocess.DEVNULL,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        stderr = result.stderr.strip()
        return False, f"ts-python exited with code {result.returncode}: {stderr}"
    except subprocess.TimeoutExpired:
        return False, "ts-python shim timed out after 30 seconds."
    except FileNotFoundError:
        return False, f"ts-python executable not found: {shim_exe}"
    except OSError as exc:
        return False, f"Failed to run ts-python shim: {exc}"
