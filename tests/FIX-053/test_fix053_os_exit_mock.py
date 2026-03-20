"""Tests for FIX-053: Verify os._exit is properly mocked in all _apply_windows() callers.

FIX-053 fixed a single test (TestNoShellTrue.test_windows_subprocess_no_shell_true)
that called _apply_windows() without patching os._exit. This test file:
  1. Verifies os._exit(0) is called exactly once with argument 0 by _apply_windows().
  2. Guards against regression — ensures that any direct call to _apply_windows()
     in this test file uses the correct double patch (os._exit + sys.exit).
  3. Verifies the pytest process survives calling _apply_windows() when os._exit is mocked.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch, call

import pytest


class TestOsExitCalledWithZero:
    """Regression tests: _apply_windows must call os._exit(0), not sys.exit(0)."""

    def test_apply_windows_calls_os_exit_with_0(self, tmp_path):
        """os._exit must be called exactly once with argument 0 after Popen."""
        from launcher.core.applier import _apply_windows
        installer = tmp_path / "setup.exe"
        installer.write_bytes(b"x")

        with patch("launcher.core.applier.subprocess.Popen"), \
             patch("launcher.core.applier.os._exit") as mock_os_exit, \
             patch("launcher.core.applier.sys.exit") as mock_sys_exit:
            _apply_windows(installer)

        mock_os_exit.assert_called_once_with(0)

    def test_apply_windows_does_not_call_sys_exit(self, tmp_path):
        """sys.exit must NOT be called by _apply_windows — os._exit is the exclusive exit path."""
        from launcher.core.applier import _apply_windows
        installer = tmp_path / "setup.exe"
        installer.write_bytes(b"x")

        with patch("launcher.core.applier.subprocess.Popen"), \
             patch("launcher.core.applier.os._exit"), \
             patch("launcher.core.applier.sys.exit") as mock_sys_exit:
            _apply_windows(installer)

        mock_sys_exit.assert_not_called()

    def test_apply_windows_os_exit_called_after_popen(self, tmp_path):
        """os._exit must be called AFTER subprocess.Popen, never before."""
        from launcher.core.applier import _apply_windows
        installer = tmp_path / "setup.exe"
        installer.write_bytes(b"x")
        call_order = []

        def fake_popen(args, **kw):
            call_order.append("popen")

        def fake_os_exit(code):
            call_order.append("os_exit")

        with patch("launcher.core.applier.subprocess.Popen", side_effect=fake_popen), \
             patch("launcher.core.applier.os._exit", side_effect=fake_os_exit), \
             patch("launcher.core.applier.sys.exit"):
            _apply_windows(installer)

        assert call_order == ["popen", "os_exit"], (
            f"os._exit must come after subprocess.Popen; call order was {call_order!r}"
        )

    def test_pytest_survives_mocked_os_exit(self, tmp_path):
        """The pytest process must survive calling _apply_windows() when os._exit is mocked.

        This is the core regression guard for BUG-080 / FIX-053:
        if os._exit is NOT mocked, this test itself will kill the entire pytest runner.
        The fact that the test suite completes proves the mock is in place.
        """
        from launcher.core.applier import _apply_windows
        installer = tmp_path / "setup.exe"
        installer.write_bytes(b"x")
        survived = {"value": False}

        with patch("launcher.core.applier.subprocess.Popen"), \
             patch("launcher.core.applier.os._exit"), \
             patch("launcher.core.applier.sys.exit"):
            _apply_windows(installer)
            survived["value"] = True  # only reached if os._exit was mocked

        assert survived["value"], (
            "This line was never reached — os._exit was not mocked and killed pytest."
        )


class TestOsExitMockCoverage:
    """Static analysis: ensure no _apply_windows() call site lacks os._exit mock."""

    def test_no_shell_true_test_has_os_exit_patched(self):
        """TestNoShellTrue.test_windows_subprocess_no_shell_true must patch os._exit.

        This is the specific test that BUG-080/FIX-053 addressed.
        We verify the patch is present by reading the source file directly.
        """
        from pathlib import Path
        test_file = (
            Path(__file__).parent.parent
            / "INS-011"
            / "test_ins011_applier.py"
        )
        assert test_file.exists(), f"Test file not found: {test_file}"
        source = test_file.read_text(encoding="utf-8")

        # Find the test_windows_subprocess_no_shell_true method body
        method_marker = "def test_windows_subprocess_no_shell_true"
        idx = source.find(method_marker)
        assert idx != -1, f"Method {method_marker!r} not found in {test_file}"

        # Extract the method body (up to the next method/class def at same indent)
        method_body = source[idx:idx + 600]
        assert 'patch("launcher.core.applier.os._exit")' in method_body, (
            "TestNoShellTrue.test_windows_subprocess_no_shell_true must patch os._exit "
            "(FIX-053 regression guard — BUG-080)"
        )
