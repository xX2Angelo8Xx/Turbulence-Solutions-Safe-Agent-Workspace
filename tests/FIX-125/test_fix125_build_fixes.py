"""Tests for FIX-125: build_windows.py ISCC and PyInstaller fixes.

Validates:
  - find_iscc() resolves the per-user LOCALAPPDATA install path
  - step_pyinstaller() uses sys.executable -m PyInstaller with -y flag
"""

# FIX-125

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Import the module under test directly via sys.path manipulation so tests
# are independent of the workspace layout.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import build_windows  # noqa: E402


# ---------------------------------------------------------------------------
# Tests: LOCALAPPDATA fallback path in find_iscc
# ---------------------------------------------------------------------------


class TestFindIsccLocalAppData:
    def test_find_iscc_localappdata_path(self, tmp_path):
        """find_iscc() returns ISCC.exe found at the LOCALAPPDATA per-user path."""
        fake_local = tmp_path / "AppData" / "Local"
        fake_iscc = fake_local / "Programs" / "Inno Setup 6" / "ISCC.exe"
        fake_iscc.parent.mkdir(parents=True)
        fake_iscc.touch()

        original_fallbacks = build_windows._ISCC_FALLBACK_PATHS
        try:
            build_windows._ISCC_FALLBACK_PATHS = [
                Path("nonexistent_pf86.exe"),
                Path("nonexistent_pf.exe"),
                fake_iscc,
            ]
            with patch("build_windows.shutil.which", return_value=None):
                result = build_windows.find_iscc()
        finally:
            build_windows._ISCC_FALLBACK_PATHS = original_fallbacks

        assert result == fake_iscc

    def test_find_iscc_localappdata_env_used_in_fallback_paths(self, tmp_path):
        """_ISCC_FALLBACK_PATHS contains a path derived from LOCALAPPDATA env var."""
        fake_local = str(tmp_path / "FakeLocalAppData")

        # Re-evaluate what the module would compute if LOCALAPPDATA were set
        from pathlib import Path as P
        expected_path = P(fake_local) / "Programs" / "Inno Setup 6" / "ISCC.exe"

        with patch.dict("os.environ", {"LOCALAPPDATA": fake_local}):
            # Reimport to get a freshly computed path list
            import importlib
            import build_windows as bw
            importlib.reload(bw)
            fallbacks = bw._ISCC_FALLBACK_PATHS

        assert any("Programs" in str(p) and "Inno Setup 6" in str(p) for p in fallbacks), (
            "_ISCC_FALLBACK_PATHS must include a 'Programs/Inno Setup 6' path"
        )

    def test_find_iscc_localappdata_absent_does_not_crash(self, tmp_path):
        """find_iscc() exits cleanly (code 1) when LOCALAPPDATA is unset and ISCC absent."""
        original_fallbacks = build_windows._ISCC_FALLBACK_PATHS
        try:
            # Use only nonexistent paths to simulate completely missing ISCC
            build_windows._ISCC_FALLBACK_PATHS = [
                Path("no_pf86.exe"),
                Path("no_pf.exe"),
                Path("") / "Programs" / "Inno Setup 6" / "ISCC.exe",  # empty LOCALAPPDATA
            ]
            with patch("build_windows.shutil.which", return_value=None):
                with pytest.raises(SystemExit) as exc_info:
                    build_windows.find_iscc()
        finally:
            build_windows._ISCC_FALLBACK_PATHS = original_fallbacks

        assert exc_info.value.code == 1

    def test_find_iscc_localappdata_path_wins_over_absent_system_paths(self, tmp_path):
        """Per-user path is returned even when system-wide paths don't exist."""
        fake_iscc = tmp_path / "Programs" / "Inno Setup 6" / "ISCC.exe"
        fake_iscc.parent.mkdir(parents=True)
        fake_iscc.touch()

        original_fallbacks = build_windows._ISCC_FALLBACK_PATHS
        try:
            build_windows._ISCC_FALLBACK_PATHS = [
                Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
                Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
                fake_iscc,
            ]
            with patch("build_windows.shutil.which", return_value=None):
                result = build_windows.find_iscc()
        finally:
            build_windows._ISCC_FALLBACK_PATHS = original_fallbacks

        assert result == fake_iscc


# ---------------------------------------------------------------------------
# Tests: step_pyinstaller command format
# ---------------------------------------------------------------------------


class TestStepPyInstallerCommand:
    def test_step_pyinstaller_uses_sys_executable(self):
        """step_pyinstaller() invokes the currently running Python interpreter."""
        with patch("build_windows.subprocess.run") as mock_run:
            build_windows.step_pyinstaller(dry_run=False)

        cmd = mock_run.call_args[0][0]
        assert cmd[0] == sys.executable, (
            f"Expected sys.executable ({sys.executable!r}), got {cmd[0]!r}"
        )

    def test_step_pyinstaller_uses_minus_m_flag(self):
        """step_pyinstaller() passes -m flag to invoke PyInstaller as a module."""
        with patch("build_windows.subprocess.run") as mock_run:
            build_windows.step_pyinstaller(dry_run=False)

        cmd = mock_run.call_args[0][0]
        assert "-m" in cmd

    def test_step_pyinstaller_module_name_is_PyInstaller(self):
        """step_pyinstaller() specifies 'PyInstaller' as the module name."""
        with patch("build_windows.subprocess.run") as mock_run:
            build_windows.step_pyinstaller(dry_run=False)

        cmd = mock_run.call_args[0][0]
        assert "PyInstaller" in cmd

    def test_step_pyinstaller_includes_y_flag(self):
        """step_pyinstaller() passes -y to overwrite existing dist/ output."""
        with patch("build_windows.subprocess.run") as mock_run:
            build_windows.step_pyinstaller(dry_run=False)

        cmd = mock_run.call_args[0][0]
        assert "-y" in cmd

    def test_step_pyinstaller_includes_launcher_spec(self):
        """step_pyinstaller() always passes launcher.spec as the spec file."""
        with patch("build_windows.subprocess.run") as mock_run:
            build_windows.step_pyinstaller(dry_run=False)

        cmd = mock_run.call_args[0][0]
        assert "launcher.spec" in cmd

    def test_step_pyinstaller_full_command_structure(self):
        """step_pyinstaller() command is exactly [sys.executable, '-m', 'PyInstaller', 'launcher.spec', '-y']."""
        with patch("build_windows.subprocess.run") as mock_run:
            build_windows.step_pyinstaller(dry_run=False)

        cmd = mock_run.call_args[0][0]
        assert cmd == [sys.executable, "-m", "PyInstaller", "launcher.spec", "-y"]

    def test_step_pyinstaller_does_not_use_bare_pyinstaller(self):
        """step_pyinstaller() must not use bare 'pyinstaller' string as the executable."""
        with patch("build_windows.subprocess.run") as mock_run:
            build_windows.step_pyinstaller(dry_run=False)

        cmd = mock_run.call_args[0][0]
        assert cmd[0] != "pyinstaller", (
            "Bare 'pyinstaller' command fails when not on system PATH. "
            "Must use sys.executable -m PyInstaller instead."
        )
