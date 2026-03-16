"""SAF-016 Edge-Case Tests — Security and boundary conditions.

Covers scenarios NOT in the primary test suite:
  - Multiple path arguments (ALL must be inside project)
  - Common flags (-r, -rf, -f, -Recurse, /S, /Q)
  - Quoted paths with spaces
  - Variable references in path args denied
  - rm -rf targeting restricted zones denied
  - rmdir with /s /q flags (Windows recursive delete)
  - remove-item -Recurse on project path allowed
  - remove-item -Recurse on restricted path denied
  - case-insensitive verb matching (REMOVE-ITEM, RM, Del)
  - Chain commands: project path allowed + restricted path denied
  - Bypass attempt: rm followed by .github path
"""
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
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


WS = "c:/workspace"
P1 = "project/src/file.txt"
P2 = "project/src/other.txt"
GITHUB = ".github/hooks/evil.txt"
VSCODE = ".vscode/settings.json"
NOAGENT = "NoAgentZone/secret.txt"
ROOT = "./root.txt"


def allow(sg, cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "allow"


def deny(sg, cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# Flags — rm -rf / -r / -f
# ---------------------------------------------------------------------------

def test_rm_rf_project_allowed(sg):
    """rm -rf targeting project folder must be allowed."""
    assert allow(sg, f"rm -rf {P1}")


def test_rm_rf_github_denied(sg):
    """rm -rf targeting .github/ must be denied."""
    assert deny(sg, f"rm -rf {GITHUB}")


def test_rm_rf_vscode_denied(sg):
    """rm -rf targeting .vscode/ must be denied."""
    assert deny(sg, f"rm -rf {VSCODE}")


def test_rm_f_project_allowed(sg):
    """rm -f targeting project file must be allowed."""
    assert allow(sg, f"rm -f {P1}")


def test_rm_r_project_allowed(sg):
    """rm -r targeting project directory must be allowed."""
    assert allow(sg, f"rm -r {P1}")


# ---------------------------------------------------------------------------
# Flags — remove-item -Recurse, -Force
# ---------------------------------------------------------------------------

def test_remove_item_recurse_project_allowed(sg):
    """remove-item -Recurse on project path must be allowed."""
    assert allow(sg, f"remove-item -Recurse {P1}")


def test_remove_item_recurse_github_denied(sg):
    """remove-item -Recurse targeting .github/ must be denied."""
    assert deny(sg, f"remove-item -Recurse {GITHUB}")


def test_remove_item_force_project_allowed(sg):
    """remove-item -Force on project path must be allowed."""
    assert allow(sg, f"remove-item -Force {P1}")


def test_remove_item_recurse_force_github_denied(sg):
    """remove-item -Recurse -Force targeting .github/ must be denied."""
    assert deny(sg, f"remove-item -Recurse -Force {GITHUB}")


# ---------------------------------------------------------------------------
# Flags — rmdir /s /q (Windows recursive delete)
# ---------------------------------------------------------------------------
# Note: Windows-style flags like /s and /q contain a forward slash, which
# makes them look like absolute Unix paths (e.g. "/s") to the zone classifier.
# Under the 2-tier deny-by-default model, "/s" resolves outside the workspace
# and is classified as "deny" — so rmdir /s /q is always blocked.
# Agents must use PowerShell Remove-Item -Recurse instead.

def test_rmdir_s_q_denied(sg):
    """rmdir /s /q is denied because /s looks like an absolute path outside workspace."""
    assert deny(sg, f"rmdir /s /q {P1}")


def test_rmdir_s_github_denied(sg):
    """rmdir /s targeting .github/ must be denied."""
    assert deny(sg, f"rmdir /s {GITHUB}")


# ---------------------------------------------------------------------------
# Variable reference in path args — always deny (runtime unknown)
# ---------------------------------------------------------------------------

def test_rm_variable_path_denied(sg):
    """rm with a variable path arg must be denied."""
    assert deny(sg, "rm $TARGET_PATH")


def test_remove_item_variable_path_denied(sg):
    """remove-item with a variable path arg must be denied."""
    assert deny(sg, "remove-item $HOME/secret")


def test_del_variable_path_denied(sg):
    """del with a variable path arg must be denied."""
    assert deny(sg, "del $APPDATA/file.txt")


# ---------------------------------------------------------------------------
# Quoted paths with spaces
# ---------------------------------------------------------------------------

def test_remove_item_quoted_project_allowed(sg):
    """remove-item with a quoted project path (spaces) must be allowed."""
    assert allow(sg, "remove-item 'project/my docs/file.txt'")


def test_rm_quoted_github_denied(sg):
    """rm with a quoted .github path must be denied."""
    assert deny(sg, "rm '.github/hooks/script.py'")


# ---------------------------------------------------------------------------
# Case-insensitive verb matching
# ---------------------------------------------------------------------------

def test_remove_item_uppercase_allowed(sg):
    """REMOVE-ITEM (all caps) targeting project folder must be allowed."""
    assert allow(sg, f"REMOVE-ITEM {P1}")


def test_rm_uppercase_github_denied(sg):
    """RM (all caps) targeting .github/ must be denied."""
    assert deny(sg, f"RM {GITHUB}")


def test_del_mixed_case_project_allowed(sg):
    """Del (mixed case) targeting project folder must be allowed."""
    assert allow(sg, f"Del {P1}")


# ---------------------------------------------------------------------------
# Chain commands — deny if ANY segment targets restricted zone
# ---------------------------------------------------------------------------

def test_chain_project_then_github_denied(sg):
    """Chain: rm project_path; rm .github path must be denied (github segment)."""
    assert deny(sg, f"rm {P1}; rm {GITHUB}")


def test_chain_two_project_paths_allowed(sg):
    """Chain: rm p1; rm p2 — both inside project — must be allowed."""
    assert allow(sg, f"rm {P1}; rm {P2}")


# ---------------------------------------------------------------------------
# Security bypass attempts
# ---------------------------------------------------------------------------

def test_rm_path_traversal_denied(sg):
    """rm with path traversal attempting to reach .github/ must be denied."""
    assert deny(sg, "rm project/../.github/hooks/security_gate.py")


def test_remove_item_path_traversal_denied(sg):
    """remove-item with traversal to .vscode/ must be denied."""
    assert deny(sg, "remove-item project/../.vscode/settings.json")


def test_del_noagentzone_denied(sg):
    """del targeting NoAgentZone/ must be denied."""
    assert deny(sg, f"del {NOAGENT}")


def test_rmdir_noagentzone_denied(sg):
    """rmdir targeting NoAgentZone/ must be denied."""
    assert deny(sg, f"rmdir {NOAGENT}")


# ---------------------------------------------------------------------------
# Multiple path arguments — ALL must be inside project
# ---------------------------------------------------------------------------

def test_rm_two_project_paths_allowed(sg):
    """rm with two project-folder paths must be allowed."""
    assert allow(sg, f"rm {P1} {P2}")


def test_rm_one_project_one_github_denied(sg):
    """rm with one project path and one .github path must be denied."""
    assert deny(sg, f"rm {P1} {GITHUB}")


def test_del_one_project_one_vscode_denied(sg):
    """del with one project path and one .vscode path must be denied."""
    assert deny(sg, f"del {P1} {VSCODE}")
