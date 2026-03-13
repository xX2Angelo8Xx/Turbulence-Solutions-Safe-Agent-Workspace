# Dev Log — FIX-001

## Summary

Fix the `test_destination_error_label_grid_row_4` test in `tests/GUI-004/test_gui004_destination_validation.py` to use `call_args_list` instead of `call_args`, resolving a mock isolation issue where all `CTkLabel` instances share the same mock object.

## Root Cause

When `customtkinter` is mocked with a single `MagicMock`, every `ctk.CTkLabel(...)` call returns the same mock object (`ctk.CTkLabel.return_value`). This means `destination_error_label`, `project_name_error_label`, `update_banner`, etc., are all the same object. The test was checking `grid.call_args` (the LAST call), which reflected the last `.grid()` call made on any `CTkLabel` — `update_banner.grid(row=8)` — rather than the `destination_error_label.grid(row=4)` call.

## Fix

**File changed:** `tests/GUI-004/test_gui004_destination_validation.py`

Changed `test_destination_error_label_grid_row_4` from checking `grid.call_args` (only the last call) to checking `grid.call_args_list` and asserting that at least one call had `row=4`.

## Tests

- All `tests/GUI-004/` tests pass after the fix (36 passed).
- No source code changes were required; the app is correct.

## Date

2026-03-13

## Assigned To

Developer Agent
