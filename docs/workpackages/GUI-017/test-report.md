# Test Report — GUI-017: Update UI Labels and Validation for New Naming Convention

## Verdict: PASS

## Tester
Tester Agent

## Date
2026-03-17

---

## Summary

All requirements for GUI-017 are correctly implemented and verified. The UI now
communicates the `TS-SAE-{name}` naming convention accurately: placeholder text,
success messages, and duplicate-folder error messages all include the prefix.
The existing test coverage is thorough, and edge-case tests added by the Tester
confirm boundary conditions and guard against regressions.

---

## Requirements Verification

| Requirement | Verified | Notes |
|---|---|---|
| Placeholder text updated to `"MatlabDemo"` | ✓ | `app.py` line 111 confirms change from `"my-project"` |
| Success message shows `TS-SAE-{folder_name}` | ✓ | `app.py` line 318 — `f'Project "TS-SAE-{folder_name}" created successfully at:\n{created_path}'` |
| Duplicate folder check uses `TS-SAE-{folder_name}` | ✓ | `app.py` line 290 — `check_duplicate_folder(f"TS-SAE-{folder_name}", ...)` |
| Duplicate error label shows `TS-SAE-{name}` | ✓ | `app.py` line 292 — error label text includes full prefixed name |
| Old `"my-project"` placeholder removed | ✓ | Not found anywhere in the codebase |

---

## Test Runs

### Developer Tests (`tests/GUI-017/test_gui017_ui_labels.py`)

| Test | Result |
|---|---|
| `TestPlaceholderText::test_placeholder_text_is_matlab_demo` | PASS |
| `TestPlaceholderText::test_placeholder_is_not_old_value` | PASS |
| `TestSuccessMessage::test_success_message_contains_ts_sae_prefix` | PASS |
| `TestSuccessMessage::test_success_message_does_not_show_bare_name_only` | PASS |
| `TestSuccessMessage::test_success_message_shows_full_created_path` | PASS |
| `TestDuplicateFolderCheck::test_duplicate_check_called_with_ts_sae_prefix` | PASS |
| `TestDuplicateFolderCheck::test_duplicate_check_not_called_with_bare_name` | PASS |
| `TestDuplicateFolderCheck::test_duplicate_error_label_shows_ts_sae_prefix` | PASS |
| `TestDuplicateFolderCheck::test_duplicate_error_label_does_not_use_bare_name` | PASS |
| `TestEndToEndNaming::test_various_project_names_all_prefixed_in_success_message` | PASS |

### Tester Edge-Case Tests (`tests/GUI-017/test_gui017_edge_cases.py`)

| Test | Result |
|---|---|
| `TestEmptyNameHandling::test_empty_name_fails_validation_before_duplicate_check` | PASS |
| `TestEmptyNameHandling::test_empty_name_sets_error_label` | PASS |
| `TestEmptyNameHandling::test_whitespace_only_name_fails_validation` | PASS |
| `TestSpecialCharacterNames::test_special_char_name_fails_before_duplicate_check[Test@Project]` | PASS |
| `TestSpecialCharacterNames::test_special_char_name_fails_before_duplicate_check[My Project]` | PASS |
| `TestSpecialCharacterNames::test_special_char_name_fails_before_duplicate_check[Hello!World]` | PASS |
| `TestSpecialCharacterNames::test_special_char_name_fails_before_duplicate_check[foo/bar]` | PASS |
| `TestSpecialCharacterNames::test_special_char_name_fails_before_duplicate_check[dot.name]` | PASS |
| `TestSpecialCharacterNames::test_special_char_name_fails_before_duplicate_check[name#tag]` | PASS |
| `TestSpecialCharacterNames::test_special_char_error_label_does_not_contain_ts_sae` | PASS |
| `TestNoOldNamingArtifacts::test_success_message_does_not_contain_my_project_placeholder` | PASS |
| `TestNoOldNamingArtifacts::test_duplicate_error_does_not_use_old_bare_name_format` | PASS |
| `TestNoPrefixDoubling::test_name_starting_with_ts_sae_gets_double_prefix_in_duplicate_check` | PASS |

### Full Regression Suite

**Command:** `.venv\Scripts\python -m pytest tests/ --tb=short -q`
**Result:** 3010 passed, 29 skipped, 7 pre-existing failures (not related to GUI-017)

**Pre-existing failures (not caused by GUI-017):**
- `tests/FIX-009/` — 6 tests fail due to `UnicodeDecodeError` reading `test-results.csv` (non-UTF-8 character at byte 4541). Pre-existing issue.
- `tests/INS-005/test_ins005_edge_cases.py::TestShortcutsAndUninstaller::test_uninstall_delete_type_is_filesandirs` — Assertion about `filesandirs` vs `filesandordirs` in installer script. Pre-existing issue.

No new failures introduced by GUI-017.

---

## Edge-Case Analysis

| Scenario | Risk | Outcome |
|---|---|---|
| Empty project name | Validation catches it; duplicate check never fires | PASS |
| Whitespace-only name (`"   "`) | Stripped to empty, fails validation | PASS |
| Special characters (`@`, space, `/`, `!`, `.`, `#`) | Validation rejects before duplicate check | PASS |
| Validation error labels must not show `TS-SAE-` prefix | Confirmed — prefix only appears in duplicate/success messages | PASS |
| Old `"my-project"` placeholder artifact | Not present in any message path | PASS |
| User types `"TS-SAE-Foo"` — prefix doubling | Consistent behaviour: `TS-SAE-TS-SAE-Foo` (documented, no silent stripping) | Documented |

---

## Security Review

No security concerns. This WP touches only UI labels and string formatting in
`_on_create_project()`. No file I/O, subprocess calls, or user-controlled
data flows to sensitive sinks were modified.

---

## Bugs Found

None.

---

## Pre-Done Checklist

- [x] `docs/workpackages/GUI-017/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/GUI-017/test-report.md` written by Tester
- [x] Test files exist in `tests/GUI-017/` (2 files, 23 tests total)
- [x] All test runs logged in `docs/test-results/test-results.csv`
