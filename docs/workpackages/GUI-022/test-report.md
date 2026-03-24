# Test Report — GUI-022

**Tester:** Tester Agent
**Date:** 2026-03-25
**Iteration:** 2

---

## Summary

**Iteration 2 re-test: PASS.** All 8 regression failures from Iteration 1 have been fixed by the Developer. The implementation is functionally correct and all 99 tests in GUI-001, GUI-011, GUI-012, and GUI-022 now pass. The 70 failures visible in the broader suite are pre-existing on `main` (code-signing CI scripts, yaml-dependent tests) and are unrelated to this WP.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| GUI-022 developer suite (11 tests) | Unit | Pass | All developer-written tests pass |
| GUI-022 edge cases (8 tests) | Unit | Pass | Added by Tester in Iteration 1 — still pass |
| GUI-001 regression check | Regression | **Pass** | Previously failing `test_open_in_vscode_checkbox_created`, `test_open_in_vscode_checkbox_text` now pass |
| GUI-011 regression check | Regression | **Pass** | Previously failing `test_checkbox_text_color`, `test_checkbox_fg_color` now pass |
| GUI-012 regression check | Regression | **Pass** | Previously failing `test_window_height_is_440`, `test_create_button_pady_at_least_10`, `test_checkbox_pady_at_least_10`, `test_create_button_sticky_ew` now pass |
| GUI-001 / GUI-011 / GUI-012 / GUI-022 combined | Regression | Pass | 99 passed, 0 failed |
| Full suite (yaml-import modules excluded) | Regression | 70 pre-existing failures | All 70 exist identically on `main` — confirmed not introduced by this WP; 5317 pass |

### Tester Edge Cases (carried from Iteration 1, still passing)

| Test | Result |
|------|--------|
| `test_get_setting_raises_propagates_from_init` | Pass |
| `test_truthy_int_one_initialises_bool_var_true` | Pass |
| `test_falsy_int_zero_initialises_bool_var_false` | Pass |
| `test_none_from_settings_initialises_bool_var_false` | Pass |
| `test_two_toggles_each_call_set_setting` | Pass |
| `test_set_setting_exception_propagates_from_toggle` | Pass |
| `test_include_readmes_true_passed_as_exact_bool` | Pass |
| `test_toggle_does_not_call_create_project` | Pass |

---

## Bugs Found

- **BUG-104**: Fixed in this WP — closing. (8 regression failures in GUI-001/011/012 caused by GUI-022's new checkbox and height change; all resolved in Iteration 2.)

---

## TODOs for Developer

None.

---

## Verdict

**PASS — Mark WP as Done**

All 99 GUI-001/011/012/022 tests pass. No new regressions introduced. Implementation satisfies all acceptance criteria from US-039 (ACs 1 and 6).
