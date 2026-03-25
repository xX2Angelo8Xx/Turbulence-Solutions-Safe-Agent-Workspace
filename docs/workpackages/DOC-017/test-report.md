# Test Report — DOC-017

**Tester:** Tester Agent
**Date:** 2026-03-25
**WP:** DOC-017 — Update documentation for template rename
**User Story:** US-041
**Branch:** DOC-017/docs-template-rename
**Verdict:** PASS

---

## Summary

All 7 documentation files updated by the Developer have been verified to contain no stale references to the old template names (`templates/coding/`, `creative-marketing/`, `templates/creative/`). All files correctly reference the new names (`templates/agent-workbench/`, `templates/certification-pipeline/`). The copilot-instructions.md file is 32 lines — well within the 40-line constraint. No regressions were introduced in the full test suite.

---

## Files Reviewed

| File | Stale Refs Removed | New Name Present |
|------|-------------------|-----------------|
| `docs/architecture.md` | ✓ | ✓ |
| `docs/project-scope.md` | ✓ | ✓ |
| `docs/work-rules/agent-workflow.md` | ✓ | ✓ |
| `docs/work-rules/index.md` | ✓ | ✓ |
| `docs/work-rules/maintenance-protocol.md` | ✓ | ✓ |
| `docs/work-rules/security-rules.md` | ✓ | ✓ |
| `.github/instructions/copilot-instructions.md` | ✓ | ✓ |

---

## Test Runs

| ID | Name | Type | Status | Notes |
|----|------|------|--------|-------|
| TST-2128 | Developer tests (18 passed) | Unit | PASS | 9 stale-ref, 8 presence, 1 line-count |
| TST-2129 | Tester edge-case tests (13 passed) | Unit | PASS | Omnibus, creative-marketing per file, table cells, broad tree scan |
| TST-2130 | Full regression suite | Integration | PASS | 5632 passed; 64 pre-existing yaml failures confirmed on main |

---

## Tester Findings

### Gaps Found and Covered

1. **`STALE_PATTERNS` defined but never used** — Developer defined `STALE_PATTERNS` including table-cell patterns (`| Coding |`, `| Creative / Marketing |`) but no test function exercised them. Added `test_no_stale_patterns_in_any_live_doc` (omnibus) and individual table-cell tests.

2. **`creative-marketing` only checked in 2 of 7 files** — Developer tests checked `architecture.md` and `project-scope.md` for `creative-marketing`, but skipped the remaining 5 live-doc files. Added per-file tests for `agent-workflow.md`, `index.md`, `maintenance-protocol.md`, `security-rules.md`, `copilot-instructions.md`.

3. **`agent-workflow.md` presence test missing** — Developer added a "no stale" test for `agent-workflow.md` but no "has new name" test. Added `test_agent_workflow_has_agent_workbench`.

4. **No broad docs-tree scan** — No test swept the entire `docs/` directory tree. Added `test_broad_docs_tree_no_stale_coding` and `test_broad_docs_tree_no_creative_marketing` (excluding historical directories: workpackages, test-results, bugs, Security Audits, maintenance, plans).

5. **`copilot-instructions.md` certification-pipeline presence** — No test verified this file references `certification-pipeline` if it referenced the old creative name. Added check (confirms old name is absent).

All 13 new tester edge-case tests passed.

### Pre-existing Failures (not introduced by DOC-017)

- 14 collection errors in FIX-010, FIX-011, FIX-029, INS-013–INS-017: `ModuleNotFoundError: No module named 'yaml'`
- 64 test failures confirmed pre-existing on `main` branch (network/config issues in INS-019, MNT-002, SAF-010)
- These failures exist identically before and after applying DOC-017 changes

### Scope Compliance

- Historical references in `docs/maintenance/`, `docs/plans/`, `docs/user-stories/user-stories.csv` intentionally left unchanged — they are historical records per the dev-log's stated Known Limitations. This is correct behavior.
- Security Audit files are snapshots and were appropriately excluded.
- No changes to source code, test infrastructure, or templates were made by the Developer — correctly scoped to documentation only.

---

## Checklist

- [x] `dev-log.md` exists and is non-empty
- [x] `test-report.md` written by Tester
- [x] Test files exist in `tests/DOC-017/` (2 files, 31 tests total)
- [x] All test results logged via `scripts/add_test_result.py` (TST-2128, TST-2129, TST-2130)
- [x] `scripts/validate_workspace.py --wp DOC-017` returned exit code 0
- [x] No bugs found — nothing to log in bugs.csv

---

## Verdict: PASS
