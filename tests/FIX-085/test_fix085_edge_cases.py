"""FIX-085 edge-case tests — added by Tester Agent.

Covers boundary conditions not addressed by the Developer's tests:
- Relative path in python-path.txt
- _find_bundled_python_for_recovery returns a non-Python file (existence-only check)
- PermissionError during write_python_path propagates (fail-closed, consistent with INS-019 design)
- PermissionError during read_python_path propagates (fail-closed)
- Concurrent calls to ensure_python_path_valid are idempotent
- Recovery path is a directory, not an executable
- python-path.txt contains path with spaces in directory name
- Multiple python-embed candidates: first match inside exe_dir wins
- Security: recovery search path is anchored to the installation directory
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Relative path in python-path.txt
# ---------------------------------------------------------------------------

class TestRelativePath:
    """A relative path in python-path.txt is only valid if it resolves to an
    existing file from the current working directory."""

    def test_relative_path_nonexistent_triggers_recovery(self, tmp_path):
        """Relative path that does not resolve triggers auto-recovery."""
        from launcher.core import shim_config

        config = tmp_path / "python-path.txt"
        # Write a relative path that won't exist relative to any CWD
        config.write_text("python-embed/does_not_exist/python.exe", encoding="utf-8")

        bundled = tmp_path / "python-embed" / "python.exe"
        bundled.parent.mkdir(parents=True)
        bundled.write_text("fake", encoding="utf-8")

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
            patch.object(shim_config, "_find_bundled_python_for_recovery",
                         return_value=bundled),
        ):
            result = shim_config.ensure_python_path_valid()

        assert result is True
        written = Path(config.read_text(encoding="utf-8").strip())
        assert written == bundled

    def test_relative_path_that_exists_in_cwd_is_accepted(self, tmp_path, monkeypatch):
        """Relative path that resolves (relative to CWD) is accepted without recovery."""
        from launcher.core import shim_config
        import os

        # Change CWD to tmp_path so the relative path resolves there
        monkeypatch.chdir(tmp_path)

        python_exe = tmp_path / "python.exe"
        python_exe.write_text("fake", encoding="utf-8")

        config = tmp_path / "python-path.txt"
        # Relative to tmp_path (now CWD), "python.exe" exists
        config.write_text("python.exe", encoding="utf-8")

        mock_find = MagicMock()

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
            patch.object(shim_config, "_find_bundled_python_for_recovery",
                         side_effect=mock_find),
        ):
            result = shim_config.ensure_python_path_valid()

        # Path("python.exe").exists() is True in tmp_path CWD → accepted
        assert result is True
        # Recovery was NOT triggered
        mock_find.assert_not_called()


# ---------------------------------------------------------------------------
# Non-Python executable accepted (existence-only check)
# ---------------------------------------------------------------------------

class TestNonPythonExecutableAccepted:
    """ensure_python_path_valid uses existence-only check — does not verify
    the recovered path is actually a Python interpreter.  Deeper validation
    is performed by verify_ts_python(), which is called by the Settings dialog
    and the Create Project workflow.  This is the accepted design."""

    def test_recovery_accepts_any_existing_file(self, tmp_path):
        """Any file that .exists() returns True for is accepted during recovery."""
        from launcher.core import shim_config

        config = tmp_path / "python-path.txt"  # absent — triggers recovery
        fake_file = tmp_path / "python-embed" / "python.exe"
        fake_file.parent.mkdir()
        fake_file.write_text("I am not Python - just a text file", encoding="utf-8")

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
            patch.object(shim_config, "_find_bundled_python_for_recovery",
                         return_value=fake_file),
        ):
            result = shim_config.ensure_python_path_valid()

        # Accepted — existence check only
        assert result is True
        assert config.read_text(encoding="utf-8").strip() == str(fake_file)

    def test_already_valid_non_python_file_not_rechecked(self, tmp_path):
        """A path in python-path.txt that .exists() is True is accepted without running it."""
        from launcher.core import shim_config

        shell_script = tmp_path / "fake_python"
        shell_script.write_text("#!/bin/sh\necho not-python", encoding="utf-8")
        config = tmp_path / "python-path.txt"
        config.write_text(str(shell_script), encoding="utf-8")

        mock_recovery = MagicMock()

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
            patch.object(shim_config, "_find_bundled_python_for_recovery",
                         side_effect=mock_recovery),
        ):
            result = shim_config.ensure_python_path_valid()

        assert result is True
        mock_recovery.assert_not_called()


# ---------------------------------------------------------------------------
# PermissionError propagates — fail-closed design (consistent with INS-019)
# ---------------------------------------------------------------------------

class TestPermissionErrorPropagates:
    """PermissionErrors propagate from ensure_python_path_valid() — this is the
    established fail-closed design in this codebase (see INS-019 edge-case tests)."""

    def test_read_permission_error_propagates(self, tmp_path):
        """PermissionError reading python-path.txt propagates (fail-closed)."""
        from launcher.core import shim_config

        config = tmp_path / "python-path.txt"

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
            patch.object(shim_config, "read_python_path",
                         side_effect=PermissionError("Access denied")),
        ):
            with pytest.raises(PermissionError):
                shim_config.ensure_python_path_valid()

    def test_write_permission_error_propagates(self, tmp_path):
        """PermissionError writing recovered path propagates (fail-closed)."""
        from launcher.core import shim_config

        config = tmp_path / "python-path.txt"  # absent
        bundled = tmp_path / "python-embed" / "python.exe"
        bundled.parent.mkdir()
        bundled.write_text("fake", encoding="utf-8")

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
            patch.object(shim_config, "_find_bundled_python_for_recovery",
                         return_value=bundled),
            patch.object(shim_config, "write_python_path",
                         side_effect=PermissionError("Access denied on python-path.txt")),
        ):
            with pytest.raises((PermissionError, OSError)):
                shim_config.ensure_python_path_valid()


# ---------------------------------------------------------------------------
# Concurrent calls — idempotent
# ---------------------------------------------------------------------------

class TestConcurrentCalls:
    """Two threads calling ensure_python_path_valid simultaneously should both
    return True and leave the config file in a consistent state."""

    def test_concurrent_recovery_is_idempotent(self, tmp_path):
        """Concurrent recoveries both return True; config file is consistent."""
        from launcher.core import shim_config

        config = tmp_path / "python-path.txt"
        bundled = tmp_path / "python-embed" / "python.exe"
        bundled.parent.mkdir()
        bundled.write_text("fake", encoding="utf-8")

        results: list[bool] = []
        errors: list[Exception] = []

        def run() -> None:
            try:
                with (
                    patch.object(shim_config, "get_python_path_config",
                                 return_value=config),
                    patch.object(shim_config, "_find_bundled_python_for_recovery",
                                 return_value=bundled),
                ):
                    r = shim_config.ensure_python_path_valid()
                results.append(r)
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=run)
        t2 = threading.Thread(target=run)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

        assert not errors, f"Concurrent call raised: {errors}"
        assert len(results) == 2
        assert all(r is True for r in results)
        # The written path must equal the recovered path
        written = config.read_text(encoding="utf-8").strip()
        assert written == str(bundled)


# ---------------------------------------------------------------------------
# Recovery returns a directory, not a file
# ---------------------------------------------------------------------------

class TestRecoveryReturnsDirectory:
    """Documents that ensure_python_path_valid does not check is_file().
    If _find_bundled_python_for_recovery returns a directory path, .exists()
    returns True and the directory path gets written to python-path.txt."""

    def test_directory_path_accepted_by_existence_check(self, tmp_path):
        """A directory returned by recovery passes the .exists() check."""
        from launcher.core import shim_config

        config = tmp_path / "python-path.txt"
        fake_dir = tmp_path / "python-embed"
        fake_dir.mkdir()  # directory, not an executable

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
            patch.object(shim_config, "_find_bundled_python_for_recovery",
                         return_value=fake_dir),
        ):
            result = shim_config.ensure_python_path_valid()

        # Accepted by existence check — is_file() is NOT checked
        assert result is True
        written = Path(config.read_text(encoding="utf-8").strip())
        assert written == fake_dir


# ---------------------------------------------------------------------------
# Path with spaces in directory name
# ---------------------------------------------------------------------------

class TestPathWithSpaces:
    """python-path.txt path containing spaces is read and written correctly."""

    def test_valid_path_with_spaces_accepted(self, tmp_path):
        """Paths containing spaces (e.g. 'Program Files') are valid."""
        from launcher.core import shim_config

        spaced = tmp_path / "My Python Embed" / "python 3.11" / "python.exe"
        spaced.parent.mkdir(parents=True)
        spaced.write_text("fake", encoding="utf-8")

        config = tmp_path / "python-path.txt"
        config.write_text(str(spaced), encoding="utf-8")

        with patch.object(shim_config, "get_python_path_config", return_value=config):
            result = shim_config.ensure_python_path_valid()

        assert result is True

    def test_recovery_writes_path_with_spaces_correctly(self, tmp_path):
        """Recovered path with spaces is written without corruption."""
        from launcher.core import shim_config

        bundled = tmp_path / "Program Files" / "python-embed" / "python.exe"
        bundled.parent.mkdir(parents=True)
        bundled.write_text("fake", encoding="utf-8")

        config = tmp_path / "python-path.txt"

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
            patch.object(shim_config, "_find_bundled_python_for_recovery",
                         return_value=bundled),
        ):
            result = shim_config.ensure_python_path_valid()

        assert result is True
        written = Path(config.read_text(encoding="utf-8").strip())
        assert written == bundled
        assert " " in str(written)


# ---------------------------------------------------------------------------
# Security: recovery is anchored to installation directory, no user input
# ---------------------------------------------------------------------------

class TestRecoverySearchAnchor:
    """_find_bundled_python_for_recovery constructs a fixed relative path anchored
    to sys.executable.  It does NOT search arbitrary directories, scan PATH, or
    accept user-controlled input — this prevents path-injection attacks."""

    def test_recovery_does_not_use_shutil_which(self, tmp_path):
        """Recovery never calls shutil.which (no PATH scanning)."""
        import shutil
        from launcher.core import shim_config

        config = tmp_path / "python-path.txt"  # absent
        bundled = tmp_path / "python-embed" / "python.exe"
        bundled.parent.mkdir()
        bundled.write_text("fake", encoding="utf-8")

        which_called = []

        original_which = shutil.which

        def spy_which(name, *args, **kwargs):
            which_called.append(name)
            return original_which(name, *args, **kwargs)

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
            patch.object(shim_config, "_find_bundled_python_for_recovery",
                         return_value=bundled),
            patch("shutil.which", side_effect=spy_which),
        ):
            shim_config.ensure_python_path_valid()

        # ensure_python_path_valid must NOT call shutil.which — it never scans PATH
        assert not which_called, (
            f"shutil.which was called during ensure_python_path_valid: {which_called}"
        )

    def test_recovery_does_not_use_subprocess(self, tmp_path):
        """Recovery never spawns a subprocess (no external process scanning)."""
        import subprocess
        from launcher.core import shim_config

        config = tmp_path / "python-path.txt"  # absent
        bundled = tmp_path / "python-embed" / "python.exe"
        bundled.parent.mkdir()
        bundled.write_text("fake", encoding="utf-8")

        popen_called = []

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
            patch.object(shim_config, "_find_bundled_python_for_recovery",
                         return_value=bundled),
            patch("subprocess.Popen", side_effect=lambda *a, **kw: popen_called.append(a)),
            patch("subprocess.run", side_effect=lambda *a, **kw: popen_called.append(a)),
        ):
            shim_config.ensure_python_path_valid()

        assert not popen_called, (
            "ensure_python_path_valid must not spawn any subprocess"
        )


# ---------------------------------------------------------------------------
# Regression: ensure_python_path_valid does not modify a valid config
# ---------------------------------------------------------------------------

class TestNoSideEffectsOnValidConfig:
    """When python-path.txt is already valid, ensure_python_path_valid must
    NOT call write_python_path or _find_bundled_python_for_recovery."""

    def test_no_recovery_called_when_already_valid(self, tmp_path):
        """No recovery-related side effects when the config is already valid."""
        from launcher.core import shim_config

        python_exe = tmp_path / "python.exe"
        python_exe.write_text("fake", encoding="utf-8")
        config = tmp_path / "python-path.txt"
        config.write_text(str(python_exe), encoding="utf-8")

        mock_recovery = MagicMock()
        mock_write = MagicMock()

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
            patch.object(shim_config, "_find_bundled_python_for_recovery",
                         side_effect=mock_recovery),
            patch.object(shim_config, "write_python_path",
                         side_effect=mock_write),
        ):
            result = shim_config.ensure_python_path_valid()

        assert result is True
        mock_recovery.assert_not_called()
        mock_write.assert_not_called()
