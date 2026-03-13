"""Tests for FIX-006: Test Safety Infrastructure — conftest.py hardening.

These tests verify that the autouse fixtures in tests/conftest.py correctly
block all dangerous side effects: VS Code launches, GUI dialogs, and HTTP calls.

Safety architecture:
- open_in_vscode is patched at both source and app.py binding → returns False
- tkinter.messagebox/filedialog functions are patched → no real dialogs
- check_for_update is patched ONLY at app.py binding (NOT at source module,
  so INS-009 tests can call the real function with their own HTTP mocks)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# 1. _prevent_vscode_launch — open_in_vscode patched at source module
# ---------------------------------------------------------------------------

def test_open_in_vscode_source_binding_is_blocked():
    """open_in_vscode in the source module returns False (not the real function)."""
    import launcher.core.vscode as vscode_mod
    result = vscode_mod.open_in_vscode("/some/path")
    assert result is False, "open_in_vscode source binding must be blocked by conftest"


def test_open_in_vscode_app_binding_is_blocked():
    """open_in_vscode imported into app.py returns False (not the real function)."""
    import launcher.gui.app as app_mod
    result = app_mod.open_in_vscode("/some/path")
    assert result is False, "open_in_vscode app.py binding must be blocked by conftest"


# ---------------------------------------------------------------------------
# 2. subprocess.Popen is NOT globally mocked (would break subprocess.run)
# ---------------------------------------------------------------------------

def test_subprocess_popen_is_real():
    """subprocess.Popen in launcher.core.vscode is the real Popen, not a mock.

    We intentionally do NOT mock it globally because vscode.subprocess IS
    sys.modules['subprocess'] — mocking Popen there would break
    subprocess.run() across the entire test suite.  Safety is ensured by the
    open_in_vscode mock (which prevents Popen from ever being reached).
    """
    import launcher.core.vscode as vscode_mod
    import subprocess as real_subprocess
    assert vscode_mod.subprocess.Popen is real_subprocess.Popen, (
        "subprocess.Popen must NOT be globally mocked — it would break subprocess.run()"
    )


# ---------------------------------------------------------------------------
# 3. _prevent_background_updates — app.py local binding only
# ---------------------------------------------------------------------------

def test_check_for_update_app_binding_is_blocked():
    """check_for_update imported into app.py returns an unpackable tuple (no HTTP call)."""
    import launcher.gui.app as app_mod
    result = app_mod.check_for_update("0.0.1")
    assert result == (False, "0.0.0"), (
        f"check_for_update app.py binding must return (False, '0.0.0'), got {result!r}"
    )


def test_check_for_update_source_is_real():
    """check_for_update at source module is the REAL function.

    INS-009 tests call check_for_update directly with their own HTTP mocks.
    The conftest must NOT replace the source function.
    """
    import launcher.core.updater as updater_mod
    assert not isinstance(updater_mod.check_for_update, MagicMock), (
        "check_for_update source must be real — INS-009 tests need it"
    )


# ---------------------------------------------------------------------------
# 4. Safety chain: open_in_vscode blocked → Popen never reached
# ---------------------------------------------------------------------------

def test_safety_chain_open_in_vscode_cannot_reach_popen():
    """Even if called, open_in_vscode returns False before reaching Popen."""
    import launcher.core.vscode as vscode_mod
    # The conftest patches open_in_vscode to return False.
    # So calling it never reaches the subprocess.Popen line.
    result = vscode_mod.open_in_vscode("/some/path")
    assert result is False
