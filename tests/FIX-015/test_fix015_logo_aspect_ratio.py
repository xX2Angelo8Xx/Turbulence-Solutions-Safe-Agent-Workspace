"""
FIX-015 regression tests — TS Logo Aspect Ratio.

Verifies that the CTkImage size for the logo is computed proportionally from
the image's actual dimensions rather than using the old hardcoded (160, 50).
"""

from __future__ import annotations

import ast
import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

APP_PY = Path(__file__).resolve().parents[2] / "src" / "launcher" / "gui" / "app.py"


def _read_app_source() -> str:
    return APP_PY.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Regression: hardcoded (160, 50) must be gone
# ---------------------------------------------------------------------------


def test_logo_no_hardcoded_160_50():
    """BUG-043 regression: size=(160, 50) must not appear in app.py."""
    source = _read_app_source()
    assert "size=(160, 50)" not in source, (
        "Hardcoded size=(160, 50) still present in app.py — FIX-015 not applied."
    )


# ---------------------------------------------------------------------------
# Source-level AST check: computed width must be present
# ---------------------------------------------------------------------------


def test_logo_size_uses_computed_width():
    """The CTkImage call must use a variable for width, not a literal 160."""
    source = _read_app_source()
    # The fix introduces _target_width and _target_height
    assert "_target_width" in source, "_target_width variable missing from app.py"
    assert "_target_height" in source, "_target_height variable missing from app.py"


# ---------------------------------------------------------------------------
# Unit: proportional width computation for a known image size
# ---------------------------------------------------------------------------


def _compute_proportional_width(img_width: int, img_height: int, target_height: int = 50) -> int:
    """Replicate the exact formula used in app.py."""
    return int(img_width * (target_height / img_height))


def test_logo_ctk_image_size_is_proportional():
    """
    Regression: App._build_ui must pass a proportionally computed size to CTkImage.

    Use a fake logo image whose dimensions are easy to predict (200×100).
    Expected: CTkImage receives size=(100, 50).
    """
    # ctk is already mocked globally by conftest; reuse the shared mock.
    _ctk_mock = sys.modules["customtkinter"]
    _ctk_mock.reset_mock()

    fake_img = MagicMock()
    fake_img.width = 200
    fake_img.height = 100

    with patch("PIL.Image.open", return_value=fake_img):
        from launcher.gui.app import App
        App()

    # CTkImage must have been called; find the call that includes a 'size' kwarg.
    ctk_image_calls = _ctk_mock.CTkImage.call_args_list
    assert ctk_image_calls, "CTkImage was never called — logo block not reached"

    size_arg = None
    for call_item in ctk_image_calls:
        kw = call_item.kwargs
        if "size" in kw:
            size_arg = kw["size"]
            break

    assert size_arg is not None, "CTkImage was called but without a 'size' keyword argument"
    width, height = size_arg
    assert height == 50, f"Expected target height 50, got {height}"
    expected_width = _compute_proportional_width(200, 100, 50)  # → 100
    assert width == expected_width, (
        f"Expected proportional width {expected_width}, got {width}"
    )


# ---------------------------------------------------------------------------
# Unit: aspect-ratio preservation for various image shapes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "img_width,img_height,expected_width",
    [
        (400, 100, 200),   # wide image (4:1 ratio → 200×50)
        (50, 200, 12),     # tall image (1:4 ratio → int(50*50/200)=12×50)
        (100, 100, 50),    # square image (1:1 ratio → 50×50)
        (320, 80, 200),    # 4:1 ratio at different scale → 200×50
        (1000, 250, 200),  # large wide image → 200×50
    ],
)
def test_logo_preserves_aspect_ratio_wide_image(img_width, img_height, expected_width):
    """Formula int(w * (50 / h)) must yield expected_width for given dimensions."""
    result = _compute_proportional_width(img_width, img_height, target_height=50)
    assert result == expected_width, (
        f"For {img_width}×{img_height}: expected width {expected_width}, got {result}"
    )


def test_logo_preserves_aspect_ratio_tall_image():
    """Tall images get a width smaller than 50."""
    result = _compute_proportional_width(50, 200, 50)
    assert result == 12
    assert result < 50


def test_logo_preserves_aspect_ratio_square_image():
    """Square images get width == target_height."""
    result = _compute_proportional_width(100, 100, 50)
    assert result == 50
