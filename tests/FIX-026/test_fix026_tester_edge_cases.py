"""FIX-026 — Tester edge-case tests for get_errors project-folder fallback.

Covers:
  - get_errors with multiple allowed project paths (all must be in project zone)
  - get_errors with mixed allow + deny paths (must deny entire call)
  - get_errors with Windows backslash path (normalisation)
  - get_errors with malformed filePaths entries (None, empty string)
"""
from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "Default-Project", ".github", "hooks", "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

WS = "c:/workspace"


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# ===========================================================================
# Multiple project-folder paths — all must allow
# ===========================================================================

def test_get_errors_multiple_project_paths_allow():
    """TST-1759: get_errors with several project-relative paths -> allow.

    All paths resolve inside the project folder via fallback; the call
    should be allowed.
    """
    data = {
        "tool_name": "get_errors",
        "filePaths": ["src/app.py", "tests/test_main.py", "src/utils.py"],
    }
    assert sg.decide(data, WS) == "allow"


def test_get_errors_mixed_allow_and_deny_path_deny():
    """TST-1760: get_errors with one project path + one deny-zone path -> deny.

    When ANY path in the array falls inside a deny zone the entire call must
    be denied.  A project-relative path earlier in the list must NOT mask the
    deny-zone violation of a later path.
    """
    data = {
        "tool_name": "get_errors",
        "filePaths": ["src/app.py", ".github/hooks/evil.py"],
    }
    assert sg.decide(data, WS) == "deny"


def test_get_errors_deny_zone_only_deny():
    """TST-1761: get_errors filePaths=['.vscode/settings.json'] -> deny.

    A single deny-zone path with no project paths must be denied.
    """
    data = {
        "tool_name": "get_errors",
        "filePaths": [".vscode/settings.json"],
    }
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# Backslash path normalisation
# ===========================================================================

def test_get_errors_backslash_path_allow():
    """TST-1762: get_errors filePaths=['src\\\\app.py'] (backslash) -> allow.

    Windows paths with backslash separators are normalised to forward-slash
    before zone-checking; the path should resolve inside the project folder
    via fallback and be allowed.
    """
    data = {
        "tool_name": "get_errors",
        "filePaths": ["src\\app.py"],
    }
    assert sg.decide(data, WS) == "allow"


# ===========================================================================
# Malformed filePaths entries
# ===========================================================================

def test_get_errors_none_in_list_deny():
    """TST-1763: get_errors filePaths=[None] -> deny.

    A None entry in the filePaths list is not a string; the gate must deny
    to fail closed rather than silently skipping the malformed path.
    """
    data = {
        "tool_name": "get_errors",
        "filePaths": [None],
    }
    assert sg.decide(data, WS) == "deny"


def test_get_errors_empty_string_in_list_deny():
    """TST-1764: get_errors filePaths=[''] -> deny.

    An empty string in the filePaths list must be denied (the gate requires
    each path to be a non-empty string).
    """
    data = {
        "tool_name": "get_errors",
        "filePaths": [""],
    }
    assert sg.decide(data, WS) == "deny"
