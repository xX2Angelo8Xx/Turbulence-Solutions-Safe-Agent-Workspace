# Test Report — SAF-039

**Tester:** Tester Agent
**Date:** 2026-03-24
**Iteration:** 1

## Summary

SAF-039 — Allow LSP tools scoped to project folder — **FAIL**.

The developer implementation is well-structured. Both `vscode_listCodeUsages` and `vscode_renameSymbol` are dispatched correctly, both tools are in `_EXEMPT_TOOLS`, and all developer tests (65) pass. However, a security vulnerability was identified during tester edge-case testing:

**BUG-097**: `_extract_lsp_file_path()` does not decode percent-encoded characters in `file://` URIs before handing the path to `zone_classifier.classify()`. An adversary can craft a URI such as `file:///workspace/project/%2E%2E/.github/config` — the security gate sees `%2E%2E` as a literal path segment (not `..`), classifies the path as inside the project folder, and returns `allow`. VS Code decodes percent-encoding per RFC 3986 before executing the tool, so the actual file operation targets `.github/config`. This bypasses the zone restriction for both tools. For `vscode_renameSymbol` (write-like), the impact is critical — it could modify files in `.github/`, `.vscode/`, or `NoAgentZone/`.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| SAF-039 developer tests (65) — `tests/SAF-039/test_saf039_lsp_tools.py` | Unit | **PASS** | All 65 pass. Logged TST-2039. |
| SAF-039 tester edge-case tests (27) — `tests/SAF-039/test_saf039_tester_edge_cases.py` | Security | **FAIL** | 7 fail (TestPercentEncodedTraversalBypass), 20 pass. Logged TST-2040. |

### Tester Test Classes and Results

| Class | Tests | Result |
|-------|-------|--------|
| `TestPercentEncodedTraversalBypass` | 7 tests | **FAIL (7/7)** — BUG-097 |
| `TestUNCPaths` | 4 tests | PASS |
| `TestMixedCaseToolNames` | 4 tests | PASS |
| `TestConflictingPathAndUri` | 4 tests | PASS |
| `TestMalformedPayloads` | 5 tests | PASS |
| `TestURIWithFragment` | 3 tests | PASS |

### Positive Findings (Edge Cases That Behave Correctly)

- **UNC filePath** (`\\server\share\project\main.py`) correctly denied. ✓
- **UNC file:// URI** (`file://buildserver/workspace/project/main.py`) correctly strips hostname and allows project path. ✓
- **Mixed-case tool names** (`vscode_listcodeusages`, `VSCODE_LISTCODEUSAGES`, `Vscode_RenameSymbol`) correctly denied by fail-closed dispatch. ✓
- **filePath takes precedence over uri** when both present — attacker cannot supply safe filePath + malicious uri and have uri used. ✓
- **Non-dict / None tool_input** falls back to top-level `filePath` correctly. ✓
- **Empty filePath** correctly falls through to `uri`. ✓
- **URI fragments** (`#L42`) are passed through without causing security issues. ✓
- **Double-slash URI** (`file:////workspace/../etc/passwd`) is denied by posixpath.normpath resolving the traversal. ✓
- **Null bytes** in filePath already tested by developer; confirmed denied. ✓

## Bugs Found

- **BUG-097**: `SAF-039: percent-encoded path traversal bypasses zone check in LSP tool URIs` — High — logged in `docs/bugs/bugs.csv`

## TODOs for Developer

- [ ] **Fix `_extract_lsp_file_path()`**: After extracting the path from a `file://` URI (after stripping the `file://[hostname]/` prefix), call `urllib.parse.unquote(path)` to decode percent-encoded characters **before** returning. This ensures `%2E%2E` is decoded to `..` and `posixpath.normpath` can then resolve traversal sequences.
  - Import: `from urllib.parse import unquote` at the top of `security_gate.py`.
  - Apply `unquote()` to the extracted path in the `file:///` branch and the `file://hostname/` branch of `_extract_lsp_file_path`.
  - Do **not** apply `unquote()` to `filePath` values — those are direct filesystem paths, not URI-encoded strings.
- [ ] **Re-run `update_hashes.py`** after applying the fix to keep `security_gate.py` hashes in sync.
- [ ] **Confirm all 65 developer tests still pass** after the fix.
- [ ] **Confirm all 7 tester tests in `TestPercentEncodedTraversalBypass` now pass** after the fix.
- [ ] **Note**: All other edge cases (UNC, mixed-case, conflicting paths, malformed payloads, URI fragments) pass — no additional code changes required for those.

## Verdict

**FAIL** — Return to Developer. Implement the `urllib.parse.unquote()` fix in `_extract_lsp_file_path()` and re-run all SAF-039 tests (developer + tester) before re-submitting for review.
