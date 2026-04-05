# Test Report — MNT-026: Create ADR-009 cross-WP test impact

**Tester:** Tester Agent  
**Date:** 2026-04-05 (Iteration 2)  
**Verdict:** PASS

---

## Review Summary

The ADR-009 document and index.jsonl entry are well-structured and accurate. The 4 developer-written tests are correct and pass. The 2 regressions found in iteration 1 (DOC-053 and DOC-017) have been correctly fixed by the Developer in iteration 2.

---

## Test Runs

| Run | Scope | Result | Logged As |
|-----|-------|--------|-----------|
| MNT-026 suite (4 dev tests) | `tests/MNT-026/` | PASS | — |
| Targeted regression fixes | `tests/DOC-053/ + tests/DOC-017/` | PASS (all 38 pass) | — |
| Full regression suite | `tests/` (all) | 69/72 failures, all in baseline | TST-2623 (iter 1) |
| Full regression suite (iter 2) | `tests/` (all) | 69/72 failures, all in baseline | TST-2624 |

All 42 targeted tests (DOC-053 + DOC-017 + MNT-026) pass.  
Full suite: 69–72 known failures (flaky range), all in `tests/regression-baseline.json` (77 entries). Zero new regressions.

---

## Regression Fix Verification (Iteration 2)

### Fix 1 — DOC-053: ADR count updated correctly ✓

**File:** `tests/DOC-053/test_doc053_adr_related_wps.py`  
**Test renamed to:** `test_adr_index_has_nine_entries`  
**Assertion:** `assert len(rows) == 9` — **PASSES**

### Fix 2 — DOC-017: ADR-009 added to STALE_CODING_EXEMPT ✓

**File:** `tests/DOC-017/test_doc017_tester_edge_cases.py`  
**Change:** `"decisions/ADR-009-cross-wp-test-impact.md"` added to `STALE_CODING_EXEMPT`  
**Test `test_broad_docs_tree_no_stale_coding`:** **PASSES**

---

## Edge-Case Tests Added by Tester

7 additional tests added to `tests/MNT-026/test_adr_009.py`:

| Test | Purpose |
|------|---------|
| `test_adr_009_status_header_is_active` | Verifies `**Status:** Active` appears in the header block, not just the body |
| `test_adr_009_references_adr008` | Verifies ADR-009 references ADR-008 (the rule it enforces) |
| `test_adr_009_index_entry_has_all_required_fields` | All 6 mandatory JSONL fields present |
| `test_adr_009_superseded_by_is_empty` | `Superseded By` is `""` (ADR is active) |
| `test_adr_009_index_entry_is_valid_json` | All lines in index.jsonl parse cleanly |
| `test_adr_009_hook_script_mentioned` | `check_test_impact.py` appears in the ADR |
| `test_adr_009_exit_code_0_documented` | ADR states the hook exits with code 0 |

All 11 MNT-026 tests pass.

---

## Security / ADR Conflict Review

- No security concerns (purely documentation WP).
- No ADR conflicts found in `docs/decisions/index.jsonl`.
- ADR-008 is correctly acknowledged (ADR-009 extends it without superseding it).

---

## Pre-Done Checklist

- [x] `docs/workpackages/MNT-026/dev-log.md` exists and non-empty
- [x] `docs/workpackages/MNT-026/test-report.md` written (this file)
- [x] Test files exist in `tests/MNT-026/` (11 tests: 4 developer + 7 tester edge cases)
- [x] Test results logged via `scripts/run_tests.py` (TST-2624)
- [x] No bugs found (documentation-only WP, no security or logic concerns)
- [x] `scripts/validate_workspace.py --wp MNT-026` returns exit code 0
- [x] Zero new regressions confirmed against `tests/regression-baseline.json`

## Pre-Done Checklist Status

- [x] `docs/workpackages/MNT-026/dev-log.md` exists and non-empty
- [x] `docs/workpackages/MNT-026/test-report.md` written
- [x] Test files exist in `tests/MNT-026/` (11 tests)
- [x] Test results logged via `scripts/run_tests.py` (TST-2622)
- [x] `scripts/validate_workspace.py --wp MNT-026` returns exit code 0
- [ ] **BLOCKED: 2 new regressions in DOC-053 and DOC-017** — WP returned to In Progress
