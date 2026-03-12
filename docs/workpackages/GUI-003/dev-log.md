# Dev Log — GUI-003

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 2

## Objective

Add a text field for the user to enter a custom project folder name and validate it: not empty, no special characters that break file systems, no duplicate folder at the target path. Display inline error feedback for invalid names.

## Implementation Summary

Iteration 2 fixes BUG-017: the `app.py` changes from Iteration 1 were never saved to disk (existed only in an unsaved editor buffer). All GUI-003 changes are now applied via file creation/edit tools and verified by read-back.

Changes made:
- Created `src/launcher/gui/validation.py` with `validate_folder_name()` and `check_duplicate_folder()`.
- Modified `src/launcher/gui/app.py`:
  - Added import of `check_duplicate_folder` and `validate_folder_name`.
  - Increased `_WINDOW_HEIGHT` from 340 to 370.
  - Added `self.project_name_error_label` (CTkLabel with `text=""`, `text_color="red"`) at grid row=1.
  - Shifted Project Type to row=2, Destination to row=3, VS Code checkbox to row=4, Create button to row=5.
- Created `tests/GUI-003/__init__.py`.
- Created `tests/GUI-003/test_gui003_folder_name.py` with 49 tests covering all validation rules, security/bypass vectors, duplicate-folder check, and App error label widget.
- Also addresses BUG-018: added `len(stripped) > 255` guard to `validate_folder_name()`.
- Tester edge-case tests from Iteration 1 review are included in the test file.

## Files Changed

- `src/launcher/gui/validation.py` — new file; validate_folder_name and check_duplicate_folder
- `src/launcher/gui/app.py` — added validation import, error label widget, row shifts, height update
- `tests/GUI-003/__init__.py` — new (empty init)
- `tests/GUI-003/test_gui003_folder_name.py` — new; full test suite

## Tests Written

- TestValidateFolderNameValid (10 tests) — valid names including unicode, emoji, leading dot, 255-char max
- TestValidateFolderNameEmpty (3 tests) — empty string, whitespace-only
- TestValidateFolderNameIllegalChars (12 tests) — all illegal characters including tab as control char
- TestValidateFolderNameDots (2 tests) — "." and ".." rejection
- TestValidateFolderNameWindowsReserved (7 tests) — CON, NUL, PRN, AUX, COM9, LPT1, case-insensitive
- TestValidateFolderNameTrailing (2 tests) — trailing dot and space
- TestValidateFolderNameLength (1 test) — name > 255 chars rejected (BUG-018 fix)
- TestValidateFolderNameSecurity (4 tests) — path traversal, null-byte, control-char bypass
- TestCheckDuplicateFolder (7 tests) — nonexistent, existing folder, file collision, symlink (skip on Windows), empty args
- TestAppErrorLabel (2 tests) — error label attribute exists, CTkLabel constructed with text=""

## Known Limitations

- `validate_folder_name` does not validate against OS-specific path length limits beyond the 255-char component limit.
- Duplicate-folder check (`check_duplicate_folder`) is a point-in-time check; TOCTOU race is accepted and deferred to GUI-007.
- `project_name_error_label` is created but never populated — wired up in GUI-007.
