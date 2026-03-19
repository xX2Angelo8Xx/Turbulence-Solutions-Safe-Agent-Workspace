"""SAF-016 — Tests for expanded terminal allowlist: delete commands.

Verifies that the following commands are allowed when targeting the project
folder and denied when targeting restricted zones or root-level files:
  remove-item, ri, rm, del, erase, rmdir

Also verifies these commands have been removed from _EXPLICIT_DENY_PATTERNS
so they are no longer hard-denied before zone checking.
"""
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
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# Workspace root used in all tests
WS = "c:/workspace"

# Path inside the project folder — always allowed
PROJECT_PATH = "project/src/output.txt"
PROJECT_DIR = "project/src/tmpdir"

# Paths that target restricted zones — always denied
GITHUB_PATH = ".github/hooks/scripts/security_gate.py"
VSCODE_PATH = ".vscode/settings.json"
NOAGENT_PATH = "NoAgentZone/secret.txt"
# Root-level file — ./ prefix triggers zone check
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
# 1. remove-item
# ---------------------------------------------------------------------------

def test_remove_item_project_folder_allowed(sg):
    """remove-item targeting project folder must be allowed."""
    assert allow(sg, f"remove-item {PROJECT_PATH}")


def test_remove_item_github_denied(sg):
    """remove-item targeting .github/ must be denied."""
    assert deny(sg, f"remove-item {GITHUB_PATH}")


def test_remove_item_vscode_denied(sg):
    """remove-item targeting .vscode/ must be denied."""
    assert deny(sg, f"remove-item {VSCODE_PATH}")


def test_remove_item_noagentzone_denied(sg):
    """remove-item targeting NoAgentZone/ must be denied."""
    assert deny(sg, f"remove-item {NOAGENT_PATH}")


def test_remove_item_root_file_denied(sg):
    """remove-item targeting a root-level file must be denied."""
    assert deny(sg, f"remove-item {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 2. ri (alias for Remove-Item)
# ---------------------------------------------------------------------------

def test_ri_project_folder_allowed(sg):
    """ri (Remove-Item alias) targeting project folder must be allowed."""
    assert allow(sg, f"ri {PROJECT_PATH}")


def test_ri_github_denied(sg):
    """ri targeting .github/ must be denied."""
    assert deny(sg, f"ri {GITHUB_PATH}")


def test_ri_vscode_denied(sg):
    """ri targeting .vscode/ must be denied."""
    assert deny(sg, f"ri {VSCODE_PATH}")


def test_ri_root_file_denied(sg):
    """ri targeting a root-level file must be denied."""
    assert deny(sg, f"ri {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 3. Alias parity — ri and remove-item behave identically
# ---------------------------------------------------------------------------

def test_ri_and_remove_item_same_allow(sg):
    """ri and remove-item must both allow the same project-folder path."""
    r1 = sg.sanitize_terminal_command(f"remove-item {PROJECT_PATH}", WS)
    r2 = sg.sanitize_terminal_command(f"ri {PROJECT_PATH}", WS)
    assert r1[0] == r2[0] == "allow"


def test_ri_and_remove_item_same_deny(sg):
    """ri and remove-item must both deny the same .github path."""
    r1 = sg.sanitize_terminal_command(f"remove-item {GITHUB_PATH}", WS)
    r2 = sg.sanitize_terminal_command(f"ri {GITHUB_PATH}", WS)
    assert r1[0] == r2[0] == "deny"


# ---------------------------------------------------------------------------
# 4. rm
# ---------------------------------------------------------------------------

def test_rm_project_folder_allowed(sg):
    """rm targeting project folder must be allowed."""
    assert allow(sg, f"rm {PROJECT_PATH}")


def test_rm_github_denied(sg):
    """rm targeting .github/ must be denied."""
    assert deny(sg, f"rm {GITHUB_PATH}")


def test_rm_vscode_denied(sg):
    """rm targeting .vscode/ must be denied."""
    assert deny(sg, f"rm {VSCODE_PATH}")


def test_rm_root_file_denied(sg):
    """rm targeting a root-level file must be denied."""
    assert deny(sg, f"rm {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 5. del
# ---------------------------------------------------------------------------

def test_del_project_folder_allowed(sg):
    """del targeting project folder must be allowed."""
    assert allow(sg, f"del {PROJECT_PATH}")


def test_del_github_denied(sg):
    """del targeting .github/ must be denied."""
    assert deny(sg, f"del {GITHUB_PATH}")


def test_del_vscode_denied(sg):
    """del targeting .vscode/ must be denied."""
    assert deny(sg, f"del {VSCODE_PATH}")


def test_del_root_file_denied(sg):
    """del targeting a root-level file must be denied."""
    assert deny(sg, f"del {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 6. erase
# ---------------------------------------------------------------------------

def test_erase_project_folder_allowed(sg):
    """erase targeting project folder must be allowed."""
    assert allow(sg, f"erase {PROJECT_PATH}")


def test_erase_github_denied(sg):
    """erase targeting .github/ must be denied."""
    assert deny(sg, f"erase {GITHUB_PATH}")


def test_erase_vscode_denied(sg):
    """erase targeting .vscode/ must be denied."""
    assert deny(sg, f"erase {VSCODE_PATH}")


def test_erase_root_file_denied(sg):
    """erase targeting a root-level file must be denied."""
    assert deny(sg, f"erase {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 7. rmdir
# ---------------------------------------------------------------------------

def test_rmdir_project_dir_allowed(sg):
    """rmdir targeting project directory must be allowed."""
    assert allow(sg, f"rmdir {PROJECT_DIR}")


def test_rmdir_github_denied(sg):
    """rmdir targeting .github/ must be denied."""
    assert deny(sg, f"rmdir {GITHUB_PATH}")


def test_rmdir_vscode_denied(sg):
    """rmdir targeting .vscode/ must be denied."""
    assert deny(sg, f"rmdir {VSCODE_PATH}")


def test_rmdir_root_denied(sg):
    """rmdir targeting a root-level path must be denied."""
    assert deny(sg, f"rmdir {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 8. Verify commands are IN the allowlist (not falling through to deny)
# ---------------------------------------------------------------------------

def test_remove_item_in_allowlist(sg):
    """remove-item must be present in _COMMAND_ALLOWLIST."""
    assert "remove-item" in sg._COMMAND_ALLOWLIST


def test_ri_in_allowlist(sg):
    """ri must be present in _COMMAND_ALLOWLIST."""
    assert "ri" in sg._COMMAND_ALLOWLIST


def test_rm_in_allowlist(sg):
    """rm must be present in _COMMAND_ALLOWLIST."""
    assert "rm" in sg._COMMAND_ALLOWLIST


def test_del_in_allowlist(sg):
    """del must be present in _COMMAND_ALLOWLIST."""
    assert "del" in sg._COMMAND_ALLOWLIST


def test_erase_in_allowlist(sg):
    """erase must be present in _COMMAND_ALLOWLIST."""
    assert "erase" in sg._COMMAND_ALLOWLIST


def test_rmdir_in_allowlist(sg):
    """rmdir must be present in _COMMAND_ALLOWLIST."""
    assert "rmdir" in sg._COMMAND_ALLOWLIST


# ---------------------------------------------------------------------------
# 9. Verify delete commands are NOT in _EXPLICIT_DENY_PATTERNS
# ---------------------------------------------------------------------------

def test_rm_not_in_explicit_deny(sg):
    """rm must NOT appear as a pattern in _EXPLICIT_DENY_PATTERNS."""
    deny_patterns_src = [p.pattern for p in sg._EXPLICIT_DENY_PATTERNS]
    assert not any("\\brm" in p for p in deny_patterns_src), (
        "rm found in _EXPLICIT_DENY_PATTERNS — must be removed (SAF-016)"
    )


def test_del_not_in_explicit_deny(sg):
    """del must NOT appear as a pattern in _EXPLICIT_DENY_PATTERNS."""
    deny_patterns_src = [p.pattern for p in sg._EXPLICIT_DENY_PATTERNS]
    assert not any("\\bdel" in p for p in deny_patterns_src), (
        "del found in _EXPLICIT_DENY_PATTERNS — must be removed (SAF-016)"
    )


def test_erase_not_in_explicit_deny(sg):
    """erase must NOT appear as a pattern in _EXPLICIT_DENY_PATTERNS."""
    deny_patterns_src = [p.pattern for p in sg._EXPLICIT_DENY_PATTERNS]
    assert not any("\\berase" in p for p in deny_patterns_src), (
        "erase found in _EXPLICIT_DENY_PATTERNS — must be removed (SAF-016)"
    )


def test_rmdir_not_in_explicit_deny(sg):
    """rmdir must NOT appear as a pattern in _EXPLICIT_DENY_PATTERNS."""
    deny_patterns_src = [p.pattern for p in sg._EXPLICIT_DENY_PATTERNS]
    assert not any("\\brmdir" in p for p in deny_patterns_src), (
        "rmdir found in _EXPLICIT_DENY_PATTERNS — must be removed (SAF-016)"
    )


def test_remove_item_not_in_explicit_deny(sg):
    """remove-item must NOT appear as a pattern in _EXPLICIT_DENY_PATTERNS."""
    deny_patterns_src = [p.pattern for p in sg._EXPLICIT_DENY_PATTERNS]
    assert not any("remove-item" in p for p in deny_patterns_src), (
        "remove-item found in _EXPLICIT_DENY_PATTERNS — must be removed (SAF-016)"
    )


def test_ri_not_in_explicit_deny(sg):
    """ri must NOT appear as a pattern in _EXPLICIT_DENY_PATTERNS."""
    deny_patterns_src = [p.pattern for p in sg._EXPLICIT_DENY_PATTERNS]
    assert not any("\\bri\\b" in p for p in deny_patterns_src), (
        "ri found in _EXPLICIT_DENY_PATTERNS — must be removed (SAF-016)"
    )


# ---------------------------------------------------------------------------
# 10. All Category N rules have path_args_restricted=True
# ---------------------------------------------------------------------------

def test_all_category_n_path_args_restricted(sg):
    """Every Category N command must have path_args_restricted=True."""
    category_n = ("remove-item", "ri", "rm", "del", "erase", "rmdir")
    for cmd in category_n:
        rule = sg._COMMAND_ALLOWLIST.get(cmd)
        assert rule is not None, f"{cmd} missing from _COMMAND_ALLOWLIST"
        assert rule.path_args_restricted is True, (
            f"{cmd} must have path_args_restricted=True"
        )
