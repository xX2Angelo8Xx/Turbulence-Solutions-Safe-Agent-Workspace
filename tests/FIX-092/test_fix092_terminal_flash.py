"""Tests for FIX-092: Hide terminal flash when opening VS Code.

Verifies that CREATE_NO_WINDOW is applied on Windows and absent on other platforms.
"""
from __future__ import annotations

import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Override the conftest autouse fixture that patches open_in_vscode to False.
# FIX-092 tests need to call the REAL open_in_vscode to verify its behaviour.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _prevent_vscode_launch():
    """FIX-092 override: do not suppress open_in_vscode — we test it here."""
    yield


# ---------------------------------------------------------------------------
# vscode.py — open_in_vscode
# ---------------------------------------------------------------------------

class TestOpenInVscode:
    def test_win32_uses_create_no_window(self, monkeypatch):
        """On Windows, Popen must receive creationflags=CREATE_NO_WINDOW."""
        import launcher.core.vscode as vscode_mod

        fake_sys = types.SimpleNamespace(platform="win32")
        calls: list = []

        def fake_popen(args, **kwargs):
            calls.append((args, kwargs))

        monkeypatch.setattr(vscode_mod, "sys", fake_sys)
        monkeypatch.setattr(vscode_mod, "find_vscode", lambda: "code")
        monkeypatch.setattr(vscode_mod.subprocess, "Popen", fake_popen)

        vscode_mod.open_in_vscode(Path("/tmp/ws"))

        assert len(calls) == 1
        _, kwargs = calls[0]
        assert kwargs.get("creationflags") == subprocess.CREATE_NO_WINDOW

    def test_non_win32_no_creationflags(self, monkeypatch):
        """On non-Windows, Popen must NOT receive creationflags."""
        import launcher.core.vscode as vscode_mod

        fake_sys = types.SimpleNamespace(platform="linux")
        calls: list = []

        def fake_popen(args, **kwargs):
            calls.append((args, kwargs))

        monkeypatch.setattr(vscode_mod, "sys", fake_sys)
        monkeypatch.setattr(vscode_mod, "find_vscode", lambda: "code")
        monkeypatch.setattr(vscode_mod.subprocess, "Popen", fake_popen)

        vscode_mod.open_in_vscode(Path("/tmp/ws"))

        assert len(calls) == 1
        _, kwargs = calls[0]
        assert "creationflags" not in kwargs

    def test_correct_popen_args(self, monkeypatch):
        """Popen is called with [exe, str(workspace_path)]."""
        import launcher.core.vscode as vscode_mod

        ws = Path("/tmp/my_workspace")
        fake_sys = types.SimpleNamespace(platform="linux")
        calls: list = []

        def fake_popen(args, **kwargs):
            calls.append((args, kwargs))

        monkeypatch.setattr(vscode_mod, "sys", fake_sys)
        monkeypatch.setattr(vscode_mod, "find_vscode", lambda: "/usr/bin/code")
        monkeypatch.setattr(vscode_mod.subprocess, "Popen", fake_popen)

        vscode_mod.open_in_vscode(ws)

        assert len(calls) == 1
        positional_args, _ = calls[0]
        assert positional_args == ["/usr/bin/code", str(ws)]

    def test_returns_true_on_success(self, monkeypatch):
        """Returns True when VS Code is found and Popen succeeds."""
        import launcher.core.vscode as vscode_mod

        fake_sys = types.SimpleNamespace(platform="linux")
        monkeypatch.setattr(vscode_mod, "sys", fake_sys)
        monkeypatch.setattr(vscode_mod, "find_vscode", lambda: "code")
        monkeypatch.setattr(vscode_mod.subprocess, "Popen", lambda *a, **kw: None)

        result = vscode_mod.open_in_vscode(Path("/tmp/ws"))
        assert result is True

    def test_returns_false_when_not_found(self, monkeypatch):
        """Returns False when find_vscode returns None."""
        import launcher.core.vscode as vscode_mod

        monkeypatch.setattr(vscode_mod, "find_vscode", lambda: None)

        result = vscode_mod.open_in_vscode(Path("/tmp/ws"))
        assert result is False


# ---------------------------------------------------------------------------
# github_auth.py — get_github_token subprocess kwargs
# ---------------------------------------------------------------------------

class TestGithubAuthCreationFlag:
    def _run_with_platform(self, platform: str):
        """Call get_github_token with no env tokens and gh returning failure."""
        import launcher.core.github_auth as auth_mod
        run_result = MagicMock()
        run_result.returncode = 1
        run_result.stdout = ""
        mock_run = MagicMock(return_value=run_result)

        env_patch = {"GITHUB_TOKEN": "", "GH_TOKEN": ""}
        with patch.dict("os.environ", env_patch, clear=False), \
             patch.object(auth_mod, "sys") as mock_sys, \
             patch.object(auth_mod.subprocess, "run", mock_run):
            mock_sys.platform = platform
            auth_mod.get_github_token()
        return mock_run

    def test_win32_uses_create_no_window(self):
        """On Windows, subprocess.run for 'gh auth token' uses CREATE_NO_WINDOW."""
        mock_run = self._run_with_platform("win32")
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs.get("creationflags") == subprocess.CREATE_NO_WINDOW

    def test_non_win32_no_creationflags(self):
        """On non-Windows, subprocess.run for 'gh auth token' has no creationflags."""
        mock_run = self._run_with_platform("linux")
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert "creationflags" not in kwargs


# ---------------------------------------------------------------------------
# updater.py — _get_local_git_version and check_for_update_source
# ---------------------------------------------------------------------------

class TestUpdaterCreationFlag:
    def test_git_describe_win32_creationflag(self):
        """_get_local_git_version uses CREATE_NO_WINDOW on Windows."""
        import launcher.core.updater as updater_mod
        run_result = MagicMock()
        run_result.returncode = 0
        run_result.stdout = "v1.0.0\n"
        mock_run = MagicMock(return_value=run_result)

        with patch.object(updater_mod, "sys") as mock_sys, \
             patch.object(updater_mod.subprocess, "run", mock_run):
            mock_sys.platform = "win32"
            updater_mod._get_local_git_version(Path("."))
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs.get("creationflags") == subprocess.CREATE_NO_WINDOW

    def test_git_fetch_win32_creationflag(self):
        """check_for_update_source git fetch call uses CREATE_NO_WINDOW on Windows."""
        import launcher.core.updater as updater_mod
        fetch_result = MagicMock(returncode=0, stdout="")
        describe_result = MagicMock(returncode=0, stdout="v1.0.0\n")
        call_count = {"n": 0}

        def run_side_effect(*args, **kwargs):
            call_count["n"] += 1
            return fetch_result if call_count["n"] == 1 else describe_result

        with patch.object(updater_mod, "sys") as mock_sys, \
             patch.object(updater_mod.subprocess, "run", side_effect=run_side_effect) as mock_run, \
             patch.object(updater_mod, "check_for_update", return_value=(False, "1.0.0")):
            mock_sys.platform = "win32"
            updater_mod.check_for_update_source(Path("."))
        # First call is the git fetch — verify CREATE_NO_WINDOW on it
        assert mock_run.call_count >= 1
        first_call_kwargs = mock_run.call_args_list[0][1]
        assert first_call_kwargs.get("creationflags") == subprocess.CREATE_NO_WINDOW
