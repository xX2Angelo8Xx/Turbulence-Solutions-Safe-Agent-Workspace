"""Tester edge-case tests for GUI-013: TS-Logo integration.

These tests supplement the developer suite and cover:
  - LOGO_PATH type and import assertions
  - Graceful fallback when PIL is not installed
  - Graceful fallback when the logo file is absent
  - Grid row/column placement of the logo label
  - Pyproject.toml Pillow dependency bounds
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# 1. LOGO_PATH is a pathlib.Path instance
# ---------------------------------------------------------------------------

def test_logo_path_is_path_instance():
    """LOGO_PATH must be a pathlib.Path, not a plain string."""
    import launcher.config as cfg

    assert isinstance(cfg.LOGO_PATH, Path), (
        f"LOGO_PATH is {type(cfg.LOGO_PATH).__name__}, expected pathlib.Path"
    )


# ---------------------------------------------------------------------------
# 2. LOGO_PATH is referenced in app.py source
# ---------------------------------------------------------------------------

def test_logo_path_referenced_in_app_source():
    """app.py source must reference LOGO_PATH (imported from launcher.config)."""
    app_src = (REPO_ROOT / "src" / "launcher" / "gui" / "app.py").read_text(
        encoding="utf-8"
    )
    assert "LOGO_PATH" in app_src, "LOGO_PATH not found in app.py source"


# ---------------------------------------------------------------------------
# 3-4. Graceful fallback when PIL is unavailable (ImportError)
# ---------------------------------------------------------------------------

def test_build_ui_no_logo_label_when_pil_unavailable():
    """logo_label must NOT be created when PIL cannot be imported."""
    # Override all PIL-related entries in sys.modules with None to simulate
    # PIL not being installed.  patch.dict restores original values on exit.
    pil_shadow = {"PIL": None, "PIL.Image": None, "PIL.ImageTk": None}

    with (
        patch.dict(sys.modules, pil_shadow),
        patch("launcher.gui.app.LOGO_PATH", REPO_ROOT / "TS-Logo.png"),
        patch("launcher.gui.app.find_vscode", return_value=None),
        patch("threading.Thread"),
    ):
        from launcher.gui.app import App  # cached – no reimport

        app = App()
        assert not hasattr(app, "logo_label"), (
            "logo_label should not exist when PIL is unavailable"
        )


def test_init_no_icon_photo_when_pil_unavailable():
    """_icon_photo must NOT be set when PIL cannot be imported."""
    pil_shadow = {"PIL": None, "PIL.Image": None, "PIL.ImageTk": None}

    with (
        patch.dict(sys.modules, pil_shadow),
        patch("launcher.gui.app.LOGO_PATH", REPO_ROOT / "TS-Logo.png"),
        patch("launcher.gui.app.find_vscode", return_value=None),
        patch("threading.Thread"),
    ):
        from launcher.gui.app import App

        app = App()
        assert not hasattr(app, "_icon_photo"), (
            "_icon_photo should not exist when PIL is unavailable"
        )


# ---------------------------------------------------------------------------
# 5-6. Graceful fallback when the logo file is absent
# ---------------------------------------------------------------------------

def test_build_ui_no_logo_label_when_file_missing():
    """logo_label must NOT be created when LOGO_PATH points to a missing file.

    PIL.Image.open raises FileNotFoundError; the except block swallows it.
    """
    fake_path = REPO_ROOT / "does-not-exist-gui013-tester.png"
    assert not fake_path.exists(), "Pre-condition: test sentinel file must not exist"

    with (
        patch("launcher.gui.app.LOGO_PATH", fake_path),
        patch("launcher.gui.app.find_vscode", return_value=None),
        patch("threading.Thread"),
    ):
        from launcher.gui.app import App

        app = App()
        assert not hasattr(app, "logo_label"), (
            "logo_label should not exist when logo file is missing"
        )


def test_init_no_icon_photo_when_file_missing():
    """_icon_photo must NOT be set when LOGO_PATH points to a missing file."""
    fake_path = REPO_ROOT / "does-not-exist-gui013-tester.png"
    assert not fake_path.exists(), "Pre-condition: test sentinel file must not exist"

    with (
        patch("launcher.gui.app.LOGO_PATH", fake_path),
        patch("launcher.gui.app.find_vscode", return_value=None),
        patch("threading.Thread"),
    ):
        from launcher.gui.app import App

        app = App()
        assert not hasattr(app, "_icon_photo"), (
            "_icon_photo should not exist when logo file is missing"
        )


# ---------------------------------------------------------------------------
# 7. App.__init__ completes without raising when logo is missing
# ---------------------------------------------------------------------------

def test_app_does_not_raise_when_logo_file_absent():
    """App() must complete cleanly even when the logo file does not exist."""
    fake_path = REPO_ROOT / "does-not-exist-gui013-tester.png"

    with (
        patch("launcher.gui.app.LOGO_PATH", fake_path),
        patch("launcher.gui.app.find_vscode", return_value=None),
        patch("threading.Thread"),
    ):
        from launcher.gui.app import App

        try:
            app = App()
        except Exception as exc:  # pragma: no cover
            pytest.fail(f"App() raised unexpectedly with missing logo: {exc}")


# ---------------------------------------------------------------------------
# 8. Logo label placed at grid row 0, columnspan 3
# ---------------------------------------------------------------------------

def test_logo_label_placed_at_row_zero_columnspan_3():
    """logo_label.grid must be called with row=0 and columnspan=3.

    Since conftest mocks all customtkinter classes to the same MagicMock
    return value, we inspect call_args_list to find the specific call.
    """
    import PIL.Image

    fake_image = MagicMock()
    with (
        patch("launcher.gui.app.LOGO_PATH", REPO_ROOT / "TS-Logo.png"),
        patch("launcher.gui.app.find_vscode", return_value=None),
        patch("threading.Thread"),
        patch.object(PIL.Image, "open", return_value=fake_image),
    ):
        from launcher.gui.app import App

        app = App()

        assert hasattr(app, "logo_label"), "logo_label attribute must exist"
        all_grid_calls = app.logo_label.grid.call_args_list
        logo_calls = [
            c
            for c in all_grid_calls
            if c.kwargs.get("row") == 0 and c.kwargs.get("columnspan") == 3
        ]
        assert logo_calls, (
            "No grid(row=0, columnspan=3) call found among CTkLabel.grid calls. "
            f"All calls: {all_grid_calls}"
        )


# ---------------------------------------------------------------------------
# 9-10. Pillow dependency declared in pyproject.toml with version bounds
# ---------------------------------------------------------------------------

def test_pillow_in_pyproject_dependencies():
    """Pillow must be listed in pyproject.toml [project] dependencies."""
    data = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    deps = data.get("project", {}).get("dependencies", [])
    assert any("Pillow" in d or "pillow" in d.lower() for d in deps), (
        "Pillow not found in pyproject.toml [project] dependencies"
    )


def test_pillow_dependency_has_upper_version_bound():
    """Pillow must have an upper-version bound (<) to prevent silent breaking upgrades."""
    data = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    deps = data.get("project", {}).get("dependencies", [])
    pillow_dep = next(
        (d for d in deps if "Pillow" in d or "pillow" in d.lower()), None
    )
    assert pillow_dep is not None, "Pillow not found in dependencies"
    assert "<" in pillow_dep, (
        f"Pillow dependency '{pillow_dep}' lacks upper bound — "
        "silent breaking upgrade risk"
    )
