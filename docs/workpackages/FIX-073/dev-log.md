# Dev Log — FIX-073

**Developer:** Developer Agent
**Date started:** 2026-03-25
**Iteration:** 1

## Objective
Fix template agent YAML frontmatter in all 10 agent files under `templates/agent-workbench/.github/agents/`. Replace individual tool names with VS Code tool categories, correct the model syntax, update the planner body, update the researcher body, and update README.md example. Fixes BUG-108 and BUG-109.

## Implementation Summary

### Agent file frontmatter changes (all 10 files)
- Changed `model: claude-sonnet-4-5` → `model: ['Claude Opus 4.6 (copilot)']`
- Mapped individual tool names to VS Code tool categories per the table:
  - `read_file` → `read`
  - `create_file`, `replace_string_in_file`, `multi_replace_string_in_file` → `edit`
  - `file_search`, `grep_search`, `semantic_search` → `search`
  - `run_in_terminal` → `execute`
  - `fetch_webpage` → removed (not a standard VS Code tool)

### Per-agent tool lists after fix
| Agent | Tools |
|-------|-------|
| programmer | [read, edit, search, execute] |
| brainstormer | [read, search] |
| tester | [read, edit, search, execute] |
| researcher | [read, search] |
| scientist | [read, edit, search, execute] |
| criticist | [read, search] |
| planner | [read, search, ask, edit] |
| fixer | [read, edit, search, execute] |
| writer | [read, edit, search] |
| prototyper | [read, edit, search, execute] |

### Planner body update (BUG-109)
- Removed: "You do not write, edit, or delete any file" and "You have no edit tools by design"
- Added: capability to create `plan.md` file when user requests a written plan
- Added: `ask` capability — the planner can ask clarifying questions about goals, constraints, and priorities before planning

### Researcher body update
- Removed: reference to `fetch_webpage` in "How You Work" step 4
- Updated: step 4 now relies on `read` and `search` tools for investigation

### README.md update
- Updated example frontmatter block to show correct tool categories and model syntax

### DOC-019 through DOC-028 test updates
- Updated all existing tests that referenced old individual tool names to use new category names
- Updated model assertions to match new `['Claude Opus 4.6 (copilot)']` format

## Files Changed
- `templates/agent-workbench/.github/agents/programmer.agent.md` — frontmatter tools + model
- `templates/agent-workbench/.github/agents/brainstormer.agent.md` — frontmatter tools + model
- `templates/agent-workbench/.github/agents/tester.agent.md` — frontmatter tools + model
- `templates/agent-workbench/.github/agents/researcher.agent.md` — frontmatter tools + model + body (fetch_webpage refs)
- `templates/agent-workbench/.github/agents/scientist.agent.md` — frontmatter tools + model
- `templates/agent-workbench/.github/agents/criticist.agent.md` — frontmatter tools + model
- `templates/agent-workbench/.github/agents/planner.agent.md` — frontmatter tools + model + body (ask/plan.md)
- `templates/agent-workbench/.github/agents/fixer.agent.md` — frontmatter tools + model
- `templates/agent-workbench/.github/agents/writer.agent.md` — frontmatter tools + model
- `templates/agent-workbench/.github/agents/prototyper.agent.md` — frontmatter tools + model
- `templates/agent-workbench/.github/agents/README.md` — example frontmatter update
- `tests/DOC-019/test_doc019_programmer_agent.py` — updated tool assertions
- `tests/DOC-019/test_doc019_tester_edge_cases.py` — updated tool assertions
- `tests/DOC-020/test_doc020_brainstormer_agent.py` — updated tool assertions
- `tests/DOC-020/test_doc020_tester_edge_cases.py` — updated tool assertions
- `tests/DOC-021/test_doc021_tester_agent.py` — updated tool assertions
- `tests/DOC-021/test_doc021_tester_edge_cases.py` — updated tool assertions
- `tests/DOC-022/test_doc022_researcher_agent.py` — updated tool assertions
- `tests/DOC-022/test_doc022_researcher_edge_cases.py` — updated tool/model assertions
- `tests/DOC-023/test_doc023_scientist_agent.py` — updated tool assertions
- `tests/DOC-023/test_doc023_scientist_edge_cases.py` — updated tool/model assertions
- `tests/DOC-024/test_doc024_criticist_agent.py` — updated tool assertions
- `tests/DOC-024/test_doc024_criticist_edge_cases.py` — updated tool/model assertions
- `tests/DOC-025/test_doc025_planner_agent.py` — updated tool assertions
- `tests/DOC-025/test_doc025_planner_edge_cases.py` — updated tool/model assertions
- `tests/DOC-026/test_doc026_fixer_agent.py` — updated tool assertions
- `tests/DOC-026/test_doc026_fixer_edge_cases.py` — updated tool/model assertions
- `tests/DOC-027/test_doc027_writer_agent.py` — updated tool assertions
- `tests/DOC-027/test_doc027_writer_edge_cases.py` — updated tool/model/forbidden assertions
- `tests/DOC-028/test_doc028_prototyper_agent.py` — updated tool assertions
- `tests/DOC-028/test_doc028_prototyper_edge_cases.py` — updated tool/model assertions
- `tests/FIX-073/test_fix073_agent_frontmatter.py` — new FIX-073 tests

## Tests Written
- `tests/FIX-073/test_fix073_agent_frontmatter.py`:
  - 10 tests verifying each agent has the correct tools list
  - 10 tests verifying each agent has the correct model
  - Tests that no old tool names remain in any agent frontmatter
  - Test that planner has `ask` and `edit` in tools
  - Test that README example shows correct syntax
