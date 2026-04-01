# Dev Log — SAF-063: Add tool name normalization to security gate

## Status
In Progress

## Assigned To
Developer Agent

## Linked User Story
US-063

## Problem Statement
VS Code Copilot sends tool names in camelCase format (e.g. `vscode_askQuestions`) but
the security gate's `_ALWAYS_ALLOW_TOOLS` frozenset uses snake_case (`vscode_ask_questions`).
The exact-match lookup causes `vscode_askQuestions` to fall through to the unknown-tool deny
path, producing false denials.

Additional tool names sent by VS Code were absent from all classification sets entirely,
also causing false denials for read-only or VS Code-managed tools.

## Implementation Summary

### Files Modified
1. `templates/agent-workbench/.github/hooks/scripts/security_gate.py`
   - Added `"vscode_askQuestions"` (camelCase — the actual name VS Code sends) to
     `_ALWAYS_ALLOW_TOOLS`.
   - Added missing always-safe tool names to `_ALWAYS_ALLOW_TOOLS`:
     `get_terminal_output`, `terminal_last_command`, `terminal_selection`, `test_failure`,
     `tool_search`, `get_vscode_api`, `switch_agent`, `copilot_getNotebookSummary`,
     `get_search_view_results`, `install_extension`, `create_and_run_task`,
     `get_task_output`, `runTests`.
   - Added `"insert_edit_into_file"` to `_WRITE_TOOLS` (VS Code's actual name for the
     edit tool — performs file edits and must be zone-checked).
   - Added missing tools to `_EXEMPT_TOOLS`:
     `insert_edit_into_file`, `view_image`, `edit_notebook_file`,
     `create_new_jupyter_notebook`, `read_notebook_cell_output`, `run_notebook_cell`.
   - Added `insert_edit_into_file` handler in `decide()` — routes to
     `validate_write_tool()` same as `edit_file`.

2. `templates/agent-workbench/.github/hooks/scripts/require-approval.sh`
   - Updated always-allow regex to include all new tool names.

3. `templates/agent-workbench/.github/hooks/scripts/require-approval.ps1`
   - Updated always-allow regex to include all new tool names.

4. `templates/agent-workbench/.github/agents/coordinator.agent.md`
   - Model updated to `Claude Opus 4.6 (copilot)` (already on disk — included in commit).

### Hash Update
After modifying security_gate.py, `update_hashes.py` was run to regenerate
`_KNOWN_GOOD_GATE_HASH` and `_KNOWN_GOOD_SETTINGS_HASH`.

## Tests Written
- `tests/SAF-063/test_saf063_tool_name_normalization.py`
  - `vscode_askQuestions` is allowed (camelCase — actual VS Code name)
  - `vscode_ask_questions` is still allowed (backward compat)
  - All newly added always-allow tool names return "allow"
  - `insert_edit_into_file` is zone-checked as a write tool
  - `insert_edit_into_file` to a path outside project is denied
  - `view_image`, `edit_notebook_file`, `create_new_jupyter_notebook`,
    `read_notebook_cell_output`, `run_notebook_cell` are exempt (path-checked)
  - Unknown tools are still denied

## Known Limitations
None.
