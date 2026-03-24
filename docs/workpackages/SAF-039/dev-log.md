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

---

## Iteration 2 — BUG-097 Fix (2026-03-24)

### Bug Fixed
**BUG-097**: `_extract_lsp_file_path()` returned the raw URI path without decoding percent-encoded characters. A URI like `file:///workspace/project/%2E%2E/.github/config` extracted to `/workspace/project/%2E%2E/.github/config`. Since `posixpath.normpath` does not interpret `%2E%2E` (only literal `..`), `zone_classifier` allowed the path, but VS Code decodes `%2E` → `.` per RFC 3986 so the actual operation targeted `.github/config`.

### Fix Applied
Added `from urllib.parse import unquote` import to `security_gate.py`.

In `_extract_lsp_file_path()`, applied `unquote()` on the extracted URI path before returning:
- `file:///` branch: `path = unquote(uri[8:])`
- `file://hostname/` branch: `return unquote(remainder[slash:])`

`unquote()` is NOT applied to `filePath` values — those are direct filesystem paths, not URI-encoded strings.

After modifying `security_gate.py`, re-ran `update_hashes.py` to re-embed SHA256 hashes (`_KNOWN_GOOD_GATE_HASH` updated to `3fe22204544f4490589cf28deba2650ce290d1feab4e70fa3ba90a2648d512ed`).

### Test Results (Iteration 2)
- **65 developer tests** (`test_saf039_lsp_tools.py`) — all pass ✓
- **27 tester edge-case tests** (`test_saf039_tester_edge_cases.py`) — all 27 pass ✓ (previously 7 failed in `TestPercentEncodedTraversalBypass`)
- **Total: 92 passed, 0 failed** — TST-2041

### Additional Files Changed in Iteration 2
- `templates/coding/.github/hooks/scripts/security_gate.py` (unquote import + URI path decoding)
- `docs/test-results/test-results.csv` (TST-2041 via add_test_result.py)
