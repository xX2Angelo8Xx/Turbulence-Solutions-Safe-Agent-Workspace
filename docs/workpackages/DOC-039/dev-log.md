# DOC-039 — Create Tidyup Agent

**Status:** In Progress  
**Assigned To:** Developer Agent  
**Branch:** main (direct-to-main per WP instructions)  
**Date Started:** 2026-03-31  

---

## Objective

Create a Tidyup agent (`tidyup.agent.md`) for the agent-workbench template that audits AgentDocs documents against the actual project state and fixes documentation drift. Integrate Tidyup into the Coordinator agent and update AGENT-RULES.md.

---

## Files Created / Modified

| File | Action |
|------|--------|
| `templates/agent-workbench/.github/agents/tidyup.agent.md` | Created |
| `templates/agent-workbench/.github/agents/coordinator.agent.md` | Modified — added Tidyup to agents list and delegation section |
| `templates/agent-workbench/Project/AGENT-RULES.md` | Modified — added Tidyup to agent-to-doc mapping |
| `docs/workpackages/workpackages.csv` | Modified — status set to In Progress → Review |
| `docs/workpackages/DOC-039/dev-log.md` | Created |

---

## Implementation Summary

1. Created `tidyup.agent.md` with:
   - Frontmatter: name, description, tools (`[read, search, edit, execute]`), model, argument-hint
   - Audit logic for all 5 AgentDocs documents: architecture.md, decisions.md, progress.md, research-log.md, open-questions.md
   - Structured audit output format (table + summary)
   - Zone restrictions matching other agents
   - Clear "What You Do Not Do" constraints

2. Updated `coordinator.agent.md`:
   - Added `Tidyup` to `agents:` frontmatter list
   - Added `@Tidyup` delegation bullet in the "Delegate implementation" section
   - Left `tools:` and `argument-hint:` lines unchanged

3. Updated `AGENT-RULES.md`:
   - Added `Tidyup → all AgentDocs documents (audit and fix drift)` to agent-to-doc mapping in section 1a

---

## Tests

This WP creates documentation/template files only — no executable code. No automated tests are required per the testing protocol (pure template/agent files).

---

## Known Limitations

None.
