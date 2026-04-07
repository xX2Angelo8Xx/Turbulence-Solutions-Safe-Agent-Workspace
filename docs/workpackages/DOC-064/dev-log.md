# DOC-064 Dev Log — Document background terminal restriction in AGENT-RULES

## WP Summary
- **ID:** DOC-064
- **Category:** DOC
- **Branch:** DOC-064/background-terminal-docs
- **Bug Reference:** BUG-209 — "Background terminal (isBackground:true) silently blocked without documentation"
- **Status:** In Progress

## ADR Check
Reviewed `docs/decisions/index.jsonl`. No prior ADRs directly govern template documentation for terminal command restrictions.

## Implementation Plan
1. Add `run_in_terminal (isBackground:true)` to the Blocked Commands table in §4 (Terminal Rules) of `templates/agent-workbench/Project/AGENT-RULES.md`
2. Add same row to `templates/clean-workspace/Project/AGENT-RULES.md` (into the Tool Permission Matrix or Known Tool Workarounds section as appropriate)
3. Add row to Known Tool Limitations table in `templates/agent-workbench/.github/instructions/copilot-instructions.md`
4. Add same row to `templates/clean-workspace/.github/instructions/copilot-instructions.md`
5. Regenerate MANIFEST.json via `scripts/generate_manifest.py`
6. Create `tests/DOC-064/` with verification tests
7. Run full test suite and validate workspace

## Files Changed
- `templates/agent-workbench/Project/AGENT-RULES.md` — Added isBackground:true row to Blocked Commands table
- `templates/clean-workspace/Project/AGENT-RULES.md` — Added isBackground:true row (Known Tool Workarounds)
- `templates/agent-workbench/.github/instructions/copilot-instructions.md` — Added isBackground:true to Known Tool Limitations
- `templates/clean-workspace/.github/instructions/copilot-instructions.md` — Added isBackground:true to Known Tool Limitations
- `templates/agent-workbench/MANIFEST.json` — Regenerated (hash update)
- `templates/clean-workspace/MANIFEST.json` — Regenerated (hash update)
- `tests/DOC-064/test_doc064_background_terminal_docs.py` — New test file
- `docs/workpackages/workpackages.jsonl` — WP status updated

## Tests Written
- `tests/DOC-064/test_doc064_background_terminal_docs.py`
  - `test_agent_workbench_agent_rules_has_isBackground` — verifies agent-workbench AGENT-RULES.md contains isBackground in Blocked Commands
  - `test_clean_workspace_agent_rules_has_isBackground` — verifies clean-workspace AGENT-RULES.md contains isBackground entry
  - `test_agent_workbench_copilot_instructions_has_isBackground` — verifies agent-workbench copilot-instructions.md has isBackground in Known Tool Limitations
  - `test_clean_workspace_copilot_instructions_has_isBackground` — verifies clean-workspace copilot-instructions.md has isBackground in Known Tool Limitations
  - `test_agent_workbench_agent_rules_use_instead_guidance` — verifies use_instead guidance text present
  - `test_clean_workspace_agent_rules_use_instead_guidance` — verifies use_instead guidance text present
  - `test_agent_workbench_copilot_instructions_use_instead_guidance` — verifies use_instead text in copilot-instructions
  - `test_clean_workspace_copilot_instructions_use_instead_guidance` — verifies use_instead text in copilot-instructions

## Decisions
- For `clean-workspace/Project/AGENT-RULES.md`: the file has no dedicated "Blocked Commands" §4 Terminal Rules section (its §4 is Security Rules). Added the entry to §6 Known Tool Workarounds table as that is the equivalent location for blocked/limited tool guidance in that template.
- For both AGENT-RULES files: the `use_instead` guidance reads "Run in foreground terminal; set `timeout` parameter for long-running commands."

## Bug Fix
- BUG-209 fixed: `isBackground:true` is now explicitly documented in both AGENT-RULES template files and both copilot-instructions files.
