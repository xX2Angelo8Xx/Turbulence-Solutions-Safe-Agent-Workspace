"""Entry point for the Turbulence Solutions Launcher.

Run directly with:
    python src/launcher/main.py

Note: v2.1.2 test build for verifying Windows update restart fix.
"""

from __future__ import annotations

import os
import sys

# When run as a script, ensure src/ is on the path so absolute imports resolve.
_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from launcher.config import APP_NAME, VERSION  # noqa: E402
from launcher.core.os_utils import get_platform  # noqa: E402
from launcher.core.shim_config import ensure_shim_deployed  # noqa: E402


def main() -> None:
    """Launch the Turbulence Solutions Launcher application."""
    # PYTEST_CURRENT_TEST is set by pytest in the parent environment and is
    # inherited by child processes created via subprocess.run().  When main.py
    # is invoked as a subprocess from within a test (e.g. the INS-001 import
    # check), we skip the blocking GUI launch so the subprocess exits cleanly.
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    # FIX-080: Handle --version before any GUI imports (tkinter may not be available).
    if "--version" in sys.argv:
        print(f"{APP_NAME} {VERSION}")
        sys.exit(0)
    # FIX-056: Deploy the ts-python shim on first launch (macOS/Linux only).
    ensure_shim_deployed()
    from launcher.gui.app import App
    App().run()


if __name__ == "__main__":
    main()
