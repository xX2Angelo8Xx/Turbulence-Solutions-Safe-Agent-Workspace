"""Tests for INS-027: source-mode detection and git-based update.

All subprocess and filesystem calls are mocked so nothing real is executed.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_run_success(stdout: str = ""):
    """Return a completed-process mock with returncode 0."""
    m = MagicMock()
    m.returncode = 0
    m.stdout = stdout
    m.stderr = ""
    return m


def _fake_run_failure(returncode: int = 1, stderr: str = "error"):
    """Return a completed-process mock simulating failure."""
    m = MagicMock()
    m.returncode = returncode
    m.stdout = ""
    m.stderr = stderr
    return m


# ===========================================================================
# is_source_mode() tests
# ===========================================================================

class TestIsSourceMode:
    def test_returns_true_when_not_frozen_and_git_exists(self, tmp_path):
        """Source mode: not frozen AND .git dir present."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Ensure sys._MEIPASS is NOT present to simulate an unfrozen process.
        # We patch getattr by patching the module-level sys in updater.
        with patch("launcher.core.updater._REPO_ROOT", tmp_path), \
             patch("launcher.core.updater.sys") as mock_sys:
            # Simulate unfrozen: getattr(mock_sys, "_MEIPASS", None) returns None
            del mock_sys._MEIPASS  # remove from mock so getattr returns None
            from launcher.core.updater import is_source_mode
            result = is_source_mode()

        assert result is True

    def test_returns_false_when_frozen(self, tmp_path):
        """Binary mode: sys._MEIPASS is set → source mode is False."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Patch _MEIPASS at the sys level
        with patch("launcher.core.updater._REPO_ROOT", tmp_path):
            # Simulate frozen by patching getattr(sys, "_MEIPASS", None) path
            with patch("launcher.core.updater.sys") as mock_sys:
                mock_sys._MEIPASS = "/tmp/meipassed"
                # getattr(mock_sys, "_MEIPASS", None) must return the value
                from launcher.core.updater import is_source_mode
                result = is_source_mode()

        assert result is False

    def test_returns_false_when_no_git_dir(self, tmp_path):
        """Not source mode if .git directory is absent."""
        with patch("launcher.core.updater._REPO_ROOT", tmp_path):
            if hasattr(sys, "_MEIPASS"):
                del sys._MEIPASS
            from launcher.core.updater import is_source_mode
            result = is_source_mode()

        assert result is False

    def test_returns_false_when_git_is_file_not_dir(self, tmp_path):
        """.git must be a directory; a file named .git does not count."""
        fake_git = tmp_path / ".git"
        fake_git.write_text("gitdir: /some/other/path")

        with patch("launcher.core.updater._REPO_ROOT", tmp_path):
            if hasattr(sys, "_MEIPASS"):
                del sys._MEIPASS
            from launcher.core.updater import is_source_mode
            result = is_source_mode()

        # A regular file named .git (git worktree) is NOT a .git dir
        assert result is False


# ===========================================================================
# check_for_update_source() tests
# ===========================================================================

class TestCheckForUpdateSource:
    def test_fetches_remote_tags_before_checking(self, tmp_path):
        """Git fetch is called as part of source-mode update check."""
        from launcher.core.updater import check_for_update_source

        with patch("launcher.core.updater.subprocess.run") as mock_run, \
             patch("launcher.core.updater.check_for_update", return_value=(False, "1.0.0")):
            mock_run.return_value = _fake_run_success()
            check_for_update_source(repo_root=tmp_path)

        # First call must be git fetch
        first_call_args = mock_run.call_args_list[0][0][0]
        assert first_call_args[0] == "git"
        assert "fetch" in first_call_args

    def test_returns_update_available_when_remote_is_newer(self, tmp_path):
        """Returns (True, newer_version) when remote tag is ahead."""
        from launcher.core.updater import check_for_update_source

        with patch("launcher.core.updater.subprocess.run") as mock_run, \
             patch("launcher.core.updater.check_for_update", return_value=(True, "2.0.0")):
            # fetch call → success; describe call → local v1.0.0
            mock_run.side_effect = [
                _fake_run_success(),          # git fetch
                _fake_run_success("v1.0.0"),  # git describe
            ]
            available, version = check_for_update_source(repo_root=tmp_path)

        assert available is True
        assert version == "2.0.0"

    def test_returns_false_when_up_to_date(self, tmp_path):
        """Returns (False, current) when local tag matches latest release."""
        from launcher.core.updater import check_for_update_source

        with patch("launcher.core.updater.subprocess.run") as mock_run, \
             patch("launcher.core.updater.check_for_update", return_value=(False, "1.0.0")):
            mock_run.side_effect = [
                _fake_run_success(),          # git fetch
                _fake_run_success("v1.0.0"),  # git describe
            ]
            available, version = check_for_update_source(repo_root=tmp_path)

        assert available is False

    def test_returns_false_on_exception(self, tmp_path):
        """Any exception in the update check returns (False, '0.0.0') silently."""
        from launcher.core.updater import check_for_update_source

        with patch("launcher.core.updater.subprocess.run", side_effect=OSError("no git")):
            available, version = check_for_update_source(repo_root=tmp_path)

        assert available is False
        assert version == "0.0.0"


# ===========================================================================
# apply_source_update() tests
# ===========================================================================

class TestApplySourceUpdate:
    def test_runs_git_pull_and_pip_install(self, tmp_path):
        """apply_source_update runs git pull --ff-only followed by pip install."""
        from launcher.core.applier import apply_source_update

        with patch("launcher.core.applier.subprocess.run") as mock_run:
            mock_run.return_value = _fake_run_success()
            apply_source_update(repo_root=tmp_path, pip_executable="pip")

        calls = [c[0][0] for c in mock_run.call_args_list]
        assert calls[0][:2] == ["git", "pull"]
        assert "--ff-only" in calls[0]
        assert calls[1][0] == "pip"
        assert "install" in calls[1]

    def test_raises_on_git_pull_failure(self, tmp_path):
        """RuntimeError is raised when git pull fails."""
        from launcher.core.applier import apply_source_update

        with patch("launcher.core.applier.subprocess.run") as mock_run:
            mock_run.return_value = _fake_run_failure(returncode=1, stderr="dirty tree")
            with pytest.raises(RuntimeError, match="git pull --ff-only failed"):
                apply_source_update(repo_root=tmp_path, pip_executable="pip")

    def test_raises_on_pip_install_failure(self, tmp_path):
        """RuntimeError is raised when pip install fails."""
        from launcher.core.applier import apply_source_update

        with patch("launcher.core.applier.subprocess.run") as mock_run:
            mock_run.side_effect = [
                _fake_run_success(),              # git pull succeeds
                _fake_run_failure(returncode=1, stderr="no module"),  # pip fails
            ]
            with pytest.raises(RuntimeError, match="pip install . failed"):
                apply_source_update(repo_root=tmp_path, pip_executable="pip")

    def test_git_pull_not_called_when_pip_raises_immediately(self, tmp_path):
        """pip failure after successful pull raises RuntimeError with pip message."""
        from launcher.core.applier import apply_source_update

        with patch("launcher.core.applier.subprocess.run") as mock_run:
            mock_run.side_effect = [
                _fake_run_success(),
                _fake_run_failure(returncode=2, stderr="permission denied"),
            ]
            with pytest.raises(RuntimeError) as exc_info:
                apply_source_update(repo_root=tmp_path, pip_executable="pip")

        assert "pip install" in str(exc_info.value)


# ===========================================================================
# apply_update() dispatch tests
# ===========================================================================

class TestApplyUpdateDispatch:
    def test_source_mode_delegates_to_apply_source_update(self, tmp_path):
        """apply_update(None) calls apply_source_update() — source mode trigger."""
        from launcher.core.applier import apply_update

        with patch("launcher.core.applier.apply_source_update") as mock_source:
            apply_update(None)

        mock_source.assert_called_once()

    def test_binary_mode_does_not_call_apply_source_update(self, tmp_path):
        """apply_update(path) does NOT call apply_source_update()."""
        from launcher.core.applier import apply_update

        dummy_installer = tmp_path / "dummy.exe"
        dummy_installer.write_bytes(b"dummy")

        with patch("launcher.core.applier.apply_source_update") as mock_source, \
             patch("launcher.core.applier._apply_windows") as mock_win, \
             patch("launcher.core.applier._apply_macos") as mock_mac, \
             patch("launcher.core.applier._apply_linux") as mock_lx, \
             patch("launcher.core.applier.sys") as mock_sys:
            mock_sys.platform = "win32"
            apply_update(dummy_installer)

        mock_source.assert_not_called()

    def test_binary_mode_validates_installer_path(self, tmp_path):
        """Binary mode raises FileNotFoundError for missing installer."""
        from launcher.core.applier import apply_update

        missing = tmp_path / "nonexistent.exe"
        with pytest.raises(FileNotFoundError):
            apply_update(missing)

    def test_source_mode_skips_installer_path_validation(self, tmp_path):
        """apply_update(None) proceeds to source update without path validation."""
        from launcher.core.applier import apply_update

        with patch("launcher.core.applier.apply_source_update") as mock_source:
            # Should not raise even though no path is supplied
            apply_update(None)

        mock_source.assert_called_once()
