"""GitHub authentication helper — obtains a token from the environment or GitHub CLI."""

from __future__ import annotations

import os
import subprocess


def get_github_token() -> str | None:
    """Try to obtain a GitHub auth token.

    Checks in order:
    1. GITHUB_TOKEN environment variable (common for CI and manual config)
    2. GH_TOKEN environment variable (GitHub CLI sets this in some contexts)
    3. Subprocess call to 'gh auth token' (GitHub CLI keyring)

    Returns the token string, or None if no authentication is available.
    """
    # 1. Check GITHUB_TOKEN environment variable
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        return token

    # 2. Check GH_TOKEN environment variable
    token = os.environ.get("GH_TOKEN", "").strip()
    if token:
        return token

    # 3. Try GitHub CLI — subprocess.run with list args, not shell=True
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0:
            token = result.stdout.strip()
            if token:
                return token
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        # gh not installed, timed out, or OS-level error — fall through to None
        pass

    return None
