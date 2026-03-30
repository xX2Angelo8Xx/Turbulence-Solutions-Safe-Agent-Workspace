# FIX-087 Test Report — Install pytest in macOS source install CI workflow

**Verdict: PASS — Done**  
**Tester:** Tester Agent  
**Date:** 2026-03-30 (Iteration 2)  
**WP Branch:** `FIX-087/install-pytest-macos-ci`

---

## Iteration 2 Summary (Final)

The INS-028 regression (BUG-160) has been resolved. The Developer narrowed both affected test conditions from `"pytest" in run` to `"python -m pytest" in run` in `tests/INS-028/test_ins028_tester_edge_cases.py`. Both previously-failing tests now pass. All 13 FIX-087 tests pass. Full suite shows 164 failures — all pre-existing (main baseline: 165 failures, 7443 passed; branch: 164 failures, 7457 passed — the branch is an improvement). No regressions introduced by FIX-087.

---

## Iteration 1 Summary (Historical)

The FIX-087 implementation was correct in isolation — the new `pip install pytest` step is placed correctly before the test suite step, uses the venv pip path, and `scripts/install-macos.sh` was correctly left unmodified. All 6 Developer tests pass.

However, the change introduced a **regression in INS-028 tests**: 2 pre-existing passing tests failed because the new step contained the word `pytest` in its `run` field and these tests checked *all* steps with `pytest` in them, not just the `python -m pytest` invocation. This was returned to the Developer as BUG-160.

---

## Files Reviewed

| File | Status |
|------|--------|
| `.github/workflows/macos-source-test.yml` | ✅ New step correctly placed |
| `scripts/install-macos.sh` | ✅ Unchanged — no pytest install |
| `tests/FIX-087/test_fix087_workflow_pytest_step.py` | ✅ 6 tests, all pass |
| `docs/bugs/bugs.csv` (BUG-159) | ✅ Marked Closed, Fixed In WP = FIX-087 |

---

## Test Results

| Test Run | ID | Type | Result | Notes |
|----------|----|------|--------|-------|
| Developer tests | TST-2312 | Unit | ✅ 6/6 PASS | All developer tests pass |
| Tester edge-case tests | TST-2313 | Unit | ✅ 7/7 PASS | New edge cases pass |
| Full suite regression | TST-2314 | Regression | ❌ FAIL | 2 INS-028 tests broken by FIX-087 |

---

## Regression Found: INS-028 test failures (BUG-160)

**Failing tests:**
- `tests/INS-028/test_ins028_tester_edge_cases.py::test_pytest_uses_fail_fast_flag`
- `tests/INS-028/test_ins028_tester_edge_cases.py::test_pytest_uses_short_traceback`

**Root cause:** Both tests iterate all workflow steps and check: `if "pytest" in run`. The new FIX-087 step `~/.local/share/TurbulenceSolutions/venv/bin/pip install pytest` contains `pytest` in its `run` field. The tests then assert `-x` and `--tb=short` must be present — which are pytest *runner* flags, not applicable to `pip install` commands.

**Error message (exact):**
```
AssertionError: pytest step should use '-x' (fail fast) flag. 
Got: '~/.local/share/TurbulenceSolutions/venv/bin/pip install pytest'
```

**Bug logged:** BUG-160

---

## Edge Cases Tested (Tester additions)

| Test | File | Result |
|------|------|--------|
| Install step has descriptive name | test_fix087_edge_cases.py | ✅ PASS |
| Install step is `pip install`, not `python -m pytest` | test_fix087_edge_cases.py | ✅ PASS |
| Install step does NOT contain pytest run flags (-x, --tb=) — INS-028 regression guard | test_fix087_edge_cases.py | ✅ PASS |
| `pip install pytest` appears exactly once | test_fix087_edge_cases.py | ✅ PASS |
| Install step only installs `pytest`, no other packages | test_fix087_edge_cases.py | ✅ PASS |
| Install step is immediately before (adjacent to) the test step | test_fix087_edge_cases.py | ✅ PASS |
| Install step uses venv pip, not bare system pip | test_fix087_edge_cases.py | ✅ PASS |

---

## Security Review

- No secrets, credentials, or hardcoded tokens introduced. ✅
- No production code modified (install-macos.sh clean). ✅
- No new external actions or dependencies added. ✅
- YAML injection not possible — `pip install pytest` is a fixed literal. ✅

---

## Pre-existing Failures (not caused by FIX-087)

Confirmed on `main` (commit `c033c82`) before FIX-087 implementation:
- `tests/DOC-008/test_doc008_read_first_directive.py::test_existing_content_preserved` — pre-existing

---

## Required Developer Actions (TODOs)

### TODO 1 — Fix INS-028 regression (BLOCKING)

**File:** `tests/INS-028/test_ins028_tester_edge_cases.py`

**Problem:** Two tests check `if "pytest" in run:` — this matches `pip install pytest` steps as well as `python -m pytest` invocations.

**Fix required:** Narrow the condition in both affected tests from `"pytest" in run` to `"python -m pytest" in run`:

```python
# BEFORE (in test_pytest_uses_fail_fast_flag and test_pytest_uses_short_traceback):
if "pytest" in run:
    assert "-x" in run, ...

# AFTER:
if "python -m pytest" in run:
    assert "-x" in run, ...
```

Apply this fix to **both** tests:
- `test_pytest_uses_fail_fast_flag` (line ~247)
- `test_pytest_uses_short_traceback` (line ~259)

After fixing, confirm:
1. `pytest tests/INS-028/ -v` → all 29 pass
2. `pytest tests/FIX-087/ -v` → all 13 pass

**Bug reference:** BUG-160

---

## Iteration 1 Verdict

**❌ FAIL — Returned to Developer (In Progress)**

The workflow change itself was correct, but it exposed fragile INS-028 tests that failed. The full test suite had to pass before approval. See BUG-160.

---

## Iteration 2 Test Results

| Test Run | ID | Type | Result | Notes |
|----------|----|------|--------|-------|
| Targeted FIX-087 + INS-028 | TST-2316 | Regression | ✅ 42/42 PASS | Both BUG-160 tests now pass |
| Full suite regression | TST-2317 | Regression | ✅ PASS | 164 pre-existing failures (main: 165); no new regressions |

### Baseline Comparison

| Metric | main (c033c82) | FIX-087 branch | Delta |
|--------|----------------|----------------|-------|
| Tests passed | 7,443 | 7,457 | +14 |
| Tests failed | 165 | 164 | -1 (improvement) |
| Tests skipped | 33 | 33 | 0 |

**All 164 failures on the FIX-087 branch are pre-existing on main.** FIX-087 introduces no new failures.

---

## Iteration 2 Verdict

**✅ PASS — Done**

The INS-028 regression (BUG-160) is resolved. The fix is minimal, correct, and targeted. All 42 FIX-087 and INS-028 tests pass. No regressions introduced.

Return with TODO above clearly addressed before re-submitting for review.
