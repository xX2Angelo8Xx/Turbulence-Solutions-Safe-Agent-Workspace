"""Workspace upgrade logic — updates security-critical files in existing workspaces.

Compares workspace files against the shipped template MANIFEST.json and offers
to update only security-critical files. User project files are NEVER touched.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from launcher.config import TEMPLATES_DIR, VERSION
from launcher.core.project_creator import replace_template_placeholders

_LOGGER = logging.getLogger(__name__)

_MANIFEST_NAME = Path(".github") / "hooks" / "scripts" / "MANIFEST.json"
_VERSION_FILE = Path(".github") / "version"

# Paths that are NEVER upgraded (user content)
_NEVER_TOUCH_PATTERNS = (
    "Project/",
    "NoAgentZone/",
    # FIX-127: counter_config.json stores user-specific threshold/enabled settings.
    # It must never be overwritten by the upgrader, even if somehow marked critical.
    ".github/hooks/scripts/counter_config.json",
    # FIX-129: .github/template stores the template name used during create_project().
    # Overwriting it would break template routing for subsequent upgrades.
    ".github/template",
)


@dataclass
class UpgradeReport:
    """Results of a workspace upgrade check or operation."""

    workspace_version: str = ""
    launcher_version: str = ""
    outdated_files: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    extra_files: list[str] = field(default_factory=list)
    upgraded_files: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    up_to_date: bool = False

    @property
    def needs_upgrade(self) -> bool:
        return bool(self.outdated_files or self.missing_files)


def _sha256(file_path: Path) -> str:
    """Compute SHA256 hex digest for a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _detect_template(workspace_path: Path) -> str:
    """Detect which template was used to create this workspace.

    Reads .github/template written by create_project() (FIX-129).  Falls back
    to 'agent-workbench' for workspaces created before this feature existed.
    """
    template_file = workspace_path / ".github" / "template"
    if template_file.exists():
        try:
            name = template_file.read_text(encoding="utf-8").strip()
            if name in ("agent-workbench", "clean-workspace"):
                return name
        except OSError:
            pass
    # Workspaces created before FIX-129 have no .github/template — default to agent-workbench.
    return "agent-workbench"


def _load_manifest(template_name: str = "agent-workbench") -> dict | None:
    """Load the shipped template MANIFEST.json for the given template."""
    manifest_path = TEMPLATES_DIR / template_name / _MANIFEST_NAME
    if not manifest_path.exists():
        _LOGGER.warning("MANIFEST.json not found at %s", manifest_path)
        return None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        _LOGGER.error("Failed to load MANIFEST.json: %s", exc)
        return None


def _is_user_content(rel_path: str) -> bool:
    """Check if a path is user content that should never be touched."""
    return any(rel_path.startswith(p) for p in _NEVER_TOUCH_PATTERNS)


def _detect_project_name(workspace_path: Path) -> str:
    """Derive the project name from the workspace folder name.

    Workspace folders are named SAE-{project_name} by convention.
    Strips the SAE- prefix; returns the folder name as-is if the prefix is absent.
    """
    folder = workspace_path.name
    if folder.startswith("SAE-"):
        return folder[len("SAE-"):]
    return folder


def get_workspace_version(workspace_path: Path) -> str:
    """Read the version from a workspace's .github/version file."""
    version_file = workspace_path / _VERSION_FILE
    if version_file.exists():
        try:
            content = version_file.read_text(encoding="utf-8").strip()
            # The version file may contain just a version string or a full line
            for line in content.splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    return stripped
        except OSError:
            pass
    return "unknown"


def check_workspace(workspace_path: Path) -> UpgradeReport:
    """Check a workspace against the template manifest without making changes.

    Returns an UpgradeReport describing what would need to be updated.
    """
    report = UpgradeReport(
        workspace_version=get_workspace_version(workspace_path),
        launcher_version=VERSION,
    )

    template_name = _detect_template(workspace_path)
    manifest = _load_manifest(template_name)
    if manifest is None:
        report.errors.append("Could not load template MANIFEST.json")
        return report

    files = manifest.get("files", {})
    for rel_path, entry in files.items():
        if _is_user_content(rel_path):
            continue
        if not entry.get("security_critical", False):
            continue

        workspace_file = workspace_path / rel_path
        if not workspace_file.exists():
            report.missing_files.append(rel_path)
            continue

        current_hash = _sha256(workspace_file)
        if current_hash != entry["sha256"]:
            report.outdated_files.append(rel_path)

    if not report.needs_upgrade:
        report.up_to_date = True

    return report


def upgrade_workspace(workspace_path: Path, dry_run: bool = False) -> UpgradeReport:
    """Upgrade security-critical files in a workspace to match the current template.

    Only files marked as security_critical in the manifest are touched.
    User content (Project/, NoAgentZone/) is NEVER modified.

    Args:
        workspace_path: Root of the user's workspace (e.g., .../SAE-MyProject/)
        dry_run: If True, report what would change without making changes.

    Returns:
        UpgradeReport with details of what was (or would be) upgraded.
    """
    report = check_workspace(workspace_path)
    if report.errors:
        return report

    if report.up_to_date:
        _LOGGER.info("Workspace is up to date (v%s)", report.workspace_version)
        return report

    template_name = _detect_template(workspace_path)
    template_dir = TEMPLATES_DIR / template_name
    files_to_update = report.outdated_files + report.missing_files

    for rel_path in files_to_update:
        source = template_dir / rel_path
        target = workspace_path / rel_path

        if not source.exists():
            report.errors.append(f"Template source missing: {rel_path}")
            continue

        if dry_run:
            report.upgraded_files.append(f"[DRY-RUN] {rel_path}")
            _LOGGER.info("[DRY-RUN] Would update: %s", rel_path)
            continue

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source), str(target))
            report.upgraded_files.append(rel_path)
            _LOGGER.info("Updated: %s", rel_path)
        except OSError as exc:
            report.errors.append(f"Failed to update {rel_path}: {exc}")

    # Update version file
    if not dry_run and not report.errors:
        version_file = workspace_path / _VERSION_FILE
        try:
            version_file.parent.mkdir(parents=True, exist_ok=True)
            version_file.write_text(VERSION, encoding="utf-8")
            _LOGGER.info("Updated workspace version to %s", VERSION)
        except OSError as exc:
            report.errors.append(f"Failed to update version file: {exc}")

    # Verification pass (must run before placeholder resolution so the hash
    # comparison is against the freshly copied template content, not the resolved copy)
    if not dry_run and not report.errors:
        verify_report = check_workspace(workspace_path)
        if verify_report.needs_upgrade:
            report.errors.append(
                f"Post-upgrade verification failed: {len(verify_report.outdated_files)} "
                f"files still outdated"
            )

    # FIX-127: After verifying the upgrade, re-resolve template placeholders in .md files.
    # The template copy of copilot-instructions.md contains {{PROJECT_NAME}} and
    # {{WORKSPACE_NAME}} tokens. These must be replaced with the actual project name
    # so the upgraded workspace behaves identically to a freshly created one.
    # Runs after the verification pass so the hash check compares raw template content.
    if not dry_run and not report.errors:
        project_name = _detect_project_name(workspace_path)
        try:
            replace_template_placeholders(workspace_path, project_name)
            _LOGGER.info("Resolved template placeholders for project '%s'", project_name)
        except OSError as exc:
            report.errors.append(f"Failed to resolve template placeholders: {exc}")

    return report
