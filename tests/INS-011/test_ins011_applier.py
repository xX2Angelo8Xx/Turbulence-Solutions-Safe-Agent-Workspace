"""Tests for INS-011: Update Apply and Restart (applier.py)."""

from __future__ import annotations

import os
import stat
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_temp_file(suffix: str = ".exe") -> Path:
    """Return a Path to a real temporary file (auto-cleaned up by pytest)."""
    fd, name = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return Path(name)


# ---------------------------------------------------------------------------
# TestValidateInstallerPath
# ---------------------------------------------------------------------------

class TestValidateInstallerPath:
    """_validate_installer_path must accept valid files and reject anything else."""

    def test_valid_file_passes(self, tmp_path):
        from launcher.core.applier import _validate_installer_path
        installer = tmp_path / "setup.exe"
        installer.write_bytes(b"dummy")
        _validate_installer_path(installer)  # must not raise

    def test_missing_file_raises_file_not_found(self, tmp_path):
        from launcher.core.applier import _validate_installer_path
        missing = tmp_path / "nonexistent.exe"
        with pytest.raises(FileNotFoundError):
            _validate_installer_path(missing)

    def test_directory_raises_value_error(self, tmp_path):
        from launcher.core.applier import _validate_installer_path
        with pytest.raises(ValueError):
            _validate_installer_path(tmp_path)


# ---------------------------------------------------------------------------
# TestPlatformDispatch
# ---------------------------------------------------------------------------

class TestPlatformDispatch:
    """apply_update must dispatch to the correct platform handler."""

    def test_windows_dispatches_to_apply_windows(self, tmp_path):
        from launcher.core import applier
        installer = tmp_path / "setup.exe"
        installer.write_bytes(b"x")
        with patch("launcher.core.applier.sys") as mock_sys, \
             patch("launcher.core.applier._apply_windows") as mock_win:
            mock_sys.platform = "win32"
            applier.apply_update(installer)
            mock_win.assert_called_once_with(installer)

    def test_macos_dispatches_to_apply_macos(self, tmp_path):
        from launcher.core import applier
        installer = tmp_path / "app.dmg"
        installer.write_bytes(b"x")
        with patch("launcher.core.applier.sys") as mock_sys, \
             patch("launcher.core.applier._apply_macos") as mock_mac:
            mock_sys.platform = "darwin"
            applier.apply_update(installer)
            mock_mac.assert_called_once_with(installer)

    def test_linux_dispatches_to_apply_linux(self, tmp_path):
        from launcher.core import applier
        installer = tmp_path / "launcher.AppImage"
        installer.write_bytes(b"x")
        with patch("launcher.core.applier.sys") as mock_sys, \
             patch("launcher.core.applier._apply_linux") as mock_linux:
            mock_sys.platform = "linux"
            applier.apply_update(installer)
            mock_linux.assert_called_once_with(installer)

    def test_unsupported_platform_raises(self, tmp_path):
        from launcher.core import applier
        installer = tmp_path / "setup.exe"
        installer.write_bytes(b"x")
        with patch("launcher.core.applier.sys") as mock_sys:
            mock_sys.platform = "freebsd14"
            with pytest.raises(RuntimeError, match="Unsupported platform"):
                applier.apply_update(installer)

    def test_missing_file_raises_before_dispatch(self, tmp_path):
        from launcher.core import applier
        missing = tmp_path / "missing.exe"
        with patch("launcher.core.applier._apply_windows") as mock_win:
            with pytest.raises(FileNotFoundError):
                applier.apply_update(missing)
            mock_win.assert_not_called()


# ---------------------------------------------------------------------------
# TestWindowsApply
# ---------------------------------------------------------------------------

class TestWindowsApply:
    """_apply_windows must launch the installer as a list-arg Popen and exit."""

    def _run_windows_apply(self, tmp_path):
        """Helper: create a dummy installer, run _apply_windows, capture calls."""
        from launcher.core.applier import _apply_windows
        installer = tmp_path / "setup.exe"
        installer.write_bytes(b"x")
        popen_calls = []

        def fake_popen(args, **kwargs):
            popen_calls.append({"args": args, "kwargs": kwargs})

        with patch("launcher.core.applier.subprocess.Popen", side_effect=fake_popen), \
             patch("launcher.core.applier.os._exit") as mock_os_exit, \
             patch("launcher.core.applier.sys.exit") as mock_exit:
            _apply_windows(installer)

        return popen_calls, mock_os_exit

    def test_windows_popen_called_with_list_args(self, tmp_path):
        popen_calls, _ = self._run_windows_apply(tmp_path)
        assert len(popen_calls) == 1
        assert isinstance(popen_calls[0]["args"], list)

    def test_windows_popen_no_shell_true(self, tmp_path):
        popen_calls, _ = self._run_windows_apply(tmp_path)
        assert popen_calls[0]["kwargs"].get("shell") is not True

    def test_windows_passes_silent_flag(self, tmp_path):
        popen_calls, _ = self._run_windows_apply(tmp_path)
        assert "/SILENT" in popen_calls[0]["args"]

    def test_windows_passes_close_applications_flag(self, tmp_path):
        popen_calls, _ = self._run_windows_apply(tmp_path)
        assert "/CLOSEAPPLICATIONS" in popen_calls[0]["args"]

    def test_windows_installer_path_first_arg(self, tmp_path):
        installer = tmp_path / "setup.exe"
        installer.write_bytes(b"x")
        from launcher.core.applier import _apply_windows
        captured = {}

        def fake_popen(args, **kw):
            captured["args"] = args

        with patch("launcher.core.applier.subprocess.Popen", side_effect=fake_popen), \
             patch("launcher.core.applier.os._exit"), \
             patch("launcher.core.applier.sys.exit"):
            _apply_windows(installer)
        assert captured["args"][0] == str(installer)

    def test_windows_exits_after_popen(self, tmp_path):
        _, mock_exit = self._run_windows_apply(tmp_path)
        mock_exit.assert_called_once_with(0)


# ---------------------------------------------------------------------------
# TestMacosApply
# ---------------------------------------------------------------------------

class TestMacosApply:
    """_apply_macos must mount, copy, unmount, and exit."""

    def _make_fake_mount(self, tmp_path: Path, app_name: str = "App.app") -> Path:
        """Create a fake mounted DMG layout with a .app directory inside."""
        mount = tmp_path / "mount"
        mount.mkdir()
        app_bundle = mount / app_name
        app_bundle.mkdir()
        return mount

    def _run_macos_apply(self, tmp_path: Path, attach_rc: int = 0):
        """Run _apply_macos with subprocess.run mocked."""
        from launcher.core.applier import _apply_macos
        installer = tmp_path / "app.dmg"
        installer.write_bytes(b"x")
        mount_point = self._make_fake_mount(tmp_path)
        run_calls: list[dict] = []

        def fake_run(args, **kwargs):
            run_calls.append({"args": args, "kwargs": kwargs})
            result = MagicMock()
            # hdiutil attach gets the requested rc; everything else succeeds.
            if "attach" in args:
                result.returncode = attach_rc
            else:
                result.returncode = 0
            result.stderr = b""
            return result

        with patch("launcher.core.applier.tempfile.mkdtemp", return_value=str(mount_point)), \
             patch("launcher.core.applier.subprocess.run", side_effect=fake_run), \
             patch("launcher.core.applier.sys.exit") as mock_exit:
            if attach_rc != 0:
                with pytest.raises(RuntimeError):
                    _apply_macos(installer)
                return run_calls, None
            _apply_macos(installer)
        return run_calls, mock_exit

    def test_macos_hdiutil_attach_called(self, tmp_path):
        run_calls, _ = self._run_macos_apply(tmp_path)
        attach_calls = [c for c in run_calls if "attach" in c["args"]]
        assert len(attach_calls) == 1

    def test_macos_hdiutil_attach_no_shell(self, tmp_path):
        run_calls, _ = self._run_macos_apply(tmp_path)
        attach = next(c for c in run_calls if "attach" in c["args"])
        assert attach["kwargs"].get("shell") is not True

    def test_macos_hdiutil_detach_called(self, tmp_path):
        run_calls, _ = self._run_macos_apply(tmp_path)
        detach_calls = [c for c in run_calls if "detach" in c["args"]]
        assert len(detach_calls) == 1

    def test_macos_rsync_copies_app(self, tmp_path):
        run_calls, _ = self._run_macos_apply(tmp_path)
        rsync_calls = [c for c in run_calls if c["args"][0] == "rsync"]
        assert len(rsync_calls) == 1
        # Destination must be under /Applications/
        dest_arg = rsync_calls[0]["args"][-1]
        assert dest_arg.startswith("/Applications/")

    def test_macos_exits_after_install(self, tmp_path):
        _, mock_exit = self._run_macos_apply(tmp_path)
        mock_exit.assert_called_once_with(0)

    def test_macos_attach_failure_raises_runtime_error(self, tmp_path):
        """hdiutil attach failure must raise RuntimeError before any copy."""
        run_calls, _ = self._run_macos_apply(tmp_path, attach_rc=1)
        rsync_calls = [c for c in run_calls if c["args"][0] == "rsync"]
        assert len(rsync_calls) == 0

    def test_macos_detach_called_even_on_copy_error(self, tmp_path):
        """hdiutil detach must always run, even if rsync raises."""
        from launcher.core.applier import _apply_macos
        installer = tmp_path / "app.dmg"
        installer.write_bytes(b"x")
        mount_point = self._make_fake_mount(tmp_path)
        run_calls: list[dict] = []

        def fake_run(args, **kwargs):
            run_calls.append({"args": args, "kwargs": kwargs})
            result = MagicMock()
            result.returncode = 0
            result.stderr = b""
            if args[0] == "rsync":
                import subprocess
                raise subprocess.CalledProcessError(1, args)
            return result

        with patch("launcher.core.applier.tempfile.mkdtemp", return_value=str(mount_point)), \
             patch("launcher.core.applier.subprocess.run", side_effect=fake_run), \
             patch("launcher.core.applier.sys.exit"):
            with pytest.raises(Exception):
                _apply_macos(installer)

        detach_calls = [c for c in run_calls if "detach" in c["args"]]
        assert len(detach_calls) == 1


# ---------------------------------------------------------------------------
# TestFindAppBundle
# ---------------------------------------------------------------------------

class TestFindAppBundle:
    """_find_app_bundle must locate .app directories and reject anything else."""

    def test_finds_app_bundle_in_directory(self, tmp_path):
        from launcher.core.applier import _find_app_bundle
        bundle = tmp_path / "Launcher.app"
        bundle.mkdir()
        result = _find_app_bundle(tmp_path)
        assert result == bundle

    def test_raises_if_no_app_bundle(self, tmp_path):
        from launcher.core.applier import _find_app_bundle
        (tmp_path / "readme.txt").write_text("hello")
        with pytest.raises(RuntimeError, match="No .app bundle found"):
            _find_app_bundle(tmp_path)

    def test_ignores_app_file_not_directory(self, tmp_path):
        from launcher.core.applier import _find_app_bundle
        # A *file* ending in .app should NOT be selected.
        fake = tmp_path / "not_a_bundle.app"
        fake.write_bytes(b"x")
        with pytest.raises(RuntimeError):
            _find_app_bundle(tmp_path)


# ---------------------------------------------------------------------------
# TestLinuxApply
# ---------------------------------------------------------------------------

class TestLinuxApply:
    """_apply_linux must chmod, swap, and execv the new AppImage."""

    def _run_linux_apply(self, tmp_path: Path, replace_side_effect=None):
        from launcher.core.applier import _apply_linux
        installer = tmp_path / "launcher.AppImage"
        installer.write_bytes(b"x")
        chmod_calls: list = []
        replace_calls: list = []
        execv_calls: list = []

        # patch.object on a class method binds the mock to the instance, so the
        # side_effect receives only the non-self arguments: (mode,).
        def fake_chmod(mode):
            chmod_calls.append((installer, mode))

        with patch.object(Path, "chmod", side_effect=fake_chmod), \
             patch("launcher.core.applier.os.replace",
                   side_effect=replace_side_effect or
                   (lambda src, dst: replace_calls.append((src, dst)))), \
             patch("launcher.core.applier.os.execv",
                   side_effect=lambda path, args: execv_calls.append((path, args))), \
             patch("launcher.core.applier.sys") as mock_sys:
            mock_sys.executable = str(tmp_path / "python")
            mock_sys.argv = ["launcher"]
            if replace_side_effect:
                with pytest.raises((PermissionError, RuntimeError)):
                    _apply_linux(installer)
            else:
                _apply_linux(installer)

        return chmod_calls, replace_calls, execv_calls

    def test_linux_makes_appimage_executable(self, tmp_path):
        chmod_calls, _, _ = self._run_linux_apply(tmp_path)
        assert len(chmod_calls) == 1
        _, applied_mode = chmod_calls[0]
        # exec bits for user, group, other must be set
        assert applied_mode & stat.S_IXUSR
        assert applied_mode & stat.S_IXGRP
        assert applied_mode & stat.S_IXOTH

    def test_linux_os_replace_called(self, tmp_path):
        _, replace_calls, _ = self._run_linux_apply(tmp_path)
        assert len(replace_calls) == 1

    def test_linux_execv_called(self, tmp_path):
        _, _, execv_calls = self._run_linux_apply(tmp_path)
        assert len(execv_calls) == 1

    def test_linux_permission_error_raises_runtime_error(self, tmp_path):
        from launcher.core.applier import _apply_linux
        installer = tmp_path / "launcher.AppImage"
        installer.write_bytes(b"x")

        def _perm_error(src, dst):
            raise PermissionError("denied")

        with patch.object(Path, "chmod"), \
             patch("launcher.core.applier.os.replace", side_effect=_perm_error), \
             patch("launcher.core.applier.sys") as mock_sys:
            mock_sys.executable = str(tmp_path / "python")
            mock_sys.argv = ["launcher"]
            with pytest.raises(RuntimeError, match="Permission denied"):
                _apply_linux(installer)

    def test_linux_installer_is_source_in_replace(self, tmp_path):
        _, replace_calls, _ = self._run_linux_apply(tmp_path)
        src, _ = replace_calls[0]
        assert str(tmp_path / "launcher.AppImage") == src

    def test_linux_execv_target_is_current_executable(self, tmp_path):
        _, _, execv_calls = self._run_linux_apply(tmp_path)
        target, _ = execv_calls[0]
        assert target == str(tmp_path / "python")


# ---------------------------------------------------------------------------
# TestNoShellTrue  (security requirement from security-rules.md)
# ---------------------------------------------------------------------------

class TestNoShellTrue:
    """Subprocess calls must NEVER use shell=True."""

    def test_windows_subprocess_no_shell_true(self, tmp_path):
        from launcher.core.applier import _apply_windows
        installer = tmp_path / "setup.exe"
        installer.write_bytes(b"x")
        captured_kwargs = {}

        def fake_popen(args, **kwargs):
            captured_kwargs.update(kwargs)

        with patch("launcher.core.applier.subprocess.Popen", side_effect=fake_popen), \
             patch("launcher.core.applier.os._exit"), \
             patch("launcher.core.applier.sys.exit"):
            _apply_windows(installer)

        assert captured_kwargs.get("shell") is not True

    def test_macos_hdiutil_attach_no_shell_true(self, tmp_path):
        from launcher.core.applier import _apply_macos
        installer = tmp_path / "app.dmg"
        installer.write_bytes(b"x")
        mount_point = tmp_path / "mnt"
        mount_point.mkdir()
        (mount_point / "Launcher.app").mkdir()
        shell_violations = []

        def fake_run(args, **kwargs):
            if kwargs.get("shell") is True:
                shell_violations.append(args)
            result = MagicMock()
            result.returncode = 0
            result.stderr = b""
            return result

        with patch("launcher.core.applier.tempfile.mkdtemp",
                   return_value=str(mount_point)), \
             patch("launcher.core.applier.subprocess.run", side_effect=fake_run), \
             patch("launcher.core.applier.sys.exit"):
            _apply_macos(installer)

        assert shell_violations == [], (
            f"shell=True found in subprocess calls: {shell_violations}"
        )


# ---------------------------------------------------------------------------
# TestGUIIntegration
# ---------------------------------------------------------------------------

class TestGUIIntegration:
    """Verify that the GUI app.py changes for INS-011 are wired up correctly."""

    def _make_app(self):
        """Instantiate App with all external calls mocked."""
        import sys
        # Remove cached module to allow re-import with fresh mocks.
        for key in list(sys.modules.keys()):
            if key.startswith("launcher.gui") or key.startswith("launcher.core"):
                del sys.modules[key]
        import customtkinter as ctk
        _CTK_MOCK = sys.modules["customtkinter"]
        from launcher.gui.app import App
        with patch("launcher.gui.app.threading.Thread"):
            app = App()
        return app

    def test_download_install_button_exists(self):
        app = self._make_app()
        assert hasattr(app, "download_install_button")

    def test_latest_version_attribute_exists(self):
        app = self._make_app()
        assert hasattr(app, "_latest_version")

    def test_apply_update_result_shows_install_button_when_update_available(self):
        app = self._make_app()
        app._apply_update_result(True, "1.2.3")
        assert app._latest_version == "1.2.3"
        app.download_install_button.grid.assert_called()

    def test_apply_update_result_hides_install_button_when_up_to_date(self):
        app = self._make_app()
        app._apply_update_result(False, "0.1.0", manual=True)
        app.download_install_button.grid_remove.assert_called()

    def test_on_install_update_disables_button(self):
        app = self._make_app()
        app._latest_version = "1.2.3"

        with patch("launcher.gui.app.threading.Thread") as mock_thread:
            app._on_install_update()
        app.download_install_button.configure.assert_called()

    def test_on_install_error_restores_button(self):
        app = self._make_app()
        with patch("launcher.gui.app.messagebox.showerror"):
            app._on_install_error("Something broke")
        app.download_install_button.configure.assert_called()

    def test_download_update_imported_in_app(self):
        import launcher.gui.app as app_module
        assert hasattr(app_module, "download_update")

    def test_apply_update_imported_in_app(self):
        import launcher.gui.app as app_module
        assert hasattr(app_module, "apply_update")
