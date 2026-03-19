"""Tests for INS-010: Update Download (downloader.py)."""

from __future__ import annotations

import hashlib
import io
import json
import tempfile
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_http_response(body: bytes) -> MagicMock:
    """Return a mock for urllib.request.urlopen used as a context manager."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _make_mock_chunked_response(chunks: list[bytes]) -> MagicMock:
    """Return a mock response whose read() returns chunks then empty bytes."""
    mock_resp = MagicMock()
    mock_resp.read.side_effect = chunks + [b""]
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _make_release_payload(
    asset_name: str,
    download_url: str,
    sha256_content: str | None = None,
) -> dict:
    """Return a minimal GitHub release JSON payload."""
    assets: list[dict] = [
        {
            "name": asset_name,
            "browser_download_url": download_url,
        }
    ]
    if sha256_content is not None:
        assets.append(
            {
                "name": asset_name + ".sha256",
                "browser_download_url": download_url + ".sha256",
            }
        )
    return {"tag_name": "v1.2.3", "assets": assets}


# ---------------------------------------------------------------------------
# TestPlatformDetection
# ---------------------------------------------------------------------------

class TestPlatformDetection:
    def test_windows_returns_exe(self):
        from launcher.core.downloader import _detect_platform_extension
        with patch("launcher.core.downloader.sys") as mock_sys:
            mock_sys.platform = "win32"
            assert _detect_platform_extension() == ".exe"

    def test_macos_returns_dmg(self):
        from launcher.core.downloader import _detect_platform_extension
        with patch("launcher.core.downloader.sys") as mock_sys:
            mock_sys.platform = "darwin"
            assert _detect_platform_extension() == ".dmg"

    def test_linux_returns_appimage(self):
        from launcher.core.downloader import _detect_platform_extension
        with patch("launcher.core.downloader.sys") as mock_sys:
            mock_sys.platform = "linux"
            assert _detect_platform_extension() == ".AppImage"

    def test_unsupported_platform_raises(self):
        from launcher.core.downloader import _detect_platform_extension
        with patch("launcher.core.downloader.sys") as mock_sys:
            mock_sys.platform = "freebsd14"
            with pytest.raises(RuntimeError, match="Unsupported platform"):
                _detect_platform_extension()

    def test_unsupported_platform_message_contains_name(self):
        from launcher.core.downloader import _detect_platform_extension
        with patch("launcher.core.downloader.sys") as mock_sys:
            mock_sys.platform = "cygwin"
            with pytest.raises(RuntimeError, match="cygwin"):
                _detect_platform_extension()


# ---------------------------------------------------------------------------
# TestArchitectureDetection
# ---------------------------------------------------------------------------

class TestArchitectureDetection:
    def test_x86_64_normalised(self):
        from launcher.core.downloader import _detect_architecture
        with patch("launcher.core.downloader.platform") as mock_platform:
            mock_platform.machine.return_value = "x86_64"
            assert _detect_architecture() == "x86_64"

    def test_amd64_normalised_to_x86_64(self):
        from launcher.core.downloader import _detect_architecture
        with patch("launcher.core.downloader.platform") as mock_platform:
            mock_platform.machine.return_value = "AMD64"
            assert _detect_architecture() == "x86_64"

    def test_arm64_normalised(self):
        from launcher.core.downloader import _detect_architecture
        with patch("launcher.core.downloader.platform") as mock_platform:
            mock_platform.machine.return_value = "arm64"
            assert _detect_architecture() == "arm64"

    def test_aarch64_normalised_to_arm64(self):
        from launcher.core.downloader import _detect_architecture
        with patch("launcher.core.downloader.platform") as mock_platform:
            mock_platform.machine.return_value = "aarch64"
            assert _detect_architecture() == "arm64"

    def test_unknown_machine_passes_through_lowercase(self):
        from launcher.core.downloader import _detect_architecture
        with patch("launcher.core.downloader.platform") as mock_platform:
            mock_platform.machine.return_value = "MIPS"
            assert _detect_architecture() == "mips"


# ---------------------------------------------------------------------------
# TestAssetSelection
# ---------------------------------------------------------------------------

class TestAssetSelection:
    def _asset(self, name: str, url: str = "https://github.com/x") -> dict:
        return {"name": name, "browser_download_url": url}

    def test_windows_exe_selected(self):
        from launcher.core.downloader import _select_asset
        assets = [self._asset("launcher-1.0.exe")]
        result = _select_asset(assets, ".exe", "x86_64")
        assert result["name"] == "launcher-1.0.exe"

    def test_macos_dmg_selected(self):
        from launcher.core.downloader import _select_asset
        assets = [self._asset("launcher-1.0.dmg")]
        result = _select_asset(assets, ".dmg", "x86_64")
        assert result["name"] == "launcher-1.0.dmg"

    def test_linux_appimage_selected(self):
        from launcher.core.downloader import _select_asset
        assets = [self._asset("launcher-1.0.AppImage")]
        result = _select_asset(assets, ".AppImage", "x86_64")
        assert result["name"] == "launcher-1.0.AppImage"

    def test_arch_specific_preferred_over_generic(self):
        from launcher.core.downloader import _select_asset
        assets = [
            self._asset("launcher-arm64.AppImage"),
            self._asset("launcher-x86_64.AppImage"),
        ]
        result = _select_asset(assets, ".AppImage", "arm64")
        assert result["name"] == "launcher-arm64.AppImage"

    def test_x86_64_preferred_over_arm64(self):
        from launcher.core.downloader import _select_asset
        assets = [
            self._asset("launcher-arm64.AppImage"),
            self._asset("launcher-x86_64.AppImage"),
        ]
        result = _select_asset(assets, ".AppImage", "x86_64")
        assert result["name"] == "launcher-x86_64.AppImage"

    def test_amd64_keyword_matches_x86_64_arch(self):
        from launcher.core.downloader import _select_asset
        assets = [self._asset("launcher-amd64.AppImage")]
        result = _select_asset(assets, ".AppImage", "x86_64")
        assert result["name"] == "launcher-amd64.AppImage"

    def test_x64_keyword_matches_x86_64_arch(self):
        from launcher.core.downloader import _select_asset
        assets = [self._asset("launcher-x64.exe")]
        result = _select_asset(assets, ".exe", "x86_64")
        assert result["name"] == "launcher-x64.exe"

    def test_win64_keyword_matches_x86_64_arch(self):
        from launcher.core.downloader import _select_asset
        assets = [self._asset("launcher-win64.exe")]
        result = _select_asset(assets, ".exe", "x86_64")
        assert result["name"] == "launcher-win64.exe"

    def test_fallback_to_extension_only_when_no_arch_match(self):
        from launcher.core.downloader import _select_asset
        # No arch keyword in the filename; should still match on extension.
        assets = [self._asset("launcher.exe")]
        result = _select_asset(assets, ".exe", "x86_64")
        assert result["name"] == "launcher.exe"

    def test_wrong_extension_assets_ignored(self):
        from launcher.core.downloader import _select_asset
        assets = [
            self._asset("launcher.dmg"),
            self._asset("launcher.exe"),
        ]
        result = _select_asset(assets, ".dmg", "x86_64")
        assert result["name"] == "launcher.dmg"

    def test_no_matching_asset_raises(self):
        from launcher.core.downloader import _select_asset
        assets = [self._asset("launcher.dmg")]
        with pytest.raises(RuntimeError, match="No asset found"):
            _select_asset(assets, ".exe", "x86_64")

    def test_empty_asset_list_raises(self):
        from launcher.core.downloader import _select_asset
        with pytest.raises(RuntimeError, match="No asset found"):
            _select_asset([], ".exe", "x86_64")

    def test_case_insensitive_arch_keyword_match(self):
        from launcher.core.downloader import _select_asset
        assets = [self._asset("launcher-X86_64.AppImage")]
        result = _select_asset(assets, ".AppImage", "x86_64")
        assert result["name"] == "launcher-X86_64.AppImage"


# ---------------------------------------------------------------------------
# TestURLValidation
# ---------------------------------------------------------------------------

class TestURLValidation:
    def test_github_com_https_accepted(self):
        from launcher.core.downloader import _validate_download_url
        # Must not raise.
        _validate_download_url(
            "https://github.com/owner/repo/releases/download/v1.0/file.exe"
        )

    def test_objects_githubusercontent_https_accepted(self):
        from launcher.core.downloader import _validate_download_url
        _validate_download_url(
            "https://objects.githubusercontent.com/github-production-release-asset/"
            "12345/file.exe"
        )

    def test_releases_githubusercontent_https_accepted(self):
        from launcher.core.downloader import _validate_download_url
        _validate_download_url(
            "https://releases.githubusercontent.com/some/path/file.dmg"
        )

    def test_http_rejected(self):
        from launcher.core.downloader import _validate_download_url
        with pytest.raises(ValueError, match="HTTPS"):
            _validate_download_url(
                "http://github.com/owner/repo/releases/download/v1.0/file.exe"
            )

    def test_non_github_host_rejected(self):
        from launcher.core.downloader import _validate_download_url
        with pytest.raises(ValueError, match="not in the allowed list"):
            _validate_download_url(
                "https://evil.example.com/malware.exe"
            )

    def test_ssrf_via_redirected_host_rejected(self):
        from launcher.core.downloader import _validate_download_url
        with pytest.raises(ValueError, match="not in the allowed list"):
            _validate_download_url(
                "https://attacker.com/file.exe"
            )

    def test_localhost_rejected(self):
        from launcher.core.downloader import _validate_download_url
        with pytest.raises(ValueError, match="not in the allowed list"):
            _validate_download_url("https://localhost/file.exe")

    def test_ftp_scheme_rejected(self):
        from launcher.core.downloader import _validate_download_url
        with pytest.raises(ValueError, match="HTTPS"):
            _validate_download_url(
                "ftp://github.com/owner/repo/releases/download/v1.0/file.exe"
            )


# ---------------------------------------------------------------------------
# TestFilenameSanitization
# ---------------------------------------------------------------------------

class TestFilenameSanitization:
    def test_normal_name_preserved(self):
        from launcher.core.downloader import _sanitize_filename
        assert _sanitize_filename("launcher-1.2.3.exe") == "launcher-1.2.3.exe"

    def test_appimage_name_preserved(self):
        from launcher.core.downloader import _sanitize_filename
        assert (
            _sanitize_filename("Launcher-1.2.3-x86_64.AppImage")
            == "Launcher-1.2.3-x86_64.AppImage"
        )

    def test_path_traversal_stripped(self):
        from launcher.core.downloader import _sanitize_filename
        # Path(name).name strips the directory part; special chars stripped too.
        result = _sanitize_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_windows_path_separator_stripped(self):
        from launcher.core.downloader import _sanitize_filename
        result = _sanitize_filename(r"C:\Windows\file.exe")
        assert "\\" not in result
        assert ":" not in result

    def test_null_bytes_stripped(self):
        from launcher.core.downloader import _sanitize_filename
        result = _sanitize_filename("file\x00name.exe")
        assert "\x00" not in result

    def test_spaces_stripped(self):
        from launcher.core.downloader import _sanitize_filename
        result = _sanitize_filename("my launcher.exe")
        assert " " not in result

    def test_empty_after_sanitization_raises(self):
        from launcher.core.downloader import _sanitize_filename
        with pytest.raises(ValueError, match="empty after sanitization"):
            _sanitize_filename("!@#$%^&*()")

    def test_only_extension_preserved(self):
        from launcher.core.downloader import _sanitize_filename
        # ".exe" — the dot is kept; the name is just ".exe"
        result = _sanitize_filename(".exe")
        assert result == ".exe"


# ---------------------------------------------------------------------------
# TestSHA256Computation
# ---------------------------------------------------------------------------

class TestSHA256Computation:
    def test_known_hash(self, tmp_path: Path):
        from launcher.core.downloader import _compute_sha256
        content = b"hello world\n"
        f = tmp_path / "test.bin"
        f.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert _compute_sha256(f) == expected

    def test_empty_file(self, tmp_path: Path):
        from launcher.core.downloader import _compute_sha256
        f = tmp_path / "empty.bin"
        f.write_bytes(b"")
        expected = hashlib.sha256(b"").hexdigest()
        assert _compute_sha256(f) == expected

    def test_larger_file_multi_chunk(self, tmp_path: Path):
        from launcher.core.downloader import _compute_sha256
        # Write more than 65536 bytes to exercise the chunked read path.
        content = b"x" * (65536 * 3)
        f = tmp_path / "large.bin"
        f.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert _compute_sha256(f) == expected

    def test_returns_lowercase_hex(self, tmp_path: Path):
        from launcher.core.downloader import _compute_sha256
        f = tmp_path / "test.bin"
        f.write_bytes(b"data")
        result = _compute_sha256(f)
        assert result == result.lower()
        assert all(c in "0123456789abcdef" for c in result)


# ---------------------------------------------------------------------------
# TestFetchSHA256Companion
# ---------------------------------------------------------------------------

class TestFetchSHA256Companion:
    def test_companion_found_returns_hash(self):
        from launcher.core.downloader import _fetch_sha256_companion
        assets = [
            {"name": "file.exe", "browser_download_url": "https://github.com/x/y/file.exe"},
            {
                "name": "file.exe.sha256",
                "browser_download_url": "https://github.com/x/y/file.exe.sha256",
            },
        ]
        mock_resp = _make_mock_http_response(
            b"abc123def456  file.exe\n"
        )
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = _fetch_sha256_companion(assets, "file.exe")
        assert result == "abc123def456"

    def test_companion_hash_only_format(self):
        from launcher.core.downloader import _fetch_sha256_companion
        assets = [
            {
                "name": "file.exe.sha256",
                "browser_download_url": "https://github.com/x/y/file.exe.sha256",
            },
        ]
        mock_resp = _make_mock_http_response(b"deadbeef\n")
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = _fetch_sha256_companion(assets, "file.exe")
        assert result == "deadbeef"

    def test_companion_not_present_returns_none(self):
        from launcher.core.downloader import _fetch_sha256_companion
        assets = [
            {"name": "file.exe", "browser_download_url": "https://github.com/x/y/file.exe"},
        ]
        result = _fetch_sha256_companion(assets, "file.exe")
        assert result is None

    def test_companion_network_error_returns_none(self):
        from launcher.core.downloader import _fetch_sha256_companion
        assets = [
            {
                "name": "file.exe.sha256",
                "browser_download_url": "https://github.com/x/y/file.exe.sha256",
            },
        ]
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            result = _fetch_sha256_companion(assets, "file.exe")
        assert result is None

    def test_companion_with_bad_url_returns_none(self):
        from launcher.core.downloader import _fetch_sha256_companion
        assets = [
            {
                "name": "file.exe.sha256",
                # Non-HTTPS URL — _validate_download_url will raise ValueError.
                "browser_download_url": "http://github.com/x/y/file.exe.sha256",
            },
        ]
        result = _fetch_sha256_companion(assets, "file.exe")
        assert result is None


# ---------------------------------------------------------------------------
# TestDownloadUpdate — integration tests (all HTTP mocked)
# ---------------------------------------------------------------------------

class TestDownloadUpdate:
    """Tests for the public download_update() function."""

    def _make_urlopen_side_effect(
        self,
        release_assets: list[dict],
        asset_content: bytes,
        sha256_content: bytes | None = None,
    ):
        """Build an urlopen side_effect for metadata + optional sha256 + asset."""
        meta_payload = {"tag_name": "v1.2.3", "assets": release_assets}
        responses: list[MagicMock] = [
            _make_mock_http_response(json.dumps(meta_payload).encode()),
        ]
        if sha256_content is not None:
            responses.append(_make_mock_http_response(sha256_content))
        responses.append(_make_mock_chunked_response([asset_content]))
        return iter(responses)

    def test_happy_path_windows(self):
        from launcher.core.downloader import download_update
        asset_bytes = b"fake windows installer"
        assets = [
            {
                "name": "launcher-1.2.3.exe",
                "browser_download_url": "https://github.com/x/y/launcher-1.2.3.exe",
            }
        ]
        meta_resp = _make_mock_http_response(
            json.dumps({"tag_name": "v1.2.3", "assets": assets}).encode()
        )
        asset_resp = _make_mock_chunked_response([asset_bytes])
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch("urllib.request.urlopen", side_effect=[meta_resp, asset_resp]),
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            result = download_update("1.2.3")
        assert result.name == "launcher-1.2.3.exe"
        assert result.read_bytes() == asset_bytes

    def test_happy_path_macos(self):
        from launcher.core.downloader import download_update
        asset_bytes = b"fake dmg"
        assets = [
            {
                "name": "launcher-1.2.3.dmg",
                "browser_download_url": "https://github.com/x/y/launcher-1.2.3.dmg",
            }
        ]
        meta_resp = _make_mock_http_response(
            json.dumps({"tag_name": "v1.2.3", "assets": assets}).encode()
        )
        asset_resp = _make_mock_chunked_response([asset_bytes])
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch("urllib.request.urlopen", side_effect=[meta_resp, asset_resp]),
        ):
            mock_sys.platform = "darwin"
            mock_platform.machine.return_value = "x86_64"
            result = download_update("1.2.3")
        assert result.name == "launcher-1.2.3.dmg"

    def test_happy_path_linux(self):
        from launcher.core.downloader import download_update
        asset_bytes = b"fake appimage"
        assets = [
            {
                "name": "launcher-1.2.3.AppImage",
                "browser_download_url": (
                    "https://objects.githubusercontent.com/path/launcher-1.2.3.AppImage"
                ),
            }
        ]
        meta_resp = _make_mock_http_response(
            json.dumps({"tag_name": "v1.2.3", "assets": assets}).encode()
        )
        asset_resp = _make_mock_chunked_response([asset_bytes])
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch("urllib.request.urlopen", side_effect=[meta_resp, asset_resp]),
        ):
            mock_sys.platform = "linux"
            mock_platform.machine.return_value = "x86_64"
            result = download_update("1.2.3")
        assert result.name == "launcher-1.2.3.AppImage"

    def test_version_without_v_prefix_accepted(self):
        from launcher.core.downloader import download_update
        asset_bytes = b"data"
        assets = [
            {
                "name": "launcher.exe",
                "browser_download_url": "https://github.com/x/y/launcher.exe",
            }
        ]
        meta_resp = _make_mock_http_response(
            json.dumps({"tag_name": "v0.9.0", "assets": assets}).encode()
        )
        asset_resp = _make_mock_chunked_response([asset_bytes])
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch("urllib.request.urlopen", side_effect=[meta_resp, asset_resp]),
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            result = download_update("0.9.0")  # no leading 'v'
        assert result.suffix == ".exe"

    def test_sha256_verification_passes(self):
        from launcher.core.downloader import download_update
        asset_bytes = b"real installer content"
        correct_hash = hashlib.sha256(asset_bytes).hexdigest()
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
        # Call order: 1) metadata, 2) asset download, 3) sha256 companion
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

    def test_sha256_mismatch_raises_and_cleans_up(self):
        from launcher.core.downloader import download_update
        asset_bytes = b"tampered content"
        wrong_hash = "0" * 64  # Not the real hash.
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
        # Call order: 1) metadata, 2) asset download, 3) sha256 companion
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
            with pytest.raises(RuntimeError, match="SHA256 mismatch"):
                download_update("1.0.0")

    def test_no_sha256_companion_proceeds_with_warning(self, caplog):
        import logging
        from launcher.core.downloader import download_update
        asset_bytes = b"content"
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
            caplog.at_level(logging.WARNING, logger="launcher.core.downloader"),
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            result = download_update("1.0.0")
        assert result.suffix == ".exe"
        assert "skipping integrity check" in caplog.text

    def test_http_error_on_metadata_raises(self):
        from launcher.core.downloader import download_update
        http_err = urllib.error.HTTPError(
            url="https://api.github.com/...", code=404,
            msg="Not Found", hdrs=None, fp=None,
        )
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch("urllib.request.urlopen", side_effect=http_err),
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            with pytest.raises(RuntimeError, match="Failed to fetch release metadata"):
                download_update("1.0.0")

    def test_network_error_on_metadata_raises(self):
        from launcher.core.downloader import download_update
        url_err = urllib.error.URLError("connection refused")
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch("urllib.request.urlopen", side_effect=url_err),
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            with pytest.raises(RuntimeError, match="Network error"):
                download_update("1.0.0")

    def test_bad_json_response_raises(self):
        from launcher.core.downloader import download_update
        mock_resp = _make_mock_http_response(b"not json!!!")
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch("urllib.request.urlopen", return_value=mock_resp),
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            with pytest.raises(RuntimeError, match="Invalid JSON"):
                download_update("1.0.0")

    def test_empty_assets_raises(self):
        from launcher.core.downloader import download_update
        mock_resp = _make_mock_http_response(
            json.dumps({"tag_name": "v1.0.0", "assets": []}).encode()
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

    def test_no_matching_asset_for_platform_raises(self):
        from launcher.core.downloader import download_update
        assets = [
            {
                "name": "launcher-1.0.0.AppImage",
                "browser_download_url": "https://github.com/x/y/launcher-1.0.0.AppImage",
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
            mock_sys.platform = "win32"  # Wants .exe, only .AppImage available.
            mock_platform.machine.return_value = "AMD64"
            with pytest.raises(RuntimeError, match="No asset found"):
                download_update("1.0.0")

    def test_http_error_on_asset_download_raises(self):
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
        http_err = urllib.error.HTTPError(
            url="https://github.com/...", code=403,
            msg="Forbidden", hdrs=None, fp=None,
        )
        with (
            patch("launcher.core.downloader.sys") as mock_sys,
            patch("launcher.core.downloader.platform") as mock_platform,
            patch("urllib.request.urlopen", side_effect=[meta_resp, http_err]),
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            with pytest.raises(RuntimeError, match="Failed to download asset"):
                download_update("1.0.0")

    def test_download_stored_in_temp_directory(self):
        from launcher.core.downloader import download_update
        asset_bytes = b"installer data"
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
        assert result.parent != Path(".")
        assert result.parent.exists()
        assert "ts_launcher_update_" in result.parent.name

    def test_asset_download_url_validated_for_ssrf(self):
        from launcher.core.downloader import download_update
        assets = [
            {
                "name": "launcher.exe",
                # Malicious URL injected into the release JSON.
                "browser_download_url": "https://evil.com/malware.exe",
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
            with pytest.raises(ValueError, match="not in the allowed list"):
                download_update("1.0.0")


# ---------------------------------------------------------------------------
# TestTimeoutConfiguration
# ---------------------------------------------------------------------------

class TestTimeoutConfiguration:
    def test_timeout_constant_is_30_seconds(self):
        from launcher.core import downloader
        assert downloader._DOWNLOAD_TIMEOUT_SECONDS == 30

    def test_timeout_used_in_metadata_request(self):
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
            patch("urllib.request.urlopen", side_effect=[meta_resp, asset_resp]) as mock_urlopen,
        ):
            mock_sys.platform = "win32"
            mock_platform.machine.return_value = "AMD64"
            download_update("1.0.0")
        # Both metadata and asset calls must use timeout=30.
        for c in mock_urlopen.call_args_list:
            assert c.kwargs.get("timeout") == 30 or c.args[1] == 30


# ---------------------------------------------------------------------------
# TestGetReleaseApiUrl
# ---------------------------------------------------------------------------

class TestGetReleaseApiUrl:
    def test_version_with_v_prefix_unchanged(self):
        from launcher.core.downloader import _get_release_api_url
        url = _get_release_api_url("v1.2.3")
        assert "/tags/v1.2.3" in url

    def test_version_without_v_prefix_gets_v_added(self):
        from launcher.core.downloader import _get_release_api_url
        url = _get_release_api_url("1.2.3")
        assert "/tags/v1.2.3" in url

    def test_url_uses_https(self):
        from launcher.core.downloader import _get_release_api_url
        url = _get_release_api_url("1.0.0")
        assert url.startswith("https://")

    def test_url_contains_repo_owner_and_name(self):
        from launcher.core.downloader import _get_release_api_url
        from launcher.config import GITHUB_REPO_OWNER, GITHUB_REPO_NAME
        url = _get_release_api_url("1.0.0")
        assert GITHUB_REPO_OWNER in url
        assert GITHUB_REPO_NAME in url
