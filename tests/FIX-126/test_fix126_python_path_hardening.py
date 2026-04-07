"""Tests for FIX-126: Harden Python runtime path persistence.

Covers:
1. ts-python.cmd self-healing fallback logic (tested via the shim_config helpers
   and by inspecting the .cmd source to verify fallback logic is present).
2. verify_ts_python() CREATE_NO_WINDOW flag on Windows.
3. ensure_python_path_valid() called before verify_ts_python() in _on_create_project.
"""
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


SHIM_PATH = (
    Path(__file__).parents[2]
    / "src" / "installer" / "shims" / "ts-python.cmd"
)


# ---------------------------------------------------------------------------
# 1. ts-python.cmd source inspection tests
# ---------------------------------------------------------------------------

class TestShimCmdSource:
    """Verify the .cmd source contains the required fallback logic."""

    def setup_method(self):
        self.source = SHIM_PATH.read_text(encoding="utf-8")

    def test_shim_cmd_contains_progfiles_fallback(self):
        """Fallback 1: %ProgramFiles%\\TurbulenceSolutions\\python-embed\\python.exe present."""
        assert "ProgramFiles" in self.source
        assert "TurbulenceSolutions\\python-embed\\python.exe" in self.source

    def test_shim_cmd_contains_localappdata_programs_fallback(self):
        """Fallback 2: %LOCALAPPDATA%\\Programs\\TurbulenceSolutions path present."""
        assert "LOCALAPPDATA%\\Programs\\TurbulenceSolutions" in self.source

    def test_shim_cmd_contains_auto_heal_write(self):
        """Auto-heal: shim writes back the found path to python-path.txt."""
        assert "echo !PYTHON_PATH!>" in self.source

    def test_shim_cmd_run_python_label_present(self):
        """Execution label :run_python must be present."""
        assert ":run_python" in self.source

    def test_shim_cmd_deny_present(self):
        """Deny path still exists when all fallbacks fail."""
        assert "permissionDecision" in self.source
        assert "deny" in self.source

    def test_shim_cmd_primary_path_read(self):
        """Primary path still reads from python-path.txt."""
        assert "python-path.txt" in self.source
        assert "set /p PYTHON_PATH=" in self.source

    def test_shim_cmd_deny_only_at_end(self):
        """Deny JSON must come after all fallback candidates."""
        prog_idx = self.source.index("ProgramFiles")
        local_idx = self.source.index("LOCALAPPDATA%\\Programs\\TurbulenceSolutions")
        deny_idx = self.source.index('"permissionDecision"')
        assert deny_idx > prog_idx
        assert deny_idx > local_idx


# ---------------------------------------------------------------------------
# 2. verify_ts_python() CREATE_NO_WINDOW flag
# ---------------------------------------------------------------------------

class TestVerifyTsPythonCreationFlags:
    """Verify CREATE_NO_WINDOW is passed on Windows, not on other platforms."""

    def _run_verify(self, platform_name, extra_patched):
        """Helper to invoke verify_ts_python with a mocked platform and subprocess."""
        import launcher.core.shim_config as sc

        fake_python = Path("/fake/python.exe")
        fake_shim = Path("/fake/ts-python.cmd")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "3.11.0"

        with (
            patch.object(sc, "read_python_path", return_value=fake_python),
            patch.object(fake_python, "exists", return_value=True),
            patch.object(sc, "get_shim_dir", return_value=fake_shim.parent),
            patch("launcher.core.shim_config.sys.platform", platform_name),
            patch("launcher.core.shim_config.subprocess.run", return_value=mock_result) as mock_run,
        ):
            # Make the fake shim appear to exist
            with patch("pathlib.Path.exists", return_value=True):
                sc.verify_ts_python()
            return mock_run

    def test_create_no_window_on_windows(self):
        """On win32, CREATE_NO_WINDOW should be in creationflags."""
        import launcher.core.shim_config as sc

        fake_python = Path("C:/fake/python.exe")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "3.11.0"

        with (
            patch.object(sc, "read_python_path", return_value=fake_python),
            patch("pathlib.Path.exists", return_value=True),
            patch("launcher.core.shim_config.sys.platform", "win32"),
            patch("launcher.core.shim_config.subprocess.run", return_value=mock_result) as mock_run,
        ):
            sc.verify_ts_python()

        _args, kwargs = mock_run.call_args
        assert "creationflags" in kwargs, "creationflags not passed on win32"
        assert kwargs["creationflags"] == subprocess.CREATE_NO_WINDOW

    def test_no_creation_flags_on_linux(self):
        """On linux, creationflags should NOT be passed."""
        import launcher.core.shim_config as sc

        fake_python = Path("/fake/python")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "3.11.0"

        with (
            patch.object(sc, "read_python_path", return_value=fake_python),
            patch("pathlib.Path.exists", return_value=True),
            patch("launcher.core.shim_config.sys.platform", "linux"),
            patch("launcher.core.shim_config.subprocess.run", return_value=mock_result) as mock_run,
        ):
            sc.verify_ts_python()

        _args, kwargs = mock_run.call_args
        assert "creationflags" not in kwargs, "creationflags should not be set on linux"

    def test_no_creation_flags_on_darwin(self):
        """On macOS, creationflags should NOT be passed."""
        import launcher.core.shim_config as sc

        fake_python = Path("/fake/python")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "3.11.0"

        with (
            patch.object(sc, "read_python_path", return_value=fake_python),
            patch("pathlib.Path.exists", return_value=True),
            patch("launcher.core.shim_config.sys.platform", "darwin"),
            patch("launcher.core.shim_config.subprocess.run", return_value=mock_result) as mock_run,
        ):
            sc.verify_ts_python()

        _args, kwargs = mock_run.call_args
        assert "creationflags" not in kwargs, "creationflags should not be set on darwin"


# ---------------------------------------------------------------------------
# 3. ensure_python_path_valid() called before verify_ts_python() in app.py
# ---------------------------------------------------------------------------

class TestAppCreateProjectRevalidation:
    """Verify ensure_python_path_valid() is called before verify_ts_python()
    in the _on_create_project background thread."""

    def test_ensure_python_path_called_before_verify_in_create(self):
        """ensure_python_path_valid must be called before verify_ts_python in _create()."""
        # Inspect app.py source to confirm call order.
        app_path = Path(__file__).parents[2] / "src" / "launcher" / "gui" / "app.py"
        source = app_path.read_text(encoding="utf-8")

        ensure_idx = source.index("ensure_python_path_valid()")
        # There are two calls: one at startup in __init__, one in _create().
        # The relevant one must appear before verify_ts_python() inside _create().
        verify_idx = source.index("verify_ts_python()")

        # Find the _create() function definition offset
        create_fn_idx = source.index("def _create()")

        # Both relevant calls must be after _create() starts
        # The ensure call (inside _create) must come before verify call
        ensure_in_create = source.index("ensure_python_path_valid()", create_fn_idx)
        verify_in_create = source.index("verify_ts_python()", create_fn_idx)

        assert ensure_in_create < verify_in_create, (
            "ensure_python_path_valid() must appear before verify_ts_python() "
            "inside _create()"
        )

    def test_ensure_python_path_valid_import_in_app(self):
        """ensure_python_path_valid must be imported in app.py."""
        app_path = Path(__file__).parents[2] / "src" / "launcher" / "gui" / "app.py"
        source = app_path.read_text(encoding="utf-8")
        assert "ensure_python_path_valid" in source
        # Verify it's imported, not just referenced
        assert "from launcher.core.shim_config import" in source
        import_line = next(
            l for l in source.splitlines()
            if "from launcher.core.shim_config import" in l
        )
        assert "ensure_python_path_valid" in import_line
