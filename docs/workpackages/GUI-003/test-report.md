# Test Report — GUI-003

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 2

## Summary

GUI-003 Iteration 2 is **PASS**. Both blocking issues from Iteration 1 are confirmed fixed:
- **BUG-017 (app.py not on disk)**: `src/launcher/gui/app.py` now contains the validation import, `project_name_error_label` widget (with `text=""`, `text_color="red"`), row-shifted widgets (type→row 2, destination→row 3, checkbox→row 4, button→row 5), and `_WINDOW_HEIGHT = 370`. Both App widget tests pass.
- **BUG-018 (no 255-char guard)**: `validate_folder_name()` now rejects names where `len(stripped) > 255`. `test_name_length_256_invalid` passes.

All 52 GUI-003 tests pass (1 skipped on Windows — symlink elevation). Three new Tester edge-case tests were added in this iteration. Full regression suite: 337 pass / 3 pre-existing failures / 1 skip — no new regressions.

## Tests Executed

### Developer + Iteration 1 Tester tests (49 tests, 1 skip)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_valid_simple_name | Unit | PASS | |
| test_valid_name_with_numbers | Unit | PASS | |
| test_valid_name_with_underscores | Unit | PASS | |
| test_valid_name_with_hyphens | Unit | PASS | |
| test_return_type_is_tuple | Unit | PASS | |
| test_valid_returns_empty_message | Unit | PASS | |
| test_unicode_accented_chars_valid | Unit | PASS | Ünïcödé-style names accepted |
| test_emoji_in_name_valid | Unit | PASS | Emoji names accepted |
| test_leading_dot_valid | Unit | PASS | .hidden-style names accepted |
| test_name_length_255_valid | Unit | PASS | Exactly 255 chars accepted |
| test_empty_string_invalid | Unit | PASS | |
| test_whitespace_only_invalid | Unit | PASS | |
| test_invalid_returns_nonempty_message | Unit | PASS | |
| test_colon_invalid | Unit | PASS | |
| test_backslash_invalid | Unit | PASS | |
| test_forward_slash_invalid | Unit | PASS | |
| test_asterisk_invalid | Unit | PASS | |
| test_question_mark_invalid | Unit | PASS | |
| test_pipe_invalid | Unit | PASS | |
| test_less_than_invalid | Unit | PASS | |
| test_greater_than_invalid | Unit | PASS | |
| test_double_quote_invalid | Unit | PASS | |
| test_null_byte_invalid | Unit | PASS | |
| test_control_char_invalid | Unit | PASS | |
| test_tab_char_invalid | Unit | PASS | Tab (0x09) rejected |
| test_single_dot_invalid | Unit | PASS | |
| test_double_dot_invalid | Unit | PASS | |
| test_windows_reserved_con_uppercase_invalid | Unit | PASS | |
| test_windows_reserved_nul_lowercase_invalid | Unit | PASS | |
| test_windows_reserved_case_insensitive | Unit | PASS | |
| test_windows_reserved_com9_invalid | Unit | PASS | |
| test_windows_reserved_lpt1_invalid | Unit | PASS | |
| test_windows_reserved_prn_invalid | Unit | PASS | |
| test_windows_reserved_aux_invalid | Unit | PASS | |
| test_name_ending_with_dot_invalid | Unit | PASS | |
| test_name_ending_with_space_invalid | Unit | PASS | |
| test_name_length_256_invalid | Unit | PASS | BUG-018 fix confirmed |
| test_path_traversal_with_slash_rejected | Security | PASS | |
| test_path_traversal_backslash_rejected | Security | PASS | |
| test_null_byte_before_reserved_rejected | Security | PASS | |
| test_control_char_bypass_rejected | Security | PASS | |
| test_nonexistent_folder_returns_false | Unit | PASS | |
| test_existing_folder_returns_true | Unit | PASS | |
| test_empty_name_returns_false | Unit | PASS | |
| test_empty_destination_returns_false | Unit | PASS | |
| test_both_empty_returns_false | Unit | PASS | |
| test_existing_file_at_target_returns_true | Unit | PASS | File collision blocked |
| test_symlink_to_existing_dir_returns_true | Unit | SKIP | Elevated privileges required on Windows |
| test_project_name_error_label_exists | Unit | PASS | BUG-017 fix confirmed |
| test_error_label_created_with_empty_text | Unit | PASS | BUG-017 fix confirmed |

### Iteration 2 Tester edge-case tests (3 new)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_digits_only_name_valid | Unit | PASS | "123" is a valid folder name |
| test_carriage_return_invalid | Unit | PASS | `\r` (0x0D) explicitly rejected as control char |
| test_newline_char_invalid | Unit | PASS | `\n` (0x0A) explicitly rejected as control char |

### Full regression suite

| Suite | Tests | Pass | Fail | Skip | Notes |
|-------|-------|------|------|------|-------|
| GUI-003 isolated (Iteration 2) | 53 | 52 | 0 | 1 | 1 SKIP = symlink on Windows |
| Full suite (excl. In-Progress WPs) | 341 | 337 | 3 | 1 | 3 pre-existing failures; no GUI-003 failures |

## Pre-existing failures (NOT caused by GUI-003)

- `tests/INS-012/test_ins012_gitignore.py::test_gitignore_git_recognises_spec` — `launcher.spec` is tracked in git so `.gitignore` rule does not hide it; pre-existing since INS-003 added the file.
- `tests/SAF-003/test_saf003_tool_parameter_validation.py::test_validate_include_pattern_brace_expansion_github_vscode` — SAF-003 brace-expansion gap; SAF-003 WP in Review.
- `tests/SAF-003/test_saf003_tool_parameter_validation.py::test_grep_search_brace_expansion_github_vscode_blocked` — same SAF-003 brace-expansion gap.

## Bugs Found

None new. Both bugs from Iteration 1 are resolved:
- GUI-003 "BUG-017" (per Iteration 1 test report): app.py changes saved to disk — **FIXED**
- GUI-003 "BUG-018" (per Iteration 1 test report): 255-char length guard added — **FIXED**

**Note on bug ID collision**: The Iteration 1 test report referenced "BUG-017" and "BUG-018" for GUI-003 issues, but these IDs were subsequently assigned to INS-004 bugs in bugs.csv. The GUI-003–specific issues were never formally logged in bugs.csv under any ID. This is a data-integrity gap (tracked as BUG-019 in the Iteration 1 report, also never formally logged). No new action required — the underlying issues are fixed.

## TODOs for Developer

None — all Iteration 1 blocking issues are resolved.

## Verdict

**PASS** — Mark WP as **Done**.

`validate_folder_name()` correctly rejects empty names, special characters, dot/double-dot, Windows reserved names, trailing dot/space, and names > 255 characters. `check_duplicate_folder()` correctly detects pre-existing directories and files. `App.project_name_error_label` is present on disk with the correct widget parameters and grid placement. 52/53 tests pass; 1 skip is platform-expected (symlink elevation on Windows). Zero regressions in full suite.

