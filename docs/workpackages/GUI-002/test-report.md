# Test Report — GUI-002

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 1

## Summary

All implementation requirements are met. `_format_template_name()`, `_get_template_options()`,
`list_templates()`, and the dropdown widget are correctly implemented and fully tested.
The developer's 25 tests all pass. Six additional edge-case tests added by the Tester Agent
also pass. Full suite of 31/31 pass; no regressions introduced (11 pre-existing failures in
INS-004, INS-012, SAF-010 are unrelated and unchanged).

The developer's dev-log claimed TST-487–TST-512 were logged in test-results.csv, but those
entries were absent from the CSV. Results have been logged as TST-481–TST-511 in this review.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_single_word_capitalised | Unit | Pass | "coding" → "Coding" |
| test_hyphenated_to_title_case | Unit | Pass | "creative-marketing" → "Creative Marketing" |
| test_underscore_separator | Unit | Pass | "data_science" → "Data Science" |
| test_mixed_hyphen_and_underscore | Unit | Pass | "my-data_project" → "My Data Project" |
| test_empty_string | Unit | Pass | "" → "" |
| test_already_title_case | Unit | Pass | "Coding" → "Coding" |
| test_all_caps | Unit | Pass | "CODING" → "Coding" |
| test_returns_list | Unit | Pass | _get_template_options returns list |
| test_with_two_subdirs | Unit | Pass | two mocked dirs → two formatted names |
| test_with_single_subdir | Unit | Pass | one dir → one formatted name |
| test_empty_list_returns_empty_list | Unit | Pass | no dirs → [] |
| test_files_are_not_included_only_dirs | Unit | Pass | pass-through from list_templates |
| test_results_preserve_order_from_list_templates | Unit | Pass | order preserved |
| test_returns_only_subdirectory_names | Integration | Pass | files in templates/ excluded |
| test_files_excluded | Integration | Pass | txt file not in results |
| test_empty_dir_returns_empty_list | Integration | Pass | empty dir → [] |
| test_missing_dir_returns_empty_list | Integration | Pass | non-existent path → [] |
| test_results_are_sorted_alphabetically | Integration | Pass | sorted output verified |
| test_dropdown_created_with_values_from_get_template_options | Integration | Pass | CTkOptionMenu receives dynamic values |
| test_adding_new_template_dir_changes_options | Integration | Pass | new subdir reflected immediately |
| test_dropdown_values_not_hardcoded | Integration | Pass | custom type appears in options |
| test_creative_marketing_dir_exists | Unit | Pass | templates/creative-marketing/ on disk |
| test_coding_dir_exists | Unit | Pass | templates/coding/ on disk |
| test_real_templates_dir_options_contain_coding | Integration | Pass | "Coding" in real options |
| test_real_templates_dir_options_contain_creative_marketing | Integration | Pass | "Creative Marketing" in real options |
| test_format_template_name_unicode_chars (Tester) | Unit | Pass | "café-design" → "Café Design" |
| test_format_template_name_numbers_prefix (Tester) | Unit | Pass | "3d-modeling" → "3D Modeling" |
| test_format_template_name_only_hyphens (Tester) | Unit | Pass | "---" → "   " |
| test_format_template_name_leading_dot (Tester) | Unit | Pass | ".hidden" → ".Hidden" |
| test_list_templates_file_path_returns_empty_list (Tester) | Unit | Pass | file path → [] (graceful) |
| test_list_templates_string_argument_returns_empty_list (Tester) | Unit | Pass | str not Path → [] (type guard) |

**Total: 31/31 passed**

## Bugs Found

None.

## TODOs for Developer

None.

## Verdict

PASS — mark WP as Done.
