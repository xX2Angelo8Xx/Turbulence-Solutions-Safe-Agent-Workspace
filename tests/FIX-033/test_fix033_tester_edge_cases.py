"""FIX-033 — Tester edge-case tests.

Tests beyond the Developer's suite, focusing on:
- Path-traversal attacks via $env: value
- Empty / degenerate path args (.'', '..', '.')
- Double-dot traversal inside env value
- Chained commands mixing allowed and denied segments
- Env var name doesn't matter — only the value is zone-checked
- Absolute workspace-root (not project) path → DENY
- Standalone redirect with dot-prefix target
- Embedded redirect with dot-prefix target
- Incorrect $env: forms that must still be denied
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "Default-Project"
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
    """Mock detect_project_folder to return 'project' without filesystem access."""
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
# 1. Path-traversal attacks in $env: value
# ---------------------------------------------------------------------------

def test_env_assign_traversal_etc_passwd_denied(sg):
    """TST-4136: $env:VIRTUAL_ENV = '../../etc/passwd' must be denied (path traversal)."""
    assert deny(sg, "$env:VIRTUAL_ENV = '../../etc/passwd'")


def test_env_assign_double_dot_dot_venv_denied(sg):
    """TST-4137: $env:VIRTUAL_ENV = 'project/../../.venv' must be denied (traversal escapes project)."""
    assert deny(sg, "$env:VIRTUAL_ENV = 'project/../../.venv'")


def test_env_assign_traversal_to_dot_github_denied(sg):
    """TST-4138: $env:VIRTUAL_ENV = 'project/../../.github' must be denied (traversal to deny zone)."""
    assert deny(sg, "$env:VIRTUAL_ENV = 'project/../../.github'")


def test_env_assign_dot_dot_value_denied(sg):
    """TST-4139: $env:VIRTUAL_ENV = '..' must be denied (value resolves above workspace)."""
    assert deny(sg, "$env:VIRTUAL_ENV = '..'")


def test_env_assign_absolute_workspace_root_denied(sg):
    """TST-4140: $env:VIRTUAL_ENV = 'c:/workspace' must be denied (workspace root, not project folder)."""
    assert deny(sg, "$env:VIRTUAL_ENV = 'c:/workspace'")


# ---------------------------------------------------------------------------
# 2. Empty / degenerate $env: forms
# ---------------------------------------------------------------------------

def test_env_assign_empty_value_denied(sg):
    """TST-4141: $env:VIRTUAL_ENV = '' must be denied (empty value normalises to '.'/CWD)."""
    assert deny(sg, "$env:VIRTUAL_ENV = ''")


def test_env_assign_only_two_tokens_denied(sg):
    """TST-4142: '$env:A =' (no value token) must be denied (falls through to $-verb guard)."""
    # shlex parsing: ['$env:A', '='] — len(tokens) < 3 → falls through to $ guard
    assert deny(sg, "$env:A =")


def test_env_assign_dot_value_denied(sg):
    """TST-4143: $env:VIRTUAL_ENV = '.' must be denied ('.' resolves to workspace root)."""
    assert deny(sg, "$env:VIRTUAL_ENV = '.'")


# ---------------------------------------------------------------------------
# 3. Path argument edge cases: '.' and '..'
# ---------------------------------------------------------------------------

def test_ls_dot_denied(sg):
    """TST-4144: 'ls .' must be denied ('.' resolves to workspace root, not inside project)."""
    # '.' → normpath('.') = '.' → classify resolves to ws_root → deny
    # project-folder fallback: parts_fb=[] (dot filtered) → no fallback → deny
    assert deny(sg, "ls .")


def test_ls_dot_dot_denied(sg):
    """TST-4145: 'ls ..' must be denied (escapes workspace root)."""
    assert deny(sg, "ls ..")


def test_cat_dot_dot_slash_file_denied(sg):
    """TST-4146: 'cat ../secret.txt' must be denied (traversal above workspace)."""
    assert deny(sg, "cat ../secret.txt")


# ---------------------------------------------------------------------------
# 4. Env var name is irrelevant — only the value is zone-checked
# ---------------------------------------------------------------------------

def test_env_assign_path_var_project_local_allowed(sg):
    """TST-4147: $env:PATH = 'project/scripts' must be allowed (any var name, project-local value)."""
    assert allow(sg, "$env:PATH = 'project/scripts'")


def test_env_assign_arbitrary_var_project_local_allowed(sg):
    """TST-4148: $env:MY_CUSTOM_VAR = 'project/.venv' must be allowed."""
    assert allow(sg, "$env:MY_CUSTOM_VAR = 'project/.venv'")


def test_env_assign_path_var_system_path_denied(sg):
    """TST-4149: $env:PATH = 'c:/windows/system32' must be denied (outside workspace)."""
    assert deny(sg, "$env:PATH = 'c:/windows/system32'")


# ---------------------------------------------------------------------------
# 5. Chained commands: good $env: followed by denied terminal segment
# ---------------------------------------------------------------------------

def test_env_assign_allowed_then_denied_segment_overall_denied(sg):
    """TST-4150: '$env:A = 'project/.venv' && ls .github' must be denied (second segment denied)."""
    assert deny(sg, "$env:A = 'project/.venv' && ls .github")


def test_env_assign_allowed_then_allowed_segment_overall_allowed(sg):
    """TST-4151: '$env:A = 'project/.venv' ; cat .gitignore' must be allowed (both segments pass)."""
    assert allow(sg, "$env:A = 'project/.venv' ; cat .gitignore")


# ---------------------------------------------------------------------------
# 6. Dot-prefix redirect edge cases not covered by developer tests
# ---------------------------------------------------------------------------

def test_redirect_embedded_dot_env_allowed(sg):
    """TST-4152: 'echo content>.env' (no spaces, embedded redirect) must be allowed via project fallback."""
    assert allow(sg, "echo content>.env")


def test_redirect_gt_dot_dot_denied(sg):
    """TST-4153: 'echo test > ..' must be denied (redirect target escapes workspace)."""
    assert deny(sg, "echo test > ..")


def test_redirect_gt_dot_vscode_file_denied(sg):
    """TST-4154: 'echo test > .vscode/settings.json' must be denied (deny zone target)."""
    assert deny(sg, "echo test > .vscode/settings.json")


# ---------------------------------------------------------------------------
# 7. Dot-prefix names that are not in the deny zone — allowed via fallback
# ---------------------------------------------------------------------------

def test_cat_dot_gitconfig_allowed(sg):
    """TST-4155: 'cat .gitconfig' must be allowed (.gitconfig is not in deny zone)."""
    assert allow(sg, "cat .gitconfig")


def test_ls_dot_pytest_cache_allowed(sg):
    """TST-4156: 'ls .pytest_cache' must be allowed (project-local dot-prefix dir)."""
    assert allow(sg, "ls .pytest_cache")


def test_cat_dot_pylintrc_allowed(sg):
    """TST-4157: 'cat .pylintrc' must be allowed (project-level dot-prefix config)."""
    assert allow(sg, "cat .pylintrc")


# ---------------------------------------------------------------------------
# 8. $env: with deny-zone dot-prefix names (defense in depth)
# ---------------------------------------------------------------------------

def test_env_assign_noagentzone_absolute_denied(sg):
    """TST-4158: $env:A = 'c:/workspace/noagentzone' must be denied (absolute deny zone path)."""
    assert deny(sg, "$env:A = 'c:/workspace/noagentzone'")


def test_env_assign_vscode_subpath_denied(sg):
    """TST-4159: $env:A = '.vscode/extensions' must be denied (.vscode is deny zone)."""
    assert deny(sg, "$env:A = '.vscode/extensions'")


def test_env_assign_github_subpath_denied(sg):
    """TST-4160: $env:A = '.github/hooks' must be denied (.github is deny zone)."""
    assert deny(sg, "$env:A = '.github/hooks'")


# ---------------------------------------------------------------------------
# 9. Security: verify the $env: handler does not affect non-env-prefix tokens
# ---------------------------------------------------------------------------

def test_dollar_sign_var_non_env_still_denied(sg):
    """TST-4161: '$MY_VAR = project/.venv' must be denied (not $env: prefix)."""
    assert deny(sg, "$MY_VAR = project/.venv")


def test_env_prefix_no_colon_still_denied(sg):
    """TST-4162: '$envVAR = project/.venv' must be denied (no colon, not $env: form)."""
    assert deny(sg, "$envVAR = project/.venv")
