# DOC-030 — Dev Log

## Workpackage
**ID:** DOC-030  
**Name:** Fix Coordinator agent name casing in instructions  
**Branch:** DOC-030/coordinator-name-casing  
**Assigned To:** Developer Agent  
**Status:** In Progress  
**User Story:** US-055  
**Bug:** BUG-120  

---

## Summary

The `coordinator.agent.md` template used lowercase agent names (`programmer`, `tester`, etc.) in both the YAML frontmatter `agents:` list and all `@agent` inline references throughout the body. VS Code performs case-sensitive agent name resolution, so `@programmer` fails to resolve while `@Programmer` succeeds. This caused delegation failures on first attempt for all 10 specialist agents.

---

## Changes Made

### `templates/agent-workbench/.github/agents/coordinator.agent.md`

1. **YAML frontmatter `agents:` list** — changed all 10 names from lowercase to PascalCase:  
   `[programmer, tester, brainstormer, researcher, scientist, criticist, planner, fixer, writer, prototyper]`  
   → `[Programmer, Tester, Brainstormer, Researcher, Scientist, Criticist, Planner, Fixer, Writer, Prototyper]`

2. **How You Work section** — all 10 `@agent` inline references updated to PascalCase:  
   `@planner`, `@programmer`, `@tester`, `@writer`, `@brainstormer`, `@researcher`, `@scientist`, `@criticist`, `@fixer`, `@prototyper`  
   → `@Planner`, `@Programmer`, `@Tester`, `@Writer`, `@Brainstormer`, `@Researcher`, `@Scientist`, `@Criticist`, `@Fixer`, `@Prototyper`

3. **Delegation Table** — all 10 `@agent` table cells updated to PascalCase.

4. **What You Do Not Do section** — two inline references updated (`@programmer`, `@tester`, `@brainstormer`).

---

## Files Changed

| File | Change |
|------|--------|
| `templates/agent-workbench/.github/agents/coordinator.agent.md` | PascalCase agent names throughout |
| `docs/workpackages/workpackages.csv` | Status → In Progress, Assigned To → Developer Agent |

---

## Tests Written

**Location:** `tests/DOC-030/`

| Test File | Tests |
|-----------|-------|
| `test_doc030_coordinator_casing.py` | 1. Frontmatter agents list PascalCase; 2. All @-refs in body PascalCase; 3. No lowercase @agent refs remain; 4. Delegation table entries PascalCase; 5. All 10 expected agents present |

---

## Test Results

All tests passed. See test-results.csv for logged results.

---

## Bugs Closed

| Bug | Fixed In |
|-----|----------|
| BUG-120 | DOC-030 |
