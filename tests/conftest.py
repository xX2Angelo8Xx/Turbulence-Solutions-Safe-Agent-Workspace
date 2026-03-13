"""Configure pytest so that src/ is on sys.path for all tests.

This module also installs global safety mocks to prevent tests from
creating real GUI windows, launching VS Code, or making network calls.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add src/ to sys.path for the src-layout.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# ---------------------------------------------------------------------------
# Force-replace customtkinter with a MagicMock BEFORE any test module
# imports launcher.gui.  Direct assignment (not setdefault) guarantees
# the real GUI toolkit is never loaded, even when pip-installed.
# ---------------------------------------------------------------------------
sys.modules["customtkinter"] = MagicMock(name="customtkinter")


@pytest.fixture(autouse=True)
def _reset_ctk_mock():
    """Reset the customtkinter mock before each test to prevent cross-test
    state pollution from accumulated widget call history."""
    ctk = sys.modules.get("customtkinter")
    if ctk is not None and hasattr(ctk, "reset_mock"):
        ctk.reset_mock()
    yield


@pytest.fixture(autouse=True)
def _prevent_vscode_launch():
    """Prevent any test from accidentally launching real VS Code instances.

    Three layers of protection:
    1. Patch open_in_vscode in the source module.
    2. Patch the import binding in app.py.
    3. Patch subprocess.Popen in the vscode module as a catch-all.
    """
    with patch("launcher.core.vscode.open_in_vscode", return_value=False), \
         patch("launcher.gui.app.open_in_vscode", return_value=False), \
         patch("launcher.core.vscode.subprocess.Popen"):
        yield


@pytest.fixture(autouse=True)
def _prevent_gui_popups():
    """Prevent tkinter messageboxes and file dialogs from opening real windows.

    app.py imports these as module aliases:
        import tkinter.messagebox as messagebox
        import tkinter.filedialog as filedialog

    Patching at the tkinter module level (not at import bindings) works
    regardless of how many times launcher.gui.app is reimported by test files.
    """
    with patch("tkinter.messagebox.showinfo", return_value="ok"), \
         patch("tkinter.messagebox.showerror", return_value="ok"), \
         patch("tkinter.messagebox.showwarning", return_value="ok"), \
         patch("tkinter.messagebox.askyesno", return_value=False), \
         patch("tkinter.filedialog.askdirectory", return_value=""), \
         patch("tkinter.filedialog.askopenfilename", return_value=""):
        yield


@pytest.fixture(autouse=True)
def _prevent_background_updates():
    """Prevent real HTTP calls from update-check daemon threads.

    App.__init__ spawns a thread calling check_for_update() which queries the
    GitHub Releases API.  Patching at both the source and the app.py binding
    ensures the thread returns immediately regardless of module reimports.
    """
    with patch("launcher.core.updater.check_for_update", return_value=(False, "")), \
         patch("launcher.gui.app.check_for_update", return_value=(False, "")):
        yield
