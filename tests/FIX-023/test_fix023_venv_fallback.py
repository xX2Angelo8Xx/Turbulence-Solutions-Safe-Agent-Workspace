"""FIX-023 — Tests for .venv directory creation and activation inside project folder.

Verifies that ``python -m venv .venv`` and venv activation scripts are
allowed when targeting the project folder.
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
        "templates", "agent-workbench", ".github", "hooks", "scripts",
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


def allow(cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "allow"


def deny(cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "deny"


# ===========================================================================
# python -m venv — target in project folder
# ===========================================================================

def test_venv_dot_venv_allow():
    """TST-1720: python -m venv .venv -> allow via project fallback."""
    assert allow("python -m venv .venv")


def test_venv_named_dir_allow():
    """TST-1721: python -m venv myenv -> allow via project fallback."""
    assert allow("python -m venv myenv")


def test_venv_project_relative_allow():
    """TST-1722: python -m venv project/.venv -> allow (direct zone check)."""
    assert allow("python -m venv project/.venv")


# ===========================================================================
# Venv activation scripts
# ===========================================================================

def test_activate_ps1_allow():
    """TST-1723: .venv/Scripts/Activate.ps1 -> allow via project fallback."""
    assert allow(".venv/Scripts/Activate.ps1")


def test_activate_bat_allow():
    """TST-1724: .venv/Scripts/activate.bat -> allow."""
    assert allow(".venv/Scripts/activate.bat")


def test_activate_unix_allow():
    """TST-1725: .venv/bin/activate -> allow."""
    assert allow(".venv/bin/activate")


def test_activate_project_prefix_allow():
    """TST-1726: project/.venv/Scripts/Activate.ps1 -> allow (direct)."""
    assert allow("project/.venv/Scripts/Activate.ps1")


def test_activate_outside_deny():
    """TST-1727: /outside/path/activate -> deny."""
    assert deny("/outside/path/activate")


# ===========================================================================
# Deny-zone venv — must NOT fallback
# ===========================================================================

def test_venv_github_deny():
    """TST-1728: python -m venv .github -> deny (deny zone guard)."""
    assert deny("python -m venv .github")
