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
# 2. subprocess.Popen — FIX-008 wraps it with a sentinel; non-VS-Code passes
# ---------------------------------------------------------------------------

def test_subprocess_popen_is_real():
    """subprocess.Popen is wrapped by the FIX-008 sentinel, not a silent no-op.

    FIX-008 change: the conftest wraps subprocess.Popen with a sentinel that
    raises RuntimeError for VS Code invocations.  The sentinel IS a MagicMock
    (created by patch()) but with a custom side_effect — it is NOT a silent
    MagicMock that returns a MagicMock for every call.  We verify this by
    confirming that calling Popen with "code" as the executable raises
    RuntimeError rather than silently returning a mock object.
    """
    import subprocess as sp_mod
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION"):
        sp_mod.Popen(["code", "/some/path"])


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
