# FIX-105 Dev Log — Fix Template Path and Prefix Test Assertions

**WP:** FIX-105  
**Name:** Fix template path and prefix test assertions  
**Status:** Review  
**Assigned To:** Developer Agent  
**Branch:** FIX-105/template-path-prefix-tests  
**Started:** 2026-04-07

---

## Prior Art Check

Reviewed `docs/decisions/index.jsonl` — 7 ADRs found (ADR-001 through ADR-007). None are related to template renaming (UI-041) or prefix renaming (GUI-033). No supersession required.

---

## Problem Statement

After two prior refactors:
1. `templates/coding/` → `templates/agent-workbench/` (GUI-023 / US-041)
2. `TS-SAE-` prefix → `SAE-` prefix (GUI-033 / US-072)

Approximately 70 test assertions still reference the old paths/prefixes, causing 33 known baseline failures:
- 27 GUI prefix failures (GUI-005, GUI-007, GUI-015, GUI-016, GUI-020, GUI-022)
- 6 INS-004 template bundling failures

Additionally, 2 new regressions (not in baseline) exist because `__pycache__` was accidentally committed into the template directory.

---

## Scope

### Sub-task A — Delete pycache pollution from template
- Delete `templates/agent-workbench/.github/hooks/scripts/__pycache__/` (fixes 2 new regressions)

### Sub-task B — Fix 27 GUI prefix tests (TS-SAE- → SAE-)
Files changed:
1. `tests/GUI-015/test_gui015_rename_root_folder.py`
2. `tests/GUI-015/test_gui015_tester_edge_cases.py`
3. `tests/GUI-016/test_gui016_rename_project_folder.py`
4. `tests/GUI-020/test_gui020_create_project_integration.py`
5. `tests/GUI-022/test_gui022_include_readmes_checkbox.py`
6. `tests/GUI-007/test_gui007_validation.py`
7. `tests/GUI-007/test_gui007_tester_additions.py`
8. `tests/GUI-005/test_gui005_project_creation.py`

### Sub-task C — Fix 6 INS-004 template bundling assertions
File changed:
- `tests/INS-004/test_ins004_template_bundling.py`

---

## Implementation Notes

- All changes are mechanical: string replacements in test files only
- No production code changes needed (the actual renames already happened)
- Template structure at `templates/agent-workbench/`:
  - Has `.github/prompts/`: `critical-review.prompt.md`, `debug-workspace.prompt.md`, `prototype.prompt.md`, `root-cause-analysis.prompt.md`
  - Has `.github/skills/`: `agentdocs-update/SKILL.md`, `safety-critical/SKILL.md`
  - `Project/AgentDocs/` contains the project files (no `app.py`, no `requirements.txt`, no `Project/README.md`)
- `test_template_discoverable_and_copyable` last assertion updated to check `AgentDocs/AGENT-RULES.md`

---

## Files Changed

### Template Cleanup
- `templates/agent-workbench/.github/hooks/scripts/__pycache__/` — DELETED

### Test File Updates
- `tests/GUI-005/test_gui005_project_creation.py` — 2 assertions fixed
- `tests/GUI-007/test_gui007_validation.py` — 3 assertions fixed
- `tests/GUI-007/test_gui007_tester_additions.py` — 1 assertion fixed
- `tests/GUI-015/test_gui015_rename_root_folder.py` — 10+ assertions fixed
- `tests/GUI-015/test_gui015_tester_edge_cases.py` — 13 assertions fixed
- `tests/GUI-016/test_gui016_rename_project_folder.py` — 1 assertion fixed
- `tests/GUI-020/test_gui020_create_project_integration.py` — 1 assertion fixed
- `tests/GUI-022/test_gui022_include_readmes_checkbox.py` — 4 assertions fixed
- `tests/INS-004/test_ins004_template_bundling.py` — 6 assertions fixed

### Regression Baseline
- `tests/regression-baseline.json` — removed 33 fixed entries, updated `_count` and `_updated`

---

## Test Results

### FIX-105 Unit Tests
- **Logged:** TST-2587
- **Result:** 9 passed in 0.25s (via `scripts/run_tests.py`)

### Targeted Integration Tests
- `tests/FIX-105/ tests/GUI-005/ tests/GUI-007/ tests/GUI-015/ tests/GUI-016/ tests/GUI-020/ tests/GUI-022/ tests/INS-004/`  
- **Result:** 366 passed, 2 skipped in 13.23s ✅

### Workspace Validation
- `scripts/validate_workspace.py --wp FIX-105` → **All checks passed** ✅

---

## Iteration History

### Iteration 1 (2026-04-07)
- Claimed WP and created dev-log
- Deleted `__pycache__` from template directory
- Fixed `TS-SAE-` → `SAE-` in 8 GUI test files (27 baseline fixes)
- Fixed 6 INS-004 assertions to reflect current template structure
- Fixed 2 extra files: INS-023 + GUI-022 edge_cases (non-baseline TS-SAE- refs)
- Created `tests/FIX-105/` verification tests (9 tests — all pass)
- Updated `tests/regression-baseline.json`: removed 33 entries (_count: 643 → 610)
- **Note:** pycache tests changed to use `git ls-files` instead of disk presence,
  because `conftest.py` unavoidably recreates `__pycache__` at import time
