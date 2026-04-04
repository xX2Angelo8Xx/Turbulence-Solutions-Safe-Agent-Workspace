# MNT-024 Test Report — Reset Regression Baseline and Verify CI Green

**Verdict: FAIL**

---

## Summary

The Developer's work is high quality: the baseline was reduced from 147 generic entries to 72 specific, well-documented entries, and all code changes are correct. However, **2 pre-existing flaky tests are not covered by the baseline**, which means CI would flag them as regressions on any run where they misbehave. The baseline must cover all known failures before this WP can be marked Done.

---

## Test Execution

| Run | Total Failures | New (non-baseline) | Notes |
|-----|---------------|--------------------|-------|
| Run 1 (tester) | 72 | 1 — MNT-015 concurrent threads | Flaky; passes in isolation |
| Run 2 (run_tests.py --full-suite) | 68 | 0 | MNT-015 did not fire |
| Run 3 (tester) | 68 | 1 — INS-019 test_verify_shim_existence_only_check | Flaky; passes in isolation |

All 8 MNT-024 targeted tests pass:

```
tests/MNT-024/test_mnt024_baseline_reset.py::test_baseline_file_exists          PASSED
tests/MNT-024/test_mnt024_baseline_reset.py::test_baseline_count_matches_entries PASSED
tests/MNT-024/test_mnt024_baseline_reset.py::test_baseline_count_reduced_from_original PASSED
tests/MNT-024/test_mnt024_baseline_reset.py::test_baseline_updated_field_present PASSED
tests/MNT-024/test_mnt024_baseline_reset.py::test_baseline_updated_after_previous_reset PASSED
tests/MNT-024/test_mnt024_baseline_reset.py::test_all_entries_have_reason       PASSED
tests/MNT-024/test_mnt024_baseline_reset.py::test_no_entry_uses_generic_reason  PASSED
tests/MNT-024/test_mnt024_baseline_reset.py::test_baseline_is_valid_json        PASSED
8 passed in 0.20s
```

Test results logged: TST-2607 (targeted suite, Pass), TST-2608 (targeted suite re-run, Pass), TST-2609 (full suite, Fail).

---

## Validation Results

| Check | Result |
|-------|--------|
| `dev-log.md` exists and non-empty | ✅ Pass |
| `tests/MNT-024/` exists with 8 tests | ✅ Pass |
| `_count` (72) == actual entry count | ✅ Pass |
| `_count` < 100 (was 147) | ✅ Pass |
| All entries have specific, non-generic reasons | ✅ Pass |
| No "pre-existing failure" generic reasons remain | ✅ Pass |
| `scripts/validate_workspace.py --wp MNT-024` | ✅ All checks passed |
| No `tmp_` files in `docs/workpackages/MNT-024/` | ✅ Pass |
| Baseline structured correctly (valid JSON, 3 top-level keys) | ✅ Pass |
| All deterministic failures covered by baseline | ✅ Pass |
| **All flaky failures covered by baseline** | ❌ **FAIL — 2 missing** |

---

## Code Review

All changes reviewed against the dev-log and found correct:

- **`templates/agent-workbench/.vscode/settings.json`** — already committed to LF; no diff visible (correct).
- **`scripts/validate_workspace.py`** — `required_fields` reduced to `["ID", "Status"]` for all 4 JSONL types. Correct.
- **`docs/test-results/test-results.jsonl`** — TST-1803A renamed to TST-2606; 14 empty Result fields populated. Correct.
- **`templates/agent-workbench/Project/AGENT-RULES.md`** — Created; satisfies FIX-091/SAF-049/SAF-056. Contradiction with DOC-045/DOC-047/FIX-103 is acknowledged and documented.
- **`templates/agent-workbench/Project/README.md`** — Created with `# {{PROJECT_NAME}}` H1. Correct.
- **`templates/agent-workbench/README.md`** — Rewritten with security tier content, 4 `{{PROJECT_NAME}}` occurrences (satisfies FIX-086). Contradiction with DOC-002 documented.
- **`templates/agent-workbench/MANIFEST.json`** — Regenerated (38 files, 10 security-critical). Correct.
- **`tests/regression-baseline.json`** — 147 → 72 entries, all with specific reasons, grouped into 11 documented categories.

---

## Bugs Found

None in the application code. The flaky tests are pre-existing infrastructure issues, not new bugs.

---

## Regression Analysis

The 2 uncovered flaky failures are **not caused by MNT-024**. They are pre-existing intermittent tests with the same root causes as existing baseline entries:

### ❌ Missing baseline entry 1: INS-019 test_verify_shim_existence_only_check

- **Test**: `tests.INS-019.test_ins019_edge_cases.test_verify_shim_existence_only_check`
- **Confirmed flaky**: passes in isolation (`pytest tests/INS-019/ — 59 passed`), fails in full suite due to sys.path mutation
- **Root cause**: Same as 16 other INS-019 baseline entries — module-level `sys.path.insert()` sensitive to import ordering
- **Missing from baseline**: The developer documented 16 INS-019 tests but missed this one variant

### ❌ Missing baseline entry 2: MNT-015 test_locked_next_id_concurrent_threads

- **Test**: `tests.MNT-015.test_mnt015_tester_edge_cases.test_locked_next_id_concurrent_threads`
- **Confirmed flaky**: passes in isolation (`1 passed in 1.03s`), fails intermittently in full suite
- **Root cause**: Same pattern as SAF-072 — threading/locking race condition in test setup under heavy parallel load (10-thread concurrency test)
- **Missing from baseline**: Not observed during developer's test runs due to non-deterministic timing

---

## ❌ TODOs for Developer (must fix before Tester re-review)

### TODO 1 — Add INS-019 flaky test to baseline

Add the following entry to `tests/regression-baseline.json` → `known_failures`:

```json
"tests.INS-019.test_ins019_edge_cases.test_verify_shim_existence_only_check": {
  "reason": "Flaky test: passes when run in isolation (python -m pytest tests/INS-019/) but fails in full suite due to sys.path mutation by other test modules. The INS-019 test file uses a module-level sys.path.insert() that is sensitive to import ordering."
}
```

Use the **exact same reason string** as the other 16 INS-019 baseline entries (same root cause).

### TODO 2 — Add MNT-015 flaky test to baseline

Add the following entry to `tests/regression-baseline.json` → `known_failures`:

```json
"tests.MNT-015.test_mnt015_tester_edge_cases.test_locked_next_id_concurrent_threads": {
  "reason": "Flaky test: passes when run in isolation but fails intermittently in the full test suite due to threading/file-locking race conditions under heavy parallel load (10-thread concurrency test). Not a regression in production code."
}
```

### TODO 3 — Update `_count`

After adding both entries, update `_count` from `72` to `74` and `_updated` to today's date.

### TODO 4 — Verify with run_tests.py

Run `python scripts/run_tests.py --wp MNT-024 --type Regression --env "Windows 11 + Python 3.13" --full-suite` and confirm the new result shows no non-baseline failures. Since these are flaky tests, 2–3 consecutive clean full-suite runs (zero non-baseline failures) would be ideal.

---

## What Does NOT Need Changing

- All application code changes are correct and do not need modification.
- All 72 existing baseline entries are correct and well-documented.
- The 8 MNT-024 unit tests are comprehensive and do not need changes.
- `scripts/validate_workspace.py` changes are correct.
- Template changes are correct.

---

## Pre-Done Checklist Status

- [x] `dev-log.md` exists and is non-empty
- [ ] `test-report.md` written by Tester — done NOW
- [x] Test files exist in `tests/MNT-024/` with 8 tests
- [x] Test results logged via `scripts/run_tests.py` (TST-2607, TST-2608, TST-2609)
- [ ] All baseline failures covered — **BLOCKED on TODO 1-4 above**
- [x] `validate_workspace.py --wp MNT-024` returns clean
- [x] No `tmp_` files in WP folder

**Status: Set WP back to `In Progress`.**
