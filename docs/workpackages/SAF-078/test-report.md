# Test Report — SAF-078

**Tester:** Tester Agent
**Date:** 2026-04-04
**Iteration:** 1

## Summary

SAF-078 correctly implements the core snapshot-locking mechanism: decision mismatches raise an explicit `AssertionError`, the `--update-snapshots` flag rewrites JSON files in-place, the session fixture defaults to `False`, and all existing 10 golden-file snapshots still pass. Documentation files (`README.md`, `agent-workflow.md`) contain the required sections.

**One blocking issue was found:** the `README.md` "Procedure — using `--update-snapshots`" step 2 documents a command (`pytest tests/snapshots/ -v --update-snapshots`) that fails with `unrecognized arguments: --update-snapshots` because `pytest_addoption` is only registered in `tests/snapshots/security_gate/conftest.py` and is invisible to pytest when the parent `tests/snapshots/` directory is the collection root. **VERDICT: FAIL.**

---

## Tests Executed

| TST-ID | Test | Type | Result | Notes |
|--------|------|------|--------|-------|
| TST-2499 | SAF-078: full regression suite (run 1) | Regression | Fail | 634 known-baseline failures; no new regressions |
| TST-2500 | SAF-078: full regression suite (run 2) | Regression | Fail | 633 known-baseline failures; no new regressions |
| TST-2501 | SAF-078: targeted unit + tester edge-cases | Unit | Fail | 17 passed, 1 failed — tester edge-case confirms README bug (BUG-187) |
| TST-2502 | SAF-078: snapshot suite (10 existing snapshots) | Security | Pass | All 10 golden-file tests pass; no regressions introduced |

Developer's logged result: TST-2498 (12 passed) — confirmed independently.

---

## Regression Check

All failures in the full regression suite (633–634 tests) are listed in `tests/regression-baseline.json`. No test that was previously passing is now failing as a result of SAF-078 changes. SAF-078 introduced 12 + 6 = 18 new tests (12 Developer + 6 Tester edge cases). Of these, 17 pass and 1 fails (the tester's `test_readme_procedure_uses_security_gate_subdirectory_for_update_command` which is intentionally designed to catch BUG-187).

---

## Edge Cases Tested (Tester Additions)

Added `tests/SAF-078/test_saf078_tester_edge_cases.py` with 6 additional tests:

| Test | Purpose | Result |
|------|---------|--------|
| `test_decision_change_never_passes_silently` | Bypass-attempt: decision change without flag always raises (cannot be silently ignored) | PASS |
| `test_bypass_with_update_flag_but_no_matching_file_still_raises` | `--update-snapshots=True` but no matching JSON file → still raises | PASS |
| `test_assertion_error_includes_input_and_ws_root_lines` | Error includes input and ws_root diagnostics for actionable debugging | PASS |
| `test_assertion_error_wraps_decision_values_in_single_quotes` | Decision values are wrapped in single quotes for clarity | PASS |
| `test_conftest_update_snapshots_fixture_default_is_false` | Fixture default is `False` — flag is opt-in, never accidentally on | PASS |
| `test_readme_procedure_uses_security_gate_subdirectory_for_update_command` | README `--update-snapshots` command targets correct scope | **FAIL** — BUG-187 |

---

## Bugs Found

- **BUG-187:** README `--update-snapshots` procedure documents non-functional command (Medium severity)
  - `README.md` step 2 documents: `pytest tests/snapshots/ -v --update-snapshots`
  - Actual behavior: `ERROR: unrecognized arguments: --update-snapshots`
  - Root cause: `pytest_addoption` is in `tests/snapshots/security_gate/conftest.py`; pytest does not propagate options from subdirectory conftest to the parent collection scope
  - Correct command: `pytest tests/snapshots/security_gate/ -v --update-snapshots`

---

## Acceptance Criteria Verification

| Criterion | Status |
|-----------|--------|
| Snapshot tests fail on any security decision change (with clear message) | ✅ PASS — `test_snapshot_fails_with_decision_change_message` confirms canonical message |
| Snapshot update requires explicit `--update-snapshots` flag | ✅ PASS — `test_conftest_update_snapshots_fixture_default_is_false` confirms default=False |
| `--update-snapshots` rewrites the snapshot JSON file in-place | ✅ PASS — `test_update_snapshots_flag_rewrites_file` confirms |
| `README.md` documents the flag, dev-log requirement, and "snapshot IS documentation" principle | ❌ **PARTIAL FAIL** — flag documented but with wrong command scope (BUG-187) |
| `agent-workflow.md` dev-log template includes `## Behavior Changes` section | ✅ PASS — present and mentions `--update-snapshots` |
| Existing snapshot tests (all 10) still pass | ✅ PASS — TST-2502 |
| All 12 SAF-078 tests pass | ✅ PASS — TST-2498/TST-2501 |

---

## TODOs for Developer

- [ ] **Fix BUG-187 — README update procedure command:** In `tests/snapshots/README.md`, the "Procedure — using `--update-snapshots`" section contains this command in its step 2:
  ```
  .venv\Scripts\python.exe -m pytest tests/snapshots/ -v --update-snapshots
  ```
  This fails because `pytest_addoption` is registered only in `tests/snapshots/security_gate/conftest.py` and is not visible to pytest when collecting from the parent directory.

  **Fix option A (preferred):** Update the command in the README to use the subdirectory path:
  ```
  .venv\Scripts\python.exe -m pytest tests/snapshots/security_gate/ -v --update-snapshots
  ```
  Also update step 5's "re-run without the flag" command to match if it was affected.

  **Fix option B (alternative):** Create `tests/snapshots/conftest.py` that registers `--update-snapshots` at the parent scope, and then both `tests/snapshots/` and `tests/snapshots/security_gate/` can use the flag. This would require refactoring the conftest to avoid duplicate `pytest_addoption` registration.

  Fix option A is simpler and lower risk. Option B is cleaner long-term when more component subdirectories are added.

- [ ] **Update `docs/workpackages/workpackages.csv`:** After fixing, add `Fixed In WP: SAF-078` for BUG-187's `bugs.csv` row (or re-use BUG-187 and mark it as `Fixed`).

---

## Verdict

**FAIL** — Return to Developer (Iteration 1).

The core locking mechanism is correct and well-tested. One specific fix is required: the README documents a `--update-snapshots` pytest command that fails with "unrecognized arguments" when run at the `tests/snapshots/` parent level. Any agent or developer following the documented procedure would encounter an error at step 2. See BUG-187 and TODO above.

---

# Iteration 1 Re-Review — 2026-04-04

**Tester:** Tester Agent

## Verdict: PASS

## Changes Verified

The Developer implemented Fix Option B (the cleaner solution): created `tests/snapshots/conftest.py` at the parent level, moved `pytest_addoption` and the `update_snapshots` fixture there, and cleaned up the child conftest. Both collection scopes now accept `--update-snapshots` without errors.

## Test Results

| TST-ID | Suite | Type | Result |
|--------|-------|------|--------|
| TST-2505 | SAF-078 targeted suite | Unit | 18 passed, 0 failed |
| TST-2506 | SAF-078 targeted suite (repeat) | Unit | 18 passed, 0 failed |
| TST-2507 | Golden-file snapshot suite (10 tests) | Security | 10 passed, 0 failed |
| TST-2504 | Full regression suite | Regression | 8026 passed — all failures in baseline |

## BUG-187 Verification

- `pytest tests/snapshots/ -v --update-snapshots` → 10 passed, no "unrecognized arguments" ✅
- `pytest tests/snapshots/security_gate/ -v --update-snapshots` → 10 passed ✅
- `tests/snapshots/conftest.py` contains `default=False` ✅
- BUG-187 status → Closed ✅

## Acceptance Criteria — Final Status

| Criterion | Status |
|-----------|--------|
| Snapshot tests fail on any decision change (canonical message) | ✅ PASS |
| `--update-snapshots` rewrites snapshot JSON in-place | ✅ PASS |
| `pytest tests/snapshots/ -v --update-snapshots` works | ✅ PASS — BUG-187 fixed |
| `pytest tests/snapshots/security_gate/ -v --update-snapshots` works | ✅ PASS |
| README documents flag, dev-log requirement, "snapshot IS the documentation" | ✅ PASS |
| `agent-workflow.md` dev-log template includes `## Behavior Changes` | ✅ PASS |
| All 10 existing snapshot tests pass | ✅ PASS |
| All 18 SAF-078 tests pass | ✅ PASS |
| BUG-187 Fixed + Closed | ✅ PASS |

## Regression Check

No new regressions. All 635 failures in the full suite are in `tests/regression-baseline.json`.

## No New Bugs Found
