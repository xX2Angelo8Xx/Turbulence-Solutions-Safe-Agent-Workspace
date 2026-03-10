"""VS Code detection and launch utilities.

Full implementation is provided in GUI-006.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def find_vscode() -> str | None:
    """Return the path to the VS Code executable, or None if not found."""
    return shutil.which("code")


def open_in_vscode(workspace_path: Path) -> bool:
    """Open *workspace_path* in VS Code.

    Returns True on success, False if VS Code is not found.
    """
    exe = find_vscode()
    if exe is None:
        return False

    # Use a list argument — never shell=True — to prevent command injection.
    subprocess.Popen([exe, str(workspace_path)])  # noqa: S603
    return True
