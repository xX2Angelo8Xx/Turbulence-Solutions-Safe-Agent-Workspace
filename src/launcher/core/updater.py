"""In-app update check, download, and apply.

Full implementation is provided in INS-009, INS-010, and INS-011.
"""

from __future__ import annotations

import collections
import json
import urllib.error
import urllib.request

from launcher.config import GITHUB_API_TIMEOUT, GITHUB_OWNER, GITHUB_REPO

UpdateCheckResult = collections.namedtuple(
    "UpdateCheckResult", ["update_available", "latest_version"]
)

_API_URL = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)


def _parse_version(version_str: str) -> tuple[int, ...]:
    version_str = version_str.lstrip("v")
    parts = version_str.split(".")
    result: list[int] = []
    for part in parts:
        numeric = ""
        for ch in part:
            if ch.isdigit():
                numeric += ch
            else:
                break
        result.append(int(numeric) if numeric else 0)
    while len(result) < 3:
        result.append(0)
    return tuple(result[:3])


def _is_newer(latest: str, current: str) -> bool:
    return _parse_version(latest) > _parse_version(current)


def _fetch_latest_version() -> str | None:
    try:
        req = urllib.request.Request(
            _API_URL,
            headers={"User-Agent": "TurbulenceSolutions-Launcher"},
        )
        with urllib.request.urlopen(req, timeout=GITHUB_API_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if not isinstance(data, dict):
            return None
        tag_name = data.get("tag_name")
        if not isinstance(tag_name, str) or not tag_name:
            return None
        return tag_name.lstrip("v")
    except Exception:
        return None


def check_for_update(current_version: str) -> UpdateCheckResult:
    """Check whether a newer version is available.

    Returns an ``UpdateCheckResult`` namedtuple of ``(update_available, latest_version)``.
    Queries the GitHub Releases API (INS-009). Never raises — all errors are caught
    silently and treated as no update available.
    """
    latest = _fetch_latest_version()
    if latest is None:
        return UpdateCheckResult(False, current_version)
    try:
        if _is_newer(latest, current_version):
            return UpdateCheckResult(True, latest)
        return UpdateCheckResult(False, current_version)
    except Exception:
        return UpdateCheckResult(False, current_version)
