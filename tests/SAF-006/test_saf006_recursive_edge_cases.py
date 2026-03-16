"""SAF-006 Tester edge-case tests — Iteration 2 (2026-03-12).

Tests added by Tester Agent beyond the Developer's test suite.

Focus areas:
 1. Tree / find with named flags (e.g. -name)
 2. ls -R standalone flag vs combined-flag inconsistency (BUG-023)
 3. gci -r path-aware behavior (BUG-023)
 4. BUG-022 regression: ls -Rl (reversed combined-flag order) detected as recursive
 5. Path traversal to protected zone via ../../.github
 6. Non-recursive listing still allowed in safe dirs after SAF-006 changes

Verdict context
---------------
Two tests (*_should_allow) are expected to FAIL on the current codebase because
standalone recursive flags (-r, -recurse) remain in denied_flags for ls and gci,
unconditionally blocking all recursive use regardless of path.  This contradicts
US-011 which requires only *protected-zone ancestors* to be blocked. BUG-023.
"""
from __future__ import annotations

import os
import sys

import pytest  # noqa: F401

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
    return sanitize(command)[0] in ("ask", "allow")


def is_deny(command: str) -> bool:
    return sanitize(command)[0] == "deny"


# ---------------------------------------------------------------------------
# Tree with relative paths
# ---------------------------------------------------------------------------

def test_ec_tree_relative_project_allowed():
    """tree Project/ — relative safe dir, not ancestor of deny zones → allow."""
    result, _ = sanitize("tree Project/")
    assert result in ("ask", "allow")


# ---------------------------------------------------------------------------
# Find with -name flag
# ---------------------------------------------------------------------------

def test_ec_find_name_flag_ws_root_blocked():
    """find . -name '*.py' — workspace root is ancestor of deny zones → deny."""
    assert is_deny("find . -name '*.py'")


def test_ec_find_project_name_flag_allowed():
    """find Project/ -name '*.py' — Project/ is safe, not ancestor of deny zones → allow."""
    result, _ = sanitize("find Project/ -name '*.py'")
    assert result in ("ask", "allow")


# ---------------------------------------------------------------------------
# ls -R standalone flag
#
# BUG-023: standalone -r/-R in ls.denied_flags (Step 1) blocks ALL paths,
# including safe ones.  Combined -lR is handled by Step 7 (path-aware) and IS
# allowed for safe paths.  The two code paths produce inconsistent outcomes for
# semantically equivalent operations:
#   ls -R  Project/  →  deny  (Step 1 fires: -r in denied_flags)
#   ls -lR Project/  →  ask   (Step 7 ancestor check: Project/ is safe)
#
# US-011 acceptance criteria: "Recursive file listing commands targeting protected
# zones are blocked."  Safe zones should NOT be blocked.
# ---------------------------------------------------------------------------

def test_ec_ls_capital_r_posix_root_blocked():
    """ls -R / — root path argument is ancestor of all deny zones → deny."""
    assert is_deny("ls -R /")


def test_ec_ls_capital_r_project_should_allow():
    """ls -R Project/ — safe zone; US-011 only requires blocking protected-zone ancestors.

    EXPECTED: ask
    ACTUAL (current): deny — BUG-023.

    Standalone -r/-R in ls.denied_flags fires (Step 1) before the SAF-006
    ancestor check (Step 7), unconditionally denying recursive ls even when the
    target is a safe directory.  This is INCONSISTENT with ls -lR Project/ which
    returns ask via Step 7.

    Fix: remove '-r' and '--recursive' from ls.denied_flags; rely on
    _has_recursive_flag() + _is_ancestor_of_deny_zone() (Step 7) for all
    recursive-flag detection.
    """
    result, _ = sanitize("ls -R Project/")
    assert result in ("ask", "allow"), (
        f"BUG-023: 'ls -R Project/' returned {result!r} instead of 'ask' or 'allow'. "
        "Standalone -R in ls.denied_flags (Step 1) blocks ALL recursive ls "
        "regardless of path. Fix: remove '-r','--recursive' from ls.denied_flags "
        "and rely on Step 7 ancestor check."
    )


# ---------------------------------------------------------------------------
# ls combined flags — BUG-022 regression
# ---------------------------------------------------------------------------

def test_ec_ls_combined_lr_project_allowed():
    """ls -lR Project/ — combined recursive flag, safe path → allow (Step 7 ancestor=False)."""
    result, _ = sanitize("ls -lR Project/")
    assert result in ("ask", "allow")


def test_ec_ls_combined_rl_no_path_blocked():
    """ls -Rl with no path — R precedes l; still detected as recursive → deny.

    BUG-022 regression: _has_recursive_flag must detect 'r' anywhere in
    combined flag string, not only at a fixed position.
    """
    assert is_deny("ls -Rl")


def test_ec_ls_combined_rl_project_allowed():
    """ls -Rl Project/ — R-first combined flag, safe path → allow.

    BUG-022 regression: reversed combined flag at safe path must still be allowed
    after the ancestor check returns False.
    """
    result, _ = sanitize("ls -Rl Project/")
    assert result in ("ask", "allow")


# ---------------------------------------------------------------------------
# gci -r with safe path
#
# BUG-023 (same root cause): standalone -r/-recurse in gci.denied_flags blocks
# all gci -r calls regardless of path.  Per US-011, gci -r Project/ should be
# allowed because Project/ is not a protected-zone ancestor.
# ---------------------------------------------------------------------------

def test_ec_gci_r_project_should_allow():
    """gci -r Project/ — safe zone; US-011 only requires blocking protected-zone ancestors.

    EXPECTED: ask
    ACTUAL (current): deny — BUG-023.

    Standalone -r in gci.denied_flags fires before Step 7 ancestor check.

    Fix: remove '-r' and '-recurse' from gci.denied_flags (and
    get-childitem.denied_flags); rely on _has_recursive_flag() + Step 7.
    """
    result, _ = sanitize("gci -r Project/")
    assert result in ("ask", "allow"), (
        f"BUG-023: 'gci -r Project/' returned {result!r} instead of 'ask' or 'allow'. "
        "Standalone -r in gci.denied_flags unconditionally blocks recursive gci. "
        "Fix: remove '-r','-recurse' from gci/get-childitem denied_flags; "
        "rely on Step 7 ancestor check."
    )


# ---------------------------------------------------------------------------
# Path traversal to protected zone
# ---------------------------------------------------------------------------

def test_ec_find_traversal_dotdot_github_blocked():
    """find ../../.github — traversal into .github deny zone → deny.

    zone_classifier resolves ../../.github relative to ws_root to /.github;
    Method 2 pattern scan detects /.github and returns 'deny'.
    """
    assert is_deny("find ../../.github")


# ---------------------------------------------------------------------------
# Non-recursive listing in safe dirs — unchanged after SAF-006
# ---------------------------------------------------------------------------

def test_ec_dir_no_s_project_safe():
    """dir Project/ without /s — non-recursive listing of safe zone → allow."""
    result, _ = sanitize("dir Project/")
    assert result in ("ask", "allow")


def test_ec_get_childitem_no_recurse_project_safe():
    """Get-ChildItem Project/ without -Recurse — non-recursive, safe path → allow."""
    result, _ = sanitize("Get-ChildItem Project/")
    assert result in ("ask", "allow")


def test_ec_ls_no_recurse_project_safe():
    """ls Project/ without -r/-R — non-recursive listing of safe zone → allow."""
    result, _ = sanitize("ls Project/")
    assert result in ("ask", "allow")
