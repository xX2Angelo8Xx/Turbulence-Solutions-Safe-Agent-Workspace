"""Tester edge-case tests for INS-027: source-mode detection and git-based update.

These tests extend the developer's suite with boundary conditions, platform
specifics, and subtle contract verifications that the developer's tests did
not exercise.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_proc(returncode: int = 0, stdout: str = "", stderr: str = ""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


# ===========================================================================
# _get_local_git_version() — direct unit tests
# The developer only tested this function indirectly through
# check_for_update_source().  These tests cover it in isolation.
# ===========================================================================

class TestGetLocalGitVersionDirect:
    """Direct tests for _get_local_git_version()."""

    def test_returns_version_string_on_success(self, tmp_path):
        """Happy-path: git returns 'v2.1.0' → returns '2.1.0'."""
        from launcher.core.updater import _get_local_git_version

        with patch("launcher.core.updater.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(returncode=0, stdout="v2.1.0\n")
            result = _get_local_git_version(tmp_path)

        assert result == "2.1.0"

    def test_strips_v_prefix_from_tag(self, tmp_path):
        """Leading 'v' is stripped, e.g. 'v0.9.3' → '0.9.3'."""
        from launcher.core.updater import _get_local_git_version

        with patch("launcher.core.updater.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(returncode=0, stdout="v0.9.3")
            result = _get_local_git_version(tmp_path)

        assert result == "0.9.3"

    def test_returns_fallback_when_git_returns_nonzero(self, tmp_path):
        """No tags in repo: git describe --tags exits non-zero → '0.0.0'."""
        from launcher.core.updater import _get_local_git_version

        with patch("launcher.core.updater.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(returncode=128, stderr="fatal: No names found")
            result = _get_local_git_version(tmp_path)

        assert result == "0.0.0"

    def test_returns_fallback_when_git_not_installed(self, tmp_path):
        """FileNotFoundError (git not in PATH) → fallback '0.0.0'."""
        from launcher.core.updater import _get_local_git_version

        with patch("launcher.core.updater.subprocess.run", side_effect=FileNotFoundError("git not found")):
            result = _get_local_git_version(tmp_path)

        assert result == "0.0.0"

    def test_returns_fallback_on_timeout(self, tmp_path):
        """TimeoutExpired from git describe is caught → fallback '0.0.0'."""
        from launcher.core.updater import _get_local_git_version

        timeout_exc = subprocess.TimeoutExpired(["git", "describe"], 10)
        with patch("launcher.core.updater.subprocess.run", side_effect=timeout_exc):
            result = _get_local_git_version(tmp_path)

        assert result == "0.0.0"

    def test_returns_fallback_on_os_error(self, tmp_path):
        """Generic OSError from subprocess (e.g. permission denied) → '0.0.0'."""
        from launcher.core.updater import _get_local_git_version

        with patch("launcher.core.updater.subprocess.run", side_effect=OSError("permission denied")):
            result = _get_local_git_version(tmp_path)

        assert result == "0.0.0"

    def test_git_describe_called_with_correct_args(self, tmp_path):
        """Verify git describe is called with --tags and --abbrev=0."""
        from launcher.core.updater import _get_local_git_version

        with patch("launcher.core.updater.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(returncode=0, stdout="v1.0.0")
            _get_local_git_version(tmp_path)

        args = mock_run.call_args[0][0]
        assert args[0] == "git"
        assert "describe" in args
        assert "--tags" in args
        assert "--abbrev=0" in args

    def test_git_describe_receives_cwd_as_repo_root(self, tmp_path):
        """Subprocess cwd is set to repo_root so git is run in the right directory."""
        from launcher.core.updater import _get_local_git_version

        with patch("launcher.core.updater.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(returncode=0, stdout="v1.0.0")
            _get_local_git_version(tmp_path)

        kwargs = mock_run.call_args[1]
        assert kwargs["cwd"] == str(tmp_path)


# ===========================================================================
# is_source_mode() — edge cases around sys._MEIPASS attribute
# ===========================================================================

class TestIsSourceModeMeipassEdgeCases:
    """Additional edge-case tests for is_source_mode() frozen detection."""

    def test_meipass_none_value_is_not_frozen(self, tmp_path):
        """sys._MEIPASS = None explicitly must NOT be treated as frozen."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("launcher.core.updater._REPO_ROOT", tmp_path), \
             patch("launcher.core.updater.sys") as mock_sys:
            # _MEIPASS attribute exists but is None (edge-case attribute presence)
            mock_sys._MEIPASS = None
            from launcher.core.updater import is_source_mode
            result = is_source_mode()

        # getattr(sys, "_MEIPASS", None) == None → falsy → NOT frozen
        assert result is True

    def test_meipass_empty_string_treats_as_frozen(self, tmp_path):
        """sys._MEIPASS = '' (empty string) is falsy — treated as NOT frozen.

        PyInstaller always sets _MEIPASS to a non-empty path, but we test
        the boundary value to document the truthiness-based check.
        """
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("launcher.core.updater._REPO_ROOT", tmp_path), \
             patch("launcher.core.updater.sys") as mock_sys:
            mock_sys._MEIPASS = ""
            from launcher.core.updater import is_source_mode
            result = is_source_mode()

        # "" is falsy → getattr returns "" → bool("") == False → NOT frozen
        assert result is True

    def test_meipass_nonempty_string_means_frozen(self, tmp_path):
        """sys._MEIPASS = '/tmp/_MEIPASSABC' (typical PyInstaller value) is frozen."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("launcher.core.updater._REPO_ROOT", tmp_path), \
             patch("launcher.core.updater.sys") as mock_sys:
            mock_sys._MEIPASS = "/tmp/_MEIPASSABC"
            from launcher.core.updater import is_source_mode
            result = is_source_mode()

        assert result is False


# ===========================================================================
# check_for_update_source() — additional edge cases
# ===========================================================================

class TestCheckForUpdateSourceEdgeCases:
    """Edge cases for check_for_update_source() not covered by developer tests."""

    def test_fetch_failure_is_silently_ignored(self, tmp_path):
        """git fetch returning non-zero does NOT abort the check.

        The function should continue to call _get_local_git_version regardless
        of whether the fetch succeeded.
        """
        from launcher.core.updater import check_for_update_source

        # Both fetch and describe calls in subprocess.run
        with patch("launcher.core.updater.subprocess.run") as mock_run, \
             patch("launcher.core.updater.check_for_update", return_value=(False, "1.0.0")):
            # fetch returns non-zero; describe succeeds
            mock_run.side_effect = [
                _make_proc(returncode=1, stderr="network error"),  # git fetch fails
                _make_proc(returncode=0, stdout="v1.0.0"),          # git describe ok
            ]
            available, version = check_for_update_source(repo_root=tmp_path)

        # Should still get a result (no exception raised)
        assert isinstance(available, bool)

    def test_local_version_ahead_of_remote_returns_false(self, tmp_path):
        """If local git tag is ahead of latest release, no update is returned."""
        from launcher.core.updater import check_for_update_source

        with patch("launcher.core.updater.subprocess.run") as mock_run, \
             patch("launcher.core.updater.check_for_update", return_value=(False, "1.0.0")):
            mock_run.side_effect = [
                _make_proc(returncode=0),              # git fetch
                _make_proc(returncode=0, stdout="v2.0.0"),  # git describe → local is 2.0.0
            ]
            available, _version = check_for_update_source(repo_root=tmp_path)

        assert available is False

    def test_returns_false_on_fetch_timeout(self, tmp_path):
        """TimeoutExpired during git fetch is caught → (False, '0.0.0')."""
        from launcher.core.updater import check_for_update_source

        timeout_exc = subprocess.TimeoutExpired(["git", "fetch"], 15)
        with patch("launcher.core.updater.subprocess.run", side_effect=timeout_exc):
            available, version = check_for_update_source(repo_root=tmp_path)

        assert available is False
        assert version == "0.0.0"

    def test_explicit_repo_root_is_used(self, tmp_path):
        """check_for_update_source passes repo_root as cwd for git commands."""
        from launcher.core.updater import check_for_update_source

        with patch("launcher.core.updater.subprocess.run") as mock_run, \
             patch("launcher.core.updater.check_for_update", return_value=(False, "1.0.0")):
            mock_run.return_value = _make_proc(returncode=0)
            check_for_update_source(repo_root=tmp_path)

        # All subprocess.run calls should use tmp_path as cwd
        for c in mock_run.call_args_list:
            assert c[1]["cwd"] == str(tmp_path)


# ===========================================================================
# apply_source_update() — pip path resolution and subprocess timeouts
# ===========================================================================

class TestApplySourceUpdatePipResolution:
    """Test that pip executable path is resolved correctly for each platform."""

    def test_pip_resolved_under_scripts_on_windows(self, tmp_path):
        """On Windows, pip is expected under <venv>/Scripts/pip."""
        from launcher.core.applier import apply_source_update

        fake_python = tmp_path / "Scripts" / "python.exe"
        fake_python.parent.mkdir(parents=True)
        fake_python.touch()

        with patch("launcher.core.applier.subprocess.run") as mock_run, \
             patch("launcher.core.applier.sys") as mock_sys:
            mock_run.return_value = _make_proc(returncode=0)
            mock_sys.executable = str(fake_python)
            mock_sys.platform = "win32"
            apply_source_update(repo_root=tmp_path)

        # The pip call should use <venv>/Scripts/pip
        pip_call_args = mock_run.call_args_list[1][0][0]
        assert "Scripts" in pip_call_args[0]
        assert "bin" not in pip_call_args[0]

    def test_pip_resolved_under_bin_on_unix(self, tmp_path):
        """On Unix, pip is expected under <venv>/bin/pip."""
        from launcher.core.applier import apply_source_update

        fake_python = tmp_path / "bin" / "python"
        fake_python.parent.mkdir(parents=True)
        fake_python.touch()

        with patch("launcher.core.applier.subprocess.run") as mock_run, \
             patch("launcher.core.applier.sys") as mock_sys:
            mock_run.return_value = _make_proc(returncode=0)
            mock_sys.executable = str(fake_python)
            mock_sys.platform = "linux"
            apply_source_update(repo_root=tmp_path)

        pip_call_args = mock_run.call_args_list[1][0][0]
        assert "bin" in pip_call_args[0]
        assert "Scripts" not in pip_call_args[0]

    def test_explicit_pip_executable_overrides_auto_detection(self, tmp_path):
        """When pip_executable is provided, auto-detection is skipped."""
        from launcher.core.applier import apply_source_update

        with patch("launcher.core.applier.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(returncode=0)
            apply_source_update(repo_root=tmp_path, pip_executable="/custom/pip")

        pip_call_args = mock_run.call_args_list[1][0][0]
        assert pip_call_args[0] == "/custom/pip"


class TestApplySourceUpdateSubprocessTimeouts:
    """Document actual behavior when subprocess calls time out.

    The docstring says 'Raises RuntimeError on any failure', but subprocess
    TimeoutExpired is NOT caught and propagates as-is.  These tests document
    the actual contract so callers are not surprised.
    """

    def test_git_pull_timeout_propagates_as_timeout_expired(self, tmp_path):
        """subprocess.TimeoutExpired from git pull is NOT wrapped in RuntimeError."""
        from launcher.core.applier import apply_source_update

        timeout_exc = subprocess.TimeoutExpired(["git", "pull", "--ff-only"], 60)
        with patch("launcher.core.applier.subprocess.run", side_effect=timeout_exc):
            with pytest.raises(subprocess.TimeoutExpired):
                apply_source_update(repo_root=tmp_path, pip_executable="pip")

    def test_pip_install_timeout_propagates_as_timeout_expired(self, tmp_path):
        """subprocess.TimeoutExpired from pip install is NOT wrapped in RuntimeError."""
        from launcher.core.applier import apply_source_update

        pip_timeout = subprocess.TimeoutExpired(["/venv/Scripts/pip", "install", "."], 120)

        with patch("launcher.core.applier.subprocess.run") as mock_run:
            mock_run.side_effect = [
                _make_proc(returncode=0),   # git pull succeeds
                pip_timeout,                # pip install times out
            ]
            with pytest.raises(subprocess.TimeoutExpired):
                apply_source_update(repo_root=tmp_path, pip_executable="pip")


# ===========================================================================
# apply_update() — backward compatibility guarantees
# ===========================================================================

class TestApplyUpdateBackwardCompatibility:
    """Verify that the binary/frozen path through apply_update() is unchanged."""

    def test_binary_mode_calls_validate_installer_path(self, tmp_path):
        """apply_update(path) always calls _validate_installer_path first."""
        from launcher.core import applier

        dummy = tmp_path / "installer.exe"
        dummy.write_bytes(b"dummy")

        with patch.object(applier, "_validate_installer_path") as mock_validate, \
             patch.object(applier, "_apply_windows"), \
             patch("launcher.core.applier.sys") as mock_sys:
            mock_sys.platform = "win32"
            applier.apply_update(dummy)

        mock_validate.assert_called_once_with(dummy)

    def test_binary_mode_missing_installer_raises_before_dispatch(self, tmp_path):
        """FileNotFoundError is raised immediately for a missing installer path."""
        from launcher.core.applier import apply_update

        missing = tmp_path / "no_such_file.exe"
        # No platform dispatch mock needed — validation fires first
        with pytest.raises(FileNotFoundError, match="not found"):
            apply_update(missing)

    def test_source_mode_never_calls_validate_installer_path(self, tmp_path):
        """apply_update(None) must NOT call _validate_installer_path."""
        from launcher.core import applier

        with patch.object(applier, "_validate_installer_path") as mock_validate, \
             patch.object(applier, "apply_source_update"):
            applier.apply_update(None)

        mock_validate.assert_not_called()

    def test_apply_update_with_path_does_not_delegate_to_source_update(self, tmp_path):
        """Binary mode: apply_source_update is never called when a path is given."""
        from launcher.core import applier

        dummy = tmp_path / "installer.exe"
        dummy.write_bytes(b"dummy")

        with patch.object(applier, "apply_source_update") as mock_source, \
             patch.object(applier, "_apply_windows"), \
             patch("launcher.core.applier.sys") as mock_sys:
            mock_sys.platform = "win32"
            applier.apply_update(dummy)

        mock_source.assert_not_called()


# ===========================================================================
# Security: subprocess calls must never use shell=True
# ===========================================================================

class TestSubprocessSecurityINS027:
    """Verify all subprocess calls in INS-027 code use shell=False (default)."""

    def test_apply_source_update_git_pull_no_shell_true(self, tmp_path):
        """git pull call must not use shell=True."""
        from launcher.core.applier import apply_source_update

        with patch("launcher.core.applier.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(returncode=0)
            apply_source_update(repo_root=tmp_path, pip_executable="pip")

        git_pull_call = mock_run.call_args_list[0]
        assert git_pull_call[1].get("shell", False) is False

    def test_apply_source_update_pip_install_no_shell_true(self, tmp_path):
        """pip install call must not use shell=True."""
        from launcher.core.applier import apply_source_update

        with patch("launcher.core.applier.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(returncode=0)
            apply_source_update(repo_root=tmp_path, pip_executable="pip")

        pip_call = mock_run.call_args_list[1]
        assert pip_call[1].get("shell", False) is False

    def test_get_local_git_version_no_shell_true(self, tmp_path):
        """git describe call must not use shell=True."""
        from launcher.core.updater import _get_local_git_version

        with patch("launcher.core.updater.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(returncode=0, stdout="v1.0.0")
            _get_local_git_version(tmp_path)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("shell", False) is False

    def test_check_for_update_source_fetch_no_shell_true(self, tmp_path):
        """git fetch call in check_for_update_source must not use shell=True."""
        from launcher.core.updater import check_for_update_source

        with patch("launcher.core.updater.subprocess.run") as mock_run, \
             patch("launcher.core.updater.check_for_update", return_value=(False, "1.0.0")):
            mock_run.return_value = _make_proc(returncode=0)
            check_for_update_source(repo_root=tmp_path)

        fetch_call_kwargs = mock_run.call_args_list[0][1]
        assert fetch_call_kwargs.get("shell", False) is False

    def test_subprocess_args_are_list_not_string(self, tmp_path):
        """All subprocess.run calls must pass args as a list, not a shell string.

        Passing a string with shell=False silently does the wrong thing on
        Windows and is a command injection risk on Unix.
        """
        from launcher.core.applier import apply_source_update

        with patch("launcher.core.applier.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(returncode=0)
            apply_source_update(repo_root=tmp_path, pip_executable="pip")

        for c in mock_run.call_args_list:
            args = c[0][0]
            assert isinstance(args, list), f"subprocess args must be a list, got {type(args)}: {args!r}"
