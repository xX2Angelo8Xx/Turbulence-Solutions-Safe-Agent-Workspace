# DOC-046 Dev Log — Slim copilot-instructions and update references

## Status
Review

## Assigned To
Developer Agent

## Date
2026-04-01

## Objective
Rewrite `templates/agent-workbench/.github/instructions/copilot-instructions.md` to a compact philosophy, and update all references from `{{PROJECT_NAME}}/AGENT-RULES.md` to `{{PROJECT_NAME}}/AgentDocs/AGENT-RULES.md` in agent files, root README.md, and project_creator.py docstring.

## Implementation Plan

### Step A — Rewrite copilot-instructions.md
Replace full content with compact version: workspace layout, security rules, known tool limitations, pointer to AgentDocs/AGENT-RULES.md.

### Step B — Update all 7 agent.md files
Files: brainstormer, coordinator, planner, programmer, researcher, tester, workspace-cleaner.
Change `{{PROJECT_NAME}}/AGENT-RULES.md` → `{{PROJECT_NAME}}/AgentDocs/AGENT-RULES.md`.

### Step C — Update root README.md
Reference AgentDocs/AGENT-RULES.md in AI Agent Rules section.

### Step D — Update project_creator.py docstring
Change `<project_name>/AGENT-RULES.md` → `<project_name>/AgentDocs/AGENT-RULES.md`.

### Step E — Write & run tests in tests/DOC-046/

## Files Changed
- `templates/agent-workbench/.github/instructions/copilot-instructions.md`
- `templates/agent-workbench/.github/agents/brainstormer.agent.md`
- `templates/agent-workbench/.github/agents/coordinator.agent.md`
- `templates/agent-workbench/.github/agents/planner.agent.md`
- `templates/agent-workbench/.github/agents/programmer.agent.md`
- `templates/agent-workbench/.github/agents/researcher.agent.md`
- `templates/agent-workbench/.github/agents/tester.agent.md`
- `templates/agent-workbench/.github/agents/workspace-cleaner.agent.md`
- `templates/agent-workbench/README.md`
- `src/launcher/core/project_creator.py`
- `tests/DOC-046/test_doc046_slim_copilot_instructions.py`

## Tests Written
- copilot-instructions.md contains `AgentDocs/AGENT-RULES.md` reference
- copilot-instructions.md does NOT contain old `{{PROJECT_NAME}}/AGENT-RULES.md` without `AgentDocs/`
- coordinator.agent.md references `AgentDocs/AGENT-RULES.md`
- planner.agent.md references `AgentDocs/AGENT-RULES.md`
- All 7 agent files reference `AgentDocs/AGENT-RULES.md`
- Root README.md references `AgentDocs/AGENT-RULES.md`
- copilot-instructions.md is concise (fewer than 60 lines)

## Result
All tests passed.
