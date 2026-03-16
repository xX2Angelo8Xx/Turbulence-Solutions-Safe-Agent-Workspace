"""Tester edge-case tests for FIX-016: Fix App Icon for Windows (.ico).

Edge cases added by Tester Agent beyond the Developer's test suite:

TST-1151  launcher.spec datas includes BOTH TS-Logo.png AND TS-Logo.ico
TST-1152  LOGO_ICO_PATH resolves to _MEIPASS/TS-Logo.ico when bundled
TST-1153  TS-Logo.ico is openable by Pillow (deep format validation)
TST-1154  Icon-setting code is wrapped in a broad except clause (no crash on failure)
TST-1155  Windows branch uses wm_iconbitmap only (not iconphoto on win32)
TST-1156  LOGO_ICO_PATH filename is exactly 'TS-Logo.ico'
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# TST-1151  launcher.spec datas includes BOTH .png AND .ico
# ---------------------------------------------------------------------------

def test_spec_datas_includes_both_png_and_ico():
    """TST-1151: launcher.spec datas must bundle both TS-Logo.png AND TS-Logo.ico."""
    spec = (REPO_ROOT / "launcher.spec").read_text(encoding="utf-8")

    # Locate the datas block
    in_datas = False
    has_png = False
    has_ico = False
    for line in spec.splitlines():
        if "datas=[" in line.replace(" ", ""):
            in_datas = True
        if in_datas and "TS-Logo.png" in line:
            has_png = True
        if in_datas and "TS-Logo.ico" in line:
            has_ico = True
        # End of datas block: a line with ]," that doesn't say "datas"
        if in_datas and "]," in line and "datas" not in line.lower() and (has_png or has_ico):
            break

    assert has_png, "launcher.spec datas is missing the TS-Logo.png entry"
    assert has_ico, "launcher.spec datas is missing the TS-Logo.ico entry"


# ---------------------------------------------------------------------------
# TST-1152  LOGO_ICO_PATH uses _MEIPASS prefix when bundled
# ---------------------------------------------------------------------------

def test_logo_ico_path_uses_meipass_when_bundled():
    """TST-1152: LOGO_ICO_PATH resolves to _MEIPASS/TS-Logo.ico when sys._MEIPASS exists."""
    fake_meipass = "/fake/meipass"

    # Remove cached module so the conditional at module level re-evaluates
    import importlib
    import launcher.config as _cfg_orig  # ensure already imported once
    real_meipass = getattr(sys, "_MEIPASS", None)

    try:
        # Inject a fake _MEIPASS
        sys._MEIPASS = fake_meipass
        # Remove the cached module and reimport
        for key in list(sys.modules.keys()):
            if key == "launcher.config":
                del sys.modules[key]
        import launcher.config as cfg_fresh
        expected = Path(fake_meipass) / "TS-Logo.ico"
        assert cfg_fresh.LOGO_ICO_PATH == expected, (
            f"Expected LOGO_ICO_PATH={expected} but got {cfg_fresh.LOGO_ICO_PATH}"
        )
    finally:
        # Restore original state
        if real_meipass is None:
            if hasattr(sys, "_MEIPASS"):
                del sys._MEIPASS
        else:
            sys._MEIPASS = real_meipass
        # Reset to original import
        for key in list(sys.modules.keys()):
            if key == "launcher.config":
                del sys.modules[key]
        import launcher.config  # restore original module in cache


# ---------------------------------------------------------------------------
# TST-1153  TS-Logo.ico is openable by Pillow (deep validation)
# ---------------------------------------------------------------------------

def test_ico_openable_by_pillow():
    """TST-1153: TS-Logo.ico must be openable by Pillow without errors."""
    try:
        from PIL import Image
    except ImportError:
        import pytest
        pytest.skip("Pillow not installed — skipping deep ICO validation")

    ico_path = REPO_ROOT / "TS-Logo.ico"
    # Opening and loading the image validates the full ICO structure
    img = Image.open(ico_path)
    img.load()  # force decode — catches truncated/corrupt files
    assert img.format == "ICO", f"Pillow reported format={img.format!r}, expected 'ICO'"


# ---------------------------------------------------------------------------
# TST-1154  Icon-setting code is wrapped in a broad except clause
# ---------------------------------------------------------------------------

def test_app_icon_setting_has_broad_exception_handler():
    """TST-1154: The icon-setting block in app.py is wrapped in 'except Exception'
    so a corrupt/missing .ico cannot crash the application on startup."""
    app_src = (REPO_ROOT / "src" / "launcher" / "gui" / "app.py").read_text(
        encoding="utf-8"
    )
    # Both the try and except Exception must be present in the icon-setting section.
    # Verify they appear close together in the source (within the __init__ context).
    lines = app_src.splitlines()
    try_found = False
    except_found = False
    for line in lines:
        stripped = line.strip()
        if stripped == "try:" and not try_found:
            try_found = True
        if try_found and stripped.startswith("except Exception"):
            except_found = True
            break
    assert try_found, "app.py is missing a 'try:' block for icon setting"
    assert except_found, (
        "app.py icon-setting block does not use 'except Exception' — "
        "a corrupt/missing .ico would crash the app"
    )


# ---------------------------------------------------------------------------
# TST-1155  Windows branch does NOT call iconphoto (only wm_iconbitmap)
# ---------------------------------------------------------------------------

def test_app_win32_branch_uses_only_iconbitmap():
    """TST-1155: The win32 branch must call wm_iconbitmap and NOT iconphoto,
    so the correct icon type is used on Windows."""
    app_src = (REPO_ROOT / "src" / "launcher" / "gui" / "app.py").read_text(
        encoding="utf-8"
    )
    lines = app_src.splitlines()

    # Find the win32 branch
    in_win32_block = False
    iconphoto_in_win32 = False
    iconbitmap_in_win32 = False

    for line in lines:
        stripped = line.strip()
        if 'sys.platform == "win32"' in stripped:
            in_win32_block = True
            continue
        if in_win32_block:
            # The else: ends the win32 block
            if stripped.startswith("else:"):
                in_win32_block = False
                break
            if "wm_iconbitmap" in stripped:
                iconbitmap_in_win32 = True
            if "iconphoto" in stripped:
                iconphoto_in_win32 = True

    assert iconbitmap_in_win32, "win32 branch does not call wm_iconbitmap"
    assert not iconphoto_in_win32, (
        "win32 branch incorrectly calls iconphoto — should use wm_iconbitmap only"
    )


# ---------------------------------------------------------------------------
# TST-1156  LOGO_ICO_PATH filename is exactly 'TS-Logo.ico'
# ---------------------------------------------------------------------------

def test_logo_ico_path_filename():
    """TST-1156: LOGO_ICO_PATH must point to a file named exactly 'TS-Logo.ico'
    (case-sensitive where applicable) to match the bundled asset name."""
    from launcher.config import LOGO_ICO_PATH
    assert LOGO_ICO_PATH.name == "TS-Logo.ico", (
        f"LOGO_ICO_PATH filename is '{LOGO_ICO_PATH.name}', expected 'TS-Logo.ico'"
    )
