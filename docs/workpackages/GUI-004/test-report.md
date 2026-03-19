# Test Report — GUI-004

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 1

## Summary

The implementation satisfies all WP-004 and US-004 (AC #4) requirements.
`validate_destination_path()` correctly handles all primary validation paths.
`destination_error_label` is present on the `App` instance at row 4 as documented.
The native OS dialog (`filedialog.askdirectory`) is wired to the Browse button.
Validation wiring into project-creation logic is intentionally deferred to GUI-005 — this is within WP scope.

16 Tester edge-case tests added across 5 categories; all pass.
Full regression suite: **553 passed / 33 failed-pre-existing / 1 skipped**. No regressions.

**Process note:** The `workpackages.csv` row for GUI-004 was found with status `Open` and `Assigned To` blank at handoff time. This is a workflow-step omission by the Developer (Steps 2 and 7 of `agent-workflow.md`). No functional gap — the dev-log, implementation, and tests are all present and correct. Corrected to `Done` by Tester.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_empty_string | Unit | Pass | TST-dev — empty input rejected |
| test_whitespace_only | Unit | Pass | TST-dev — whitespace-only rejected |
| test_nonexistent_path | Unit | Pass | TST-dev — non-existent path rejected |
| test_path_is_file_not_dir | Unit | Pass | TST-dev — file instead of dir rejected |
| test_valid_writable_dir | Unit | Pass | TST-dev — valid writable dir accepted |
| test_app_has_destination_error_label | Unit | Pass | TST-dev — attribute present on App |
| test_destination_error_label_created_with_empty_text | Unit | Pass | TST-dev — label initialised with empty text |
| test_single_space_rejected | Unit | Pass | TST-235 — single space rejected |
| test_leading_whitespace_on_valid_path_rejected | Unit | Pass | TST-236 — leading spaces → path not found |
| test_trailing_whitespace_no_crash | Unit | Pass | TST-237 — trailing spaces handled gracefully; on Windows OS strips trailing spaces silently (accepted); function does not crash |
| test_dir_with_spaces_in_name_accepted | Unit | Pass | TST-238 — spaces in directory name accepted |
| test_dir_with_unicode_chars_accepted | Unit | Pass | TST-239 — Unicode directory name accepted |
| test_dir_with_parentheses_accepted | Unit | Pass | TST-240 — parentheses in directory name accepted |
| test_dir_with_hyphens_and_underscores_accepted | Unit | Pass | TST-241 — hyphens/underscores accepted |
| test_dir_starting_with_dot_accepted | Unit | Pass | TST-242 — hidden-style directory accepted |
| test_long_segment_nonexistent_rejected | Unit | Pass | TST-243 — 200-char segment rejected gracefully |
| test_deeply_nested_nonexistent_path_rejected | Unit | Pass | TST-244 — 20-level deep path rejected gracefully |
| test_forward_slashes_accepted_on_windows | Cross-platform | Pass | TST-245 — forward slashes on Windows path accepted |
| test_none_input_rejected_without_crash | Unit | Pass | TST-246 — None input handled by `if not path` guard |
| test_return_is_two_tuple_for_valid_path | Unit | Pass | TST-247 — return type (bool, str) confirmed |
| test_return_is_two_tuple_for_invalid_path | Unit | Pass | TST-248 — return type (bool, str) confirmed |
| test_error_message_nonempty_when_rejected | Unit | Pass | TST-249 — error string is non-empty on False |
| test_error_message_empty_when_accepted | Unit | Pass | TST-250 — error string is "" on True |
| Full regression suite (553/33/1) | Regression | Pass | TST-251 — zero new failures; 553 pass; 33 pre-existing INS-004/INS-012 failures unrelated to GUI-004 |

## Bugs Found

None.

**Platform behaviour note (not a bug):** On Windows, the Win32 API silently strips trailing spaces from path strings. A caller passing `str(tmp_path) + "   "` will receive `(True, "")` because Windows resolves the path to the same underlying directory. On Linux/macOS, the same input returns `(False, "Destination path does not exist.")`. This is documented OS behaviour; no code change required. Test TST-341 captures this cross-platform difference.

## TODOs for Developer

None — no action required.

## Verdict

**PASS — mark WP as Done.**
