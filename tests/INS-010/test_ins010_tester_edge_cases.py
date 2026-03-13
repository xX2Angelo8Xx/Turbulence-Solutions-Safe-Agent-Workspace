"""Tester edge-case tests for INS-010: Update Download (downloader.py).

Covers boundary conditions, security bypasses, and edge paths not exercised
by the developer's test suite.
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers (duplicated from dev tests to keep this file self-contained)
# ---------------------------------------------------------------------------

def _make_mock_http_response(body: bytes) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _make_mock_chunked_response(chunks: list[bytes]) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.read.side_effect = chunks + [b""]
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# TestPlatformDetectionEdgeCases
# ---------------------------------------------------------------------------

class TestPlatformDetectionEdgeCases:
    """Platform detection edge cases not covered by developer tests."""

    def test_linux2_raises(self):
        """Old 'linux2' platform identifier (Python < 3.3) should raise."""
        from launcher.core.downloader import _detect_platform_extension
        with patch("launcher.core.downloader.sys") as mock_sys:
            mock_sys.platform = "linux2"
            with pytest.raises(RuntimeError, match="Unsupported platform"):
                _detect_platform_extension()

    def test_win32_case_sensitive(self):
        """'Win32' with capital W is not recognized — map is exact-match."""
        from launcher.core.downloader import _detect_platform_extension
        with patch("launcher.core.downloader.sys") as mock_sys:
            mock_sys.platform = "Win32"
            with pytest.raises(RuntimeError, match="Unsupported platform"):
                _detect_platform_extension()

    def test_empty_platform_raises(self):
        """Empty platform string is not in the map — should raise."""
        from launcher.core.downloader import _detect_platform_extension
        with patch("launcher.core.downloader.sys") as mock_sys:
            mock_sys.platform = ""
            with pytest.raises(RuntimeError, match="Unsupported platform"):
                _detect_platform_extension()


# ---------------------------------------------------------------------------
# TestArchitectureDetectionEdgeCases
# ---------------------------------------------------------------------------

class TestArchitectureDetectionEdgeCases:
    """Architecture detection edge cases."""

    def test_empty_machine_returns_empty_string(self):
        """platform.machine() returning '' passes through as '' (lowercased)."""
        from launcher.core.downloader import _detect_architecture
        with patch("launcher.core.downloader.platform") as mock_platform:
            mock_platform.machine.return_value = ""
            result = _detect_architecture()
        assert result == ""

    def test_i686_passes_through_lowercase(self):
        """32-bit x86 'i686' is not normalised to x86_64 — it passes through."""
        from launcher.core.downloader import _detect_architecture
        with patch("launcher.core.downloader.platform") as mock_platform:
            mock_platform.machine.return_value = "i686"
            result = _detect_architecture()
        assert result == "i686"

    def test_arm64_keyword_not_used_for_unknown_arch(self):
        """An unknown arch uses its own name as keyword, not arm64."""
        from launcher.core.downloader import _detect_architecture
        with patch("launcher.core.downloader.platform") as mock_platform:
            mock_platform.machine.return_value = "riscv64"
            result = _detect_architecture()
        assert result == "riscv64"


# ---------------------------------------------------------------------------
# TestFilenameSanitizationEdgeCases
# ---------------------------------------------------------------------------

class TestFilenameSanitizationEdgeCases:
    """Edge cases for filename sanitization."""

    def test_empty_string_input_raises(self):
        """Directly passing '' should raise ValueError (before regex even runs)."""
        from launcher.core.downloader import _sanitize_filename
        with pytest.raises(ValueError, match="empty after sanitization"):
            _sanitize_filename("")

    def test_dot_dot_preserved_as_filename(self):
        """'..' after Path().name is still '..' — dots are safe chars; no ValueError."""
        from launcher.core.downloader import _sanitize_filename
        # Path("..").name == ".." — both dots are kept by the regex.
        result = _sanitize_filename("..")
        assert result == ".."

    def test_only_hyphens_preserved(self):
        """A name consisting only of hyphens is safe and preserved."""
        from launcher.core.downloader import _sanitize_filename
        result = _sanitize_filename("---")
        assert result == "---"

    def test_newline_in_name_stripped(self):
        """Newline characters are not in \\w, '.', or '-' and must be removed."""
        from launcher.core.downloader import _sanitize_filename
        result = _sanitize_filename("launcher\n1.0.exe")
        assert "\n" not in result
        assert result == "launcher1.0.exe"

    def test_tab_in_name_stripped(self):
        """Tab characters are stripped from the filename."""
        from launcher.core.downloader import _sanitize_filename
        result = _sanitize_filename("launcher\t1.0.exe")
        assert "\t" not in result

    def test_long_path_strips_directory(self):
        """Deep path component is stripped; only the final filename is kept."""
        from launcher.core.downloader import _sanitize_filename
        result = _sanitize_filename("a/b/c/d/file.exe")
        assert "/" not in result
        assert result == "file.exe"


# ---------------------------------------------------------------------------
# TestURLValidationEdgeCases
# ---------------------------------------------------------------------------

class TestURLValidationEdgeCases:
    """Additional URL validation edge cases focusing on SSRF bypass attempts."""

    def test_empty_url_raises(self):
        """Empty URL has scheme '' != 'https' — must raise ValueError."""
        from launcher.core.downloader import _validate_download_url
        with pytest.raises(ValueError, match="HTTPS"):
            _validate_download_url("")

    def test_api_github_com_subdomain_rejected(self):
        """api.github.com is NOT in the allowed download host list."""
        from launcher.core.downloader import _validate_download_url
        with pytest.raises(ValueError, match="not in the allowed list"):
            _validate_download_url(
                "https://api.github.com/repos/owner/repo/releases/download/file.exe"
            )

    def test_ssrf_via_at_github_dot_com_at_evil(self):
        """'https://github.com@evil.com/file' — hostname resolves to evil.com → blocked."""
        from launcher.core.downloader import _validate_download_url
        with pytest.raises(ValueError, match="not in the allowed list"):
            _validate_download_url("https://github.com@evil.com/file.exe")

    def test_ssrf_via_github_subdomain_of_evil(self):
        """'github.com.evil.com' is not github.com — must be blocked."""
        from launcher.core.downloader import _validate_download_url
        with pytest.raises(ValueError, match="not in the allowed list"):
            _validate_download_url("https://github.com.evil.com/file.exe")

    def test_url_with_auth_on_valid_host_accepted(self):
        """'https://user:token@objects.githubusercontent.com/file' — hostname is valid."""
        from launcher.core.downloader import _validate_download_url
        # Constructing user:pass@host where host is an allowed host should PASS
        # since urlparse resolves hostname to the permitted domain.
        _validate_download_url(
            "https://user:token@objects.githubusercontent.com/path/file.exe"
        )

    def test_javascript_scheme_rejected(self):
        """javascript: scheme must be rejected (scheme != 'https')."""
        from launcher.core.downloader import _validate_download_url
        with pytest.raises(ValueError, match="HTTPS"):
            _validate_download_url("javascript:alert(1)")

    def test_file_scheme_rejected(self):
        """file:// scheme is not HTTPS — must be rejected."""
        from launcher.core.downloader import _validate_download_url
        with pytest.raises(ValueError, match="HTTPS"):
            _validate_download_url("file:///etc/passwd")


# ---------------------------------------------------------------------------
# TestFetchSHA256CompanionEdgeCases
# ---------------------------------------------------------------------------

class TestFetchSHA256CompanionEdgeCases:
    """Edge cases for the SHA256 companion downloader."""

    def test_whitespace_only_content_returns_none(self):
        """Companion file with only whitespace — split()[0] raises IndexError → None."""
        from launcher.core.downloader import _fetch_sha256_companion
        assets = [
            {
                "name": "file.exe.sha256",
                "browser_download_url": "https://github.com/x/y/file.exe.sha256",
            }
        ]
        mock_resp = _make_mock_http_response(b"   \n  \n  ")
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = _fetch_sha256_companion(assets, "file.exe")
        assert result is None

    def test_multiline_sha256_file_uses_first_hash(self):
        """Companion file with multiple entries — only the first hash is returned."""
        from launcher.core.downloader import _fetch_sha256_companion
        assets = [
            {
                "name": "file.exe.sha256",
                "browser_download_url": "https://github.com/x/y/file.exe.sha256",
            }
        ]
        first_hash = "aabbccdd" * 8  # 64 chars
        second_hash = "11223344" * 8
        content = f"{first_hash}  file.exe\n{second_hash}  other.exe\n"
        mock_resp = _make_mock_http_response(content.encode())
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = _fetch_sha256_companion(assets, "file.exe")
        assert result == first_hash

    def test_companion_url_for_http_rejected_returns_none(self):
        """Companion with HTTP (not HTTPS) URL fails _validate_download_url → None."""
        from launcher.core.downloader import _fetch_sha256_companion
        assets = [
            {
                "name": "file.exe.sha256",
                "browser_download_url": "http://github.com/x/y/file.exe.sha256",
            }
        ]
        result = _fetch_sha256_companion(assets, "file.exe")
        assert result is None

    def test_empty_browser_download_url_returns_none(self):
        """Companion entry with empty browser_download_url fails validation → None."""
        from launcher.core.downloader import _fetch_sha256_companion
        assets = [
            {
                "name": "file.exe.sha256",
                "browser_download_url": "",
            }
        ]
        result = _fetch_sha256_companion(assets, "file.exe")
        assert result is None


# ---------------------------------------------------------------------------
# TestSHA256VerificationEdgeCases
# ---------------------------------------------------------------------------

class TestSHA256VerificationEdgeCases:
    """Edge cases for SHA256 comparison logic in download_update."""

    def test_sha256_comparison_is_case_insensitive(self):
        """An UPPERCASE expected hash in the companion file still matches."""
        from launcher.core.downloader import download_update
        asset_bytes = b"real installer content"
        correct_hash = hashlib.sha256(asset_bytes).hexdigest().upper()  # UPPERCASE

        assets = [
            {
                "name": "launcher.exe",
                "browser_download_url": "https://github.com/x/y/launcher.exe",
            },
            {
                "name": "launcher.exe.sha256",
                "browser_download_url": "https://github.com/x/y/launcher.exe.sha256",
            },
        ]
        meta_resp = _make_mock_http_response(
            json.dumps({"tag_name": "v1.0.0", "assets": assets}).encode()
        )
        sha256_resp = _make_mock_http_response(
            f"{correct_hash}  launcher.exe\n".encode()
        )
        asset_resp = _make_mock_chunked_response([asset_bytes])

        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch(
                "urllib.request.urlopen",
                side_effect=[meta_resp, asset_resp, sha256_resp],
            ),
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            result = download_update("1.0.0")
        assert result.name == "launcher.exe"

    def test_sha256_mismatch_file_is_removed(self):
        """On SHA256 mismatch the temp file is deleted — not left on disk."""
        from launcher.core.downloader import download_update
        asset_bytes = b"tampered"
        wrong_hash = "0" * 64

        assets = [
            {
                "name": "launcher.exe",
                "browser_download_url": "https://github.com/x/y/launcher.exe",
            },
            {
                "name": "launcher.exe.sha256",
                "browser_download_url": "https://github.com/x/y/launcher.exe.sha256",
            },
        ]
        meta_resp = _make_mock_http_response(
            json.dumps({"tag_name": "v1.0.0", "assets": assets}).encode()
        )
        sha256_resp = _make_mock_http_response(
            f"{wrong_hash}  launcher.exe\n".encode()
        )
        asset_resp = _make_mock_chunked_response([asset_bytes])
        downloaded_path: list[Path] = []

        original_mkdtemp = __import__("tempfile").mkdtemp

        def recording_mkdtemp(**kwargs):
            tmp = original_mkdtemp(**kwargs)
            downloaded_path.append(Path(tmp) / "launcher.exe")
            return tmp

        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch("tempfile.mkdtemp", side_effect=recording_mkdtemp),
            patch(
                "urllib.request.urlopen",
                side_effect=[meta_resp, asset_resp, sha256_resp],
            ),
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            with pytest.raises(RuntimeError, match="SHA256 mismatch"):
                download_update("1.0.0")

        if downloaded_path:
            assert not downloaded_path[0].exists(), (
                "Partial/mismatched file should be deleted on SHA256 failure"
            )


# ---------------------------------------------------------------------------
# TestDownloadUpdateEdgeCases
# ---------------------------------------------------------------------------

class TestDownloadUpdateEdgeCases:
    """Integration-level edge cases for download_update()."""

    def test_missing_assets_key_in_json_raises(self):
        """Release JSON with no 'assets' key at all (not just empty list)."""
        from launcher.core.downloader import download_update
        mock_resp = _make_mock_http_response(
            json.dumps({"tag_name": "v1.0.0"}).encode()  # no "assets" key
        )
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch("urllib.request.urlopen", return_value=mock_resp),
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            with pytest.raises(RuntimeError, match="no downloadable assets"):
                download_update("1.0.0")

    def test_asset_with_no_browser_download_url_raises(self):
        """Asset entry missing 'browser_download_url' key → empty URL fails validation."""
        from launcher.core.downloader import download_update
        assets = [
            {
                "name": "launcher.exe",
                # No browser_download_url key — defaults to ""
            }
        ]
        mock_resp = _make_mock_http_response(
            json.dumps({"tag_name": "v1.0.0", "assets": assets}).encode()
        )
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch("urllib.request.urlopen", return_value=mock_resp),
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            with pytest.raises((ValueError, RuntimeError)):
                download_update("1.0.0")

    def test_network_error_on_asset_download_raises(self):
        """URLError during asset byte download is raised as RuntimeError."""
        from launcher.core.downloader import download_update
        assets = [
            {
                "name": "launcher.exe",
                "browser_download_url": "https://github.com/x/y/launcher.exe",
            }
        ]
        meta_resp = _make_mock_http_response(
            json.dumps({"tag_name": "v1.0.0", "assets": assets}).encode()
        )
        url_err = urllib.error.URLError("connection reset")
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch(
                "urllib.request.urlopen",
                side_effect=[meta_resp, url_err],
            ),
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            with pytest.raises(RuntimeError, match="Network error"):
                download_update("1.0.0")

    def test_accept_header_is_octet_stream_on_asset_download(self):
        """The asset download request uses Accept: application/octet-stream."""
        from launcher.core.downloader import download_update
        assets = [
            {
                "name": "launcher.exe",
                "browser_download_url": "https://github.com/x/y/launcher.exe",
            }
        ]
        meta_resp = _make_mock_http_response(
            json.dumps({"tag_name": "v1.0.0", "assets": assets}).encode()
        )
        asset_resp = _make_mock_chunked_response([b"data"])
        captured_requests: list = []

        original_urlopen_calls = [meta_resp, asset_resp]

        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch(
                "urllib.request.urlopen",
                side_effect=original_urlopen_calls,
            ) as mock_urlopen,
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            download_update("1.0.0")

        # Second call is the asset download; check its Accept header.
        assert mock_urlopen.call_count >= 2
        asset_request = mock_urlopen.call_args_list[1][0][0]
        assert asset_request.get_header("Accept") == "application/octet-stream"

    def test_metadata_accept_header_is_github_json(self):
        """The metadata fetch uses Accept: application/vnd.github+json."""
        from launcher.core.downloader import download_update
        assets = [
            {
                "name": "launcher.exe",
                "browser_download_url": "https://github.com/x/y/launcher.exe",
            }
        ]
        meta_resp = _make_mock_http_response(
            json.dumps({"tag_name": "v1.0.0", "assets": assets}).encode()
        )
        asset_resp = _make_mock_chunked_response([b"data"])
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch(
                "urllib.request.urlopen",
                side_effect=[meta_resp, asset_resp],
            ) as mock_urlopen,
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            download_update("1.0.0")

        meta_request = mock_urlopen.call_args_list[0][0][0]
        assert meta_request.get_header("Accept") == "application/vnd.github+json"

    def test_temp_dir_prefix_is_ts_launcher_update(self):
        """Temp directory name begins with 'ts_launcher_update_'."""
        from launcher.core.downloader import download_update
        assets = [
            {
                "name": "launcher.exe",
                "browser_download_url": "https://github.com/x/y/launcher.exe",
            }
        ]
        meta_resp = _make_mock_http_response(
            json.dumps({"tag_name": "v1.0.0", "assets": assets}).encode()
        )
        asset_resp = _make_mock_chunked_response([b"data"])
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch("urllib.request.urlopen", side_effect=[meta_resp, asset_resp]),
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            result = download_update("1.0.0")
        assert result.parent.name.startswith("ts_launcher_update_")

    def test_version_double_v_prefix_not_double_added(self):
        """'vv1.2.3' already starts with 'v' so no extra 'v' is prepended."""
        from launcher.core.downloader import _get_release_api_url
        url = _get_release_api_url("vv1.2.3")
        # The result should contain /tags/vv1.2.3 — not /tags/vvv1.2.3
        assert "/tags/vv1.2.3" in url
        assert "/tags/vvv1.2.3" not in url

    def test_http_500_on_metadata_raises_with_code(self):
        """HTTP 500 on metadata → RuntimeError message contains HTTP code."""
        from launcher.core.downloader import download_update
        http_err = urllib.error.HTTPError(
            url="https://api.github.com/...", code=500,
            msg="Internal Server Error", hdrs=None, fp=None,
        )
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch("urllib.request.urlopen", side_effect=http_err),
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            with pytest.raises(RuntimeError, match="500"):
                download_update("1.0.0")

    def test_download_result_is_a_file_path(self):
        """Return value of download_update is a Path object pointing to an existing file."""
        from launcher.core.downloader import download_update
        asset_bytes = b"installer content"
        assets = [
            {
                "name": "launcher.exe",
                "browser_download_url": "https://github.com/x/y/launcher.exe",
            }
        ]
        meta_resp = _make_mock_http_response(
            json.dumps({"tag_name": "v1.0.0", "assets": assets}).encode()
        )
        asset_resp = _make_mock_chunked_response([asset_bytes])
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch("urllib.request.urlopen", side_effect=[meta_resp, asset_resp]),
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            result = download_update("1.0.0")

        assert isinstance(result, Path)
        assert result.is_file()
        assert result.stat().st_size == len(asset_bytes)

    def test_arm64_macos_asset_preferred_over_x86(self):
        """On macOS ARM64 the arm64 .dmg asset is selected over the x86_64 one."""
        from launcher.core.downloader import download_update
        asset_bytes = b"apple silicon dmg"
        assets = [
            {
                "name": "launcher-x86_64.dmg",
                "browser_download_url": "https://github.com/x/y/launcher-x86_64.dmg",
            },
            {
                "name": "launcher-arm64.dmg",
                "browser_download_url": "https://github.com/x/y/launcher-arm64.dmg",
            },
        ]
        meta_resp = _make_mock_http_response(
            json.dumps({"tag_name": "v1.0.0", "assets": assets}).encode()
        )
        asset_resp = _make_mock_chunked_response([asset_bytes])
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch("urllib.request.urlopen", side_effect=[meta_resp, asset_resp]),
        ):
            mock_sys.platform = "darwin"
            mock_platform.machine.return_value = "arm64"
            result = download_update("1.0.0")
        assert "arm64" in result.name
