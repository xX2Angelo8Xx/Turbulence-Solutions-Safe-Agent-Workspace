# Dev Log — GUI-007

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective

Validate all user inputs before project creation. Display clear, inline error
messages for: empty name, invalid characters, path not found, write permission
denied, and duplicate folder name.

## Implementation Summary

After a careful review of the source files (`validation.py`, `app.py`,
`components.py`) the validation layer is **fully implemented by prior workpackages
(GUI-003, GUI-004, GUI-005)**. No source-code changes were required for GUI-007.

The following coverage was confirmed:

| Acceptance Criterion | Location | Status |
|---|---|---|
| Empty name rejected with inline message | `validate_folder_name()` + `project_name_error_label` | ✅ |
| Invalid characters rejected with inline message | `validate_folder_name()` + `project_name_error_label` | ✅ |
| Path not found rejected with inline message | `validate_destination_path()` + `destination_error_label` | ✅ |
| Write permission denied rejected with inline message | `validate_destination_path()` + `destination_error_label` | ✅ |
| Duplicate folder name rejected with inline message | `check_duplicate_folder()` + `project_name_error_label` | ✅ |
| Errors cleared before re-validation on next Create click | `_on_create_project()` clears both labels unconditionally | ✅ |
| Invalid template falls back to messagebox error | `_on_create_project()` — `raw_template is None` branch | ✅ |

Additional validation present beyond the WP requirements:
- Trailing period or space in name
- Names longer than 255 characters
- Windows reserved names (CON, PRN, AUX, NUL, COM1–COM9, LPT1–LPT9), case-insensitive
- Special names `.` and `..`
- Control characters (U+0000–U+001F)

## Files Changed

_No source files were modified for this workpackage._

## Tests Written

Unit tests for `validate_folder_name()`:
- `test_empty_name` — empty string returns error
- `test_whitespace_only_name` — spaces-only returns error
- `test_valid_simple_name` — plain ASCII name is accepted
- `test_valid_name_with_hyphens_and_numbers` — hyphens and digits accepted
- `test_valid_unicode_name` — unicode characters accepted
- `test_name_trailing_period` — name ending with `.` rejected
- `test_name_trailing_space` — name ending with ` ` rejected
- `test_name_exactly_255_chars` — 255-char name accepted
- `test_name_256_chars_rejected` — 256-char name rejected
- `test_name_with_angle_bracket_lt` — `<` rejected
- `test_name_with_angle_bracket_gt` — `>` rejected
- `test_name_with_colon` — `:` rejected
- `test_name_with_double_quote` — `"` rejected
- `test_name_with_forward_slash` — `/` rejected
- `test_name_with_backslash` — `\` rejected
- `test_name_with_pipe` — `|` rejected
- `test_name_with_question_mark` — `?` rejected
- `test_name_with_asterisk` — `*` rejected
- `test_name_with_null_byte` — `\x00` control char rejected
- `test_name_with_other_control_char` — `\x1f` control char rejected
- `test_name_single_dot` — `.` rejected
- `test_name_double_dot` — `..` rejected
- `test_reserved_name_con` — `con` rejected
- `test_reserved_name_prn` — `prn` rejected
- `test_reserved_name_aux` — `aux` rejected
- `test_reserved_name_nul` — `nul` rejected
- `test_reserved_name_com1` — `com1` rejected
- `test_reserved_name_com9` — `com9` rejected
- `test_reserved_name_lpt1` — `lpt1` rejected
- `test_reserved_name_lpt9` — `lpt9` rejected
- `test_reserved_name_uppercase` — `CON` rejected (case-insensitive)
- `test_error_message_for_empty_name` — exact error text verified
- `test_error_message_for_invalid_chars` — exact error text verified
- `test_error_message_for_trailing_dot` — exact error text verified
- `test_error_message_for_too_long` — exact error text verified
- `test_error_message_for_reserved` — exact error text verified

Unit tests for `check_duplicate_folder()`:
- `test_duplicate_exists` — returns True when folder exists
- `test_no_duplicate` — returns False when folder absent
- `test_empty_name_returns_false` — empty name → False (no crash)
- `test_empty_destination_returns_false` — empty destination → False

Unit tests for `validate_destination_path()`:
- `test_empty_path` — empty string returns error
- `test_whitespace_only_path` — whitespace-only returns error
- `test_nonexistent_path` — non-existing path returns error
- `test_path_is_file_not_dir` — file path returns error
- `test_valid_writable_dir` — tmp_path returns success
- `test_non_writable_dir` — monkeypatched os.access → False returns error
- `test_error_message_empty_path` — exact error text verified
- `test_error_message_nonexistent` — exact error text verified
- `test_error_message_not_dir` — exact error text verified
- `test_error_message_not_writable` — exact error text verified

Integration tests for `App._on_create_project()`:
- `test_empty_name_shows_name_error_label` — label gets error text
- `test_invalid_name_shows_name_error_label` — label gets error text
- `test_empty_destination_shows_dest_error_label` — dest label gets error text
- `test_nonexistent_destination_shows_dest_error_label` — dest label gets error text
- `test_duplicate_folder_shows_name_error_label` — label gets duplicate message
- `test_name_error_cleared_before_validation` — label reset on each call
- `test_dest_error_cleared_before_validation` — label reset on each call
- `test_valid_inputs_call_create_project` — happy path proceeds to create_project
- `test_template_not_found_shows_messagebox` — messagebox on missing template
- `test_success_shows_info_messagebox` — success dialog after creation

## Known Limitations

- The trailing-period/space check in `validate_folder_name()` operates on the
  raw (unstripped) name. In practice `_on_create_project()` strips the name
  before passing it to the validator, so the check is defensive-only for direct
  API callers. This is by design from GUI-003 and is not changed here.
- Reserved-name-with-extension (e.g., `con.txt`) is not blocked because it is
  not listed in the WP acceptance criteria.
