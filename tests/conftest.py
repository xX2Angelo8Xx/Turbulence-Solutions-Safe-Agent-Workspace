"""Configure pytest so that src/ is on sys.path for all tests.

This is required for the src-layout: packages live under src/ and are not
installed during development unless `pip install -e .` has been run
(deferred to INS-002).
"""

from __future__ import annotations

import os
import sys
import tkinter.filedialog
import tkinter.messagebox
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

sys.modules["customtkinter"] = MagicMock(name="customtkinter")


@pytest.fixture(autouse=True)
def _prevent_vscode_launch():
    """Prevent any test from accidentally launching real VS Code instances.

    Patches both the source module and the import binding in app.py so that
    no code path can reach the real subprocess.Popen call.
    """
    with patch("launcher.core.vscode.open_in_vscode", return_value=False), \
         patch("launcher.gui.app.open_in_vscode", return_value=False):
        yield


@pytest.fixture(autouse=True)
def _prevent_gui_popups():
    """Prevent real popup dialogs from appearing during tests.

    Patches tkinter.messagebox and tkinter.filedialog functions so that no
    real OS-level dialog boxes can appear during the test run.
    """
    with patch.object(tkinter.messagebox, "showinfo", return_value=None), \
         patch.object(tkinter.messagebox, "showerror", return_value=None), \
         patch.object(tkinter.messagebox, "showwarning", return_value=None), \
         patch.object(tkinter.messagebox, "askyesno", return_value=False), \
         patch.object(tkinter.filedialog, "askdirectory", return_value=""), \
         patch.object(tkinter.filedialog, "askopenfilename", return_value=""):
        yield


@pytest.fixture(autouse=True)
def _prevent_background_updates():
    """Prevent real HTTP calls to the GitHub Releases API during tests.

    Only patches the app.py local binding — NOT the source module.
    INS-009 tests directly test check_for_update and need the real function.
    """
    with patch("launcher.gui.app.check_for_update", return_value=(False, "0.0.0")):
        yield
