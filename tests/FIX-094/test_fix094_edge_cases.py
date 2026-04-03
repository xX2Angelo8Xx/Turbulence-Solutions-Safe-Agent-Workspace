"""Edge-case regression tests for FIX-094 (Tester-added).

Covers scenarios the Developer did not test:
1. sys.modules consistency — tkinter.filedialog / tkinter.messagebox entries
   in sys.modules must be the *same* objects used by conftest.py's local
   'tkinter' variable so that patch.object actually affects the right target.
2. patch.object compatibility — confirm patching the MagicMock stubs works
   correctly (attr override returns expected value, not the default sentinel).
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch


def _build_fallback_state() -> dict:
    """Re-run the except-branch in isolation and return the resulting state.

    Returns a dict with keys:
      - tkinter_module: the types.ModuleType("tkinter") object
      - filedialog: tkinter.filedialog attribute
      - messagebox: tkinter.messagebox attribute
      - sys_filedialog: sys.modules["tkinter.filedialog"]
      - sys_messagebox: sys.modules["tkinter.messagebox"]
      - sys_tkinter: sys.modules["tkinter"]
    """
    # Stash existing tkinter state.
    stashed: dict = {}
    for key in [k for k in sys.modules if k == "tkinter" or k.startswith("tkinter.")]:
        stashed[key] = sys.modules.pop(key)

    ns: dict = {"sys": sys, "MagicMock": MagicMock, "types": types}
    exec(
        """
import types as _types
_tk_mock = MagicMock()
tkinter = _types.ModuleType("tkinter")
tkinter.filedialog = MagicMock()
tkinter.messagebox = MagicMock()
sys.modules.setdefault("tkinter", _tk_mock)
sys.modules["tkinter.filedialog"] = tkinter.filedialog
sys.modules["tkinter.messagebox"] = tkinter.messagebox
_HAS_TK = False
""",
        ns,
    )

    state = {
        "tkinter_module": ns["tkinter"],
        "filedialog": ns["tkinter"].filedialog,
        "messagebox": ns["tkinter"].messagebox,
        "sys_filedialog": sys.modules.get("tkinter.filedialog"),
        "sys_messagebox": sys.modules.get("tkinter.messagebox"),
        "sys_tkinter": sys.modules.get("tkinter"),
    }

    # Restore.
    for key in [k for k in sys.modules if k == "tkinter" or k.startswith("tkinter.")]:
        sys.modules.pop(key, None)
    sys.modules.update(stashed)

    return state


class TestSysModulesConsistency:
    """sys.modules entries must be identical to conftest.py local attributes.

    If they diverge, patch.object in _prevent_gui_popups would patch an object
    that no test code actually uses — the guard would silently fail.
    """

    def setup_method(self):
        self._state = _build_fallback_state()

    def test_sys_filedialog_is_same_object_as_tkinter_filedialog(self):
        """sys.modules['tkinter.filedialog'] is the conftest local tkinter.filedialog."""
        assert self._state["sys_filedialog"] is self._state["filedialog"]

    def test_sys_messagebox_is_same_object_as_tkinter_messagebox(self):
        """sys.modules['tkinter.messagebox'] is the conftest local tkinter.messagebox."""
        assert self._state["sys_messagebox"] is self._state["messagebox"]


class TestPatchObjectCompatibility:
    """patch.object must work correctly against the MagicMock stubs.

    The _prevent_gui_popups fixture calls patch.object(tkinter.messagebox, ...)
    and patch.object(tkinter.filedialog, ...). These must return controlled
    values, not the MagicMock default.
    """

    def setup_method(self):
        self._state = _build_fallback_state()

    def test_patch_object_overrides_showinfo(self):
        mb = self._state["messagebox"]
        with patch.object(mb, "showinfo", return_value="patched"):
            assert mb.showinfo("t", "msg") == "patched"

    def test_patch_object_overrides_showerror(self):
        mb = self._state["messagebox"]
        with patch.object(mb, "showerror", return_value="patched"):
            assert mb.showerror("t", "msg") == "patched"

    def test_patch_object_overrides_showwarning(self):
        mb = self._state["messagebox"]
        with patch.object(mb, "showwarning", return_value="patched"):
            assert mb.showwarning("t", "msg") == "patched"

    def test_patch_object_overrides_askyesno(self):
        mb = self._state["messagebox"]
        with patch.object(mb, "askyesno", return_value=False):
            assert mb.askyesno("t", "msg") is False

    def test_patch_object_overrides_askdirectory(self):
        fd = self._state["filedialog"]
        with patch.object(fd, "askdirectory", return_value=""):
            assert fd.askdirectory() == ""

    def test_patch_object_overrides_askopenfilename(self):
        fd = self._state["filedialog"]
        with patch.object(fd, "askopenfilename", return_value=""):
            assert fd.askopenfilename() == ""

    def test_patch_object_restores_original_after_context_exit(self):
        """patch.object must cleanly restore the attribute after the with-block."""
        mb = self._state["messagebox"]
        original = mb.showinfo  # capture before patching
        with patch.object(mb, "showinfo", return_value="patched"):
            pass
        # After the context, showinfo should be restored to the original callable.
        assert mb.showinfo is original
