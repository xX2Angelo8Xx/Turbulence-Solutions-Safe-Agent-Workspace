# Test Report — FIX-121

**Tester:** Tester Agent  
**Date:** 2026-04-07  
**Iteration:** 1

---

## Summary

**VERDICT: FAIL** — Two blocking issues prevent approval: a new regression in the GUI-034 test suite caused by the threading model change, and BUG-206 not being closed in `bugs.jsonl`.

The core implementation is correct and complete. All 12 FIX-121 tests pass (7 developer + 5 Tester edge-cases), all 39 SAF-034 tests pass, and the fix eliminates the UX freeze described in BUG-206. However, the refactor changed the threading contract for `_on_create_project()` in a way that breaks an existing, non-baseline test in `tests/GUI-034/`.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| `tests/FIX-121/test_fix121_button_feedback.py` (7 tests) | Regression | **PASS** | All developer-written regression tests pass |
| `tests/FIX-121/test_fix121_edge_cases.py` (5 tests) | Regression | **PASS** | Added by Tester; COMING_SOON guard, threshold fallback, template not found, label clearing |
| `tests/SAF-034/test_saf034.py` (25 tests) | Unit | **PASS** | All verify_ts_python + _on_create_project tests pass |
| `tests/SAF-034/test_saf034_edge.py` (14 tests) | Unit | **PASS** | All SAF-034 edge cases pass |
| `tests/GUI-034/test_gui034_progress_bar.py` (24 tests) | Unit | **FAIL** | 1 failure — see Regressions section |
| `tests/SAF-036/` (16 tests) | Unit | **PASS** | Counter config integration unaffected |
| Full suite (`--full-suite`) | Regression | See notes | 215 failed / 9124 passed. All non-baseline failures are pre-existing. **One new regression: GUI-034.** |

**Test result IDs logged:**
- TST-2720 — FIX-121 full regression suite (Fail — pre-existing failures in baseline)
- TST-2721 — FIX-121 targeted suite (Pass — 12/12)

---

## Regressions Found

### BUG-210 — `test_on_create_project_no_thread_on_invalid_name` fails (NEW — not in baseline)

**File:** `tests/GUI-034/test_gui034_progress_bar.py`  
**Test:** `test_on_create_project_no_thread_on_invalid_name`

**Failure:**
```
AssertionError: Expected 'start' to not have been called. Called 1 times.
```

**Root cause:** This test asserts the *pre-FIX-121 behaviour*: no thread starts when name validation fails, and `_set_creation_ui_state` is never called. After FIX-121, the design is:
1. `_set_creation_ui_state(disabled=True)` is called **immediately**, before any validation.
2. The thread **always starts** (validation runs inside the thread).

The developer updated tests 11, 12, 14 in `tests/SAF-034/` to reflect this new contract but **missed** this test in `tests/GUI-034/`.

**Impact:** This test was passing before FIX-121 and is now failing — a genuine new regression, not in `tests/regression-baseline.json`.

**Fix required:** The developer must update `test_on_create_project_no_thread_on_invalid_name` to assert the new semantics:
- `thread.start()` IS called once (thread always starts)
- `_set_creation_ui_state(disabled=True)` IS called (UI disabled immediately)
- The test's second assertion `mock_set_state.assert_not_called()` must also be removed or reversed

---

## BUG-206 Not Closed

`docs/bugs/bugs.jsonl` → BUG-206 still reads `"Status": "Open"` with no `"Fixed In WP"` field set. Per the developer pre-handoff checklist, the developer must set `Fixed In WP = FIX-121` and `Status = Closed` before re-submitting.

---

## Code Review Findings

### Implementation quality: GOOD

- `_on_create_project()` refactor is logically clean.
- `_set_creation_ui_state(disabled=True)` fires before any blocking work — BUG-206 is correctly addressed.
- All validation failure paths re-enable the UI via `self._window.after(0, callback)` — main-thread safety is maintained.
- `open_vscode` captured before checkbox is disabled — no race condition on the BooleanVar.
- `get_counter_threshold()` / ValueError fallback to 20 is safe.
- Closure variable capture uses explicit locals (`_name_err`, `_dest_err`, etc.) — correct Python late-binding mitigation.

### Security review: PASS

- No new inputs introduced; all existing input validation paths retained.
- No shell=True, no eval/exec.
- Threading does not introduce privilege escalation risk.
- `self._window.after(0, callback)` is the standard tkinter thread-safe dispatch — correct pattern.

### ADR compliance: PASS

- ADR-008 (Tests Must Track Current Codebase State) — violated by missing GUI-034 test update (BUG-210).
- No other ADR conflicts found.

---

## Edge Cases Verified (by Tester)

| Scenario | Outcome |
|----------|---------|
| COMING_SOON selected — UI NOT disabled, no thread | PASS |
| Thread always starts even on invalid name (new contract) | PASS |
| `get_counter_threshold()` raises ValueError → fallback to 20 | PASS |
| No template found → error dialog + UI re-enabled | PASS |
| Inline error labels cleared at start of each `_create()` run | PASS |

---

## Pre-Done Checklist Status

- [x] `dev-log.md` exists and is non-empty
- [ ] `test-report.md` written — **this document** (Tester writes it)
- [x] Test files exist in `tests/FIX-121/` — 12 tests total
- [x] Test results logged (TST-2720, TST-2721)
- [x] BUG-210 logged via `scripts/add_bug.py`
- [ ] BUG-206 not updated: `Status` still `Open`, `Fixed In WP` not set
- [ ] `test_on_create_project_no_thread_on_invalid_name` in GUI-034 still failing
- [ ] `scripts/validate_workspace.py --wp FIX-121` — returns clean (exit 0) ✓

---

## Mandatory TODOs for Developer (Iteration 2)

1. **Update `tests/GUI-034/test_gui034_progress_bar.py::test_on_create_project_no_thread_on_invalid_name`**  
   The test must reflect the FIX-121 threading contract:
   - `mock_thread_instance.start.assert_called_once()` (thread always starts)
   - `mock_set_state.assert_called_once_with(disabled=True)` (UI disabled before validation)
   - Remove the existing `start.assert_not_called()` and `mock_set_state.assert_not_called()` assertions
   - Optionally add an assertion that the inline name error is set and UI is re-enabled after the (synchronous) thread run

2. **Close BUG-206 in `docs/bugs/bugs.jsonl`**  
   Set `"Status": "Closed"` and `"Fixed In WP": "FIX-121"`.  
   Use the JSON update directly (bugs.jsonl text edit) — `update_bug_status.py` is recommended if available, otherwise edit the line directly and verify with `git diff`.

3. **Re-run full test suite** after both fixes and confirm no regressions:
   ```powershell
   .venv\Scripts\python scripts/run_tests.py --wp FIX-121 --type Regression --env "Windows 11 + Python 3.11" --full-suite
   ```

4. **Re-run workspace validation:**
   ```powershell
   .venv\Scripts\python scripts/validate_workspace.py --wp FIX-121
   ```

5. **Commit and re-handoff** with all changed files staged.
