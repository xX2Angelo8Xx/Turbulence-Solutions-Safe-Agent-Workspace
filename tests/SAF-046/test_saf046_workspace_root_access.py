"""SAF-046 — Tests for workspace root read access in the security gate.

Covers:
    is_workspace_root_readable() unit tests
        - workspace root itself → True
        - direct child file (pyproject.toml, README.md) → True
        - direct child dir that is NOT in deny dirs → True
        - .github/ direct child → False (deny zone)
        - .vscode/ direct child → False (deny zone)
        - NoAgentZone/ direct child → False (deny zone)
        - path two levels deep (root/some_folder/file.py) → False
        - path outside workspace root entirely → False
        - path traversal attempt → False
        - case variations of deny dirs → False (case-insensitive)
        - Windows backslash form → True (correct normalization)

    decide() integration tests (read_file / list_dir)
        - list_dir on workspace root → allow
        - read_file on pyproject.toml at root → allow
        - read_file on README.md at root → allow
        - read_file on .github/secrets.json → deny
        - read_file on NoAgentZone/secret → deny
        - list_dir on .github/ → deny
        - read_file two levels deep, non-project dir → deny
        - write to workspace root file → deny (write-denied)
        - .git at workspace root → deny (git internals)
"""
from __future__ import annotations

import json
import sys
import os
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Make zone_classifier and security_gate importable
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


# ===========================================================================
# is_workspace_root_readable() — unit tests
# ===========================================================================

def test_workspace_root_itself_readable():
    """Workspace root itself must be readable (supports list_dir)."""
    assert zc.is_workspace_root_readable(WS, WS) is True


def test_workspace_root_pyproject_toml_readable():
    """pyproject.toml directly at workspace root must be readable."""
    assert zc.is_workspace_root_readable(f"{WS}/pyproject.toml", WS) is True


def test_workspace_root_readme_readable():
    """README.md directly at workspace root must be readable."""
    assert zc.is_workspace_root_readable(f"{WS}/README.md", WS) is True


def test_workspace_root_direct_dir_readable():
    """A non-denied direct subdirectory of workspace root must be readable."""
    assert zc.is_workspace_root_readable(f"{WS}/some_other_tool_dir", WS) is True


def test_workspace_root_github_child_denied():
    """.github/ as a direct child of workspace root must NOT be readable."""
    assert zc.is_workspace_root_readable(f"{WS}/.github", WS) is False


def test_workspace_root_vscode_child_denied():
    """.vscode/ as a direct child must NOT be readable."""
    assert zc.is_workspace_root_readable(f"{WS}/.vscode", WS) is False


def test_workspace_root_noagentzone_child_denied():
    """NoAgentZone/ as a direct child must NOT be readable."""
    assert zc.is_workspace_root_readable(f"{WS}/noagentzone", WS) is False


def test_workspace_root_deep_path_denied():
    """Path two levels below workspace root (in non-project dir) is NOT readable."""
    assert zc.is_workspace_root_readable(f"{WS}/tools/helper.py", WS) is False


def test_workspace_root_outside_path_denied():
    """Path outside workspace root entirely must NOT be readable."""
    assert zc.is_workspace_root_readable("c:/other_workspace/file.txt", WS) is False


def test_workspace_root_traversal_attempt_denied():
    """Path traversal that resolves to a denied zone must NOT be readable."""
    # Traversal: ws_root/safe_name/../.github -> resolves to ws_root/.github
    assert zc.is_workspace_root_readable(f"{WS}/safe/../.github", WS) is False


def test_workspace_root_deny_dir_case_insensitive():
    """Case variations of denied directory names must be denied."""
    assert zc.is_workspace_root_readable(f"{WS}/.GITHUB", WS) is False
    assert zc.is_workspace_root_readable(f"{WS}/.VSCODE", WS) is False
    assert zc.is_workspace_root_readable(f"{WS}/NoAgentZone", WS) is False


def test_workspace_root_windows_backslash_form():
    """Windows backslash path to workspace root file must be normalized and allowed."""
    win_path = WS.replace("/", "\\") + "\\pyproject.toml"
    assert zc.is_workspace_root_readable(win_path, WS) is True


# ===========================================================================
# decide() integration tests
# ===========================================================================

def _decide(tool_name: str, path: str) -> str:
    """Helper: build a minimal payload and call sg.decide()."""
    data = {
        "tool_name": tool_name,
        "tool_input": {"filePath": path},
    }
    return sg.decide(data, WS)


def test_decide_list_dir_workspace_root_allow():
    """list_dir on workspace root must be allowed."""
    assert _decide("list_dir", WS) == "allow"


def test_decide_read_file_pyproject_allow():
    """read_file on pyproject.toml at workspace root must be allowed."""
    assert _decide("read_file", f"{WS}/pyproject.toml") == "allow"


def test_decide_read_file_readme_allow():
    """read_file on README.md at workspace root must be allowed."""
    assert _decide("read_file", f"{WS}/README.md") == "allow"


def test_decide_read_file_github_secrets_deny():
    """read_file on .github/secrets.json must still be denied."""
    assert _decide("read_file", f"{WS}/.github/secrets.json") == "deny"


def test_decide_read_file_noagentzone_deny():
    """read_file targeting NoAgentZone/ must remain denied."""
    assert _decide("read_file", f"{WS}/NoAgentZone/secret.txt") == "deny"


def test_decide_list_dir_github_deny():
    """list_dir on .github/ directory must remain denied."""
    assert _decide("list_dir", f"{WS}/.github") == "deny"


def test_decide_read_deep_nonproject_path_deny():
    """read_file two levels deep in a non-project dir must be denied."""
    assert _decide("read_file", f"{WS}/tools/internal/helper.py") == "deny"


def test_decide_write_to_workspace_root_deny():
    """create_file targeting workspace root file must remain denied (write-only → project folder)."""
    assert _decide("create_file", f"{WS}/pyproject.toml") == "deny"


def test_decide_read_git_at_workspace_root_deny():
    """.git directory at workspace root must be denied even though it is a direct child."""
    assert _decide("read_file", f"{WS}/.git") == "deny"


def test_decide_read_file_inside_project_still_allow():
    """read_file inside the project folder must still be allowed (regression guard)."""
    assert _decide("read_file", f"{WS}/project/src/main.py") == "allow"
