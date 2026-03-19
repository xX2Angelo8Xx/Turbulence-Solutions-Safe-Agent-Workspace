"""SAF-028 — Bare directory enumeration protection tests.

Covers:
- Bare dir/ls/Get-ChildItem/gci with no path, CWD=workspace root → DENY
- Bare dir/ls/Get-ChildItem with no path, CWD=project folder → ALLOW
- Get-ChildItem -Recurse (no path) → DENY  (SAF-006 Step 7 regression)
- Get-ChildItem -Recurse -Force (no path) → DENY  (SAF-006 Step 7 regression)
- tree/find (no path) → DENY  (inherently recursive, SAF-006 Step 7)
- Explicit path arguments preserve existing allow behaviour
- Bypass attempts: Windows flags only (no path), quoted empty paths
"""
from __future__ import annotations

import os
import sys

import pytest
from unittest.mock import patch

_SCRIPTS_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__),
    "..", "..",
    "templates", "coding", ".github", "hooks", "scripts",
))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

_WS_ROOT = "/workspace"
_PROJECT_CWD = "/workspace/project"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sanitize(command: str, cwd: str = _WS_ROOT) -> tuple[str, str | None]:
    with patch.object(sg.os, "getcwd", return_value=cwd):
        return sg.sanitize_terminal_command(command, _WS_ROOT)


def is_deny(command: str, cwd: str = _WS_ROOT) -> bool:
    return sanitize(command, cwd)[0] == "deny"


def is_allow(command: str, cwd: str = _WS_ROOT) -> bool:
    return sanitize(command, cwd)[0] in ("allow", "ask")


# ---------------------------------------------------------------------------
# Test 1 — Get-ChildItem -Recurse (no path, CWD=workspace root) → DENY
# ---------------------------------------------------------------------------

def test_gci_recurse_no_path_ws_root_denied():
    """Get-ChildItem -Recurse with no path arg, CWD=workspace root → DENY.

    Step 7 (SAF-006 ancestor check) catches this via the '.' CWD fallback.
    Step 8 (SAF-028) provides defence-in-depth.
    """
    assert is_deny("Get-ChildItem -Recurse")


# ---------------------------------------------------------------------------
# Test 2 — Get-ChildItem -Recurse -Force (no path) → DENY
# ---------------------------------------------------------------------------

def test_gci_recurse_force_no_path_denied():
    """Get-ChildItem -Recurse -Force with no explicit path → DENY.

    Regression for Security Audit V2.0.0 Finding 2.
    """
    assert is_deny("Get-ChildItem -Recurse -Force")


# ---------------------------------------------------------------------------
# Test 3 — dir (no path, CWD=workspace root) → DENY
# ---------------------------------------------------------------------------

def test_dir_bare_ws_root_denied():
    """Bare dir with no path, CWD=workspace root → DENY (SAF-028)."""
    assert is_deny("dir")


# ---------------------------------------------------------------------------
# Test 4 — ls (no path, CWD=workspace root) → DENY
# ---------------------------------------------------------------------------

def test_ls_bare_ws_root_denied():
    """Bare ls with no path, CWD=workspace root → DENY (SAF-028)."""
    assert is_deny("ls")


# ---------------------------------------------------------------------------
# Test 5 — tree (no path, CWD=workspace root) → DENY
# ---------------------------------------------------------------------------

def test_tree_bare_ws_root_denied():
    """Bare tree with no path, CWD=workspace root → DENY.

    tree is inherently recursive (Step 7); also caught by Step 8.
    """
    assert is_deny("tree")


# ---------------------------------------------------------------------------
# Test 6 — find (no path, CWD=workspace root) → DENY
# ---------------------------------------------------------------------------

def test_find_bare_ws_root_denied():
    """Bare find with no path, CWD=workspace root → DENY.

    find is inherently recursive (Step 7); also caught by Step 8.
    """
    assert is_deny("find")


# ---------------------------------------------------------------------------
# Test 7 — dir Project/ (explicit project path) → ALLOW
# ---------------------------------------------------------------------------

def test_dir_explicit_project_path_allowed():
    """dir Project/ — explicit safe path arg → ALLOW (unchanged behaviour)."""
    result, _ = sanitize("dir Project/")
    assert result in ("allow", "ask"), f"Expected allow/ask, got {result!r}"


# ---------------------------------------------------------------------------
# Test 8 — ls src/ (explicit project path) → ALLOW
# ---------------------------------------------------------------------------

def test_ls_explicit_project_path_allowed():
    """ls src/ — explicit project-relative path → ALLOW."""
    result, _ = sanitize(f"ls {_WS_ROOT}/project")
    assert result in ("allow", "ask"), f"Expected allow/ask, got {result!r}"


# ---------------------------------------------------------------------------
# Test 9 — Get-ChildItem -Recurse Project/ (explicit project path) → ALLOW
# ---------------------------------------------------------------------------

def test_gci_recurse_explicit_project_path_allowed():
    """Get-ChildItem -Recurse Project/ — explicit safe path → ALLOW."""
    result, _ = sanitize("Get-ChildItem -Recurse Project/")
    assert result in ("allow", "ask"), f"Expected allow/ask, got {result!r}"


# ---------------------------------------------------------------------------
# Test 10 — Get-ChildItem (no -Recurse, no path, CWD=workspace root) → DENY
# ---------------------------------------------------------------------------

def test_gci_bare_no_recurse_ws_root_denied():
    """Get-ChildItem alone (no flags, no path), CWD=workspace root → DENY.

    SAF-028 Step 8 catches bare listing even without the recursive flag.
    """
    assert is_deny("Get-ChildItem")


# ---------------------------------------------------------------------------
# Additional: gci alias bare → DENY
# ---------------------------------------------------------------------------

def test_gci_alias_bare_ws_root_denied():
    """gci bare (alias for Get-ChildItem), CWD=workspace root → DENY."""
    assert is_deny("gci")


# ---------------------------------------------------------------------------
# CWD inside project folder — bare listing should be ALLOWED
# ---------------------------------------------------------------------------

def test_dir_bare_project_cwd_allowed():
    """dir with no path, CWD=project folder → ALLOW (not ancestor of deny zones)."""
    assert is_allow("dir", cwd=_PROJECT_CWD)


def test_ls_bare_project_cwd_allowed():
    """ls with no path, CWD=project folder → ALLOW."""
    assert is_allow("ls", cwd=_PROJECT_CWD)


def test_gci_bare_project_cwd_allowed():
    """Get-ChildItem with no path, CWD=project folder → ALLOW."""
    assert is_allow("Get-ChildItem", cwd=_PROJECT_CWD)


# ---------------------------------------------------------------------------
# Windows-flag-only tokens (no real path) — still DENY from ws root
# ---------------------------------------------------------------------------

def test_dir_windows_flags_only_no_path_denied():
    """dir /b (Windows display flag only, no path), CWD=ws root → DENY.

    /b is a Windows-style flag filtered by the WIN_FLAG_RE guard in Step 8.
    With no remaining path args, CWD check fires → DENY.
    """
    assert is_deny("dir /b")


def test_dir_slash_a_no_path_denied():
    """dir /a (attribute filter only, no path), CWD=ws root → DENY."""
    assert is_deny("dir /a")


# ---------------------------------------------------------------------------
# Explicit deny-zone path arguments — still DENY
# ---------------------------------------------------------------------------

def test_dir_explicit_github_denied():
    """dir .github — explicit deny-zone path arg → DENY."""
    assert is_deny("dir .github")


def test_ls_explicit_vscode_denied():
    """ls .vscode — explicit deny-zone path arg → DENY."""
    assert is_deny("ls .vscode")


def test_gci_explicit_github_denied():
    """Get-ChildItem .github — explicit deny-zone path (leading dot) → DENY."""
    assert is_deny("Get-ChildItem .github")


# ---------------------------------------------------------------------------
# Bypass attempt: quoted empty string as path (should NOT be treated as path)
# ---------------------------------------------------------------------------

def test_dir_quoted_empty_string_no_real_path_denied():
    """dir '' (quoted empty string) — not a real path, CWD=ws root → DENY.

    An attacker might use dir '' to bypass the 'has_path_arg' detection.
    Empty stripped string is falsy, so it must not set has_path_arg=True.
    """
    assert is_deny("dir ''")


# ---------------------------------------------------------------------------
# _BARE_LISTING_VERBS constant is publicly accessible
# ---------------------------------------------------------------------------

def test_bare_listing_verbs_constant_exists():
    """_BARE_LISTING_VERBS constant exists and contains all expected verbs."""
    assert hasattr(sg, "_BARE_LISTING_VERBS")
    expected = {"dir", "ls", "get-childitem", "gci", "tree", "find"}
    assert expected.issubset(sg._BARE_LISTING_VERBS)
