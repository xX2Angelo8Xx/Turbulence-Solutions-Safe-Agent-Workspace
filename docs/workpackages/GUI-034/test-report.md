# Test Report — GUI-034

**Tester:** Tester Agent  
**Date:** 2026-04-06  
**Iteration:** 3

---

## Summary

Iteration 3 resolves the single remaining regression found in Iteration 2.
The SAF-034 test `test_on_create_project_proceeds_when_shim_ok` now passes after the Developer:
- Added `_window`, `create_button`, `browse_button`, `create_progress_bar` mocks to the bare instance.
- Added `_SyncThread` inline and patched `launcher.gui.app.threading.Thread` with it.
- Set `_window.after.side_effect = lambda ms, cb: cb()` so the completion callback fires synchronously.

All 166 WP-specific tests pass. No new regressions were introduced. All 5 acceptance criteria
from US-079 are satisfied.

**Verdict: PASS — marking WP as Done.**

---

## Tests Executed

| Test Suite | Type | Logged As | Result | Notes |
|-----------|------|-----------|--------|-------|
| `tests/GUI-034/` (24 tests) | Unit | TST-2700 | PASS | All WP-specific progress bar tests |
| `tests/GUI-034/ + GUI-005 + GUI-006 + GUI-012 + SAF-034 + FIX-072` (166 tests) | Unit | Manual | PASS | Full WP-impacted suite; 166 passed, 0 failed |
| Full regression suite | Regression | TST-2699 | Baseline | 248 failures all pre-existing per regression-baseline.json |

### Acceptance Criteria Verification (US-079)

| AC | Requirement | Status | Test |
|----|------------|--------|------|
| 1 | Indeterminate progress bar appears during creation | PASS | `test_set_creation_ui_state_shows_progress_bar` |
| 2 | Create button disabled during creation | PASS | `test_set_creation_ui_state_disables` |
| 3 | Project name + destination inputs disabled | PASS | `test_set_creation_ui_state_disables` |
| 4 | Progress bar hides and button re-enables on completion | PASS | `test_set_creation_ui_state_hides_progress_bar`, `test_on_creation_complete_re_enables_ui` |
| 5 | Success/error messagebox still appears | PASS | `test_on_creation_complete_success_shows_info`, `test_on_creation_complete_failure_shows_error` |

### Iteration 3 Regression Fixed

| Test | File | Iteration 2 Failure | Iteration 3 Result |
|------|------|--------------------|--------------------|
| `test_on_create_project_proceeds_when_shim_ok` | `tests/SAF-034/test_saf034.py` | `AttributeError: App has no attribute create_button` | PASS |

### Full Regression Suite Analysis

The full suite run (TST-2699) reported 248 failed + 96 errors. Cross-referencing with
`tests/regression-baseline.json` (261 known failures):
- All failures are either in the known baseline or are pre-existing issues on the main branch
  unrelated to GUI-034 (e.g. manifest staleness in MNT-029/FIX-114, template duplicate in FIX-119).
- GUI-034 only changes `src/launcher/gui/app.py` and test files — it cannot affect manifests,
  CI pipeline YAML, or template files.
- Three unbaselined failures (MNT-029, FIX-114, FIX-119) are pre-existing on `main` and were
  present prior to this branch.

---

## Bugs Found

- BUG-204 (logged in Iteration 2): SAF-034 `test_on_create_project_proceeds_when_shim_ok` —
  missing widget attrs after threading refactor. **Resolved** in Iteration 3. Status updated
  to `Closed`.
- No new bugs found in Iteration 3.

### Workspace Validation Warning

`validate_workspace.py --wp GUI-034` passes with one warning:
> `BUG-204 referenced in GUI-034 dev-log/test-report but Fixed In WP is empty or doesn't match`

The Developer did not populate `Fixed In WP: GUI-034` on BUG-204 (no tooling exists to set this
field after creation). The bug is now Closed and the fix is in place — this is a tracking artifact
only and does not block the PASS.

---

## TODOs for Developer

None.

---

## Verdict

**PASS — mark WP as Done.**
