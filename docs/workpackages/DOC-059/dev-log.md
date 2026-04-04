# Dev Log — DOC-059: Update testing protocol and propose ADR-008

**Developer:** Developer Agent  
**Date Started:** 2026-04-04  
**Status:** In Progress  
**Branch:** DOC-059/testing-protocol-adr008

---

## Prior Art Check

Reviewed `docs/decisions/index.jsonl`. Relevant ADRs:
- **ADR-002** (Mandatory CI Test Gate Before Release Builds) — related to CI green state. ADR-008 complements ADR-002 by addressing the developer-side obligation to keep tests current.
- **ADR-007** (Migrate from CSV to JSONL) — one of the 5 waves of drift that caused CI failure.

No existing ADR covers the "tests must track code" process rule. ADR-008 is a new, non-conflicting addition.

---

## User Story

**US-077**: Fix Stale Test Suite to Unblock CI/CD Releases

The CI release pipeline failed due to accumulated test drift across 5 waves of codebase evolution. This WP documents the root cause and establishes a process rule to prevent recurrence.

---

## Implementation Summary

### Files Created
1. `docs/decisions/ADR-008-tests-track-code.md` — new ADR documenting the "tests must track current codebase state" rule and root cause analysis of the CI failure wave
2. `docs/workpackages/DOC-059/dev-log.md` — this file
3. `tests/DOC-059/test_doc059_adr008.py` — tests verifying ADR-008 exists, index.jsonl has the entry, and testing-protocol.md contains the new rule

### Files Modified
1. `docs/work-rules/testing-protocol.md` — added "Test Maintenance During Refactors" section
2. `docs/decisions/index.jsonl` — added ADR-008 entry

---

## Root Cause Being Documented

The CI release pipeline failed because 5 waves of codebase evolution broke test assertions without updating tests:

1. **Template rename**: `templates/coding/` → `templates/agent-workbench/` (~40 tests)
2. **Agent redesign**: 10 agent files rewritten (~452 tests)
3. **Prefix rename**: `TS-SAE-` → `SAE-` (~27 tests)
4. **Version churn**: 3.2.x → 3.3.11 (~60 tests)
5. **JSONL migration**: CSV → JSONL (~30 tests)

Total: ~688 known failures + ~400 uncovered failures blocking CI.

The existing rule "Test scripts are permanent" prevented deletion but there was NO rule requiring tests to be UPDATED when asserted-against code changes. ADR-008 and the new testing-protocol section close this gap.

This was fixed in FIX-103 through FIX-107 and companion MNT-024.

---

## Tests Written

- `tests/DOC-059/test_doc059_adr008.py`
  - `test_adr008_file_exists` — confirms ADR-008 markdown file exists on disk
  - `test_adr008_in_index_jsonl` — confirms index.jsonl has an entry with ADR-ID "ADR-008"
  - `test_testing_protocol_has_refactor_section` — confirms testing-protocol.md contains the new "Test Maintenance During Refactors" section heading
  - `test_testing_protocol_has_refactor_rule` — confirms testing-protocol.md contains the key rule text about updating tests in the same commit

---

## Known Limitations

None. This WP is purely documentation.

---

## Iteration 2 — Regression Fixes (2026-04-05)

**Tester Verdict (Iteration 1):** FAIL — 2 regressions introduced by DOC-059.

### Regression 1 Fixed: ADR count assertion in DOC-053

**File:** `tests/DOC-053/test_doc053_adr_related_wps.py`  
**Change:** Updated `test_adr_index_has_seven_entries` — changed assertion from `== 7` to `== 8` and updated docstring to reflect ADR-001 through ADR-008.

### Regression 2 Fixed: Stale-path guard in DOC-017

**File:** `tests/DOC-017/test_doc017_tester_edge_cases.py`  
**Change:** Added `STALE_CODING_EXEMPT` set containing `decisions/ADR-008-tests-track-code.md` and `work-rules/testing-protocol.md`. The `test_broad_docs_tree_no_stale_coding` test now skips these files because their references to `templates/coding/` are intentional historical documentation (root-cause analysis), not stale paths.

### Tests Re-run

- `tests/DOC-053/test_doc053_adr_related_wps.py` — all pass
- `tests/DOC-017/test_doc017_tester_edge_cases.py` — all pass
- `tests/DOC-059/` — 18 passed (TST-2602)
