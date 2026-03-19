# Test Report — FIX-021

**Tester:** Tester Agent
**Date:** 2026-03-17
**Iteration:** 1

## Summary

FIX-021 correctly addresses BUG-054 by fixing three search-tool handlers in
`security_gate.py`. The implementation is sound:

- `validate_grep_search()` now returns `"allow"` when no `filePath` field is
  present (after passing the `includeIgnoredFiles` and `includePattern` checks),
  instead of the old fail-closed `"deny"`.
- `validate_semantic_search()` now unconditionally returns `"allow"`, relying on
  VS Code's `search.exclude` settings to hide restricted content from the index.
- `decide()` has a new explicit `file_search` handler that allows queries by
  default but denies any query containing `.github`, `.vscode`, `noagentzone`,
  or `..`.

The changes are correctly synced to `templates/coding/` and hashes are
re-embedded. All security properties that existed before the fix (deny for
`includeIgnoredFiles=True`, deny for restricted-zone `includePattern`, deny for
`file_search` queries naming restricted zones or using `..`) are preserved.

The fix does **not** weaken any previously working deny path. The only behavioural
change is that the three search tools are allowed where they were incorrectly
denied before.

---

## Tests Executed

### Developer-written tests (24 tests — `tests/FIX-021/test_fix021_search_tools.py`)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_grep_search_no_params_allow | Unit | PASS | FIX-021 core change verified |
| test_grep_search_no_params_via_validate | Unit | PASS | Direct validate_grep_search call |
| test_grep_search_project_include_pattern_allow | Unit | PASS | No includePattern → allow |
| test_grep_search_nested_project_include_pattern_allow | Unit | PASS | Nested tool_input format |
| test_grep_search_include_ignored_files_true_denied | Regression | PASS | Protection unchanged |
| test_grep_search_include_ignored_files_string_true_denied | Regression | PASS | String "true" also denied |
| test_grep_search_github_include_pattern_denied | Regression | PASS | .github protection unchanged |
| test_grep_search_vscode_include_pattern_denied | Regression | PASS | .vscode protection unchanged |
| test_grep_search_noagentzone_include_pattern_denied | Regression | PASS | NoAgentZone protection unchanged |
| test_semantic_search_allow | Unit | PASS | FIX-021 core change verified |
| test_semantic_search_validate_allow | Unit | PASS | Direct validate_semantic_search call |
| test_semantic_search_nested_format_allow | Unit | PASS | Nested tool_input format |
| test_semantic_search_with_protected_query_allow | Unit | PASS | Query text not treated as path |
| test_file_search_basic_query_allow | Unit | PASS | FIX-021 core change verified |
| test_file_search_nested_format_allow | Unit | PASS | Nested tool_input format |
| test_file_search_no_query_allow | Unit | PASS | Missing query field → allow |
| test_file_search_github_in_query_denied | Security | PASS | .github query denied |
| test_file_search_github_nested_denied | Security | PASS | Nested .github query denied |
| test_file_search_github_mixed_case_denied | Security | PASS | .GITHUB (uppercase) denied |
| test_file_search_noagentzone_in_query_denied | Security | PASS | NoAgentZone query denied |
| test_file_search_noagentzone_lowercase_denied | Security | PASS | noagentzone lowercase denied |
| test_file_search_vscode_in_query_denied | Security | PASS | .vscode query denied |
| test_file_search_dotdot_in_query_denied | Security | PASS | .. traversal denied |
| test_file_search_dotdot_nested_denied | Security | PASS | .. in nested query denied |

### Tester-added edge-case tests (9 tests — TST-1682 to TST-1690)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_file_search_vscode_mixed_case_denied (TST-1682) | Security | PASS | .VSCODE uppercase case-insensitive |
| test_file_search_github_camelcase_denied (TST-1683) | Security | PASS | .GitHub camelCase denied |
| test_file_search_empty_string_query_allow (TST-1684) | Unit | PASS | Empty string → allow |
| test_file_search_whitespace_query_allow (TST-1685) | Unit | PASS | Whitespace-only → allow |
| test_file_search_tool_input_empty_dict_allow (TST-1686) | Unit | PASS | tool_input={} no query → allow |
| test_grep_search_explicit_project_include_pattern_allow (TST-1687) | Integration | PASS | Real tmpdir Project/** → allow |
| test_grep_search_uppercase_github_include_pattern_denied (TST-1688) | Security | PASS | .GITHUB/** includePattern denied (normalize_path lowercases) |
| test_file_search_traversal_combined_with_github_denied (TST-1689) | Security | PASS | src/../.github → both triggers active |
| test_grep_search_nested_vscode_include_pattern_denied (TST-1690) | Security | PASS | Nested tool_input .vscode includePattern denied |

### Full regression suite

| Run | Environment | Result |
|-----|-------------|--------|
| Full suite (3208 tests) | Windows 11 + Python 3.11 | 3208 passed, 29 skipped, 1 xfailed, 2 failed (pre-existing) |

**Pre-existing failures (not caused by FIX-021):**
- `FIX-009::test_no_duplicate_tst_ids` — duplicate TST-1557 and TST-599 in test-results.csv (pre-existing BUG)
- `INS-005::test_uninstall_delete_type_is_filesandirs` — BUG-045 (`filesandordirs` vs `filesandirs`)

---

## Code Review

### `validate_grep_search()` change
The original code returned `"deny"` when `extract_path(data)` returned `None`. Because
`grep_search` never includes a `filePath` field, every call without a restricted
`includePattern` was wrongly denied. The fix returns `"allow"` at that point, which is
correct — the `includeIgnoredFiles` and `includePattern` guards ran first, so if we reach
the `raw_path is None` branch, the call is safe.

**Verified:** `includeIgnoredFiles=True` still triggers before the None-path branch → deny preserved.
**Verified:** Restricted-zone `includePattern` still triggers before the None-path branch → deny preserved.

### `validate_semantic_search()` change
The old code unconditionally returned `"deny"`. The fix unconditionally returns `"allow"`.
This is safe because VS Code's `search.exclude` settings exclude `.github/`, `.vscode/`,
and `NoAgentZone/` from the semantic index entirely — semantic search cannot return content
from those directories even without gate-level filtering.

**Verified:** The function accepts `data` and `ws_root` for API consistency; neither is needed given the policy rationale.

### `file_search` handler in `decide()`
The handler correctly extracts the query from both flat and nested (`tool_input.query`) formats.
String type check prevents non-string values from being zone-checked. Case-insensitive check
via `.lower()` prevents bypass via mixed-case zone names. `".."` check prevents path traversal.

**Verified:** All four deny triggers tested (`.github`, `.vscode`, `noagentzone`, `..`) including
combined traversal+zone case.

### Sync to `templates/coding/`
`security_gate.py` copied and `update_hashes.py` run in both directories.

---

## Bugs Found

None. All previously open concerns were the pre-existing BUG-045 (INS-005) and FIX-009 dup
TST-IDs, neither related to this workpackage.

---

## TODOs for Developer

None.

---

## Verdict

**PASS** — mark FIX-021 as Done.

All 33 FIX-021 tests pass (24 developer + 9 tester edge-case). The full regression suite
shows only the 2 known pre-existing failures, unchanged from before this WP. The security
properties that protect `.github/`, `.vscode/`, and `NoAgentZone/` are all intact. BUG-054
is resolved.
