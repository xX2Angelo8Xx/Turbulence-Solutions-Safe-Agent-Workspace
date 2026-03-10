"""In-app update check, download, and apply.

Full implementation is provided in INS-009, INS-010, and INS-011.
"""

from __future__ import annotations


def check_for_update(current_version: str) -> tuple[bool, str]:
    """Check whether a newer version is available.

    Returns a tuple of ``(update_available, latest_version)``.
    This stub always reports no update; the real implementation queries
    the GitHub Releases API (INS-009).
    """
    return False, current_version
