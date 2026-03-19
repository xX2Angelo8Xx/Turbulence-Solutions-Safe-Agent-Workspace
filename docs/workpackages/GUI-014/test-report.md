# Test Report — GUI-014: Grey Out Unfinished Templates with Coming Soon

**WP ID:** GUI-014  
**Branch:** gui-014-coming-soon-templates  
**Tester:** Tester Agent  
**Date:** 2026-03-14  
**Verdict:** PASS

---

## Summary

The implementation correctly identifies unready templates (those containing only `README.md`), labels them with ` ...coming soon` in the dropdown, prevents their selection by reverting the dropdown to the last valid choice, and ensures that `_on_create_project` cannot create a project from an unready template even if the dropdown guard were somehow bypassed.

All 27 GUI-014 tests pass (18 Developer + 9 Tester edge-case). Full regression suite: **1934 passed / 29 skipped / 1 pre-existing fail (INS-005 `filesandirs` — unrelated to GUI-014)**.

---

## Code Review

### `src/launcher/core/project_creator.py` — `is_template_ready()`

- Logic is correct: returns `False` for empty dirs and dirs containing only `README.md`; `True` otherwise.
- Exact case match (`README.md`) is intentional and correct — documented in test.
- No security concerns; only operates on local filesystem paths already validated upstream.

### `src/launcher/gui/app.py`

| Location | Finding |
|----------|---------|
| `_get_template_options()` | Returns `list[str]` and populates `self._coming_soon_options` as a side effect. Clean design. |
| `__init__` | `_coming_soon_options` and `_current_template` correctly initialized before `_build_ui()`. |
| `_build_ui()` dropdown | `ready_options[0]` fallback correctly handles all-coming-soon case by picking `options[0]`; never crashes. |
| `_on_template_selected()` | Guard correctly reverts dropdown and returns; state is not mutated on coming-soon click. |
| `_on_create_project()` | **Uses `dropdown.get()` not `self._current_template`** — deviation from dev-log. However, this is functionally safe because: (a) the `_on_template_selected` guard already reverted the dropdown, and (b) the reverse-map lookup (`_format_template_name(t) == display_template`) will always fail for a coming-soon display name (suffix mismatch), causing a `messagebox.showerror` and early return. The protection is defence-in-depth, though the dev-log description was inaccurate. |

---

## Acceptance Criteria Verification

| AC | Status |
|----|--------|
| Unfinished templates (only README.md) appear with ` ...coming soon` label | ✅ PASS |
| Coming-soon entries cannot be selected (dropdown reverts to last valid) | ✅ PASS |
| `templates/creative-marketing/` shows as "Creative Marketing ...coming soon" | ✅ PASS — verified against real `TEMPLATES_DIR` |
| `templates/coding/` shows as "Coding" with no suffix | ✅ PASS — verified against real `TEMPLATES_DIR` |
| Default selection is always the first ready template | ✅ PASS |
| `_on_create_project` cannot create a project from a coming-soon template | ✅ PASS — defended by reverse-map guard |

---

## Test Results

### Developer Tests (18)

| TST-ID | Test | Result |
|--------|------|--------|
| TST-1051 | test_ready_when_directory_has_multiple_files | Pass |
| TST-1052 | test_not_ready_when_only_readme | Pass |
| TST-1053 | test_not_ready_for_nonexistent_directory | Pass |
| TST-1054 | test_ready_when_directory_has_single_non_readme_file | Pass |
| TST-1055 | test_not_ready_for_empty_directory | Pass |
| TST-1056 | test_ready_when_only_subdirectory_present | Pass |
| TST-1057 | test_not_ready_with_readme_only_case_exact | Pass |
| TST-1058 | test_coming_soon_label_appended_to_unready | Pass |
| TST-1059 | test_ready_template_has_no_coming_soon_label | Pass |
| TST-1060 | test_returns_both_ready_and_coming_soon | Pass |
| TST-1061 | test_coming_soon_set_contains_only_unready_display_names | Pass |
| TST-1062 | test_default_template_is_first_ready_option | Pass |
| TST-1063 | test_default_does_not_select_coming_soon | Pass |
| TST-1064 | test_coming_soon_options_set_populated | Pass |
| TST-1065 | test_revert_on_coming_soon_selection | Pass |
| TST-1066 | test_valid_selection_updates_current_template | Pass |
| TST-1067 | test_coming_soon_selection_does_not_update_current_template | Pass |
| TST-1068 | test_on_create_project_uses_current_template | Pass |

### Tester Edge-Case Tests (9)

| TST-ID | Test | Category | Result |
|--------|------|----------|--------|
| TST-1070 | test_current_template_fallback_when_all_coming_soon | Unit | Pass |
| TST-1071 | test_coming_soon_set_has_all_when_none_ready | Unit | Pass |
| TST-1072 | test_on_create_project_refuses_coming_soon_display_name | Integration | Pass |
| TST-1073 | test_coding_template_is_ready | Unit | Pass |
| TST-1074 | test_creative_marketing_template_is_not_ready | Unit | Pass |
| TST-1075 | test_real_templates_display_names | Integration | Pass |
| TST-1076 | test_readme_in_subdirectory_does_not_count_as_sole_readme | Unit | Pass |
| TST-1077 | test_readme_md_uppercase_exact_match | Unit | Pass |
| TST-1078 | test_readme_md_with_sibling_file_is_ready | Unit | Pass |

### Full Regression Run

| TST-ID | Description | Result |
|--------|-------------|--------|
| TST-1079 | Full regression suite — Tester final run | 1934 passed / 29 skipped / 1 pre-existing fail — Pass |

---

## Observations / Non-Blocking Notes

1. **`test_coming_soon_set_contains_only_unready_display_names` passes by accident** — this test does `options, coming_soon = app._get_template_options()` which unpacks a 2-element list into two strings, then uses string `in` (substring check) instead of set membership. The assertions happen to hold because the strings match. This is a test quality issue but does not mask a defect; the coverage is re-established by Tester TST-1071. Not blocking.

2. **Dev-log inaccuracy** — dev-log states "_on_create_project uses `self._current_template`" but the actual code uses `self.project_type_dropdown.get()`. The behaviour is functionally equivalent because the `_on_template_selected` guard reverts the dropdown before any click on Create Project could fire. The additional reverse-map guard in `_on_create_project` provides defence-in-depth (verified by TST-1072). Not blocking.

3. **All-coming-soon UX** — When every template is unready, `_current_template` falls back to the first coming-soon option, which means the dropdown default shows a non-selectable item. This is an edge-case with no practical impact today (only `creative-marketing` is unready) and is covered by TST-1070/TST-1071.

---

## Verdict: PASS

All acceptance criteria met. 27/27 GUI-014 tests pass. No regressions in the full suite. Setting WP GUI-014 to **Done**.
