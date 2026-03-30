# DOC-033 Dev Log — README management for agent-workbench template

**Status:** Review  
**Assigned To:** Developer Agent  
**Branch:** `DOC-033/readme-management`  
**User Story:** US-067
**Iteration:** 2

---

## Summary

Two changes to `templates/agent-workbench/`:
1. Replace existing agent-facing `README.md` with a minimal user-facing version.
2. Delete `templates/agent-workbench/.github/agents/README.md` (developer-only document).

---

## Implementation

### Files Changed
- `templates/agent-workbench/README.md` — replaced with user-facing workspace overview (uses `{{PROJECT_NAME}}` and `{{WORKSPACE_NAME}}` placeholders)
- `templates/agent-workbench/.github/agents/README.md` — deleted

### Decisions
- The existing README.md was agent-facing (describing security zones to AI agents). Replaced with a brief user-facing document per WP scope.
- Kept the new README under 30 lines for brevity.
- `{{PROJECT_NAME}}` and `{{WORKSPACE_NAME}}` are template placeholders replaced by the launcher at workspace creation time.

---

## Tests

Tests in `tests/DOC-033/test_doc033_readme_management.py`:
1. `templates/agent-workbench/README.md` exists
2. Contains `{{PROJECT_NAME}}` placeholder
3. Contains `{{WORKSPACE_NAME}}` placeholder
4. Mentions `NoAgentZone`
5. Is under 50 lines
6. `templates/agent-workbench/.github/agents/README.md` does NOT exist

---

## Iteration 2 — 2026-03-30

**Trigger:** Tester returned WP to In Progress (test-report.md). 8 DOC-002 regression tests failed because the new user-facing README replaced the old agent-facing README that the DOC-002 tests were checking for. Bug: BUG-162.

### Root Cause
DOC-002 tests were tightly coupled to the old README's security-zone content (Tier 1/2, Exempt Tools) and assumed exactly 4 `{{PROJECT_NAME}}` occurrences and no `{{WORKSPACE_NAME}}`. The new user-facing README has 3 `{{PROJECT_NAME}}` occurrences and uses `{{WORKSPACE_NAME}}` as its title.

### Files Changed
- `tests/DOC-002/test_doc002_readme_placeholders.py` — replaced 3 stale security-zone assertions (`test_placeholder_present_in_tier1_description`, `test_placeholder_present_in_tier2_description`, `test_placeholder_present_in_exempt_tools_section`) with equivalent assertions against the new README content (`test_placeholder_present_in_getting_started_section`, `test_placeholder_present_in_agent_rules_section`, `test_placeholder_present_in_folder_table_row`)
- `tests/DOC-002/test_doc002_tester_edge_cases.py` — updated `TestPlaceholderCount` class: count assertions `== 4` → `== 3`, flipped `{{WORKSPACE_NAME}} not in content` assertions to `{{WORKSPACE_NAME}} in content`; updated `test_all_four_actual_readme_occurrences_replaced` → `test_all_three_actual_readme_occurrences_replaced` (count 4→3, added `{{WORKSPACE_NAME}} not in result` assertion)
- `docs/bugs/bugs.csv` — BUG-162 status set to Fixed, Fixed In WP = DOC-033

### Test Results (Iteration 2)
- TST-2330: DOC-033 Iteration 2 regression fix — 42 passed, 0 failed (DOC-033 + DOC-002 suites combined)
