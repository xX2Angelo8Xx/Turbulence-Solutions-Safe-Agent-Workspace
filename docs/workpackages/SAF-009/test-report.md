# Test Report — SAF-009

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 1

## Summary

SAF-009 delivers 50 integration / regression / cross-platform tests covering every audit finding, every tool type, all three security zones, three path formats (Windows backslash, WSL `/mnt/c/`, Git Bash `/c/`), and the VS Code nested `tool_input` hook format. The suite runs cleanly in 0.19 s with zero failures.

The Tester added 9 edge-case tests covering alternative path field names (`path`, `file_path`), `includeIgnoredFiles=True` in nested format, the `tree` recursive-enumeration vector, write-tool behaviour when `path` field is used, and the fail-safe empty-payload scenario. All 9 edge-case tests pass immediately, confirming the underlying implementation is robust beyond the Developer's test matrix.

All 59 SAF-009 tests (50 Developer + 9 Tester) pass.  
No regressions were introduced in any prior WP test suite.

---

## Tests Executed

### SAF-009 Developer Suite (50 tests)

| Test (TST-ID) | Type | Result | Notes |
|---|---|---|---|
| TST-521 test_af1_core_deny_malformed_input | Regression | PASS | AF-1: malformed JSON fails closed |
| TST-522 test_af1_core_allow_project_path | Regression | PASS | AF-1: Project/ path allowed end-to-end |
| TST-523 test_af2_grep_includepattern_github_nested | Regression | PASS | AF-2: nested includePattern .github → deny |
| TST-524 test_af2_grep_brace_expansion_bypass | Regression | PASS | AF-2: {src,.github}/** bypass denied |
| TST-525 test_af3_semantic_search_never_allow | Regression | PASS | AF-3: semantic_search never auto-allowed |
| TST-526 test_af3_semantic_search_nested_input | Regression | PASS | AF-3: nested semantic_search → ask |
| TST-527 test_af4_recursive_get_childitem | Regression | PASS | AF-4: Get-ChildItem -Recurse ws-root denied |
| TST-528 test_af4_recursive_find_command | Regression | PASS | AF-4: find . ws-root denied |
| TST-529 test_af5_integrity_constants_not_zeroed | Regression | PASS | AF-5: hash constants valid 64-char hex |
| TST-530 test_af5_verify_integrity_function_callable | Regression | PASS | AF-5: verify_file_integrity() callable → bool |
| TST-531 test_af6_all_write_tools_project_allowed | Regression | PASS | AF-6: all _WRITE_TOOLS allowed on Project/ |
| TST-532 test_af6_all_write_tools_outside_denied | Regression | PASS | AF-6: all write tools denied outside Project/ |
| TST-533 test_tools_create_file_project | Integration | PASS | create_file → Project/ → allow |
| TST-534 test_tools_create_file_github | Integration | PASS | create_file → .github/ → deny |
| TST-535 test_tools_replace_project | Integration | PASS | replace_string_in_file → Project/ → allow |
| TST-536 test_tools_replace_docs | Integration | PASS | replace → docs/ (ask zone) → deny (SAF-007) |
| TST-537 test_tools_multi_replace_project | Integration | PASS | multi_replace → Project/ → allow |
| TST-538 test_tools_multi_replace_vscode | Integration | PASS | multi_replace → .vscode/ → deny |
| TST-539 test_tools_grep_safe_no_path | Integration | PASS | grep safe, no path → ask |
| TST-540 test_tools_grep_blocked_include | Integration | PASS | grep includePattern=.github/** → deny |
| TST-541 test_tools_semantic_search | Integration | PASS | semantic_search → ask |
| TST-542 test_tools_read_file_project | Integration | PASS | read_file → Project/ → allow |
| TST-543 test_tools_read_file_github | Integration | PASS | read_file → .github/ → deny |
| TST-544 test_tools_list_dir_project | Integration | PASS | list_dir → Project/ → allow |
| TST-545 test_tools_list_dir_noagentzone | Integration | PASS | list_dir → NoAgentZone/ → deny |
| TST-546 test_tools_terminal_safe | Integration | PASS | run_in_terminal safe cmd → ask |
| TST-547 test_tools_terminal_blocked_path | Integration | PASS | run_in_terminal .github ref → deny |
| TST-548 test_tools_unknown_tool_asks | Integration | PASS | unrecognised tool → ask |
| TST-549 test_crossplat_win_create_project | Cross-platform | PASS | Win backslash → create_file → Project/ → allow |
| TST-550 test_crossplat_win_create_github | Cross-platform | PASS | Win backslash → create_file → .github/ → deny |
| TST-551 test_crossplat_wsl_create_project | Cross-platform | PASS | WSL /mnt/c/ → create_file → Project/ → allow |
| TST-552 test_crossplat_wsl_create_vscode | Cross-platform | PASS | WSL /mnt/c/ → create_file → .vscode/ → deny |
| TST-553 test_crossplat_gitbash_create_project | Cross-platform | PASS | Git Bash /c/ → create_file → Project/ → allow |
| TST-554 test_crossplat_gitbash_create_noagentzone | Cross-platform | PASS | Git Bash /c/ → NoAgentZone/ → deny |
| TST-555 test_crossplat_win_read_project | Cross-platform | PASS | Win path → read_file → Project/ → allow |
| TST-556 test_crossplat_win_read_github | Cross-platform | PASS | Win path → read_file → .github/ → deny |
| TST-557 test_crossplat_wsl_read_project | Cross-platform | PASS | WSL path → read_file → Project/ → allow |
| TST-558 test_crossplat_wsl_read_vscode | Cross-platform | PASS | WSL path → read_file → .vscode/ → deny |
| TST-559 test_crossplat_gitbash_read_project | Cross-platform | PASS | Git Bash path → read_file → Project/ → allow |
| TST-560 test_crossplat_gitbash_read_noagentzone | Cross-platform | PASS | Git Bash path → read_file → NoAgentZone/ → deny |
| TST-561 test_nested_read_file_project | Integration | PASS | VS Code nested format → read_file → allow |
| TST-562 test_nested_read_file_github | Integration | PASS | VS Code nested format → read_file → deny |
| TST-563 test_nested_create_file_project | Integration | PASS | VS Code nested format → create_file → allow |
| TST-564 test_nested_create_file_outside | Integration | PASS | VS Code nested format → create_file → docs/ → deny |
| TST-565 test_nested_grep_include_github | Integration | PASS | VS Code nested format → grep includePattern → deny |
| TST-566 test_nested_grep_safe | Integration | PASS | VS Code nested format → grep safe → ask |
| TST-567 test_nested_terminal_safe | Integration | PASS | VS Code nested format → terminal safe → ask |
| TST-568 test_nested_terminal_blocked | Integration | PASS | VS Code nested format → terminal .vscode → deny |
| TST-569 test_nested_always_allow | Integration | PASS | always-allow tool bypasses zone checks → allow |
| TST-570 test_nested_semantic_search_asks | Integration | PASS | VS Code nested format → semantic_search → ask |

### Tester Edge-Case Tests (9 tests)

| Test (TST-ID) | Type | Result | Notes |
|---|---|---|---|
| TST-578 test_path_field_project_allowed | Security | PASS | `path` field variant → Project/ → allow |
| TST-579 test_path_field_github_denied | Security | PASS | `path` field variant → .github/ → deny |
| TST-580 test_file_path_underscore_field_project_allowed | Security | PASS | `file_path` field → Project/ → allow |
| TST-581 test_file_path_underscore_field_vscode_denied | Security | PASS | `file_path` field → .vscode/ → deny |
| TST-582 test_include_ignored_files_nested_format_denied | Security | PASS | includeIgnoredFiles=True in nested tool_input → deny |
| TST-583 test_af4_tree_command_blocked | Security | PASS | `tree /workspace` recursive enumeration → deny |
| TST-584 test_decide_empty_dict_not_allow | Security | PASS | decide({}, WS) must not return allow (fail-safe) |
| TST-585 test_write_tool_path_field_outside_project_denied | Security | PASS | create_file `path` field → docs/ → deny |
| TST-586 test_write_tool_path_field_inside_project_allowed | Security | PASS | create_file `path` field → Project/ → allow |

### Full SAF-009 Suite Run

| Test Run | Type | Result | Notes |
|---|---|---|---|
| TST-587 SAF-009 combined suite (59 tests) | Regression | PASS | 59/59 — 50 Developer + 9 Tester; 0.17 s; zero failures |

---

## Coverage Assessment — Audit Findings

| Audit Finding | Covered By | Tests | Status |
|---|---|---|---|
| AF-1: Core hook / JSON input validation | SAF-001 (unit) + SAF-009 TST-521/522 | 2 regressions + all SAF-001 unit tests | ✅ COVERED |
| AF-2: grep_search includePattern bypass | SAF-003 (unit) + SAF-009 TST-523/524 | 2 regressions (flat + nested formats, brace expansion) | ✅ COVERED |
| AF-3: semantic_search zone bypass | SAF-003 (unit) + SAF-009 TST-525/526 | 2 regressions (plain + nested) | ✅ COVERED |
| AF-4: Recursive enumeration | SAF-006 (unit) + SAF-009 TST-527/528 + TST-583 (Tester tree) | 3 regression vectors (Get-ChildItem, find, tree) | ✅ COVERED |
| AF-5: Hook file integrity | SAF-008 (unit) + SAF-009 TST-529/530 | 2 regressions (constants + function callable) | ✅ COVERED |
| AF-6: Write restriction outside Project/ | SAF-007 (unit) + SAF-009 TST-531/532 | 2 regressions (all write tools × all zones) | ✅ COVERED |

All 6 audit findings have regression tests in this suite. ✅

---

## Bugs Found

None. No new bugs discovered during review.

---

## TODOs for Developer

None.

---

## Verdict

**PASS — mark SAF-009 as Done.**

All 59 SAF-009 tests pass (50 Developer + 9 Tester edge cases). Every audit finding (AF-1 through AF-6) has dedicated regression coverage. All tool types, all three zones, three cross-platform path formats, and the VS Code nested hook format are validated. No regressions in the prior test suite.
