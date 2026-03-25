# Dev Log — FIX-076

**Developer:** Developer Agent
**Date started:** 2026-03-25
**Iteration:** 1

## Objective

Fix the Reset Agent Blocks button visibility and functionality in the Settings dialog. The button exists in source code but was invisible at runtime because the dialog window height (280px) was too small to display the Reset Agent Blocks section (rows 4–6). Also ensure the dialog's grid column stretches properly.

## Implementation Summary

- Increased `SettingsDialog` geometry height from `480x280` to `480x480` so all 7 rows (Python Runtime section rows 0–3 plus Reset Agent Blocks section rows 4–6) are visible.
- Added `self._dialog.grid_columnconfigure(1, weight=1)` in `_build_ui()` so the workspace entry field stretches to fill available width.
- The underlying reset logic (`_reset_hook_state`, `_atomic_write_hook_state`) and all button handlers (`_browse_workspace`, `_on_reset_agent_blocks`) were already correct — only the dialog size was the issue.
- No new dependencies introduced.

## Files Changed

- `src/launcher/gui/app.py` — SettingsDialog: geometry changed from `480x280` to `480x480`; added `grid_columnconfigure(1, weight=1)` in `_build_ui()`.
- `docs/workpackages/workpackages.csv` — FIX-076 status set to `In Progress`.

## Tests Written

- `tests/FIX-076/test_fix076_reset_agent_blocks.py`
  - `test_reset_hook_state_clears_sessions` — verifies `_reset_hook_state` deletes session deny_count entries
  - `test_reset_hook_state_no_file` — verifies no-op when file absent
  - `test_reset_hook_state_corrupt_file` — verifies corrupt file is replaced with empty state
  - `test_reset_hook_state_empty_state` — verifies empty state returns 0 sessions reset
  - `test_reset_hook_state_multiple_sessions` — verifies all sessions are cleared
  - `test_reset_hook_state_preserves_non_session_keys` — verifies non-session keys are kept
  - `test_on_reset_agent_blocks_no_workspace` — verifies error shown when no workspace selected
  - `test_on_reset_agent_blocks_invalid_path` — verifies error shown for non-existent directory
  - `test_on_reset_agent_blocks_success` — verifies success info shown after reset
  - `test_on_reset_agent_blocks_os_error` — verifies error shown on OSError
  - `test_dialog_height_sufficient` — verifies dialog geometry height >= 400px
  - `test_dialog_columnconfigure` — verifies column 1 has weight=1
  - `test_reset_button_exists` — verifies reset_agent_blocks_button widget exists
  - `test_workspace_entry_exists` — verifies workspace_entry widget exists
  - `test_browse_workspace_button_exists` — verifies browse_workspace_button exists

## Known Limitations

- The dialog is fixed-size (`resizable(False, False)`). Future sections would require another height increase.

---

## Iteration 2 — 2026-03-25

**Trigger:** Tester regression — `test_dialog_geometry_is_480x280` asserted the old geometry string `"480x280"`, which contradicts the fix implemented in iteration 1 (geometry is now `"480x480"`).

### Changes

- `tests/GUI-018/test_gui018_edge_cases.py`
  - Renamed `test_dialog_geometry_is_480x280` → `test_dialog_geometry_is_480x480`
  - Updated docstring: "480×280" → "480×480"
  - Updated assertion: `assert_called_with("480x280")` → `assert_called_with("480x480")`
  - Updated module docstring entry to say `"480x480"`

### Test Results

All 64 tests passed (tests/FIX-076/ + tests/GUI-018/).
