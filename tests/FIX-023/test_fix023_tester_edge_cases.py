"""FIX-023 — Tester edge-case tests for venv creation and activation scripts.

Covers:
  - Activation scripts with Windows backslash separators
  - Venv targets specified with backslash separators (multi-segment)
  - .venv target with trailing backslash (normalisation edge-case)
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


def allow(cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "allow"


def deny(cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "deny"


# ===========================================================================
# Activation scripts — Windows backslash variants
# ===========================================================================

def test_activate_ps1_backslash_allow():
    """TST-1754: .venv\\Scripts\\Activate.ps1 (backslash) -> allow.

    Windows users typically write activation commands with backslashes.
    The gate normalises the path to forward-slashes before zone-checking,
    so backslash activation scripts inside the project folder must be allowed.
    """
    assert allow(".venv\\Scripts\\Activate.ps1")


def test_activate_bat_backslash_allow():
    """TST-1755: .venv\\Scripts\\activate.bat (backslash) -> allow."""
    assert allow(".venv\\Scripts\\activate.bat")


def test_activate_unix_backslash_allow():
    """TST-1756: .venv\\bin\\activate (backslash on Unix-style path) -> allow.

    Backslash form of the Unix activation script path must be normalised and
    allowed via the project-folder fallback.
    """
    assert allow(".venv\\bin\\activate")


# ===========================================================================
# Venv targets — backslash normalisation
# ===========================================================================

def test_venv_backslash_src_venv_allow():
    """TST-1757: python -m venv src\\venv (backslash 2-segment) -> allow.

    Multi-segment backslash target normalises to src/venv which resolves to
    project/src/venv via project-folder fallback -> allow.
    """
    assert allow("python -m venv src\\venv")


def test_venv_dot_venv_trailing_backslash_deny():
    """TST-1758: python -m venv .venv\\ (trailing backslash) -> deny.

    A trailing backslash at the end of the command string is interpreted by
    shlex as a line-continuation escape character, making the command string
    syntactically invalid.  The gate correctly denies with 'Command could not
    be parsed' — this is the expected safe-failure mode.  Users should use
    'python -m venv .venv' (no trailing backslash) or 'python -m venv .venv/'
    on Windows.
    """
    assert deny("python -m venv .venv\\")
