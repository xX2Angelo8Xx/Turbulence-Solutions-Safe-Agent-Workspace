# Dev Log — GUI-010

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective

Add a "Check for Updates" button to the launcher UI that allows the user to manually trigger the same version-check flow used by the silent on-launch check (GUI-009).

## Implementation Summary

GUI-009 and GUI-010 were implemented together in a single `app.py` edit to prevent merge conflicts (both WPs modify the same file).

**Changes to `src/launcher/gui/app.py`:**
- Added `check_updates_button` (`CTkButton`) in row 7 of the grid, right-aligned, with a transparent background (text-link style) to maintain visual hierarchy.
- Added `_on_check_for_updates()`: called when the button is clicked. Immediately disables the button and changes text to "Checking…", then spawns a daemon thread that calls `check_for_update(VERSION)` and schedules `_finish_manual_check()` on the main thread.
- Added `_finish_manual_check(update_available, latest_version)`: restores the button to its original state and delegates to `_apply_update_result(..., manual=True)` to update the banner.

**Design decisions:**
- The "Check for Updates" button uses `fg_color="transparent"` to appear as a secondary text action, keeping the "Create Project" button as the primary CTA.
- Disabling the button during the check prevents double-clicks from spawning multiple concurrent threads.

## Files Changed
- `src/launcher/gui/app.py` — added check_updates_button widget, _on_check_for_updates method, _finish_manual_check method

## Tests Written
- `tests/GUI-010/test_gui010_check_for_updates_button.py` (9 tests)
  - `test_check_updates_button_attribute_exists` — widget attribute present on App
  - `test_check_updates_button_not_none` — widget object is not None
  - `test_check_updates_button_created_with_correct_text` — CTkButton called with text='Check for Updates'
  - `test_on_check_for_updates_disables_button` — button.configure(state='disabled') called
  - `test_on_check_for_updates_spawns_daemon_thread` — Thread created with daemon=True
  - `test_finish_manual_check_restores_button` — button.configure(state='normal') called
  - `test_finish_manual_check_shows_banner_on_update` — banner shows update message
  - `test_finish_manual_check_shows_up_to_date_on_no_update` — "up to date" shown
  - `test_manual_check_calls_check_for_update` — check_for_update called from inner thread target

## Known Limitations
- No rate-limiting on the manual check (user could click repeatedly after re-enabling); the button disable/re-enable mitigates rapid double-clicks.
