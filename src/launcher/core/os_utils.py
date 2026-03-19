"""Operating system detection and cross-platform path utilities."""

from __future__ import annotations

import platform


def get_platform() -> str:
    """Return the current OS as a normalised string.

    Returns:
        ``'windows'``, ``'macos'``, or ``'linux'``.
    """
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    return "linux"
