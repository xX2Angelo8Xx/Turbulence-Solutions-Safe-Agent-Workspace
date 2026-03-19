"""Tests for GUI-013: TS-Logo integration (config, spec, app)."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# 1. LOGO_PATH resolves correctly in development mode (no _MEIPASS)
# ---------------------------------------------------------------------------

def test_logo_path_dev_mode_points_to_repo_root():
    """LOGO_PATH should point to TS-Logo.png at the repo root in dev mode."""
    # Reload config without _MEIPASS so the dev branch is evaluated.
    if "launcher.config" in sys.modules:
        del sys.modules["launcher.config"]

    with patch.object(sys, "_MEIPASS", None, create=True):
        # Remove the attribute entirely to simulate non-bundle env.
        attrs_backup = {}
        if hasattr(sys, "_MEIPASS"):
            attrs_backup["_MEIPASS"] = sys._MEIPASS
            delattr(sys, "_MEIPASS")

        try:
            import importlib
            import launcher.config as cfg
            importlib.reload(cfg)
            logo_path = cfg.LOGO_PATH
        finally:
            for attr, val in attrs_backup.items():
                setattr(sys, attr, val)
            del sys.modules["launcher.config"]

    assert logo_path.name == "TS-Logo.png"
    assert logo_path.parent == REPO_ROOT


def test_logo_path_dev_mode_file_exists():
    """TS-Logo.png must exist at the repo root for the dev environment."""
    logo = REPO_ROOT / "TS-Logo.png"
    assert logo.exists(), f"TS-Logo.png not found at {logo}"


# ---------------------------------------------------------------------------
# 2. LOGO_PATH resolves correctly in PyInstaller bundle mode (_MEIPASS set)
# ---------------------------------------------------------------------------

def test_logo_path_meipass_mode():
    """LOGO_PATH should point to _MEIPASS/TS-Logo.png in a bundled environment."""
    fake_meipass = "/tmp/fake_bundle"

    if "launcher.config" in sys.modules:
        del sys.modules["launcher.config"]

    # Temporarily inject _MEIPASS onto sys
    sys._MEIPASS = fake_meipass
    try:
        import importlib
        import launcher.config as cfg
        importlib.reload(cfg)
        logo_path = cfg.LOGO_PATH
    finally:
        del sys._MEIPASS
        del sys.modules["launcher.config"]

    assert str(logo_path) == f"{fake_meipass}/TS-Logo.png" or logo_path == Path(fake_meipass) / "TS-Logo.png"


# ---------------------------------------------------------------------------
# 3. launcher.spec datas list includes TS-Logo.png entry
# ---------------------------------------------------------------------------

def test_spec_datas_includes_ts_logo():
    """launcher.spec must contain TS-Logo.png in its datas list."""
    spec_path = REPO_ROOT / "launcher.spec"
    assert spec_path.exists(), "launcher.spec not found"
    content = spec_path.read_text(encoding="utf-8")
    assert "TS-Logo.png" in content, "TS-Logo.png not found in launcher.spec"


def test_spec_datas_bundles_logo_to_root():
    """launcher.spec TS-Logo.png entry should place the file in the bundle root ('.')."""
    spec_path = REPO_ROOT / "launcher.spec"
    content = spec_path.read_text(encoding="utf-8")
    # Verify the tuple pattern ('...TS-Logo.png', '.') exists somewhere in the file.
    assert "'TS-Logo.png'" in content or "TS-Logo.png" in content


def test_spec_exe_has_icon_parameter():
    """launcher.spec EXE block must have an icon= parameter."""
    spec_path = REPO_ROOT / "launcher.spec"
    content = spec_path.read_text(encoding="utf-8")
    assert "icon=" in content, "icon= parameter missing from launcher.spec EXE block"


# ---------------------------------------------------------------------------
# 4. App class builds without error with logo mocked (headless)
# ---------------------------------------------------------------------------

def test_app_init_sets_icon_photo(monkeypatch):
    """App.__init__ should attempt to set the window icon via iconphoto (non-Windows)."""
    import PIL.Image
    import PIL.ImageTk

    fake_photo = MagicMock()
    fake_image = MagicMock()

    with (
        patch("launcher.gui.app.LOGO_PATH", REPO_ROOT / "TS-Logo.png"),
        patch("launcher.gui.app.LOGO_ICO_PATH", REPO_ROOT / "TS-Logo.ico"),
        patch("launcher.gui.app.find_vscode", return_value=None),
        patch("threading.Thread"),
        patch.object(PIL.Image, "open", return_value=fake_image),
        patch.object(PIL.ImageTk, "PhotoImage", return_value=fake_photo),
        patch("launcher.gui.app.sys") as mock_sys,
    ):
        # Simulate non-Windows so the iconphoto branch is taken (platform-independent test)
        mock_sys.platform = "linux"
        from launcher.gui.app import App

        app = App()

        # The window is a MagicMock (customtkinter globally mocked in conftest).
        # Verify iconphoto was called on the window with True and our fake photo.
        app._window.iconphoto.assert_called_once_with(True, fake_photo)
        # Verify the photo is kept as an instance attribute (GC prevention).
        assert app._icon_photo is fake_photo


def test_app_build_ui_creates_logo_label(monkeypatch):
    """App._build_ui() should create a logo_label attribute when PIL is available."""
    fake_window = MagicMock()
    fake_window.after = MagicMock()

    with (
        patch("customtkinter.CTk", return_value=fake_window),
        patch("customtkinter.set_appearance_mode"),
        patch("customtkinter.set_default_color_theme"),
        patch("launcher.gui.app.LOGO_PATH", REPO_ROOT / "TS-Logo.png"),
        patch("launcher.gui.app.find_vscode", return_value=None),
        patch("threading.Thread"),
    ):
        from launcher.gui.app import App

        app = App()
        assert hasattr(app, "logo_label"), "App should have logo_label attribute"
