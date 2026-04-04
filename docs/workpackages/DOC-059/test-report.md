# Test Report — DOC-059

**Tester:** Tester Agent  
**Date:** 2026-04-04  
**Iteration:** 1

## Summary

DOC-059 delivers a solid documentation artifact: ADR-008 is well-structured, complete, and accurately documents the root cause of the CI failure wave. The `testing-protocol.md` section is clear, actionable, and correctly cross-references ADR-008. The `index.jsonl` entry is properly formatted.

However, the WP introduced **two test regressions** by violating the very process rule it documents: externally-asserted values changed (ADR count, stale-path guard) without updating the affected tests.

**Verdict: FAIL — Return to Developer**

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| `tests/DOC-059/test_doc059_adr008.py` (8 tests) | Unit | PASS | All developer-written tests pass |
| `tests/DOC-059/test_doc059_edge_cases.py` (10 tests) | Unit | PASS | Tester-added edge cases — all pass |
| Full regression suite | Regression | FAIL | 2 new failures introduced by DOC-059 (see below) |

**TST-2600** — DOC-059 targeted suite: 18 passed (logged)  
**TST-2601** — Full regression suite: 143 failed (logged; 141 are pre-existing per baseline)

---

## Regressions Introduced by DOC-059

### Regression 1: ADR count test broken

**Test:** `tests/DOC-053/test_doc053_adr_related_wps.py::test_adr_index_has_seven_entries`

**Failure:**
```
AssertionError: Expected 7 ADR entries, found 8: 
['ADR-001', 'ADR-002', ..., 'ADR-008']
```

**Root cause:** DOC-053's test was written when 7 ADRs existed. Adding ADR-008 to `index.jsonl` increased the count to 8, but the test was not updated. This is textbook test drift — the exact pattern ADR-008 documents.

---

### Regression 2: Stale-path guard broken

**Test:** `tests/DOC-017/test_doc017_tester_edge_cases.py::test_broad_docs_tree_no_stale_coding`

**Failure:**
```
AssertionError: Found 'templates/coding/' in:
  docs\decisions\ADR-008-tests-track-code.md
  docs\work-rules\testing-protocol.md
```

**Root cause:** The DOC-017 stale-path guard rejects any doc that literally contains `templates/coding/`. ADR-008 and the new testing-protocol section reference the old path in a historical context (documenting Wave 1 of test drift). The test does not exempt historical-documentation files in `docs/decisions/` or the new section in `testing-protocol.md`.

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

None — the regressions above are test gaps, not defects in the documentation content itself.

---

## TODOs for Developer

- [ ] **Fix Regression 1** — Update `tests/DOC-053/test_doc053_adr_related_wps.py::test_adr_index_has_seven_entries` to expect **8** entries instead of 7. The assertion `assert len(rows) == 7` must become `assert len(rows) == 8`. Also update the docstring to say "ADR-001 through ADR-008".

- [ ] **Fix Regression 2** — Resolve the `templates/coding/` literal in docs files. Choose one of:
  - **Option A (preferred):** Update `tests/DOC-017/test_doc017_tester_edge_cases.py::test_broad_docs_tree_no_stale_coding` to add `ADR-008-tests-track-code.md` to the historical-docs exception list, and add `docs/work-rules/testing-protocol.md` to the list of files permitted to reference the old path as historical context.
  - **Option B:** Rephrase the Wave 1 references in `ADR-008-tests-track-code.md` and `testing-protocol.md` to avoid the literal substring `templates/coding/` where possible (e.g., `templates/coding` without the trailing slash), and verify the DOC-017 test no longer flags them.

- [ ] **Pre-handoff:** After fixing, run `python scripts/run_tests.py --wp DOC-059 --type Regression --env "Windows 11 + Python 3.13" --full-suite` and confirm the two regression tests now pass.

- [ ] **Ironically:** This WP violated the process rule it was documenting. The Developer must grep `tests/` for all values changed by a WP before handoff. Explicitly note this in the dev-log update.

---

## Verdict

**FAIL — Return to Developer**

The documentation content quality is high and the 18 DOC-059-specific tests all pass. However, two pre-existing tests were broken by adding ADR-008 (an intended consequence of this WP) without updating those tests. Per `testing-protocol.md` — the very document being updated — test assertions must be updated in the same commit as the change that breaks them.
