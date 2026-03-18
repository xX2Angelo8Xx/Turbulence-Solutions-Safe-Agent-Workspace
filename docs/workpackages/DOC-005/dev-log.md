# DOC-005 Dev Log — Add known SAE limitations to project copilot-instructions

## Status
In Progress

## Assigned To
Developer Agent

## Summary
Add a compact "Known Tool Limitations" section to both copilot-instructions.md files documenting 7 accepted SAE limitations and their workarounds. Sync template copy. Re-embed integrity hashes.

## Files Changed
- `Default-Project/.github/instructions/copilot-instructions.md` — Added "Known Tool Limitations" section
- `templates/coding/.github/instructions/copilot-instructions.md` — Synced to match
- `Default-Project/.github/hooks/scripts/security_gate.py` — Hash re-embedded via update_hashes.py

## Implementation Notes
- The "Known Tool Limitations" section appended at end of file
- Table contains exactly 7 rows covering Out-File, dir/ls/GCI bare, GCI -Recurse, pip install, venv activation, venv python, memory tool
- Both files made byte-for-byte identical
- update_hashes.py run after changes to ensure SAF-008 integrity check passes

## Tests Written
- `tests/DOC-005/test_doc005_limitations.py`
  - test_default_project_has_known_tool_limitations_heading
  - test_template_has_known_tool_limitations_heading
  - test_both_files_are_identical
  - test_table_contains_out_file_entry
  - test_table_contains_dir_ls_gci_entry
  - test_table_contains_gci_recurse_entry
  - test_table_contains_pip_install_entry
  - test_table_contains_venv_activation_entry
  - test_table_contains_venv_python_entry
  - test_table_contains_memory_tool_entry

## Iteration 1 — 2026-03-18
- Added limitations section to Default-Project copilot-instructions.md
- Synced to templates/coding
- Ran update_hashes.py to re-embed hashes
- Verified both template security_gate.py files in sync
- All 10 DOC-005 tests pass
