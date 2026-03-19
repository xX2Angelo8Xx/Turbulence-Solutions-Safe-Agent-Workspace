"""In-app update check — queries GitHub Releases API for the latest version."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from launcher.config import GITHUB_RELEASES_URL
from launcher.core.github_auth import get_github_token

_TIMEOUT_SECONDS: int = 5


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

