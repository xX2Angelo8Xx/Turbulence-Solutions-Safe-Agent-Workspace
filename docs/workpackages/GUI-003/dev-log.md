# Dev Log — GUI-003

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 2

## Objective

Add a text field for the user to enter a custom project folder name and validate it
inline. Valid rules: not empty, no filesystem-breaking special characters, no Windows
reserved names, no trailing dot or space, no path traversal, max 255 chars.
Provide `validate_folder_name()` and `check_duplicate_folder()` utilities and wire an
inline red error label into the App window.

## Implementation Summary

Iteration 1 failed because both `src/launcher/gui/validation.py` and the `app.py`
changes were never saved to disk (VS Code editor buffer only). In iteration 2, all
files were created/modified via file tools and confirmed on disk.

**`src/launcher/gui/validation.py`** — Created with:
- `validate_folder_name(name: str) -> tuple[bool, str]`: checks trailing dot/space
  (on raw input before strip), empty/whitespace, dot-only, 255-char length, forbidden
  chars regex (`[\:/*?|<>"\x00-\x1f]`), Windows reserved names regex, and finally
  returns `(True, "")` on success.
- `check_duplicate_folder(name: str, destination: str) -> bool`: returns
  `os.path.exists(os.path.join(destination, name))`; guards against empty inputs.

Key design decision for trailing-space detection: the raw name's last character is
checked _before_ `name.strip()`, so `"project "` is correctly rejected whereas a
pure `strip()` approach would silently accept it.

**`src/launcher/gui/app.py`** — Modified:
- Added import for `check_duplicate_folder`, `validate_folder_name`.
- Changed `_WINDOW_HEIGHT` from 340 → 370.
- Added `self.project_name_error_label` CTkLabel (text="", text_color="red") at
  row=1 col=1, spanning 2 columns.
- Shifted existing rows: Project Type → 2, Destination → 3, Checkbox → 4,
  Create button → 5.

## Files Changed

- `src/launcher/gui/validation.py` — Created (new file)
- `src/launcher/gui/app.py` — Added import, error label widget, row shifts, height
- `tests/GUI-003/test_gui003_folder_name.py` — Created (new file, 49 tests)
- `tests/GUI-003/__init__.py` — Created

## Tests Written

49 tests total (48 pass, 1 skip):

- `TestValidateFolderNameValid` (6 tests) — basic valid names, return type
- `TestValidateFolderNameEmpty` (3 tests) — empty string, whitespace only
- `TestValidateFolderNameInvalidChars` (11 tests) — colon, backslash, slash, `*?|<>"`, null byte, control char
- `TestValidateFolderNameDots` (4 tests) — single/double dot, trailing dot, trailing space
- `TestValidateFolderNameReserved` (7 tests) — CON, NUL, PRN, AUX, COM9, LPT1, case-insensitive
- `TestValidateFolderNameSecurity` (4 tests) — path traversal, null byte bypass, control char bypass
- `TestValidateFolderNameEdgeCases` (5 tests) — unicode, emoji, tab char, 255-char length, leading dot
- `TestCheckDuplicateFolder` (7 tests, 1 skip) — non-existent, existing folder, empty inputs, file collision, symlink
- `TestAppErrorLabel` (2 tests) — `project_name_error_label` attribute exists, created with `text=""`

## Iteration 2 — 2026-03-12

### Tester Feedback Addressed

- **BUG-017 (BLOCKING)**: All GUI-003 files now saved to disk:
  - `src/launcher/gui/validation.py` created
  - `src/launcher/gui/app.py` modified with error label, row shifts, height
  - `tests/GUI-003/test_gui003_folder_name.py` created
  - `tests/GUI-003/__init__.py` created
- **BUG-018 (non-blocking)**: 255-char length guard added to `validate_folder_name`
  (`if len(stripped) > 255: return False, "Name is too long..."`)

### Additional Changes

- Fixed a trailing-space detection bug discovered during testing: moved the
  `name[-1] in (".", " ")` check to operate on the _raw_ input before `name.strip()`,
  so that `"project "` is correctly rejected.

## Known Limitations

- `check_duplicate_folder` is string-path-based and does not follow symlinks for
  liveness detection — OS-level collision is caught, but symlinks pointing outside
  the destination are not resolved.
- Symlink test (`test_symlink_to_existing_dir_returns_true`) is permanently skipped
  on non-elevated Windows hosts without Developer Mode.
- The error label is wired up visually but not yet connected to live keystroke
  validation — that is deferred to GUI-007 (Input Validation & Error UX).
