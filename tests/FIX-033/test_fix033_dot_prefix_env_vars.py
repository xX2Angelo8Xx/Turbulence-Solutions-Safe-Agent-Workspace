"""FIX-033 — Tests for dot-prefix paths and $env: variable assignments in project.

Verifies that:
1. Single-segment dot-prefix paths (.venv, .env, .gitignore) are allowed
   when they resolve inside the project folder via project-folder fallback.
2. Dot-prefix paths outside the project folder are denied.
3. Deny-zone dot names (.github, .vscode) are still denied.
4. $env:VAR = 'value' assignments are allowed when value is inside project folder.
5. $env:VAR = 'value' assignments are denied when value is outside project folder.
6. $env: with deny-zone values are denied.
7. Redirect targets that are dot-prefix names work correctly.
8. Regression: FIX-023 python -m venv .venv still passes.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "coding"
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


# Workspace root used in all tests
WS = "c:/workspace"


def allow(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "allow"


def deny(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# 1. Dot-prefix single-segment paths — allowed via project fallback
# ---------------------------------------------------------------------------

def test_ls_dot_venv_allowed(sg):
    """TST-4100: ls .venv must be allowed (project-folder fallback)."""
    assert allow(sg, "ls .venv")


def test_cat_dot_gitignore_allowed(sg):
    """TST-4101: cat .gitignore must be allowed (project-folder fallback)."""
    assert allow(sg, "cat .gitignore")


def test_cat_dot_env_allowed(sg):
    """TST-4102: cat .env must be allowed (project-folder fallback)."""
    assert allow(sg, "cat .env")


def test_cat_dot_editorconfig_allowed(sg):
    """TST-4103: cat .editorconfig must be allowed (project-folder fallback)."""
    assert allow(sg, "cat .editorconfig")


def test_get_content_dot_env_allowed(sg):
    """TST-4104: Get-Content .env must be allowed (project-folder fallback)."""
    assert allow(sg, "Get-Content .env")


def test_get_childitem_dot_venv_allowed(sg):
    """TST-4105: Get-ChildItem .venv must be allowed (project-folder fallback)."""
    assert allow(sg, "Get-ChildItem .venv")


def test_ls_dot_nvmrc_allowed(sg):
    """TST-4106: ls .nvmrc must be allowed (project dot-prefix file)."""
    assert allow(sg, "ls .nvmrc")


# ---------------------------------------------------------------------------
# 2. Dot-prefix paths with project/ prefix — allowed directly
# ---------------------------------------------------------------------------

def test_ls_project_dot_venv_allowed(sg):
    """TST-4107: ls project/.venv must be allowed (direct zone check)."""
    assert allow(sg, "ls project/.venv")


def test_cat_project_dot_gitignore_allowed(sg):
    """TST-4108: cat project/.gitignore must be allowed."""
    assert allow(sg, "cat project/.gitignore")


def test_cat_project_dot_env_allowed(sg):
    """TST-4109: cat project/.env must be allowed."""
    assert allow(sg, "cat project/.env")


# ---------------------------------------------------------------------------
# 3. Deny-zone dot names — still denied
# ---------------------------------------------------------------------------

def test_ls_dot_github_denied(sg):
    """TST-4110: ls .github must be denied (deny zone)."""
    assert deny(sg, "ls .github")


def test_ls_dot_vscode_denied(sg):
    """TST-4111: ls .vscode must be denied (deny zone)."""
    assert deny(sg, "ls .vscode")


def test_cat_dot_github_file_denied(sg):
    """TST-4112: cat .github/instructions/copilot-instructions.md must be denied."""
    assert deny(sg, "cat .github/instructions/copilot-instructions.md")


# ---------------------------------------------------------------------------
# 4. python -m venv .venv — regression (FIX-023)
# ---------------------------------------------------------------------------

def test_venv_dot_venv_allowed_regression(sg):
    """TST-4113: python -m venv .venv must be allowed (FIX-023 regression)."""
    assert allow(sg, "python -m venv .venv")


def test_venv_project_dot_venv_allowed_regression(sg):
    """TST-4114: python -m venv project/.venv must be allowed."""
    assert allow(sg, "python -m venv project/.venv")


# ---------------------------------------------------------------------------
# 5. $env: variable assignments — value inside project folder
# ---------------------------------------------------------------------------

def test_env_assign_relative_project_path_allowed(sg):
    """TST-4115: $env:VIRTUAL_ENV = 'project/.venv' must be allowed."""
    assert allow(sg, "$env:VIRTUAL_ENV = 'project/.venv'")


def test_env_assign_absolute_project_path_allowed(sg):
    """TST-4116: $env:VIRTUAL_ENV = 'c:/workspace/project/.venv' must be allowed."""
    assert allow(sg, "$env:VIRTUAL_ENV = 'c:/workspace/project/.venv'")


def test_env_assign_dot_venv_allowed(sg):
    """TST-4117: $env:VIRTUAL_ENV = '.venv' must be allowed via project fallback."""
    assert allow(sg, "$env:VIRTUAL_ENV = '.venv'")


def test_env_assign_project_src_allowed(sg):
    """TST-4118: $env:MY_VAR = 'project/src' must be allowed."""
    assert allow(sg, "$env:MY_VAR = 'project/src'")


# ---------------------------------------------------------------------------
# 6. $env: variable assignments — value outside project folder (deny)
# ---------------------------------------------------------------------------

def test_env_assign_dot_github_denied(sg):
    """TST-4119: $env:VIRTUAL_ENV = '.github' must be denied (deny zone)."""
    assert deny(sg, "$env:VIRTUAL_ENV = '.github'")


def test_env_assign_dot_vscode_denied(sg):
    """TST-4120: $env:VIRTUAL_ENV = '.vscode' must be denied (deny zone)."""
    assert deny(sg, "$env:VIRTUAL_ENV = '.vscode'")


def test_env_assign_noagentzone_denied(sg):
    """TST-4121: $env:VIRTUAL_ENV = 'noagentzone' must be denied."""
    assert deny(sg, "$env:VIRTUAL_ENV = 'noagentzone'")


def test_env_assign_absolute_etc_denied(sg):
    """TST-4122: $env:HOME = '/etc/passwd' must be denied (outside workspace)."""
    assert deny(sg, "$env:HOME = '/etc/passwd'")


def test_env_assign_absolute_c_root_denied(sg):
    """TST-4123: $env:PATH = 'c:/windows/system32' must be denied."""
    assert deny(sg, "$env:PATH = 'c:/windows/system32'")


def test_env_assign_nested_dollar_denied(sg):
    """TST-4124: $env:VIRTUAL_ENV = '$env:OTHER' must be denied (nested $)."""
    assert deny(sg, "$env:VIRTUAL_ENV = '$env:OTHER'")


def test_env_assign_no_equals_denied(sg):
    """TST-4125: bare $env:VIRTUAL_ENV (no assignment) must be denied."""
    assert deny(sg, "$env:VIRTUAL_ENV")


def test_env_assign_wrong_order_denied(sg):
    """TST-4126: 'project/.venv' = $env:VAR (value on left) must be denied."""
    assert deny(sg, "'project/.venv' = $env:VIRTUAL_ENV")


# ---------------------------------------------------------------------------
# 7. Redirect targets that are dot-prefix names
# ---------------------------------------------------------------------------

def test_redirect_gt_dot_env_allowed(sg):
    """TST-4127: echo test > .env must be allowed (project fallback for redirect)."""
    assert allow(sg, "echo test > .env")


def test_redirect_gt_dot_gitignore_allowed(sg):
    """TST-4128: echo '# comment' > .gitignore must be allowed."""
    assert allow(sg, "echo '# comment' > .gitignore")


def test_redirect_gt_dot_github_file_denied(sg):
    """TST-4129: echo test > .github/file must be denied."""
    assert deny(sg, "echo test > .github/file")


# ---------------------------------------------------------------------------
# 8. Edge cases
# ---------------------------------------------------------------------------

def test_dot_venv_denied_outside_project_absolute(sg):
    """TST-4130: cat c:/workspace/.venv must be denied (workspace root level)."""
    assert deny(sg, "cat c:/workspace/.venv")


def test_dot_env_in_deny_zone_denied(sg):
    """TST-4131: cat .vscode/.env must be denied (inside deny zone)."""
    assert deny(sg, "cat .vscode/.env")


def test_rm_dot_env_fallback_not_allowed(sg):
    """TST-4132: rm .env must be denied — rm verb not in _PROJECT_FALLBACK_VERBS."""
    assert deny(sg, "rm .env")


def test_env_assign_uppercase_var_name_allowed(sg):
    """TST-4133: $env:VIRTUAL_ENV (uppercase) with project path must be allowed."""
    assert allow(sg, "$env:VIRTUAL_ENV = 'project/.venv'")


def test_env_assign_double_quoted_value_allowed(sg):
    """TST-4134: $env:VIRTUAL_ENV = \"project/.venv\" (double quotes) must be allowed."""
    assert allow(sg, '$env:VIRTUAL_ENV = "project/.venv"')


def test_env_assign_dot_venv_nested_path_allowed(sg):
    """TST-4135: cat project/.venv/pyvenv.cfg must be allowed."""
    assert allow(sg, "cat project/.venv/pyvenv.cfg")
