"""Tests for FIX-018: auth headers in download_update() and _fetch_sha256_companion().

Verifies that the Authorization header is present on all three request types
(metadata, sha256 companion, asset download) when a token is available.
"""

from __future__ import annotations

import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Patch target: get_github_token as imported in downloader.py
_GET_TOKEN_PATH = "launcher.core.downloader.get_github_token"


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


def _make_mock_response_bytes(raw: bytes) -> MagicMock:
    """Return a mock urlopen that yields bytes (for asset download)."""
    mock_resp = MagicMock()

    def _read(size=-1):
        if _read.consumed:
            return b""
        _read.consumed = True
        return raw

    _read.consumed = False
    mock_resp.read = _read
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _build_release_payload(asset_url: str = "https://objects.githubusercontent.com/file.exe") -> dict:
    """Return a minimal GitHub release API payload with one asset."""
    return {
        "tag_name": "v1.0.0",
        "assets": [
            {
                "name": "AgentEnvironmentLauncher-x86_64.exe",
                "browser_download_url": asset_url,
            }
        ],
    }


# ---------------------------------------------------------------------------
# get_github_token is called once at start of download_update
# ---------------------------------------------------------------------------

class TestDownloadUpdateCallsGetTokenOnce:
    def test_get_github_token_called_once(self):
        """get_github_token is called exactly once per download_update invocation."""
        from launcher.core import downloader

        release_payload = _build_release_payload()
        meta_resp = _make_mock_response(release_payload)
        asset_resp = _make_mock_response_bytes(b"fake_installer_data")

        call_count = [0]

        def _urlopen_side_effect(req, timeout=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return meta_resp
            return asset_resp

        with patch(_GET_TOKEN_PATH, return_value=None) as mock_tok, \
             patch("urllib.request.urlopen", side_effect=_urlopen_side_effect), \
             patch.object(sys, "platform", "win32"), \
             patch("platform.machine", return_value="x86_64"):
            try:
                downloader.download_update("1.0.0")
            except Exception:
                pass  # path may not exist — we only care about call count

        assert mock_tok.call_count == 1


# ---------------------------------------------------------------------------
# Auth header present on metadata request
# ---------------------------------------------------------------------------

class TestDownloadUpdateMetaAuthHeader:
    def test_metadata_request_has_auth_header_when_token_present(self):
        """Authorization header is sent on the release metadata API request."""
        from launcher.core import downloader

        captured_requests: list = []
        release_payload = _build_release_payload()
        meta_resp = _make_mock_response(release_payload)
        asset_resp = _make_mock_response_bytes(b"data")

        call_count = [0]

        def _urlopen_side_effect(req, timeout=None):
            captured_requests.append(req)
            call_count[0] += 1
            if call_count[0] == 1:
                return meta_resp
            return asset_resp

        with patch(_GET_TOKEN_PATH, return_value="ghp_meta_tok"), \
             patch("urllib.request.urlopen", side_effect=_urlopen_side_effect), \
             patch.object(sys, "platform", "win32"), \
             patch("platform.machine", return_value="x86_64"):
            try:
                downloader.download_update("1.0.0")
            except Exception:
                pass

        assert len(captured_requests) >= 1
        meta_req = captured_requests[0]
        assert meta_req.get_header("Authorization") == "Bearer ghp_meta_tok"

    def test_metadata_request_no_auth_when_no_token(self):
        """No Authorization header on metadata request when token is None."""
        from launcher.core import downloader

        captured_requests: list = []
        release_payload = _build_release_payload()
        meta_resp = _make_mock_response(release_payload)
        asset_resp = _make_mock_response_bytes(b"data")

        call_count = [0]

        def _urlopen_side_effect(req, timeout=None):
            captured_requests.append(req)
            call_count[0] += 1
            if call_count[0] == 1:
                return meta_resp
            return asset_resp

        with patch(_GET_TOKEN_PATH, return_value=None), \
             patch("urllib.request.urlopen", side_effect=_urlopen_side_effect), \
             patch.object(sys, "platform", "win32"), \
             patch("platform.machine", return_value="x86_64"):
            try:
                downloader.download_update("1.0.0")
            except Exception:
                pass

        assert len(captured_requests) >= 1
        meta_req = captured_requests[0]
        assert meta_req.get_header("Authorization") is None


# ---------------------------------------------------------------------------
# Auth header present on asset download request
# ---------------------------------------------------------------------------

class TestDownloadUpdateAssetAuthHeader:
    def test_asset_download_request_has_auth_header(self):
        """Authorization header is sent on the asset download request."""
        from launcher.core import downloader

        captured_requests: list = []
        release_payload = _build_release_payload()
        meta_resp = _make_mock_response(release_payload)
        asset_resp = _make_mock_response_bytes(b"installer")

        call_count = [0]

        def _urlopen_side_effect(req, timeout=None):
            captured_requests.append(req)
            call_count[0] += 1
            if call_count[0] == 1:
                return meta_resp
            return asset_resp

        with patch(_GET_TOKEN_PATH, return_value="ghp_asset_tok"), \
             patch("urllib.request.urlopen", side_effect=_urlopen_side_effect), \
             patch.object(sys, "platform", "win32"), \
             patch("platform.machine", return_value="x86_64"):
            try:
                downloader.download_update("1.0.0")
            except Exception:
                pass

        # Second request is the asset download
        assert len(captured_requests) >= 2
        asset_req = captured_requests[1]
        assert asset_req.get_header("Authorization") == "Bearer ghp_asset_tok"

    def test_asset_download_request_no_auth_when_no_token(self):
        """No Authorization header on asset download when token is None."""
        from launcher.core import downloader

        captured_requests: list = []
        release_payload = _build_release_payload()
        meta_resp = _make_mock_response(release_payload)
        asset_resp = _make_mock_response_bytes(b"installer")

        call_count = [0]

        def _urlopen_side_effect(req, timeout=None):
            captured_requests.append(req)
            call_count[0] += 1
            if call_count[0] == 1:
                return meta_resp
            return asset_resp

        with patch(_GET_TOKEN_PATH, return_value=None), \
             patch("urllib.request.urlopen", side_effect=_urlopen_side_effect), \
             patch.object(sys, "platform", "win32"), \
             patch("platform.machine", return_value="x86_64"):
            try:
                downloader.download_update("1.0.0")
            except Exception:
                pass

        assert len(captured_requests) >= 2
        asset_req = captured_requests[1]
        assert asset_req.get_header("Authorization") is None


# ---------------------------------------------------------------------------
# Auth header in _fetch_sha256_companion
# ---------------------------------------------------------------------------

class TestFetchSha256CompanionAuthHeader:
    def test_auth_header_added_when_token_provided(self):
        """_fetch_sha256_companion adds Authorization header when token is given."""
        from launcher.core.downloader import _fetch_sha256_companion

        sha_resp = MagicMock()
        sha_resp.read.return_value = b"abcd1234  file.exe\n"
        sha_resp.__enter__ = MagicMock(return_value=sha_resp)
        sha_resp.__exit__ = MagicMock(return_value=False)

        captured_requests: list = []

        def _urlopen_side_effect(req, timeout=None):
            captured_requests.append(req)
            return sha_resp

        assets = [
            {
                "name": "file.exe.sha256",
                "browser_download_url": "https://objects.githubusercontent.com/file.exe.sha256",
            }
        ]

        with patch("urllib.request.urlopen", side_effect=_urlopen_side_effect):
            result = _fetch_sha256_companion(assets, "file.exe", token="sha_tok")

        assert result == "abcd1234"
        assert len(captured_requests) == 1
        assert captured_requests[0].get_header("Authorization") == "Bearer sha_tok"

    def test_no_auth_header_when_no_token(self):
        """_fetch_sha256_companion does not add Authorization header when token is None."""
        from launcher.core.downloader import _fetch_sha256_companion

        sha_resp = MagicMock()
        sha_resp.read.return_value = b"deadbeef\n"
        sha_resp.__enter__ = MagicMock(return_value=sha_resp)
        sha_resp.__exit__ = MagicMock(return_value=False)

        captured_requests: list = []

        def _urlopen_side_effect(req, timeout=None):
            captured_requests.append(req)
            return sha_resp

        assets = [
            {
                "name": "file.exe.sha256",
                "browser_download_url": "https://objects.githubusercontent.com/file.exe.sha256",
            }
        ]

        with patch("urllib.request.urlopen", side_effect=_urlopen_side_effect):
            result = _fetch_sha256_companion(assets, "file.exe", token=None)

        assert result == "deadbeef"
        assert captured_requests[0].get_header("Authorization") is None

    def test_backward_compat_no_token_arg(self):
        """_fetch_sha256_companion(assets, name) without token still works (backward compat)."""
        from launcher.core.downloader import _fetch_sha256_companion

        sha_resp = MagicMock()
        sha_resp.read.return_value = b"cafebabe\n"
        sha_resp.__enter__ = MagicMock(return_value=sha_resp)
        sha_resp.__exit__ = MagicMock(return_value=False)

        assets = [
            {
                "name": "file.exe.sha256",
                "browser_download_url": "https://objects.githubusercontent.com/file.exe.sha256",
            }
        ]

        with patch("urllib.request.urlopen", return_value=sha_resp):
            result = _fetch_sha256_companion(assets, "file.exe")

        assert result == "cafebabe"

    def test_accept_header_still_present(self):
        """Accept: text/plain is still present regardless of token."""
        from launcher.core.downloader import _fetch_sha256_companion

        sha_resp = MagicMock()
        sha_resp.read.return_value = b"hash123\n"
        sha_resp.__enter__ = MagicMock(return_value=sha_resp)
        sha_resp.__exit__ = MagicMock(return_value=False)

        captured_requests: list = []

        def _urlopen_side_effect(req, timeout=None):
            captured_requests.append(req)
            return sha_resp

        assets = [
            {
                "name": "file.dmg.sha256",
                "browser_download_url": "https://objects.githubusercontent.com/file.dmg.sha256",
            }
        ]

        with patch("urllib.request.urlopen", side_effect=_urlopen_side_effect):
            _fetch_sha256_companion(assets, "file.dmg", token="tok")

        req = captured_requests[0]
        assert req.get_header("Accept") == "text/plain"
