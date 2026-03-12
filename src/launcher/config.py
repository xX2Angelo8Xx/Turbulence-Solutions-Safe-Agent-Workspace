"""Application-wide constants for the Turbulence Solutions Launcher."""

from pathlib import Path

APP_NAME: str = "Turbulence Solutions Launcher"
VERSION: str = "0.1.0"
TEMPLATES_DIR: Path = Path(__file__).resolve().parent.parent.parent / "templates"
GITHUB_OWNER: str = "TurbulenceSolutions"
GITHUB_REPO: str = "agent-environment-launcher"
GITHUB_API_TIMEOUT: int = 5
