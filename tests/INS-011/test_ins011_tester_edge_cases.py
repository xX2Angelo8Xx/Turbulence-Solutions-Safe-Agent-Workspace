"""Tester-added edge case tests for INS-011: Update Apply and Restart.

These tests focus on security, platform edge cases, boundary conditions,
and re-entrancy scenarios that the Developer's tests did not cover.
"""

from __future__ import annotations

import inspect
import os
import stat
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Security: Static source scan
# ---------------------------------------------------------------------------

class TestStaticSecurity:
    """Static analysis checks on applier.py source code."""

    def test_no_shell_true_in_source(self):
        """applier.py must have zero occurrences of shell=True."""
        import launcher.core.applier as applier_module
        source = inspect.getsource(applier_module)
        assert "shell=True" not in source, (
            "Found 'shell=True' in applier.py — this is a security violation."
        )

    def test_all_subprocess_calls_use_shell_false(self):
        """Every subprocess call in applier.py must use shell=False."""
        import launcher.core.applier as applier_module
        source = inspect.getsource(applier_module)
        # Count occurrences of shell= assignments
        import re
        shell_uses = re.findall(r"shell\s*=\s*(True|False)", source)
        # All must be False
        for val in shell_uses:
            assert val == "False", (
                f"Found shell={val} in applier.py — must always be 'False'."
            )

    def test_no_eval_or_exec_in_source(self):
        """applier.py must not use eval() or exec() per security-rules.md."""
        import launcher.core.applier as applier_module
        source = inspect.getsource(applier_module)
        assert "eval(" not in source
        assert "exec(" not in source


# ---------------------------------------------------------------------------
# Platform edge cases
# ---------------------------------------------------------------------------

class TestPlatformEdgeCases:
    """Edge cases for platform dispatch logic."""

    def test_linux2_dispatches_to_apply_linux(self, tmp_path):
        """linux2 (legacy Python Linux identifier) must dispatch to _apply_linux."""
        from launcher.core import applier
        installer = tmp_path / "launcher.AppImage"
        installer.write_bytes(b"x")
        with patch("launcher.core.applier.sys") as mock_sys, \
             patch("launcher.core.applier._apply_linux") as mock_linux:
            mock_sys.platform = "linux2"
            applier.apply_update(installer)
            mock_linux.assert_called_once_with(installer)

    def test_linux_arm_dispatches_to_apply_linux(self, tmp_path):
        """linux with ARM suffix variant still dispatches to _apply_linux."""
        from launcher.core import applier
        installer = tmp_path / "launcher.AppImage"
        installer.write_bytes(b"x")
        with patch("launcher.core.applier.sys") as mock_sys, \
             patch("launcher.core.applier._apply_linux") as mock_linux:
            mock_sys.platform = "linux-arm"
            applier.apply_update(installer)
            mock_linux.assert_called_once_with(installer)

    def test_apply_update_dispatches_exactly_once(self, tmp_path):
        """apply_update must invoke the platform handler exactly once, never twice."""
        from launcher.core import applier
        installer = tmp_path / "setup.exe"
        installer.write_bytes(b"x")
        call_count = {"n": 0}

        def counting_handler(path):
            call_count["n"] += 1

        with patch("launcher.core.applier.sys") as mock_sys, \
             patch("launcher.core.applier._apply_windows", side_effect=counting_handler):
            mock_sys.platform = "win32"
            applier.apply_update(installer)

        assert call_count["n"] == 1, "Platform handler must be called exactly once."


# ---------------------------------------------------------------------------
# Path edge cases
# ---------------------------------------------------------------------------

class TestPathEdgeCases:
    """Tests for installer paths with unusual characteristics."""

    def test_windows_path_with_spaces(self, tmp_path):
        """Windows: installer path containing spaces must be passed as a single list arg."""
        from launcher.core.applier import _apply_windows
        spacy_dir = tmp_path / "My Programs Dir"
        spacy_dir.mkdir()
        installer = spacy_dir / "My Setup File.exe"
        installer.write_bytes(b"x")
        captured = {}

        def fake_popen(args, **kw):
            captured["args"] = args

        with patch("launcher.core.applier.subprocess.Popen", side_effect=fake_popen), \
             patch("launcher.core.applier.sys.exit"):
            _apply_windows(installer)

        assert captured["args"][0] == str(installer), (
            "Installer path with spaces must be preserved as a single string in args."
        )
        assert " " in captured["args"][0], "Test fixture must include spaces."
        assert isinstance(captured["args"], list), "Args must be a list, not a string."

    def test_windows_path_with_unicode(self, tmp_path):
        """Windows: installer path with unicode characters must be passed correctly."""
        from launcher.core.applier import _apply_windows
        unicode_dir = tmp_path / "Tëst Üpdate"
        unicode_dir.mkdir()
        installer = unicode_dir / "setup_v1.0.exe"
        installer.write_bytes(b"x")
        captured = {}

        def fake_popen(args, **kw):
            captured["args"] = args

        with patch("launcher.core.applier.subprocess.Popen", side_effect=fake_popen), \
             patch("launcher.core.applier.sys.exit"):
            _apply_windows(installer)

        assert captured["args"][0] == str(installer)

    def test_validate_accepts_regular_file(self, tmp_path):
        """Baseline: a regular file passes _validate_installer_path."""
        from launcher.core.applier import _validate_installer_path
        f = tmp_path / "update.exe"
        f.write_bytes(b"PE\x00\x00")
        _validate_installer_path(f)  # must not raise

    def test_validate_rejects_empty_file(self, tmp_path):
        """Empty file is still a file — validation must pass (size is not checked)."""
        from launcher.core.applier import _validate_installer_path
        f = tmp_path / "empty.exe"
        f.write_bytes(b"")
        _validate_installer_path(f)  # size is not a validation criterion; must pass

    def test_validate_rejects_nested_directory(self, tmp_path):
        """A nested directory inside tmp_path must raise ValueError, not be silently accepted."""
        from launcher.core.applier import _validate_installer_path
        nested = tmp_path / "sub" / "dir"
        nested.mkdir(parents=True)
        with pytest.raises(ValueError):
            _validate_installer_path(nested)


# ---------------------------------------------------------------------------
# macOS edge cases
# ---------------------------------------------------------------------------

class TestMacosEdgeCases:
    """macOS-specific edge case tests."""

    def test_macos_nobrowse_flag_in_attach(self, tmp_path):
        """-nobrowse flag must be passed to hdiutil attach to prevent Finder sidebar entry."""
        from launcher.core.applier import _apply_macos
        installer = tmp_path / "launcher.dmg"
        installer.write_bytes(b"x")
        mount_point = tmp_path / "mnt"
        mount_point.mkdir()
        (mount_point / "Launcher.app").mkdir()
        attach_args_captured = []

        def fake_run(args, **kw):
            if "attach" in args:
                attach_args_captured.extend(args)
            result = MagicMock()
            result.returncode = 0
            result.stderr = b""
            return result

        with patch("launcher.core.applier.tempfile.mkdtemp", return_value=str(mount_point)), \
             patch("launcher.core.applier.subprocess.run", side_effect=fake_run), \
             patch("launcher.core.applier.sys.exit"):
            _apply_macos(installer)

        assert "-nobrowse" in attach_args_captured, (
            "hdiutil attach must include -nobrowse to prevent DMG sidebar entry."
        )

    def test_macos_installer_path_passed_to_hdiutil(self, tmp_path):
        """hdiutil attach must receive the actual installer path as an argument."""
        from launcher.core.applier import _apply_macos
        installer = tmp_path / "launcher.dmg"
        installer.write_bytes(b"x")
        mount_point = tmp_path / "mnt"
        mount_point.mkdir()
        (mount_point / "Launcher.app").mkdir()
        attach_args_captured = []

        def fake_run(args, **kw):
            if "attach" in args:
                attach_args_captured.extend(args)
            result = MagicMock()
            result.returncode = 0
            result.stderr = b""
            return result

        with patch("launcher.core.applier.tempfile.mkdtemp", return_value=str(mount_point)), \
             patch("launcher.core.applier.subprocess.run", side_effect=fake_run), \
             patch("launcher.core.applier.sys.exit"):
            _apply_macos(installer)

        assert str(installer) in attach_args_captured, (
            "hdiutil attach must receive the actual DMG installer path."
        )

    def test_macos_mount_point_uses_mkdtemp_not_volumes(self, tmp_path):
        """Mount point must come from tempfile.mkdtemp, not a hardcoded /Volumes path."""
        from launcher.core import applier
        installer = tmp_path / "launcher.dmg"
        installer.write_bytes(b"x")
        mount_point = tmp_path / "mnt"
        mount_point.mkdir()
        (mount_point / "Launcher.app").mkdir()
        mkdtemp_calls = []

        def fake_mkdtemp(**kw):
            mkdtemp_calls.append(kw)
            return str(mount_point)

        def fake_run(args, **kw):
            result = MagicMock()
            result.returncode = 0
            result.stderr = b""
            return result

        with patch("launcher.core.applier.tempfile.mkdtemp", side_effect=fake_mkdtemp), \
             patch("launcher.core.applier.subprocess.run", side_effect=fake_run), \
             patch("launcher.core.applier.sys.exit"):
            applier._apply_macos(installer)

        assert len(mkdtemp_calls) == 1, "Exactly one temp directory must be created."
        prefix = mkdtemp_calls[0].get("prefix", "")
        assert "ts_update" in prefix, (
            f"Temp directory prefix should identify the update purpose; got {prefix!r}"
        )

    def test_find_app_bundle_with_multiple_app_dirs(self, tmp_path):
        """_find_app_bundle returns the first .app dir when multiple are present."""
        from launcher.core.applier import _find_app_bundle
        # Create multiple .app dirs — both are valid bundles
        bundle_a = tmp_path / "AppA.app"
        bundle_a.mkdir()
        bundle_b = tmp_path / "AppB.app"
        bundle_b.mkdir()
        # Must return one of them without error (not raise)
        result = _find_app_bundle(tmp_path)
        assert result.suffix == ".app"
        assert result.is_dir()

    def test_macos_rsync_source_has_trailing_slash(self, tmp_path):
        """rsync source path must have a trailing slash for correct directory sync."""
        from launcher.core.applier import _apply_macos
        installer = tmp_path / "launcher.dmg"
        installer.write_bytes(b"x")
        mount_point = tmp_path / "mnt"
        mount_point.mkdir()
        (mount_point / "Launcher.app").mkdir()
        rsync_args_captured = []

        def fake_run(args, **kw):
            if args and args[0] == "rsync":
                rsync_args_captured.extend(args)
            result = MagicMock()
            result.returncode = 0
            result.stderr = b""
            return result

        with patch("launcher.core.applier.tempfile.mkdtemp", return_value=str(mount_point)), \
             patch("launcher.core.applier.subprocess.run", side_effect=fake_run), \
             patch("launcher.core.applier.sys.exit"):
            _apply_macos(installer)

        # rsync source (second-to-last arg) must end with /
        assert len(rsync_args_captured) >= 2
        source_arg = rsync_args_captured[-2]
        assert source_arg.endswith("/"), (
            f"rsync source must have trailing slash for directory sync; got {source_arg!r}"
        )

    def test_macos_dest_is_under_applications(self, tmp_path):
        """/Applications/ prefix must be used as rsync destination."""
        from launcher.core.applier import _apply_macos
        installer = tmp_path / "launcher.dmg"
        installer.write_bytes(b"x")
        mount_point = tmp_path / "mnt"
        mount_point.mkdir()
        (mount_point / "Launcher.app").mkdir()
        rsync_args_captured = []

        def fake_run(args, **kw):
            if args and args[0] == "rsync":
                rsync_args_captured.extend(args)
            result = MagicMock()
            result.returncode = 0
            result.stderr = b""
            return result

        with patch("launcher.core.applier.tempfile.mkdtemp", return_value=str(mount_point)), \
             patch("launcher.core.applier.subprocess.run", side_effect=fake_run), \
             patch("launcher.core.applier.sys.exit"):
            _apply_macos(installer)

        dest_arg = rsync_args_captured[-1]
        assert dest_arg.startswith("/Applications/"), (
            f"rsync destination must start with /Applications/; got {dest_arg!r}"
        )


# ---------------------------------------------------------------------------
# Linux edge cases
# ---------------------------------------------------------------------------

class TestLinuxEdgeCases:
    """Linux-specific edge case tests."""

    def test_linux_execv_passes_sys_argv(self, tmp_path):
        """os.execv must receive the original sys.argv so relaunch preserves CLI args."""
        from launcher.core.applier import _apply_linux
        installer = tmp_path / "launcher.AppImage"
        installer.write_bytes(b"x")
        execv_calls = []
        fake_argv = ["launcher", "--arg1", "--arg2"]

        with patch.object(Path, "chmod"), \
             patch("launcher.core.applier.os.replace"), \
             patch("launcher.core.applier.os.execv",
                   side_effect=lambda p, a: execv_calls.append((p, a))), \
             patch("launcher.core.applier.sys") as mock_sys:
            mock_sys.executable = str(tmp_path / "launcher.AppImage")
            mock_sys.argv = fake_argv
            _apply_linux(installer)

        assert len(execv_calls) == 1
        _, argv_passed = execv_calls[0]
        assert argv_passed == fake_argv, (
            f"sys.argv must be passed to os.execv; got {argv_passed!r}"
        )

    def test_linux_execv_target_matches_os_replace_destination(self, tmp_path):
        """os.execv path must be the same as the os.replace destination (sys.executable)."""
        from launcher.core.applier import _apply_linux
        installer = tmp_path / "launcher.AppImage"
        installer.write_bytes(b"x")
        replace_calls = []
        execv_calls = []

        with patch.object(Path, "chmod"), \
             patch("launcher.core.applier.os.replace",
                   side_effect=lambda s, d: replace_calls.append((s, d))), \
             patch("launcher.core.applier.os.execv",
                   side_effect=lambda p, a: execv_calls.append((p, a))), \
             patch("launcher.core.applier.sys") as mock_sys:
            mock_sys.executable = str(tmp_path / "old_launcher.AppImage")
            mock_sys.argv = ["launcher"]
            _apply_linux(installer)

        # os.replace destination and os.execv path must be the same
        _, replace_dest = replace_calls[0]
        execv_path, _ = execv_calls[0]
        assert replace_dest == execv_path, (
            "The file swapped in by os.replace must be the same path launched by os.execv."
        )

    def test_linux_chmod_sets_all_exec_bits(self, tmp_path):
        """chmod must set S_IXUSR, S_IXGRP, and S_IXOTH — all three exec bits."""
        from launcher.core.applier import _apply_linux
        installer = tmp_path / "launcher.AppImage"
        installer.write_bytes(b"x")
        chmod_calls = []

        def fake_chmod(mode):
            chmod_calls.append(mode)

        with patch.object(Path, "chmod", side_effect=fake_chmod), \
             patch("launcher.core.applier.os.replace"), \
             patch("launcher.core.applier.os.execv"), \
             patch("launcher.core.applier.sys") as mock_sys:
            mock_sys.executable = str(tmp_path / "launcher")
            mock_sys.argv = ["launcher"]
            _apply_linux(installer)

        assert len(chmod_calls) == 1
        mode = chmod_calls[0]
        assert mode & stat.S_IXUSR, "S_IXUSR (user exec) must be set"
        assert mode & stat.S_IXGRP, "S_IXGRP (group exec) must be set"
        assert mode & stat.S_IXOTH, "S_IXOTH (other exec) must be set"


# ---------------------------------------------------------------------------
# GUI re-entrancy edge cases
# ---------------------------------------------------------------------------

class TestGUIReentrancy:
    """Re-entrancy and UI state management tests."""

    def _make_app(self):
        """Instantiate App with all external calls mocked (shared helper)."""
        for key in list(sys.modules.keys()):
            if key.startswith("launcher.gui") or key.startswith("launcher.core"):
                del sys.modules[key]
        from launcher.gui.app import App
        with patch("launcher.gui.app.threading.Thread"):
            app = App()
        return app

    def test_install_button_hidden_on_startup(self):
        """Download & Install button must be hidden on startup (no update detected yet)."""
        app = self._make_app()
        app.download_install_button.grid_remove.assert_called()

    def test_install_button_shows_only_when_update_available(self):
        """Install button must not be visible when update_available is False."""
        app = self._make_app()
        # Reset call counts
        app.download_install_button.grid_remove.reset_mock()
        app.download_install_button.grid.reset_mock()

        app._apply_update_result(False, "0.0.0", manual=False)
        app.download_install_button.grid_remove.assert_called()
        app.download_install_button.grid.assert_not_called()

    def test_on_install_update_disables_button_before_thread(self):
        """Button must be disabled synchronously before the download thread starts."""
        app = self._make_app()
        app._latest_version = "1.2.3"
        configure_calls = []

        original_configure = app.download_install_button.configure.side_effect

        def track_configure(*a, **kw):
            configure_calls.append(kw)

        app.download_install_button.configure.side_effect = track_configure

        with patch("launcher.gui.app.threading.Thread") as mock_thread:
            app._on_install_update()

        # First configure call (button disable) must have state="disabled"
        assert len(configure_calls) >= 1
        first_call = configure_calls[0]
        assert first_call.get("state") == "disabled", (
            f"Button must be disabled before thread starts; got {first_call!r}"
        )

    def test_on_install_error_restores_to_normal_state(self):
        """_on_install_error must restore button text to the standard label."""
        app = self._make_app()
        with patch("launcher.gui.app.messagebox.showerror"):
            app._on_install_error("Network timeout")

        configure_calls = app.download_install_button.configure.call_args_list
        assert any(
            call.kwargs.get("state") == "normal"
            for call in configure_calls
        ), "Button must be restored to state='normal' after install error."
        assert any(
            "Install" in str(call.kwargs.get("text", ""))
            for call in configure_calls
        ), "Button text must be restored to Install label after error."

    def test_apply_update_result_updates_latest_version_tracking(self):
        """_latest_version must be updated when a new update version is reported."""
        app = self._make_app()
        app._apply_update_result(True, "2.5.0")
        assert app._latest_version == "2.5.0", (
            "_latest_version must be updated so _on_install_update uses the correct version."
        )

    def test_apply_update_result_does_not_update_version_when_up_to_date(self):
        """_latest_version must NOT be updated when no update is available."""
        app = self._make_app()
        app._latest_version = "1.0.0"
        app._apply_update_result(False, "0.9.0", manual=True)
        # Version should remain at 1.0.0, not be changed to 0.9.0
        assert app._latest_version == "1.0.0", (
            "_latest_version must not be overwritten when update_available=False."
        )
