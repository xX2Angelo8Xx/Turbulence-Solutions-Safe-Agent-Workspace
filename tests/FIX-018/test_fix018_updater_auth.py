"""Tests for FIX-018: auth header in check_for_update() (updater.py).

Verifies that the Authorization header is included when a token is available
and absent when no token is available.
"""

from __future__ import annotations

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

# Patch target: get_github_token as imported in updater.py
_GET_TOKEN_PATH = "launcher.core.updater.get_github_token"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_response(payload: dict) -> MagicMock:
    """Return a mock urlopen context-manager response with JSON payload."""
    body = json.dumps(payload).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# Auth header present when token available
# ---------------------------------------------------------------------------

class TestCheckForUpdateAuthHeaderPresent:
    def test_authorization_header_added_when_token_available(self):
        """Authorization: Bearer header is included in the request when a token exists."""
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "v1.0.0"})
        with patch(_GET_TOKEN_PATH, return_value="ghp_mytoken"), \
             patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            check_for_update("0.9.9")
        req_obj = mock_urlopen.call_args[0][0]
        assert req_obj.get_header("Authorization") == "Bearer ghp_mytoken"

    def test_accept_header_still_present_with_token(self):
        """The Accept header is present alongside the Authorization header."""
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "v1.0.0"})
        with patch(_GET_TOKEN_PATH, return_value="tok"), \
             patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            check_for_update("0.9.9")
        req_obj = mock_urlopen.call_args[0][0]
        assert req_obj.get_header("Accept") == "application/vnd.github+json"

    def test_update_result_correct_with_token(self):
        """check_for_update returns correct result even with auth header."""
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "v2.0.0"})
        with patch(_GET_TOKEN_PATH, return_value="tok"), \
             patch("urllib.request.urlopen", return_value=mock_resp):
            available, latest = check_for_update("1.9.9")
        assert available is True
        assert latest == "2.0.0"


# ---------------------------------------------------------------------------
# Auth header absent when no token
# ---------------------------------------------------------------------------

class TestCheckForUpdateNoAuthHeader:
    def test_no_authorization_header_when_no_token(self):
        """No Authorization header is added when get_github_token returns None."""
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "v0.9.9"})
        with patch(_GET_TOKEN_PATH, return_value=None), \
             patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            check_for_update("0.9.9")
        req_obj = mock_urlopen.call_args[0][0]
        assert req_obj.get_header("Authorization") is None

    def test_update_result_correct_without_token(self):
        """check_for_update still works correctly without a token."""
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "v1.0.0"})
        with patch(_GET_TOKEN_PATH, return_value=None), \
             patch("urllib.request.urlopen", return_value=mock_resp):
            available, latest = check_for_update("0.9.9")
        assert available is True
        assert latest == "1.0.0"


# ---------------------------------------------------------------------------
# Regression: 404 (private repo, no auth) still returns (False, current)
# ---------------------------------------------------------------------------

class TestCheckForUpdatePrivateRepo404Regression:
    def test_http_404_returns_no_update_available(self):
        """BUG-046 regression: HTTP 404 silently returns (False, current_version)."""
        from launcher.core.updater import check_for_update
        with patch(_GET_TOKEN_PATH, return_value=None), \
             patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
                 url="https://api.github.com/...",
                 code=404,
                 msg="Not Found",
                 hdrs=None,
                 fp=None,
             )):
            available, latest = check_for_update("1.0.0")
        assert available is False
        assert latest == "1.0.0"

    def test_http_404_with_token_still_silent(self):
        """Even with a token, HTTP 404 should return (False, current_version) silently."""
        from launcher.core.updater import check_for_update
        with patch(_GET_TOKEN_PATH, return_value="tok"), \
             patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
                 url="https://api.github.com/...",
                 code=404,
                 msg="Not Found",
                 hdrs=None,
                 fp=None,
             )):
            available, latest = check_for_update("1.0.2")
        assert available is False
        assert latest == "1.0.2"


# ---------------------------------------------------------------------------
# get_github_token is called exactly once per check_for_update call
# ---------------------------------------------------------------------------

class TestCheckForUpdateCallsGetTokenOnce:
    def test_get_github_token_called_once(self):
        """get_github_token is called exactly once per check_for_update invocation."""
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "v1.0.0"})
        with patch(_GET_TOKEN_PATH, return_value=None) as mock_token, \
             patch("urllib.request.urlopen", return_value=mock_resp):
            check_for_update("0.9.9")
        assert mock_token.call_count == 1

