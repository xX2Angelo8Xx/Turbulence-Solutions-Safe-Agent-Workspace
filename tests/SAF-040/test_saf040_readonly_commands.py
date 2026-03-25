"""tests/SAF-040/test_saf040_readonly_commands.py

Tests for SAF-040: read-only commands added to the terminal allowlist.

Verifies that the following commands are allowed when targeting the project
folder and denied when targeting restricted zones or outside the project:
  diff, fc, comp, sort, uniq, awk, sed

Also verifies regression: pre-existing more/less continue to work.
"""
from __future__ import annotations

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
PROJECT_FILE = "project/src/file.txt"
PROJECT_FILE_2 = "project/src/other.txt"

# Paths outside the project folder — always denied
GITHUB_PATH = ".github/hooks/scripts/security_gate.py"
VSCODE_PATH = ".vscode/settings.json"
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
# 1. diff
# ---------------------------------------------------------------------------

def test_diff_project_allowed(sg):
    """diff comparing two project-folder files must be allowed."""
    assert allow(sg, f"diff {PROJECT_FILE} {PROJECT_FILE_2}")


def test_diff_github_denied(sg):
    """diff targeting .github/ must be denied."""
    assert deny(sg, f"diff {PROJECT_FILE} {GITHUB_PATH}")


def test_diff_vscode_denied(sg):
    """diff targeting .vscode/ must be denied."""
    assert deny(sg, f"diff {PROJECT_FILE} {VSCODE_PATH}")


def test_diff_root_file_denied(sg):
    """diff targeting a root-level file outside the project must be denied."""
    assert deny(sg, f"diff {ROOT_FILE} {PROJECT_FILE}")


# ---------------------------------------------------------------------------
# 2. fc (Windows file compare)
# ---------------------------------------------------------------------------

def test_fc_project_allowed(sg):
    """fc comparing two project-folder files must be allowed."""
    assert allow(sg, f"fc {PROJECT_FILE} {PROJECT_FILE_2}")


def test_fc_github_denied(sg):
    """fc targeting .github/ must be denied."""
    assert deny(sg, f"fc {PROJECT_FILE} {GITHUB_PATH}")


def test_fc_vscode_denied(sg):
    """fc targeting .vscode/ must be denied."""
    assert deny(sg, f"fc {PROJECT_FILE} {VSCODE_PATH}")


def test_fc_root_file_denied(sg):
    """fc targeting a root-level file outside the project must be denied."""
    assert deny(sg, f"fc {ROOT_FILE} {PROJECT_FILE}")


# ---------------------------------------------------------------------------
# 3. comp (Windows binary compare)
# ---------------------------------------------------------------------------

def test_comp_project_allowed(sg):
    """comp comparing two project-folder files must be allowed."""
    assert allow(sg, f"comp {PROJECT_FILE} {PROJECT_FILE_2}")


def test_comp_github_denied(sg):
    """comp targeting .github/ must be denied."""
    assert deny(sg, f"comp {PROJECT_FILE} {GITHUB_PATH}")


def test_comp_vscode_denied(sg):
    """comp targeting .vscode/ must be denied."""
    assert deny(sg, f"comp {PROJECT_FILE} {VSCODE_PATH}")


def test_comp_root_file_denied(sg):
    """comp targeting a root-level file must be denied."""
    assert deny(sg, f"comp {ROOT_FILE} {PROJECT_FILE}")


# ---------------------------------------------------------------------------
# 4. sort
# ---------------------------------------------------------------------------

def test_sort_project_allowed(sg):
    """sort with a project-folder file argument must be allowed."""
    assert allow(sg, f"sort {PROJECT_FILE}")


def test_sort_github_denied(sg):
    """sort targeting .github/ must be denied."""
    assert deny(sg, f"sort {GITHUB_PATH}")


def test_sort_vscode_denied(sg):
    """sort targeting .vscode/ must be denied."""
    assert deny(sg, f"sort {VSCODE_PATH}")


def test_sort_root_file_denied(sg):
    """sort targeting a root-level file must be denied."""
    assert deny(sg, f"sort {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 5. uniq
# ---------------------------------------------------------------------------

def test_uniq_project_allowed(sg):
    """uniq with a project-folder file argument must be allowed."""
    assert allow(sg, f"uniq {PROJECT_FILE}")


def test_uniq_github_denied(sg):
    """uniq targeting .github/ must be denied."""
    assert deny(sg, f"uniq {GITHUB_PATH}")


def test_uniq_vscode_denied(sg):
    """uniq targeting .vscode/ must be denied."""
    assert deny(sg, f"uniq {VSCODE_PATH}")


def test_uniq_root_file_denied(sg):
    """uniq targeting a root-level file must be denied."""
    assert deny(sg, f"uniq {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 6. awk
# ---------------------------------------------------------------------------

def test_awk_project_allowed(sg):
    """awk with a project-folder file argument must be allowed."""
    assert allow(sg, f"awk 'NR==1' {PROJECT_FILE}")


def test_awk_github_denied(sg):
    """awk targeting .github/ must be denied."""
    assert deny(sg, f"awk 'NR==1' {GITHUB_PATH}")


def test_awk_vscode_denied(sg):
    """awk targeting .vscode/ must be denied."""
    assert deny(sg, f"awk 'NR==1' {VSCODE_PATH}")


def test_awk_root_file_denied(sg):
    """awk targeting a root-level file must be denied."""
    assert deny(sg, f"awk 'NR==1' {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 7. sed
# ---------------------------------------------------------------------------

def test_sed_project_allowed(sg):
    """sed with a project-folder file argument must be allowed."""
    assert allow(sg, f"sed -n '1p' {PROJECT_FILE}")


def test_sed_github_denied(sg):
    """sed targeting .github/ must be denied."""
    assert deny(sg, f"sed -n '1p' {GITHUB_PATH}")


def test_sed_vscode_denied(sg):
    """sed targeting .vscode/ must be denied."""
    assert deny(sg, f"sed -n '1p' {VSCODE_PATH}")


def test_sed_root_file_denied(sg):
    """sed targeting a root-level file must be denied."""
    assert deny(sg, f"sed -n '1p' {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 8. Regression — more and less (pre-existing Category G entries)
# ---------------------------------------------------------------------------

def test_more_project_allowed(sg):
    """more targeting a project-folder file must still be allowed (regression)."""
    assert allow(sg, f"more {PROJECT_FILE}")


def test_more_github_denied(sg):
    """more targeting .github/ must be denied (regression)."""
    assert deny(sg, f"more {GITHUB_PATH}")


def test_less_project_allowed(sg):
    """less targeting a project-folder file must still be allowed (regression)."""
    assert allow(sg, f"less {PROJECT_FILE}")


def test_less_github_denied(sg):
    """less targeting .github/ must be denied (regression)."""
    assert deny(sg, f"less {GITHUB_PATH}")


# ---------------------------------------------------------------------------
# 9. Piped usage — no path args → allowed (stdin pipe, no zone risk)
# ---------------------------------------------------------------------------

def test_sort_no_path_args_piped(sg):
    """sort with no file path arguments (piped from stdin) must be allowed."""
    decision, _ = sg.sanitize_terminal_command("sort", WS)
    # No path args means no restricted paths — should be allow (or ask at most)
    assert decision in ("allow", "ask")


def test_uniq_no_path_args_piped(sg):
    """uniq with no file path arguments (piped from stdin) must be allowed."""
    decision, _ = sg.sanitize_terminal_command("uniq", WS)
    assert decision in ("allow", "ask")


def test_awk_no_path_args_piped(sg):
    """awk with only a program argument and no file (piped) must be allowed."""
    decision, _ = sg.sanitize_terminal_command("awk 'NR==1'", WS)
    assert decision in ("allow", "ask")
