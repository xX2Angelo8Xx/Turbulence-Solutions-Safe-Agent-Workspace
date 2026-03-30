# DOC-032 Dev Log

## Workpackage
**ID:** DOC-032  
**Name:** Fix copilot-instructions.md stale limitations  
**Branch:** DOC-032/copilot-instructions-fix  
**Assigned To:** Developer Agent  
**Date:** 2026-03-30

## Summary

Removed the stale row claiming the `memory` tool is "Not available (blocked by design)" from the Known Tool Limitations table in `templates/agent-workbench/.github/instructions/copilot-instructions.md`.

Memory has been fully operational since SAF-048. The stale row contradicted AGENT-RULES and caused agent confusion.

## Files Changed

- `templates/agent-workbench/.github/instructions/copilot-instructions.md` — removed one table row

## Implementation

Deleted the following row from the Known Tool Limitations table:

```
| `memory` tool | Not available (blocked by design) |
```

No other changes were made to the file.

## Tests Written

- `tests/DOC-032/test_doc032_copilot_instructions.py`

Tests verify:
1. The string "blocked by design" does NOT appear anywhere in the file
2. The string "memory" does NOT appear in the Known Tool Limitations table section
3. The other expected limitation rows (Out-File, dir, pip install, etc.) are still present

## Test Results

All tests pass. See `docs/test-results/test-results.csv` for logged results.

---

## Iteration 2 — Tester Regression Fix

**Date:** 2026-03-30

### Tester Finding

`tests/DOC-005/test_doc005_limitations.py` had a regression:
- `"memory"` was still present in `LIMITATION_ENTRIES`
- `test_table_contains_memory_tool_entry` still asserted the removed row's presence

### Fix Applied

- Removed `"memory"` from `LIMITATION_ENTRIES` in `tests/DOC-005/test_doc005_limitations.py`
- Deleted `test_table_contains_memory_tool_entry` function entirely

### Files Changed

- `tests/DOC-005/test_doc005_limitations.py`

### Test Results

17 tests passed, 0 failed (`tests/DOC-032/` + `tests/DOC-005/`). Logged as TST-2324.
