# Dev Log — MNT-023: Update pre-commit hook for JSONL validation

## Summary

**Status:** In Progress  
**Branch:** MNT-023/pre-commit-jsonl-validation  
**Agent:** Developer Agent  
**Date Started:** 2026-04-04

---

## ADRs Referenced

- **ADR-007** (Active) — *Migrate from CSV to JSONL for All Data Files*: This WP is ADR-007 Phase 3. Validation infrastructure must be updated to reflect the completed CSV→JSONL migration. No supersession required.

---

## Audit Findings

### `scripts/hooks/pre-commit`
**Status: No changes required.**  
The hook is already clean — it resolves the venv Python, locates `validate_workspace.py`, and calls `--full`. No CSV-specific logic is present.

### `scripts/install_hooks.py`
**Status: No changes required.**  
Correctly sets `core.hooksPath` to `scripts/hooks` and verifies the setting. No CSV-specific references.

### `scripts/validate_workspace.py`
**Status: Updates required.** The following gaps were identified:

1. `_check_jsonl_structural()` only checks 4 of 6 JSONL files — missing `docs/decisions/index.jsonl` and `docs/maintenance/orchestrator-runs.jsonl`.
2. No per-row required-field validation (only full-file field discovery via `read_jsonl`).
3. No empty-line-in-middle detection (blank lines between records violate JSONL spec).
4. Comment in `validate_full()` reads `# CSV structural integrity` — stale label.
5. No duplicate-ID check for `decisions/index.jsonl` (uses `ADR-ID` field, not `ID`).

---

## Changes Made

### `scripts/validate_workspace.py`
1. Added `DECISIONS_JSONL` and `MAINT_RUNS_JSONL` path constants.
2. Extended `_check_jsonl_structural()`:
   - Added decisions/index.jsonl (required fields: ADR-ID, Status, Title; valid Status: Active, Superseded, Draft).
   - Added maintenance/orchestrator-runs.jsonl (just parse-level check; no required fields for empty file).
   - Added per-row required-field validation for all 6 JSONL types.
   - Added empty-line-in-middle detection (reads raw file, flags non-trailing blank lines).
3. Added `_check_duplicate_ids(DECISIONS_JSONL, "ADR-ID", result)` in `validate_full()`.
4. Fixed stale comment `# CSV structural integrity` → `# JSONL structural integrity`.

---

## Tests Written

- `tests/MNT-023/test_mnt023_jsonl_validation.py`
  - Tests empty-line detection (middle vs trailing)
  - Tests required-field validation for each file type
  - Tests invalid JSON detection
  - Tests duplicate ID detection (including ADR-ID)
  - Tests valid enum enforcement for WP, Bug, TST, US, and ADR status fields
  - Tests orchestrator-runs: empty file passes, parse error fails
  - Tests decisions/index.jsonl structural checks

---

## Known Limitations

None.
