"""Project creation logic — copies a template to the user's chosen destination.

Full implementation is provided in GUI-005.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
from pathlib import Path

from launcher.config import VERSION

_COUNTER_CONFIG_PATH = Path(".github") / "hooks" / "scripts" / "counter_config.json"
_DEFAULT_COUNTER_ENABLED = True
_DEFAULT_COUNTER_THRESHOLD = 20


def write_counter_config(
    project_dir: Path, counter_enabled: bool, counter_threshold: int
) -> None:
    """Write counter_config.json into the workspace's .github/hooks/scripts/ directory."""
    config_path = project_dir / _COUNTER_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_data = {
        "counter_enabled": counter_enabled,
        "lockout_threshold": counter_threshold,
    }
    config_path.write_text(json.dumps(config_data, indent=4), encoding="utf-8")


def create_project(
    template_path: Path,
    destination: Path,
    folder_name: str,
    counter_enabled: bool = _DEFAULT_COUNTER_ENABLED,
    counter_threshold: int = _DEFAULT_COUNTER_THRESHOLD,
    include_readmes: bool = True,
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

    # Prepend the SAE- brand prefix to the folder name.
    prefixed_name = f"SAE-{folder_name}"

    # Guard against path-traversal in folder_name (e.g. "../../etc").
    target = (destination / prefixed_name).resolve()
    if not target.is_relative_to(destination.resolve()):
        raise ValueError(
            "Invalid folder name: path traversal attempt detected"
        )

    shutil.copytree(str(template_path), str(target))

    # Write counter config from GUI settings into the new workspace (GUI-020).
    write_counter_config(target, counter_enabled, counter_threshold)

    # Rename the internal "Project/" subfolder to match the user's project name.
    # This gives the working folder a meaningful name (e.g. "MatlabDemo/").
    internal_project = target / "Project"
    renamed_project = target / folder_name
    if internal_project.is_dir() and not renamed_project.exists():
        internal_project.rename(renamed_project)

    # Replace placeholder tokens in all .md files within the new project tree.
    replace_template_placeholders(target, folder_name)

    # Remove README.md files when not requested (INS-023).
    if not include_readmes:
        for dirpath, _dirnames, filenames in os.walk(target):
            for filename in filenames:
                if filename == "README.md":
                    path = os.path.join(dirpath, filename)
                    try:
                        os.unlink(path)
                    except PermissionError:
                        # Read-only file (common on Windows) — clear write-protect then retry.
                        try:
                            os.chmod(path, stat.S_IWRITE)
                            os.unlink(path)
                        except OSError:
                            pass
                    except FileNotFoundError:
                        pass

    return target


def replace_template_placeholders(
    project_dir: Path, project_name: str, version: str = VERSION
) -> None:
    """Replace placeholder tokens in .md files and the .github/version file under *project_dir*.

    Tokens replaced:
      {{PROJECT_NAME}}    → project_name
      {{WORKSPACE_NAME}}  → SAE-{project_name}
      {{VERSION}}         → version

    All .md files in the project tree are processed via rglob, including
    (but not limited to):
      - <project_name>/AGENT-RULES.md
      - <project_name>/README.md
      - .github/instructions/copilot-instructions.md

    The `.github/version` file (extensionless) is also processed so that
    `{{VERSION}}` is replaced with the launcher version string.

    Non-.md files (except the version file) and binary files are skipped.
    The function is idempotent: if no placeholder is found the file is not written.
    """
    workspace_name = f"SAE-{project_name}"

    candidates = list(project_dir.rglob("*.md")) + list(project_dir.rglob("version"))
    for file_path in candidates:
        if not file_path.is_file():
            continue
        try:
            original = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            # Skip files that cannot be decoded as UTF-8 (e.g. binary files).
            continue

        updated = original.replace("{{PROJECT_NAME}}", project_name)
        updated = updated.replace("{{WORKSPACE_NAME}}", workspace_name)
        updated = updated.replace("{{VERSION}}", version)

        if updated != original:
            try:
                file_path.write_text(updated, encoding="utf-8")
            except OSError:
                # Skip read-only or otherwise unwritable files (mirrors the
                # read-guard above — silently continue rather than raising).
                continue


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
