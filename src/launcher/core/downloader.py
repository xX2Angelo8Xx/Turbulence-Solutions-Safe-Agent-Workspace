"""Download the platform-appropriate installer from a GitHub Release."""

from __future__ import annotations

import hashlib
import json
import logging
import platform
import re
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from launcher.config import GITHUB_REPO_NAME, GITHUB_REPO_OWNER

_LOGGER = logging.getLogger(__name__)

_DOWNLOAD_TIMEOUT_SECONDS: int = 30

# Map sys.platform values to expected installer file extensions.
_PLATFORM_EXTENSIONS: dict[str, str] = {
    "win32": ".exe",
    "darwin": ".dmg",
    "linux": ".AppImage",
}

# Hostnames from which asset downloads are permitted.
_ALLOWED_DOWNLOAD_HOSTS: frozenset[str] = frozenset(
    {
        "github.com",
        "objects.githubusercontent.com",
        "releases.githubusercontent.com",
    }
)

# Only these characters are allowed in a sanitized filename.
_SAFE_FILENAME_RE: re.Pattern[str] = re.compile(r"[^\w.\-]")


def _get_release_api_url(version: str) -> str:
    """Return the GitHub API URL for the release tagged with *version*."""
    tag = version if version.startswith("v") else f"v{version}"
    return (
        f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"
        f"/releases/tags/{tag}"
    )


def _detect_platform_extension() -> str:
    """Return the asset file extension appropriate for the current platform."""
    extension = _PLATFORM_EXTENSIONS.get(sys.platform)
    if extension is None:
        raise RuntimeError(f"Unsupported platform: {sys.platform!r}")
    return extension


def _detect_architecture() -> str:
    """Return a normalised CPU architecture string.

    Returns ``'x86_64'`` for Intel/AMD 64-bit, ``'arm64'`` for Apple Silicon /
    AArch64, or the raw (lowercased) machine string for anything else.
    """
    machine = platform.machine().lower()
    if machine in {"amd64", "x86_64"}:
        return "x86_64"
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    return machine


def _sanitize_filename(name: str) -> str:
    """Return a safe filename, stripping path components and non-safe characters.

    Raises :class:`ValueError` if the result is empty.
    """
    # Strip any directory component the server might inject.
    name = Path(name).name
    sanitized = _SAFE_FILENAME_RE.sub("", name)
    if not sanitized:
        raise ValueError(
            f"Asset filename is empty after sanitization: {name!r}"
        )
    return sanitized


def _validate_download_url(url: str) -> None:
    """Raise :class:`ValueError` if *url* is not a safe GitHub asset URL.

    Enforces HTTPS and restricts hostnames to the known GitHub CDN hosts.
    This prevents SSRF attacks where a crafted API response redirects the
    download to an attacker-controlled server.
    """
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(
            f"Download URL does not use HTTPS: {url!r}"
        )
    if parsed.hostname not in _ALLOWED_DOWNLOAD_HOSTS:
        raise ValueError(
            f"Download URL hostname {parsed.hostname!r} is not in the allowed "
            f"list: {sorted(_ALLOWED_DOWNLOAD_HOSTS)}"
        )


def _select_asset(
    assets: list[dict],
    extension: str,
    arch: str,
) -> dict:
    """Select the best matching asset dict for the given extension and arch.

    First tries to find an asset whose name contains an architecture keyword.
    Falls back to the first asset whose name ends with *extension*.
    Raises :class:`RuntimeError` if no suitable asset exists.
    """
    # Keywords that identify each architecture in typical installer filenames.
    if arch == "x86_64":
        arch_keywords: list[str] = ["x86_64", "amd64", "x64", "win64"]
    elif arch == "arm64":
        arch_keywords = ["arm64", "aarch64"]
    else:
        arch_keywords = [arch]

    # Pass 1: extension AND architecture keyword present in filename.
    for asset in assets:
        name: str = asset.get("name", "")
        if name.endswith(extension):
            lower_name = name.lower()
            for kw in arch_keywords:
                if kw.lower() in lower_name:
                    return asset

    # Pass 2: extension only — accept any architecture.
    for asset in assets:
        name = asset.get("name", "")
        if name.endswith(extension):
            return asset

    raise RuntimeError(
        f"No asset found for extension={extension!r}, arch={arch!r}. "
        f"Available assets: {[a.get('name') for a in assets]}"
    )


def _compute_sha256(path: Path) -> str:
    """Return the lowercase hex SHA256 digest of the file at *path*."""
    sha = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _fetch_sha256_companion(assets: list[dict], asset_name: str) -> str | None:
    """Download the ``<asset_name>.sha256`` companion file and return the hash.

    Returns ``None`` if no companion asset exists or if the download fails.
    """
    companion_name = asset_name + ".sha256"
    for asset in assets:
        if asset.get("name") != companion_name:
            continue
        url: str = asset.get("browser_download_url", "")
        try:
            _validate_download_url(url)
            req = urllib.request.Request(url, headers={"Accept": "text/plain"})
            with urllib.request.urlopen(
                req, timeout=_DOWNLOAD_TIMEOUT_SECONDS
            ) as resp:
                content = resp.read().decode("utf-8").strip()
            # SHA256 files may be "<hash>  <filename>" or just "<hash>".
            return content.split()[0]
        except Exception as exc:  # noqa: BLE001
            _LOGGER.warning(
                "Failed to fetch .sha256 companion for %r: %s", asset_name, exc
            )
            return None
    return None


def download_update(version: str) -> Path:
    """Download the platform installer for *version* from GitHub Releases.

    Steps:
    1. Fetch release metadata from the GitHub Releases API.
    2. Select the asset matching the current platform and architecture.
    3. Validate the download URL (HTTPS, GitHub host).
    4. Download the asset to a temporary directory.
    5. Verify SHA256 integrity via a companion ``.sha256`` file when available.
    6. Return the :class:`pathlib.Path` to the downloaded installer.

    Raises :class:`RuntimeError` or :class:`ValueError` on any failure.
    Never returns silently on error.
    """
    release_url = _get_release_api_url(version)
    extension = _detect_platform_extension()
    arch = _detect_architecture()

    # --- fetch release metadata ---
    try:
        meta_req = urllib.request.Request(
            release_url,
            headers={"Accept": "application/vnd.github+json"},
        )
        with urllib.request.urlopen(
            meta_req, timeout=_DOWNLOAD_TIMEOUT_SECONDS
        ) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"Failed to fetch release metadata for {version!r}: HTTP {exc.code}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Network error fetching release metadata for {version!r}: {exc.reason}"
        ) from exc

    try:
        data: dict = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in GitHub API response for version {version!r}"
        ) from exc

    assets: list[dict] = data.get("assets", [])
    if not assets:
        raise RuntimeError(
            f"Release {version!r} has no downloadable assets"
        )

    # --- select the right asset ---
    asset = _select_asset(assets, extension, arch)
    asset_name: str = asset.get("name", "")
    download_url: str = asset.get("browser_download_url", "")

    _validate_download_url(download_url)
    safe_filename = _sanitize_filename(asset_name)

    # --- stream download to temp directory ---
    tmp_dir = tempfile.mkdtemp(prefix="ts_launcher_update_")
    dest_path = Path(tmp_dir) / safe_filename

    try:
        dl_req = urllib.request.Request(
            download_url,
            headers={"Accept": "application/octet-stream"},
        )
        with urllib.request.urlopen(
            dl_req, timeout=_DOWNLOAD_TIMEOUT_SECONDS
        ) as resp, dest_path.open("wb") as fh:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                fh.write(chunk)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"Failed to download asset {asset_name!r}: HTTP {exc.code}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Network error downloading asset {asset_name!r}: {exc.reason}"
        ) from exc

    # --- integrity verification ---
    actual_hash = _compute_sha256(dest_path)
    expected_hash = _fetch_sha256_companion(assets, asset_name)

    if expected_hash is not None:
        if actual_hash.lower() != expected_hash.lower():
            dest_path.unlink(missing_ok=True)
            raise RuntimeError(
                f"SHA256 mismatch for {asset_name!r}: "
                f"expected {expected_hash!r}, got {actual_hash!r}"
            )
        _LOGGER.info("SHA256 verified for %s: %s", asset_name, actual_hash)
    else:
        _LOGGER.warning(
            "No .sha256 companion found for %r — skipping integrity check",
            asset_name,
        )

    return dest_path
