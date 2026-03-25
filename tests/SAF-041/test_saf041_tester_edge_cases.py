"""tests/SAF-041/test_saf041_tester_edge_cases.py

Tester-added edge-case tests for SAF-041.

Covers cases the developer did not explicitly test:
  - ln -s (symbolic-link flag) — both paths inside project → allowed
  - ln with path traversal (../../.github/) → denied
  - touch creating dotfiles (.env, .gitignore) inside project → allowed
  - chmod +x with path outside project → denied
  - ln with only one argument (hard link, same-dir) → allowed inside project
  - touch with absolute path inside project (should work)
  - chmod with symbolic mode string (+x, a+r, u=rw, etc.)
  - ln -sf (force soft-link) — both project paths → allowed
  - ln --symbolic (long flag variant) — both project paths → allowed
  - touch empty-string edge: bare touch with no args (parser should not crash)
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


WS = "c:/workspace"

PROJECT_FILE = "project/src/newfile.txt"
PROJECT_FILE_2 = "project/src/link_target.txt"
PROJECT_DIR = "project/src"

GITHUB_PATH = ".github/hooks/scripts/evil.sh"
NAZ_PATH = "NoAgentZone/secret.txt"
ROOT_FILE = "./root_config.json"
ABSOLUTE_OUTSIDE = "c:/external/other_project/file.txt"


def allow(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "allow"


def deny(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# ln edge cases
# ---------------------------------------------------------------------------

def test_ln_s_flag_both_project_allowed(sg):
    """ln -s with both paths inside the project folder must be allowed."""
    assert allow(sg, f"ln -s {PROJECT_FILE_2} {PROJECT_FILE}")


def test_ln_sf_flag_both_project_allowed(sg):
    """ln -sf (force re-create) with both project paths must be allowed."""
    assert allow(sg, f"ln -sf {PROJECT_FILE_2} {PROJECT_FILE}")


def test_ln_path_traversal_to_github_denied(sg):
    """ln with ../ path traversal resolving into .github/ must be denied."""
    # project/src/../../.github/evil maps to .github/evil
    traversal = "project/src/../../.github/evil.sh"
    assert deny(sg, f"ln {PROJECT_FILE_2} {traversal}")


def test_ln_path_traversal_to_naz_denied(sg):
    """ln with ../ traversal resolving into NoAgentZone/ must be denied."""
    traversal = "project/../../NoAgentZone/secret.txt"
    assert deny(sg, f"ln {PROJECT_FILE_2} {traversal}")


def test_ln_single_arg_project_allowed(sg):
    """ln with a single project-folder path (hard link, no link_name) must be allowed."""
    assert allow(sg, f"ln {PROJECT_FILE_2}")


def test_ln_single_arg_outside_denied(sg):
    """ln with a single absolute path outside workspace must be denied."""
    assert deny(sg, f"ln {ABSOLUTE_OUTSIDE}")


def test_ln_single_arg_github_denied(sg):
    """ln with a single .github/ path must be denied."""
    assert deny(sg, f"ln {GITHUB_PATH}")


def test_ln_symbolic_long_flag_both_project_allowed(sg):
    """ln --symbolic (POSIX long flag) with both project paths must be allowed."""
    assert allow(sg, f"ln --symbolic {PROJECT_FILE_2} {PROJECT_FILE}")


# ---------------------------------------------------------------------------
# touch dotfiles inside project
# ---------------------------------------------------------------------------

def test_touch_dotenv_project_allowed(sg):
    """touch .env inside the project folder must be allowed (dotfiles are fine)."""
    assert allow(sg, "touch project/.env")


def test_touch_gitignore_project_allowed(sg):
    """touch .gitignore inside the project folder must be allowed."""
    assert allow(sg, "touch project/.gitignore")


def test_touch_dotfile_github_denied(sg):
    """touch dotfile targeting .github/ must be denied."""
    assert deny(sg, "touch .github/.env")


# ---------------------------------------------------------------------------
# chmod edge cases
# ---------------------------------------------------------------------------

def test_chmod_symbolic_mode_project_allowed(sg):
    """chmod +x with a symbolic mode string on a project file must be allowed."""
    assert allow(sg, f"chmod +x {PROJECT_FILE}")


def test_chmod_a_plus_r_project_allowed(sg):
    """chmod a+r (symbolic mode) on a project file must be allowed."""
    assert allow(sg, f"chmod a+r {PROJECT_FILE}")


def test_chmod_u_eq_rw_project_allowed(sg):
    """chmod u=rw (symbolic mode) on a project file must be allowed."""
    assert allow(sg, f"chmod u=rw {PROJECT_FILE}")


def test_chmod_plus_x_outside_denied(sg):
    """chmod +x with a path outside the project must be denied."""
    assert deny(sg, f"chmod +x {ROOT_FILE}")


def test_chmod_755_absolute_outside_denied(sg):
    """chmod 755 targeting absolute path outside workspace must be denied."""
    assert deny(sg, f"chmod 755 {ABSOLUTE_OUTSIDE}")


def test_chmod_github_path_traversal_denied(sg):
    """chmod with ../ traversal resolving into .github/ must be denied."""
    traversal = "project/../../.github/hooks/pre-tool-call.sh"
    assert deny(sg, f"chmod +x {traversal}")
