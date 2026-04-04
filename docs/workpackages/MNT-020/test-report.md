# Test Report — MNT-020

**Tester:** Tester Agent  
**Date:** 2026-04-04  
**Iteration:** 1  
**Verdict:** FAIL — return to Developer

---

## Summary

MNT-020 updated 9 documentation files to replace `.csv` path references with `.jsonl`. The Developer's 18 tests all pass and MNT-020 introduces zero regressions in the full suite. However, one stale `CSV` reference survives in `docs/work-rules/maintenance-protocol.md`: the embedded maintenance log template table still labels check #3 as `CSV Integrity` instead of `JSONL Integrity`. A Tester-added edge-case test catches this bug. The WP cannot be marked Done until this is fixed.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| MNT-020 developer tests (18 passed) — TST-2564 | Unit | **Pass** | All 9 absence + 9 presence checks passed |
| MNT-020 tester edge-case tests — TST-2565 | Unit | **FAIL** | 14 passed, 1 FAILED: `test_maintenance_log_template_uses_jsonl_integrity` |
| MNT-020 full regression suite — TST-2566 | Regression | **Pass** | Zero new failures; 747 pre-existing failures confirmed on `main` too |

---

## Findings

### BUG: Stale `CSV Integrity` in maintenance-protocol.md log template

**File:** `docs/work-rules/maintenance-protocol.md`  
**Line:** 101  
**Content:** `| 3 | CSV Integrity | Pass/Warning/Fail | <findings> |`  
**Expected:** `| 3 | JSONL Integrity | Pass/Warning/Fail | <findings> |`

**Explanation:** The maintenance protocol has two places that reference check #3:
1. The actual check heading at line 29: `### 3. JSONL Integrity` — correctly updated.
2. The embedded Markdown log template that maintenance agents copy when creating audit logs — **still says `CSV Integrity`**.

When a Maintenance Agent generates a log from this template, it will produce a stale `CSV Integrity` row, inconsistent with the actual check. The Developer's tests only verified the section heading; the template table entry was missed.

**Caught by:** `tests/MNT-020/test_mnt020_edge_cases.py::test_maintenance_log_template_uses_jsonl_integrity`

---

### Note: Pre-existing test failures (not caused by MNT-020)

Full suite shows 118 failures beyond the 684-entry baseline. These are all pre-existing on `main` before MNT-020 was branched. Cause categories:
- Missing agent `.md` files in `templates/agent-workbench/.github/agents/` (DOC-023, DOC-024, DOC-026, DOC-027, DOC-028, DOC-039 tests)
- Tests that still reference deleted `.csv` files (FIX-059, FIX-065 etc.) — these tests were written for CSV infrastructure that was removed in MNT-018
- ADR index entry count mismatch (DOC-053)

None of these are related to MNT-020 scope. They should be addressed in separate maintenance WPs.

---

## Tester Edge-Case Tests Added

File: `tests/MNT-020/test_mnt020_edge_cases.py` (15 tests)

| Test Name | Purpose |
|-----------|---------|
| `test_maintenance_log_template_uses_jsonl_integrity` | **[FAILS]** Detects stale `CSV Integrity` in the log template |
| `test_all_jsonl_files_referenced_in_docs_exist` | All `.jsonl` paths referenced in the docs resolve to existing files |
| `test_no_csv_utils_in_agent_workflow` | No operational `csv_utils` instructions remain in agent-workflow.md |
| `test_no_csv_utils_in_testing_protocol` | No operational `csv_utils` instructions remain in testing-protocol.md |
| `test_no_csv_in_headings_workpackage_rules` | No heading lines in workpackage-rules.md contain bare `CSV` |
| `test_no_csv_in_headings_bug_tracking_rules` | No heading lines in bug-tracking-rules.md contain bare `CSV` |
| `test_no_csv_in_headings_user_story_rules` | No heading lines in user-story-rules.md contain bare `CSV` |
| `test_no_csv_in_headings_testing_protocol` | No heading lines in testing-protocol.md contain bare `CSV` |
| `test_no_csv_in_headings_maintenance_protocol` | No heading lines in maintenance-protocol.md contain bare `CSV` |
| `test_workpackage_rules_no_csv_columns_section` | `## CSV Columns` section removed from workpackage-rules.md |
| `test_bug_tracking_no_csv_columns_section` | `## CSV Columns` section removed from bug-tracking-rules.md |
| `test_user_story_rules_no_csv_columns_section` | `## CSV Columns` section removed from user-story-rules.md |
| `test_recovery_md_references_jsonl_utils_not_csv_utils` | recovery.md references jsonl_utils in operational text |
| `test_all_target_files_are_utf8_decodable` | No encoding corruption in any of the 9 updated files |
| `test_agent_workflow_references_test_results_jsonl` | agent-workflow.md explicitly references test-results.jsonl |

---

## Bugs Found

No formal bugs logged — the stale reference is a minor doc oversight, handled as a TODO below.

---

## TODOs for Developer

- [ ] **Fix `docs/work-rules/maintenance-protocol.md` line 101:** Change `| 3 | CSV Integrity | Pass/Warning/Fail | <findings> |` to `| 3 | JSONL Integrity | Pass/Warning/Fail | <findings> |` in the embedded maintenance log template.

After this fix, re-run `tests/MNT-020/` (all 33 tests must pass: 18 developer + 15 tester).

---

## Verdict

**FAIL — return to Developer.**  
One stale `CSV Integrity` reference survives in the maintenance log template. Fix the line and re-submit for review.
