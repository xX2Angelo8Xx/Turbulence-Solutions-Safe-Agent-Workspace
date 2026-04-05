# Dev Log — MNT-026: Create ADR-009 cross-WP test impact

**Status:** In Progress  
**Assigned To:** Developer Agent  
**Date Started:** 2026-04-05

## Prior Art Check

- ADR-008 (`docs/decisions/ADR-008-tests-track-code.md`) is directly related — it established the rule that tests must track code changes. ADR-009 extends ADR-008 by adding enforcement tooling (advisory pre-commit hook). Referenced in this ADR.
- MNT-025 created `scripts/check_test_impact.py` — the hook being documented here.

## Implementation Summary

Created `docs/decisions/ADR-009-cross-wp-test-impact.md` documenting the decision to add an advisory pre-commit hook (`scripts/check_test_impact.py`) for cross-WP test impact detection.

Added ADR-009 entry to `docs/decisions/index.jsonl`.

## Files Changed

- `docs/decisions/ADR-009-cross-wp-test-impact.md` — new ADR
- `docs/decisions/index.jsonl` — new entry for ADR-009
- `tests/MNT-026/test_adr_009.py` — tests verifying ADR existence, index entry, and content

## Tests Written

- `tests/MNT-026/test_adr_009.py`
  - `test_adr_009_file_exists` — verifies the ADR file exists
  - `test_adr_009_required_sections` — verifies Title, Status, Context, Decision, Consequences sections
  - `test_adr_009_index_entry` — verifies index.jsonl has the ADR-009 entry
  - `test_adr_009_references_mnt025` — verifies ADR-009 content references MNT-025

## Known Limitations

None. This WP is purely documentation.

---

## Iteration 2 — 2026-04-05

### Tester Findings

The Tester found 2 regressions caused by adding ADR-009:
1. `tests/DOC-053/test_doc053_adr_related_wps.py::test_adr_index_has_seven_entries` — hardcoded count of 8 ADRs, now 9.
2. `tests/DOC-017/test_doc017_tester_edge_cases.py::test_broad_docs_tree_no_stale_coding` — ADR-009 contains `templates/coding/` in a historical context table; was not in `STALE_CODING_EXEMPT`.

### Changes Made

- `tests/DOC-053/test_doc053_adr_related_wps.py` — Renamed `test_adr_index_has_seven_entries` → `test_adr_index_has_nine_entries`; updated assertion and docstring to expect 9 ADR entries.
- `tests/DOC-017/test_doc017_tester_edge_cases.py` — Added `"decisions/ADR-009-cross-wp-test-impact.md"` to `STALE_CODING_EXEMPT` set.

### Test Results

- `tests/DOC-053/ tests/DOC-017/ tests/MNT-026/`: 60 passed, 0 failed.
- Full suite: 72 failures, all covered by `tests/regression-baseline.json` (77 entries). No new regressions.
