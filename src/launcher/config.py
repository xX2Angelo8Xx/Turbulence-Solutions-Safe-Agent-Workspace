"""Application-wide constants for the Turbulence Solutions Launcher."""

import sys
from pathlib import Path

APP_NAME: str = "Turbulence Solutions Launcher"
VERSION: str = "2.1.2"
COLOR_PRIMARY: str = "#0A1D4E"
COLOR_SECONDARY: str = "#5BC5F2"
COLOR_TEXT: str = "#FFFFFF"

# PyInstaller bundles templates/ at _MEIPASS/templates/.
# In development, templates/ is at repo_root/templates/ (3 levels up from config.py).
if getattr(sys, '_MEIPASS', None):
    TEMPLATES_DIR: Path = Path(sys._MEIPASS) / "templates"
else:
    TEMPLATES_DIR: Path = Path(__file__).resolve().parent.parent.parent / "templates"

# PyInstaller bundles TS-Logo.png at _MEIPASS/TS-Logo.png.
# In development, TS-Logo.png is at repo_root/ (3 levels up from config.py).
if getattr(sys, '_MEIPASS', None):
    LOGO_PATH: Path = Path(sys._MEIPASS) / "TS-Logo.png"
else:
    LOGO_PATH: Path = Path(__file__).resolve().parent.parent.parent / "TS-Logo.png"

# PyInstaller bundles TS-Logo.ico at _MEIPASS/TS-Logo.ico.
# In development, TS-Logo.ico is at repo_root/ (3 levels up from config.py).
if getattr(sys, '_MEIPASS', None):
    LOGO_ICO_PATH: Path = Path(sys._MEIPASS) / "TS-Logo.ico"
else:
    LOGO_ICO_PATH: Path = Path(__file__).resolve().parent.parent.parent / "TS-Logo.ico"

GITHUB_REPO_OWNER: str = "xX2Angelo8Xx"
GITHUB_REPO_NAME: str = "Turbulence-Solutions-Safe-Agent-Workspace"
GITHUB_RELEASES_URL: str = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"


def get_display_version() -> str:
    """Return the installed package version, falling back to VERSION constant."""
    # In PyInstaller bundles, always use the VERSION constant — importlib.metadata
    # may read stale .dist-info from a previous overlay install (BUG-075).
    if getattr(sys, '_MEIPASS', None):
        return VERSION
    try:
        from importlib.metadata import version, PackageNotFoundError
        return version("agent-environment-launcher")
    except PackageNotFoundError:
        return VERSION
