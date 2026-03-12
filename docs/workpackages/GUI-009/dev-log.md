# Dev Log — GUI-009

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective

Show a non-blocking banner in the UI when a newer version of the Launcher is available. The banner must appear automatically on launch (silent background check) and must not interrupt the normal project-creation workflow.

## Implementation Summary

GUI-009 and GUI-010 were implemented together in a single `app.py` edit to prevent merge conflicts (both WPs modify the same file).

**Changes to `src/launcher/gui/app.py`:**
- Added `import threading` to stdlib imports.
- Added `check_for_update` to the `launcher.core.updater` import.
- Added `VERSION` to the `launcher.config` import.
- Increased `_WINDOW_HEIGHT` from 440 to 520 to accommodate the two new rows.
- In `_build_ui()`, added row 7 (`check_updates_button`) and row 8 (`update_banner`). The banner is hidden via `grid_remove()` on init.
- In `__init__()`, after `_build_ui()`, a daemon thread is started that calls `_run_update_check()`.
- Added `_run_update_check()`: calls `check_for_update(VERSION)` and schedules `_apply_update_result()` on the main thread via `_window.after(0, ...)`.
- Added `_apply_update_result(update_available, latest_version, manual)`: updates the banner text and shows/hides it. Shows "You're up to date." on manual no-update checks.

**Thread safety:** The background thread never mutates widget state directly. It posts work to the Tk main loop via `_window.after(0, callback)`, which is the correct cross-thread update pattern for Tkinter/customtkinter.

## Files Changed
- `src/launcher/gui/app.py` — added threading import, check_for_update import, VERSION import, increased window height, added update_banner widget, added _run_update_check and _apply_update_result methods, started background thread in __init__

## Tests Written
- `tests/GUI-009/test_gui009_update_banner.py` (10 tests)
  - `test_update_banner_attribute_exists` — widget attribute present
  - `test_update_banner_hidden_on_init` — grid_remove() called during _build_ui
  - `test_update_banner_is_not_none` — widget object is not None
  - `test_apply_shows_banner_when_update_available` — configure + grid called with update text
  - `test_apply_hides_banner_on_silent_no_update` — grid_remove called when no update (silent)
  - `test_apply_shows_up_to_date_on_manual_no_update` — "You're up to date." shown on manual check
  - `test_apply_banner_text_contains_version_number` — version number appears in banner text
  - `test_apply_shows_banner_on_update_regardless_of_manual` — update=True always shows banner
  - `test_run_update_check_calls_check_for_update_with_version` — correct VERSION arg passed
  - `test_run_update_check_schedules_result_on_main_thread` — _window.after(0, callable) called

## Known Limitations
- The banner does not auto-hide after a timeout (out of scope for this WP).
- No retry logic if the network request fails (by design — `check_for_update` silently returns (False, current_version) on any error).
