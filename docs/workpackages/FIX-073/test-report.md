# Test Report — FIX-073

**Tester:** Tester Agent  
**Date:** 2026-03-25  
**WP:** FIX-073 — Fix template agent YAML frontmatter  
**Branch:** FIX-073/agent-frontmatter  
**Bugs addressed:** BUG-108, BUG-109  
**Verdict:** PASS

---

## Summary

FIX-073 correctly updates all 10 agent files in `templates/agent-workbench/.github/agents/` from individual tool names to VS Code tool categories, changes the model to `['Claude Opus 4.6 (copilot)']`, adds `ask` + `edit` tools and `plan.md` capability to the planner, removes `fetch_webpage` from the researcher body, updates the README example, and updates all DOC-019 through DOC-028 test files. All changes are correct and complete.

---

## Code Review

| Area | Finding |
|------|---------|
| Frontmatter tools (10 agents) | All agents use correct VS Code categories: `read`, `edit`, `search`, `execute`, `ask` — no old individual names remain |
| Model syntax (10 agents) | All agents now use `model: ['Claude Opus 4.6 (copilot)']` — correct YAML list format |
| Planner body (BUG-109) | `ask` and `edit` added to tools; body describes clarifying questions and `plan.md` creation; old "no edit tools by design" text removed |
| Researcher body (BUG-108) | Step 4 of "How You Work" no longer references `fetch_webpage` — replaced with `read` and `search` |
| README.md example | Shows `tools: [read, edit, search, execute]` and `model: ['Claude Opus 4.6 (copilot)']` — correct |
| DOC-019 – DOC-028 tests | All updated to assert new category names and new model format — no stale assertions |

---

## Tests Run

| Run | Test IDs | Type | Count | Result |
|-----|----------|------|-------|--------|
| Targeted suite | TST-2169 | Regression | 515 | PASS |
| Edge-case tests | TST-2170 | Unit | 41 | PASS |
| Full regression | TST-2171 | Regression | 1013+1 | 1013 PASS / 1 pre-existing FAIL |

### Developer tests (29 in FIX-073 suite)
- 10 tools-correctness tests (one per agent)
- 10 model-correctness tests (one per agent)
- `test_no_old_tool_names_in_any_agent` — scans frontmatter tools list
- `test_fetch_webpage_not_in_any_agent` — frontmatter scan
- `test_planner_has_ask_tool` / `test_planner_has_edit_tool` — BUG-109
- `test_planner_body_mentions_plan_md` — BUG-109
- `test_planner_body_mentions_ask_capability` — BUG-109
- `test_planner_no_longer_says_no_edit_tools` — BUG-109
- `test_readme_example_uses_category_tools` / `test_readme_example_uses_correct_model` / `test_readme_no_old_model`

### Tester edge-case tests (12 in `test_fix073_edge_cases.py`)
- `test_all_agent_files_exist` — existence check for all 10 files
- `test_old_model_not_in_any_file_content` — full-file scan, not just frontmatter
- `test_fetch_webpage_not_in_researcher_body` — body text scan
- `test_fetch_webpage_not_in_any_agent_body` — body text scan for all agents
- `test_tools_is_list_in_all_agents` — YAML type check (list, not string)
- `test_model_is_list_in_all_agents` — YAML type check (list, not string)
- `test_frontmatter_has_exactly_four_keys` — no extra/missing keys
- `test_no_old_tool_names_in_planner_body` — planner body text scan
- `test_no_agent_has_empty_tools_list` — non-empty tools guard
- `test_all_tool_values_are_non_empty_strings` — tool entry type guards
- `test_readme_no_old_model_anywhere` — full README file scan

---

## Pre-Existing Failure (unrelated to FIX-073)

**Test:** `tests/FIX-007/test_fix007_mock_pattern.py::TestGUI012WindowHeight::test_window_height_assertion_matches_app`

**Status:** Pre-existing on `main` before FIX-073 was branched. Not introduced by this WP.

**Cause:** The test checks that `tests/GUI-012/test_gui012_spacing.py` contains a height string literal (`"520"` or `"590"`), but the GUI-012 test file uses a dynamic comparison (`height >= 400`), not a hardcoded string. The test assertion in FIX-007 is stale.

**Action:** Logged as **BUG-110**. FIX-073 does not touch these files and is not responsible for this failure.

---

## Security Review

No security concerns. Changes are limited to YAML frontmatter and Markdown body text in template agent files. No executable code, credentials, or sensitive data involved.

---

## Edge-Case Analysis

| Scenario | Covered? | Result |
|----------|----------|--------|
| Tool value is plain string instead of YAML list | Yes — `test_tools_is_list_in_all_agents` | PASS |
| Model value is plain string instead of YAML list | Yes — `test_model_is_list_in_all_agents` | PASS |
| Old model string in agent body (not just frontmatter) | Yes — `test_old_model_not_in_any_file_content` | PASS |
| `fetch_webpage` in agent body text | Yes — `test_fetch_webpage_not_in_any_agent_body` | PASS |
| Extra or missing frontmatter keys | Yes — `test_frontmatter_has_exactly_four_keys` | PASS |
| Old tool names in planner body text | Yes — `test_no_old_tool_names_in_planner_body` | PASS |
| Empty tools list | Yes — `test_no_agent_has_empty_tools_list` | PASS |
| Invalid (non-string) tool entries | Yes — `test_all_tool_values_are_non_empty_strings` | PASS |
| Agent file missing from disk | Yes — `test_all_agent_files_exist` | PASS |
| Race conditions / concurrency | N/A — read-only template files, no state | — |
| Platform differences | N/A — pure YAML/Markdown parsing, pathlib | — |

---

## Acceptance Criteria Verification

From BUG-108:
- [x] All 10 agents use VS Code tool categories (not individual names)
- [x] Model is `['Claude Opus 4.6 (copilot)']` in all 10 agents
- [x] README example shows correct syntax

From BUG-109:
- [x] Planner has `ask` and `edit` in tools list
- [x] Planner body describes `ask` capability for clarifying questions
- [x] Planner body describes `plan.md` creation
- [x] Planner body no longer says "no edit tools by design"

---

## Bugs Logged

| Bug | Title | Severity |
|-----|-------|---------|
| BUG-110 | FIX-007 test_window_height_assertion_matches_app uses stale height literal check | Low |

---

## Verdict: PASS

All 41 FIX-073 tests pass. All 515 targeted-suite tests pass. The one full-regression failure is pre-existing (BUG-110) and unrelated to this workpackage. Implementation fully satisfies BUG-108 and BUG-109 acceptance criteria.
