# FIX-119 Dev Log — Remove duplicate AGENT-RULES.md from AgentDocs

**WP ID:** FIX-119  
**Branch:** FIX-119/remove-duplicate-agent-rules  
**Developer:** Developer Agent  
**Date:** 2026-04-06  
**Fixes:** BUG-200  
**User Story:** US-081  

---

## Prior Art Check

No ADRs in `docs/decisions/index.jsonl` relate directly to the AGENT-RULES.md file location. US-072 (line 72 in user-stories.jsonl) previously established `AgentDocs/AGENT-RULES.md` as the central location, but subsequent workpackages (FIX-091, SAF-049, SAF-056, DOC-004) re-established that `Project/AGENT-RULES.md` at project root is the authoritative copy. DOC-045/DOC-047 tests (requiring root to be deleted) are tracked as known failures in regression-baseline.json, confirming the root copy is the current design.

---

## Scope

Remove `Project/AgentDocs/AGENT-RULES.md` (duplicate) and update all references that point to `AgentDocs/AGENT-RULES.md` across template files, agent .md files, and tests. Regenerate MANIFEST.

---

## Implementation

### Files Deleted
- `templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md` — the duplicate mirror copy

### Template Files Updated (AgentDocs/AGENT-RULES.md → AGENT-RULES.md)
- `templates/agent-workbench/.github/instructions/copilot-instructions.md`
- `templates/agent-workbench/.github/agents/coordinator.agent.md`
- `templates/agent-workbench/.github/agents/planner.agent.md`
- `templates/agent-workbench/.github/agents/brainstormer.agent.md`
- `templates/agent-workbench/.github/agents/programmer.agent.md`
- `templates/agent-workbench/.github/agents/README.md`
- `templates/agent-workbench/.github/agents/researcher.agent.md`
- `templates/agent-workbench/.github/agents/workspace-cleaner.agent.md`
- `templates/agent-workbench/.github/agents/tester.agent.md`
- `templates/agent-workbench/README.md`
- `templates/agent-workbench/Project/README.md`
- `templates/agent-workbench/MANIFEST.json` (regenerated)

### Source Code Updated
- `src/launcher/core/project_creator.py` — updated docstring comment referencing old path

### Tests Updated
- `tests/DOC-007/test_doc007_agent_rules.py` — path updated to `Project/AGENT-RULES.md`
- `tests/DOC-008/test_doc008_tester_edge_cases.py` — path assertion updated
- `tests/DOC-008/test_doc008_read_first_directive.py` — error message updated
- `tests/DOC-009/test_doc009_placeholder_replacement.py` — path and helper updated
- `tests/DOC-002/test_doc002_readme_placeholders.py` — assertion updated
- `tests/DOC-061/test_doc061_subagent_denial_docs.py` — mirror tests removed (file deleted)

### Regression Baseline Updated
- Removed `test_placeholder_present_in_agent_rules_section` (now passes after fix)

### Bugs Updated
- BUG-200: Status → Fixed, Fixed In WP → FIX-119

---

## Tests Written

- `tests/FIX-119/test_fix119_no_duplicate_agent_rules.py`
  - `test_duplicate_file_does_not_exist` — verifies `Project/AgentDocs/AGENT-RULES.md` is gone
  - `test_primary_file_exists` — verifies `Project/AGENT-RULES.md` still exists
  - `test_copilot_instructions_references_root` — verifies copilot-instructions.md uses root path
  - `test_agent_files_reference_root` — verifies all agent .md files use root path
  - `test_readme_references_root` — verifies workspace README uses root path
  - `test_project_readme_references_root` — verifies Project/README.md uses root path
  - `test_manifest_no_agentdocs_entry` — verifies MANIFEST has no `AgentDocs/AGENT-RULES.md` entry

---

## Known Limitations

None. All references updated and duplicate removed.
