"""Tests for FIX-018: get_github_token() in github_auth.py.

Covers all three token sources and all failure/fallback paths.
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_run_result(stdout: str = "", returncode: int = 0) -> MagicMock:
    """Return a MagicMock mimicking subprocess.CompletedProcess."""
    mock = MagicMock()
    mock.stdout = stdout
    mock.returncode = returncode
    return mock


# ---------------------------------------------------------------------------
# GITHUB_TOKEN environment variable (priority 1)
# ---------------------------------------------------------------------------

class TestGithubTokenEnvVar:
    def test_returns_github_token_when_set(self):
        """GITHUB_TOKEN env var is returned first."""
        from launcher.core.github_auth import get_github_token
        with patch.dict("os.environ", {"GITHUB_TOKEN": "ghp_test123", "GH_TOKEN": ""}, clear=False):
            token = get_github_token()
        assert token == "ghp_test123"

    def test_github_token_strips_whitespace(self):
        """Leading/trailing whitespace is stripped from GITHUB_TOKEN."""
        from launcher.core.github_auth import get_github_token
        with patch.dict("os.environ", {"GITHUB_TOKEN": "  ghp_abc  "}, clear=False):
            token = get_github_token()
        assert token == "ghp_abc"

    def test_github_token_preferred_over_gh_token(self):
        """GITHUB_TOKEN takes priority even when GH_TOKEN is also set."""
        from launcher.core.github_auth import get_github_token
        with patch.dict("os.environ", {"GITHUB_TOKEN": "primary_tok", "GH_TOKEN": "secondary_tok"}, clear=False):
            token = get_github_token()
        assert token == "primary_tok"

    def test_empty_github_token_falls_through(self):
        """Empty GITHUB_TOKEN is treated as absent — falls through to GH_TOKEN."""
        from launcher.core.github_auth import get_github_token
        with patch.dict("os.environ", {"GITHUB_TOKEN": "", "GH_TOKEN": "gh_tok_fallback"}, clear=False):
            token = get_github_token()
        assert token == "gh_tok_fallback"

    def test_whitespace_only_github_token_falls_through(self):
        """Whitespace-only GITHUB_TOKEN is treated as absent."""
        from launcher.core.github_auth import get_github_token
        with patch.dict("os.environ", {"GITHUB_TOKEN": "   ", "GH_TOKEN": "real_token"}, clear=False):
            token = get_github_token()
        assert token == "real_token"


# ---------------------------------------------------------------------------
# GH_TOKEN environment variable (priority 2)
# ---------------------------------------------------------------------------

class TestGhTokenEnvVar:
    def test_returns_gh_token_when_github_token_absent(self):
        """GH_TOKEN is used when GITHUB_TOKEN is not set."""
        from launcher.core.github_auth import get_github_token
        env = {"GH_TOKEN": "cli_token_xyz"}
        # Ensure GITHUB_TOKEN is absent
        with patch.dict("os.environ", env, clear=False):
            with patch("os.environ.get") as mock_get:
                mock_get.side_effect = lambda key, default="": {
                    "GITHUB_TOKEN": "",
                    "GH_TOKEN": "cli_token_xyz",
                }.get(key, default)
                token = get_github_token()
        assert token == "cli_token_xyz"

    def test_gh_token_strips_whitespace(self):
        """GH_TOKEN has whitespace stripped."""
        from launcher.core.github_auth import get_github_token
        with patch("os.environ.get") as mock_get:
            mock_get.side_effect = lambda key, default="": {
                "GITHUB_TOKEN": "",
                "GH_TOKEN": "  tok_padded  ",
            }.get(key, default)
            token = get_github_token()
        assert token == "tok_padded"

    def test_empty_gh_token_falls_through_to_cli(self):
        """Empty GH_TOKEN falls through to the GitHub CLI."""
        from launcher.core.github_auth import get_github_token
        mock_result = _make_run_result(stdout="cli_tok_from_gh\n")
        with patch("os.environ.get") as mock_get, \
             patch("subprocess.run", return_value=mock_result):
            mock_get.side_effect = lambda key, default="": {
                "GITHUB_TOKEN": "",
                "GH_TOKEN": "",
            }.get(key, default)
            token = get_github_token()
        assert token == "cli_tok_from_gh"


# ---------------------------------------------------------------------------
# GitHub CLI — subprocess fallback (priority 3)
# ---------------------------------------------------------------------------

class TestGithubCliSubprocess:
    def test_returns_token_from_gh_auth_token(self):
        """Token is retrieved from 'gh auth token' when env vars are absent."""
        from launcher.core.github_auth import get_github_token
        mock_result = _make_run_result(stdout="ghp_cli_token\n")
        with patch("os.environ.get", return_value=""), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            token = get_github_token()
        assert token == "ghp_cli_token"
        # Verify list args and no shell=True
        call_args = mock_run.call_args
        assert call_args[0][0] == ["gh", "auth", "token"]
        assert call_args[1].get("shell", False) is False

    def test_subprocess_called_with_list_args(self):
        """subprocess.run is invoked with a list, not a shell string."""
        from launcher.core.github_auth import get_github_token
        mock_result = _make_run_result(stdout="tok")
        with patch("os.environ.get", return_value=""), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            get_github_token()
        args = mock_run.call_args[0][0]
        assert isinstance(args, list)
        assert args == ["gh", "auth", "token"]

    def test_subprocess_timeout_is_three_seconds(self):
        """subprocess.run is called with timeout=3."""
        from launcher.core.github_auth import get_github_token
        mock_result = _make_run_result(stdout="tok")
        with patch("os.environ.get", return_value=""), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            get_github_token()
        kwargs = mock_run.call_args[1]
        assert kwargs.get("timeout") == 3

    def test_cli_token_strips_whitespace(self):
        """Token from CLI has leading/trailing whitespace stripped."""
        from launcher.core.github_auth import get_github_token
        mock_result = _make_run_result(stdout="  ghp_padded  \n")
        with patch("os.environ.get", return_value=""), \
             patch("subprocess.run", return_value=mock_result):
            token = get_github_token()
        assert token == "ghp_padded"

    def test_returns_none_when_gh_not_installed(self):
        """Returns None when FileNotFoundError (gh not installed)."""
        from launcher.core.github_auth import get_github_token
        with patch("os.environ.get", return_value=""), \
             patch("subprocess.run", side_effect=FileNotFoundError("gh not found")):
            token = get_github_token()
        assert token is None

    def test_returns_none_on_timeout(self):
        """Returns None when subprocess.TimeoutExpired."""
        from launcher.core.github_auth import get_github_token
        with patch("os.environ.get", return_value=""), \
             patch("subprocess.run", side_effect=subprocess.TimeoutExpired("gh", 3)):
            token = get_github_token()
        assert token is None

    def test_returns_none_on_os_error(self):
        """Returns None on generic OSError."""
        from launcher.core.github_auth import get_github_token
        with patch("os.environ.get", return_value=""), \
             patch("subprocess.run", side_effect=OSError("permission denied")):
            token = get_github_token()
        assert token is None

    def test_returns_none_when_gh_outputs_empty_string(self):
        """Returns None when 'gh auth token' outputs only whitespace."""
        from launcher.core.github_auth import get_github_token
        mock_result = _make_run_result(stdout="   \n")
        with patch("os.environ.get", return_value=""), \
             patch("subprocess.run", return_value=mock_result):
            token = get_github_token()
        assert token is None


# ---------------------------------------------------------------------------
# No authentication available
# ---------------------------------------------------------------------------

class TestNoAuthAvailable:
    def test_returns_none_when_nothing_available(self):
        """Returns None when all three sources are unavailable."""
        from launcher.core.github_auth import get_github_token
        mock_result = _make_run_result(stdout="")
        with patch("os.environ.get", return_value=""), \
             patch("subprocess.run", return_value=mock_result):
            token = get_github_token()
        assert token is None
