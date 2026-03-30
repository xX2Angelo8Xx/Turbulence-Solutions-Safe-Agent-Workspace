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


def ensure_shim_deployed() -> None:
    """Deploy the ts-python shim on first launch (macOS/Linux only).

    On Windows, the Inno Setup installer handles shim deployment.
    On macOS/Linux, there is no installer post-install step, so the launcher
    deploys the shim on first launch when python-path.txt does not exist yet.
    """
    if platform.system() == "Windows":
        return  # Windows uses Inno Setup for deployment

    config = get_python_path_config()
    if config.exists() and config.read_text(encoding="utf-8").strip():
        return  # Already configured — skip

    shim_source = _find_bundled_shim()
    if shim_source is None:
        return  # Not a bundled build or shim not found

    python_exe = _find_bundled_python_exe()
    if python_exe is None:
        return  # No bundled Python found

    shim_dir = get_shim_dir()
    shim_dir.mkdir(parents=True, exist_ok=True)

    shim_dest = shim_dir / "ts-python"
    shutil.copy2(str(shim_source), str(shim_dest))
    os.chmod(str(shim_dest), 0o755)

    write_python_path(python_exe)

    _add_to_shell_profile(str(shim_dir))


def _find_bundled_shim() -> "Path | None":
    """Locate the ts-python shim bundled with the app."""
    import sys
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller _MEIPASS approach (datas entry in launcher.spec)
        meipass = Path(sys._MEIPASS) / "shims" / "ts-python"
        if meipass.exists():
            return meipass
        # macOS .app layout: Contents/MacOS/launcher → shim at Contents/Resources/shims/
        exe_dir = Path(sys.executable).parent
        resources = exe_dir.parent / "Resources" / "shims" / "ts-python"
        if resources.exists():
            return resources
        # Linux AppImage layout: usr/bin/launcher → shim at usr/share/shims/
        linux_shim = exe_dir / ".." / ".." / "usr" / "share" / "shims" / "ts-python"
        resolved = linux_shim.resolve()
        if resolved.exists():
            return resolved
    return None


def _find_bundled_python_exe() -> "Path | None":
    """Locate the bundled Python executable."""
    import sys
    if hasattr(sys, "_MEIPASS"):
        exe_dir = Path(sys.executable).parent
        # macOS: Python.framework bundled by PyInstaller
        framework = (
            exe_dir
            / "_internal"
            / "Python.framework"
            / "Versions"
            / "Current"
            / "bin"
            / "python3"
        )
        if framework.exists():
            return framework
        # macOS/Linux: python-embed directory next to executable
        for name in ("python3", "python"):
            candidate = exe_dir / "python-embed" / name
            if candidate.exists():
                return candidate
    return None


def _add_to_shell_profile(bin_dir: str) -> None:
    """Append the shim bin directory to shell profile(s) if not already present."""
    export_line = f'\nexport PATH="$PATH:{bin_dir}"\n'

    home = Path.home()
    if platform.system() == "Darwin":
        profiles = [home / ".zshrc", home / ".bashrc"]
    else:
        profiles = [home / ".bashrc", home / ".zshrc"]

    for profile in profiles:
        if not profile.exists():
            continue
        content = profile.read_text(encoding="utf-8", errors="replace")
        if bin_dir in content:
            continue  # Already present
        try:
            with open(profile, "a", encoding="utf-8") as f:
                f.write(export_line)
        except OSError:
            pass  # Best-effort — don't fail if profile is read-only


def _find_bundled_python_for_recovery() -> "Path | None":
    """Locate the bundled Python executable for path auto-recovery.

    Mirrors the logic in SettingsDialog._find_bundled_python() but lives here
    so it can be used without importing any GUI module.
    """
    import sys

    if hasattr(sys, "_MEIPASS"):
        # Running from a PyInstaller bundle — executable sits next to python-embed/.
        exe_dir = Path(sys.executable).parent
    else:
        # Development layout: .venv/Scripts/python.exe → go up two levels to repo root.
        exe_dir = Path(sys.executable).parent.parent

    if sys.platform == "win32":
        candidate = exe_dir / "python-embed" / "python.exe"
    else:
        for name in ("python3", "python"):
            c = exe_dir / "python-embed" / name
            if c.exists():
                return c
        candidate = exe_dir / "python-embed" / "python3"

    return candidate if candidate.exists() else None


def ensure_python_path_valid() -> bool:
    """Validate python-path.txt and auto-recover if the path is missing or invalid.

    Called at launcher startup (FIX-085) to self-heal after an in-app update
    that may have corrupted or not written python-path.txt correctly.

    Returns True if, after this call, python-path.txt points to an existing
    executable.  Returns False if the path could not be established (auto-detect
    also failed) — the caller should warn the user to configure manually.
    """
    python_path = read_python_path()
    if python_path is not None and python_path.exists():
        # Already valid — nothing to do.
        return True

    # Path is missing, empty, or points to a non-existent file.  Attempt recovery.
    recovered = _find_bundled_python_for_recovery()
    if recovered is not None:
        write_python_path(recovered)
        return True

    return False
