"""FIX-018 Tester edge-case tests.

Covers attack vectors and boundary conditions not addressed in the Developer
tests:
  - gh auth token exits non-zero (success/failure path split)
  - gh exits non-zero with error text on stdout (returncode-not-checked bug)
  - 401 Unauthorized from GitHub API (invalid/expired token)
  - Token value not present in logging output
  - All three sources fail simultaneously via exceptions
  - PermissionError (subclass of OSError) from subprocess
"""

from __future__ import annotations

import importlib
import json
import logging
import subprocess
import sys
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GET_TOKEN_UPDATER = "launcher.core.updater.get_github_token"
_GET_TOKEN_DOWNLOADER = "launcher.core.downloader.get_github_token"


def _make_run_result(stdout: str = "", returncode: int = 0) -> MagicMock:
    """Return a MagicMock mimicking subprocess.CompletedProcess."""
    mock = MagicMock()
    mock.stdout = stdout
    mock.returncode = returncode
    return mock


def _make_mock_json_response(payload: dict) -> MagicMock:
    """Return a mock urlopen context-manager response with JSON payload."""
    body = json.dumps(payload).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# Edge case 1: gh exits non-zero with EMPTY stdout — must return None
# ---------------------------------------------------------------------------

class TestGhNonzeroExitEmptyStdout:
    def test_nonzero_exit_empty_stdout_returns_none(self):
        """Non-zero exit code from gh auth token with empty stdout → None.

        The typical real-world gh failure case: exit 1, error goes to stderr,
        stdout is empty. Expected: None.
        """
        from launcher.core.github_auth import get_github_token

        mock_result = _make_run_result(stdout="", returncode=1)
        with patch("os.environ.get", return_value=""), \
             patch("subprocess.run", return_value=mock_result):
            token = get_github_token()

        assert token is None, (
            "Non-zero exit from gh with empty stdout must return None"
        )

    def test_nonzero_exit_whitespace_stdout_returns_none(self):
        """Non-zero exit with whitespace-only stdout → None (strip makes it empty)."""
        from launcher.core.github_auth import get_github_token

        mock_result = _make_run_result(stdout="   \n", returncode=1)
        with patch("os.environ.get", return_value=""), \
             patch("subprocess.run", return_value=mock_result):
            token = get_github_token()

        assert token is None


# ---------------------------------------------------------------------------
# Edge case 2: gh exits non-zero with ERROR TEXT on stdout
#
# The spec states: "Returns None if no auth is available."
# A non-zero returncode IS a failure — the stdout content must not be used
# as a token, regardless of whether it looks like text or not.
# ---------------------------------------------------------------------------

class TestGhNonzeroExitWithStdoutContent:
    def test_nonzero_exit_with_error_text_on_stdout_returns_none(self):
        """gh exits non-zero AND stdout has error text → must return None.

        If returncode is not validated, the error text would be treated as a
        valid token and sent in an Authorization header — violating the
        'Returns None on any failure' contract.
        """
        from launcher.core.github_auth import get_github_token

        error_text = "error: not logged in to any GitHub hosts. Run gh auth login to authenticate."
        mock_result = _make_run_result(stdout=error_text + "\n", returncode=1)
        with patch("os.environ.get", return_value=""), \
             patch("subprocess.run", return_value=mock_result):
            token = get_github_token()

        assert token is None, (
            "get_github_token() must return None when gh auth token exits non-zero, "
            f"even if stdout is non-empty. Got: {token!r}"
        )

    def test_nonzero_exit_error_text_not_used_as_auth_header(self):
        """gh exits non-zero with token-shaped stdout → that text must NOT reach updater.

        Ensures the error-text-as-token value cannot accidentally appear in an
        Authorization header sent to the GitHub API.
        """
        from launcher.core.updater import check_for_update

        error_text = "error: this is not a real token"
        bad_run_result = _make_run_result(stdout=error_text, returncode=1)
        captured_requests: list = []
        mock_resp = _make_mock_json_response({"tag_name": "v1.0.0"})

        def _urlopen_side_effect(req, timeout=None):
            captured_requests.append(req)
            return mock_resp

        # Both env vars absent; gh CLI returns non-zero with error text
        with patch("os.environ.get", return_value=""), \
             patch("subprocess.run", return_value=bad_run_result), \
             patch("urllib.request.urlopen", side_effect=_urlopen_side_effect):
            check_for_update("0.9.9")

        assert len(captured_requests) >= 1
        auth_header = captured_requests[0].get_header("Authorization")
        # Either no header (correct: None returned → no header added) or
        # must not contain the error text.
        if auth_header is not None:
            assert error_text not in auth_header, (
                "Error text from gh auth token stdout must not appear in Authorization header"
            )


# ---------------------------------------------------------------------------
# Edge case 3: 401 Unauthorized response from GitHub API
# ---------------------------------------------------------------------------

class TestApiReturns401:
    def test_updater_401_returns_no_update_silently(self):
        """check_for_update silently returns (False, current) when API returns 401."""
        from launcher.core.updater import check_for_update

        with patch(_GET_TOKEN_UPDATER, return_value="invalid_or_expired_token"), \
             patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
                 url="https://api.github.com/repos/x/y/releases/latest",
                 code=401,
                 msg="Unauthorized",
                 hdrs=None,
                 fp=None,
             )):
            available, latest = check_for_update("1.0.2")

        assert available is False
        assert latest == "1.0.2"

    def test_downloader_401_raises_runtime_error(self):
        """download_update raises RuntimeError when metadata request returns 401."""
        from launcher.core import downloader

        with patch(_GET_TOKEN_DOWNLOADER, return_value="invalid_token"), \
             patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
                 url="https://api.github.com/repos/x/y/releases/tags/v1.0.0",
                 code=401,
                 msg="Unauthorized",
                 hdrs=None,
                 fp=None,
             )), \
             patch.object(sys, "platform", "win32"), \
             patch("platform.machine", return_value="x86_64"):
            with pytest.raises(RuntimeError, match="401"):
                downloader.download_update("1.0.0")

    def test_updater_403_forbidden_returns_no_update_silently(self):
        """check_for_update silently returns (False, current) when API returns 403."""
        from launcher.core.updater import check_for_update

        with patch(_GET_TOKEN_UPDATER, return_value="rate_limited_token"), \
             patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
                 url="https://api.github.com/repos/x/y/releases/latest",
                 code=403,
                 msg="Forbidden",
                 hdrs=None,
                 fp=None,
             )):
            available, latest = check_for_update("1.0.2")

        assert available is False
        assert latest == "1.0.2"


# ---------------------------------------------------------------------------
# Edge case 4: Token value must not appear in log records
# ---------------------------------------------------------------------------

class TestTokenNotInLogs:
    def test_token_not_in_downloader_log_records(self):
        """Token value must not appear in any log record emitted by downloader.py."""
        from launcher.core import downloader

        SECRET_TOKEN = "ghp_SUPERSECRET_TESTER_VERIFY_NOT_LOGGED"

        captured_messages: list[str] = []

        class CapturingHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                captured_messages.append(self.format(record))

        handler = CapturingHandler()
        dl_logger = logging.getLogger("launcher.core.downloader")
        dl_logger.addHandler(handler)
        dl_logger.setLevel(logging.DEBUG)

        asset_url = "https://objects.githubusercontent.com/file.exe"
        release_payload = {
            "tag_name": "v1.0.3",
            "assets": [
                {
                    "name": "AgentEnvironmentLauncher-x86_64.exe",
                    "browser_download_url": asset_url,
                },
                {
                    "name": "AgentEnvironmentLauncher-x86_64.exe.sha256",
                    "browser_download_url": asset_url + ".sha256",
                },
            ],
        }

        call_count = [0]
        meta_resp = _make_mock_json_response(release_payload)

        sha_resp = MagicMock()
        sha_resp.read.return_value = b"aabbccdd  file.exe\n"
        sha_resp.__enter__ = MagicMock(return_value=sha_resp)
        sha_resp.__exit__ = MagicMock(return_value=False)

        asset_resp = MagicMock()
        asset_resp.__enter__ = MagicMock(return_value=asset_resp)
        asset_resp.__exit__ = MagicMock(return_value=False)
        asset_resp.read.side_effect = [b"fake_data", b""]

        def _urlopen_side_effect(req, timeout=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return meta_resp
            if call_count[0] == 2:
                return asset_resp
            return sha_resp

        try:
            with patch(_GET_TOKEN_DOWNLOADER, return_value=SECRET_TOKEN), \
                 patch("urllib.request.urlopen", side_effect=_urlopen_side_effect), \
                 patch.object(sys, "platform", "win32"), \
                 patch("platform.machine", return_value="x86_64"):
                try:
                    downloader.download_update("1.0.3")
                except Exception:
                    pass
        finally:
            dl_logger.removeHandler(handler)

        for message in captured_messages:
            assert SECRET_TOKEN not in message, (
                f"Token appeared in log record: {message!r}"
            )

    def test_token_not_printed_to_stdout_in_github_auth(self):
        """get_github_token() must not print the token to stdout or stderr."""
        import io
        from contextlib import redirect_stdout, redirect_stderr
        from launcher.core.github_auth import get_github_token

        SECRET = "ghp_MUST_NOT_BE_PRINTED"
        mock_result = _make_run_result(stdout=SECRET, returncode=0)

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            with patch("os.environ.get", return_value=""), \
                 patch("subprocess.run", return_value=mock_result):
                get_github_token()

        stdout_output = stdout_buf.getvalue()
        stderr_output = stderr_buf.getvalue()

        assert SECRET not in stdout_output, "Token must not be printed to stdout"
        assert SECRET not in stderr_output, "Token must not be printed to stderr"


# ---------------------------------------------------------------------------
# Edge case 5: All three sources fail via exceptions simultaneously
# ---------------------------------------------------------------------------

class TestAllSourcesFailViaExceptions:
    def test_all_sources_fail_returns_none(self):
        """All three sources unavailable (env absent + CLI raises) → None."""
        from launcher.core.github_auth import get_github_token

        with patch("os.environ.get", return_value=""), \
             patch("subprocess.run", side_effect=FileNotFoundError("gh not found")):
            token = get_github_token()

        assert token is None

    def test_permission_error_from_subprocess_returns_none(self):
        """PermissionError (subclass of OSError) from subprocess → None.

        Verifies the OSError catch covers PermissionError on restrictive OS configs.
        """
        from launcher.core.github_auth import get_github_token

        with patch("os.environ.get", return_value=""), \
             patch("subprocess.run", side_effect=PermissionError("access denied")):
            token = get_github_token()

        assert token is None

    def test_env_vars_missing_from_os_environ_entirely(self):
        """When the env vars are not present at all (KeyError scenario) → None.

        os.environ.get(key, '') handles missing keys, but this confirms the
        fallback to CLI also works when env vars are absent, not just empty.
        """
        from launcher.core.github_auth import get_github_token

        # Simulate environment where these keys do not exist
        clean_env = {k: v for k, v in __import__("os").environ.items()
                     if k not in ("GITHUB_TOKEN", "GH_TOKEN")}

        with patch.dict("os.environ", clean_env, clear=True), \
             patch("subprocess.run", side_effect=FileNotFoundError("no gh")):
            token = get_github_token()

        assert token is None


# ---------------------------------------------------------------------------
# Edge case 6: check_for_update called while get_github_token raises
# ---------------------------------------------------------------------------

class TestGetTokenRaisesInUpdater:
    def test_check_for_update_survives_get_token_exception(self):
        """check_for_update still returns (False, current) even if get_github_token raises.

        get_github_token() should never raise internally (all exceptions caught),
        but if a future refactor breaks this, the updater must not crash.
        """
        from launcher.core.updater import check_for_update

        with patch(_GET_TOKEN_UPDATER, side_effect=RuntimeError("unexpected token error")):
            # The try/except Exception in check_for_update must catch this
            available, latest = check_for_update("1.0.2")

        assert available is False
        assert latest == "1.0.2"
