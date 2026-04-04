# MNT-014: Create ADR-007 and Migration Plan

## Summary
Created ADR-007 documenting the CSV-to-JSONL migration decision, including rationale, migration strategy, and linked workpackages (MNT-014 through MNT-023).

## Implementation
- Created `docs/decisions/ADR-007-csv-to-jsonl-migration.md`
- Added ADR-007 entry to `docs/decisions/index.csv` (later migrated to JSONL)
- Created 10 workpackages (MNT-014 through MNT-023) covering the full migration

## Decisions
- JSONL chosen over YAML/SQLite for line-oriented diffs and streaming reads
- Migration executed in 10 atomic WPs to minimize risk
- Orchestrator-managed task (no feature branch — executed on main)

## Tests
- Validation: ADR file exists and follows standard format
- All 10 WPs created with correct IDs, categories, and descriptions
