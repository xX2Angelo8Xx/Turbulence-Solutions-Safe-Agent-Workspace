"""SAF-006 Tester edge-case tests (Iteration 3).

Covers scenarios not present in the Developer's test file:
- find with filter expression arguments (find . -name "*.py")
- Recursive commands targeting safe safe (Project/) zones → ask
- ls BUG-022/BUG-023 regression: ls -lR / ls -R / gci -r targeting Project/
- dir BUG-024: dir /s with no explicit directory argument must deny
- dir /s /b (two Windows flags, no path) must deny
- Non-recursive dir Project/ → ask
- Path traversal: find ../../.github → deny
- tree / (filesystem root is ancestor of all deny zones) → deny
- Additional deny-zone specific: tree .vscode, find .vscode -type f
- Windows flags not treated as POSIX path-args for ancestor tests
"""
from __future__ import annotations

import os
import sys

import pytest

_SCRIPTS_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__),
    "..", "..",
    "templates", "coding", ".github", "hooks", "scripts",
))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

_WS_ROOT = "/workspace"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sanitize(command: str) -> tuple[str, str | None]:
    return sg.sanitize_terminal_command(command, _WS_ROOT)


def is_ask(command: str) -> bool:
    return sanitize(command)[0] in ("ask", "allow")


def is_deny(command: str) -> bool:
    return sanitize(command)[0] == "deny"


# ---------------------------------------------------------------------------
# find with filter expression arguments
# ---------------------------------------------------------------------------

def test_find_dot_with_name_filter_blocked():
    """find . -name '*.py' — '.' is workspace root, ancestor of deny zones, deny."""
    assert is_deny("find . -name '*.py'")


def test_find_project_with_name_filter_safe():
    """find Project/ -name '*.py' — Project/ not a deny-zone ancestor, ask."""
    assert is_ask(f"find {_WS_ROOT}/project -name '*.py'")


def test_find_vscode_with_type_filter_blocked():
    """find .vscode -type f — .vscode IS a deny zone, must deny."""
    assert is_deny("find .vscode -type f")


def test_find_traversal_to_github_blocked():
    """find ../../.github — path traversal resolved to .github zone, deny."""
    assert is_deny("find ../../.github")


# ---------------------------------------------------------------------------
# BUG-022 regression — ls -lR / ls -alR targeting Project/ must be ask
# ---------------------------------------------------------------------------

def test_ls_combined_lr_project_safe():
    """ls -lR Project/ — combined flag with safe target → ask (BUG-022 regression)."""
    assert is_ask(f"ls -lR {_WS_ROOT}/project")


def test_ls_combined_alr_project_safe():
    """ls -alR Project/ — three-char combined flag with safe target → ask."""
    assert is_ask(f"ls -alR {_WS_ROOT}/project")


# ---------------------------------------------------------------------------
# BUG-023 regression — ls -R / gci -r targeting Project/ must be ask
# ---------------------------------------------------------------------------

def test_ls_r_project_safe():
    """ls -R Project/ — recursive flag but safe target → ask (BUG-023 regression)."""
    assert is_ask(f"ls -R {_WS_ROOT}/project")


def test_gci_r_project_safe():
    """gci -r Project/ — recursive flag but safe target → ask (BUG-023 regression)."""
    assert is_ask(f"gci -r {_WS_ROOT}/project")


def test_ls_recursive_long_project_safe():
    """ls --recursive Project/ — long-form recursive flag with safe target → ask."""
    assert is_ask(f"ls --recursive {_WS_ROOT}/project")


# ---------------------------------------------------------------------------
# dir with recursive flag — safe path
# ---------------------------------------------------------------------------

def test_dir_slash_s_project_safe():
    """dir /s Project/ — recursive flag with non-deny target → ask."""
    assert is_ask(f"dir /s {_WS_ROOT}/project")


def test_dir_no_s_project_safe():
    """dir Project/ (no /s) — non-recursive listing → ask."""
    assert is_ask(f"dir {_WS_ROOT}/project")


# ---------------------------------------------------------------------------
# BUG-024: dir /s with no explicit directory argument must deny
# (Windows-style /flags must not be collected as path arguments in Step 7)
# ---------------------------------------------------------------------------

def test_dir_slash_s_no_path_blocked():
    """dir /s with no path defaults to cwd (workspace root) — must deny.

    BUG-024: Windows-style /flags are incorrectly collected as path arguments
    in Step 7, preventing the no-argument fallback to '.' (workspace root).
    Without the fallback, _is_ancestor_of_deny_zone('/s', ...) returns False
    and the command incorrectly passes as 'ask' instead of 'deny'.
    """
    assert is_deny("dir /s")


def test_dir_slash_s_slash_b_no_path_blocked():
    """dir /s /b with two Windows flags and no path must deny.

    Same root cause as BUG-024: both /s and /b collected as path args,
    neither is a deny-zone ancestor, and the cwd fallback is never applied.
    """
    assert is_deny("dir /s /b")


# ---------------------------------------------------------------------------
# Additional deny-zone specific scenarios
# ---------------------------------------------------------------------------

def test_tree_vscode_blocked():
    """tree .vscode — targeting a deny zone directly → deny."""
    assert is_deny("tree .vscode")


def test_tree_root_slash_blocked():
    """tree / — filesystem root is ancestor of every deny zone → deny."""
    assert is_deny("tree /")


def test_find_absolute_workspace_root_blocked():
    """find /workspace — absolute workspace root is ancestor of deny zones → deny."""
    assert is_deny(f"find {_WS_ROOT}")


def test_ls_r_vscode_blocked():
    """ls -r .vscode — recursive listing of vscode deny zone → deny."""
    assert is_deny("ls -r .vscode")


def test_get_childitem_recurse_path_github_blocked():
    """Get-ChildItem -Recurse -Path .github — explicit -Path flag on deny zone → deny."""
    assert is_deny("Get-ChildItem -Recurse -Path .github")


def test_gci_recurse_noagentzone_blocked():
    """gci -recurse targeting NoAgentZone/ → deny."""
    assert is_deny("gci -recurse NoAgentZone")
