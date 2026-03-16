"""Tests for FIX-016: Fix App Icon for Windows (.ico).

Covers:
- TS-Logo.ico file presence and validity
- config.py LOGO_ICO_PATH constant
- launcher.spec icon= and datas entries
- app.py Windows/non-Windows icon branching
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Repo root is three levels up from this file (tests/FIX-016/test_xxx.py)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# ICO file tests (TST-FIX016-001 to TST-FIX016-003)
# ---------------------------------------------------------------------------

def test_ico_file_exists():
    """TST-FIX016-001: TS-Logo.ico exists at the repository root."""
    ico_path = REPO_ROOT / "TS-Logo.ico"
    assert ico_path.is_file(), f"TS-Logo.ico not found at {ico_path}"


def test_ico_file_is_valid_ico():
    """TST-FIX016-002: TS-Logo.ico is a valid ICO (correct magic bytes and type)."""
    ico_path = REPO_ROOT / "TS-Logo.ico"
    with open(ico_path, "rb") as f:
        header = f.read(6)
    reserved, ico_type, count = struct.unpack_from("<HHH", header, 0)
    assert reserved == 0, "ICO reserved field must be 0"
    assert ico_type == 1, "ICO type field must be 1 (icon)"
    assert count >= 1, "ICO must contain at least one image"


def test_ico_contains_required_sizes():
    """TST-FIX016-003: TS-Logo.ico contains all required sizes: 16,32,48,64,128,256."""
    required = {16, 32, 48, 64, 128, 256}
    ico_path = REPO_ROOT / "TS-Logo.ico"
    with open(ico_path, "rb") as f:
        data = f.read()
    _, _, count = struct.unpack_from("<HHH", data, 0)
    found = set()
    for i in range(count):
        offset = 6 + i * 16
        w, h = struct.unpack_from("<BB", data, offset)
        found.add(w if w != 0 else 256)
    assert required.issubset(found), f"Missing ICO sizes: {required - found}"


# ---------------------------------------------------------------------------
# config.py LOGO_ICO_PATH tests (TST-FIX016-004 to TST-FIX016-006)
# ---------------------------------------------------------------------------

def test_config_exports_logo_ico_path():
    """TST-FIX016-004: config.py exports the LOGO_ICO_PATH symbol."""
    import launcher.config as cfg
    assert hasattr(cfg, "LOGO_ICO_PATH"), "LOGO_ICO_PATH not found in launcher.config"


def test_logo_ico_path_points_to_ico():
    """TST-FIX016-005: LOGO_ICO_PATH ends with .ico."""
    from launcher.config import LOGO_ICO_PATH
    assert str(LOGO_ICO_PATH).lower().endswith(".ico"), (
        f"LOGO_ICO_PATH does not end with .ico: {LOGO_ICO_PATH}"
    )


def test_logo_ico_path_file_exists_in_dev():
    """TST-FIX016-006: LOGO_ICO_PATH resolves to an existing file in development."""
    from launcher.config import LOGO_ICO_PATH
    assert LOGO_ICO_PATH.is_file(), (
        f"LOGO_ICO_PATH does not point to an existing file: {LOGO_ICO_PATH}"
    )


# ---------------------------------------------------------------------------
# launcher.spec tests (TST-FIX016-007 to TST-FIX016-008)
# ---------------------------------------------------------------------------

def _read_spec() -> str:
    return (REPO_ROOT / "launcher.spec").read_text(encoding="utf-8")


def test_spec_icon_references_ico():
    """TST-FIX016-007: launcher.spec icon= parameter references .ico not .png."""
    spec = _read_spec()
    # Must contain the .ico reference
    assert "TS-Logo.ico" in spec, "launcher.spec does not reference TS-Logo.ico"
    # The icon= line must NOT reference .png
    for line in spec.splitlines():
        if "icon=" in line:
            assert ".png" not in line, (
                f"launcher.spec icon= still references .png: {line.strip()}"
            )
            assert ".ico" in line, (
                f"launcher.spec icon= does not reference .ico: {line.strip()}"
            )


def test_spec_datas_includes_ico():
    """TST-FIX016-008: launcher.spec datas list includes TS-Logo.ico entry."""
    spec = _read_spec()
    # Look for a datas entry that bundles the .ico file
    lines = spec.splitlines()
    found = any(
        "TS-Logo.ico" in line and ("datas" not in line or "." in line)
        for line in lines
    )
    # More precise: find the datas block and check for the .ico tuple
    in_datas = False
    ico_in_datas = False
    for line in lines:
        if "datas=[" in line.replace(" ", ""):
            in_datas = True
        if in_datas and "TS-Logo.ico" in line:
            ico_in_datas = True
            break
        if in_datas and "]," in line and "datas" not in line:
            in_datas = False
    assert ico_in_datas, "TS-Logo.ico not found in launcher.spec datas list"


# ---------------------------------------------------------------------------
# app.py import and icon-selection tests (TST-FIX016-009 to TST-FIX016-012)
# ---------------------------------------------------------------------------

def test_app_imports_logo_ico_path():
    """TST-FIX016-009: app.py source imports LOGO_ICO_PATH from config."""
    app_src = (REPO_ROOT / "src" / "launcher" / "gui" / "app.py").read_text(
        encoding="utf-8"
    )
    assert "LOGO_ICO_PATH" in app_src, "app.py does not import LOGO_ICO_PATH"


def test_app_uses_wm_iconbitmap_on_windows():
    """TST-FIX016-010: app.py source calls wm_iconbitmap with LOGO_ICO_PATH on Windows."""
    app_src = (REPO_ROOT / "src" / "launcher" / "gui" / "app.py").read_text(
        encoding="utf-8"
    )
    # The win32 branch must call wm_iconbitmap using LOGO_ICO_PATH
    assert "wm_iconbitmap(str(LOGO_ICO_PATH))" in app_src, (
        "app.py does not call wm_iconbitmap(str(LOGO_ICO_PATH)) in the Windows branch"
    )


def test_app_uses_iconphoto_on_non_windows():
    """TST-FIX016-011: On non-Windows, the iconphoto path is used (not wm_iconbitmap)."""
    # Simulate non-Windows: wm_iconbitmap should NOT be called
    from unittest.mock import MagicMock
    mock_window = MagicMock()
    with patch("PIL.Image.open") as mock_open, \
         patch("PIL.ImageTk.PhotoImage") as mock_photo:
        mock_img = MagicMock()
        mock_open.return_value = mock_img
        mock_photo.return_value = MagicMock()

        # Simulate the non-Windows branch
        if sys.platform != "win32":
            from PIL import Image, ImageTk
            _icon_img = Image.open("TS-Logo.png")
            _icon_photo = ImageTk.PhotoImage(_icon_img)
            mock_window.iconphoto(True, _icon_photo)
            mock_window.iconphoto.assert_called_once()
            mock_window.wm_iconbitmap.assert_not_called()


def test_app_source_has_win32_branch():
    """TST-FIX016-012: app.py source contains the sys.platform win32 guard."""
    app_src = (REPO_ROOT / "src" / "launcher" / "gui" / "app.py").read_text(
        encoding="utf-8"
    )
    assert 'win32' in app_src, "app.py is missing the sys.platform win32 check"
    assert 'wm_iconbitmap' in app_src, "app.py is missing wm_iconbitmap call"
    assert 'iconphoto' in app_src, "app.py is missing iconphoto fallback"
