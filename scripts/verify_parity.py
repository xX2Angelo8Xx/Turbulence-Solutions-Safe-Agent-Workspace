"""Parity verification for the Agent Environment Launcher (SAF-077).

Verifies that a freshly installed workspace and an upgraded workspace contain
byte-identical security-critical files, guaranteeing users get the same
protection regardless of whether they performed a clean install or an in-place
upgrade.

Design note:
    Both paths (fresh install and upgrade) ultimately source security-critical
    files from the same template directory using shutil.copy2/copytree.
    create_project() performs post-copy modifications (write_counter_config,
    replace_template_placeholders) that intentionally diverge some security-
    critical files from the template. Using shutil.copytree() directly for
    the parity baseline is intentional: it tests the core fidelity guarantee
    (template → workspace) without noise from per-workspace customisation.

Usage:
    python scripts/verify_parity.py [--verbose]

Exit codes:
    0  — all security-critical files match between fresh and upgraded workspace
    1  — one or more files differ (parity failure)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

# Resolve the repository root relative to this script's location.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATES_DIR = _REPO_ROOT / "templates"
_MANIFEST_PATH = _TEMPLATES_DIR / "agent-workbench" / ".github" / "hooks" / "scripts" / "MANIFEST.json"

# Sentinel written into security files to simulate an outdated workspace.
_OLD_CONTENT_SENTINEL = b"__SAF077_OLD_CONTENT_SENTINEL__"

# Files that are expected to differ between create_project() output and a raw
# shutil.copytree() copy of the template (FIX-129).
# - counter_config.json: create_project() writes custom enabled/threshold values.
# - .github/template: not present in the raw template; written by path traversal check.
# These divergences are intentional and should NOT be flagged as parity failures.
_EXPECTED_DIVERGENCE_FILES: frozenset[str] = frozenset({
    ".github/hooks/scripts/counter_config.json",
})

# Placeholder token used in .md files and .github/version by replace_template_placeholders.
# After create_project() resolves these, the files will differ from template copies.
# We normalise by reversing the substitution before comparing.
_PLACEHOLDER_TOKEN = "{{PROJECT_NAME}}"
_PARITY_TEST_PROJECT_NAME = "ParityTest"


def _sha256(file_path: Path) -> str:
    """Return the SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(manifest_path: Path = _MANIFEST_PATH) -> dict:
    """Load and return the parsed MANIFEST.json.

    Raises:
        FileNotFoundError: If the manifest does not exist.
        ValueError: If the manifest cannot be parsed as JSON.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"MANIFEST.json not found at {manifest_path}. "
            "Run scripts/generate_manifest.py to regenerate it."
        )
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse MANIFEST.json: {exc}") from exc


def get_security_critical_files(manifest: dict) -> list[str]:
    """Return a list of relative paths that are marked security_critical in the manifest."""
    return [
        rel_path
        for rel_path, entry in manifest.get("files", {}).items()
        if entry.get("security_critical", False)
    ]


def _ensure_src_on_path() -> None:
    """Add the repo src/ directory to sys.path so launcher modules can be imported."""
    src_dir = str(_REPO_ROOT / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)


def create_fresh_workspace(template_dir: Path, dest_root: Path) -> Path:
    """Create a fresh workspace by copying the template via shutil.copytree.

    Uses a direct tree copy rather than create_project() to avoid per-workspace
    post-copy modifications (write_counter_config, replace_template_placeholders)
    that would cause artificial parity failures unrelated to the upgrade path.

    Returns the path to the copied workspace root.
    """
    workspace = dest_root / "fresh_workspace"
    shutil.copytree(str(template_dir), str(workspace))
    return workspace


def create_upgraded_workspace(
    template_dir: Path,
    dest_root: Path,
    security_files: list[str],
) -> Path:
    """Simulate an upgrade path: copy template → corrupt security files → upgrade.

    Steps:
    1. Direct-copy the template (same baseline as create_fresh_workspace).
    2. Replace every security-critical file with a sentinel payload to simulate
       outdated content (as if the workspace was created with an older launcher).
    3. Run workspace_upgrader.upgrade_workspace() which restores all security files
       from the current template.

    Returns the path to the upgraded workspace root.

    Raises:
        RuntimeError: If the upgrader reports file-copy errors (not post-upgrade
            verification errors, which may occur when MANIFEST.json is stale).
    """
    _ensure_src_on_path()
    from launcher.core.workspace_upgrader import upgrade_workspace  # noqa: PLC0415

    workspace = dest_root / "upgraded_workspace"
    shutil.copytree(str(template_dir), str(workspace))

    # Overwrite every security-critical file with sentinel content so the upgrader
    # sees them as outdated and replaces them from the current template.
    for rel_path in security_files:
        target_file = workspace / rel_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_bytes(_OLD_CONTENT_SENTINEL)

    report = upgrade_workspace(workspace)
    # Filter out post-upgrade verification errors. These occur when MANIFEST.json
    # is stale (template file changed but manifest not regenerated). Our own byte-level
    # compare_workspaces() is the authoritative parity check, so we do not rely on
    # the upgrader's self-verification against potentially stale manifest hashes.
    copy_errors = [
        e for e in report.errors
        if "Post-upgrade verification" not in e
    ]
    if copy_errors:
        raise RuntimeError(
            f"upgrade_workspace() failed to copy files: {copy_errors}"
        )

    return workspace


def compare_workspaces(
    fresh_workspace: Path,
    upgraded_workspace: Path,
    security_files: list[str],
    verbose: bool = False,
) -> list[str]:
    """Compare security-critical files between fresh and upgraded workspaces.

    Returns a list of mismatch descriptions. Empty list means full parity.
    """
    mismatches: list[str] = []

    for rel_path in security_files:
        fresh_file = fresh_workspace / rel_path
        upgraded_file = upgraded_workspace / rel_path

        # Both missing — not a mismatch, but worth noting.
        if not fresh_file.exists() and not upgraded_file.exists():
            if verbose:
                print(f"  SKIP (absent in both): {rel_path}")
            continue

        if not fresh_file.exists():
            mismatches.append(f"MISSING in fresh workspace: {rel_path}")
            if verbose:
                print(f"  FAIL: {rel_path} — missing in fresh workspace")
            continue

        if not upgraded_file.exists():
            mismatches.append(f"MISSING in upgraded workspace: {rel_path}")
            if verbose:
                print(f"  FAIL: {rel_path} — missing in upgraded workspace")
            continue

        fresh_hash = _sha256(fresh_file)
        upgraded_hash = _sha256(upgraded_file)

        if fresh_hash != upgraded_hash:
            mismatches.append(
                f"HASH MISMATCH: {rel_path} "
                f"(fresh={fresh_hash[:12]}… upgraded={upgraded_hash[:12]}…)"
            )
            if verbose:
                print(f"  FAIL: {rel_path}")
                print(f"    fresh hash:    {fresh_hash}")
                print(f"    upgraded hash: {upgraded_hash}")
        else:
            if verbose:
                print(f"  OK:   {rel_path}")

    return mismatches


def verify_parity(verbose: bool = False) -> bool:
    """Run the full install-vs-upgrade parity check.

    Creates a fresh workspace and a simulated upgraded workspace in a temporary
    directory, then compares all security-critical files byte-by-byte.

    Returns:
        True if every security-critical file is identical, False otherwise.

    Raises:
        FileNotFoundError: If MANIFEST.json is missing.
        ValueError: If MANIFEST.json is invalid JSON.
        RuntimeError: If workspace creation or upgrade fails.
    """
    manifest = load_manifest()
    security_files = get_security_critical_files(manifest)

    if not security_files:
        print("WARNING: No security-critical files found in MANIFEST.json.")
        return True

    if verbose:
        print(f"Parity check: {len(security_files)} security-critical file(s) in MANIFEST.json")

    template_dir = _TEMPLATES_DIR / "agent-workbench"

    with tempfile.TemporaryDirectory(prefix="saf077_parity_") as tmpdir:
        tmp = Path(tmpdir)
        fresh_root = tmp / "fresh"
        upgrade_root = tmp / "upgrade"
        fresh_root.mkdir()
        upgrade_root.mkdir()

        if verbose:
            print("Creating fresh workspace...")
        fresh_workspace = create_fresh_workspace(template_dir, fresh_root)

        if verbose:
            print("Creating upgraded workspace (simulate outdated -> upgrade)...")
        upgraded_workspace = create_upgraded_workspace(
            template_dir, upgrade_root, security_files
        )

        if verbose:
            print("Comparing security-critical files...")
        mismatches = compare_workspaces(
            fresh_workspace, upgraded_workspace, security_files, verbose=verbose
        )

    if mismatches:
        print(f"\nParity check FAILED — {len(mismatches)} mismatch(es) detected:")
        for mismatch in mismatches:
            print(f"  {mismatch}")
        return False

    print(
        f"Parity check PASSED — all {len(security_files)} security-critical "
        "files are byte-identical between fresh install and upgrade paths."
    )
    return True


def verify_create_project_parity(verbose: bool = False) -> bool:
    """Run the create_project()-based parity check (FIX-129).

    Creates two workspaces from the agent-workbench template:
      A) via create_project() — the real user installation path
      B) via shutil.copytree() + upgrade_workspace() — the upgrade path

    Compares all security-critical files between A and B, accounting for
    expected divergences (_EXPECTED_DIVERGENCE_FILES and placeholder tokens).

    Files containing {{PROJECT_NAME}} tokens in the template are normalised
    before comparison: resolved values in workspace A are substituted back to
    the token so they can be compared to workspace B's raw template copies.

    Returns:
        True if every security-critical file matches (after normalisation), False otherwise.

    Raises:
        RuntimeError: If workspace creation or upgrade fails.
    """
    _ensure_src_on_path()
    from launcher.core.project_creator import create_project  # noqa: PLC0415

    manifest = load_manifest()
    security_files = get_security_critical_files(manifest)

    if not security_files:
        print("WARNING: No security-critical files found in MANIFEST.json.")
        return True

    if verbose:
        print(
            f"create_project parity check: {len(security_files)} security-critical "
            "file(s) to compare"
        )

    template_dir = _TEMPLATES_DIR / "agent-workbench"
    workspace_name = f"SAE-{_PARITY_TEST_PROJECT_NAME}"

    with tempfile.TemporaryDirectory(prefix="fix129_cp_parity_") as tmpdir:
        tmp = Path(tmpdir)
        cp_root = tmp / "create_project_dest"
        cp_root.mkdir()
        upgrade_root = tmp / "upgrade"
        upgrade_root.mkdir()

        if verbose:
            print("Creating workspace via create_project()...")
        cp_workspace = create_project(
            template_path=template_dir,
            destination=cp_root,
            folder_name=_PARITY_TEST_PROJECT_NAME,
        )

        if verbose:
            print("Creating upgraded workspace (raw copy + upgrade)...")
        upgraded_workspace = create_upgraded_workspace(
            template_dir, upgrade_root, security_files
        )

        if verbose:
            print("Comparing security-critical files (with normalisation)...")

        mismatches: list[str] = []
        skipped: list[str] = []

        for rel_path in security_files:
            # Skip files that are intentionally different in create_project() output.
            if rel_path in _EXPECTED_DIVERGENCE_FILES:
                if verbose:
                    print(f"  SKIP (expected divergence): {rel_path}")
                skipped.append(rel_path)
                continue

            cp_file = cp_workspace / rel_path
            upgraded_file = upgraded_workspace / rel_path

            if not cp_file.exists() and not upgraded_file.exists():
                if verbose:
                    print(f"  SKIP (absent in both): {rel_path}")
                continue

            if not cp_file.exists():
                mismatches.append(f"MISSING in create_project workspace: {rel_path}")
                if verbose:
                    print(f"  FAIL: {rel_path} — missing in create_project workspace")
                continue

            if not upgraded_file.exists():
                mismatches.append(f"MISSING in upgraded workspace: {rel_path}")
                if verbose:
                    print(f"  FAIL: {rel_path} — missing in upgraded workspace")
                continue

            # Normalise create_project() output by reversing placeholder substitution
            # so we can compare against the unresolved raw-copy in the upgraded workspace.
            # IMPORTANT: replace longer/compound tokens before shorter ones to avoid
            # partial substitution mangling (e.g. SAE-ParityTest before ParityTest).
            try:
                cp_text = cp_file.read_text(encoding="utf-8")
                upgraded_text = upgraded_file.read_text(encoding="utf-8")

                # Step 1: reverse SAE-ParityTest → {{WORKSPACE_NAME}} first.
                cp_normalised = cp_text.replace(
                    f"SAE-{_PARITY_TEST_PROJECT_NAME}", "{{WORKSPACE_NAME}}"
                )
                # Step 2: reverse ParityTest → {{PROJECT_NAME}}.
                cp_normalised = cp_normalised.replace(
                    _PARITY_TEST_PROJECT_NAME, "{{PROJECT_NAME}}"
                )

                if cp_normalised == upgraded_text:
                    if verbose:
                        print(f"  OK:   {rel_path}")
                    continue
            except (UnicodeDecodeError, OSError):
                # Binary file — compare byte hashes directly.
                pass

            # Fall back to direct byte-level hash comparison.
            cp_hash = _sha256(cp_file)
            upgraded_hash = _sha256(upgraded_file)

            if cp_hash != upgraded_hash:
                mismatches.append(
                    f"MISMATCH: {rel_path} "
                    f"(create_project={cp_hash[:12]}… upgraded={upgraded_hash[:12]}…)"
                )
                if verbose:
                    print(f"  FAIL: {rel_path}")
                    print(f"    create_project hash: {cp_hash}")
                    print(f"    upgraded hash:       {upgraded_hash}")
            else:
                if verbose:
                    print(f"  OK:   {rel_path}")

    if verbose and skipped:
        print(f"\nSkipped {len(skipped)} expected divergence file(s): {skipped}")

    if mismatches:
        print(
            f"\ncreate_project parity check FAILED — {len(mismatches)} unexpected "
            "mismatch(es):"
        )
        for mismatch in mismatches:
            print(f"  {mismatch}")
        return False

    checked = len(security_files) - len(skipped)
    print(
        f"create_project parity check PASSED — {checked} security-critical file(s) "
        f"match between create_project and upgrade paths "
        f"({len(skipped)} expected divergence(s) skipped)."
    )
    return True


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description=(
            "Verify that a fresh workspace and an upgraded workspace produce "
            "byte-identical security-critical files. "
            "Exit 0 on parity, exit 1 on any mismatch."
        )
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the comparison result for every file.",
    )
    args = parser.parse_args()

    try:
        copytree_passed = verify_parity(verbose=args.verbose)
        print()
        cp_passed = verify_create_project_parity(verbose=args.verbose)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0 if (copytree_passed and cp_passed) else 1)


if __name__ == "__main__":
    main()
