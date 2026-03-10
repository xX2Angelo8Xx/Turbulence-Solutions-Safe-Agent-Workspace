# Dev Log — SAF-001

**Developer:** Developer Agent
**Date started:** 2026-03-10
**Iteration:** 2

## Objective

Design and implement `security_gate.py` — a cross-platform Python script that replaces the existing `.ps1`/`.sh` PreToolUse hooks. The script parses VS Code hook JSON from stdin, determines the tool name and target path, and returns an allow/deny/ask JSON response to stdout. Must be stdlib-only, fail-closed, and always exit 0.

## Implementation Summary

Source files were never committed in Iteration 1 — only compiled `.pyc` cache existed. Iteration 2 restores both source files from scratch, incorporating all fixes mandated by the Tester report.

**Key decisions:**

- `_PATH_FIELDS` intentionally excludes `query` and `pattern`. These are search-content fields, not file-system paths. Including them caused false positives on legitimate `grep_search` calls (e.g., `query=".github/commit-branch-rules.md"` triggering a deny). Path extraction for search-tool parameters is deferred to SAF-003.
- Null-byte sanitization added to `normalize_path`: `p.replace("\x00", "")` strips null bytes before any other processing, eliminating the null-byte-before-blocked-segment bypass vector.
- Stdin read limit: `sys.stdin.read(_STDIN_MAX_BYTES)` caps input at 1 MiB. If `len(raw) >= _STDIN_MAX_BYTES`, the script fails closed (deny + exit 0). This addresses Concern 4 from the Tester report.
- Dual-method zone detection retained from original design:
  - **Method 1**: Strip ws_root prefix → check first path segment against `_BLOCKED_NAMES` / `"project"`.
  - **Method 2**: Pattern-based regex fallback (`/(\.github|\.vscode|noagentzone)(/|$)`) catches mismatched roots, UNC paths, and edge cases Method 1 misses.
- `get_zone` normalizes `ws_root` with `rstrip("/")` internally, so callers passing a trailing-slash root work correctly.
- Concern 5 (ws_root derived from `os.getcwd()`) documented as a known limitation below.

## Files Changed

- `Default-Project/.github/hooks/scripts/security_gate.py` — created (source restored; `query`/`pattern` removed from `_PATH_FIELDS`; null-byte sanitization and stdin size limit added)
- `tests/test_saf001_security_gate.py` — created (60 tests: 49 original + 11 Tester-required edge cases)
- `docs/workpackages/SAF-001/dev-log.md` — created
- `docs/workpackages/workpackages.csv` — SAF-001 status updated to `Review`
- `docs/test-results/test-results.csv` — new test run results appended (TST-093 to TST-103 for new edge-case tests; TST-088 re-confirmed)

## Tests Written

**Original 49 (TST-033 to TST-081 — restored and verified runnable):**
- `test_parse_input_valid_json` through `test_integration_exit_code_always_zero`

**11 Tester-required edge cases (TST-093 to TST-103):**
- `test_null_byte_in_path` — null byte before blocked segment is stripped then denied
- `test_unc_path_always_denied` — `\\server\share\.github\secret` is denied
- `test_unc_path_project_asks` — `\\server\share\project\file` is not denied
- `test_very_large_input_fails_closed` — 1 MiB+1 garbage stdin returns deny, exit 0
- `test_query_field_not_treated_as_path` — `grep_search(query=".github/secret")` is not denied
- `test_empty_tool_name` — empty `tool_name` falls through to path-based zone check
- `test_tool_name_not_string` — non-string `tool_name` does not raise; returns safe result
- `test_ws_root_with_trailing_slash` — `get_zone` handles trailing-slash ws_root correctly
- `test_response_hookSpecificOutput_exact_structure` — response structure matches VS Code spec exactly
- `test_decide_project_sibling_prefix_bypass` — `project-evil/.github/x` is denied via Method 2
- `test_normalize_deep_traversal` — `project/../../../../.github/x` resolves and is denied

**Full run result:** 92 passed (32 existing + 60 SAF-001) in 0.96s. Zero failures.

## Known Limitations

- **Concern 5 (ws_root stability):** `ws_root = normalize_path(os.getcwd())` relies on the hook executor's working directory matching the workspace root. If VS Code or the extension changes directory before invoking the hook, zone decisions may be incorrect. The root should ideally be passed via hook configuration or environment variable in a future iteration.
- **Concern 4 (large stdin):** Mitigated with `_STDIN_MAX_BYTES = 1_048_576`. Inputs at exactly the limit are denied conservatively. This is documented in the script and tested (`test_very_large_input_fails_closed`).
- The `require-approval.json` hook config still points to the `.ps1`/`.sh` scripts. Switching to `security_gate.py` is SAF-010's scope.

## Iteration 2 — 2026-03-10

### Tester Feedback Addressed

- **BLOCKING: Restore `security_gate.py`** — Source file created at `Default-Project/.github/hooks/scripts/security_gate.py`.
- **BLOCKING: Restore `tests/test_saf001_security_gate.py`** — Source file created at `tests/test_saf001_security_gate.py`. All 49 original tests + 11 edge cases = 60 tests pass.
- **BLOCKING: Create `dev-log.md`** — This file.
- **BLOCKING: Set WP status to `Review`** — Updated in `workpackages.csv`.
- **REQUIRED FIX: Remove `query` and `pattern` from `_PATH_FIELDS`** — Done. `_PATH_FIELDS = ("filePath", "file_path", "path", "directory", "target")`.
- **REQUIRED FIX: Add null-byte path test** — Added `test_null_byte_in_path`; also fixed the vulnerability by stripping null bytes in `normalize_path`.
- **REQUIRED FIX: Add UNC path test** — Added `test_unc_path_always_denied` and `test_unc_path_project_asks`.
- **REQUIRED FIX: Resource guard for large stdin** — Added `_STDIN_MAX_BYTES = 1_048_576` limit; tested with `test_very_large_input_fails_closed`.

### Additional Changes
- `security_gate.py` — null-byte strip in `normalize_path`; `query`/`pattern` removed from `_PATH_FIELDS`; `ws_root.rstrip("/")` inside `get_zone`; stdin size guard in `main`
- `tests/test_saf001_security_gate.py` — all 11 Tester-required edge cases added

### Tests Added/Updated
- TST-093 to TST-103 (11 new edge-case tests) — all pass
