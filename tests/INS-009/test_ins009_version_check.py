"""Tests for INS-009: GitHub Releases Version Check."""

from __future__ import annotations

import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest


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
    """Return a mock urlopen context-manager response with raw bytes."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = raw
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# parse_version tests
# ---------------------------------------------------------------------------

class TestParseVersion:
    def test_basic_semver(self):
        from launcher.core.updater import parse_version
        assert parse_version("1.2.3") == (1, 2, 3)

    def test_leading_v_stripped(self):
        from launcher.core.updater import parse_version
        assert parse_version("v0.2.0") == (0, 2, 0)

    def test_zero_version(self):
        from launcher.core.updater import parse_version
        assert parse_version("0.0.0") == (0, 0, 0)

    def test_single_component(self):
        from launcher.core.updater import parse_version
        assert parse_version("3") == (3,)

    def test_two_components(self):
        from launcher.core.updater import parse_version
        assert parse_version("1.5") == (1, 5)

    def test_large_numbers(self):
        from launcher.core.updater import parse_version
        assert parse_version("10.20.300") == (10, 20, 300)

    def test_non_numeric_part_becomes_zero(self):
        from launcher.core.updater import parse_version
        result = parse_version("1.2.alpha")
        assert result == (1, 2, 0)

    def test_v_only_stripped_not_middle(self):
        from launcher.core.updater import parse_version
        # only a leading v is stripped; digits in version are unaffected
        assert parse_version("v2.3.4") == (2, 3, 4)

    def test_current_version_constant(self):
        from launcher.core.updater import parse_version
        from launcher.config import VERSION
        tup = parse_version(VERSION)
        assert isinstance(tup, tuple)
        assert all(isinstance(n, int) for n in tup)


# ---------------------------------------------------------------------------
# check_for_update — update available
# ---------------------------------------------------------------------------

class TestCheckForUpdateAvailable:
    def test_newer_patch_version(self):
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "v0.2.0"})
        with patch("urllib.request.urlopen", return_value=mock_resp):
            available, latest = check_for_update("0.1.0")
        assert available is True
        assert latest == "0.2.0"

    def test_newer_minor_version(self):
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "v1.0.0"})
        with patch("urllib.request.urlopen", return_value=mock_resp):
            available, latest = check_for_update("0.9.9")
        assert available is True
        assert latest == "1.0.0"

    def test_newer_major_version(self):
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "v2.0.0"})
        with patch("urllib.request.urlopen", return_value=mock_resp):
            available, latest = check_for_update("1.99.99")
        assert available is True
        assert latest == "2.0.0"

    def test_tag_without_v_prefix(self):
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "0.5.0"})
        with patch("urllib.request.urlopen", return_value=mock_resp):
            available, latest = check_for_update("0.4.9")
        assert available is True
        assert latest == "0.5.0"

    def test_latest_version_string_returned(self):
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "v1.2.3"})
        with patch("urllib.request.urlopen", return_value=mock_resp):
            available, latest = check_for_update("1.2.2")
        assert latest == "1.2.3"
        assert available is True


# ---------------------------------------------------------------------------
# check_for_update — no update available
# ---------------------------------------------------------------------------

class TestCheckForUpdateNotAvailable:
    def test_same_version_no_update(self):
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "v0.1.0"})
        with patch("urllib.request.urlopen", return_value=mock_resp):
            available, latest = check_for_update("0.1.0")
        assert available is False

    def test_older_remote_no_update(self):
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "v0.0.9"})
        with patch("urllib.request.urlopen", return_value=mock_resp):
            available, latest = check_for_update("0.1.0")
        assert available is False

    def test_same_version_returns_latest_string(self):
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "v0.1.0"})
        with patch("urllib.request.urlopen", return_value=mock_resp):
            available, latest = check_for_update("0.1.0")
        assert latest == "0.1.0"

    def test_local_newer_than_remote(self):
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "v1.0.0"})
        with patch("urllib.request.urlopen", return_value=mock_resp):
            available, _ = check_for_update("2.0.0")
        assert available is False


# ---------------------------------------------------------------------------
# check_for_update — error handling
# ---------------------------------------------------------------------------

class TestCheckForUpdateErrorHandling:
    def test_network_error_returns_false(self):
        from launcher.core.updater import check_for_update
        with patch("urllib.request.urlopen", side_effect=OSError("network down")):
            available, latest = check_for_update("0.1.0")
        assert available is False
        assert latest == "0.1.0"

    def test_url_error_returns_false(self):
        from launcher.core.updater import check_for_update
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            available, latest = check_for_update("0.1.0")
        assert available is False
        assert latest == "0.1.0"

    def test_http_error_returns_false(self):
        from launcher.core.updater import check_for_update
        http_err = urllib.error.HTTPError(
            url="https://example.com",
            code=404,
            msg="Not Found",
            hdrs=None,  # type: ignore[arg-type]
            fp=None,
        )
        with patch("urllib.request.urlopen", side_effect=http_err):
            available, latest = check_for_update("0.1.0")
        assert available is False
        assert latest == "0.1.0"

    def test_malformed_json_returns_false(self):
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response_bytes(b"not valid json {{{")
        with patch("urllib.request.urlopen", return_value=mock_resp):
            available, latest = check_for_update("0.1.0")
        assert available is False
        assert latest == "0.1.0"

    def test_missing_tag_name_key_returns_false(self):
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"name": "Release 0.2.0"})  # no tag_name
        with patch("urllib.request.urlopen", return_value=mock_resp):
            available, latest = check_for_update("0.1.0")
        assert available is False
        assert latest == "0.1.0"

    def test_timeout_returns_false(self):
        from launcher.core.updater import check_for_update
        import socket
        with patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
            available, latest = check_for_update("0.1.0")
        assert available is False
        assert latest == "0.1.0"

    def test_empty_response_returns_false(self):
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response_bytes(b"")
        with patch("urllib.request.urlopen", return_value=mock_resp):
            available, latest = check_for_update("0.1.0")
        assert available is False
        assert latest == "0.1.0"

    def test_null_json_response_returns_false(self):
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response_bytes(b"null")
        with patch("urllib.request.urlopen", return_value=mock_resp):
            available, latest = check_for_update("0.1.0")
        assert available is False
        assert latest == "0.1.0"

    def test_no_exception_raised_on_error(self):
        from launcher.core.updater import check_for_update
        with patch("urllib.request.urlopen", side_effect=RuntimeError("unexpected")):
            try:
                result = check_for_update("0.1.0")
            except Exception as exc:
                pytest.fail(f"check_for_update raised unexpectedly: {exc}")
        assert result == (False, "0.1.0")

    def test_returns_current_version_on_error(self):
        from launcher.core.updater import check_for_update
        with patch("urllib.request.urlopen", side_effect=Exception("any error")):
            available, latest = check_for_update("1.2.3")
        assert latest == "1.2.3"


# ---------------------------------------------------------------------------
# Config constants
# ---------------------------------------------------------------------------

class TestConfigConstants:
    def test_github_repo_owner_exists(self):
        from launcher.config import GITHUB_REPO_OWNER
        assert isinstance(GITHUB_REPO_OWNER, str)
        assert GITHUB_REPO_OWNER != ""

    def test_github_repo_name_exists(self):
        from launcher.config import GITHUB_REPO_NAME
        assert isinstance(GITHUB_REPO_NAME, str)
        assert GITHUB_REPO_NAME != ""

    def test_github_releases_url_exists(self):
        from launcher.config import GITHUB_RELEASES_URL
        assert isinstance(GITHUB_RELEASES_URL, str)
        assert GITHUB_RELEASES_URL.startswith("https://")

    def test_github_releases_url_contains_owner(self):
        from launcher.config import GITHUB_RELEASES_URL, GITHUB_REPO_OWNER
        assert GITHUB_REPO_OWNER in GITHUB_RELEASES_URL

    def test_github_releases_url_contains_repo_name(self):
        from launcher.config import GITHUB_RELEASES_URL, GITHUB_REPO_NAME
        assert GITHUB_REPO_NAME in GITHUB_RELEASES_URL

    def test_github_releases_url_is_api_endpoint(self):
        from launcher.config import GITHUB_RELEASES_URL
        assert "api.github.com" in GITHUB_RELEASES_URL
        assert "releases/latest" in GITHUB_RELEASES_URL

    def test_github_releases_url_correct_format(self):
        from launcher.config import GITHUB_RELEASES_URL, GITHUB_REPO_OWNER, GITHUB_REPO_NAME
        expected = (
            f"https://api.github.com/repos/{GITHUB_REPO_OWNER}"
            f"/{GITHUB_REPO_NAME}/releases/latest"
        )
        assert GITHUB_RELEASES_URL == expected

    def test_existing_constants_unchanged(self):
        """Ensure adding GITHUB constants did not remove existing ones."""
        from launcher.config import APP_NAME, VERSION, COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TEXT, TEMPLATES_DIR
        assert APP_NAME
        assert VERSION
        assert COLOR_PRIMARY == "#0A1D4E"
        assert COLOR_SECONDARY == "#5BC5F2"
        assert COLOR_TEXT == "#FFFFFF"
        assert TEMPLATES_DIR is not None


# ---------------------------------------------------------------------------
# Tester edge-case tests
# ---------------------------------------------------------------------------

class TestParseVersionEdgeCases:
    """Edge-case tests added by Tester Agent (Iteration 1)."""

    def test_leading_V_uppercase_not_stripped(self):
        """lstrip('v') is case-sensitive; uppercase 'V' is NOT stripped.

        Documents actual behavior: 'V1.0.0' → first segment 'V1' is
        non-numeric → becomes 0. Result is (0, 0, 0), not (1, 0, 0).
        This is a known limitation consistent with the docstring (which
        only mentions lowercase 'v'). GitHub API always returns lowercase.
        """
        from launcher.core.updater import parse_version
        result = parse_version("V1.0.0")
        assert result == (0, 0, 0)

    def test_empty_string_returns_zero_tuple(self):
        """Empty string produces (0,) — all segments non-numeric → 0."""
        from launcher.core.updater import parse_version
        result = parse_version("")
        assert result == (0,)

    def test_four_component_version(self):
        """Four-component version strings are supported."""
        from launcher.core.updater import parse_version
        assert parse_version("1.2.3.4") == (1, 2, 3, 4)


class TestCheckForUpdateImplementation:
    """Tester-added tests verifying internal implementation correctness."""

    def test_request_sent_with_accept_header(self):
        """Verify the GitHub API Accept header is included in the Request."""
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": "v0.2.0"})
        with patch("urllib.request.Request") as mock_req_cls, \
             patch("urllib.request.urlopen", return_value=mock_resp):
            check_for_update("0.1.0")
        args, kwargs = mock_req_cls.call_args
        headers = kwargs.get("headers", {})
        assert "Accept" in headers, "Request must include an Accept header"
        assert "github" in headers["Accept"].lower(), (
            f"Accept header should reference github API: {headers['Accept']}"
        )

    def test_uses_hardcoded_github_releases_url(self):
        """Verify the URL used is the GITHUB_RELEASES_URL constant — not user-injectable."""
        from launcher.core.updater import check_for_update
        from launcher.config import GITHUB_RELEASES_URL
        mock_resp = _make_mock_response({"tag_name": "v0.2.0"})
        with patch("urllib.request.Request") as mock_req_cls, \
             patch("urllib.request.urlopen", return_value=mock_resp):
            check_for_update("0.1.0")
        args, _ = mock_req_cls.call_args
        assert args[0] == GITHUB_RELEASES_URL, (
            "check_for_update must use GITHUB_RELEASES_URL; "
            "URL must not be derived from user-supplied input"
        )

    def test_tag_name_non_string_type_returns_false(self):
        """If tag_name is not a string (e.g. API returns an int), return False silently."""
        from launcher.core.updater import check_for_update
        mock_resp = _make_mock_response({"tag_name": 100})  # int, not str
        with patch("urllib.request.urlopen", return_value=mock_resp):
            available, latest = check_for_update("0.1.0")
        assert available is False
        assert latest == "0.1.0"
