"""In-app update check — queries GitHub Releases API for the latest version."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from launcher.config import GITHUB_RELEASES_URL
from launcher.core.github_auth import get_github_token

_TIMEOUT_SECONDS: int = 5
_LOGGER = logging.getLogger(__name__)

# Repo root is 3 levels up from this file (src/launcher/core/updater.py).
_REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent


def is_source_mode() -> bool:
    """Return True when running from a git clone, not a frozen PyInstaller bundle.

    Source mode is detected by two conditions both being true:
    1. The process is NOT frozen (sys._MEIPASS is absent).
    2. A .git directory exists at the repository root.
    """
    if getattr(sys, "_MEIPASS", None):
        return False
    return (_REPO_ROOT / ".git").is_dir()


def parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a semver string like '1.2.3' into a tuple of ints (1, 2, 3).

    A leading 'v' is stripped before parsing (e.g. 'v0.2.0' → (0, 2, 0)).
    """
    cleaned = version_str.lstrip("v")
    parts = cleaned.split(".")
    result: list[int] = []
    for part in parts:
        try:
            result.append(int(part))
        except ValueError:
            result.append(0)
    return tuple(result)


def check_for_update(current_version: str) -> tuple[bool, str]:
    """Check GitHub Releases for a newer version.

    Returns (update_available, latest_version).
    On any error, silently returns (False, current_version).
    """
    try:
        headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
        token = get_github_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(
            GITHUB_RELEASES_URL,
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as response:
            raw = response.read()
        data = json.loads(raw)
        tag_name: str = data["tag_name"]
        latest_version = tag_name.lstrip("v")
        current_tuple = parse_version(current_version)
        latest_tuple = parse_version(latest_version)
        return latest_tuple > current_tuple, latest_version
    except Exception:  # noqa: BLE001
        return False, current_version


def _get_local_git_version(repo_root: Path) -> str:
    """Return the current version tag from git describe --tags.

    Falls back to '0.0.0' if no tags exist or git is unavailable.
    """
    kwargs: dict = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            **kwargs,
        )
        if result.returncode == 0:
            return result.stdout.strip().lstrip("v")
    except Exception:  # noqa: BLE001
        pass
    return "0.0.0"


def check_for_update_source(
    repo_root: Path | None = None,
) -> tuple[bool, str]:
    """Check for updates when running in source mode.

    Compares the local git tag (git describe --tags) against the latest
    GitHub Release tag.  Returns (update_available, latest_version).
    On any error, silently returns (False, '0.0.0').
    """
    root = repo_root if repo_root is not None else _REPO_ROOT
    fetch_kwargs: dict = {}
    if sys.platform == "win32":
        fetch_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        # Fetch latest remote tags so the comparison is accurate.
        subprocess.run(
            ["git", "fetch", "--tags", "--quiet"],
            cwd=str(root),
            capture_output=True,
            check=False,
            timeout=15,
            **fetch_kwargs,
        )
        local_version = _get_local_git_version(root)
        # Re-use the existing GitHub Releases API call.
        update_available, latest_version = check_for_update(local_version)
        _LOGGER.info(
            "Source-mode update check: local=%s latest=%s available=%s",
            local_version,
            latest_version,
            update_available,
        )
        return update_available, latest_version
    except Exception:  # noqa: BLE001
        return False, "0.0.0"

