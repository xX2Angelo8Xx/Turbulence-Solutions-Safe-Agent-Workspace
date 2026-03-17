# Test Report — DOC-003

**Tester:** Tester Agent
**Date:** 2026-03-17
**Iteration:** 1

## Summary

DOC-003 updates both copilot-instructions.md template files to replace the hardcoded `` `Project/` `` folder reference with the `{{PROJECT_NAME}}` placeholder. The implementation is minimal and correct: exactly one line changed in two files, both files remain in sync, and the `replace_template_placeholders()` function from DOC-001 correctly substitutes the token at project creation time.

All 6 developer tests pass. Tester added 11 edge-case tests covering placeholder count exactness, immutability of literal folder names (NoAgentZone, .github, .vscode), replacement with various valid project name formats, placement in the correct section, and UTF-8 BOM hygiene. All 17 tests pass. No new regressions introduced.

## Acceptance Criteria Check (US-023)

| AC | Requirement | Status |
|----|-------------|--------|
| AC 2 | copilot-instructions.md references the actual project folder name instead of hardcoded "Project" | **PASS** — `{{PROJECT_NAME}}` replaces the hardcoded reference |

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_default_project_uses_placeholder | Unit | Pass | ✓ {{PROJECT_NAME}} present in Default-Project file |
| test_default_project_no_bare_project_folder | Unit | Pass | ✓ No backtick-quoted `Project/` literal remains |
| test_templates_coding_uses_placeholder | Unit | Pass | ✓ {{PROJECT_NAME}} present in templates/coding file |
| test_templates_coding_no_bare_project_folder | Unit | Pass | ✓ No backtick-quoted `Project/` literal remains |
| test_files_are_identical | Unit | Pass | ✓ Both files byte-for-byte identical |
| test_placeholder_replaced_in_copy | Integration | Pass | ✓ Simulated replacement produces correct output |
| test_placeholder_count_exactly_one_in_default_project (Tester) | Unit | Pass | ✓ Exactly 1 placeholder in Default-Project file |
| test_placeholder_count_exactly_one_in_templates_coding (Tester) | Unit | Pass | ✓ Exactly 1 placeholder in templates/coding file |
| test_noagentzone_reference_unchanged_in_default_project (Tester) | Unit | Pass | ✓ `NoAgentZone/` remains literal |
| test_github_reference_unchanged_in_default_project (Tester) | Unit | Pass | ✓ `.github/` remains literal |
| test_vscode_reference_unchanged_in_default_project (Tester) | Unit | Pass | ✓ `.vscode/` remains literal |
| test_placeholder_is_in_workspace_rules_section (Tester) | Unit | Pass | ✓ Placeholder is under the Workspace Rules heading |
| test_replacement_with_hyphenated_project_name (Tester) | Unit | Pass | ✓ My-Cool-Project replaces correctly |
| test_replacement_with_underscored_project_name (Tester) | Unit | Pass | ✓ my_project_42 replaces correctly |
| test_replacement_with_numeric_suffix_project_name (Tester) | Unit | Pass | ✓ Project2025 replaces correctly |
| test_default_project_file_has_no_bom (Tester) | Unit | Pass | ✓ No UTF-8 BOM in Default-Project file |
| test_templates_coding_file_has_no_bom (Tester) | Unit | Pass | ✓ No UTF-8 BOM in templates/coding file |
| Full DOC-003 suite (17 tests) — Tester run | Regression | Pass | 17/17 pass |
| Full regression suite (3087 pass / 2 pre-existing fail) | Regression | Pass | 2 pre-existing: FIX-009 dup TST-1557 (GUI-017 issue) + INS-005 BUG-045 |

## Bugs Found

None.

## TODOs for Developer

None.

## Verdict

PASS — mark WP as Done.
