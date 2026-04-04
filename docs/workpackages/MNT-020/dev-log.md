# Dev Log — MNT-020

**Developer:** Developer Agent  
**WP:** MNT-020 — Update all work-rules docs for JSONL  
**Branch:** MNT-020/update-work-rules-jsonl  
**Started:** 2026-04-04  

---

## ADR Acknowledgement

ADR-007 (Migrate from CSV to JSONL for All Data Files) is the driving decision for this workpackage. All 6 data files are already in JSONL format (MNT-014 through MNT-018). This WP updates documentation to match the migration.

---

## Goal

Update all 9 documentation files so they reference `.jsonl` instead of `.csv`, JSONL fields instead of CSV columns, and `jsonl_utils` instead of `csv_utils`. Eliminate all operational CSV format descriptions.

---

## Files Changed

| File | Changes |
|------|---------|
| `docs/work-rules/index.md` | Updated file table and decisions link from `.csv` → `.jsonl` |
| `docs/work-rules/agent-workflow.md` | Updated Steps 0, 1, 5, 9 references; CSV → JSONL; test-results; add_test_result |
| `docs/work-rules/workpackage-rules.md` | Renamed "CSV Columns" → "JSONL Fields"; updated tracking reference |
| `docs/work-rules/bug-tracking-rules.md` | Renamed "CSV Columns" → "JSONL Fields"; updated tracking reference; bugs.csv → bugs.jsonl |
| `docs/work-rules/user-story-rules.md` | Renamed "CSV Columns" → "JSONL Fields"; updated tracking references |
| `docs/work-rules/testing-protocol.md` | Updated "Test Result CSV" section → JSONL; test-results.csv → test-results.jsonl; all references updated |
| `docs/work-rules/maintenance-protocol.md` | Updated "CSV Integrity" check to "JSONL Integrity"; bugs.csv → bugs.jsonl |
| `docs/work-rules/recovery.md` | Rewrote "Corrupt CSV File" section to "Corrupt JSONL File"; updated test-results.csv → test-results.jsonl; updated csv_utils → jsonl_utils lock note |
| `docs/architecture.md` | Updated all `.csv` → `.jsonl` in the Key Files table and repo structure |

---

## Implementation Summary

All 9 files were updated to:
1. Replace `.csv` path references with `.jsonl`
2. Rename "CSV Columns" sections to "JSONL Fields"
3. Update "CSV" format descriptions to "JSONL"
4. Replace `csv_utils` references with `jsonl_utils`
5. Update `QUOTE_ALL` / CSV quoting references to JSON serialization
6. Rewrite CSV-specific recovery procedures for JSONL
7. Preserve historical references to "CSV" where they describe the migration itself (ADR-007)

---

## Tests Written

- `tests/MNT-020/test_mnt020_jsonl_docs.py` — verifies no stale `.csv` path references remain in the 9 target files, and verifies expected `.jsonl` references are present

---

## Known Limitations / Decisions

- `scripts/csv_utils.py` still exists (will be deleted in MNT-022 per the plan). Its existence does not affect test outcomes since we test documentation, not scripts.
- Historical mentions of `.csv` in ADR titles or description prose (e.g., "Migrated from CSV to JSONL") are intentionally preserved as audit trail.
