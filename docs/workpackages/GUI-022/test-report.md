# Test Report — GUI-022

**Tester:** Tester Agent
**Date:** 2026-03-25
**Iteration:** 1

---

## Summary

The implementation is functionally correct: the "Include README files" `CTkCheckBox` is present, defaults to `True`, persists state via `get_setting`/`set_setting`, and passes `include_readmes` to `create_project()`. All 20 GUI-022-specific tests pass (12 Developer + 8 Tester edge cases).

**However, the WP cannot be approved.** GUI-022 introduced **8 regressions** in pre-existing test suites (GUI-001, GUI-011, GUI-012). These tests encoded assumptions about a single `CTkCheckBox` and a window height of 590 that are no longer valid. The Developer must update those tests before this WP can be marked Done.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| GUI-022 developer suite (12 tests) | Unit | Pass | All 12 original tests pass |
| GUI-022 edge cases (8 tests) | Unit | Pass | Added by Tester — see below |
| GUI-001 / GUI-011 / GUI-012 regression check | Regression | **FAIL** | 8 regressions — see Bugs Found |
| Full suite (yaml-import modules excluded) | Regression | Fail (pre-existing) | 70 pre-existing failures unrelated to GUI-022; 8 new failures caused by GUI-022 |

### Tester Edge Cases Added (`tests/GUI-022/test_gui022_edge_cases.py`)

| Test | Rationale |
|------|-----------|
| `test_get_setting_raises_propagates_from_init` | `get_setting` unavailable — exception must not be silently swallowed |
| `test_truthy_int_one_initialises_bool_var_true` | Non-bool truthy value (1) must be coerced to True |
| `test_falsy_int_zero_initialises_bool_var_false` | Non-bool falsy value (0) must be coerced to False |
| `test_none_from_settings_initialises_bool_var_false` | `None` from settings → `bool(None)` = False |
| `test_two_toggles_each_call_set_setting` | Rapid toggling — each toggle persists the current state |
| `test_set_setting_exception_propagates_from_toggle` | `set_setting` raises — must propagate, not silence |
| `test_include_readmes_true_passed_as_exact_bool` | Value forwarded to `create_project` is un-modified |
| `test_toggle_does_not_call_create_project` | Toggle must only persist, never create a project |

---

## Bugs Found

- **BUG-104**: GUI-022: 8 pre-existing tests broken by new checkbox and window-height change (logged in `docs/bugs/bugs.csv`)

---

## TODOs for Developer

The following **8 tests** in existing test files must be updated. All fixes are isolated to those specific assertion lines — no source-code changes are needed.

### `tests/GUI-001/test_gui001_main_window.py`

1. **`test_open_in_vscode_checkbox_created`** (≈line 134)
   - **Problem:** `_CTK_MOCK.CTkCheckBox.assert_called_once()` fails because GUI-022 added a second `CTkCheckBox`.
   - **Fix:** Replace `assert_called_once()` with `assert _CTK_MOCK.CTkCheckBox.call_count >= 2` (or exactly 2 if no further checkboxes are planned).

2. **`test_open_in_vscode_checkbox_text`** (≈line 140)
   - **Problem:** `CTkCheckBox.call_args` returns the **last** call ("Include README files"), not "Open in VS Code".
   - **Fix:** Search all calls:
     ```python
     calls = _CTK_MOCK.CTkCheckBox.call_args_list
     assert any("Open in VS Code" in str(c) for c in calls)
     ```

### `tests/GUI-011/test_gui011_color_theme.py`

3. **`test_checkbox_text_color`** (≈line 147)
   - **Problem:** `assert len(calls) == 1` fails; there are now 2 `CTkCheckBox` calls.
   - **Fix:** Replace count assertion with style validation across all checkboxes:
     ```python
     from launcher.config import COLOR_TEXT
     calls = _CTK_MOCK.CTkCheckBox.call_args_list
     assert len(calls) == 2
     assert all(c.kwargs.get("text_color") == COLOR_TEXT for c in calls)
     ```

4. **`test_checkbox_fg_color`** (≈line 153)
   - **Problem:** Same as above (`len(calls) == 1` fails).
   - **Fix:**
     ```python
     from launcher.config import COLOR_SECONDARY
     calls = _CTK_MOCK.CTkCheckBox.call_args_list
     assert len(calls) == 2
     assert all(c.kwargs.get("fg_color") == COLOR_SECONDARY for c in calls)
     ```

### `tests/GUI-012/test_gui012_spacing.py`

5. **`test_window_height_is_440`** (≈line 40)
   - **Problem:** Asserts `"590" in geometry_call`; GUI-022 changed height to 630.
   - **Fix:** Change `"590"` → `"630"`. (Also consider renaming the test to `test_window_height_is_630`.)

6. **`test_create_button_pady_at_least_10`** (≈line 72)
   - **Problem:** Searches for grid call with `row == 7`; Create Project button is now at `row=8` (shifted by the new checkbox row).
   - **Fix:** Change `row == 7` → `row == 8`.

7. **`test_checkbox_pady_at_least_10`** (≈line 83)
   - **Problem:** `checkbox_instance.grid.call_args` returns the **last** `.grid()` call — the "Include README files" checkbox with `pady=(0, 6)`. `any(v >= 10 for v in (0, 6))` is `False`.
   - **Fix:** Target the first checkbox (Open in VS Code) whose `pady=10` satisfies the test, or accept that the second checkbox uses a tighter top-padding and assert per-checkbox. Simplest fix: check the first `.grid()` call on the checkbox instance:
     ```python
     grid_call = checkbox_instance.grid.call_args_list[0]
     ```

8. **`test_create_button_sticky_ew`** (≈line 122)
   - **Problem:** Finds grid call with `row == 7`; Create Project button grid call is now `row=8`.
   - **Fix:** Change `row == 7` → `row == 8`.

---

## Verdict

**FAIL — Return to Developer**

8 regression failures in existing test suites (GUI-001, GUI-011, GUI-012). The implementation is correct; only the outdated test assertions need updating. See TODOs above for exact line-by-line fixes. Once those 8 tests pass, re-run the full suite to confirm no remaining regressions, then hand off to Tester again.
