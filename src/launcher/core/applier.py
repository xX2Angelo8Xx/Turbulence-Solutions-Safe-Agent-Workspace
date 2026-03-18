"""Apply a downloaded installer and restart the Launcher (INS-011)."""

from __future__ import annotations

import logging
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

_LOGGER = logging.getLogger(__name__)


def _validate_installer_path(installer_path: Path) -> None:
    """Raise an error if installer_path does not point to an existing file.

    This is a pre-flight check before any OS-level action is taken.
    """
    if not installer_path.exists():
        raise FileNotFoundError(f"Installer file not found: {installer_path}")
    if not installer_path.is_file():
        raise ValueError(f"Installer path is not a regular file: {installer_path}")


def apply_update(installer_path: Path) -> None:
    """Launch the downloaded installer and exit the current Launcher instance.

    Platform dispatch:
    - Windows: runs the Inno Setup .exe silently, then sys.exit(0).
    - macOS:   mounts the .dmg, copies the .app bundle to /Applications,
               unmounts, then sys.exit(0).
    - Linux:   makes the AppImage executable, swaps it with os.replace,
               then relaunches via os.execv.

    Raises FileNotFoundError if installer_path does not exist.
    Raises ValueError if installer_path is not a regular file.
    Raises RuntimeError on any unrecoverable platform-level error.
    """
    _validate_installer_path(installer_path)
    _LOGGER.info(
        "Applying update from: %s (platform=%s)", installer_path, sys.platform
    )

    if sys.platform == "win32":
        _apply_windows(installer_path)
    elif sys.platform == "darwin":
        _apply_macos(installer_path)
    elif sys.platform.startswith("linux"):
        _apply_linux(installer_path)
    else:
        raise RuntimeError(
            f"Unsupported platform for apply_update: {sys.platform!r}"
        )


def _apply_windows(installer_path: Path) -> None:
    """Launch the Inno Setup installer silently and exit the launcher.

    /SILENT    — no progress dialog shown to the user.
    /CLOSEAPPLICATIONS — installer automatically closes any running instances.
    shell=False is mandatory per security-rules.md; args are always a list.
    """
    _LOGGER.info("Windows: launching installer %s", installer_path)
    subprocess.Popen(
        [str(installer_path), "/SILENT", "/CLOSEAPPLICATIONS"],
        shell=False,
    )
    # os._exit() instead of sys.exit() — sys.exit() from a daemon thread
    # only raises SystemExit in that thread; the main thread (tkinter
    # mainloop) continues running.  os._exit() terminates the entire
    # process from any thread.
    os._exit(0)


def _find_app_bundle(directory: Path) -> Path:
    """Return the first .app directory bundle found inside *directory*.

    Raises RuntimeError if no .app directory is present.
    """
    for item in directory.iterdir():
        if item.suffix == ".app" and item.is_dir():
            return item
    raise RuntimeError(f"No .app bundle found in mounted DMG at {directory}")


def _apply_macos(installer_path: Path) -> None:
    """Mount the .dmg, copy the .app to /Applications, unmount, then exit.

    Uses hdiutil for mount/detach and rsync for the atomic copy.  The mount
    point is a dedicated temp directory to avoid polluting /Volumes.
    """
    mount_point = Path(tempfile.mkdtemp(prefix="ts_update_mnt_"))
    _LOGGER.info("macOS: mounting %s at %s", installer_path, mount_point)

    attach_result = subprocess.run(
        [
            "hdiutil", "attach",
            str(installer_path),
            "-mountpoint", str(mount_point),
            "-nobrowse",
            "-quiet",
        ],
        shell=False,
        capture_output=True,
        check=False,
    )
    if attach_result.returncode != 0:
        raise RuntimeError(
            f"hdiutil attach failed (rc={attach_result.returncode}): "
            f"{attach_result.stderr.decode(errors='replace').strip()}"
        )

    try:
        app_bundle = _find_app_bundle(mount_point)
        dest = f"/Applications/{app_bundle.name}/"
        _LOGGER.info("macOS: copying %s -> %s", app_bundle, dest)
        subprocess.run(
            ["rsync", "-a", "--delete", str(app_bundle) + "/", dest],
            shell=False,
            capture_output=True,
            check=True,
        )
    finally:
        # Always unmount, even if the copy step failed.
        subprocess.run(
            ["hdiutil", "detach", str(mount_point), "-quiet"],
            shell=False,
            capture_output=True,
            check=False,
        )

    _LOGGER.info("macOS: update applied, exiting launcher")
    sys.exit(0)


def _apply_linux(installer_path: Path) -> None:
    """Make the AppImage executable, swap it in-place, then relaunch.

    os.replace provides an atomic rename on the same filesystem.
    os.execv replaces the current process image so there is no orphan process.
    """
    _LOGGER.info("Linux: making %s executable", installer_path)
    current_mode = installer_path.stat().st_mode
    installer_path.chmod(
        current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )

    target_path = Path(sys.executable)
    _LOGGER.info("Linux: swapping %s -> %s", installer_path, target_path)
    try:
        os.replace(str(installer_path), str(target_path))
    except PermissionError as exc:
        raise RuntimeError(
            f"Permission denied swapping AppImage at {target_path}: {exc}"
        ) from exc

    _LOGGER.info("Linux: relaunching from %s", target_path)
    # os.execv replaces the current process; sys.argv preserves the original
    # command-line arguments.
    os.execv(str(target_path), sys.argv)
