# Dev Log — DOC-044: Rename Tidyup agent to Workspace-Cleaner

| Field | Value |
|-------|-------|
| WP ID | DOC-044 |
| Status | In Progress |
| Assigned To | Developer Agent |
| Branch | DOC-044/workspace-cleaner |
| Started | 2026-03-31 |

---

## Goal

Rename the `Tidyup` agent in the `agent-workbench` template to `Workspace-Cleaner`. This involves:
- Renaming `tidyup.agent.md` → `workspace-cleaner.agent.md` (via `git mv`)
- Updating agent name, self-references, and output headers inside the file
- Updating `coordinator.agent.md` agents list and delegation table
- Updating `AGENT-RULES.md` agent-to-doc mapping
- Verifying no Tidyup references remain in `copilot-instructions.md` or `AgentDocs/README.md`

---

## Implementation Summary

### Files Changed

| File | Change |
|------|--------|
| `templates/agent-workbench/.github/agents/tidyup.agent.md` | Renamed to `workspace-cleaner.agent.md` (git mv) |
| `templates/agent-workbench/.github/agents/workspace-cleaner.agent.md` | Updated `name: Tidyup` → `name: Workspace-Cleaner`; updated body self-references |
| `templates/agent-workbench/.github/agents/coordinator.agent.md` | Updated agents list and delegation table |
| `templates/agent-workbench/Project/AGENT-RULES.md` | Updated agent-to-doc mapping (section 1a) |

### Files Checked (No Changes Needed)

| File | Status |
|------|--------|
| `templates/agent-workbench/.github/instructions/copilot-instructions.md` | No Tidyup references found |
| `templates/agent-workbench/Project/AgentDocs/README.md` | No Tidyup references found |

---

## Tests Written

- `tests/DOC-044/test_doc044_workspace_cleaner_rename.py`
  - workspace-cleaner.agent.md exists
  - tidyup.agent.md does NOT exist
  - name field is `Workspace-Cleaner`
  - coordinator agents list contains `Workspace-Cleaner`, not `Tidyup`
  - coordinator body uses `@Workspace-Cleaner`, not `@Tidyup`
  - AGENT-RULES.md uses `Workspace-Cleaner`, not `Tidyup`
  - No remaining Tidyup references in any template agent file

---

## Status

Implementation complete. Tests passed. Ready for Tester review.
