"""Shared version utility for tests.

Reads CURRENT_VERSION dynamically from src/launcher/config.py so that
version-consistency tests never need to hard-code the current version string.
Adding this as the single source of truth means future version bumps do NOT
require any test file updates.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _read_current_version() -> str:
    config_py = REPO_ROOT / "src" / "launcher" / "config.py"
    text = config_py.read_text(encoding="utf-8")
    match = re.search(r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not find VERSION constant in {config_py}")
    return match.group(1)


CURRENT_VERSION: str = _read_current_version()
