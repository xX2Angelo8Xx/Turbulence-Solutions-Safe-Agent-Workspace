# Dev Log — GUI-004

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective
Add destination path validation to support the native folder browser dialog. The browse dialog already exists (from GUI-001). This WP adds: `validate_destination_path()` in `validation.py`, a `destination_error_label` widget in `app.py`, and wires up the import so GUI-005 can consume both.

## Implementation Summary
- Added `validate_destination_path(path: str) -> tuple[bool, str]` to `src/launcher/gui/validation.py`. Validates: not empty, path exists, path is a directory, path is writable (`os.access`). Added `import os` to the module.
- Updated `src/launcher/gui/app.py`:
  - Added `validate_destination_path` to the import from `launcher.gui.validation`.
  - Added `self.destination_error_label` (CTkLabel, text="", text_color="red") at grid row 4, after the destination browse row.
  - Shifted the VS Code checkbox to row 5 and the Create Project button to row 6.
  - Increased `_WINDOW_HEIGHT` from 370 to 390 to accommodate the additional label row.

## Files Changed
- `src/launcher/gui/validation.py` — added `validate_destination_path()` and `import os`
- `src/launcher/gui/app.py` — added destination error label, shifted rows, updated import, adjusted window height

## Tests Written
- `tests/GUI-004/test_gui004_destination_validation.py`
  - `test_empty_string_rejected` — empty path returns False
  - `test_whitespace_only_rejected` — whitespace-only path returns False
  - `test_return_type_is_tuple` — return value is a 2-tuple
  - `test_valid_path_returns_empty_message` — valid path returns empty error string
  - `test_nonexistent_path_rejected` — non-existent path returns False
  - `test_file_path_rejected` — regular file (not directory) returns False
  - `test_valid_writable_dir_accepted` — tempdir returns True
  - `test_nonwritable_path_rejected` — mocked os.access returns False → rejected
  - `test_error_message_not_empty_on_failure` — all failure cases produce non-empty message
  - `test_destination_error_label_exists` — App has destination_error_label attribute
  - `test_destination_error_label_initial_text_empty` — initial text is ""
  - `test_destination_error_label_text_color_red` — text_color is "red"

## Known Limitations
- The error label is positioned but not yet wired to real-time validation — that is GUI-005 scope (Create Project click).
- Non-writable path test uses `unittest.mock.patch` to mock `os.access` since forcing a non-writable directory is not reliably cross-platform.
