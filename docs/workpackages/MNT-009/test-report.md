# Test Report — MNT-009

**Tester:** Tester Agent  
**Date:** 2026-04-03  
**Iteration:** 1

## Summary

MNT-009 is a pure documentation change that adds `scripts/add_bug.py` mandate to `tester.agent.md`. All three required locations (Edit Permissions, Pre-Done Checklist, Constraints) were correctly updated. The implementation aligns with `agent-workflow.md`'s Mandatory Script Usage table. No source code was modified; no regressions were introduced.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2474 (Developer) | Unit | Pass | 9 original WP tests — all pass |
| TST-2475 | Regression | Pass* | 7832 passed, 37 skipped, 5 xfailed, 50 errors — all failures are pre-existing baseline entries |
| TST-2476 (Tester) | Unit | Pass | 12 tests (9 Developer + 3 tester edge cases) — all pass |

*Full suite exit code 1 due to 633 pre-existing failures, all confirmed in `tests/regression-baseline.json`. No new regressions.

## Edge-Case Tests Added

Three additional tests were added to `tests/MNT-009/test_mnt009_tester_add_bug_mandate.py`:

- `test_edit_permissions_uses_full_script_path` — verifies `scripts/add_bug.py` (with path prefix, not bare `add_bug.py`) in Edit Permissions
- `test_pre_done_checklist_uses_full_script_path` — same check for Pre-Done Checklist
- `test_constraints_uses_full_script_path` — same check for Constraints

**Rationale:** A bare `add_bug.py` reference without the `scripts/` prefix is not actionable — agents would need to guess the script location. All three tests pass.

## Analysis

**Attack vectors / misuse scenarios:**
- An agent might interpret `add_bug.py` without the path and try to run it from the wrong directory — mitigated by the edge-case tests above verifying the full path is present.
- An agent might try to directly edit `bugs.csv` and claim the prohibition only applies to "while testing" not "at any time" — the Constraints section's `**ALWAYS**` bolding prevents this interpretation.

**Boundary conditions:**
- The `_section()` helper in the test file correctly handles the last section (Constraints) hitting `\Z` instead of the next `##` heading.

**Alignment verified:**
- `tester.agent.md` Constraints now says: `Direct editing of docs/bugs/bugs.csv is prohibited.`
- `agent-workflow.md` Mandatory Script Usage table has: `Log a bug | scripts/add_bug.py | Tester`
- Consistent and non-contradictory.

**ADR check:** No relevant ADRs found in `docs/decisions/index.csv` for this domain.

**No bugs found during testing.**

## Bugs Found

None.

## TODOs for Developer

N/A — PASS verdict.

## Verdict

**PASS — mark WP as Done.**
