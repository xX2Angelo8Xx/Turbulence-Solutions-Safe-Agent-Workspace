"""FIX-120 regression tests — Suppress terminal windows during git init.

Verifies that _init_git_repository() passes subprocess.CREATE_NO_WINDOW
as a creationflag on Windows, and does not pass it on other platforms.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_success_result() -> MagicMock:
    """Return a mock CompletedProcess with returncode 0."""
    result = MagicMock()
    result.returncode = 0
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCreateNoWindowOnWindows:
    """CREATE_NO_WINDOW must be present in the common kwargs on win32."""

    def test_create_no_window_flag_set_on_windows(self, tmp_path: Path) -> None:
        """creationflags=CREATE_NO_WINDOW is passed to every subprocess.run call on Windows."""
        with (
            patch("launcher.core.project_creator.sys.platform", "win32"),
            patch("launcher.core.project_creator.subprocess.run") as mock_run,
        ):
            mock_run.return_value = _make_success_result()
            from launcher.core.project_creator import _init_git_repository

            _init_git_repository(tmp_path)

            # Every call must have creationflags with CREATE_NO_WINDOW.
            for c in mock_run.call_args_list:
                kwargs = c.kwargs if c.kwargs else c[1]
                assert "creationflags" in kwargs, (
                    f"creationflags missing in call: {c}"
                )
                assert kwargs["creationflags"] == subprocess.CREATE_NO_WINDOW, (
                    f"Expected CREATE_NO_WINDOW, got {kwargs['creationflags']!r}"
                )

    def test_no_creationflags_on_non_windows(self, tmp_path: Path) -> None:
        """creationflags must NOT be present when platform is not win32."""
        with (
            patch("launcher.core.project_creator.sys.platform", "linux"),
            patch("launcher.core.project_creator.subprocess.run") as mock_run,
        ):
            mock_run.return_value = _make_success_result()
            from launcher.core.project_creator import _init_git_repository

            _init_git_repository(tmp_path)

            for c in mock_run.call_args_list:
                kwargs = c.kwargs if c.kwargs else c[1]
                assert "creationflags" not in kwargs, (
                    f"Unexpected creationflags in call on non-Windows: {c}"
                )

    def test_no_creationflags_on_darwin(self, tmp_path: Path) -> None:
        """creationflags must NOT be present when platform is darwin."""
        with (
            patch("launcher.core.project_creator.sys.platform", "darwin"),
            patch("launcher.core.project_creator.subprocess.run") as mock_run,
        ):
            mock_run.return_value = _make_success_result()
            from launcher.core.project_creator import _init_git_repository

            _init_git_repository(tmp_path)

            for c in mock_run.call_args_list:
                kwargs = c.kwargs if c.kwargs else c[1]
                assert "creationflags" not in kwargs


class TestGitInitBehaviour:
    """Behavioural tests for _init_git_repository."""

    def test_git_init_called_first(self, tmp_path: Path) -> None:
        """git init must be the first subprocess call."""
        with (
            patch("launcher.core.project_creator.sys.platform", "linux"),
            patch("launcher.core.project_creator.subprocess.run") as mock_run,
        ):
            mock_run.return_value = _make_success_result()
            from launcher.core.project_creator import _init_git_repository

            _init_git_repository(tmp_path)

            first_call_args = mock_run.call_args_list[0][0][0]
            assert first_call_args == ["git", "init"]

    def test_returns_true_on_success(self, tmp_path: Path) -> None:
        """Returns True when all git subprocesses succeed."""
        with (
            patch("launcher.core.project_creator.sys.platform", "linux"),
            patch("launcher.core.project_creator.subprocess.run") as mock_run,
        ):
            mock_run.return_value = _make_success_result()
            from launcher.core.project_creator import _init_git_repository

            result = _init_git_repository(tmp_path)
            assert result is True

    def test_returns_false_when_git_init_fails(self, tmp_path: Path) -> None:
        """Returns False when git init returns non-zero exit code."""
        fail_result = MagicMock()
        fail_result.returncode = 128

        with (
            patch("launcher.core.project_creator.sys.platform", "linux"),
            patch("launcher.core.project_creator.subprocess.run") as mock_run,
        ):
            mock_run.return_value = fail_result
            from launcher.core.project_creator import _init_git_repository

            result = _init_git_repository(tmp_path)
            assert result is False

    def test_returns_false_on_os_error(self, tmp_path: Path) -> None:
        """Returns False (non-fatal) when git is not installed (OSError)."""
        with (
            patch("launcher.core.project_creator.sys.platform", "linux"),
            patch(
                "launcher.core.project_creator.subprocess.run",
                side_effect=OSError("git not found"),
            ),
        ):
            from launcher.core.project_creator import _init_git_repository

            result = _init_git_repository(tmp_path)
            assert result is False

    def test_returns_false_on_timeout(self, tmp_path: Path) -> None:
        """Returns False (non-fatal) when a git subprocess times out."""
        with (
            patch("launcher.core.project_creator.sys.platform", "linux"),
            patch(
                "launcher.core.project_creator.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="git", timeout=30),
            ),
        ):
            from launcher.core.project_creator import _init_git_repository

            result = _init_git_repository(tmp_path)
            assert result is False

    def test_cwd_set_to_workspace(self, tmp_path: Path) -> None:
        """cwd must be set to the workspace path in every subprocess call."""
        with (
            patch("launcher.core.project_creator.sys.platform", "linux"),
            patch("launcher.core.project_creator.subprocess.run") as mock_run,
        ):
            mock_run.return_value = _make_success_result()
            from launcher.core.project_creator import _init_git_repository

            _init_git_repository(tmp_path)

            for c in mock_run.call_args_list:
                kwargs = c.kwargs if c.kwargs else c[1]
                assert kwargs["cwd"] == str(tmp_path)
