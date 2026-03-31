# DOC-036 Dev Log — Rewrite 6 Agent Personas

**WP ID:** DOC-036  
**Type:** DOC  
**Assigned To:** Developer Agent  
**Date:** 2026-03-31  
**Branch:** main  

## Objective

Rewrite all 6 agent persona files in `templates/agent-workbench/.github/agents/` to align with the AgentDocs philosophy. Remove all references to deleted agents (Scientist, Criticist, Writer, Fixer, Prototyper). Each agent must read/write specific AgentDocs documents. Coordinator targets a working demonstrator, not just a plan.

## Implementation Summary

### Files Modified

1. `templates/agent-workbench/.github/agents/coordinator.agent.md`
   - Rewrote to target "working demonstrator"
   - Reduced agent roster to 5 (Programmer, Tester, Brainstormer, Researcher, Planner)
   - Removed all references to Scientist, Criticist, Writer, Fixer, Prototyper
   - Added AgentDocs section: reads progress.md, writes progress.md + decisions.md
   - Updated argument-hint to reflect demonstrator goal

2. `templates/agent-workbench/.github/agents/brainstormer.agent.md`
   - Added `edit` to tools (needed to write to AgentDocs open-questions.md)
   - Added AgentDocs section: writes to open-questions.md
   - Added workflow step to read progress.md first
   - Removed references to Scientist, Criticist, Writer, Fixer, Prototyper

3. `templates/agent-workbench/.github/agents/researcher.agent.md`
   - Added `fetch` tool for web-first investigation
   - Added mandatory source link requirement
   - Added AgentDocs section: writes to research-log.md
   - Removed references to deleted agents

4. `templates/agent-workbench/.github/agents/planner.agent.md`
   - Added AgentDocs section: reads process.md + architecture.md, writes architecture.md + decisions.md
   - Added workflow step to read AgentDocs first
   - Removed references to deleted agents

5. `templates/agent-workbench/.github/agents/programmer.agent.md`
   - Added AgentDocs section: writes to progress.md
   - Added workflow step to read progress.md first
   - Removed references to deleted agents

6. `templates/agent-workbench/.github/agents/tester.agent.md`
   - Added AgentDocs section: writes to progress.md
   - Added edge-case-first principle
   - Added workflow step to read progress.md first
   - Removed references to deleted agents

## Tests

No tests required — documentation-only WP (no code changes).

## Verification Checklist

- [x] No references to Scientist, Criticist, Writer, Fixer, Prototyper in any of the 6 files
- [x] Each agent has an AgentDocs section specifying which documents they read/write
- [x] Coordinator lists only 5 agents in frontmatter `agents:` field
- [x] Researcher has `fetch` in its `tools:` frontmatter
- [x] Brainstormer has `edit` in its `tools:`
- [x] All agents start their workflow by reading `AgentDocs/progress.md`
