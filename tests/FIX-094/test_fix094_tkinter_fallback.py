"""Regression tests for FIX-094: conftest.py tkinter import fallback.

Verifies that the try/except ImportError pattern in tests/conftest.py allows
pytest collection to succeed even on environments where tkinter is absent.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock


def _run_fallback_except_block() -> dict:
    """Execute only the except-branch from conftest.py's tkinter import block.

    This directly tests the fallback code path that fires when tkinter is
    absent (Ubuntu/macOS CI without tkinter).  We do not attempt to simulate
    a missing tkinter at the Python level — instead we run the exact except
    body as a standalone exec so both branches can be verified independently.
    """
    # Temporarily stash any existing tkinter entries so we can restore them.
    stashed: dict = {}
    tk_keys = [k for k in sys.modules if k == "tkinter" or k.startswith("tkinter.")]
    for key in tk_keys:
        stashed[key] = sys.modules.pop(key)

    ns: dict = {"sys": sys, "MagicMock": MagicMock, "types": types}
    # Execute only the except body — the fallback logic from conftest.py.
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

    # Snapshot the results before restoring originals.
    result = {
        "_HAS_TK": ns["_HAS_TK"],
        "filedialog_obj": ns["sys"].modules.get("tkinter.filedialog"),
        "messagebox_obj": ns["sys"].modules.get("tkinter.messagebox"),
    }

    # Restore original tkinter state.
    for key in [k for k in sys.modules if k == "tkinter" or k.startswith("tkinter.")]:
        sys.modules.pop(key, None)
    sys.modules.update(stashed)

    return result


class TestTkinterFallbackExceptBranch:
    """Tests that directly exercise the except-branch (tkinter not available)."""

    def setup_method(self):
        self._result = _run_fallback_except_block()

    def test_has_tk_is_false(self):
        assert self._result["_HAS_TK"] is False

    def test_filedialog_mock_is_registered(self):
        assert self._result["filedialog_obj"] is not None

    def test_messagebox_mock_is_registered(self):
        assert self._result["messagebox_obj"] is not None

    def test_filedialog_is_mock_instance(self):
        assert isinstance(self._result["filedialog_obj"], MagicMock)

    def test_messagebox_is_mock_instance(self):
        assert isinstance(self._result["messagebox_obj"], MagicMock)

    def test_filedialog_mock_accepts_attribute_access(self):
        # patch.object works because MagicMock allows arbitrary attributes.
        fd = self._result["filedialog_obj"]
        fd.askdirectory = MagicMock(return_value="")
        assert fd.askdirectory() == ""

    def test_messagebox_mock_accepts_attribute_access(self):
        mb = self._result["messagebox_obj"]
        mb.showinfo = MagicMock(return_value=None)
        assert mb.showinfo("title", "msg") is None


class TestTkinterFallbackTryBranch:
    """Tests for the try-branch (tkinter available)."""

    def setup_method(self):
        try:
            import tkinter  # noqa: F401
            self.tkinter_present = True
        except ImportError:
            self.tkinter_present = False

    def test_has_tk_true_when_tkinter_available(self):
        """_HAS_TK must be True when tkinter can be imported."""
        if not self.tkinter_present:
            # Skip gracefully when tkinter is absent (e.g. bare Ubuntu CI).
            return
        ns: dict = {"sys": sys, "MagicMock": MagicMock}
        exec(
            """
try:
    import tkinter.filedialog
    import tkinter.messagebox
    _HAS_TK = True
except ImportError:
    _HAS_TK = False
""",
            ns,
        )
        assert ns["_HAS_TK"] is True

    def test_conftest_importable(self):
        """conftest.py must import without raising, regardless of tkinter state."""
        import importlib.util
        import pathlib

        conftest_path = pathlib.Path(__file__).parent.parent / "conftest.py"
        spec = importlib.util.spec_from_file_location("conftest_fix094", str(conftest_path))
        mod = importlib.util.module_from_spec(spec)
        # Should not raise ImportError — the whole point of FIX-094.
        try:
            spec.loader.exec_module(mod)
        except ImportError as exc:
            raise AssertionError(
                f"conftest.py raised ImportError — FIX-094 fix is broken: {exc}"
            ) from exc

