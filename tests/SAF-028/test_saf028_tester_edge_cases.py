"""SAF-028 Tester edge-case tests — bypass attempt analysis.

These tests probe the nine bypass vectors identified by the Tester Agent
during review of the SAF-028 implementation.

Bypass vectors discovered:
  BUG-T01  dir "   "   — whitespace-only quoted arg bypasses Step 8 path detection
  BUG-T02  gci -Include *.py — flag value treated as path arg, bypasses CWD check
  BUG-T03  dir -Recurse -Depth 1 — numeric flag value treated as path arg
  BUG-T04  Get-ChildItem -Depth 1 — numeric flag value treated as path arg
  BUG-T05  ls . — explicit dot resolves to workspace root, zone-classified as allow

Cases that pass correctly (documenting expected good behaviour):
  OK-01  Get-ChildItem -Path ""   — empty -Path value → DENY via Step 8
  OK-02  ls -la                  — combined Unix flag → DENY via Step 8
  OK-03  Get-ChildItem -LiteralPath "" — empty -LiteralPath value → DENY
  OK-04  dir ./.github           — posix-slash deny-zone path → DENY via Step 5
"""
from __future__ import annotations

import os
import sys

import pytest
from unittest.mock import patch

_SCRIPTS_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__),
    "..", "..",
    "Default-Project", ".github", "hooks", "scripts",
))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

_WS_ROOT = "/workspace"
_PROJECT_CWD = "/workspace/project"


# ---------------------------------------------------------------------------
# Helpers (mirrors parent test file)
# ---------------------------------------------------------------------------

def sanitize(command: str, cwd: str = _WS_ROOT) -> tuple[str, str | None]:
    with patch.object(sg.os, "getcwd", return_value=cwd):
        return sg.sanitize_terminal_command(command, _WS_ROOT)


def is_deny(command: str, cwd: str = _WS_ROOT) -> bool:
    return sanitize(command, cwd)[0] == "deny"


def is_allow(command: str, cwd: str = _WS_ROOT) -> bool:
    return sanitize(command, cwd)[0] in ("allow", "ask")


# ===========================================================================
# PASSING EDGE CASES — these are already handled correctly by the
# current implementation and serve as regression anchors.
# ===========================================================================

def test_gci_empty_path_param_denied():
    """Get-ChildItem -Path "" — empty -Path value is not a real path → DENY.

    The quoted empty string is stripped to "", filtered as falsy in Step 8,
    leaving path_args_s8 empty → CWD ancestor check fires → DENY.
    """
    assert is_deny('Get-ChildItem -Path ""')


def test_ls_combined_unix_flags_denied():
    """`ls -la` — combined Unix flag with no path → DENY.

    -la starts with -, filtered in Step 8 → path_args_s8 empty → CWD check
    fires → DENY from workspace root.
    """
    assert is_deny("ls -la")


def test_gci_empty_literalpath_param_denied():
    """`Get-ChildItem -LiteralPath ""` — empty -LiteralPath value → DENY.

    Empty quoted argument is filtered; path_args_s8 empty → CWD check → DENY.
    """
    assert is_deny('Get-ChildItem -LiteralPath ""')


def test_dir_posix_github_path_denied():
    """`dir ./.github` — posix-slash explicit deny-zone path → DENY.

    The path ./.github resolves to a deny zone; caught by Step 5 zone check.
    """
    assert is_deny("dir ./.github")


# ===========================================================================
# FAILING EDGE CASES — these expose genuine bypass vectors in Step 8.
# Each test is marked xfail to document the known bug. The Developer
# MUST fix Step 8 so these all pass (xpass → remove xfail marker).
# ===========================================================================

def test_dir_whitespace_only_path_denied():
    """`dir "   "` — whitespace-only quoted path should NOT bypass Step 8.

    Expected: DENY (whitespace cannot be a real path — treat same as empty).
    Actual (BUG): ALLOW — whitespace-only stripped token is truthy, added to
    path_args_s8, so CWD ancestor check never fires.
    """
    assert is_deny('dir "   "')


def test_gci_include_filter_no_path_denied():
    """`gci -Include *.py` — filter pattern should not substitute for a path.

    Expected: DENY — no real path arg, CWD=workspace root.
    Actual (BUG): ALLOW — '*.py' (value of -Include) added to path_args_s8.
    """
    assert is_deny("gci -Include *.py")


def test_gci_filter_no_path_denied():
    """`gci -Filter *.py` — filter value should not count as a path argument.

    Expected: DENY — no real path arg, CWD=workspace root.
    Actual (BUG): ALLOW — '*.py' (value of -Filter) added to path_args_s8.
    """
    assert is_deny("gci -Filter *.py")


def test_dir_recurse_depth_no_path_denied():
    """`dir -Recurse -Depth 1` — depth value should not substitute for a path.

    Expected: DENY — no real path arg, CWD=workspace root.
    Actual (BUG): ALLOW — '1' (value of -Depth) added to path_args_s8.
    """
    assert is_deny("dir -Recurse -Depth 1")


def test_gci_depth_no_path_denied():
    """`Get-ChildItem -Depth 1` — depth value should not count as a path.

    Expected: DENY — no real path, CWD=workspace root.
    Actual (BUG): ALLOW — '1' (value of -Depth) mistaken for path argument.
    """
    assert is_deny("Get-ChildItem -Depth 1")


def test_ls_dot_ws_root_denied():
    """`ls .` from workspace root should be treated as bare listing → DENY.

    `ls .` is semantically equivalent to `ls` from workspace root: both list
    CWD contents (including deny-zone subdirectory names).
    Expected: DENY — '.' resolves to workspace root, which is an ancestor of
    deny zones.
    Actual (BUG): ALLOW — zone classifier returns 'allow' for workspace root.
    """
    assert is_deny("ls .")
