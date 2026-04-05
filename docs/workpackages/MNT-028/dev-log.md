# Dev Log — MNT-028: Create ADR-010 Windows-only CI

**Status:** In Progress
**Assigned To:** Developer Agent
**Date:** 2026-04-05

---

## Prior Art Check

Read `docs/decisions/index.jsonl`. Relevant ADRs reviewed:
- **ADR-002** (Mandatory CI Test Gate Before Release Builds) — context for CI decisions.
- **ADR-008** (Tests Must Track Current Codebase State) — referenced in DOC-017 exempt list.
- **ADR-009** (Advisory Pre-Commit Hook) — sibling MNT decision, same decision domain.

No supersession needed. ADR-010 is a new standalone decision.

---

## Implementation

### Files Created / Modified

| File | Action |
|------|--------|
| `docs/decisions/ADR-010-windows-only-ci.md` | Created |
| `docs/decisions/index.jsonl` | Appended ADR-010 entry |
| `tests/DOC-053/test_doc053_adr_related_wps.py` | Updated ADR count assertion: 9 → 10 |
| `tests/MNT-028/test_mnt028_adr010.py` | Created (3 tests) |
| `docs/workpackages/workpackages.jsonl` | Claimed WP (In Progress) |

### DOC-053 Impact

The test `test_adr_index_has_nine_entries` hardcodes the expected count of ADR entries.
After adding ADR-010 that count becomes 10. Updated the assertion and test name accordingly.

### DOC-017 Impact

ADR-010 does not contain the string `templates/coding/`, so the DOC-017 broad-docs-tree
scan will pass without any exemption changes needed.

---

## Tests Written

Three unit tests in `tests/MNT-028/test_mnt028_adr010.py`:

1. `test_adr010_file_exists` — ADR-010 markdown file is present in `docs/decisions/`.
2. `test_adr010_index_entry_exists` — `index.jsonl` contains an entry with `ADR-ID == ADR-010`.
3. `test_adr010_references_mnt027` — ADR-010 markdown mentions MNT-027.

---

## Known Limitations

None.
