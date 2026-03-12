"""Application-wide constants for the Turbulence Solutions Launcher."""

from pathlib import Path

APP_NAME: str = "Turbulence Solutions Launcher"
VERSION: str = "0.1.0"
COLOR_PRIMARY: str = "#0A1D4E"
COLOR_SECONDARY: str = "#5BC5F2"
COLOR_TEXT: str = "#FFFFFF"
TEMPLATES_DIR: Path = Path(__file__).resolve().parent.parent.parent / "templates"

GITHUB_REPO_OWNER: str = "xX2Angelo8Xx"
GITHUB_REPO_NAME: str = "Turbulence-Solutions-Safe-Agent-Workspace"
GITHUB_RELEASES_URL: str = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
