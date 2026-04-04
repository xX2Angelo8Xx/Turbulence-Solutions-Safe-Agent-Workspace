# Dev Log — MNT-019: Update all agent definitions for JSONL

**WP ID:** MNT-019  
**Status:** In Progress  
**Assigned To:** Developer Agent  
**Branch:** MNT-019/update-agent-defs-jsonl  
**Date:** 2026-04-04  

---

## ADR Acknowledgement

**ADR-007 — Migrate from CSV to JSONL for All Data Files** (Active, 2026-04-04)  
This WP is explicitly listed under ADR-007 Phase 2. All 7 agent/instruction files are being updated to reference the new `.jsonl` data files and `jsonl_utils` utility module, as prescribed by ADR-007.

---

## Summary

Updated all 6 agent definition files in `.github/agents/` and `copilot-instructions.md` in `.github/instructions/` to replace CSV path references with JSONL path references. This completes Phase 2 of the ADR-007 CSV-to-JSONL migration for agent documentation.

---

## Changes Made

### `.github/agents/developer.agent.md`
- Startup steps: `workpackages.csv` → `workpackages.jsonl`, `user-stories.csv` → `user-stories.jsonl`, `index.csv` → `index.jsonl`
- Pre-handoff checklist: `test-results.csv` → `test-results.jsonl`

### `.github/agents/tester.agent.md`
- Startup steps: `workpackages.csv` → `workpackages.jsonl`, `user-stories.csv` → `user-stories.jsonl`
- Workflow step 2: `test-results.csv` → `test-results.jsonl`
- Workflow step 5: `index.csv` → `index.jsonl`
- Edit Permissions: all CSV paths → JSONL paths; "direct CSV editing prohibited" → "direct JSONL editing prohibited"
- Pre-Done Checklist: `test-results.csv` → `test-results.jsonl`, `bugs.csv` → `bugs.jsonl`
- Constraints: "tracking CSVs" → "tracking JSONL files"

### `.github/agents/orchestrator.agent.md`
- Startup: `workpackages.csv` → `workpackages.jsonl`
- Workflow step 2: `index.csv` → `index.jsonl`
- Finalization step 1: `workpackages.csv` → `workpackages.jsonl`
- WP Splitting: `workpackages.csv` → `workpackages.jsonl`

### `.github/agents/planner.agent.md`
- Startup steps: `index.csv` → `index.jsonl`, `workpackages.csv` → `workpackages.jsonl`, `bugs.csv` → `bugs.jsonl`
- Constraints: `workpackages.csv` → `workpackages.jsonl`, "write to any CSV" → "write to any JSONL data file"

### `.github/agents/story-writer.agent.md`
- Description: `user-stories.csv` → `user-stories.jsonl`
- Startup: `user-stories.csv` → `user-stories.jsonl`, `index.csv` → `index.jsonl`
- Step 4: `user-stories.csv` → `user-stories.jsonl`, "column order" → "field order"
- Constraints: `workpackages.csv` → `workpackages.jsonl`, `user-stories.csv` → `user-stories.jsonl`, "the CSV" → "the JSONL file"

### `.github/agents/maintenance.agent.md`
- Startup: `workpackages.csv` → `workpackages.jsonl`, `user-stories.csv` → `user-stories.jsonl`

### `.github/instructions/copilot-instructions.md`
- Key Files table: all 4 CSV paths updated to JSONL paths

---

## Files Changed
- `.github/agents/developer.agent.md`
- `.github/agents/tester.agent.md`
- `.github/agents/orchestrator.agent.md`
- `.github/agents/planner.agent.md`
- `.github/agents/story-writer.agent.md`
- `.github/agents/maintenance.agent.md`
- `.github/instructions/copilot-instructions.md`
- `docs/workpackages/workpackages.jsonl` (WP status updated)
- `docs/workpackages/MNT-019/dev-log.md` (this file)
- `tests/MNT-019/test_mnt019_agent_jsonl_refs.py` (tests)

---

## Tests Written
- `tests/MNT-019/test_mnt019_agent_jsonl_refs.py`
  - 7 tests: one per file, each verifying no `.csv` path references remain
  - Additional tests: verify expected `.jsonl` references exist in each file

---

## Known Limitations
- `docs/work-rules/` files (agent-workflow.md, workpackage-rules.md, etc.) are not in scope for this WP; they still reference `.csv`. Those are handled by separate MNT WPs.
- Historical references to "CSV" format (e.g., in ADR descriptions or migration context) remain unchanged.

---

## Iteration 2 — 2026-04-04

**Returned by Tester:** Defect DEF-001 (BUG-188): Residual generic noun "CSVs" in `.github/agents/planner.agent.md` line 15.

**Root cause:** Developer's test pattern `FORBIDDEN_CSV_PATH_PATTERN` only matched specific filenames (e.g., `workpackages.csv`) and did not catch the generic noun "CSVs" used as a format description. The Tester's edge-case test `test_planner_no_generic_csv_word` exposed this gap.

**Fix applied:**
- `.github/agents/planner.agent.md` line 15: `edit CSVs` → `edit JSONL data files`

**Tests run:** 25 passed, 0 failed (14 original + 11 Tester edge cases) — logged as TST-2561.

**Workspace validation:** Clean (exit code 0).
