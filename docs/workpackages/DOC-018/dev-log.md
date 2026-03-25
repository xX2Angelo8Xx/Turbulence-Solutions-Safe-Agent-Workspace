# DOC-018 Dev Log — Create agents/ directory in Agent Workbench template

## WP Summary

- **ID:** DOC-018
- **Branch:** DOC-018/agents-directory
- **Assigned To:** Developer Agent
- **User Story:** US-042 (Programmer Agent for Agent Workbench)
- **Depends On:** GUI-023 (Done)

## Goal

Create `templates/agent-workbench/.github/agents/` directory with a README explaining the agent roster. Update `copilot-instructions.md` and `AGENT-RULES.md` to reference the available agents.

---

## Implementation

### Files Created

- `templates/agent-workbench/.github/agents/README.md` — Agent roster reference; describes all 10 agents, how to invoke, and how to customize `.agent.md` files.

### Files Modified

- `templates/agent-workbench/.github/instructions/copilot-instructions.md` — Added one bullet to Workspace Rules referencing the agents directory and roster.
- `templates/agent-workbench/Project/AGENT-RULES.md` — Added Section 8 "Available Agent Personas" documenting all 10 agents and when to use each.

### Decisions

- Added agents reference as a single compact bullet in copilot-instructions.md (file was already at 50 lines; minimized additional line impact).
- AGENT-RULES.md Section 8 placed at the end of the file after Section 7 (Known Workarounds), consistent with the existing numbered-section pattern.
- Roster in README.md lists all 10 agents from the WP spec: programmer, brainstormer, tester, researcher, scientist, criticist, planner, fixer, writer, prototyper.
- `.agent.md` files themselves are not created in this WP (those are scope for DOC-019 through DOC-028).

---

## Tests

- Test file: `tests/DOC-018/test_doc018_agents_directory.py`
- 7 test cases covering:
  1. agents/ directory exists
  2. README.md exists in agents/
  3. README.md mentions all 10 agents
  4. README.md contains customization instructions
  5. copilot-instructions.md references agents/
  6. AGENT-RULES.md section on agent personas exists
  7. AGENT-RULES.md lists all 10 agent names

## Test Results

All 7 tests pass. Logged via `scripts/add_test_result.py`.

---

## Checklist

- [x] `dev-log.md` created and filled in
- [x] `tests/DOC-018/` folder and test file exist
- [x] All tests pass
- [x] Test results logged
- [x] `validate_workspace.py --wp DOC-018` clean
- [x] All changes staged and committed
- [x] Branch pushed
