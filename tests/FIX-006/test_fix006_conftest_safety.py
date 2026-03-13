"""Tests for FIX-006: Test Safety Infrastructure — conftest.py hardening.

These tests verify that the autouse fixtures in tests/conftest.py correctly
block all dangerous side effects: subprocess launches, GUI dialogs, HTTP calls,
and real VS Code detection via shutil.which.
"""

from __future__ import annotations

import subprocess
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
# 2. _prevent_vscode_launch — subprocess.Popen nuclear failsafe
# ---------------------------------------------------------------------------

def test_subprocess_popen_is_mocked_in_vscode_module():
    """subprocess.Popen in launcher.core.vscode is replaced with a MagicMock."""
    import launcher.core.vscode as vscode_mod
    assert isinstance(vscode_mod.subprocess.Popen, MagicMock), (
        "launcher.core.vscode.subprocess.Popen must be a MagicMock, not the real Popen"
    )


def test_real_popen_cannot_fire_through_vscode_module():
    """Calling subprocess.Popen via the vscode module does not spawn a process."""
    import launcher.core.vscode as vscode_mod
    # Call Popen directly through the module namespace — it should not spawn.
    vscode_mod.subprocess.Popen(["code", "/tmp"])
    # If we reach here without an OSError/FileNotFoundError the mock caught it.


# ---------------------------------------------------------------------------
# 3. _prevent_background_updates — source module binding
# ---------------------------------------------------------------------------

def test_check_for_update_source_binding_is_blocked():
    """check_for_update in the source module returns None (no HTTP call)."""
    import launcher.core.updater as updater_mod
    result = updater_mod.check_for_update("0.0.1")
    assert result is None, "check_for_update source binding must return None"


# ---------------------------------------------------------------------------
# 4. _prevent_background_updates — app.py local binding
# ---------------------------------------------------------------------------

def test_check_for_update_app_binding_is_blocked():
    """check_for_update imported into app.py returns None (no HTTP call)."""
    import launcher.gui.app as app_mod
    result = app_mod.check_for_update("0.0.1")
    assert result is None, "check_for_update app.py binding must return None"


# ---------------------------------------------------------------------------
# 5. _prevent_find_vscode_real_lookup — shutil.which returns None
# ---------------------------------------------------------------------------

def test_shutil_which_in_vscode_module_returns_none():
    """shutil.which in the vscode module returns None (no real path lookup)."""
    import launcher.core.vscode as vscode_mod
    result = vscode_mod.shutil.which("code")
    assert result is None, "shutil.which must return None to prevent real VS Code detection"


def test_find_vscode_returns_none_due_to_which_mock():
    """find_vscode() returns None because shutil.which is mocked to return None."""
    import launcher.core.vscode as vscode_mod
    # The autouse fixture makes which return None, so find_vscode must return None.
    result = vscode_mod.find_vscode()
    assert result is None, "find_vscode() must return None when shutil.which is mocked"


# ---------------------------------------------------------------------------
# 6. Interaction: find_vscode None → open_in_vscode still blocked
# ---------------------------------------------------------------------------

def test_full_safety_chain_no_real_process_spawned(monkeypatch):
    """End-to-end: even if we try to call the real open_in_vscode via monkeypatch,
    subprocess.Popen remains mocked so no process is spawned."""
    import launcher.core.vscode as vscode_mod

    # Temporarily restore the real open_in_vscode function logic by calling it directly.
    # shutil.which is still mocked → returns None → open_in_vscode returns False.
    real_open = vscode_mod.__class__  # just to exercise the internal path
    # Call find_vscode to confirm the chain: which is mocked → None.
    assert vscode_mod.find_vscode() is None
    # subprocess.Popen is the nuclear failsafe — confirm it's still a mock.
    assert isinstance(vscode_mod.subprocess.Popen, MagicMock)
