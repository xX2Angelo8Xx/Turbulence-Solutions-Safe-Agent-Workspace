"""Tests for launcher.core.updater — INS-009: GitHub Releases version check.

20 tests covering:
- UpdateCheckResult namedtuple structure and 2-tuple unpacking
- _parse_version: semver parsing, v-prefix stripping, short-version padding
- _is_newer: major/minor/patch bump detection, same-version guard
- _fetch_latest_version: happy path, HTTPS URL, timeout forwarding,
  network errors, invalid/missing tag_name
- check_for_update: update available, network failure fallback
"""

from __future__ import annotations

import json
import urllib.error
from unittest.mock import MagicMock, patch

from launcher.config import GITHUB_API_TIMEOUT
from launcher.core.updater import (
    UpdateCheckResult,
    _fetch_latest_version,
    _is_newer,
    _parse_version,
    check_for_update,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_url_mock(data: object) -> MagicMock:
    """Build a mock suitable for use as the return value of urllib.request.urlopen.

    The returned mock supports the context-manager protocol so that
    ``with urlopen(req, timeout=...) as resp:`` works as expected.
    """
    body = json.dumps(data).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# 1–4: UpdateCheckResult structure and 2-tuple unpacking
# ---------------------------------------------------------------------------


def test_update_check_result_is_namedtuple() -> None:
    assert issubclass(UpdateCheckResult, tuple)


def test_update_check_result_has_update_available_field() -> None:
    r = UpdateCheckResult(True, "2.0.0")
    assert r.update_available is True


def test_update_check_result_has_latest_version_field() -> None:
    r = UpdateCheckResult(False, "0.1.0")
    assert r.latest_version == "0.1.0"


def test_update_check_result_tuple_unpacking() -> None:
    available, latest = UpdateCheckResult(False, "0.1.0")
    assert available is False
    assert latest == "0.1.0"


# ---------------------------------------------------------------------------
# 5–8: _parse_version
# ---------------------------------------------------------------------------


def test_parse_version_basic_semver() -> None:
    assert _parse_version("1.2.3") == (1, 2, 3)


def test_parse_version_v_prefix_stripped() -> None:
    assert _parse_version("v2.0.0") == (2, 0, 0)


def test_parse_version_two_components_padded() -> None:
    assert _parse_version("1.4") == (1, 4, 0)


def test_parse_version_one_component_padded() -> None:
    assert _parse_version("3") == (3, 0, 0)


# ---------------------------------------------------------------------------
# 9–12: _is_newer
# ---------------------------------------------------------------------------


def test_is_newer_major_bump() -> None:
    assert _is_newer("2.0.0", "1.9.9") is True


def test_is_newer_minor_bump() -> None:
    assert _is_newer("1.1.0", "1.0.9") is True


def test_is_newer_patch_bump() -> None:
    assert _is_newer("1.0.1", "1.0.0") is True


def test_is_newer_same_version_returns_false() -> None:
    assert _is_newer("1.0.0", "1.0.0") is False


# ---------------------------------------------------------------------------
# 13–18: _fetch_latest_version
# ---------------------------------------------------------------------------


def test_fetch_latest_version_returns_version_string() -> None:
    with patch("urllib.request.urlopen", return_value=_make_url_mock({"tag_name": "v1.2.3"})):
        assert _fetch_latest_version() == "1.2.3"


def test_fetch_latest_version_uses_https() -> None:
    from launcher.core import updater as _updater_module

    assert _updater_module._API_URL.startswith("https://")


def test_fetch_latest_version_timeout_forwarded() -> None:
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = _make_url_mock({"tag_name": "v0.1.0"})
        _fetch_latest_version()
        _, kwargs = mock_urlopen.call_args
        assert kwargs.get("timeout") == GITHUB_API_TIMEOUT


def test_fetch_latest_version_network_error_returns_none() -> None:
    with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
        assert _fetch_latest_version() is None


def test_fetch_latest_version_http_error_returns_none() -> None:
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.HTTPError(
            url="https://example.com", code=404, msg="Not Found", hdrs={}, fp=None
        ),
    ):
        assert _fetch_latest_version() is None


def test_fetch_latest_version_missing_tag_name_returns_none() -> None:
    with patch("urllib.request.urlopen", return_value=_make_url_mock({"name": "release"})):
        assert _fetch_latest_version() is None


def test_fetch_latest_version_empty_tag_name_returns_none() -> None:
    with patch("urllib.request.urlopen", return_value=_make_url_mock({"tag_name": ""})):
        assert _fetch_latest_version() is None


# ---------------------------------------------------------------------------
# 19–20: check_for_update
# ---------------------------------------------------------------------------


def test_check_for_update_returns_true_when_newer() -> None:
    with patch("launcher.core.updater._fetch_latest_version", return_value="2.0.0"):
        result = check_for_update("1.0.0")
        assert result.update_available is True
        assert result.latest_version == "2.0.0"


def test_check_for_update_network_failure_returns_no_update() -> None:
    with patch("launcher.core.updater._fetch_latest_version", return_value=None):
        available, latest = check_for_update("0.1.0")
        assert available is False
        assert latest == "0.1.0"
