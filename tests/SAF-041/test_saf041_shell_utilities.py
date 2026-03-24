"""tests/SAF-041/test_saf041_shell_utilities.py

Tests for SAF-041: shell utility commands added to the terminal allowlist.

Verifies that the following commands are allowed when targeting the project
folder and denied when targeting restricted zones or outside the project:
  touch, chmod, ln

For ln: both source and destination path arguments must be zone-checked;
any cross-zone link attempt (either endpoint outside the project folder or
inside a restricted zone) must be denied.
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
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# Workspace root used in all tests
WS = "c:/workspace"

# Path inside the project folder — always allowed
PROJECT_FILE = "project/src/newfile.txt"
PROJECT_FILE_2 = "project/src/link_target.txt"
PROJECT_SCRIPT = "project/scripts/run.sh"

# Restricted zone paths — always denied
GITHUB_PATH = ".github/hooks/scripts/evil.sh"
VSCODE_PATH = ".vscode/settings.json"
NAZ_PATH = "NoAgentZone/secret.txt"

# Path outside the project but not in a named restricted zone
ROOT_FILE = "./root_config.json"
ABSOLUTE_OUTSIDE = "c:/external/other_project/file.txt"


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
# 1. touch
# ---------------------------------------------------------------------------

def test_touch_project_file_allowed(sg):
    """touch creating a file inside the project folder must be allowed."""
    assert allow(sg, f"touch {PROJECT_FILE}")


def test_touch_github_denied(sg):
    """touch targeting .github/ must be denied."""
    assert deny(sg, f"touch {GITHUB_PATH}")


def test_touch_vscode_denied(sg):
    """touch targeting .vscode/ must be denied."""
    assert deny(sg, f"touch {VSCODE_PATH}")


def test_touch_noagentzone_denied(sg):
    """touch targeting NoAgentZone/ must be denied."""
    assert deny(sg, f"touch {NAZ_PATH}")


def test_touch_root_file_denied(sg):
    """touch targeting a root-level file outside the project must be denied."""
    assert deny(sg, f"touch {ROOT_FILE}")


def test_touch_multiple_project_files_allowed(sg):
    """touch with multiple project-folder targets must be allowed."""
    assert allow(sg, f"touch {PROJECT_FILE} {PROJECT_FILE_2}")


def test_touch_mixed_denied(sg):
    """touch where any target is outside the project must be denied."""
    assert deny(sg, f"touch {PROJECT_FILE} {GITHUB_PATH}")


# ---------------------------------------------------------------------------
# 2. chmod
# ---------------------------------------------------------------------------

def test_chmod_project_file_allowed(sg):
    """chmod on a project-folder file must be allowed."""
    assert allow(sg, f"chmod 755 {PROJECT_SCRIPT}")


def test_chmod_github_denied(sg):
    """chmod targeting .github/ must be denied."""
    assert deny(sg, f"chmod 755 {GITHUB_PATH}")


def test_chmod_vscode_denied(sg):
    """chmod targeting .vscode/ must be denied."""
    assert deny(sg, f"chmod 644 {VSCODE_PATH}")


def test_chmod_noagentzone_denied(sg):
    """chmod targeting NoAgentZone/ must be denied."""
    assert deny(sg, f"chmod 600 {NAZ_PATH}")


def test_chmod_root_file_denied(sg):
    """chmod targeting a root-level file outside the project must be denied."""
    assert deny(sg, f"chmod 644 {ROOT_FILE}")


def test_chmod_recursive_project_allowed(sg):
    """chmod -R on a project-folder directory must be allowed."""
    assert allow(sg, "chmod -R 755 project/src")


# ---------------------------------------------------------------------------
# 3. ln
# ---------------------------------------------------------------------------

def test_ln_both_project_allowed(sg):
    """ln with both source and link_name inside project folder must be allowed."""
    assert allow(sg, f"ln {PROJECT_FILE_2} {PROJECT_FILE}")


def test_ln_soft_both_project_allowed(sg):
    """ln -s with both paths inside project folder must be allowed."""
    assert allow(sg, f"ln -s {PROJECT_FILE_2} {PROJECT_FILE}")


def test_ln_source_outside_denied(sg):
    """ln where the source is an absolute path outside the workspace must be denied."""
    assert deny(sg, f"ln {ABSOLUTE_OUTSIDE} {PROJECT_FILE}")


def test_ln_target_github_denied(sg):
    """ln creating a link inside .github/ must be denied (cross-zone bridge)."""
    assert deny(sg, f"ln {PROJECT_FILE_2} {GITHUB_PATH}")


def test_ln_target_vscode_denied(sg):
    """ln creating a link inside .vscode/ must be denied."""
    assert deny(sg, f"ln {PROJECT_FILE_2} {VSCODE_PATH}")


def test_ln_target_noagentzone_denied(sg):
    """ln creating a link inside NoAgentZone/ must be denied."""
    assert deny(sg, f"ln {PROJECT_FILE_2} {NAZ_PATH}")


def test_ln_source_github_denied(sg):
    """ln where the source is in .github/ must be denied."""
    assert deny(sg, f"ln {GITHUB_PATH} {PROJECT_FILE}")


def test_ln_both_outside_denied(sg):
    """ln where both source and target are outside workspace must be denied."""
    assert deny(sg, f"ln {ABSOLUTE_OUTSIDE} c:/external/link.txt")


def test_ln_cross_zone_source_to_github_target_denied(sg):
    """ln bridging from project source to .github/ target must be denied."""
    assert deny(sg, f"ln {PROJECT_FILE_2} {GITHUB_PATH}")


def test_ln_cross_zone_naz_source_to_project_target_denied(sg):
    """ln bridging from NoAgentZone/ source to project target must be denied."""
    assert deny(sg, f"ln {NAZ_PATH} {PROJECT_FILE}")
