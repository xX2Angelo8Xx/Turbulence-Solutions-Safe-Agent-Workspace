# Dev Log — GUI-003

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective
Text field for the user to enter a custom project folder name. Validate: not empty, no special characters that break file systems, no duplicate folder at target path.

## Implementation Summary

Created `src/launcher/gui/validation.py` containing:
- `validate_folder_name(name)` — validates against cross-platform file-system rules: empty check, trailing period/space, length > 255, illegal characters (`< > : " / \ | ? * \x00-\x1f`), dot/dotdot names, Windows reserved names (CON, PRN, AUX, NUL, COM1-9, LPT1-9).
- `check_duplicate_folder(name, destination)` — returns True if `<destination>/<name>` already exists on disk.

Updated `src/launcher/gui/app.py` to import validation functions and add `project_name_error_label` (inline red label) below the project name entry.

## Files Changed
- `src/launcher/gui/validation.py` — created
- `src/launcher/gui/app.py` — updated (merged with GUI-004, GUI-011, GUI-012)

## Tests Written
- `tests/GUI-003/test_gui003_folder_name.py`
  - Valid names (ASCII, underscores, numbers, spaces, exactly 255 chars)
  - Empty / whitespace rejection
  - Trailing period and trailing space rejection
  - Illegal character rejection for all 9 forbidden chars
  - Null-byte and control-char rejection
  - Windows reserved name rejection (8 parametrized cases)
  - Length > 255 rejection
  - Path traversal / security bypass cases
  - `check_duplicate_folder` edge cases
  - App `project_name_error_label` attribute and red color

## Known Limitations
- `check_duplicate_folder` performs a plain `Path.exists()` check; symlink race conditions are a theoretical concern but out of scope for this WP.
