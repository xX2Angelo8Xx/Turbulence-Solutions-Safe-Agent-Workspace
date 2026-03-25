"""SAF-014 — Tests for expanded terminal allowlist: read-only file inspection commands.

Verifies that the following commands are allowed when targeting the project folder
and denied when targeting restricted zones or root-level files:
  get-content, gc, select-string, findstr, grep, wc, file, stat
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
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
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# Workspace root used in all tests
WS = "c:/workspace"

# Path inside the project folder — always allowed
PROJECT_PATH = "project/src/main.py"

# Paths that target restricted zones — always denied
GITHUB_PATH = ".github/hooks/scripts/security_gate.py"
VSCODE_PATH = ".vscode/settings.json"
# Root-level file — reference as ./ so the path-detection logic triggers zone check
ROOT_FILE = "./root_config.json"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def allow(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "allow"


def deny(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# 1. get-content
# ---------------------------------------------------------------------------

def test_get_content_project_folder_allowed(sg):
    """get-content targeting project folder must be allowed."""
    assert allow(sg, f"get-content {PROJECT_PATH}")


def test_get_content_github_denied(sg):
    """get-content targeting .github/ must be denied."""
    assert deny(sg, f"get-content {GITHUB_PATH}")


def test_get_content_vscode_denied(sg):
    """get-content targeting .vscode/ must be denied."""
    assert deny(sg, f"get-content {VSCODE_PATH}")


def test_get_content_root_file_denied(sg):
    """get-content targeting a root-level file (outside project) must be denied."""
    assert deny(sg, f"get-content {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 2. gc (alias for Get-Content)
# ---------------------------------------------------------------------------

def test_gc_project_folder_allowed(sg):
    """gc (Get-Content alias) targeting project folder must be allowed."""
    assert allow(sg, f"gc {PROJECT_PATH}")


def test_gc_github_denied(sg):
    """gc targeting .github/ must be denied."""
    assert deny(sg, f"gc {GITHUB_PATH}")


def test_gc_vscode_denied(sg):
    """gc targeting .vscode/ must be denied."""
    assert deny(sg, f"gc {VSCODE_PATH}")


def test_gc_root_file_denied(sg):
    """gc targeting a root-level file must be denied."""
    assert deny(sg, f"gc {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 3. Alias parity — gc and get-content behave identically
# ---------------------------------------------------------------------------

def test_gc_and_get_content_same_allow(sg):
    """gc and get-content must both allow the same project-folder path."""
    r1 = sg.sanitize_terminal_command(f"get-content {PROJECT_PATH}", WS)
    r2 = sg.sanitize_terminal_command(f"gc {PROJECT_PATH}", WS)
    assert r1 == r2


def test_gc_and_get_content_same_deny(sg):
    """gc and get-content must both deny the same .github path."""
    r1 = sg.sanitize_terminal_command(f"get-content {GITHUB_PATH}", WS)
    r2 = sg.sanitize_terminal_command(f"gc {GITHUB_PATH}", WS)
    assert r1[0] == r2[0] == "deny"


# ---------------------------------------------------------------------------
# 4. select-string
# ---------------------------------------------------------------------------

def test_select_string_project_folder_allowed(sg):
    """select-string targeting project folder must be allowed."""
    assert allow(sg, f"select-string pattern {PROJECT_PATH}")


def test_select_string_github_denied(sg):
    """select-string targeting .github/ must be denied."""
    assert deny(sg, f"select-string pattern {GITHUB_PATH}")


def test_select_string_vscode_denied(sg):
    """select-string targeting .vscode/ must be denied."""
    assert deny(sg, f"select-string pattern {VSCODE_PATH}")


def test_select_string_root_file_denied(sg):
    """select-string targeting a root-level file must be denied."""
    assert deny(sg, f"select-string pattern {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 5. findstr
# ---------------------------------------------------------------------------

def test_findstr_project_folder_allowed(sg):
    """findstr targeting project folder must be allowed."""
    assert allow(sg, f"findstr pattern {PROJECT_PATH}")


def test_findstr_github_denied(sg):
    """findstr targeting .github/ must be denied."""
    assert deny(sg, f"findstr pattern {GITHUB_PATH}")


def test_findstr_vscode_denied(sg):
    """findstr targeting .vscode/ must be denied."""
    assert deny(sg, f"findstr pattern {VSCODE_PATH}")


def test_findstr_root_file_denied(sg):
    """findstr targeting a root-level file must be denied."""
    assert deny(sg, f"findstr pattern {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 6. grep
# ---------------------------------------------------------------------------

def test_grep_project_folder_allowed(sg):
    """grep targeting project folder must be allowed."""
    assert allow(sg, f"grep pattern {PROJECT_PATH}")


def test_grep_github_denied(sg):
    """grep targeting .github/ must be denied."""
    assert deny(sg, f"grep pattern {GITHUB_PATH}")


def test_grep_vscode_denied(sg):
    """grep targeting .vscode/ must be denied."""
    assert deny(sg, f"grep pattern {VSCODE_PATH}")


def test_grep_root_file_denied(sg):
    """grep targeting root-level file must be denied."""
    assert deny(sg, f"grep pattern {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 7. wc
# ---------------------------------------------------------------------------

def test_wc_project_folder_allowed(sg):
    """wc targeting project folder must be allowed."""
    assert allow(sg, f"wc {PROJECT_PATH}")


def test_wc_github_denied(sg):
    """wc targeting .github/ must be denied."""
    assert deny(sg, f"wc {GITHUB_PATH}")


def test_wc_vscode_denied(sg):
    """wc targeting .vscode/ must be denied."""
    assert deny(sg, f"wc {VSCODE_PATH}")


def test_wc_root_file_denied(sg):
    """wc targeting a root-level file must be denied."""
    assert deny(sg, f"wc {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 8. file
# ---------------------------------------------------------------------------

def test_file_project_folder_allowed(sg):
    """file targeting project folder must be allowed."""
    assert allow(sg, f"file {PROJECT_PATH}")


def test_file_github_denied(sg):
    """file targeting .github/ must be denied."""
    assert deny(sg, f"file {GITHUB_PATH}")


def test_file_vscode_denied(sg):
    """file targeting .vscode/ must be denied."""
    assert deny(sg, f"file {VSCODE_PATH}")


def test_file_root_file_denied(sg):
    """file targeting root-level file must be denied."""
    assert deny(sg, f"file {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 9. stat
# ---------------------------------------------------------------------------

def test_stat_project_folder_allowed(sg):
    """stat targeting project folder must be allowed."""
    assert allow(sg, f"stat {PROJECT_PATH}")


def test_stat_github_denied(sg):
    """stat targeting .github/ must be denied."""
    assert deny(sg, f"stat {GITHUB_PATH}")


def test_stat_vscode_denied(sg):
    """stat targeting .vscode/ must be denied."""
    assert deny(sg, f"stat {VSCODE_PATH}")


def test_stat_root_file_denied(sg):
    """stat targeting root-level file must be denied."""
    assert deny(sg, f"stat {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 10. Mixed paths — one inside project, one outside → deny
# ---------------------------------------------------------------------------

def test_get_content_mixed_paths_denied(sg):
    """get-content with a project path and a .github path must be denied."""
    assert deny(sg, f"get-content {PROJECT_PATH} {GITHUB_PATH}")


def test_grep_mixed_paths_denied(sg):
    """grep with a project path and a .vscode path must be denied."""
    assert deny(sg, f"grep pattern {PROJECT_PATH} {VSCODE_PATH}")


def test_wc_mixed_paths_denied(sg):
    """wc with project path and root file must be denied."""
    assert deny(sg, f"wc {PROJECT_PATH} {ROOT_FILE}")


def test_stat_mixed_paths_denied(sg):
    """stat with project path and .github path must be denied."""
    assert deny(sg, f"stat {PROJECT_PATH} {GITHUB_PATH}")


# ---------------------------------------------------------------------------
# 11. Case-insensitive verb matching (PowerShell verbs are case-insensitive)
# ---------------------------------------------------------------------------

def test_get_content_uppercase_allowed(sg):
    """Get-Content (mixed case as used in PowerShell) must be allowed."""
    assert allow(sg, f"Get-Content {PROJECT_PATH}")


def test_select_string_titlecase_allowed(sg):
    """Select-String (title case) targeting project folder must be allowed."""
    assert allow(sg, f"Select-String pattern {PROJECT_PATH}")


def test_gc_uppercase_allowed(sg):
    """GC (uppercase alias) targeting project folder must be allowed."""
    assert allow(sg, f"GC {PROJECT_PATH}")


# ---------------------------------------------------------------------------
# 12. AllowList structure verification
# ---------------------------------------------------------------------------

def test_all_new_commands_in_allowlist(sg):
    """All 8 SAF-014 commands must be present in _COMMAND_ALLOWLIST."""
    new_commands = {
        "get-content", "gc", "select-string", "findstr",
        "grep", "wc", "file", "stat",
    }
    for cmd in new_commands:
        assert cmd in sg._COMMAND_ALLOWLIST, f"Missing from allowlist: {cmd}"


def test_all_new_commands_path_args_restricted(sg):
    """All 8 SAF-014 commands must have path_args_restricted=True."""
    new_commands = {
        "get-content", "gc", "select-string", "findstr",
        "grep", "wc", "file", "stat",
    }
    for cmd in new_commands:
        rule = sg._COMMAND_ALLOWLIST[cmd]
        assert rule.path_args_restricted is True, (
            f"{cmd}: expected path_args_restricted=True, got {rule.path_args_restricted}"
        )


def test_all_new_commands_allow_arbitrary_paths_false(sg):
    """All 8 SAF-014 commands must have allow_arbitrary_paths=False."""
    new_commands = {
        "get-content", "gc", "select-string", "findstr",
        "grep", "wc", "file", "stat",
    }
    for cmd in new_commands:
        rule = sg._COMMAND_ALLOWLIST[cmd]
        assert rule.allow_arbitrary_paths is False, (
            f"{cmd}: expected allow_arbitrary_paths=False, got {rule.allow_arbitrary_paths}"
        )


# ---------------------------------------------------------------------------
# 13. Templates file sync verification
# ---------------------------------------------------------------------------

def test_templates_security_gate_has_new_commands():
    """templates/coding security_gate.py must contain all 8 SAF-014 commands."""
    templates_gate = (
        Path(__file__).parents[2]
        / "templates"
        / "agent-workbench"
        / ".github"
        / "hooks"
        / "scripts"
        / "security_gate.py"
    )
    content = templates_gate.read_text(encoding="utf-8")
    new_commands = [
        '"get-content"', '"gc"', '"select-string"',
        '"findstr"', '"grep"', '"wc"', '"file"', '"stat"',
    ]
    for cmd in new_commands:
        assert cmd in content, (
            f"templates/coding security_gate.py is missing allowlist entry: {cmd}"
        )
