"""SAF-068 — Regression tests for shlex backslash normalization in _tokenize_segment.

BUG-173: shlex(posix=True) consumed backslashes in unquoted Windows paths,
allowing C:\\Users\\angel\\secret.txt to pass zone checks as 'C:Usersangelsecret.txt'.

Fix: segment.replace("\\", "/") inserted in _tokenize_segment() BEFORE shlex call.

Tests:
  T01 - _tokenize_segment preserves path with forward slashes after normalization
  T02 - Unquoted C:\\Users\\angel\\secret.txt (Get-Content) is denied
  T03 - Unquoted C:\\Users (Get-ChildItem) is denied
  T04 - Quoted "C:\\Users\\angel\\secret.txt" (Get-Content) still denied
  T05 - Project-relative path is allowed
  T06 - UNC path \\\\server\\share is denied
"""
from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "templates", "agent-workbench", ".github", "hooks", "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

WS = "c:/workspace"


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# ---------------------------------------------------------------------------
# T01: _tokenize_segment normalizes backslashes to forward slashes
# ---------------------------------------------------------------------------

def test_tokenize_segment_normalizes_backslashes():
    """BUG-173: backslashes in unquoted path must survive shlex as forward slashes."""
    tokens = sg._tokenize_segment(r"Get-Content C:\Users\angel\secret.txt")
    # After normalization the path token must contain forward slashes, not be empty
    path_token = next((t for t in tokens if "Users" in t), None)
    assert path_token is not None, "Path token should not be consumed by shlex"
    assert "/" in path_token, (
        f"Forward slashes expected in path token, got: {path_token!r}"
    )
    assert "\\" not in path_token, (
        f"Backslashes should have been normalized away, got: {path_token!r}"
    )


# ---------------------------------------------------------------------------
# T02: Unquoted Windows absolute path — Get-Content — must be denied
# ---------------------------------------------------------------------------

def test_unquoted_windows_path_get_content_denied():
    """BUG-173: Get-Content C:\\Users\\angel\\secret.txt must be denied."""
    decision, reason = sg.sanitize_terminal_command(
        r"Get-Content C:\Users\angel\secret.txt", WS
    )
    assert decision == "deny", (
        f"Expected deny for unquoted Windows path, got {decision!r}; reason={reason!r}"
    )


# ---------------------------------------------------------------------------
# T03: Unquoted Windows absolute path — Get-ChildItem — must be denied
# ---------------------------------------------------------------------------

def test_unquoted_windows_path_get_childitem_denied():
    """BUG-173: Get-ChildItem C:\\Users must be denied."""
    decision, reason = sg.sanitize_terminal_command(
        r"Get-ChildItem C:\Users", WS
    )
    assert decision == "deny", (
        f"Expected deny for unquoted Get-ChildItem path, got {decision!r}; reason={reason!r}"
    )


# ---------------------------------------------------------------------------
# T04: Quoted Windows absolute path still denied (regression: existing behaviour)
# ---------------------------------------------------------------------------

def test_quoted_windows_path_still_denied():
    """Quoted C:\\Users\\angel\\secret.txt must continue to be denied."""
    decision, reason = sg.sanitize_terminal_command(
        'Get-Content "C:\\Users\\angel\\secret.txt"', WS
    )
    assert decision == "deny", (
        f"Expected deny for quoted Windows path, got {decision!r}; reason={reason!r}"
    )


# ---------------------------------------------------------------------------
# T05: Project-relative path must remain allowed
# ---------------------------------------------------------------------------

def test_project_relative_path_allowed():
    """A path inside the project folder must still be allowed after the fix."""
    decision, reason = sg.sanitize_terminal_command(
        "Get-Content project/README.md", WS
    )
    assert decision == "allow", (
        f"Expected allow for project-relative path, got {decision!r}; reason={reason!r}"
    )


# ---------------------------------------------------------------------------
# T06: UNC path must be denied
# ---------------------------------------------------------------------------

def test_unc_path_denied():
    """UNC path \\\\server\\share after normalization becomes //server/share — deny."""
    decision, reason = sg.sanitize_terminal_command(
        r"Get-Content \\server\share\file.txt", WS
    )
    assert decision == "deny", (
        f"Expected deny for UNC path, got {decision!r}; reason={reason!r}"
    )


# ===========================================================================
# Tester edge-case tests — SAF-068
# ===========================================================================

# ---------------------------------------------------------------------------
# T07: Trailing backslash — ls tests\ (FIX-022/023 safe-fail preserved)
# ---------------------------------------------------------------------------

def test_trailing_backslash_safe_fail_deny():
    """Trailing backslash must NOT be normalized and must still safe-fail deny.

    The fix uses (?=\\S) lookahead so trailing backslashes are NOT converted
    to forward slashes. shlex should raise ValueError → empty token list →
    safe-fail deny.
    """
    decision, reason = sg.sanitize_terminal_command(
        r"ls tests\ ", WS  # Note: trailing backslash followed by space
    )
    # The result must be deny (either via shlex error or zone check)
    # We do NOT mandate the specific reason — only that it does not allow.
    assert decision == "deny", (
        f"Expected deny for trailing-backslash command, got {decision!r}; reason={reason!r}"
    )


# ---------------------------------------------------------------------------
# T08: Mixed separators — C:\Users/angel/file.txt — must be denied
# ---------------------------------------------------------------------------

def test_mixed_separators_denied():
    """Path mixing \\ and / separators must be denied (escapes outside project)."""
    decision, reason = sg.sanitize_terminal_command(
        r"Get-Content C:\Users/angel/file.txt", WS
    )
    assert decision == "deny", (
        f"Expected deny for mixed-separator path, got {decision!r}; reason={reason!r}"
    )


# ---------------------------------------------------------------------------
# T09: Multiple consecutive backslashes — C:\\\\Users\\\\angel — must be denied
# ---------------------------------------------------------------------------

def test_multiple_backslashes_denied():
    """Multiple consecutive backslashes (e.g. C:\\\\Users\\\\angel) must be denied."""
    decision, reason = sg.sanitize_terminal_command(
        "Get-Content C:\\\\Users\\\\angel", WS
    )
    assert decision == "deny", (
        f"Expected deny for multi-backslash path, got {decision!r}; reason={reason!r}"
    )


# ---------------------------------------------------------------------------
# T10: Relative Windows path traversal — ..\\..\\.github\\hooks — must be denied
# ---------------------------------------------------------------------------

def test_relative_windows_traversal_denied():
    """Relative Windows-style path traversal must be denied."""
    decision, reason = sg.sanitize_terminal_command(
        r"Get-Content ..\..\\.github\hooks", WS
    )
    assert decision == "deny", (
        f"Expected deny for relative traversal path, got {decision!r}; reason={reason!r}"
    )


# ---------------------------------------------------------------------------
# T11: _tokenize_segment trailing backslash returns empty list (safe-fail)
# ---------------------------------------------------------------------------

def test_tokenize_segment_trailing_backslash_returns_empty():
    """Trailing backslash (unmatched escape) must cause shlex ValueError → empty list."""
    # A lone trailing backslash at end of segment triggers shlex ValueError in posix mode
    result = sg._tokenize_segment("ls tests\\")
    assert result == [], (
        f"Expected empty list for trailing-backslash segment (safe-fail), got {result!r}"
    )


# ---------------------------------------------------------------------------
# T12: Drive-letter-only path is denied (e.g. just "C:\\")
# ---------------------------------------------------------------------------

def test_drive_root_path_denied():
    """Get-ChildItem C:\\ must be denied — drive root is outside workspace."""
    decision, reason = sg.sanitize_terminal_command(
        "Get-ChildItem C:\\", WS
    )
    assert decision == "deny", (
        f"Expected deny for drive-root path, got {decision!r}; reason={reason!r}"
    )
