"""Persistent user settings for the Turbulence Solutions Launcher.

Settings are stored as JSON at an OS-appropriate location:
  Windows : %LOCALAPPDATA%\\TurbulenceSolutions\\settings.json
  macOS/Linux: ~/.config/TurbulenceSolutions/settings.json

The module is intentionally dependency-free (stdlib only) so that it can be
imported by both GUI and non-GUI code without pulling in heavy packages.
"""

from __future__ import annotations

import json
import os
import platform
import tempfile
from pathlib import Path
from typing import Any

# Default values returned when the settings file is absent or corrupt.
_DEFAULT_SETTINGS: dict[str, Any] = {
    "include_readmes": True,
}


def _settings_path() -> Path:
    """Return the full path to the settings JSON file for the current OS."""
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA") or str(
            Path.home() / "AppData" / "Local"
        )
        return Path(base) / "TurbulenceSolutions" / "settings.json"
    else:
        # XDG-compliant: ~/.config/TurbulenceSolutions/settings.json
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        return Path(base) / "TurbulenceSolutions" / "settings.json"


def load_settings() -> dict[str, Any]:
    """Load settings from disk, merging with defaults.

    Returns default settings if the file does not exist or cannot be parsed.
    Unknown extra keys present in the file are preserved.
    """
    path = _settings_path()
    if not path.exists():
        return dict(_DEFAULT_SETTINGS)

    try:
        raw = path.read_text(encoding="utf-8")
        on_disk: Any = json.loads(raw)
        if not isinstance(on_disk, dict):
            # File contains valid JSON but not a dict — treat as corrupt.
            return dict(_DEFAULT_SETTINGS)
        # Start from defaults so new keys are always present, then overlay disk values.
        merged = dict(_DEFAULT_SETTINGS)
        merged.update(on_disk)
        return merged
    except Exception:
        # Covers JSONDecodeError, PermissionError, UnicodeDecodeError, etc.
        return dict(_DEFAULT_SETTINGS)


def save_settings(settings: dict[str, Any]) -> None:
    """Persist *settings* to disk using an atomic write.

    The directory is created automatically if it does not exist.
    Writes to a temp file in the same directory, then uses os.replace() for
    an atomic rename — safe against partial writes and power loss.
    """
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = json.dumps(settings, indent=2, ensure_ascii=False)

    # Write to a sibling temp file, then atomically rename.
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(data)
        os.replace(tmp_path, path)
    except Exception:
        # Clean up orphaned temp file on failure.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def get_setting(key: str, default: Any = None) -> Any:
    """Return the value of *key* from persisted settings.

    Falls back to *default* if the key is not present in the loaded settings.
    """
    return load_settings().get(key, default)


def set_setting(key: str, value: Any) -> None:
    """Update a single *key* in persisted settings and save."""
    settings = load_settings()
    settings[key] = value
    save_settings(settings)
