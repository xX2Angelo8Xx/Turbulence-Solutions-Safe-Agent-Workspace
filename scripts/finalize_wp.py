#!/usr/bin/env python3
"""Finalize a Done workpackage: merge, branch cleanup, status cascades, architecture sync.

This script replaces the multi-step manual Post-Done Finalization in agent-workflow.md
with a single command. It handles all WP types (feature, Enabler, bug fix).

Usage:
    .venv/Scripts/python scripts/finalize_wp.py GUI-001
    .venv/Scripts/python scripts/finalize_wp.py GUI-001 --dry-run
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from csv_utils import REPO_ROOT, FileLock, read_csv, update_cell, write_csv

WP_CSV = REPO_ROOT / "docs" / "workpackages" / "workpackages.csv"
US_CSV = REPO_ROOT / "docs" / "user-stories" / "user-stories.csv"
BUG_CSV = REPO_ROOT / "docs" / "bugs" / "bugs.csv"

CANONICAL_ORIGIN = (
    "https://github.com/xX2Angelo8Xx/"
    "Turbulence-Solutions-Safe-Agent-Workspace.git"
)


def _run_git(args: list[str], dry_run: bool, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command, or print it in dry-run mode."""
    cmd = ["git"] + args
    if dry_run:
        print(f"  [DRY RUN] {' '.join(cmd)}")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    return subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), check=check,
    )


def _get_current_branch() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    return result.stdout.strip()


def _verify_remote_origin(dry_run: bool) -> None:
    """Verify git remote origin matches the canonical URL.

    Auto-corrects if mismatched. This is a non-negotiable safety check
    from copilot-instructions.md and commit-branch-rules.md.
    """
    if dry_run:
        print("  [DRY RUN] Verify remote origin URL")
        return
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    current_url = result.stdout.strip()
    if current_url != CANONICAL_ORIGIN:
        print(f"  WARNING: Remote origin mismatch!")
        print(f"    Current:  {current_url}")
        print(f"    Expected: {CANONICAL_ORIGIN}")
        subprocess.run(
            ["git", "remote", "set-url", "origin", CANONICAL_ORIGIN],
            capture_output=True, text=True, cwd=str(REPO_ROOT), check=True,
        )
        print(f"  Auto-corrected remote origin to canonical URL.")
    else:
        print(f"  Remote origin verified ✓")


def _state_path(wp_id: str) -> Path:
    """Return the path to the finalization state file for a WP."""
    return REPO_ROOT / "docs" / "workpackages" / wp_id / ".finalization-state.json"


def _load_state(wp_id: str) -> dict:
    """Load finalization state, or return empty state if none exists."""
    path = _state_path(wp_id)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_state(wp_id: str, state: dict) -> None:
    """Persist finalization state to disk."""
    path = _state_path(wp_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _clear_state(wp_id: str) -> None:
    """Remove the finalization state file on successful completion."""
    path = _state_path(wp_id)
    if path.exists():
        path.unlink()


def _validate_wp(wp_id: str) -> None:
    """Run validate_workspace.py --wp and abort on errors."""
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_workspace.py"), "--wp", wp_id],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print(f"Validation failed for {wp_id}:")
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        sys.exit(1)


def _cascade_us_status(wp_id: str, dry_run: bool) -> None:
    """If all linked WPs for the parent US are Done, set US to Done."""
    _, wp_rows = read_csv(WP_CSV)
    wp_row = next((r for r in wp_rows if r["ID"] == wp_id), None)
    if not wp_row:
        return

    us_id = wp_row.get("User Story", "").strip()
    if not us_id or us_id == "Enabler":
        print(f"  Skip US cascade: {wp_id} is an Enabler WP")
        return

    wp_status_map = {r["ID"]: r["Status"] for r in wp_rows}

    _, us_rows = read_csv(US_CSV)
    for us in us_rows:
        if us["ID"] != us_id:
            continue
        if us.get("Status") in ("Done", "Closed"):
            print(f"  Skip US cascade: {us_id} already {us['Status']}")
            return

        linked_raw = us.get("Linked WPs", "").strip()
        linked_wps = [w.strip() for w in linked_raw.split(",") if w.strip()]
        if not linked_wps:
            return

        all_done = all(wp_status_map.get(wp) == "Done" for wp in linked_wps)
        if all_done:
            if dry_run:
                print(f"  [DRY RUN] Set {us_id} status to Done (all {len(linked_wps)} WPs done)")
            else:
                update_cell(US_CSV, "ID", us_id, "Status", "Done")
                print(f"  Set {us_id} status to Done")
        else:
            pending = [wp for wp in linked_wps if wp_status_map.get(wp) != "Done"]
            print(f"  Skip US cascade: {us_id} has pending WPs: {', '.join(pending)}")
        return

    print(f"  Warning: User Story {us_id} not found in user-stories.csv")


def _cascade_bug_status(wp_id: str, dry_run: bool) -> None:
    """Close any Open bugs whose Fixed In WP matches this WP."""
    _, bug_rows = read_csv(BUG_CSV)
    for bug in bug_rows:
        fixed_wp = bug.get("Fixed In WP", "").strip()
        if fixed_wp == wp_id and bug.get("Status") == "Open":
            bug_id = bug["ID"]
            if dry_run:
                print(f"  [DRY RUN] Close {bug_id} (fixed by {wp_id})")
            else:
                update_cell(BUG_CSV, "ID", bug_id, "Status", "Closed")
                print(f"  Closed {bug_id} (fixed by {wp_id})")


def _sync_architecture(dry_run: bool) -> None:
    """Run update_architecture.py to sync docs/architecture.md."""
    script = REPO_ROOT / "scripts" / "update_architecture.py"
    if not script.exists():
        print("  Warning: scripts/update_architecture.py not found, skipping")
        return
    if dry_run:
        print(f"  [DRY RUN] Run update_architecture.py")
        return
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    if result.returncode == 0:
        print(f"  Architecture sync: {result.stdout.strip()}")
    else:
        print(f"  Warning: architecture sync failed: {result.stderr.strip()}")


def _verify_no_stale_branches(dry_run: bool) -> None:
    """Check for stale merged branches on remote."""
    if dry_run:
        print("  [DRY RUN] Check for stale merged remote branches")
        return
    result = subprocess.run(
        ["git", "branch", "-r", "--merged", "main"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    for line in result.stdout.strip().splitlines():
        branch = line.strip()
        if branch and "origin/main" not in branch and "origin/HEAD" not in branch:
            print(f"  Warning: stale merged branch found: {branch}")


def finalize(wp_id: str, dry_run: bool) -> int:
    mode = "[DRY RUN] " if dry_run else ""
    print(f"\n{mode}Finalizing {wp_id}...")
    state = {} if dry_run else _load_state(wp_id)
    if state:
        print(f"  Resuming from previous state (completed: {[k for k, v in state.items() if v]})")

    # Step 0: Verify remote origin URL
    print(f"\n--- Step 0: Verify remote origin ---")
    _verify_remote_origin(dry_run)

    # Step 1: Read WP row, confirm Done
    print(f"\n--- Step 1: Verify WP status ---")
    _, wp_rows = read_csv(WP_CSV)
    wp_row = next((r for r in wp_rows if r["ID"] == wp_id), None)
    if not wp_row:
        print(f"Error: {wp_id} not found in workpackages.csv")
        return 1
    if wp_row["Status"] != "Done":
        print(f"Error: {wp_id} status is '{wp_row['Status']}', expected 'Done'")
        return 1
    print(f"  {wp_id} is Done ✓")

    # Step 2: Detect feature branch
    print(f"\n--- Step 2: Detect branch ---")
    current_branch = _get_current_branch()
    if current_branch == "main":
        # Already on main — maybe finalization is being run after manual merge
        print(f"  Already on main — skipping merge and branch delete steps")
        branch_name = None
    else:
        branch_name = current_branch
        print(f"  Current branch: {branch_name}")

    # Step 3: Validate workspace
    if not state.get("validated"):
        print(f"\n--- Step 3: Validate workspace ---")
        if not dry_run:
            _validate_wp(wp_id)
            print(f"  Validation passed ✓")
            state["validated"] = True
            _save_state(wp_id, state)
        else:
            print(f"  [DRY RUN] Run validate_workspace.py --wp {wp_id}")
    else:
        print(f"\n--- Step 3: Validate workspace (already done) ---")

    # Steps 4-5: Merge to main
    if branch_name and not state.get("merged"):
        print(f"\n--- Step 4: Merge to main ---")
        _run_git(["checkout", "main"], dry_run)
        _run_git(["merge", branch_name, "--no-edit"], dry_run)
        _run_git(["push", "origin", "main"], dry_run)
        if not dry_run:
            print(f"  Merged {branch_name} into main and pushed ✓")
            state["merged"] = True
            _save_state(wp_id, state)
    elif branch_name:
        print(f"\n--- Step 4: Merge to main (already done) ---")

    # Steps 6-7: Delete feature branch
    if branch_name and not state.get("branch_deleted"):
        print(f"\n--- Step 5: Delete feature branch ---")
        _run_git(["branch", "-d", branch_name], dry_run, check=False)
        _run_git(["push", "origin", "--delete", branch_name], dry_run, check=False)
        if not dry_run:
            print(f"  Deleted branch {branch_name} (local + remote) ✓")
            state["branch_deleted"] = True
            _save_state(wp_id, state)
    elif branch_name:
        print(f"\n--- Step 5: Delete feature branch (already done) ---")

    # Step 8: Cascade US status
    if not state.get("us_cascaded"):
        print(f"\n--- Step 6: Cascade User Story status ---")
        _cascade_us_status(wp_id, dry_run)
        if not dry_run:
            state["us_cascaded"] = True
            _save_state(wp_id, state)
    else:
        print(f"\n--- Step 6: Cascade User Story status (already done) ---")

    # Step 9: Cascade Bug status
    if not state.get("bug_cascaded"):
        print(f"\n--- Step 7: Cascade Bug status ---")
        _cascade_bug_status(wp_id, dry_run)
        if not dry_run:
            state["bug_cascaded"] = True
            _save_state(wp_id, state)
    else:
        print(f"\n--- Step 7: Cascade Bug status (already done) ---")

    # Step 10: Architecture sync
    if not state.get("arch_synced"):
        print(f"\n--- Step 8: Architecture sync ---")
        _sync_architecture(dry_run)
        if not dry_run:
            state["arch_synced"] = True
            _save_state(wp_id, state)
    else:
        print(f"\n--- Step 8: Architecture sync (already done) ---")

    # Step 11: Commit cascade changes
    if not state.get("cascade_committed"):
        print(f"\n--- Step 9: Commit cascade changes ---")
        if not dry_run:
            # Check if there are changes to commit
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=str(REPO_ROOT),
            )
            if status.stdout.strip():
                _run_git(["add", "-A"], dry_run)
                _run_git(["commit", "-m", f"{wp_id}: finalize (cascade + cleanup)"], dry_run)
                _run_git(["push", "origin", "main"], dry_run)
                print(f"  Committed and pushed cascade changes ✓")
            else:
                print(f"  No cascade changes to commit")
            state["cascade_committed"] = True
            _save_state(wp_id, state)
        else:
            print(f"  [DRY RUN] git add -A && git commit && git push (if changes exist)")
    else:
        print(f"\n--- Step 9: Commit cascade changes (already done) ---")

    # Step 12: Verify no stale branches
    print(f"\n--- Step 10: Verify no stale branches ---")
    _verify_no_stale_branches(dry_run)

    # Clean up state file on success
    if not dry_run:
        _clear_state(wp_id)

    print(f"\n{'='*60}")
    print(f"{mode}Finalization of {wp_id} complete.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Finalize a Done workpackage: merge, cleanup, cascades, sync."
    )
    parser.add_argument("wp_id", help="Workpackage ID (e.g. GUI-001)")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be done without executing"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Discard any saved finalization state and restart from scratch"
    )

    args = parser.parse_args()
    if args.reset:
        _clear_state(args.wp_id)
        print(f"Cleared finalization state for {args.wp_id}")
    return finalize(args.wp_id, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
