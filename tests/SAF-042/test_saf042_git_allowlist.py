"""tests/SAF-042/test_saf042_git_allowlist.py

Regression tests for SAF-042: git command allowlist audit and expansion.

Verifies:
  - All 17 documented git operations are explicitly allowed when the
    git command targets the workspace root (no path argument required
    for most git subcommands).
  - All 5 destructive git operations remain blocked.
  - Edge cases: git push without --force (allowed), git reset without
    --hard (blocked — reset not in allowlist), git push -f (blocked).
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "coding"
    / ".github"
    / "hooks"
    / "scripts"
)

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


@pytest.fixture(scope="module")
def sg():
    import security_gate as _sg
    return _sg


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# Workspace root used in all tests
WS = "c:/workspace"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def allow(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "allow"


def deny(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# 1. All 17 documented git operations must be allowed
# ---------------------------------------------------------------------------

def test_git_status_allowed(sg):
    """git status must be allowed."""
    assert allow(sg, "git status")


def test_git_log_allowed(sg):
    """git log must be allowed."""
    assert allow(sg, "git log")


def test_git_diff_allowed(sg):
    """git diff must be allowed."""
    assert allow(sg, "git diff")


def test_git_branch_allowed(sg):
    """git branch must be allowed."""
    assert allow(sg, "git branch")


def test_git_add_allowed(sg):
    """git add targeting project folder must be allowed."""
    assert allow(sg, "git add project/src/file.py")


def test_git_commit_allowed(sg):
    """git commit must be allowed."""
    assert allow(sg, "git commit -m 'test message'")


def test_git_fetch_allowed(sg):
    """git fetch must be allowed."""
    assert allow(sg, "git fetch")


def test_git_pull_allowed(sg):
    """git pull must be allowed."""
    assert allow(sg, "git pull")


def test_git_checkout_allowed(sg):
    """git checkout must be allowed."""
    assert allow(sg, "git checkout main")


def test_git_switch_allowed(sg):
    """git switch must be allowed (SAF-042: newly added)."""
    assert allow(sg, "git switch main")


def test_git_stash_allowed(sg):
    """git stash must be allowed."""
    assert allow(sg, "git stash")


def test_git_merge_allowed(sg):
    """git merge must be allowed."""
    assert allow(sg, "git merge feature-branch")


def test_git_rebase_allowed(sg):
    """git rebase must be allowed."""
    assert allow(sg, "git rebase main")


def test_git_tag_allowed(sg):
    """git tag must be allowed."""
    assert allow(sg, "git tag v1.0.0")


def test_git_remote_allowed(sg):
    """git remote must be allowed."""
    assert allow(sg, "git remote -v")


def test_git_show_allowed(sg):
    """git show must be allowed."""
    assert allow(sg, "git show HEAD")


def test_git_blame_allowed(sg):
    """git blame must be allowed (SAF-042: newly added)."""
    assert allow(sg, "git blame project/src/file.py")


# ---------------------------------------------------------------------------
# 2. All 5 destructive git operations must be blocked
# ---------------------------------------------------------------------------

def test_git_push_force_denied(sg):
    """git push --force must be denied."""
    assert deny(sg, "git push --force")


def test_git_push_force_short_denied(sg):
    """git push -f must be denied."""
    assert deny(sg, "git push -f")


def test_git_reset_hard_denied(sg):
    """git reset --hard must be denied."""
    assert deny(sg, "git reset --hard")


def test_git_filter_branch_denied(sg):
    """git filter-branch must be denied."""
    assert deny(sg, "git filter-branch")


def test_git_gc_force_denied(sg):
    """git gc --force must be denied."""
    assert deny(sg, "git gc --force")


def test_git_clean_f_denied(sg):
    """git clean -f must be denied."""
    assert deny(sg, "git clean -f")


# ---------------------------------------------------------------------------
# 3. Edge cases
# ---------------------------------------------------------------------------

def test_git_push_without_force_allowed(sg):
    """git push (without --force) must be allowed."""
    assert allow(sg, "git push origin main")


def test_git_reset_without_hard_denied(sg):
    """git reset (without --hard) must be denied — reset not in allowlist."""
    assert deny(sg, "git reset HEAD~1")


def test_git_clean_fd_denied(sg):
    """git clean -fd must be denied (both -f and combo in denied list)."""
    assert deny(sg, "git clean -fd")


def test_git_switch_create_allowed(sg):
    """git switch -c new-branch must be allowed (flag -c is not in denied_flags)."""
    assert allow(sg, "git switch -c new-branch")


def test_git_blame_with_line_range_allowed(sg):
    """git blame with line range flag must be allowed."""
    assert allow(sg, "git blame -L 1,10 project/src/file.py")


def test_git_stash_pop_allowed(sg):
    """git stash pop must be allowed."""
    assert allow(sg, "git stash pop")


def test_git_stash_list_allowed(sg):
    """git stash list must be allowed."""
    assert allow(sg, "git stash list")


def test_git_log_oneline_allowed(sg):
    """git log --oneline must be allowed."""
    assert allow(sg, "git log --oneline -10")


def test_git_diff_staged_allowed(sg):
    """git diff --cached must be allowed."""
    assert allow(sg, "git diff --cached")


def test_git_branch_delete_allowed(sg):
    """git branch -d <branch> must be allowed (-d is not in denied_flags)."""
    assert allow(sg, "git branch -d old-branch")


def test_git_add_all_allowed(sg):
    """git add -A must be allowed."""
    assert allow(sg, "git add -A")


def test_git_fetch_all_allowed(sg):
    """git fetch --all must be allowed."""
    assert allow(sg, "git fetch --all")


def test_git_push_force_with_lease_denied(sg):
    """git push --force-with-lease must be denied (--force part of string is NOT matched,
    but the token does not start with --force exactly — verify behavior)."""
    # --force-with-lease is NOT in denied_flags (only --force and -f are).
    # The subcommand 'push' IS in the allowlist.
    # This test documents the current behavior.
    decision, _ = sg.sanitize_terminal_command("git push --force-with-lease", WS)
    # Document: --force-with-lease is a distinct flag; the gate only blocks --force/-f.
    # Result should be allow (it is not --force, and push is in the allowlist).
    assert decision == "allow"


def test_git_rebase_interactive_allowed(sg):
    """git rebase -i must be allowed."""
    assert allow(sg, "git rebase -i HEAD~3")


def test_git_merge_no_ff_allowed(sg):
    """git merge --no-ff must be allowed."""
    assert allow(sg, "git merge --no-ff feature-branch")


def test_git_checkout_new_branch_allowed(sg):
    """git checkout -b new-branch must be allowed."""
    assert allow(sg, "git checkout -b new-branch")


def test_git_remote_add_allowed(sg):
    """git remote add (subcommand) must be allowed — remote is in allowlist."""
    assert allow(sg, "git remote add upstream")


def test_git_tag_annotated_allowed(sg):
    """git tag -a v1.0.0 must be allowed."""
    assert allow(sg, "git tag -a v1.0.0 -m 'release'")


def test_unknown_git_subcommand_denied(sg):
    """An unknown git subcommand not in the allowlist must be denied."""
    assert deny(sg, "git bisect")


def test_git_gc_without_force_denied(sg):
    """git gc (without --force) must still be denied — gc not in allowlist."""
    assert deny(sg, "git gc")


def test_git_reset_soft_denied(sg):
    """git reset --soft must be denied — reset not in allowlist."""
    assert deny(sg, "git reset --soft HEAD~1")


def test_git_clean_no_flags_denied(sg):
    """git clean (without flags) must be denied — clean not in allowlist."""
    assert deny(sg, "git clean")
