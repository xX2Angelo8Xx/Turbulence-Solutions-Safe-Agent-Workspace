"""Project creation logic — copies a template to the user's chosen destination.

Full implementation is provided in GUI-005.
"""

from __future__ import annotations

import shutil
from pathlib import Path


def create_project(
    template_path: Path, destination: Path, folder_name: str
) -> Path:
    """Copy *template_path* into *destination* / *folder_name*.

    Returns the path to the newly created project directory.

    Raises:
        ValueError: If the template path does not exist, the destination is
            invalid, or *folder_name* would escape *destination* via path
            traversal.
    """
    # Validate inputs at the system boundary (security-rules.md §Secure Coding).
    if not template_path.is_dir():
        raise ValueError(
            f"Template path does not exist or is not a directory: {template_path}"
        )
    if not destination.is_dir():
        raise ValueError(
            f"Destination path does not exist or is not a directory: {destination}"
        )

    # Guard against path-traversal in folder_name (e.g. "../../etc").
    target = (destination / folder_name).resolve()
    if not target.is_relative_to(destination.resolve()):
        raise ValueError(
            "Invalid folder name: path traversal attempt detected"
        )

    shutil.copytree(str(template_path), str(target))
    return target
