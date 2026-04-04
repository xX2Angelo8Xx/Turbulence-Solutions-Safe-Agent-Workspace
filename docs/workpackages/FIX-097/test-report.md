# Test Report — FIX-097

**WP ID:** FIX-097  
**Title:** Make --rc Flag Meaningful  
**Branch:** FIX-097/remove-rc-flag  
**Tester:** Tester Agent  
**Date:** 2026-04-04  
**Verdict:** PASS

---

## Summary

FIX-097 removes the cosmetic `--rc` argument from `scripts/release.py` and updates all documentation and tests accordingly. All releases are draft by default per ADR-001 — no opt-in flag is needed.

The implementation is clean, minimal, and correct. All 21 targeted tests pass. No new regressions were introduced.

---

## Test Results

| ID | Type | Status | Details |
|----|------|--------|---------|
| TST-2516 | Unit | Pass | 4 FIX-097 developer tests in 0.45s |
| TST-2517 | Unit | Pass | 21 tests (7 FIX-097 + 14 MNT-013) in 0.63s |

---

## Targeted Tests Run

### FIX-097 tests (`tests/FIX-097/test_fix097_rc_flag_removed.py`) — 7 tests

| Test | Result |
|------|--------|
| `test_rc_flag_not_in_argparse` | ✅ Pass |
| `test_args_rc_not_referenced_in_source` | ✅ Pass |
| `test_help_text_mentions_draft` | ✅ Pass |
| `test_dry_run_still_works` | ✅ Pass |
| `test_module_docstring_documents_draft_behaviour` *(Tester)* | ✅ Pass |
| `test_old_cosmetic_test_name_no_longer_exists_in_mnt013` *(Tester)* | ✅ Pass |
| `test_rc_flag_absent_from_orchestrator_agent` *(Tester)* | ✅ Pass |

### MNT-013 tests (`tests/MNT-013/test_mnt013_human_approval_gate.py`) — 14 tests

All 14 pass, including the renamed `test_all_releases_are_draft_documented` (was `test_rc_flag_clarified_as_cosmetic`). ✅

### Regression check — MNT-004 (`tests/MNT-004/`) — 50 passed, 1 xfailed

No regressions in release.py unit tests following removal of `--rc`. ✅

### DOC-034 failures — 14 failures (all pre-existing baseline)

All 14 DOC-034 test failures are pre-existing known failures in `tests/regression-baseline.json` caused by the missing `CLOUD-orchestrator.agent.md` file. Not caused by FIX-097. ✅

---

## Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|---------|
| `--rc` flag is removed from release.py | ✅ Pass | `test_rc_flag_not_in_argparse` — non-zero exit when `--rc` passed; argparse error message present |
| No `args.rc` reference in source | ✅ Pass | `test_args_rc_not_referenced_in_source` confirms absence |
| `release.py --help` documents draft behaviour | ✅ Pass | `test_help_text_mentions_draft` — "draft" present in `--help` output |
| No cosmetic-only flags remain | ✅ Pass | Only meaningful flags exist: `version` (positional) and `--dry-run` |
| orchestrator.agent.md updated | ✅ Pass | `test_rc_flag_absent_from_orchestrator_agent` + `test_all_releases_are_draft_documented` |
| MNT-013 test updated cleanly | ✅ Pass | `test_old_cosmetic_test_name_no_longer_exists_in_mnt013` confirms rename without leftover |

---

## ADR Conflicts

- **ADR-001 (Draft GitHub Releases):** Active. This WP aligns with ADR-001 — removing the cosmetic `--rc` flag makes the draft-by-default behaviour explicit and removes misleading UI. No conflict. ✅

---

## Edge Cases and Boundary Analysis

| Scenario | Result |
|----------|--------|
| `--rc` with valid version (`1.0.0 --rc`) | ✅ argparse error, non-zero exit — correct |
| `--rc` alone (no version) | argparse rejects unrecognised `--rc` before version validation — tested implicitly |
| `--dry-run` still works after removal | ✅ `test_dry_run_still_works` confirmed |
| Module docstring does not mention `--rc` | ✅ Verified via source inspection |
| MNT-013 test file rename is clean (no duplicate function) | ✅ `test_old_cosmetic_test_name_no_longer_exists_in_mnt013` |

---

## Security Assessment

No security concerns. The removed `--rc` flag had no effect on the security model — it was purely a UI/UX reminder banner. Removing it does not weaken any safety control.

---

## Tester Edge-Case Additions

Three tests added to `tests/FIX-097/test_fix097_rc_flag_removed.py`:

1. `test_module_docstring_documents_draft_behaviour` — verifies the module docstring at the top of `release.py` documents draft behaviour (belt-and-suspenders with `test_help_text_mentions_draft`)
2. `test_old_cosmetic_test_name_no_longer_exists_in_mnt013` — verifies the MNT-013 rename was clean: old function gone, new function present
3. `test_rc_flag_absent_from_orchestrator_agent` — verifies the CI/CD section of `orchestrator.agent.md` no longer references `--rc` (belt-and-suspenders with the MNT-013 check)

---

## Pre-Done Checklist

- [x] `docs/workpackages/FIX-097/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/FIX-097/test-report.md` written (this file)
- [x] Test files exist in `tests/FIX-097/` with 7 tests
- [x] All test results logged via `scripts/add_test_result.py` (TST-2516, TST-2517)
- [x] No bugs found during testing
- [x] `scripts/validate_workspace.py --wp FIX-097` returns clean (exit code 0)
- [x] No regression baseline entries to remove (this WP fixes a cosmetic UX issue, not a pre-existing failing test)
- [x] `git add -A` staged; `git commit` and `git push` to follow
