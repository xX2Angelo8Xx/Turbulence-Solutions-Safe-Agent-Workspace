# Test Report — FIX-103: Bulk-fix agent specification tests

**Tester:** Tester Agent  
**Date:** 2026-04-04  
**Verdict:** ✅ PASS (Iteration 2)

---

## Summary

FIX-103 fixed 22 DOC test suites (DOC-018 through DOC-045) and correctly updated the regression baseline count from 578 to 147. However, the Developer changed the **schema** of `tests/regression-baseline.json` — converting `known_failures` from a dict-of-objects to a plain list — which broke 2 previously-passing DOC-051 tests.

**Test Results (TST-2596):**
- Total collected: ~783 (excluding already-skipped removed-agent suites)
- Passed: 779
- Failed: **2** (DOC-051 regressions — new, not in baseline)
- Skipped: 310 (6 removed-agent suites properly skipped)
- Errors: 0

---

## Tests Run

| Suite | Result | Notes |
|-------|--------|-------|
| tests/FIX-103/ | ✅ 9 passed | All regression tests pass |
| tests/DOC-018/ | ✅ passed | Agent count fixed (10→7) |
| tests/DOC-019/ | ✅ passed | |
| tests/DOC-020/ | ✅ passed | edit restriction removed |
| tests/DOC-021/ | ✅ passed | |
| tests/DOC-022/ | ✅ passed | edit restriction, model, sections fixed |
| tests/DOC-023/ | ✅ skipped | Scientist agent removed — correct |
| tests/DOC-024/ | ✅ skipped | Criticist agent removed — correct |
| tests/DOC-025/ | ✅ passed | ask tool and section refs fixed |
| tests/DOC-026/ | ✅ skipped | Fixer agent removed — correct |
| tests/DOC-027/ | ✅ skipped | Writer agent removed — correct |
| tests/DOC-028/ | ✅ skipped | Prototyper agent removed — correct |
| tests/DOC-029/ | ✅ passed | EXPECTED_AGENTS/TOOLS updated |
| tests/DOC-030/ | ✅ passed | EXPECTED_AGENTS (6), sections fixed |
| tests/DOC-031/ | ✅ passed | |
| tests/DOC-032/ | ✅ passed | |
| tests/DOC-033/ | ✅ passed | README.md existence check corrected |
| tests/DOC-034/ | ✅ skipped | CLOUD-orchestrator removed — correct |
| tests/DOC-035/ | ✅ passed | AgentDocs/README.md verified |
| tests/DOC-036/ | ✅ passed | workspace-cleaner added, researcher fetch fixed |
| tests/DOC-037/ | ✅ passed | |
| tests/DOC-038/ | ✅ passed | |
| tests/DOC-039/ | ✅ passed | tidyup→workspace-cleaner, AGENT-RULES path |
| tests/DOC-040/ | ✅ passed | |
| tests/DOC-041/ | ✅ passed | |
| tests/DOC-042/ | ✅ passed | tidyup→workspace-cleaner, model settings |
| tests/DOC-043/ | ✅ passed | AGENT-RULES path, workspace-cleaner |
| tests/DOC-044/ | ✅ passed | AGENT-RULES path fixed |
| tests/DOC-045/ | ✅ 1 passed, 1 skipped | old_agentdocs_readme_deleted correctly skipped |
| tests/DOC-046–058/ | ✅ 201 passed | No regressions |
| tests/DOC-051/ | ❌ **2 FAILED** | Schema regression (see below) |

---

## Failures

### BUG-190 — DOC-051: `known_failures` schema broken

**Files:** `tests/regression-baseline.json`

**Root Cause:** FIX-103 changed the `known_failures` field from a dict (schema required by DOC-051) to a flat list of test IDs.

**Old format (correct):**
```json
{
  "known_failures": {
    "tests.DOC-004.test_doc004_…test_name": {
      "reason": "pre-existing failure as of 2026-04-04 baseline reset"
    }
  }
}
```

**New format (incorrect — introduced by FIX-103):**
```json
{
  "known_failures": [
    "tests.DOC-004.test_doc004_…test_name",
    …
  ]
}
```

**Failing tests:**
1. `tests/DOC-051/test_doc051_regression_baseline_docs.py::test_regression_baseline_has_known_failures_field`  
   — `isinstance(data["known_failures"], dict)` → False
2. `tests/DOC-051/test_doc051_regression_baseline_docs.py::test_regression_baseline_each_entry_has_reason`  
   — `data["known_failures"].items()` → AttributeError: list has no attribute 'items'

These tests were passing before FIX-103 (DOC-051 entries do not appear in any previous regression baseline).

---

## Template File Verification

The three template files created/modified are correct:

- `templates/agent-workbench/.github/agents/README.md` — Added "customiz" language and coordinator delegation note. Verified by DOC-033, DOC-018 passing.
- `templates/agent-workbench/.github/instructions/copilot-instructions.md` — Added AgentDocs section. Verified by DOC-035 passing.
- `templates/agent-workbench/Project/AgentDocs/README.md` — Created with required content. Verified by DOC-035 and DOC-043 passing.

---

## Regression Check

Checked `tests/regression-baseline.json` (pre-FIX-103 had 578 entries, all as dict with reasons). DOC-051 was NOT in the old baseline — the two DOC-051 failures are confirmed **new regressions**.

---

## validate_workspace.py

```
python scripts/validate_workspace.py --wp FIX-103
→ All checks passed.
```

Note: `validate_workspace.py` does not run the test suite — it only checks structural files. The schema regression is not caught by validation.

---

## Verdict: FAIL

**Return to Developer with the following TODOs:**

---

## TODOs for Developer

### TODO-1 (Required — Blocker): Fix `known_failures` schema in `tests/regression-baseline.json`

The `known_failures` field must remain a **dict** (not a list). Restore the dict format for all 147 remaining entries, each with a `reason` sub-object.

**Steps:**
1. Open `tests/regression-baseline.json`
2. Change `"known_failures": [...]` back to `"known_failures": {...}`
3. For each test ID in the list, convert to:
   ```json
   "tests.DOC-004.test_doc004_…test_name": {
     "reason": "pre-existing failure as of 2026-04-04 baseline reset"
   }
   ```
4. Keep `_count: 147` and `_updated: "2026-04-04"` unchanged
5. Verify: `python -m pytest tests/DOC-051/ -q` → 32 passed, 0 failed
6. Re-run: `python scripts/run_tests.py` — all DOC-051 tests must pass

**Reference:** The pre-FIX-103 format is visible at git commit `c3fefd4` (`tests/regression-baseline.json`).

---

## Iteration 2 — Tester Review (2026-04-04)

**Test Result ID:** TST-2598

### Fix Applied

Developer restored `known_failures` from a list back to a dict with `{"reason": "..."}` objects per the documented schema.

### Verification

**`tests/regression-baseline.json` structure:**
- `known_failures` type: **dict** ✅
- `_count`: 147 ✅
- Actual entries: 147 ✅
- Count matches: ✅
- All entries have `reason` field: ✅

**DOC-051 tests:** 32/32 passed ✅  
- `test_regression_baseline_has_known_failures_field` — PASSED  
- `test_regression_baseline_each_entry_has_reason` — PASSED  
- All other DOC-051 tests — PASSED  

**FIX-103 regression tests:** 9/9 passed ✅

**Full test suite (TST-2598):**
- Collected: ~9,256
- Passed: 8,769
- Failed: 141 (all pre-existing in baseline — 0 new regressions)
- Skipped: 346
- xfailed: 5

**Regression baseline check:** 141 failures vs 147 baseline entries — 0 new regressions ✅

**`validate_workspace.py --wp FIX-103`:** Passed with 1 warning (BUG-190 Fixed-In field mismatch — non-blocking) ✅

### Verdict: PASS
