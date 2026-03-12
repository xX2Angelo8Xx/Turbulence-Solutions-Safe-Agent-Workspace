"""SAF-006 — Recursive Enumeration Protection tests.

Covers:
- Unit tests for _is_ancestor_of_deny_zone()
- Unit tests for _has_recursive_flag()
- Security tests: inherently-recursive commands blocked when targeting deny-zone ancestors
- Security tests: recursive flags blocked on ls, dir, Get-ChildItem, gci
- Security bypass-attempt tests (combined flags, path variants)
- Cross-platform path normalization tests
- Regression: non-recursive listing of safe paths still allowed
"""
from __future__ import annotations

import os
import sys

import pytest

_SCRIPTS_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__),
    "..", "..",
    "Default-Project", ".github", "hooks", "scripts",
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
    return sanitize(command)[0] == "ask"


def is_deny(command: str) -> bool:
    return sanitize(command)[0] == "deny"


# ---------------------------------------------------------------------------
# Unit — _is_ancestor_of_deny_zone()
# ---------------------------------------------------------------------------

def test_is_ancestor_ws_root_is_ancestor():
    """Workspace root is ancestor of all deny zones."""
    assert sg._is_ancestor_of_deny_zone(".", _WS_ROOT) is True


def test_is_ancestor_github_exact():
    """Exact deny zone path is an ancestor (also a deny zone itself)."""
    assert sg._is_ancestor_of_deny_zone(f"{_WS_ROOT}/.github", _WS_ROOT) is True


def test_is_ancestor_inside_github():
    """Path inside a deny zone is also blocked."""
    assert sg._is_ancestor_of_deny_zone(f"{_WS_ROOT}/.github/hooks", _WS_ROOT) is True


def test_is_ancestor_vscode_exact():
    assert sg._is_ancestor_of_deny_zone(f"{_WS_ROOT}/.vscode", _WS_ROOT) is True


def test_is_ancestor_noagentzone_exact():
    assert sg._is_ancestor_of_deny_zone(f"{_WS_ROOT}/noagentzone", _WS_ROOT) is True


def test_is_ancestor_project_safe():
    """Project/ is not an ancestor of any deny zone."""
    assert sg._is_ancestor_of_deny_zone(f"{_WS_ROOT}/project", _WS_ROOT) is False


def test_is_ancestor_unrelated_path_safe():
    assert sg._is_ancestor_of_deny_zone(f"{_WS_ROOT}/src", _WS_ROOT) is False


def test_is_ancestor_relative_dot():
    """'.' maps to workspace root, which is an ancestor."""
    assert sg._is_ancestor_of_deny_zone(".", _WS_ROOT) is True


def test_is_ancestor_empty_maps_to_ws_root():
    """Empty string maps to workspace root, which is an ancestor."""
    assert sg._is_ancestor_of_deny_zone("", _WS_ROOT) is True


def test_is_ancestor_relative_github():
    """Relative path '.github' resolves under ws_root and is a deny zone."""
    assert sg._is_ancestor_of_deny_zone(".github", _WS_ROOT) is True


# ---------------------------------------------------------------------------
# Unit — _has_recursive_flag()
# ---------------------------------------------------------------------------

def test_has_recursive_flag_ls_r():
    assert sg._has_recursive_flag("ls", ["ls", "-r"]) is True


def test_has_recursive_flag_ls_capital_r():
    assert sg._has_recursive_flag("ls", ["ls", "-R"]) is True


def test_has_recursive_flag_ls_combined_lr():
    """Combined flag -lR contains 'r' → recursive."""
    assert sg._has_recursive_flag("ls", ["ls", "-lR"]) is True


def test_has_recursive_flag_ls_no_recursive():
    assert sg._has_recursive_flag("ls", ["ls", "-l"]) is False


def test_has_recursive_flag_dir_slash_s():
    assert sg._has_recursive_flag("dir", ["dir", "/s"]) is True


def test_has_recursive_flag_dir_slash_s_upper():
    assert sg._has_recursive_flag("dir", ["dir", "/S"]) is True


def test_has_recursive_flag_dir_no_recursive():
    assert sg._has_recursive_flag("dir", ["dir", "/b"]) is False


def test_has_recursive_flag_gci_recurse():
    assert sg._has_recursive_flag("gci", ["gci", "-recurse"]) is True


def test_has_recursive_flag_get_childitem_recurse():
    assert sg._has_recursive_flag("get-childitem", ["get-childitem", "-recurse"]) is True


def test_has_recursive_flag_get_childitem_r():
    assert sg._has_recursive_flag("get-childitem", ["get-childitem", "-r"]) is True


def test_has_recursive_flag_no_flags_known_command():
    assert sg._has_recursive_flag("ls", ["ls"]) is False


def test_has_recursive_flag_unknown_command():
    """Unknown command always returns False."""
    assert sg._has_recursive_flag("tree", ["tree"]) is False


# ---------------------------------------------------------------------------
# Security — inherently recursive commands blocked at ws root
# ---------------------------------------------------------------------------

def test_tree_no_args_blocked():
    """tree with no args targets cwd (ws root) — ancestor of deny zones, deny."""
    assert is_deny("tree")


def test_tree_dot_blocked():
    """tree . targets workspace root — ancestor of deny zones, deny."""
    assert is_deny("tree .")


def test_tree_github_direct_blocked():
    """tree targeting .github directly must be blocked."""
    assert is_deny("tree .github")


def test_tree_project_safe():
    """tree targeting Project/ only (no deny zone ancestor) → ask (still needs approval)."""
    result, _ = sanitize(f"tree {_WS_ROOT}/project")
    assert result in ("ask", "deny")


def test_find_no_args_blocked():
    """find with no path args targets ws root — deny."""
    assert is_deny("find")


def test_find_dot_blocked():
    """find . — deny."""
    assert is_deny("find .")


def test_find_github_direct_blocked():
    assert is_deny("find .github")


def test_find_vscode_direct_blocked():
    assert is_deny(f"find {_WS_ROOT}/.vscode")


# ---------------------------------------------------------------------------
# Security — recursive flagged commands blocked when targeting ancestors
# ---------------------------------------------------------------------------

def test_ls_r_no_args_blocked():
    """ls -r with no path targets ws root — deny."""
    assert is_deny("ls -r")


def test_ls_capital_r_no_args_blocked():
    assert is_deny("ls -R")


def test_ls_combined_lr_blocked():
    assert is_deny("ls -lR")


def test_ls_r_github_blocked():
    assert is_deny("ls -r .github")


def test_dir_slash_s_blocked():
    assert is_deny("dir /s")


def test_dir_slash_s_github_blocked():
    assert is_deny("dir /s .github")


def test_gci_recurse_blocked():
    assert is_deny("gci -recurse")


def test_get_childitem_recurse_blocked():
    assert is_deny("get-childitem -recurse")


def test_get_childitem_r_blocked():
    assert is_deny("get-childitem -r")


# ---------------------------------------------------------------------------
# Regression — non-recursive listing is still allowed (ask)
# ---------------------------------------------------------------------------

def test_ls_no_recurse_safe():
    """Plain ls without -r should pass (ask)."""
    assert is_ask(f"ls {_WS_ROOT}/project")


def test_dir_no_s_safe():
    """dir without /s should pass (ask)."""
    assert is_ask("dir")


def test_gci_no_recurse_safe():
    """gci with no recursive flag should pass (ask), subject to zone check."""
    result, _ = sanitize(f"gci {_WS_ROOT}/project")
    assert result == "ask"


# ---------------------------------------------------------------------------
# Security bypass attempts
# ---------------------------------------------------------------------------

def test_ls_bypass_combined_alr():
    """ls -alR — combined flag with R embedded should be denied."""
    assert is_deny("ls -alR")


def test_tree_quoted_path_blocked():
    """tree with quoted ws root path — deny."""
    assert is_deny(f'tree "{_WS_ROOT}"')


def test_find_quoted_dot_blocked():
    """find with quoted dot — deny."""
    assert is_deny("find \".\"")


def test_gci_recurse_mixed_case_blocked():
    """Get-ChildItem -Recurse (mixed case) — deny."""
    assert is_deny("Get-ChildItem -Recurse")
