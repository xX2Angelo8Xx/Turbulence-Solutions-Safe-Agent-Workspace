"""ts-python shim configuration helpers."""
import os
import platform
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
