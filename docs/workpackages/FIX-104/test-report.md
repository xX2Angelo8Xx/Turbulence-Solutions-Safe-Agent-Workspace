# FIX-104 Test Report — Fix version-hardcoded test assertions

**Tester:** Tester Agent  
**Date:** 2026-04-04  
**WP Status:** Done  
**Verdict:** PASS

---

## Summary

All 128 tests across the 12 modified test files and FIX-104's own verification suite pass.  
The Developer correctly converted 43 stale hardcoded version strings (`3.2.3`, `3.2.4`, `3.2.6`, `3.3.1`) to use `CURRENT_VERSION` from `tests/shared/version_utils.py`.  
The regression baseline was updated from 686 → 643 entries, removing the 43 now-passing tests.

---

## Test Runs

| Test ID  | Scope                                          | Type       | Result           |
|----------|------------------------------------------------|------------|------------------|
| TST-2584 | FIX-104 targeted suite (6 tests)               | Unit       | **Pass** (6/6)   |
| TST-2585 | Full regression suite                          | Unit       | Fail* — 47 pre-existing collection errors |
| TST-2586 | 12 modified files + FIX-104 tests (128 tests)  | Regression | **Pass** (128/128) |

*TST-2585 Fail is entirely due to 47 pre-existing `ModuleNotFoundError: No module named 'yaml'` errors across DOC-019 through MNT-008. These are confirmed pre-existing on `main` (verified by git stash + retest) and are fully covered by the regression baseline (643 known failures). No new failures were introduced by FIX-104.

---

## Files Reviewed

### Modified test files — all pass
| File | Stale version removed | Status |
|------|-----------------------|--------|
| `tests/FIX-077/test_fix077_version_322.py` | `3.2.3` | PASS |
| `tests/FIX-078/test_fix078_version_323.py` | `3.2.4` | PASS |
| `tests/FIX-078/test_fix078_edge_cases.py` | `3.2.4` | PASS |
| `tests/FIX-088/test_fix088_version_bump.py` | `3.2.6` | PASS |
| `tests/FIX-088/test_fix088_edge_cases.py` | `3.2.6` | PASS |
| `tests/FIX-090/test_fix090_version_bump.py` | `3.3.1` | PASS |
| `tests/FIX-090/test_fix090_edge_cases.py` | `3.3.1` | PASS |
| `tests/INS-029/test_ins029_version_bump.py` | `3.2.4` | PASS |
| `tests/FIX-070/test_fix070_version_bump.py` | `3.2.3` | PASS |
| `tests/FIX-047/test_fix047_version.py` | sys.path workaround removed | PASS |
| `tests/FIX-019/test_fix019_edge_cases.py` | minor==0 assertion removed | PASS |
| `tests/FIX-036/test_fix036_version_consistency.py` | `2.1.0` in arch assertion removed | PASS |

### New test file
- `tests/FIX-104/test_fix104_version_assertions.py` — 6 tests, all pass

---

## Regression Baseline

- Previous `_count`: 686 (before FIX-104)
- New `_count`: 643
- Entries removed: 43 (the previously-failing version assertions)
- Baseline file `_updated`: 2026-04-04 ✓
- No new entries required: no new failures introduced

---

## Accept Criteria Verification (US-077 AC #2)

> All tests that currently hardcode obsolete launcher versions are updated to use dynamic version sourcing or the current expected version 3.3.11.

**Met.** All 8 `EXPECTED_VERSION = "<stale>"` patterns removed. FIX-070 updated to reference `3.3.11` explicitly as documented. FIX-047 uses the standard `from tests.shared.version_utils import CURRENT_VERSION` import.

---

## Edge-Case Analysis

**Considered and verified:**

1. **FIX-090 regex edge case**: The developer updated `test_no_future_version_in_files` where `3\.3\.[2-9]` would false-match `3.3.11` (the "1" in "11" matched `[2-9]` is wrong — actually `3.3.1` would match). The fix (accepting `3.3.11` as valid) is correct and tested.

2. **FIX-019 minor==0 removal**: At v3.3.11 the minor is 3, so the old assertion `new_parts[1] == 0` was invalid. Correctly removed.

3. **FIX-036 architecture.md**: `2.1.0` no longer appears in architecture.md (confirmed by running the test). The fix to check for FIX-036 reference only is correct.

4. **Semantics-preserving changes**: Tests that test version *parsing logic* (e.g., semver comparison in FIX-049) were correctly untouched — those use arbitrary test data, not the launcher version.

5. **STALE_VERSION constants preserved**: Tests asserting that old versions are *gone* from canonical files (e.g., `STALE_VERSION = "3.2.2"`) were correctly left intact.

6. **No hardcoded version strings in assertion context remain**: Verified by FIX-104's own `test_affected_files_no_hardcoded_expected_version` test.

**No additional edge cases found.** No extra tests required.

---

## Security Review

No security concerns. These are pure test assertion changes with no effect on application code.

---

## ADR Conflicts

No ADR conflicts. ADR-002 (Mandatory CI Test Gate) is unblocked by this fix, not contradicted.

---

## Bugs Found

None.

---

## Verdict: PASS

All acceptance criteria for FIX-104 are met. WP status set to `Done`.
