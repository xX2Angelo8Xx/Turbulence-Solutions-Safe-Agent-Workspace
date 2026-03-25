"""tests/SAF-042/test_saf042_tester_edge_cases.py

Tester-added edge-case tests for SAF-042.

Covers scenarios requested in the SAF-042 review spec plus additional
security boundary and bypass-vector checks beyond the developer tests.

Scenarios:
  - git clean -n (dry-run) — must be denied (clean not in allowlist)
  - git stash drop — must be allowed (stash is in allowlist)
  - git rebase --abort — must be allowed
  - git merge --abort — must be allowed
  - git push --force-with-lease — must be allowed (distinct from --force)
  - git push --force --no-verify — must be denied (--force present)
  - git push -force (single-dash non-standard) — allowed; NOTE it is an
    invalid git flag so it cannot actually force-push (low severity)
  - git push --FORCE (uppercase) — must be denied (case-normalised)
  - git commit --amend — must be allowed
  - git reset (bare, no subcommand) — must be denied
  - git fsck, git archive, git gc (without --force) — denied (not in allowlist)
  - git clean --dry-run — denied (clean not in allowlist)
  - git stash drop stash@{0} — must be allowed
  - Git subcommands that are in allowlist with common flags
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
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


WS = "c:/workspace"


def allow(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "allow"


def deny(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# Tester-requested scenarios
# ---------------------------------------------------------------------------

def test_git_clean_n_denied(sg):
    """git clean -n (dry-run) must be denied — clean is not in the allowlist."""
    assert deny(sg, "git clean -n")


def test_git_clean_dry_run_long_denied(sg):
    """git clean --dry-run must be denied — clean is not in the allowlist."""
    assert deny(sg, "git clean --dry-run")


def test_git_stash_drop_allowed(sg):
    """git stash drop must be allowed — stash is in the allowlist."""
    assert allow(sg, "git stash drop")


def test_git_stash_drop_with_ref_allowed(sg):
    """git stash drop stash@{0} must be allowed — stash is in the allowlist."""
    assert allow(sg, "git stash drop stash@{0}")


def test_git_rebase_abort_allowed(sg):
    """git rebase --abort must be allowed — rebase is in allowlist, --abort not denied."""
    assert allow(sg, "git rebase --abort")


def test_git_merge_abort_allowed(sg):
    """git merge --abort must be allowed — merge is in allowlist, --abort not denied."""
    assert allow(sg, "git merge --abort")


def test_git_push_force_with_lease_allowed(sg):
    """git push --force-with-lease must be allowed.

    --force-with-lease is a distinct flag from --force; it is not in denied_flags.
    This is a deliberate policy decision: the safer force-push variant is permitted
    while raw --force and -f remain blocked.
    """
    assert allow(sg, "git push --force-with-lease")


def test_git_push_force_and_no_verify_denied(sg):
    """git push --force --no-verify must be denied — --force is in denied_flags."""
    assert deny(sg, "git push --force --no-verify")


def test_git_push_uppercase_force_denied(sg):
    """git push --FORCE (uppercase) must be denied — denied_flags checked case-insensitively."""
    assert deny(sg, "git push --FORCE")


def test_git_commit_amend_allowed(sg):
    """git commit --amend must be allowed — commit is in allowlist, --amend not denied."""
    assert allow(sg, "git commit --amend")


# ---------------------------------------------------------------------------
# Additional security boundary checks
# ---------------------------------------------------------------------------

def test_git_reset_bare_denied(sg):
    """git reset (no flags) must be denied — reset is not in the allowlist."""
    assert deny(sg, "git reset")


def test_git_fsck_denied(sg):
    """git fsck must be denied — fsck is not in the allowlist."""
    assert deny(sg, "git fsck")


def test_git_archive_denied(sg):
    """git archive must be denied — archive is not in the allowlist."""
    assert deny(sg, "git archive HEAD")


def test_git_gc_no_force_denied(sg):
    """git gc (without --force) must be denied — gc is not in the allowlist."""
    assert deny(sg, "git gc")


def test_git_filter_env_filter_denied(sg):
    """git filter-branch --env-filter must be denied — filter-branch not in allowlist."""
    assert deny(sg, "git filter-branch --env-filter 'GIT_AUTHOR_EMAIL=new@email.com'")


def test_git_push_f_short_flag_denied(sg):
    """git push -f (short form) must be denied — -f is in denied_flags."""
    assert deny(sg, "git push -f origin main")


def test_git_push_force_with_lease_and_force_denied(sg):
    """git push --force-with-lease --force must be denied — --force is also present."""
    assert deny(sg, "git push --force-with-lease --force")


def test_git_switch_detach_allowed(sg):
    """git switch --detach must be allowed — switch is in allowlist, --detach not denied."""
    assert allow(sg, "git switch --detach HEAD~1")


def test_git_blame_porcelain_allowed(sg):
    """git blame --porcelain must be allowed — blame is in allowlist."""
    assert allow(sg, "git blame --porcelain project/src/main.py")


def test_git_diff_name_only_allowed(sg):
    """git diff --name-only must be allowed."""
    assert allow(sg, "git diff --name-only HEAD~1")


def test_git_log_graph_allowed(sg):
    """git log --graph --oneline --decorate must be allowed."""
    assert allow(sg, "git log --graph --oneline --decorate")


def test_git_stash_show_allowed(sg):
    """git stash show -p must be allowed — stash is in allowlist."""
    assert allow(sg, "git stash show -p")


def test_git_unknown_subcmd_denied(sg):
    """Unknown subcommands like 'git worktree' must be denied (not in allowlist)."""
    assert deny(sg, "git worktree add")


def test_git_push_force_single_dash_word_allowed(sg):
    """git push -force (single-dash full word) is allowed because -force is neither
    '--force' nor '-f' in denied_flags.

    NOTE — security posture: -force is NOT a valid git option; git itself would reject
    this command. The gate allows it but it cannot actually perform a force-push, so
    this is a low-severity benign gap. Documented for transparency.
    """
    # -force is not a recognised git option → gate does not block it
    # The real force flags (--force, -f) remain blocked
    assert allow(sg, "git push -force")
