"""FIX-026 — Tests for get_errors project-folder fallback.

Verifies that ``get_errors`` allows relative paths inside the project folder
(e.g. ``src/app.py``) without requiring an absolute path.
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
# get_errors with relative project paths
# ===========================================================================

def test_get_errors_relative_src_allow():
    """TST-1729: get_errors filePaths=['src/app.py'] -> allow via fallback."""
    data = {"tool_name": "get_errors", "filePaths": ["src/app.py"]}
    assert sg.decide(data, WS) == "allow"


def test_get_errors_relative_tests_allow():
    """TST-1730: get_errors filePaths=['tests/'] -> allow."""
    data = {"tool_name": "get_errors", "filePaths": ["tests/"]}
    assert sg.decide(data, WS) == "allow"


def test_get_errors_absolute_project_allow():
    """TST-1731: get_errors with absolute project path -> allow (direct)."""
    data = {"tool_name": "get_errors", "filePaths": ["c:/workspace/project/src/app.py"]}
    assert sg.decide(data, WS) == "allow"


def test_get_errors_empty_allow():
    """TST-1732: get_errors with no filePaths -> allow (unchanged)."""
    data = {"tool_name": "get_errors"}
    assert sg.decide(data, WS) == "allow"


# ===========================================================================
# get_errors with deny-zone paths — must DENY
# ===========================================================================

def test_get_errors_github_deny():
    """TST-1733: get_errors filePaths=['.github/hooks/script.py'] -> deny."""
    data = {"tool_name": "get_errors", "filePaths": [".github/hooks/script.py"]}
    assert sg.decide(data, WS) == "deny"


def test_get_errors_mixed_allow_deny():
    """TST-1734: get_errors with one project + one deny path -> deny."""
    data = {"tool_name": "get_errors", "filePaths": ["src/app.py", ".github/hooks/evil.py"]}
    assert sg.decide(data, WS) == "deny"


def test_get_errors_nested_tool_input_allow():
    """TST-1735: get_errors via nested tool_input -> allow."""
    data = {
        "tool_name": "get_errors",
        "tool_input": {"filePaths": ["src/app.py"]},
    }
    assert sg.decide(data, WS) == "allow"
