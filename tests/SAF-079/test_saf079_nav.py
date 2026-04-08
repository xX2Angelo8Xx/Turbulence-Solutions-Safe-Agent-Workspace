"""SAF-079 — Tests for workspace-internal navigation and push-location allowlist.

Covers:
    push-location in allowlist
        - push-location with project-folder path -> allowed
        - push-location with deny-zone path (.github) -> denied
        - push-location with deny-zone path (.vscode) -> denied
        - push-location navigating above workspace root -> denied

    _check_nav_path_arg unit tests
        - cd .. from project folder -> workspace root -> allowed
        - set-location .. -> workspace root -> allowed
        - sl .. -> workspace root -> allowed
        - cd ../.. -> above workspace root -> denied
        - cd .github -> denied
        - cd .vscode -> denied
        - cd noagentzone -> denied
        - cd NoAgentZone -> denied (case-insensitive)
        - cd with absolute path inside workspace -> allowed
        - cd with absolute path outside workspace -> denied
        - cd with absolute path to workspace root itself -> allowed
        - _check_nav_path_arg: project-internal subdir (relative) -> allowed
        - _check_nav_path_arg: dollar-sign token -> denied
        - _check_nav_path_arg: non-path token -> allowed
        - _check_nav_path_arg: workspace root via absolute path -> allowed
        - _check_nav_path_arg: path above workspace absolute -> denied
"""
from __future__ import annotations

import sys
import os
import functools
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Make security_gate importable from the template scripts directory
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "templates", "agent-workbench",
        ".github", "hooks", "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

WS = "c:/workspace"
PROJECT = "project"


def _mock_pf(fn):
    """Decorator: patch detect_project_folder to return PROJECT constant."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with patch("zone_classifier.detect_project_folder", return_value=PROJECT):
            return fn(*args, **kwargs)
    return wrapper


def allow(cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "allow"


def deny(cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "deny"


# ===========================================================================
# push-location in allowlist
# ===========================================================================

@_mock_pf
def test_push_location_project_subdir_allowed():
    """push-location Project/src (relative multi-segment) must be allowed."""
    # "project/src" resolves to c:/workspace/project/src — inside workspace
    assert allow("push-location project/src"), (
        "push-location project/src must be allowed"
    )


@_mock_pf
def test_push_location_absolute_inside_workspace_allowed():
    """push-location with absolute path inside workspace must be allowed."""
    assert allow(f"push-location {WS}/project"), (
        "push-location to absolute path inside workspace must be allowed"
    )


@_mock_pf
def test_push_location_github_denied():
    """push-location .github must be denied (deny zone)."""
    assert deny("push-location .github"), (
        "push-location .github must be denied"
    )


@_mock_pf
def test_push_location_vscode_denied():
    """push-location .vscode must be denied (deny zone)."""
    assert deny("push-location .vscode"), (
        "push-location .vscode must be denied"
    )


@_mock_pf
def test_push_location_above_workspace_denied():
    """push-location ../.. (above workspace root) must be denied."""
    assert deny("push-location ../.."), (
        "push-location ../.. must be denied — navigates above workspace root"
    )


# ===========================================================================
# cd .. — workspace-root navigation
# ===========================================================================

@_mock_pf
def test_cd_dotdot_allowed():
    """cd .. from project folder reaches workspace root — must be allowed."""
    assert allow("cd .."), "cd .. must be allowed (project-folder fallback reaches workspace root)"


@_mock_pf
def test_set_location_dotdot_allowed():
    """Set-Location .. from project folder — must be allowed."""
    assert allow("Set-Location .."), "Set-Location .. must be allowed"


@_mock_pf
def test_sl_dotdot_allowed():
    """sl .. (alias for Set-Location) — must be allowed."""
    assert allow("sl .."), "sl .. must be allowed"


@_mock_pf
def test_cd_dotdot_dotdot_denied():
    """cd ../.. navigates above workspace root — must be denied."""
    assert deny("cd ../.."), "cd ../.. must be denied — above workspace root"


# ===========================================================================
# Deny zones — navigation into protected directories is blocked
# ===========================================================================

@_mock_pf
def test_cd_github_denied():
    """cd .github must be denied."""
    assert deny("cd .github"), "cd .github must be denied"


@_mock_pf
def test_cd_vscode_denied():
    """`cd .vscode` must be denied."""
    assert deny("cd .vscode"), "cd .vscode must be denied"


@_mock_pf
def test_cd_noagentzone_denied():
    """cd noagentzone must be denied."""
    assert deny("cd noagentzone"), "cd noagentzone must be denied"


@_mock_pf
def test_cd_noagentzone_case_insensitive_denied():
    """cd NoAgentZone (mixed case) must be denied."""
    assert deny("cd NoAgentZone"), "cd NoAgentZone must be denied (case-insensitive)"


# ===========================================================================
# Absolute path tests
# ===========================================================================

@_mock_pf
def test_cd_absolute_inside_workspace_allowed():
    """cd to absolute path inside workspace must be allowed."""
    assert allow(f"cd {WS}/project"), (
        "cd to absolute path inside workspace must be allowed"
    )


@_mock_pf
def test_cd_absolute_workspace_root_allowed():
    """cd to workspace root itself (absolute) must be allowed."""
    assert allow(f"cd {WS}"), (
        "cd to workspace root (absolute path) must be allowed"
    )


@_mock_pf
def test_cd_absolute_outside_workspace_denied():
    """cd to absolute path outside workspace must be denied."""
    assert deny("cd c:/other"), (
        "cd to absolute path outside workspace must be denied"
    )


@_mock_pf
def test_set_location_absolute_inside_workspace_allowed():
    """Set-Location with absolute path inside workspace must be allowed."""
    assert allow(f"Set-Location {WS}/project/src"), (
        "Set-Location to absolute path inside workspace must be allowed"
    )


# ===========================================================================
# _check_nav_path_arg unit tests
# ===========================================================================

@_mock_pf
def test_check_nav_path_arg_dollar_token_denied():
    """Dollar sign in nav path arg must be denied."""
    assert not sg._check_nav_path_arg("$HOME", WS), (
        "_check_nav_path_arg must deny dollar-sign tokens"
    )


@_mock_pf
def test_check_nav_path_arg_non_path_token_allowed():
    """Non-path-like token (plain identifier) must be allowed."""
    # "somecommand" has no slashes, no .., no . prefix — not path-like
    assert sg._check_nav_path_arg("somecommand", WS), (
        "_check_nav_path_arg must allow non-path tokens"
    )


@_mock_pf
def test_check_nav_path_arg_dotdot_allowed():
    """.. resolved from project folder reaches workspace root — allowed."""
    assert sg._check_nav_path_arg("..", WS), (
        "_check_nav_path_arg('..', ws_root) must return True via project-folder fallback"
    )


@_mock_pf
def test_check_nav_path_arg_dotdot_dotdot_denied():
    """../.. resolved from project folder goes above workspace root — denied."""
    assert not sg._check_nav_path_arg("../..", WS), (
        "_check_nav_path_arg('../..', ws_root) must return False"
    )


@_mock_pf
def test_check_nav_path_arg_workspace_root_absolute_allowed():
    """Absolute path equal to workspace root must be allowed."""
    assert sg._check_nav_path_arg(WS, WS), (
        "_check_nav_path_arg(ws_root, ws_root) must return True"
    )


@_mock_pf
def test_check_nav_path_arg_inside_workspace_allowed():
    """Absolute path inside workspace must be allowed."""
    assert sg._check_nav_path_arg(f"{WS}/project/subdir", WS), (
        "_check_nav_path_arg must allow path inside workspace"
    )


@_mock_pf
def test_check_nav_path_arg_outside_workspace_denied():
    """Absolute path outside workspace must be denied."""
    assert not sg._check_nav_path_arg("c:/outside", WS), (
        "_check_nav_path_arg must deny path outside workspace"
    )


@_mock_pf
def test_check_nav_path_arg_github_denied():
    """.github path must be denied."""
    assert not sg._check_nav_path_arg(".github", WS), (
        "_check_nav_path_arg('.github', ws_root) must return False"
    )


@_mock_pf
def test_check_nav_path_arg_noagentzone_denied():
    """noagentzone path must be denied."""
    assert not sg._check_nav_path_arg("noagentzone", WS), (
        "_check_nav_path_arg('noagentzone', ws_root) must return False"
    )


# ===========================================================================
# Tester edge cases — SAF-030 tilde bypass via project-folder fallback
# These tests guard against the project-folder fallback in _check_nav_path_arg
# incorrectly allowing tilde navigation (which expands to HOME at runtime).
# ===========================================================================

@_mock_pf
def test_cd_tilde_denied():
    """cd ~ must be denied — tilde expands to HOME (outside workspace) at runtime."""
    assert deny("cd ~"), (
        "cd ~ must be denied; tilde expands to HOME outside workspace"
    )


@_mock_pf
def test_push_location_tilde_denied():
    """push-location ~ must be denied — tilde expands to HOME at runtime."""
    assert deny("push-location ~"), (
        "push-location ~ must be denied"
    )


@_mock_pf
def test_sl_tilde_denied():
    """sl ~ must be denied — tilde expands to HOME at runtime."""
    assert deny("sl ~"), (
        "sl ~ must be denied"
    )


@_mock_pf
def test_set_location_tilde_slash_denied():
    """Set-Location ~/documents must be denied — tilde prefix targets HOME."""
    assert deny("Set-Location ~/documents"), (
        "Set-Location ~/documents must be denied"
    )


@_mock_pf
def test_check_nav_path_arg_tilde_denied():
    """_check_nav_path_arg must deny bare tilde (HOME reference)."""
    assert not sg._check_nav_path_arg("~", WS), (
        "_check_nav_path_arg('~', ws_root) must return False"
    )


@_mock_pf
def test_check_nav_path_arg_tilde_slash_denied():
    """_check_nav_path_arg must deny tilde-prefixed paths (HOME reference)."""
    assert not sg._check_nav_path_arg("~/workspace", WS), (
        "_check_nav_path_arg('~/workspace', ws_root) must return False"
    )
