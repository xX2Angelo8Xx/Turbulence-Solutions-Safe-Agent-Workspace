# Dev Log — GUI-022: Add README Toggle Checkbox to Launcher

**Branch:** `GUI-022/readme-toggle`
**Assigned To:** Developer Agent
**User Story:** US-039
**Depends On:** INS-022 (Done)

---

## Status
In Progress

---

## Requirements Summary

1. Add "Include README files" `CTkCheckBox` to the main window project creation area.
2. On app launch, restore checkbox state from `get_setting('include_readmes', True)`.
3. On checkbox state change, persist new value via `set_setting('include_readmes', value)`.
4. Pass `include_readmes` value to `create_project()` in `_on_create_project`.
5. Add `include_readmes: bool = True` stub parameter to `create_project()` so the call is valid (actual README deletion logic is INS-023's scope).

---

## Implementation Plan

- **`src/launcher/gui/app.py`**
  - Import `get_setting`, `set_setting` from `launcher.core.user_settings`
  - Increase `_WINDOW_HEIGHT` from 590 → 630 to accommodate the extra row
  - Add `include_readmes_var` BooleanVar initialized from settings in `_build_ui()`
  - Add `CTkCheckBox` widget at row=7; shift all downstream rows by 1 (rows 7→8 through 12→13)
  - Add `_on_include_readmes_toggle` method that calls `set_setting('include_readmes', value)`
  - In `_on_create_project`, read checkbox value and pass `include_readmes=...` to `create_project()`

- **`src/launcher/core/project_creator.py`**
  - Add `include_readmes: bool = True` parameter to `create_project()` (stub, not used yet — INS-023 implements the behavior)

---

## Implementation Summary

### Files Changed

| File | Change |
|------|--------|
| `src/launcher/gui/app.py` | Added Include README files checkbox, import, persistence, row renumbering |
| `src/launcher/core/project_creator.py` | Added `include_readmes=True` stub parameter |
| `docs/workpackages/workpackages.csv` | Status → In Progress / Review |

### Decisions

- Placed the new checkbox at row=7 (between "Open in VS Code" and "Create Project"), consistent with the existing Open in VS Code checkbox style.
- `ctk.BooleanVar(value=bool(initial_include_readmes))` ensures safe coercion of any truthy JSON value.
- The `include_readmes` parameter is added as a stub to `create_project()` with `default=True` and no behavior change; INS-023 will implement the actual README deletion logic.
- Window height bumped from 590 → 630 to prevent widget clipping after the row shift.

### Tests Written

- `tests/GUI-022/test_gui022_include_readmes_checkbox.py` — 8 tests covering:
  - Checkbox exists in the built UI
  - Default value is `True`
  - Checkbox initializes from `get_setting` value (True / False cases)
  - `_on_include_readmes_toggle` calls `set_setting` with correct value
  - `_on_create_project` passes `include_readmes=True` to `create_project`
  - `_on_create_project` passes `include_readmes=False` to `create_project`
  - `create_project()` accepts `include_readmes` parameter without error

---

## Test Results

All 8 unit tests passed. See `docs/test-results/test-results.csv`.

---

## Known Limitations / Notes

- INS-023 must implement the actual README file deletion when `include_readmes=False`.
- The stub parameter in `create_project()` means passing `False` has no visible effect until INS-023 is done.
