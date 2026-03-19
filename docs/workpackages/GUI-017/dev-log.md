# Dev Log — GUI-017: Update UI Labels and Validation for New Naming Convention

## Status
In Progress

## Assigned To
Developer Agent

## Date
2026-03-17

---

## Scope

Update UI text in `src/launcher/gui/app.py` to communicate the new `TS-SAE-{name}` naming convention:
1. Update placeholder text on the project name entry from `"my-project"` to `"MatlabDemo"`.
2. Update the success message to reference `TS-SAE-{folder_name}` in the displayed project name.
3. Confirm (already done in GUI-015) that the duplicate folder check uses `TS-SAE-{folder_name}`.

---

## Implementation

### Files Changed

| File | Change |
|------|--------|
| `src/launcher/gui/app.py` | Updated placeholder text and success message |

### Change Details

**Placeholder text** (`app.py` line ~113):
- Before: `placeholder="my-project"`
- After: `placeholder="MatlabDemo"`
- Reason: The example in US-017 uses "MatlabDemo"; this helps users understand the format expected (no prefix needed — it's added automatically).

**Success message** (`app.py` `_on_create_project()`):
- Before: `f'Project "{folder_name}" created successfully at:\n{created_path}'`
- After: `f'Project "TS-SAE-{folder_name}" created successfully at:\n{created_path}'`
- Reason: The messagebox should show the actual folder name the user will find at the destination, including the TS-SAE prefix.

**Duplicate folder check** (already correct from GUI-015, confirmed):
- Uses `f"TS-SAE-{folder_name}"` in `check_duplicate_folder()` call
- Error message already reads: `A folder named "TS-SAE-{folder_name}" already exists at the destination.`

---

## Tests Written

- `tests/GUI-017/test_gui017_ui_labels.py`
  - `test_placeholder_text_is_updated` — verifies placeholder is "MatlabDemo"
  - `test_success_message_shows_ts_sae_prefix` — verifies showinfo called with TS-SAE-{name}
  - `test_duplicate_check_uses_ts_sae_prefix` — verifies check_duplicate_folder called with TS-SAE- prefix
  - `test_duplicate_error_message_shows_ts_sae_prefix` — verifies error label contains TS-SAE-

---

## Test Results

All tests pass. See `docs/test-results/test-results.csv` for logged runs.

---

## Known Limitations

None.
