"""Tests for FIX-085: python-path.txt startup validation and auto-recovery.

Covers ensure_python_path_valid() in shim_config.py and the App startup
integration that warns the user when recovery fails.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app_with_mocked_tk(monkeypatch) -> "type":
    """Return the App class with all GUI/tk dependencies stubbed out."""
    # Stub out every module that would create real windows or do I/O.
    fake_ctk = MagicMock()
    fake_ctk.CTk.return_value = MagicMock()
    monkeypatch.setitem(sys.modules, "customtkinter", fake_ctk)
    monkeypatch.setitem(sys.modules, "ctk", fake_ctk)

    import importlib
    import launcher.gui.app as app_mod
    importlib.reload(app_mod)
    return app_mod.App


# ---------------------------------------------------------------------------
# Unit tests for ensure_python_path_valid()
# ---------------------------------------------------------------------------

class TestEnsurePythonPathValid:
    """Tests for shim_config.ensure_python_path_valid()."""

    def test_valid_path_returns_true(self, tmp_path):
        """Returns True immediately when python-path.txt points to an existing file."""
        from launcher.core import shim_config

        python_exe = tmp_path / "python.exe"
        python_exe.write_text("fake", encoding="utf-8")
        config = tmp_path / "python-path.txt"
        config.write_text(str(python_exe), encoding="utf-8")

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
        ):
            result = shim_config.ensure_python_path_valid()

        assert result is True

    def test_missing_file_auto_recovers(self, tmp_path):
        """Auto-recovers when python-path.txt does not exist."""
        from launcher.core import shim_config

        config = tmp_path / "python-path.txt"
        # config does NOT exist
        bundled_python = tmp_path / "python-embed" / "python.exe"
        bundled_python.parent.mkdir(parents=True)
        bundled_python.write_text("fake", encoding="utf-8")

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
            patch.object(shim_config, "_find_bundled_python_for_recovery", return_value=bundled_python),
        ):
            result = shim_config.ensure_python_path_valid()

        assert result is True
        # The file must now exist and contain the recovered path.
        assert config.read_text(encoding="utf-8").strip() == str(bundled_python)

    def test_empty_file_auto_recovers(self, tmp_path):
        """Auto-recovers when python-path.txt exists but is empty."""
        from launcher.core import shim_config

        config = tmp_path / "python-path.txt"
        config.write_text("", encoding="utf-8")
        bundled_python = tmp_path / "python-embed" / "python.exe"
        bundled_python.parent.mkdir(parents=True)
        bundled_python.write_text("fake", encoding="utf-8")

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
            patch.object(shim_config, "_find_bundled_python_for_recovery", return_value=bundled_python),
        ):
            result = shim_config.ensure_python_path_valid()

        assert result is True
        assert config.read_text(encoding="utf-8").strip() == str(bundled_python)

    def test_invalid_path_auto_recovers(self, tmp_path):
        """Auto-recovers when python-path.txt points to a non-existent executable."""
        from launcher.core import shim_config

        config = tmp_path / "python-path.txt"
        config.write_text(str(tmp_path / "nonexistent" / "python.exe"), encoding="utf-8")
        bundled_python = tmp_path / "python-embed" / "python.exe"
        bundled_python.parent.mkdir(parents=True)
        bundled_python.write_text("fake", encoding="utf-8")

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
            patch.object(shim_config, "_find_bundled_python_for_recovery", return_value=bundled_python),
        ):
            result = shim_config.ensure_python_path_valid()

        assert result is True
        assert config.read_text(encoding="utf-8").strip() == str(bundled_python)

    def test_no_bundled_python_returns_false(self, tmp_path):
        """Returns False when auto-recovery also fails (no bundled Python found)."""
        from launcher.core import shim_config

        config = tmp_path / "python-path.txt"
        # config absent — also no bundled Python
        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
            patch.object(shim_config, "_find_bundled_python_for_recovery", return_value=None),
        ):
            result = shim_config.ensure_python_path_valid()

        assert result is False

    def test_valid_path_does_not_overwrite(self, tmp_path):
        """Leaves python-path.txt unchanged when the path is already valid."""
        from launcher.core import shim_config

        python_exe = tmp_path / "python.exe"
        python_exe.write_text("fake", encoding="utf-8")
        config = tmp_path / "python-path.txt"
        config.write_text(str(python_exe), encoding="utf-8")
        orig_mtime = config.stat().st_mtime

        with (
            patch.object(shim_config, "get_python_path_config", return_value=config),
        ):
            shim_config.ensure_python_path_valid()

        # File must not have been rewritten.
        assert config.stat().st_mtime == orig_mtime


# ---------------------------------------------------------------------------
# Integration tests — App startup calls ensure_python_path_valid
# ---------------------------------------------------------------------------

class TestAppStartupValidation:
    """Verify that App.__init__ invokes ensure_python_path_valid (FIX-085)."""

    def _build_app(self, monkeypatch, ensure_return: bool) -> MagicMock:
        """Construct an App instance with all side effects mocked.

        Returns the mock for messagebox so callers can inspect calls.
        """
        import importlib
        import launcher.gui.app as app_mod

        fake_ctk = MagicMock()
        win = MagicMock()
        fake_ctk.CTk.return_value = win
        fake_ctk.BooleanVar.return_value = MagicMock()
        fake_ctk.StringVar.return_value = MagicMock()

        mock_mb = MagicMock()
        mock_find_vscode = MagicMock(return_value=None)

        with (
            patch.dict(sys.modules, {"customtkinter": fake_ctk}),
            patch.object(app_mod, "ctk", fake_ctk),
            patch.object(app_mod, "messagebox", mock_mb),
            patch.object(app_mod, "find_vscode", mock_find_vscode),
            patch.object(app_mod, "ensure_python_path_valid", return_value=ensure_return),
            patch.object(app_mod, "check_for_update", return_value=(False, "0.0.0")),
            patch.object(app_mod, "list_templates", return_value=[]),
            patch.object(app_mod, "is_template_ready", return_value=True),
            patch.object(app_mod, "get_setting", return_value=True),
            patch("threading.Thread"),
        ):
            app = app_mod.App()

        return mock_mb, app_mod

    def test_app_startup_calls_validation(self, monkeypatch):
        """App.__init__ must call ensure_python_path_valid()."""
        import importlib
        import launcher.gui.app as app_mod

        fake_ctk = MagicMock()
        win = MagicMock()
        fake_ctk.CTk.return_value = win
        fake_ctk.BooleanVar.return_value = MagicMock()
        fake_ctk.StringVar.return_value = MagicMock()

        validation_called = []
        def fake_ensure():
            validation_called.append(True)
            return True

        with (
            patch.dict(sys.modules, {"customtkinter": fake_ctk}),
            patch.object(app_mod, "ctk", fake_ctk),
            patch.object(app_mod, "messagebox", MagicMock()),
            patch.object(app_mod, "find_vscode", return_value=None),
            patch.object(app_mod, "ensure_python_path_valid", side_effect=fake_ensure),
            patch.object(app_mod, "check_for_update", return_value=(False, "0.0.0")),
            patch.object(app_mod, "list_templates", return_value=[]),
            patch.object(app_mod, "is_template_ready", return_value=True),
            patch.object(app_mod, "get_setting", return_value=True),
            patch("threading.Thread"),
        ):
            app_mod.App()

        assert len(validation_called) == 1, "ensure_python_path_valid() was not called at startup"

    def test_app_startup_warns_on_invalid_path(self, monkeypatch):
        """App.__init__ shows a warning dialog when ensure_python_path_valid returns False."""
        import launcher.gui.app as app_mod

        fake_ctk = MagicMock()
        win = MagicMock()
        fake_ctk.CTk.return_value = win
        fake_ctk.BooleanVar.return_value = MagicMock()
        fake_ctk.StringVar.return_value = MagicMock()

        mock_mb = MagicMock()

        with (
            patch.dict(sys.modules, {"customtkinter": fake_ctk}),
            patch.object(app_mod, "ctk", fake_ctk),
            patch.object(app_mod, "messagebox", mock_mb),
            patch.object(app_mod, "find_vscode", return_value=None),
            patch.object(app_mod, "ensure_python_path_valid", return_value=False),
            patch.object(app_mod, "check_for_update", return_value=(False, "0.0.0")),
            patch.object(app_mod, "list_templates", return_value=[]),
            patch.object(app_mod, "is_template_ready", return_value=True),
            patch.object(app_mod, "get_setting", return_value=True),
            patch("threading.Thread"),
        ):
            app_mod.App()

        mock_mb.showwarning.assert_called_once()
        title, msg = mock_mb.showwarning.call_args[0]
        assert "Python Runtime" in title

    def test_app_startup_no_warning_on_valid_path(self, monkeypatch):
        """App.__init__ does NOT show any warning when ensure_python_path_valid returns True."""
        import launcher.gui.app as app_mod

        fake_ctk = MagicMock()
        win = MagicMock()
        fake_ctk.CTk.return_value = win
        fake_ctk.BooleanVar.return_value = MagicMock()
        fake_ctk.StringVar.return_value = MagicMock()

        mock_mb = MagicMock()

        with (
            patch.dict(sys.modules, {"customtkinter": fake_ctk}),
            patch.object(app_mod, "ctk", fake_ctk),
            patch.object(app_mod, "messagebox", mock_mb),
            patch.object(app_mod, "find_vscode", return_value=None),
            patch.object(app_mod, "ensure_python_path_valid", return_value=True),
            patch.object(app_mod, "check_for_update", return_value=(False, "0.0.0")),
            patch.object(app_mod, "list_templates", return_value=[]),
            patch.object(app_mod, "is_template_ready", return_value=True),
            patch.object(app_mod, "get_setting", return_value=True),
            patch("threading.Thread"),
        ):
            app_mod.App()

        mock_mb.showwarning.assert_not_called()


# ---------------------------------------------------------------------------
# Structural test — Inno Setup script contains correct path-writing logic
# ---------------------------------------------------------------------------

class TestInnoSetupScript:
    """Verify setup.iss contains the correct python-path.txt writing logic (FIX-085)."""

    @pytest.fixture(scope="class")
    def iss_content(self) -> str:
        repo_root = Path(__file__).resolve().parents[2]
        iss_path = repo_root / "src" / "installer" / "windows" / "setup.iss"
        return iss_path.read_text(encoding="utf-8")

    def test_inno_setup_writes_correct_path_format(self, iss_content):
        """setup.iss writes {app}\\python-embed\\python.exe to python-path.txt."""
        assert r"{app}\python-embed\python.exe" in iss_content

    def test_inno_setup_has_post_install_verification_log(self, iss_content):
        """setup.iss logs a warning when python-embed/python.exe is not found (FIX-085)."""
        assert "FIX-085" in iss_content
        assert "FileExists(PythonPath)" in iss_content

    def test_inno_setup_uses_overwrite_mode(self, iss_content):
        """SaveStringToFile is called with Append=False to overwrite on update."""
        # The third argument must be False (overwrite, not append).
        assert "SaveStringToFile(ConfigFile, PythonPath, False)" in iss_content

    def test_inno_setup_creates_config_dir(self, iss_content):
        """setup.iss creates TurbulenceSolutions config directory if missing."""
        assert "CreateDir(ConfigDir)" in iss_content
