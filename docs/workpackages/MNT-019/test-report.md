# Test Report — MNT-019: Update all agent definitions for JSONL

**Tester:** Tester Agent  
**Date:** 2026-04-04  
**Iteration 1 Verdict:** ❌ FAIL — Returned to Developer  
**Iteration 2 Verdict:** ✅ PASS — Done  
**Branch:** MNT-019/update-agent-defs-jsonl

---

## Summary

The Developer updated all 7 agent/instruction files to replace `.csv` path references with `.jsonl`. The 14 Developer-authored tests all pass. However, one residual "CSVs" word reference was found in `planner.agent.md` that was not caught by the Developer's tests (which only checked for filename-pattern matches like `workpackages.csv`, not generic word usage).

---

## Test Execution Results

### MNT-019 Developer Tests (14 tests)
**Result: 14 passed, 0 failed**

All path-reference tests and JSONL-presence tests pass:
- `test_developer_no_csv_path_refs` ✅
- `test_tester_no_csv_path_refs` ✅
- `test_orchestrator_no_csv_path_refs` ✅
- `test_planner_no_csv_path_refs` ✅
- `test_story_writer_no_csv_path_refs` ✅
- `test_maintenance_no_csv_path_refs` ✅
- `test_copilot_instructions_no_csv_path_refs` ✅
- `test_developer_has_jsonl_refs` ✅
- `test_tester_has_jsonl_refs` ✅
- `test_orchestrator_has_jsonl_refs` ✅
- `test_planner_has_jsonl_refs` ✅
- `test_story_writer_has_jsonl_refs` ✅
- `test_maintenance_has_jsonl_refs` ✅
- `test_copilot_instructions_has_jsonl_refs` ✅

### Tester Edge-Case Tests (11 tests — added by Tester)
**Result: 10 passed, 1 FAILED**

File: `tests/MNT-019/test_mnt019_edge_cases.py`

- `test_developer_no_generic_csv_word` ✅
- `test_tester_no_generic_csv_word` ✅
- `test_orchestrator_no_generic_csv_word` ✅
- **`test_planner_no_generic_csv_word` ❌ FAILED**
- `test_story_writer_no_generic_csv_word` ✅
- `test_maintenance_no_generic_csv_word` ✅
- `test_copilot_instructions_no_generic_csv_word` ✅
- `test_all_seven_files_exist` ✅
- `test_referenced_jsonl_files_exist` ✅
- `test_tester_prohibits_direct_jsonl_editing` ✅
- `test_tester_tracking_terminology` ✅

### Full Test Suite Regression Check
**Result: No new regressions from MNT-019**

Full suite: 744 failed, 8278 passed. All 744 failures are pre-existing entries in `tests/regression-baseline.json` or unrelated to MNT-019 changes (they test `templates/agent-workbench/` template files and ADR index content that MNT-019 did not touch).

---

## Defect Found

### DEF-001: Residual "CSVs" word in planner.agent.md (missed update)

**File:** `.github/agents/planner.agent.md`  
**Line:** 15  
**Current text:**
```
You are the **Planner Agent** for the Turbulence Solutions project. You analyze feature requests, bug reports, and security gaps — then produce structured, actionable plans. You never write code, edit CSVs, or create workpackages.
```

**Expected text:**
```
You are the **Planner Agent** for the Turbulence Solutions project. You analyze feature requests, bug reports, and security gaps — then produce structured, actionable plans. You never write code, edit JSONL data files, or create workpackages.
```

**Root cause:** The Developer's test pattern (`FORBIDDEN_CSV_PATH_PATTERN`) only matched specific filenames like `workpackages.csv`, `user-stories.csv`, etc. It did not match the generic noun "CSVs" used as a format description. The WP description explicitly says "Change all path references, **format descriptions**, and **operational instructions** from CSV to JSONL" — this word falls under both categories.

---

## ADR Conflict Check

No ADR conflicts found. This WP is explicitly listed as Phase 2 of ADR-007 (Migrate from CSV to JSONL for All Data Files). The change is compliant.

---

## Security Analysis

This WP only modifies documentation/instruction files. No security-relevant code paths were changed. No attack vectors introduced.

---

## TODOs for Developer (Required to resume)

1. **Fix `planner.agent.md` line 15:** Change `edit CSVs` → `edit JSONL data files` in the description paragraph.

   Before:
   ```
   You never write code, edit CSVs, or create workpackages.
   ```
   After:
   ```
   You never write code, edit JSONL data files, or create workpackages.
   ```

2. **Do NOT broaden the test's FORBIDDEN_CSV_PATH_PATTERN** — the Tester has already added `tests/MNT-019/test_mnt019_edge_cases.py` which covers generic CSV word detection. After fixing the text, all 25 tests (14 Developer + 11 Tester) must pass.

3. Re-run `scripts/validate_workspace.py --wp MNT-019` and confirm exit code 0.

4. Commit the fix and push. Hand off back to Tester.

---

## Iteration 2 — Tester Re-Review (2026-04-04)

### Fix Verified

`.github/agents/planner.agent.md` line 15 now reads:
```
You never write code, edit JSONL data files, or create workpackages.
```
The word "CSVs" is gone. `test_planner_no_generic_csv_word` passes.

### Full MNT-019 Test Suite — Iteration 2

**Command:** `pytest tests/MNT-019/ -v`  
**Result:** 25 passed, 0 failed  
**Test Run ID:** TST-2562

All tests pass:
- 14 Developer path-reference tests ✅
- 11 Tester edge-case tests (including `test_planner_no_generic_csv_word`) ✅

### DEF-001 Resolution

DEF-001 (BUG-188) is confirmed resolved:
- Fix verified in source file ✅
- Regression test passes ✅
- BUG-188 status updated: Open → Fixed → Closed ✅

### workspace validation

`scripts/validate_workspace.py --wp MNT-019` — Passed with 1 warning (BUG-188 Fixed In WP now set, warning resolved after update).

### Security & Regression

No security-relevant code changes. No new failures against regression baseline.
