# Test Report — DOC-059

**Tester:** Tester Agent  
**Date:** 2026-04-05 (Iteration 2 — updated)  
**Iteration:** 2

## Summary

DOC-059 delivers a solid documentation artifact: ADR-008 is well-structured, complete, and accurately documents the root cause of the CI failure wave. The `testing-protocol.md` section is clear, actionable, and correctly cross-references ADR-008. The `index.jsonl` entry is properly formatted.

Iteration 1 found two regressions; Iteration 2 confirms those are fully resolved. No new regressions were introduced by DOC-059.

**Verdict: PASS**

---

## Tests Executed

### Iteration 1 (2026-04-04)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| `tests/DOC-059/test_doc059_adr008.py` (8 tests) | Unit | PASS | All developer-written tests pass |
| `tests/DOC-059/test_doc059_edge_cases.py` (10 tests) | Unit | PASS | Tester-added edge cases — all pass |
| Full regression suite | Regression | FAIL | 2 new failures introduced by DOC-059 |

**TST-2600** — DOC-059 targeted suite: 18 passed (logged)  
**TST-2601** — Full regression suite: 143 failed (141 pre-existing + 2 DOC-059 regressions)

### Iteration 2 (2026-04-05)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| `tests/DOC-059/test_doc059_adr008.py` (8 tests) | Unit | PASS | |
| `tests/DOC-059/test_doc059_edge_cases.py` (10 tests) | Unit | PASS | |
| `tests/DOC-053/test_doc053_adr_related_wps.py` | Regression | PASS | Regression 1 fixed — `test_adr_index_has_seven_entries` now asserts 8 |
| `tests/DOC-017/test_doc017_tester_edge_cases.py` | Regression | PASS | Regression 2 fixed — `test_broad_docs_tree_no_stale_coding` exempts historical docs |
| Full regression suite | Regression | PASS | 138 failed (all ≤ 147 baseline); no new regressions from DOC-059 |

**TST-2603** — DOC-059 Iteration 2 targeted suite: 18 passed  
**TST-2604** — Regression fix verification (DOC-053 + DOC-017): pass  
**TST-2605** — Full regression suite: 138 failed, all baseline-known

---

## Regressions from Iteration 1 — Resolution Status

### Regression 1: ADR count test broken

**Test:** `tests/DOC-053/test_doc053_adr_related_wps.py::test_adr_index_has_seven_entries`

**Fix (Iteration 2):** Assertion updated from `== 7` to `== 8`. Docstring updated to reference ADR-001 through ADR-008. **RESOLVED ✓**

---

### Regression 2: Stale-path guard broken

**Test:** `tests/DOC-017/test_doc017_tester_edge_cases.py::test_broad_docs_tree_no_stale_coding`

**Fix (Iteration 2):** `STALE_CODING_EXEMPT` set added containing `decisions/ADR-008-tests-track-code.md` and `work-rules/testing-protocol.md`. Both files contain intentional historical references to `templates/coding/` as root-cause documentation. **RESOLVED ✓**

---

## Edge-Case Tests Added by Tester

File: `tests/DOC-059/test_doc059_edge_cases.py` — 10 tests

| Test | Purpose |
|------|---------|
| `test_adr008_documents_all_five_waves` | Verifies all 5 drift waves are in the Context table |
| `test_adr008_related_wps_include_all_fix_wps` | Verifies all 7 Related WPs in index.jsonl entry |
| `test_adr008_file_mentions_all_fix_wps_in_text` | Verifies ADR body references FIX-103—107, MNT-024 |
| `test_adr008_clarifies_permanent_vs_immutable` | Verifies the "permanent ≠ immutable" distinction is present |
| `test_testing_protocol_permanent_rule_clarification` | Verifies protocol mentions assertions must evolve |
| `test_testing_protocol_refactor_section_has_grep_example` | Verifies a grep command example is in the checklist |
| `test_adr008_has_notes_section` | Verifies ADR-008 includes a Notes section |
| `test_adr008_index_entry_has_superseded_by_field` | Verifies `Superseded By` field is present and empty |
| `test_index_jsonl_is_valid_jsonl` | Verifies every line of index.jsonl parses as valid JSON |
| `test_adr008_file_not_empty` | Verifies ADR-008 is not a stub (> 500 chars) |

---

## Bugs Found

None.

---

## Verdict

**PASS — Marking Done**

All 18 DOC-059 tests pass. Both Iteration 1 regressions are resolved. The full regression suite (138 failures) is entirely within the 147-entry baseline — no new regressions from DOC-059. Documentation quality is high: ADR-008 is well-structured, complete, and accurately documents the CI failure root cause. The `testing-protocol.md` section is actionable and correctly cross-references ADR-008.
