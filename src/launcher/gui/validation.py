"""Folder name validation for the Turbulence Solutions Launcher."""

from __future__ import annotations

import re
from pathlib import Path

_INVALID_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

_WINDOWS_RESERVED = frozenset({
    "con", "prn", "aux", "nul",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
})


def validate_folder_name(name: str) -> tuple[bool, str]:
    """Validate a project folder name against cross-platform file system rules.

    Returns:
        (True, "") if the name is valid.
        (False, error_message) if the name is invalid.
    """
    if not name or not name.strip():
        return False, "Project name cannot be empty."

    if name[-1] in (".", " "):
        return False, "Name cannot end with a period or space."

    stripped = name.strip()

    if len(stripped) > 255:
        return False, "Name is too long (maximum 255 characters)."

    if _INVALID_CHARS_RE.search(stripped):
        return False, 'Name contains invalid characters: < > : " / \\ | ? * or control characters.'

    if stripped in (".", ".."):
        return False, 'Name cannot be "." or "..".'

    if stripped.lower() in _WINDOWS_RESERVED:
        return False, f'"{stripped}" is a reserved system name and cannot be used.'

    return True, ""


def check_duplicate_folder(name: str, destination: str) -> bool:
    """Return True if <destination>/<name> already exists on disk."""
    if not name or not destination:
        return False
    target = Path(destination) / name
    return target.exists()
