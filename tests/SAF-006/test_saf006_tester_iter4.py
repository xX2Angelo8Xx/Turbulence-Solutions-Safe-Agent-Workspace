"""SAF-006 Tester edge-case tests — Iteration 4.

Targets the BUG-024 fix (_WIN_FLAG_RE guard in Step 7 path_args collection) and
verifies there are no new bypass vectors introduced by the change.

Covers:
- dir /s /b Project/   : two Windows flags filtered, explicit safe path retained → ask
- dir /ad              : non-recursive attribute flag — Step 7 never triggered → ask
- dir /s .github/      : trailing slash on deny-zone path still caught → deny
- dir /S               : uppercase Windows flag filtered, cwd fallback fires → deny
- dir /s /workspace/project : long path NOT matched by WIN_FLAG_RE → treated as
                              real path arg → ask
- tree /f              : inherently recursive + Windows display flag filtered →
                         cwd fallback fires → deny
- tree /f Project/     : Windows flag filtered, safe path retained → ask
- dir /s /ad           : 2-char Windows flag also matched by WIN_FLAG_RE,
                         no real path → cwd fallback → deny
- dir /s /b .github    : both flags filtered, deny-zone path retained → deny
- tree /f /a           : two Windows flags both filtered, no path → deny
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
# BUG-024 fix: mixed Windows flags + explicit path argument
# ---------------------------------------------------------------------------

def test_dir_slash_s_slash_b_with_safe_path_asks():
    """dir /s /b Project/ — both flags filtered by WIN_FLAG_RE, safe path remains.

    Verifies the BUG-024 fix does not over-censor: real path args must survive
    the WIN_FLAG_RE guard so the ancestor check can evaluate them correctly.
    """
    assert is_ask(f"dir /s /b {_WS_ROOT}/project")


def test_dir_slash_s_slash_b_relative_safe_path_asks():
    """dir /s /b Project/ with relative path — flags filtered, safe path kept → ask."""
    assert is_ask("dir /s /b Project/")


def test_dir_slash_s_slash_b_deny_zone_denied():
    """dir /s /b .github — flags filtered, deny-zone path retained → deny."""
    assert is_deny("dir /s /b .github")


# ---------------------------------------------------------------------------
# Non-recursive Windows attribute flag — Step 7 must NOT fire
# ---------------------------------------------------------------------------

def test_dir_attr_flag_not_recursive():
    """/ad is an attribute filter, not a recursive flag — Step 7 should not trigger."""
    assert is_ask("dir /ad")


def test_dir_attr_flag_with_path_asks():
    """dir /ad Project/ — attribute flag only, no recursion, safe path → ask."""
    assert is_ask(f"dir /ad {_WS_ROOT}/project")


# ---------------------------------------------------------------------------
# Trailing slash on deny-zone path
# ---------------------------------------------------------------------------

def test_dir_slash_s_github_trailing_slash_denied():
    """dir /s .github/ — trailing slash on deny-zone path must still be blocked.

    Path normalisation must strip the trailing slash before ancestry check.
    """
    assert is_deny("dir /s .github/")


def test_dir_slash_s_vscode_trailing_slash_denied():
    """dir /s .vscode/ — trailing slash variant for .vscode deny zone → deny."""
    assert is_deny("dir /s .vscode/")


# ---------------------------------------------------------------------------
# Mixed-case Windows flag (uppercase /S)
# ---------------------------------------------------------------------------

def test_dir_slash_S_uppercase_cwd_fallback_denied():
    """dir /S — uppercase flag: has_recursive_flag fires (case-insensitive) AND
    WIN_FLAG_RE filters /S → path_args empty → cwd fallback → deny.
    """
    assert is_deny("dir /S")


# ---------------------------------------------------------------------------
# Long absolute path starting with '/' — must NOT be treated as a Windows flag
# ---------------------------------------------------------------------------

def test_dir_slash_s_long_absolute_path_not_filtered():
    """dir /s /workspace/project — /workspace/project is more than 2 chars after /
    and must NOT be matched by WIN_FLAG_RE.  It must be added to path_args,
    evaluated as a safe path, and the command must return ask.
    """
    assert is_ask(f"dir /s {_WS_ROOT}/project")


def test_dir_slash_s_long_absolute_deny_zone_denied():
    """dir /s /workspace/.github — long absolute deny-zone path not filtered → deny."""
    assert is_deny(f"dir /s {_WS_ROOT}/.github")


# ---------------------------------------------------------------------------
# tree with Windows display flag (/f) — inherently recursive command
# ---------------------------------------------------------------------------

def test_tree_slash_f_no_path_denied():
    """tree /f — inherently recursive; /f is a Windows display flag (1 char),
    matched by WIN_FLAG_RE → filtered → path_args empty → cwd fallback → deny.
    """
    assert is_deny("tree /f")


def test_tree_slash_f_slash_a_no_path_denied():
    """tree /f /a — both /f and /a filtered as Windows flags → cwd fallback → deny."""
    assert is_deny("tree /f /a")


def test_tree_slash_f_safe_path_asks():
    """tree /f Project/ — /f filtered, safe path retained → ask."""
    assert is_ask(f"tree /f {_WS_ROOT}/project")


def test_tree_slash_f_deny_zone_denied():
    """tree /f .github — /f filtered, deny-zone path retained → deny."""
    assert is_deny("tree /f .github")


# ---------------------------------------------------------------------------
# 2-char Windows flag (/ad) in combination with /s — WIN_FLAG_RE 2-char match
# ---------------------------------------------------------------------------

def test_dir_slash_s_slash_ad_no_path_denied():
    """dir /s /ad — /s triggers recursive; /ad is 2 alphanumeric chars so also
    matched and filtered by WIN_FLAG_RE → path_args empty → cwd fallback → deny.
    """
    assert is_deny("dir /s /ad")


def test_dir_slash_s_slash_ad_safe_path_asks():
    """dir /s /ad Project/ — both flags filtered, safe path kept → ask."""
    assert is_ask(f"dir /s /ad {_WS_ROOT}/project")


def test_dir_slash_s_slash_ad_deny_zone_denied():
    """dir /s /ad .github — flags filtered, deny zone path retained → deny."""
    assert is_deny("dir /s /ad .github")
