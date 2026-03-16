# Dev Log — FIX-015: Fix TS Logo Aspect Ratio

## Status
Review

## Developer
Developer Agent

## Date
2026-03-16

## Branch
`FIX-015/add-logo-fix-tracking`

## Bug Reference
BUG-043

---

## Problem

In `src/launcher/gui/app.py`, the logo was displayed using a hardcoded
`size=(160, 50)` in the `CTkImage` call. This does not match the actual image
dimensions, causing the TS logo to appear stretched or distorted when the
natural aspect ratio of the image differs from 160:50.

## Solution

After opening the image with `Image.open()`, read the actual pixel dimensions
via `_logo_img.width` and `_logo_img.height`. Compute a proportional width for
the target height of 50 pixels:

```python
_target_height = 50
_target_width = int(_logo_img.width * (_target_height / _logo_img.height))
```

Pass the computed `(_target_width, _target_height)` tuple to `CTkImage(size=...)`.

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/gui/app.py` | `_build_ui`: replaced hardcoded `size=(160, 50)` with proportional width computation |

## Tests Written

| File | Test | Type |
|------|------|------|
| `tests/FIX-015/test_fix015_logo_aspect_ratio.py` | `test_logo_no_hardcoded_160_50` | Regression |
| `tests/FIX-015/test_fix015_logo_aspect_ratio.py` | `test_logo_size_uses_computed_width` | Regression |
| `tests/FIX-015/test_fix015_logo_aspect_ratio.py` | `test_logo_ctk_image_size_is_proportional` | Integration |
| `tests/FIX-015/test_fix015_logo_aspect_ratio.py` | `test_logo_preserves_aspect_ratio_wide_image[400-100-200]` | Unit |
| `tests/FIX-015/test_fix015_logo_aspect_ratio.py` | `test_logo_preserves_aspect_ratio_wide_image[50-200-12]` | Unit |
| `tests/FIX-015/test_fix015_logo_aspect_ratio.py` | `test_logo_preserves_aspect_ratio_wide_image[100-100-50]` | Unit |
| `tests/FIX-015/test_fix015_logo_aspect_ratio.py` | `test_logo_preserves_aspect_ratio_wide_image[320-80-200]` | Unit |
| `tests/FIX-015/test_fix015_logo_aspect_ratio.py` | `test_logo_preserves_aspect_ratio_wide_image[1000-250-200]` | Unit |
| `tests/FIX-015/test_fix015_logo_aspect_ratio.py` | `test_logo_preserves_aspect_ratio_tall_image` | Unit |
| `tests/FIX-015/test_fix015_logo_aspect_ratio.py` | `test_logo_preserves_aspect_ratio_square_image` | Unit |

## Test Results

All 10 tests pass. See `docs/test-results/test-results.csv` entries TST-1107 to TST-1117.

## Decisions

- Target height kept at 50 px to match the original UI layout intent.
- Integer truncation used (not rounding) to avoid subpixel sizes in CTkImage.
- No other files modified — scope strictly limited to `_build_ui` in `app.py`.
