"""Edge-case tests for FIX-092: Hide terminal flash when opening VS Code.

Additional coverage beyond the Developer's test suite:
  - Exact value of CREATE_NO_WINDOW
  - macOS / Darwin platform (third platform family)
  - capture_output still present on subprocess.run calls
  - git describe / git fetch still receive correct arguments
  - Updater non-Windows: no creationflags anywhere
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
# FIX-092 edge-case tests call the REAL open_in_vscode to verify its behaviour.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _prevent_vscode_launch():
    """FIX-092 edge-case override: do not suppress open_in_vscode — we test it."""
    yield


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateNoWindowValue:
    """CREATE_NO_WINDOW must equal the documented Windows API constant."""

    def test_exact_hex_value(self):
        """subprocess.CREATE_NO_WINDOW == 0x08000000 (Win32 DETACHED_PROCESS family)."""
        assert subprocess.CREATE_NO_WINDOW == 0x08000000


# ─────────────────────────────────────────────────────────────────────────────
# vscode.py edge cases
# ─────────────────────────────────────────────────────────────────────────────

class TestOpenInVscodeEdgeCases:
    """Extra platforms and argument-correctness checks for open_in_vscode."""

    def test_darwin_no_creationflags(self, monkeypatch):
        """On macOS (darwin), Popen must NOT receive creationflags."""
        import launcher.core.vscode as vscode_mod

        fake_sys = types.SimpleNamespace(platform="darwin")
        calls: list = []

        def fake_popen(args, **kwargs):
            calls.append((args, kwargs))

        monkeypatch.setattr(vscode_mod, "sys", fake_sys)
        monkeypatch.setattr(vscode_mod, "find_vscode", lambda: "/usr/local/bin/code")
        monkeypatch.setattr(vscode_mod.subprocess, "Popen", fake_popen)

        result = vscode_mod.open_in_vscode(Path("/home/user/project"))

        assert result is True
        assert len(calls) == 1
        _, kwargs = calls[0]
        assert "creationflags" not in kwargs

    def test_win32_path_string_conversion(self, monkeypatch):
        """Workspace Path is converted to str before being passed to Popen."""
        import launcher.core.vscode as vscode_mod

        ws = Path("C:/Users/user/my project")
        fake_sys = types.SimpleNamespace(platform="win32")
        calls: list = []

        def fake_popen(args, **kwargs):
            calls.append((args, kwargs))

        monkeypatch.setattr(vscode_mod, "sys", fake_sys)
        monkeypatch.setattr(vscode_mod, "find_vscode", lambda: "code")
        monkeypatch.setattr(vscode_mod.subprocess, "Popen", fake_popen)

        vscode_mod.open_in_vscode(ws)

        assert len(calls) == 1
        positional_args, _ = calls[0]
        # Second element must be a str, not a Path
        assert isinstance(positional_args[1], str)
        assert positional_args[1] == str(ws)

    def test_popen_not_called_when_vscode_missing(self, monkeypatch):
        """Popen is never called when find_vscode returns None."""
        import launcher.core.vscode as vscode_mod

        calls: list = []

        def fake_popen(args, **kwargs):
            calls.append((args, kwargs))

        monkeypatch.setattr(vscode_mod, "find_vscode", lambda: None)
        monkeypatch.setattr(vscode_mod.subprocess, "Popen", fake_popen)

        result = vscode_mod.open_in_vscode(Path("/tmp/ws"))

        assert result is False
        assert calls == [], "Popen must not be called when VS Code is not found"


# ─────────────────────────────────────────────────────────────────────────────
# github_auth.py edge cases
# ─────────────────────────────────────────────────────────────────────────────

class TestGithubAuthEdgeCases:
    """capture_output and Darwin platform checks for get_github_token."""

    def _run_with_platform(self, platform: str):
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

    def test_capture_output_always_present(self):
        """capture_output=True must be passed on every platform."""
        for platform in ("win32", "linux", "darwin"):
            mock_run = self._run_with_platform(platform)
            mock_run.assert_called_once()
            _, kwargs = mock_run.call_args
            assert kwargs.get("capture_output") is True, (
                f"capture_output missing on {platform}"
            )

    def test_darwin_no_creationflags(self):
        """On macOS, subprocess.run for gh must NOT have creationflags."""
        mock_run = self._run_with_platform("darwin")
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert "creationflags" not in kwargs

    def test_correct_gh_command(self):
        """The subprocess call uses exactly ['gh', 'auth', 'token']."""
        mock_run = self._run_with_platform("linux")
        mock_run.assert_called_once()
        args, _ = mock_run.call_args
        assert args[0] == ["gh", "auth", "token"]


# ─────────────────────────────────────────────────────────────────────────────
# updater.py edge cases
# ─────────────────────────────────────────────────────────────────────────────

class TestUpdaterEdgeCases:
    """capture_output, correct git args, and non-Windows platform checks."""

    # -- _get_local_git_version -----------------------------------------------

    def test_git_describe_non_win32_no_creationflags(self):
        """_get_local_git_version has no creationflags on Linux."""
        import launcher.core.updater as updater_mod

        run_result = MagicMock(returncode=0, stdout="v1.0.0\n")
        mock_run = MagicMock(return_value=run_result)

        with patch.object(updater_mod, "sys") as mock_sys, \
             patch.object(updater_mod.subprocess, "run", mock_run):
            mock_sys.platform = "linux"
            updater_mod._get_local_git_version(Path("."))

        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert "creationflags" not in kwargs

    def test_git_describe_capture_output_present(self):
        """_get_local_git_version passes capture_output=True on every platform."""
        import launcher.core.updater as updater_mod

        for platform in ("win32", "linux", "darwin"):
            run_result = MagicMock(returncode=0, stdout="v1.0.0\n")
            mock_run = MagicMock(return_value=run_result)

            with patch.object(updater_mod, "sys") as mock_sys, \
                 patch.object(updater_mod.subprocess, "run", mock_run):
                mock_sys.platform = platform
                updater_mod._get_local_git_version(Path("."))

            mock_run.assert_called_once()
            _, kwargs = mock_run.call_args
            assert kwargs.get("capture_output") is True, (
                f"capture_output missing on {platform}"
            )

    def test_git_describe_correct_args(self):
        """_get_local_git_version calls git with the exact expected arguments."""
        import launcher.core.updater as updater_mod

        run_result = MagicMock(returncode=0, stdout="v2.3.0\n")
        mock_run = MagicMock(return_value=run_result)

        with patch.object(updater_mod, "sys") as mock_sys, \
             patch.object(updater_mod.subprocess, "run", mock_run):
            mock_sys.platform = "linux"
            updater_mod._get_local_git_version(Path("/repo"))

        args, _ = mock_run.call_args
        assert args[0] == ["git", "describe", "--tags", "--abbrev=0"]

    # -- check_for_update_source (git fetch call) ------------------------------

    def test_git_fetch_non_win32_no_creationflags(self):
        """check_for_update_source git fetch has no creationflags on Linux."""
        import launcher.core.updater as updater_mod

        fetch_result = MagicMock(returncode=0, stdout="")
        call_count = {"n": 0}

        def run_side_effect(*args, **kwargs):
            call_count["n"] += 1
            return fetch_result

        with patch.object(updater_mod, "sys") as mock_sys, \
             patch.object(updater_mod.subprocess, "run", side_effect=run_side_effect) as mock_run, \
             patch.object(updater_mod, "check_for_update", return_value=(False, "1.0.0")), \
             patch.object(updater_mod, "_get_local_git_version", return_value="1.0.0"):
            mock_sys.platform = "linux"
            updater_mod.check_for_update_source(Path("."))

        assert mock_run.call_count >= 1
        first_kwargs = mock_run.call_args_list[0][1]
        assert "creationflags" not in first_kwargs

    def test_git_fetch_capture_output_always_present(self):
        """check_for_update_source git fetch passes capture_output=True on every platform."""
        import launcher.core.updater as updater_mod

        for platform in ("win32", "linux", "darwin"):
            fetch_result = MagicMock(returncode=0, stdout="")

            with patch.object(updater_mod, "sys") as mock_sys, \
                 patch.object(updater_mod.subprocess, "run", return_value=fetch_result) as mock_run, \
                 patch.object(updater_mod, "check_for_update", return_value=(False, "1.0.0")), \
                 patch.object(updater_mod, "_get_local_git_version", return_value="1.0.0"):
                mock_sys.platform = platform
                updater_mod.check_for_update_source(Path("."))

            assert mock_run.call_count >= 1
            first_kwargs = mock_run.call_args_list[0][1]
            assert first_kwargs.get("capture_output") is True, (
                f"capture_output missing on {platform}"
            )

    def test_git_fetch_correct_args(self):
        """check_for_update_source issues: git fetch --tags --quiet."""
        import launcher.core.updater as updater_mod

        fetch_result = MagicMock(returncode=0, stdout="")

        with patch.object(updater_mod, "sys") as mock_sys, \
             patch.object(updater_mod.subprocess, "run", return_value=fetch_result) as mock_run, \
             patch.object(updater_mod, "check_for_update", return_value=(False, "1.0.0")), \
             patch.object(updater_mod, "_get_local_git_version", return_value="1.0.0"):
            mock_sys.platform = "linux"
            updater_mod.check_for_update_source(Path("."))

        first_args = mock_run.call_args_list[0][0]
        assert first_args[0] == ["git", "fetch", "--tags", "--quiet"]

    def test_darwin_git_fetch_no_creationflags(self):
        """macOS: git fetch in check_for_update_source has no creationflags."""
        import launcher.core.updater as updater_mod

        fetch_result = MagicMock(returncode=0, stdout="")

        with patch.object(updater_mod, "sys") as mock_sys, \
             patch.object(updater_mod.subprocess, "run", return_value=fetch_result) as mock_run, \
             patch.object(updater_mod, "check_for_update", return_value=(False, "1.0.0")), \
             patch.object(updater_mod, "_get_local_git_version", return_value="1.0.0"):
            mock_sys.platform = "darwin"
            updater_mod.check_for_update_source(Path("."))

        first_kwargs = mock_run.call_args_list[0][1]
        assert "creationflags" not in first_kwargs
