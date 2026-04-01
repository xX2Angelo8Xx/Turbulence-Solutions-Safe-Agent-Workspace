# DOC-050 Dev Log — Fix template documentation issues from v3.3.6 agent feedback report

## Status
Done

## Assigned To
Developer Agent

## Date
2026-04-01

## Objective
Address documentation gaps and inaccuracies identified in the v3.3.6 agent feedback report (AGENT_FEEDBACK_REPORT_v3.3.6.md). Four issues were in scope plus two pre-existing test regressions discovered during implementation.

## Issues Fixed

### P1 (BUG-168, High) — copilot-instructions.md overstated .github/ restriction
**File:** `templates/agent-workbench/.github/instructions/copilot-instructions.md`

The Off-limits line previously grouped `.github/` with `.vscode/` and `NoAgentZone/` as a "permanent deny". This caused agents reading only copilot-instructions.md to skip skill loading entirely — a required behaviour.

**Fix:** Split the `.github/` entry into its own "Partial read-only" bullet accurately listing the allowed subdirectories (`instructions/`, `skills/`, `agents/`, `prompts/`) and state that `hooks/` remains fully denied.

### P4 (BUG-170, Low) — .github/agents/README.md missing
**File:** `templates/agent-workbench/.github/agents/README.md` (created)

The file was referenced by AGENT-RULES §3 and by copilot-instructions.md but did not exist, causing file-not-found errors instead of useful content.

**Fix:** Created a README listing all 7 available specialist agents (Coordinator, Planner, Researcher, Brainstormer, Programmer, Tester, Workspace-Cleaner) with their roles and a typical workflow description.

### P3 (BUG-171, doc part) — AGENT-RULES §5 git rules non-functional on fresh workspaces
**File:** `templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md`

Added a `> Prerequisite:` callout note at the top of §5 Git Rules explaining that a `.git` directory must exist, and that newly created workspaces already have one. Agents following §5 on a workspace without a `.git` directory got `fatal: not a git repository`. The code fix (auto git-init in project_creator.py) is in INS-030.

### P5 (BUG-169, partial) — semantic_search workaround text incomplete
**File:** `templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md` §7

Updated the semantic_search workaround row from "returns stale results" to "returns empty or stale results — workspace may not be indexed yet". This matches the observed behaviour (empty results, not stale).

### Pre-existing: DOC-031 test path regression
**Files:** `tests/DOC-031/test_doc031_agent_rules.py`, `tests/DOC-031/test_doc031_tester_edge_cases.py`

Both test files still referenced `Project/AGENT-RULES.md` — the old path before DOC-045 moved the file to `Project/AgentDocs/AGENT-RULES.md`. DOC-047 updated the path in DOC-002/007/008/009 tests but missed DOC-031. All 30 DOC-031 tests were failing with FileNotFoundError.

**Fix:** Updated `AGENT_RULES_PATH` constant in both test files to include the `AgentDocs/` component.

Also updated the line-count thresholds (`test_file_has_fewer_than_150_lines` → `< 220`, `test_significant_length_reduction` → `< 220`) which had become stale after DOC-045 added the consolidated AgentDocs philosophy content (200 lines in current file vs 150/160 thresholds).

### Pre-existing: DOC-003 section heading regression
**File:** `tests/DOC-003/test_doc003_edge_cases.py`

`test_placeholder_is_in_workspace_rules_section` looked for `## Workspace Rules` but the section heading was renamed to `## Workspace Layout` in an earlier WP. Fixed the lookup string.

## Files Changed
- `templates/agent-workbench/.github/instructions/copilot-instructions.md`
- `templates/agent-workbench/.github/agents/README.md` (created)
- `templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md`
- `tests/DOC-050/test_doc050_template_doc_fixes.py` (created)
- `tests/DOC-031/test_doc031_agent_rules.py`
- `tests/DOC-031/test_doc031_tester_edge_cases.py`
- `tests/DOC-003/test_doc003_edge_cases.py`
- `docs/bugs/bugs.csv` (BUG-168, BUG-169, BUG-170, BUG-171 registered)
- `docs/workpackages/workpackages.csv`
