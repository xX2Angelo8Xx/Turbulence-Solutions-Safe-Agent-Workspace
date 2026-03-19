"""FIX-035 — Tests for deferred development tools in security_gate.py.

Verifies that:
- `install_python_packages` is in _EXEMPT_TOOLS and returns "allow"
- `configure_python_environment` is in _EXEMPT_TOOLS and returns "allow"
- `fetch_webpage` is in _EXEMPT_TOOLS and returns "allow"
- Other non-exempt tools still go through normal checks and are denied
  when they target paths outside the project folder.
- Tools that are genuinely exempt still work as expected.

Addresses audit finding L13 from Security Audit V2.0.0.
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
        "templates", "coding", ".github", "hooks", "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

WS = "/workspace"


def _decide(tool_name: str, extra: dict | None = None) -> str:
    """Build a minimal payload and call decide()."""
    data: dict = {"tool_name": tool_name}
    if extra:
        data.update(extra)
    return sg.decide(data, WS)


# ===========================================================================
# TST-FIX035-001: _EXEMPT_TOOLS membership
# ===========================================================================

def test_install_python_packages_in_exempt_tools():
    """TST-FIX035-001: install_python_packages must be in _EXEMPT_TOOLS."""
    assert "install_python_packages" in sg._EXEMPT_TOOLS


def test_configure_python_environment_in_exempt_tools():
    """TST-FIX035-002: configure_python_environment must be in _EXEMPT_TOOLS."""
    assert "configure_python_environment" in sg._EXEMPT_TOOLS


def test_fetch_webpage_in_exempt_tools():
    """TST-FIX035-003: fetch_webpage must be in _EXEMPT_TOOLS."""
    assert "fetch_webpage" in sg._EXEMPT_TOOLS


# ===========================================================================
# TST-FIX035-004 to TST-FIX035-006: decide() returns "allow"
# ===========================================================================

def test_install_python_packages_returns_allow():
    """TST-FIX035-004: decide() returns 'allow' for install_python_packages."""
    assert _decide("install_python_packages") == "allow"


def test_configure_python_environment_returns_allow():
    """TST-FIX035-005: decide() returns 'allow' for configure_python_environment."""
    assert _decide("configure_python_environment") == "allow"


def test_fetch_webpage_returns_allow():
    """TST-FIX035-006: decide() returns 'allow' for fetch_webpage."""
    assert _decide("fetch_webpage") == "allow"


# ===========================================================================
# TST-FIX035-007: decide() returns "allow" even with no path in payload
# ===========================================================================

def test_install_python_packages_no_path_returns_allow():
    """TST-FIX035-007: install_python_packages with no path field still returns 'allow'."""
    # Previously, exempt tools without a path would fail closed ("deny").
    # FIX-035 adds early allow handling so no path field is needed.
    data = {"tool_name": "install_python_packages", "packages": ["requests"]}
    assert sg.decide(data, WS) == "allow"


def test_configure_python_environment_no_path_returns_allow():
    """TST-FIX035-008: configure_python_environment with no path still returns 'allow'."""
    data = {"tool_name": "configure_python_environment"}
    assert sg.decide(data, WS) == "allow"


def test_fetch_webpage_no_path_returns_allow():
    """TST-FIX035-009: fetch_webpage with no path field still returns 'allow'."""
    data = {"tool_name": "fetch_webpage", "url": "https://docs.python.org"}
    assert sg.decide(data, WS) == "allow"


# ===========================================================================
# TST-FIX035-010 to TST-FIX035-012: normal check still applies to unknown tools
# ===========================================================================

def test_unknown_tool_without_path_returns_deny():
    """TST-FIX035-010: An unknown non-exempt tool with no path returns 'deny'."""
    assert _decide("some_unknown_tool") == "deny"


def test_unknown_tool_with_deny_zone_path_returns_deny():
    """TST-FIX035-011: A non-exempt tool targeting a deny zone is still denied."""
    data = {
        "tool_name": "some_custom_tool",
        "filePath": "/workspace/.github/hooks/scripts/evil.py",
    }
    assert sg.decide(data, WS) == "deny"


def test_non_exempt_tool_denied():
    """TST-FIX035-012: A tool not in any allow set is denied by the normal flow."""
    # 'my_special_tool' is not in _EXEMPT_TOOLS, _ALWAYS_ALLOW_TOOLS,
    # or any explicit handler — it must be denied.
    assert _decide("my_special_tool") == "deny"


# ===========================================================================
# TST-FIX035-013: existing exempt tools still work (regression)
# ===========================================================================

def test_read_file_in_project_still_allowed():
    """TST-FIX035-013: read_file targeting the project folder is still allowed."""
    data = {
        "tool_name": "read_file",
        "filePath": "/workspace/project/src/app.py",
    }
    # detect_project_folder requires the filesystem; mock it for unit tests.
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        assert sg.decide(data, WS) == "allow"


def test_read_file_in_deny_zone_still_denied():
    """TST-FIX035-014: read_file targeting .github is still denied."""
    data = {
        "tool_name": "read_file",
        "filePath": "/workspace/.github/hooks/scripts/security_gate.py",
    }
    assert sg.decide(data, WS) == "deny"
