# Dev Log — SAF-009

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective
Create automated tests (pytest) validating all security zones, all bypass vectors from the audit report, and all tool types. Tests must run on Windows, macOS, and Linux. Every audit finding has a regression test.

## Implementation Summary
Created a comprehensive cross-platform integration test suite (`tests/SAF-009/test_saf009_cross_platform.py`) that consolidates key security scenarios across all dependent WPs (SAF-001 through SAF-008). The suite deliberately does NOT duplicate unit tests that already exist in the individual WP test suites — instead it provides:

1. **Audit Finding Regression Tests** — one regression test per audit finding (AF-1 through AF-6) using the same payloads that originally exposed each vulnerability
2. **All Tool Types Matrix** — every tool category (write, search, terminal, read, unknown, always-allow) exercised against every zone (allow/deny/ask), using the VS Code nested `tool_input` format where applicable
3. **Cross-Platform Path Format Tests** — Windows backslash, WSL `/mnt/c/`, and Git Bash `/c/` paths tested for both write and read tools across all zones
4. **VS Code Nested Hook Format Integration** — tests using the realistic `{"tool_name": ..., "tool_input": {...}}` structure that VS Code sends to the hook

All tests use `os.sep`-agnostic path formulations and forward-slash normalization so they run identically on Windows, macOS, and Linux without platform-specific guards.

## Files Changed
- `docs/workpackages/workpackages.csv` — set SAF-009 to In Progress / Assigned To Developer Agent
- `docs/workpackages/SAF-009/dev-log.md` — this file (created)
- `tests/SAF-009/__init__.py` — created (empty package marker)
- `tests/SAF-009/test_saf009_cross_platform.py` — 50 new integration/regression/cross-platform tests

## Tests Written
- test_af1_core_deny_malformed_input — regression AF-1: JSON parse failure returns deny
- test_af1_core_allow_project_path — regression AF-1: Project/ path returns allow
- test_af2_grep_includepattern_github_nested — regression AF-2: nested tool_input includePattern .github/** denied
- test_af2_grep_brace_expansion_bypass — regression AF-2: brace-expansion bypass {src,.github}/** denied
- test_af3_semantic_search_never_allow — regression AF-3: semantic_search never auto-allowed
- test_af3_semantic_search_nested_input — regression AF-3: nested format semantic_search returns ask
- test_af4_recursive_get_childitem — regression AF-4: Get-ChildItem -Recurse on workspace root denied
- test_af4_recursive_find_command — regression AF-4: find . targeting workspace root denied
- test_af5_integrity_constants_not_zeroed — regression AF-5: embedded hash constants are non-zero and 64-char hex
- test_af5_verify_integrity_function_callable — regression AF-5: verify_file_integrity() exists and is callable
- test_af6_all_write_tools_project_allowed — regression AF-6: all write tools inside Project/ allowed
- test_af6_all_write_tools_outside_denied — regression AF-6: all write tools outside Project/ denied
- test_tools_create_file_project — create_file → Project/ → allow
- test_tools_create_file_github — create_file → .github/ → deny
- test_tools_replace_project — replace_string_in_file → Project/ → allow
- test_tools_replace_docs — replace_string_in_file → docs/ (ask zone) → deny (write restriction)
- test_tools_multi_replace_project — multi_replace_string_in_file → Project/ → allow
- test_tools_multi_replace_vscode — multi_replace_string_in_file → .vscode/ → deny
- test_tools_grep_safe_no_path — grep_search safe params, no path → ask
- test_tools_grep_blocked_include — grep_search includePattern=.github/** → deny
- test_tools_semantic_search — semantic_search → ask
- test_tools_read_file_project — read_file → Project/ → allow
- test_tools_read_file_github — read_file → .github/ → deny
- test_tools_list_dir_project — list_dir → Project/ → allow
- test_tools_list_dir_noagentzone — list_dir → NoAgentZone/ → deny
- test_tools_terminal_safe — run_in_terminal safe pytest command → ask
- test_tools_terminal_blocked_path — run_in_terminal cat .github/secret → deny
- test_tools_unknown_tool_asks — unknown non-exempt tool → ask
- test_crossplat_win_create_project — Windows backslash path → Project/ → allow
- test_crossplat_win_create_github — Windows backslash path → .github/ → deny
- test_crossplat_wsl_create_project — WSL /mnt/c/ path → Project/ → allow
- test_crossplat_wsl_create_vscode — WSL /mnt/c/ path → .vscode/ → deny
- test_crossplat_gitbash_create_project — Git Bash /c/ path → Project/ → allow
- test_crossplat_gitbash_create_noagentzone — Git Bash /c/ path → NoAgentZone/ → deny
- test_crossplat_win_read_project — Windows path → read_file → Project/ → allow
- test_crossplat_win_read_github — Windows path → read_file → .github/ → deny
- test_crossplat_wsl_read_project — WSL path → read_file → Project/ → allow
- test_crossplat_wsl_read_vscode — WSL path → read_file → .vscode/ → deny
- test_crossplat_gitbash_read_project — Git Bash path → read_file → Project/ → allow
- test_crossplat_gitbash_read_noagentzone — Git Bash path → read_file → NoAgentZone/ → deny
- test_nested_read_file_project — VS Code nested tool_input → read_file → allow
- test_nested_read_file_github — VS Code nested tool_input → read_file → deny
- test_nested_create_file_project — VS Code nested tool_input → create_file → allow
- test_nested_create_file_outside — VS Code nested tool_input → create_file → docs/ → deny
- test_nested_grep_include_github — VS Code nested tool_input → grep_search includePattern → deny
- test_nested_grep_safe — VS Code nested tool_input → grep_search safe → ask
- test_nested_terminal_safe — VS Code nested tool_input → run_in_terminal safe → ask
- test_nested_terminal_blocked — VS Code nested tool_input → run_in_terminal .vscode ref → deny
- test_nested_always_allow — VS Code nested tool_input → ask_questions with deny path → allow
- test_nested_semantic_search_asks — VS Code nested tool_input → semantic_search → ask

## Known Limitations
- The cross-platform tests use path-prefix simulation (e.g., `/mnt/c/`, `/c/`, `c:/`) rather than actually running on multiple OSes — this is consistent with the approach used in all prior SAF test suites and accurately tests the normalization logic.
- SAF-008 integrity verification is tested functionally (constants are valid hex, function is callable) rather than running the full disk-based integrity check on tampered files, since the individual SAF-008 suite already covers that thoroughly.
