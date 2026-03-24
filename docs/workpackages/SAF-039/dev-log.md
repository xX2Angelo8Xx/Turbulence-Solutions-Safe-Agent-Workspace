# SAF-039 Dev Log — Allow LSP Tools Scoped to Project Folder

## WP Details
- **ID:** SAF-039
- **Name:** Allow LSP tools scoped to project folder
- **Branch:** SAF-039/lsp-tools-project-scope
- **Assigned To:** Developer Agent
- **Status:** Review

## Implementation Summary

Added `vscode_listCodeUsages` and `vscode_renameSymbol` to the security gate with project-folder-scoped access control.

### Changes Made

**`templates/coding/.github/hooks/scripts/security_gate.py`**

1. Added `vscode_listCodeUsages` and `vscode_renameSymbol` to `_EXEMPT_TOOLS`
2. Added helper `_extract_lsp_file_path(data)` — extracts the target file path from either `filePath` or `uri` fields in the tool payload. URI is stripped of its `file://` scheme prefix.
3. Added `validate_vscode_list_code_usages(data, ws_root)` — zones checks the extracted path; allows project-folder files, denies everything else. Fails closed (deny) if no path is present.
4. Added `validate_vscode_rename_symbol(data, ws_root)` — same as above, but additionally blocks `.git/` internals  (write-like operation).
5. Added dispatch blocks in `decide()` for both tools before the `_EXEMPT_TOOLS` fallback.

**`templates/coding/.github/hooks/scripts/update_hashes.py`** — run after editing to re-embed SHA256 hashes.

### Design Decisions
- `vscode_listCodeUsages` is read-only (symbol lookup/navigation) → zone-allow is sufficient, no .git/ block needed beyond the general `is_git_internals()` guard inside `validate_write_tool`. However, since the function is delegating to `zone_classifier.classify()` which already allows project files, and `.git/` is classified as "deny" anyway, it naturally blocks .git/ access.
- `vscode_renameSymbol` is write-like (modifies source files) → explicitly blocks `.git/` internals as an extra safety layer, consistent with write tools.
- URI extraction: strips `file://` or `file:///` prefix and normalises path separators. Windows drive-letter URIs (`file:///C:/...`) resolved correctly.
- Fail closed when neither `filePath` nor `uri` is present.

## Tests Written

`tests/SAF-039/test_saf039_lsp_tools.py`

Coverage:
- `vscode_listCodeUsages` — allowed in project, denied outside, denied for null bytes, denied for path traversal, denied when no path present, URI format allowed in project, URI format denied outside
- `vscode_renameSymbol` — allowed in project, denied outside, denied for .git/ internals, denied for null bytes, denied for path traversal, denied when no path present, URI format allowed in project, URI format denied outside

## Files Changed
- `templates/coding/.github/hooks/scripts/security_gate.py`
- `docs/workpackages/workpackages.csv`
- `docs/workpackages/SAF-039/dev-log.md` (this file)
- `tests/SAF-039/test_saf039_lsp_tools.py`
- `docs/test-results/test-results.csv` (via add_test_result.py)
