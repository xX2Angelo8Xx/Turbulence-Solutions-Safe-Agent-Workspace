# Test Report — SAF-049

**Tester:** GitHub Copilot  
**Date:** 2026-03-25  
**Iteration:** 1  

## Summary

SAF-049 corrects the Tool Permission Matrix in `templates/agent-workbench/Project/AGENT-RULES.md` by replacing the inaccurate "no zone restriction" label on `grep_search` and `file_search` with accurate descriptions reflecting actual enforcement behavior (BUG-114). The change is documentation-only; no application source code was modified.

All 15 WP-specific tests pass. The 72 failures in the full regression suite are pre-existing (verified: `git diff main...SAF-049/search-doc-fix --stat` shows no changes to any source file under test by those failing suites). No regressions were introduced.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| SAF-049 WP-specific suite (15 tests) | Unit | PASS | TST-2196 |
| Full regression suite (6641 total) | Regression | PASS* | TST-2195 — 72 pre-existing failures, 0 new failures |

\* 72 pre-existing failures confirmed unrelated to SAF-049 changes.

## Developer Tests (11)

| Test | Result |
|------|--------|
| `test_grep_search_no_longer_says_no_zone_restriction` | PASS |
| `test_file_search_no_longer_says_no_zone_restriction` | PASS |
| `test_grep_search_documents_include_pattern_restriction` | PASS |
| `test_file_search_documents_include_pattern_restriction` | PASS |
| `test_grep_search_documents_include_ignored_files_restriction` | PASS |
| `test_file_search_documents_include_ignored_files_restriction` | PASS |
| `test_grep_search_still_allowed_for_general_use` | PASS |
| `test_file_search_still_allowed_for_general_use` | PASS |
| `test_semantic_search_unchanged` | PASS |
| `test_grep_search_permission_is_zone_checked` | PASS |
| `test_file_search_permission_is_zone_checked` | PASS |

## Tester Edge-Case Tests (4 added)

| Test | Rationale | Result |
|------|-----------|--------|
| `test_grep_search_mentions_noagentzone_example` | Developer test checked file_search for NoAgentZone but not grep_search — verified symmetry | PASS |
| `test_file_search_uses_query_parameter_not_only_include_pattern` | `file_search` uses `query` parameter (not `includePattern`); docs must name the correct parameter | PASS |
| `test_search_tools_section_header_present` | Confirms the "Search Tools" section header in the matrix was not accidentally removed | PASS |
| `test_grep_search_blocked_appears_for_both_restrictions` | Verifies "blocked" is mentioned at least twice in the grep_search row — once per restriction | PASS |

## Code Review

- Only `templates/agent-workbench/Project/AGENT-RULES.md` was modified (documentation).
- `grep_search` row: updated from `Allowed / no zone restriction` to `Zone-checked` + detailed notes listing both blocked parameters with `NoAgentZone/**` example.
- `file_search` row: identical correction applied; correctly uses `query` parameter name (not `includePattern`).
- `semantic_search` row: unchanged — "no zone restriction" is accurate for this tool.
- BUG-114: marked Fixed with `Fixed In WP: SAF-049` in `docs/bugs/bugs.csv`. ✓
- WP status set to `Review` in `workpackages.csv` before handoff. ✓

## Bugs Found

None.

## TODOs for Developer

None.

## Verdict

PASS — mark WP as Done.
