"""Tests for INS-009 — GitHub Releases Version Check.

Covers interface contract, API URL security, stdlib-only dependency
requirement, silent error handling, semantic version comparison, version
parsing edge cases, and response validation.

All tests in classes 1–2 and 5 verify requirements that MUST be satisfied
by a real implementation; they will FAIL against the current stub and are
the primary signal for the developer.  Tests in classes 3–4 and 6–7 also
guard against regressions once the real implementation exists.
"""

from __future__ import annotations

import inspect
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

import launcher.core.updater as _updater
from launcher.core.updater import check_for_update


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(body: bytes | str) -> MagicMock:
    """Return a mock context-manager that simulates urlopen() returning body."""
    if isinstance(body, str):
        body = body.encode()
    mock = MagicMock()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    mock.read.return_value = body
    return mock


def _release_response(tag: str, **extra) -> MagicMock:
    """Return a mock response for a GitHub Releases API payload."""
    payload = {"tag_name": tag, **extra}
    return _make_response(json.dumps(payload))


# ---------------------------------------------------------------------------
# 1. Interface Contract  (INS-001 backward compatibility)
# ---------------------------------------------------------------------------

class TestInterfaceContract:
    """check_for_update() must satisfy the 2-tuple interface from INS-001."""

    def test_function_is_callable(self):
        assert callable(check_for_update)

    def test_returns_tuple(self):
        result = check_for_update("1.0.0")
        assert isinstance(result, tuple)

    def test_returns_two_element_tuple(self):
        assert len(check_for_update("1.0.0")) == 2

    def test_first_element_is_bool(self):
        flag, _ = check_for_update("1.0.0")
        assert isinstance(flag, bool)

    def test_second_element_is_str(self):
        _, ver = check_for_update("1.0.0")
        assert isinstance(ver, str)

    def test_tuple_unpack_compatible(self):
        # Two-name unpack must not raise ValueError — verifies exact 2-tuple.
        update_available, latest_version = check_for_update("1.0.0")  # noqa: F841


# ---------------------------------------------------------------------------
# 2. API URL Security
# ---------------------------------------------------------------------------

class TestApiUrlSecurity:
    """_API_URL constant must exist, use HTTPS, and target GitHub Releases."""

    def test_api_url_attribute_exists(self):
        assert hasattr(_updater, "_API_URL"), (
            "_API_URL constant is missing from launcher.core.updater"
        )

    def test_api_url_starts_with_https(self):
        url = getattr(_updater, "_API_URL", "")
        assert url.startswith("https://"), (
            f"_API_URL must use HTTPS only; got: {url!r}"
        )

    def test_api_url_not_plain_http(self):
        url = getattr(_updater, "_API_URL", "")
        assert not url.startswith("http://"), (
            "_API_URL must not use unencrypted HTTP"
        )

    def test_api_url_targets_github_api(self):
        url = getattr(_updater, "_API_URL", "")
        assert "api.github.com" in url, (
            f"_API_URL must target api.github.com; got: {url!r}"
        )

    def test_api_url_references_releases_endpoint(self):
        url = getattr(_updater, "_API_URL", "")
        assert "releases" in url, (
            f"_API_URL must reference the releases endpoint; got: {url!r}"
        )


# ---------------------------------------------------------------------------
# 3. No External Dependencies  (stdlib only)
# ---------------------------------------------------------------------------

class TestNoDependencies:
    """The updater must use only Python stdlib — no third-party packages."""

    def test_source_does_not_import_requests(self):
        src = inspect.getsource(_updater)
        assert "import requests" not in src, (
            "updater.py must not use 'requests'; use urllib from stdlib instead"
        )

    def test_source_uses_urllib_for_http(self):
        src = inspect.getsource(_updater)
        assert "urllib" in src, (
            "updater.py should use urllib (stdlib) for HTTP requests; "
            "no reference to urllib found in source"
        )


# ---------------------------------------------------------------------------
# 4. Silent Error Handling — function NEVER raises
# ---------------------------------------------------------------------------

class TestSilentErrorHandling:
    """All errors must be absorbed silently; check_for_update never propagates."""

    def test_url_error_caught_silently(self):
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("no route to host"),
        ):
            result = check_for_update("1.0.0")
        assert isinstance(result, tuple) and len(result) == 2

    def test_http_404_caught_silently(self):
        err = urllib.error.HTTPError(
            url="https://api.github.com/x",
            code=404, msg="Not Found", hdrs={}, fp=None,
        )
        with patch("urllib.request.urlopen", side_effect=err):
            result = check_for_update("1.0.0")
        assert isinstance(result, tuple) and len(result) == 2

    def test_http_500_caught_silently(self):
        err = urllib.error.HTTPError(
            url="https://api.github.com/x",
            code=500, msg="Internal Server Error", hdrs={}, fp=None,
        )
        with patch("urllib.request.urlopen", side_effect=err):
            result = check_for_update("1.0.0")
        assert isinstance(result, tuple) and len(result) == 2

    def test_timeout_error_caught_silently(self):
        with patch(
            "urllib.request.urlopen",
            side_effect=TimeoutError("connection timed out"),
        ):
            result = check_for_update("1.0.0")
        assert isinstance(result, tuple) and len(result) == 2

    def test_generic_exception_caught_silently(self):
        with patch(
            "urllib.request.urlopen",
            side_effect=Exception("unexpected error"),
        ):
            result = check_for_update("1.0.0")
        assert isinstance(result, tuple) and len(result) == 2

    def test_invalid_json_response_caught_silently(self):
        with patch(
            "urllib.request.urlopen",
            return_value=_make_response(b"not-valid-json{["),
        ):
            result = check_for_update("1.0.0")
        assert isinstance(result, tuple) and len(result) == 2

    def test_empty_current_version_string_no_raise(self):
        try:
            result = check_for_update("")
            assert isinstance(result, tuple) and len(result) == 2
        except Exception as exc:
            pytest.fail(f"check_for_update('') raised unexpectedly: {exc!r}")

    def test_whitespace_padded_version_no_raise(self):
        try:
            result = check_for_update("  1.0.0  ")
            assert isinstance(result, tuple) and len(result) == 2
        except Exception as exc:
            pytest.fail(f"Whitespace-padded version raised: {exc!r}")


# ---------------------------------------------------------------------------
# 5. Semantic Version Comparison
# ---------------------------------------------------------------------------

class TestVersionComparison:
    """Correct comparison between current_version and GitHub tag_name."""

    def test_newer_major_version_sets_flag_true(self):
        with patch(
            "urllib.request.urlopen", return_value=_release_response("v2.0.0")
        ):
            flag, _ = check_for_update("1.0.0")
        assert flag is True, "Newer major version must produce update_available=True"

    def test_newer_minor_version_sets_flag_true(self):
        with patch(
            "urllib.request.urlopen", return_value=_release_response("v1.1.0")
        ):
            flag, _ = check_for_update("1.0.0")
        assert flag is True, "Newer minor version must produce update_available=True"

    def test_newer_patch_version_sets_flag_true(self):
        with patch(
            "urllib.request.urlopen", return_value=_release_response("v1.0.1")
        ):
            flag, _ = check_for_update("1.0.0")
        assert flag is True, "Newer patch version must produce update_available=True"

    def test_same_version_flag_false(self):
        with patch(
            "urllib.request.urlopen", return_value=_release_response("v1.0.0")
        ):
            flag, _ = check_for_update("1.0.0")
        assert flag is False, "Same version must NOT produce update_available=True"

    def test_older_api_version_flag_false(self):
        with patch(
            "urllib.request.urlopen", return_value=_release_response("v0.9.0")
        ):
            flag, _ = check_for_update("1.0.0")
        assert flag is False, "API version older than current must return False"

    def test_v_prefix_stripped_before_comparison(self):
        with patch(
            "urllib.request.urlopen", return_value=_release_response("v1.2.3")
        ):
            flag, _ = check_for_update("1.2.2")
        assert flag is True, "'v' prefix in tag must be stripped before comparison"

    def test_latest_version_string_returned_non_empty(self):
        with patch(
            "urllib.request.urlopen", return_value=_release_response("v2.0.0")
        ):
            _, latest = check_for_update("1.0.0")
        assert isinstance(latest, str) and latest != "", (
            "Second return value should be the latest version string"
        )


# ---------------------------------------------------------------------------
# 6. Version Parsing Edge Cases
# ---------------------------------------------------------------------------

class TestVersionParsingEdgeCases:
    """Unusual version string formats must never raise."""

    @pytest.mark.parametrize(
        "tag",
        [
            "v1.0.0-alpha",       # pre-release: alpha suffix
            "v1.0.0-beta",        # pre-release: beta suffix
            "v1.0.0-rc1",         # release candidate
            "v1.0.0-rc.2",        # dotted RC
            "v1.2",               # two-component version
            "v1",                 # single-component version
            "v999.999.999",       # very large version numbers
            "1.0.0",              # no leading 'v' on tag
            "1.2.3.4",            # four-component version
        ],
    )
    def test_unusual_tag_does_not_raise(self, tag: str):
        with patch(
            "urllib.request.urlopen", return_value=_release_response(tag)
        ):
            result = check_for_update("1.0.0")
        assert isinstance(result, tuple) and len(result) == 2, (
            f"Tag {tag!r} produced an invalid result"
        )


# ---------------------------------------------------------------------------
# 7. API Response Validation
# ---------------------------------------------------------------------------

class TestResponseValidation:
    """Malformed or unexpected API response shapes must be handled silently."""

    def test_missing_tag_name_field(self):
        with patch(
            "urllib.request.urlopen",
            return_value=_make_response(b'{"name":"v1.0.0"}'),
        ):
            result = check_for_update("1.0.0")
        assert isinstance(result, tuple) and len(result) == 2

    def test_empty_string_tag_name(self):
        with patch(
            "urllib.request.urlopen",
            return_value=_make_response(b'{"tag_name":""}'),
        ):
            result = check_for_update("1.0.0")
        assert isinstance(result, tuple) and len(result) == 2

    def test_null_tag_name(self):
        with patch(
            "urllib.request.urlopen",
            return_value=_make_response(b'{"tag_name":null}'),
        ):
            result = check_for_update("1.0.0")
        assert isinstance(result, tuple) and len(result) == 2

    def test_integer_tag_name(self):
        with patch(
            "urllib.request.urlopen",
            return_value=_make_response(b'{"tag_name":123}'),
        ):
            result = check_for_update("1.0.0")
        assert isinstance(result, tuple) and len(result) == 2

    def test_response_is_json_array_not_object(self):
        with patch(
            "urllib.request.urlopen",
            return_value=_make_response(b'[{"tag_name":"v1.0.0"}]'),
        ):
            result = check_for_update("1.0.0")
        assert isinstance(result, tuple) and len(result) == 2

    def test_empty_json_object(self):
        with patch(
            "urllib.request.urlopen",
            return_value=_make_response(b'{}'),
        ):
            result = check_for_update("1.0.0")
        assert isinstance(result, tuple) and len(result) == 2

    def test_extra_fields_do_not_break_parsing(self):
        with patch(
            "urllib.request.urlopen",
            return_value=_release_response(
                "v2.0.0",
                name="Release 2.0.0",
                body="## Changelog",
                draft=False,
                prerelease=False,
                html_url="https://github.com/x/y/releases/tag/v2.0.0",
                published_at="2026-01-01T00:00:00Z",
            ),
        ):
            result = check_for_update("1.0.0")
        assert isinstance(result, tuple) and len(result) == 2
