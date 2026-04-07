# Dev Log — FIX-128

**Developer:** Developer Agent
**Date started:** 2026-04-07
**Branch:** FIX-128/move-agent-rules
**Status:** In Progress

## Summary

Move `AGENT-RULES.md` from `templates/agent-workbench/Project/AGENT-RULES.md` to
`templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md`. Update all cross-references
inside the agent-workbench template and the test files that assert the old path.
The clean-workspace template is unaffected.

## ADR Check

No ADRs in `docs/decisions/index.jsonl` relate to agent-workbench template file layout.

## Files Changed

### Moved
- `templates/agent-workbench/Project/AGENT-RULES.md` → `templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md` (git mv)

### Template cross-references updated
- `templates/agent-workbench/README.md` — updated `{{PROJECT_NAME}}/AGENT-RULES.md` → `{{PROJECT_NAME}}/AgentDocs/AGENT-RULES.md`
- `templates/agent-workbench/Project/README.md` — updated two references to `AGENT-RULES.md` → `AgentDocs/AGENT-RULES.md`
- `templates/agent-workbench/.github/instructions/copilot-instructions.md` — updated one reference
- `templates/agent-workbench/.github/agents/brainstormer.agent.md` — updated one reference
- `templates/agent-workbench/.github/agents/coordinator.agent.md` — updated one reference
- `templates/agent-workbench/.github/agents/planner.agent.md` — updated one reference
- `templates/agent-workbench/.github/agents/programmer.agent.md` — updated one reference
- `templates/agent-workbench/.github/agents/README.md` — updated one reference
- `templates/agent-workbench/.github/agents/researcher.agent.md` — updated one reference
- `templates/agent-workbench/.github/agents/tester.agent.md` — updated one reference
- `templates/agent-workbench/.github/agents/workspace-cleaner.agent.md` — updated one reference
- `templates/agent-workbench/.github/prompts/debug-workspace.prompt.md` — updated four references

### MANIFEST.json regenerated
- `templates/agent-workbench/.github/hooks/scripts/MANIFEST.json` — regenerated via `scripts/generate_manifest.py templates/agent-workbench`

### Tests updated (old path → new path)
- `tests/DOC-064/test_doc064_background_terminal_docs.py` — `AW_AGENT_RULES` constant
- `tests/DOC-064/test_doc064_tester_edge_cases.py` — `AW_AGENT_RULES` constant
- `tests/FIX-123/test_fix123_get_changed_files_zone_bypass.py` — `_agent_rules_path()` method
- `tests/DOC-009/test_doc009_placeholder_replacement.py` — `AGENT_RULES_TEMPLATE` constant

## WP folder created
- `tests/FIX-128/test_fix128_move_agent_rules.py`

## Test Results

All tests pass. See `docs/test-results/test-results.jsonl` for logged run.

## Known Limitations

None. This is a pure file move + reference update — no behavioural change.
