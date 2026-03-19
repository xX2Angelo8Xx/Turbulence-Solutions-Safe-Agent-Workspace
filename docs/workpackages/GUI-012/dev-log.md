# Dev Log — GUI-012

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective
Refine the launcher layout to ensure generous spacing between UI elements, a clear visual hierarchy guiding the user through project creation steps, and consistent polished styling on all components.

## Implementation Summary

Updated `src/launcher/gui/app.py`:
- Window height increased from 340 to 440 to accommodate extra error label rows.
- All widget grid calls use `padx=(20, ...)` and `pady=12` (up from `padx=(16, ...)` and `pady=8`).
- Create Project button: `height=40`, `sticky="ew"`, `padx=20`, `pady=(20, 24)`.
- Checkbox: `pady=10`.
- Error labels use `pady=(0, 4)` for tight spacing below their parent entry.

Updated `src/launcher/gui/components.py`:
- `padx=(20, 8)` on labels (up from `(16, 8)`).
- `pady=12` on all widget grid calls (up from `8`).
- Browse button: `padx=(0, 20)` (up from `(0, 16)`).

## Files Changed
- `src/launcher/gui/app.py` — spacing and height updated (merged with GUI-003, GUI-004, GUI-011)
- `src/launcher/gui/components.py` — spacing updated (merged with GUI-011)

## Tests Written
- `tests/GUI-012/test_gui012_spacing.py`
  - Window height >= 400 and == 440
  - Create button padx/pady >= 10
  - Checkbox padx/pady >= 10
  - Create button columnspan=3 and sticky="ew"
  - Create button height >= 36
  - Component label/entry padx/pady >= 10
  - Browse button padx/pady >= 10

## Known Limitations
None.
