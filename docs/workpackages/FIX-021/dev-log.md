# Dev Log — FIX-021: Fix Search Tools Blocking for Project Folder

**WP ID:** FIX-021  
**Branch:** fix/FIX-021-search-tools  
**Developer:** Developer Agent  
**Date:** 2026-03-17  
**Status:** Review  

---

## Problem

BUG-054. Search tools (`grep_search`, `file_search`, `semantic_search`) were blocked even for legitimate project-folder searches.

Root causes:
1. `validate_grep_search()` returned `"deny"` when `extract_path(data)` returned `None` — but `grep_search` never provides a `filePath` field, so every call without a dangerous `includePattern` was denied.
2. `validate_semantic_search()` unconditionally returned `"deny"`.
3. `file_search` was in `_EXEMPT_TOOLS` but `extract_path()` returns `None` for its payload, causing the bottom-of-`decide()` fail-closed path to deny it.

---

## Implementation

### File: `Default-Project/.github/hooks/scripts/security_gate.py`

**Change 1 — `validate_grep_search()` (around line 1496):**  
Changed `return "deny"` when `raw_path is None` to `return "allow"`. The includeIgnoredFiles and includePattern checks run first — if they pass, VS Code's `search.exclude` settings prevent restricted content from being returned.

**Change 2 — `validate_semantic_search()` (around line 1513):**  
Changed `return "deny"` to `return "allow"`. Updated docstring to explain the rationale: VS Code's `search.exclude` settings hide `.github/`, `.vscode/`, and `NoAgentZone/` from the semantic index.

**Change 3 — `decide()` (around line 1742):**  
Added explicit `file_search` handler after `get_errors` and before write tools. Allows `file_search` by default but denies if the query string explicitly names a restricted zone (`.github`, `.vscode`, `noagentzone`) or contains `..` (path traversal).

### Sync

After changes, `security_gate.py` was copied from `Default-Project/` to `templates/coding/` and `update_hashes.py` was run in both directories to re-embed the SHA256 integrity hashes.

---

## Tests Written

**New file:** `tests/FIX-021/test_fix021_search_tools.py` (24 tests, TST-1658 to TST-1681)

| Test | Scenario | Expected |
|------|----------|----------|
| test_grep_search_no_params_allow | no params, no filePath | allow |
| test_grep_search_no_params_via_validate | via validate_grep_search | allow |
| test_grep_search_project_include_pattern_allow | safe params, no restrictive flags | allow |
| test_grep_search_nested_project_include_pattern_allow | nested tool_input, safe | allow |
| test_grep_search_include_ignored_files_true_denied | includeIgnoredFiles=True | deny |
| test_grep_search_include_ignored_files_string_true_denied | includeIgnoredFiles="true" | deny |
| test_grep_search_github_include_pattern_denied | includePattern=.github/** | deny |
| test_grep_search_vscode_include_pattern_denied | includePattern=.vscode/** | deny |
| test_grep_search_noagentzone_include_pattern_denied | includePattern=NoAgentZone/** | deny |
| test_semantic_search_allow | basic query | allow |
| test_semantic_search_validate_allow | via validate_semantic_search | allow |
| test_semantic_search_nested_format_allow | nested tool_input | allow |
| test_semantic_search_with_protected_query_allow | query text mentions zone name | allow |
| test_file_search_basic_query_allow | plain query | allow |
| test_file_search_nested_format_allow | nested tool_input | allow |
| test_file_search_no_query_allow | no query field | allow |
| test_file_search_github_in_query_denied | .github in query | deny |
| test_file_search_github_nested_denied | .github in nested query | deny |
| test_file_search_github_mixed_case_denied | .GITHUB (case-insensitive) | deny |
| test_file_search_noagentzone_in_query_denied | NoAgentZone in query | deny |
| test_file_search_noagentzone_lowercase_denied | noagentzone in query | deny |
| test_file_search_vscode_in_query_denied | .vscode in query | deny |
| test_file_search_dotdot_in_query_denied | .. (path traversal) in query | deny |
| test_file_search_dotdot_nested_denied | .. in nested query | deny |

**Updated tests (expected behavior changed from deny → allow):**
- `tests/SAF-003/test_saf003_tool_parameter_validation.py` — TST-290, TST-293, TST-295, TST-296, TST-297, TST-307, TST-311
- `tests/SAF-009/test_saf009_cross_platform.py` — TST-525, TST-526, TST-539, TST-541, TST-566, TST-570
- `tests/SAF-013/test_saf013_security_gate_2tier.py` — test_grep_search_no_path_returns_deny, test_semantic_search_always_returns_deny, test_response_json_never_ask (semantic_search scenario)
- `tests/SAF-024/test_saf024_edge_cases.py` — TST-615 (now verifies allow, not deny)

---

## Test Results

Full suite: **3199 passed, 29 skipped, 1 xfailed, 2 failed**

Pre-existing failures (unchanged):
- `FIX-009::test_no_duplicate_tst_ids` — duplicate TST-IDs in test-results.csv (pre-existing BUG)
- `INS-005::test_uninstall_delete_type_is_filesandirs` — BUG-045 (pre-existing)

---

## Files Changed

- `Default-Project/.github/hooks/scripts/security_gate.py` — 3 logic changes (validate_grep_search, validate_semantic_search, decide file_search handler)
- `templates/coding/.github/hooks/scripts/security_gate.py` — synced from Default-Project
- `tests/FIX-021/test_fix021_search_tools.py` — new test file (24 tests)
- `tests/SAF-003/test_saf003_tool_parameter_validation.py` — 7 tests updated
- `tests/SAF-009/test_saf009_cross_platform.py` — 6 tests updated
- `tests/SAF-013/test_saf013_security_gate_2tier.py` — 3 tests updated
- `tests/SAF-024/test_saf024_edge_cases.py` — 1 test updated
- `docs/workpackages/workpackages.csv` — FIX-021 status → Review
- `docs/test-results/test-results.csv` — test run logged
