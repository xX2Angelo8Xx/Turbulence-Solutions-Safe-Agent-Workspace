"""Folder name validation utilities for the Turbulence Solutions Launcher."""

from __future__ import annotations

import os
import re

_INVALID_CHARS_RE = re.compile(r'[:\\/*?|<>"\x00-\x1f]')
_WINDOWS_RESERVED_RE = re.compile(
    r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$", re.IGNORECASE
)


def validate_folder_name(name: str) -> tuple[bool, str]:
    """Return (True, "") if name is a valid folder name, else (False, reason)."""
    if name and name[-1] in (".", " "):
        return False, "Name cannot end with a dot or space."
    stripped = name.strip()
    if not stripped:
        return False, "Name cannot be empty."
    if stripped in (".", ".."):
        return False, "Name cannot be '.' or '..'."
    if len(stripped) > 255:
        return False, "Name is too long (maximum 255 characters)."
    if _INVALID_CHARS_RE.search(stripped):
        return False, "Name contains invalid characters."
    if _WINDOWS_RESERVED_RE.match(stripped):
        return False, f"'{stripped}' is a reserved name on Windows."
    return True, ""


def check_duplicate_folder(name: str, destination: str) -> bool:
    """Return True if a file or folder named *name* already exists in *destination*."""
    if not name or not destination:
        return False
    return os.path.exists(os.path.join(destination, name))
