"""SAF-046 — Tester edge-case tests for workspace root read access.

Covers cases the Developer's tests did not explicitly test:
    Defense-in-depth:
        - is_workspace_root_readable() returns True for .git direct child
          (the .git block is handled only via is_git_internals() in decide())
        - decide() still denies .git/config (depth > 1, caught by length guard)

    Cross-platform path forms:
        - Git Bash /c/workspace/pyproject.toml → allow
        - WSL /mnt/c/workspace/pyproject.toml → allow

    Common dot-config files at workspace root (not in deny dirs):
        - .gitignore → allow
        - .editorconfig → allow
        - .env must NOT be readable if classified as deny zone (not a deny dir,
          so it IS readable — documents the intended behavior)

    Additional write tools denied on workspace root:
        - edit_file on workspace root file → deny
        - replace_string_in_file on workspace root file → deny
        - multi_replace_string_in_file on workspace root file → deny

    Trailing-slash handling:
        - .github/ with trailing slash → deny

    list_dir with the native 'path' field (not 'filePath'):
        - list_dir {"path": WS} → allow
        - list_dir {"path": WS + "/.github"} → deny

    Binary/Unicode in path (should not bypass deny):
        - C0 control char in .github segment → deny (stripped, still .github)
"""
from __future__ import annotations

import json
import sys
import os
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Import zone_classifier and security_gate from template scripts dir
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

import zone_classifier as zc   # noqa: E402
import security_gate as sg     # noqa: E402

WS = "c:/workspace"


@pytest.fixture(autouse=True)
def mock_project_folder():
    """Avoid requiring the workspace directory to exist on disk."""
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _decide_path(tool_name: str, path: str, path_field: str = "filePath") -> str:
    """Build a minimal payload with a configurable path field name."""
    data = {
        "tool_name": tool_name,
        "tool_input": {path_field: path},
    }
    return sg.decide(data, WS)


# ===========================================================================
# Defense-in-depth: .git at workspace root
# ===========================================================================

def test_is_workspace_root_readable_returns_true_for_git_dir():
    """.git is a direct non-denied child — is_workspace_root_readable() returns
    True because .git is NOT in _DENY_DIRS.  The .git block is enforced by
    is_git_internals() in decide(), not by is_workspace_root_readable()."""
    # Document the current behavior: the function alone does NOT block .git.
    assert zc.is_workspace_root_readable(f"{WS}/.git", WS) is True


def test_decide_still_denies_git_dir_at_workspace_root():
    """decide() must deny read_file on .git even though
    is_workspace_root_readable() returns True — is_git_internals() is the
    additional guard inside decide()."""
    assert _decide_path("read_file", f"{WS}/.git") == "deny"


def test_decide_denies_git_config_two_levels_deep():
    """.git/config is two levels deep → denied by len(rel.parts) == 1 guard."""
    assert _decide_path("read_file", f"{WS}/.git/config") == "deny"


# ===========================================================================
# Cross-platform path forms
# ===========================================================================

def test_git_bash_path_to_workspace_root_file_allowed():
    """Git Bash path /c/workspace/pyproject.toml should normalise to
    c:/workspace/pyproject.toml and be allowed for read_file."""
    git_bash_path = "/c/workspace/pyproject.toml"
    # Verify normalize_path converts it correctly
    assert zc.normalize_path(git_bash_path) == "c:/workspace/pyproject.toml"
    assert zc.is_workspace_root_readable(git_bash_path, WS) is True


def test_wsl_path_to_workspace_root_file_allowed():
    """WSL path /mnt/c/workspace/pyproject.toml should normalise to
    c:/workspace/pyproject.toml and be allowed for read_file."""
    wsl_path = "/mnt/c/workspace/pyproject.toml"
    assert zc.normalize_path(wsl_path) == "c:/workspace/pyproject.toml"
    assert zc.is_workspace_root_readable(wsl_path, WS) is True


# ===========================================================================
# Common dot-config files at workspace root
# ===========================================================================

def test_gitignore_at_workspace_root_readable():
    """.gitignore is a common root-level config file and must be readable."""
    assert zc.is_workspace_root_readable(f"{WS}/.gitignore", WS) is True
    assert _decide_path("read_file", f"{WS}/.gitignore") == "allow"


def test_editorconfig_at_workspace_root_readable():
    """.editorconfig is a root-level config file and must be readable."""
    assert zc.is_workspace_root_readable(f"{WS}/.editorconfig", WS) is True
    assert _decide_path("read_file", f"{WS}/.editorconfig") == "allow"


# ===========================================================================
# Additional write tools denied on workspace root
# ===========================================================================

def test_edit_file_on_workspace_root_denied():
    """edit_file targeting a workspace root file must remain denied."""
    assert _decide_path("edit_file", f"{WS}/pyproject.toml") == "deny"


def test_replace_string_in_file_on_workspace_root_denied():
    """replace_string_in_file targeting a workspace root file must be denied."""
    assert _decide_path("replace_string_in_file", f"{WS}/README.md") == "deny"


def test_multi_replace_on_workspace_root_denied():
    """multi_replace_string_in_file targeting a workspace root file must be denied."""
    data = {
        "tool_name": "multi_replace_string_in_file",
        "tool_input": {
            "replacements": [
                {"filePath": f"{WS}/pyproject.toml", "oldString": "a", "newString": "b"}
            ]
        },
    }
    assert sg.decide(data, WS) == "deny"


def test_write_file_on_workspace_root_denied():
    """write_file targeting a workspace root file must remain denied."""
    assert _decide_path("write_file", f"{WS}/pyproject.toml") == "deny"


# ===========================================================================
# Trailing-slash handling
# ===========================================================================

def test_github_with_trailing_slash_denied():
    """.github/ with trailing slash must still be denied after normalization."""
    # normalize_path strips trailing slashes before zone check
    assert zc.is_workspace_root_readable(f"{WS}/.github/", WS) is False


def test_vscode_with_trailing_slash_denied():
    """.vscode/ with trailing slash must be denied."""
    assert zc.is_workspace_root_readable(f"{WS}/.vscode/", WS) is False


# ===========================================================================
# list_dir with the native 'path' field
# ===========================================================================

def test_list_dir_with_path_field_workspace_root_allow():
    """list_dir uses 'path' as its native field — must allow workspace root."""
    assert _decide_path("list_dir", WS, path_field="path") == "allow"


def test_list_dir_with_path_field_github_deny():
    """list_dir with 'path' field pointing to .github/ must remain denied."""
    assert _decide_path("list_dir", f"{WS}/.github", path_field="path") == "deny"


def test_list_dir_with_directory_field_workspace_root_allow():
    """list_dir with 'directory' field pointing to workspace root must allow."""
    assert _decide_path("list_dir", WS, path_field="directory") == "allow"


# ===========================================================================
# C0 control character injection
# ===========================================================================

def test_c0_control_char_in_path_does_not_bypass_deny():
    """.github with an injected C0 control character must still be denied.
    normalize_path strips C0 chars, leaving .github which is in _DENY_DIRS."""
    # \x01 is a C0 control character injected between . and g
    assert zc.is_workspace_root_readable(f"{WS}/.\x01github", WS) is False


def test_control_char_in_noagentzone_still_denied():
    """NoAgentZone with embedded C0 char must remain denied after stripping."""
    assert zc.is_workspace_root_readable(f"{WS}/NoAgent\x02Zone", WS) is False
