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

    # Prepend the TS-SAE- brand prefix to the folder name.
    prefixed_name = f"TS-SAE-{folder_name}"

    # Guard against path-traversal in folder_name (e.g. "../../etc").
    target = (destination / prefixed_name).resolve()
    if not target.is_relative_to(destination.resolve()):
        raise ValueError(
            "Invalid folder name: path traversal attempt detected"
        )

    shutil.copytree(str(template_path), str(target))

    # Rename the internal "Project/" subfolder to match the user's project name.
    # This gives the working folder a meaningful name (e.g. "MatlabDemo/").
    internal_project = target / "Project"
    renamed_project = target / folder_name
    if internal_project.is_dir() and not renamed_project.exists():
        internal_project.rename(renamed_project)

    return target


def list_templates(templates_dir: Path) -> list[str]:
    """Return a sorted list of template directory names under *templates_dir*.

    Returns an empty list if the path does not exist or is not a directory.
    """
    if not isinstance(templates_dir, Path) or not templates_dir.is_dir():
        return []
    return sorted(entry.name for entry in templates_dir.iterdir() if entry.is_dir())


def is_template_ready(templates_dir: Path, template_name: str) -> bool:
    """Return True if the template directory has files beyond just README.md."""
    template_path = templates_dir / template_name
    if not template_path.is_dir():
        return False
    contents = [f.name for f in template_path.iterdir()]
    # A template is ready if it has more than just README.md
    return len(contents) > 1 or (len(contents) == 1 and contents[0] != "README.md")
