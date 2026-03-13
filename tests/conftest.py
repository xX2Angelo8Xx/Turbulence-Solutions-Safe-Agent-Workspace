"""Configure pytest so that src/ is on sys.path for all tests.

This is required for the src-layout: packages live under src/ and are not
installed during development unless `pip install -e .` has been run
(deferred to INS-002).
"""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))


@pytest.fixture(autouse=True)
def _prevent_vscode_launch():
    """Prevent any test from accidentally launching real VS Code instances.

    Patches both the source module and the import binding in app.py so that
    no code path can reach the real subprocess.Popen call.
    """
    with patch("launcher.core.vscode.open_in_vscode", return_value=False), \
         patch("launcher.gui.app.open_in_vscode", return_value=False):
        yield
