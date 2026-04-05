# Dev Log — FIX-109: Update FIX-073 tests to match current template

**Agent:** Developer Agent  
**Date:** 2026-04-05  
**Branch:** FIX-109/update-fix073-tests-to-match-current-template

---

## Prior Art Check

- ADR-003 (Template Manifest and Workspace Upgrade System, Active) — reviewed; relates to template manifest/upgrade system, not directly to agent frontmatter tests. No contradiction.

---

## WP Summary

Update `tests/FIX-073/test_fix073_agent_frontmatter.py` and `test_fix073_edge_cases.py` to match the current 7-agent template. The old tests expected 10 agents (including removed agents: scientist, criticist, fixer, writer, prototyper) and the old model/tool structure. Remove the now-passing FIX-073 entries from `tests/regression-baseline.json`.

---

## Changes Made

### `tests/FIX-073/test_fix073_agent_frontmatter.py`

- Changed `AGENT_FILES` from 10 agents to 7 current agents: programmer, brainstormer, tester, researcher, coordinator, planner, workspace-cleaner.
- Replaced single `CORRECT_MODEL` constant with per-agent model constants:
  - `SONNET_MODEL = ["Claude Sonnet 4.6 (copilot)"]` for programmer, brainstormer, tester, researcher, workspace-cleaner
  - `OPUS_MODEL = ["Claude Opus 4.6 (copilot)"]` for planner
  - `COORDINATOR_MODEL = ["Claude Opus 4.6 (copilot)", "Claude Sonnet 4.6 (copilot)"]` for coordinator
- Updated `EXPECTED_TOOLS` for all 7 agents to match actual frontmatter in each `.agent.md` file.
- Removed tests for removed agents: `test_scientist_tools`, `test_criticist_tools`, `test_fixer_tools`, `test_writer_tools`, `test_prototyper_tools`, `test_scientist_model`, `test_criticist_model`, `test_fixer_model`, `test_writer_model`, `test_prototyper_model`.
- Added tests for new agents: `test_coordinator_tools`, `test_coordinator_model`, `test_workspace_cleaner_tools`, `test_workspace_cleaner_model`.
- Fixed `test_planner_has_ask_tool` to check for `vscode/askQuestions` (not `ask`).
- Fixed `test_readme_example_uses_category_tools` to check for `tools: [read, edit, search]` (not `[read, edit, search, execute]`).
- Fixed `test_readme_example_uses_correct_model` to check for `Claude Sonnet 4.6 (copilot)` (the README example uses Sonnet, not Opus).
- Updated model assertions per-agent instead of using single `CORRECT_MODEL`.

### `tests/FIX-073/test_fix073_edge_cases.py`

- Changed `AGENT_FILES` to the 7 current agents (matching frontmatter.py).
- Updated `test_all_agent_files_exist` docstring from "All 10" to "All 7".
- Changed `test_frontmatter_has_exactly_four_keys` to check required keys are a **subset** (not exactly 4), because coordinator has 6 keys and workspace-cleaner has 5 keys by design.

### `tests/regression-baseline.json`

- Removed all 32 FIX-073 baseline entries (all now pass after test update).
- Updated `_count` and `_updated`.

---

## Tests Written

- All modifications are to existing test files in `tests/FIX-073/`.
- No new test files created (WP modifies existing tests, not adds new infrastructure).

---

## Test Results

- All FIX-073 tests pass.
- Full suite run via `scripts/run_tests.py`.
