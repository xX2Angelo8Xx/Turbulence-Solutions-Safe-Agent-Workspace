"""Release script: bumps all 5 version files, creates a git commit and annotated tag, then pushes."""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Absolute paths resolved from the repo root (parent of this script's directory).
_REPO_ROOT = Path(__file__).resolve().parent.parent

VERSION_FILES = {
    "config_py": _REPO_ROOT / "src" / "launcher" / "config.py",
    "pyproject_toml": _REPO_ROOT / "pyproject.toml",
    "setup_iss": _REPO_ROOT / "src" / "installer" / "windows" / "setup.iss",
    "build_dmg_sh": _REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh",
    "build_appimage_sh": _REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh",
}

# Regex patterns for locating and replacing each version string.
# Each entry: (search_pattern, replacement_template)
_FILE_PATTERNS = {
    "config_py": (
        r'(VERSION\s*:\s*str\s*=\s*")[^"]+(")',
        r'\g<1>{version}\g<2>',
    ),
    "pyproject_toml": (
        r'(^version\s*=\s*")[^"]+(")',
        r'\g<1>{version}\g<2>',
    ),
    "setup_iss": (
        r'(#define\s+MyAppVersion\s+")[^"]+(")',
        r'\g<1>{version}\g<2>',
    ),
    "build_dmg_sh": (
        r'(^APP_VERSION=")[^"]+(")',
        r'\g<1>{version}\g<2>',
    ),
    "build_appimage_sh": (
        r'(^APP_VERSION=")[^"]+(")',
        r'\g<1>{version}\g<2>',
    ),
}

SEMVER_RE = re.compile(r'^\d+\.\d+\.\d+$')


def validate_version(version: str) -> bool:
    """Return True if version matches X.Y.Z semver format."""
    return bool(SEMVER_RE.match(version))


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run a git command and return the result. Raises RuntimeError on non-zero exit."""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed (exit {result.returncode}):\n{result.stderr.strip()}"
        )
    return result


def check_on_main_branch(repo_root: Path) -> None:
    """Abort if the current branch is not main."""
    result = _run_git(["branch", "--show-current"], repo_root)
    branch = result.stdout.strip()
    if branch != "main":
        print(f"[ABORT] Current branch is '{branch}'. Release must be run from 'main'.")
        sys.exit(1)


def check_clean_working_tree(repo_root: Path) -> None:
    """Abort if there are uncommitted changes in the working tree."""
    result = _run_git(["status", "--porcelain"], repo_root)
    if result.stdout.strip():
        print("[ABORT] Working tree is not clean. Commit or stash changes before releasing.")
        print(result.stdout.strip())
        sys.exit(1)


def update_file(key: str, new_version: str, dry_run: bool) -> bool:
    """
    Update the version string in the file identified by key.
    Returns True if the pattern was found and (in non-dry-run mode) the file was written.
    """
    file_path = VERSION_FILES[key]
    search_pattern, replacement_template = _FILE_PATTERNS[key]
    replacement = replacement_template.replace("{version}", new_version)

    original = file_path.read_text(encoding="utf-8")
    # Use MULTILINE so ^ matches line starts for pyproject.toml / shell scripts.
    updated, count = re.subn(search_pattern, replacement, original, flags=re.MULTILINE)

    if count == 0:
        print(f"  [FAIL]  Pattern not found in {file_path.name}")
        return False

    if dry_run:
        print(f"  [DRY]   Would update {file_path.name}")
        return True

    file_path.write_text(updated, encoding="utf-8")
    print(f"  [OK]    Updated {file_path.name}")
    return True


def validate_version_file(key: str, expected_version: str) -> bool:
    """Read the file back from disk and confirm expected_version is present."""
    file_path = VERSION_FILES[key]
    content = file_path.read_text(encoding="utf-8")
    return expected_version in content


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bump all version files, commit, tag, and push a new release."
    )
    parser.add_argument("version", help="New version string in X.Y.Z format (e.g. 3.2.7)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making any changes.",
    )
    parser.add_argument(
        "--rc",
        action="store_true",
        help="Create a release candidate. Reminds you that the GitHub Release will be a draft.",
    )
    args = parser.parse_args()

    version = args.version
    dry_run = args.dry_run

    # --- Validate version format ---
    if not validate_version(version):
        print(f"[ERROR] Invalid version '{version}'. Expected format: X.Y.Z (e.g. 3.2.7)")
        sys.exit(1)

    tag = f"v{version}"
    print(f"{'[DRY-RUN] ' if dry_run else ''}Release {tag}")
    print()

    repo_root = _REPO_ROOT

    # --- Pre-flight checks (skip in dry-run so the script can be tested off main) ---
    if not dry_run:
        print("Checking branch...")
        check_on_main_branch(repo_root)
        print("  [OK]    On main branch.")

        print("Checking working tree...")
        check_clean_working_tree(repo_root)
        print("  [OK]    Working tree is clean.")
        print()

    # --- Update all 5 version files ---
    print("Updating version files...")
    for key in VERSION_FILES:
        success = update_file(key, version, dry_run)
        if not success:
            print(f"[ABORT] Failed to update '{key}'. No changes have been committed.")
            sys.exit(1)

    # --- Validate (read-back) each file ---
    if not dry_run:
        print()
        print("Validating version files...")
        for key in VERSION_FILES:
            if not validate_version_file(key, version):
                print(f"[ABORT] Validation failed: '{key}' does not contain '{version}' after update.")
                sys.exit(1)
            print(f"  [OK]    Verified {VERSION_FILES[key].name}")

    print()

    if dry_run:
        print(f"[DRY-RUN] Would create git commit: 'release: bump version to {tag}'")
        print(f"[DRY-RUN] Would create annotated tag: '{tag}' with message 'Release {tag}'")
        print(f"[DRY-RUN] Would push commit and tag to origin.")
        print()
        print("[DRY-RUN] No changes were made.")
        return

    # --- Git: stage all 5 version files ---
    print("Staging version files...")
    files_to_stage = [str(p.relative_to(repo_root)) for p in VERSION_FILES.values()]
    _run_git(["add"] + files_to_stage, repo_root)
    print("  [OK]    Files staged.")

    # --- Git: commit ---
    commit_message = f"release: bump version to {tag}"
    print(f"Creating commit: '{commit_message}'...")
    try:
        _run_git(["commit", "-m", commit_message], repo_root)
    except RuntimeError as exc:
        print(f"[ABORT] Commit failed: {exc}")
        sys.exit(1)
    print("  [OK]    Commit created.")

    # --- Git: annotated tag ---
    tag_message = f"Release {tag}"
    print(f"Creating annotated tag '{tag}'...")
    try:
        _run_git(["tag", "-a", tag, "-m", tag_message], repo_root)
    except RuntimeError as exc:
        print(f"[ABORT] Tag creation failed: {exc}")
        sys.exit(1)
    print("  [OK]    Tag created.")

    # --- Git: push commit ---
    print("Pushing commit to origin...")
    try:
        _run_git(["push", "origin", "main"], repo_root)
    except RuntimeError as exc:
        print(f"[ABORT] Push failed: {exc}")
        sys.exit(1)
    print("  [OK]    Commit pushed.")

    # --- Git: push tag ---
    print(f"Pushing tag {tag} to origin...")
    try:
        _run_git(["push", "origin", tag], repo_root)
    except RuntimeError as exc:
        print(f"[ABORT] Tag push failed: {exc}")
        sys.exit(1)
    print("  [OK]    Tag pushed.")

    print()
    print(f"Release {tag} complete.")

    if args.rc:
        print()
        print("=" * 60)
        print("RELEASE CANDIDATE — Draft Release Workflow")
        print("=" * 60)
        print(f"1. CI/CD will build artifacts and create a DRAFT release for {tag}")
        print("2. Draft releases are NOT visible to the auto-updater")
        print("3. Run staging smoke tests: Actions → 'Staging Smoke Tests' → Run workflow")
        print("4. Download and test artifacts manually on your machine")
        print("5. When satisfied, publish the draft on GitHub Releases page")
        print("=" * 60)
    else:
        print()
        print("NOTE: GitHub Release will be created as a DRAFT.")
        print("You must manually publish it on the GitHub Releases page")
        print("after verifying staging smoke tests pass.")


if __name__ == "__main__":
    main()
