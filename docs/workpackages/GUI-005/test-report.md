# Test Report — GUI-005

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 1

## Summary

Implementation is correct and complete. `_on_create_project()` in `app.py` satisfies all four acceptance criteria from US-005: the button is present (AC1), the template is copied to `<destination>/<folder_name>/` (AC2), a success dialog is shown (AC3), and error dialogs are shown on failure (AC4). The path-traversal guard in `create_project()` is verified working. All 42 tests pass with zero regressions across GUI tests.

**One coverage gap found and closed:** The Developer wrote 27 tests covering only the `_on_create_project()` handler via mocks. There were zero unit tests for the `create_project()` core function itself. Tester added 15 edge-case tests covering the real filesystem behaviour and additional handler edge cases.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TestOnCreateProjectClearsPreviousErrors::test_name_error_label_cleared_at_start | Unit | Pass | Dev |
| TestOnCreateProjectClearsPreviousErrors::test_destination_error_label_cleared_at_start | Unit | Pass | Dev |
| TestOnCreateProjectNameValidation::test_empty_name_shows_inline_error | Unit | Pass | Dev |
| TestOnCreateProjectNameValidation::test_invalid_name_shows_inline_error | Unit | Pass | Dev |
| TestOnCreateProjectNameValidation::test_invalid_name_does_not_call_create_project | Unit | Pass | Dev |
| TestOnCreateProjectNameValidation::test_invalid_name_does_not_show_destination_error | Unit | Pass | Dev |
| TestOnCreateProjectDestinationValidation::test_bad_destination_shows_inline_error | Unit | Pass | Dev |
| TestOnCreateProjectDestinationValidation::test_bad_destination_does_not_call_create_project | Unit | Pass | Dev |
| TestOnCreateProjectDestinationValidation::test_empty_destination_shows_inline_error | Unit | Pass | Dev |
| TestOnCreateProjectDuplicateFolder::test_duplicate_folder_shows_name_inline_error | Unit | Pass | Dev |
| TestOnCreateProjectDuplicateFolder::test_duplicate_folder_does_not_call_create_project | Unit | Pass | Dev |
| TestOnCreateProjectUnknownTemplate::test_unknown_template_shows_error_dialog | Unit | Pass | Dev |
| TestOnCreateProjectUnknownTemplate::test_unknown_template_does_not_call_create_project | Unit | Pass | Dev |
| TestOnCreateProjectSuccess::test_create_project_called_with_correct_args | Unit | Pass | Dev |
| TestOnCreateProjectSuccess::test_success_shows_info_dialog | Unit | Pass | Dev |
| TestOnCreateProjectSuccess::test_success_info_dialog_mentions_project_name | Unit | Pass | Dev |
| TestOnCreateProjectSuccess::test_success_does_not_show_error_dialog | Unit | Pass | Dev |
| TestOnCreateProjectSuccess::test_success_no_inline_errors_set | Unit | Pass | Dev |
| TestOnCreateProjectSuccess::test_multiword_template_reverse_mapped_correctly | Unit | Pass | Dev |
| TestOnCreateProjectCreationError::test_create_project_exception_shows_error_dialog | Unit | Pass | Dev |
| TestOnCreateProjectCreationError::test_create_project_exception_message_passed_to_dialog | Unit | Pass | Dev |
| TestOnCreateProjectCreationError::test_create_project_exception_does_not_show_info_dialog | Unit | Pass | Dev |
| TestOnCreateProjectCreationError::test_create_project_oserror_shows_error_dialog | Unit | Pass | Dev |
| TestAppModuleStructure::test_create_project_imported_in_app | Unit | Pass | Dev |
| TestAppModuleStructure::test_messagebox_imported_in_app | Unit | Pass | Dev |
| TestAppModuleStructure::test_path_imported_in_app | Unit | Pass | Dev |
| TestAppModuleStructure::test_on_create_project_is_callable | Unit | Pass | Dev |
| TestCreateProjectCoreFunction::test_returns_correct_target_path | Unit | Pass | Tester |
| TestCreateProjectCoreFunction::test_files_are_actually_copied | Integration | Pass | Tester — proves real copy occurs |
| TestCreateProjectCoreFunction::test_nonexistent_template_raises_valueerror | Unit | Pass | Tester |
| TestCreateProjectCoreFunction::test_template_is_file_not_dir_raises_valueerror | Unit | Pass | Tester |
| TestCreateProjectCoreFunction::test_nonexistent_destination_raises_valueerror | Unit | Pass | Tester |
| TestCreateProjectCoreFunction::test_path_traversal_in_folder_name_raises_valueerror | Security | Pass | Tester — ../../etc blocked |
| TestCreateProjectCoreFunction::test_path_traversal_dotdot_slash_raises_valueerror | Security | Pass | Tester — ../sibling blocked |
| TestCreateProjectCoreFunction::test_existing_target_directory_raises_error | Unit | Pass | Tester — FileExistsError propagates |
| TestCreateProjectCoreFunction::test_created_directory_is_relative_to_destination | Security | Pass | Tester — output is always within dest |
| TestOnCreateProjectHandlerEdgeCases::test_generic_runtime_error_shows_error_dialog | Unit | Pass | Tester — any Exception caught |
| TestOnCreateProjectHandlerEdgeCases::test_project_name_whitespace_stripped_before_use | Unit | Pass | Tester |
| TestOnCreateProjectHandlerEdgeCases::test_empty_template_list_shows_error | Unit | Pass | Tester |
| TestOnCreateProjectHandlerEdgeCases::test_success_info_dialog_includes_created_path | Unit | Pass | Tester — path shown to user |
| TestOnCreateProjectHandlerEdgeCases::test_destination_whitespace_stripped_before_use | Unit | Pass | Tester |
| TestOnCreateProjectHandlerEdgeCases::test_create_project_exception_does_not_show_success | Unit | Pass | Tester — PermissionError shows error not success |

## Bugs Found

None.

## TODOs for Developer

None.

## Verdict

PASS — mark WP as Done.
