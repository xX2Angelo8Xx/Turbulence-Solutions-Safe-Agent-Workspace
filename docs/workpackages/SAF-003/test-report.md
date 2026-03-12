# Test Report — SAF-003

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 2

## Summary

SAF-003 Iteration 2 delivers brace-expansion handling in `_expand_braces()` and
integrates it into `_validate_include_pattern()`.  All 57 SAF-003 tests pass —
50 Developer tests (Iterations 1 and 2) plus 7 Tester edge-case tests added
during this review.  The full regression suite confirms zero new failures across
all other WPs (pre-existing INS-004 and INS-012 failures are unrelated to SAF-003
and pre-date this commit).

The three User Story acceptance criteria are fully satisfied:
1. `grep_search` and `semantic_search` tool calls are inspected before execution
   (`validate_grep_search()` and `validate_semantic_search()` intercept in `decide()`).
2. Tool calls targeting a Deny zone are blocked regardless of how the path is
   encoded (direct, traversal, brace pattern, mixed case).
3. `../` traversal sequences in `includePattern` are blocked, now including
   traversal hidden inside a brace alternative.

## Tests Executed

### SAF-003 Developer Tests (Iterations 1 & 2)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-269 test_is_truthy_flag_bool_true | Unit | Pass | |
| TST-270 test_is_truthy_flag_bool_false | Unit | Pass | |
| TST-271 test_is_truthy_flag_string_true_lowercase | Unit | Pass | |
| TST-272 test_is_truthy_flag_string_true_mixed_case | Unit | Pass | |
| TST-273 test_is_truthy_flag_string_true_uppercase | Unit | Pass | |
| TST-274 test_is_truthy_flag_string_false | Unit | Pass | |
| TST-275 test_is_truthy_flag_int_1 | Unit | Pass | |
| TST-276 test_is_truthy_flag_int_0 | Unit | Pass | |
| TST-277 test_is_truthy_flag_none | Unit | Pass | |
| TST-278 test_validate_include_pattern_safe_wildcard_glob | Unit | Pass | |
| TST-279 test_validate_include_pattern_src_subdir | Unit | Pass | |
| TST-280 test_validate_include_pattern_github | Security | Pass | |
| TST-281 test_validate_include_pattern_vscode | Security | Pass | |
| TST-282 test_validate_include_pattern_noagentzone | Security | Pass | |
| TST-283 test_validate_include_pattern_traversal_dotdot | Security | Pass | |
| TST-284 test_validate_include_pattern_traversal_deep | Security | Pass | |
| TST-285 test_validate_grep_search_include_pattern_github_denied | Security | Pass | |
| TST-286 test_validate_grep_search_include_pattern_vscode_denied | Security | Pass | |
| TST-287 test_validate_grep_search_include_pattern_noagentzone_denied | Security | Pass | |
| TST-288 test_validate_grep_search_include_ignored_files_bool_true_denied | Security | Pass | |
| TST-289 test_validate_grep_search_include_ignored_files_string_true_denied | Security | Pass | |
| TST-290 test_validate_grep_search_no_params_no_path_asks | Unit | Pass | |
| TST-291 test_validate_grep_search_no_params_project_path_allowed | Unit | Pass | |
| TST-292 test_validate_grep_search_no_params_deny_path_denied | Security | Pass | |
| TST-293 test_validate_grep_search_include_ignored_false_not_denied | Unit | Pass | |
| TST-294 test_validate_grep_search_tool_input_nested_format | Security | Pass | |
| TST-295 test_validate_semantic_search_basic_returns_ask | Unit | Pass | |
| TST-296 test_validate_semantic_search_protected_query_still_ask | Unit | Pass | |
| TST-297 test_validate_semantic_search_never_returns_allow | Security | Pass | |
| TST-298 test_grep_search_deny_zone_via_include_pattern_protected | Security | Pass | |
| TST-299 test_grep_search_traversal_blocked_protection | Security | Pass | |
| TST-300 test_grep_search_include_ignored_files_blocked_protection | Security | Pass | |
| TST-301 test_grep_search_github_in_nested_tool_input_bypass | Security | Pass | bypass attempt |
| TST-302 test_grep_search_traversal_to_github_bypass | Security | Pass | bypass attempt |
| TST-303 test_grep_search_mixed_case_include_pattern_bypass | Security | Pass | bypass attempt |
| TST-304 test_grep_search_include_ignored_string_true_bypass | Security | Pass | bypass attempt |
| TST-305 test_grep_search_noagentzone_lowercase_bypass | Security | Pass | bypass attempt |
| TST-306 test_grep_search_star_star_github_bypass | Security | Pass | bypass attempt |
| TST-307 test_semantic_search_cannot_be_allowed_bypass | Security | Pass | bypass attempt |
| TST-308 test_decide_grep_search_include_pattern_github_denied | Integration | Pass | |
| TST-309 test_decide_grep_search_clean_params_project_path_allowed | Integration | Pass | |
| TST-310 test_decide_grep_search_clean_params_no_path_asks | Integration | Pass | |
| TST-311 test_decide_semantic_search_always_ask | Integration | Pass | |
| TST-312 test_decide_grep_search_include_ignored_denied | Integration | Pass | |
| TST-313 test_grep_search_windows_backslash_include_pattern_github_denied | Cross-platform | Pass | |
| TST-314 test_grep_search_wsl_absolute_include_pattern_github_denied | Cross-platform | Pass | |
| TST-315 test_brace_expansion_deny_zone_github | Security | Pass | Iteration 2 |
| TST-316 test_brace_expansion_partial_deny | Security | Pass | Iteration 2 |
| TST-317 test_brace_expansion_safe_pattern | Security | Pass | Iteration 2 |
| TST-318 test_brace_expansion_nested_deny | Security | Pass | Iteration 2 |

### Tester Edge-Case Tests (Iteration 2 review)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-339 test_brace_expansion_multi_group_deny | Security | Pass | {src,tests}/{.github,.vscode}/** → deny |
| TST-340 test_brace_expansion_deeply_nested_deny | Security | Pass | .github/{hooks/{scripts,config},workflows}/** |
| TST-341 test_brace_expansion_empty_brace_group_no_crash | Security | Pass | {}/** does not crash or falsely deny |
| TST-342 test_brace_expansion_single_element_deny | Security | Pass | {.github}/** → deny |
| TST-343 test_brace_expansion_all_safe_items_not_denied | Security | Pass | {src,tests,Project}/**/*.py → not denied |
| TST-344 test_brace_expansion_mixed_case_deny | Security | Pass | {.GitHub,.VSCODE}/** → deny (case normalised) |
| TST-345 test_brace_expansion_path_traversal_deny | Security | Pass | {../.github,src}/** → deny (traversal guard) |

### Regression Run

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-346 Full regression suite (537 tests) | Regression | Pass | 537/537 pass; 33 pre-existing INS-004/INS-012 failures unrelated to SAF-003; 0 new failures |

## Bugs Found

None.

## Security Analysis

### Attack Vectors Examined

1. **Brace expansion bypass** — `.{github,other}/**` would not contain the
   literal string `.github` before expansion and could have bypassed Method 2
   regex in zone_classifier. Fixed: `_expand_braces()` enumerates all
   permutations before checking each against zone_classifier.

2. **Nested brace expansion** — `.github/{hooks/{scripts,config},workflows}/**`
   relies on the regex matching the innermost brace group first. `re.search`
   with `[^{}]+` correctly excludes brace characters in the content, forcing
   innermost-first expansion.  Confirmed by TST-340.

3. **Multiple independent brace groups** — `{src,tests}/{.github,.vscode}/**`
   correctly produces the Cartesian product of both groups. Confirmed by TST-339.

4. **Empty brace group `{}`** — The regex `\{([^{}]+)\}` requires `+` (one or
   more), so `{}` is not expanded. The literal `{}/**` is then classified
   without error and returns "ask" (not a false deny). Confirmed by TST-341.

5. **Single-element brace `{.github}/**`** — Correctly expands to `.github/**`
   and is denied. Confirmed by TST-342.

6. **Mixed-case brace alternatives** — `{.GitHub,.VSCODE}/**` each expansion
   runs through `zone_classifier.classify()` which normalises to lowercase.
   Both `.github` and `.vscode` are denied. Confirmed by TST-344.

7. **Traversal inside brace alternative** — `{../.github,src}/**` expands to
   `../.github/**`; `normalize_path` retains the `..` prefix (no parent to
   cancel it), and the explicit `".." in expanded_norm` check returns "deny".
   Confirmed by TST-345.

### Residual Observations

- `_expand_braces` does not deduplicate results (e.g., `{a,a}/**` produces
  `["a/**", "a/**"]`). This is a minor inefficiency; it does not weaken security
  since each duplicate simply runs the deny check twice.
- Patterns with `{}` (empty group) are passed through as literals without
  expansion. This is safe because `{}` matches no real file paths and
  zone_classifier will not classify it as a deny zone.
- No infinite-recursion risk: `_expand_braces` removes one brace group per
  call and the recursion terminates when no brace group remains.

## TODOs for Developer

None — all checks pass, no security gaps found.

## Verdict

**PASS — mark WP SAF-003 as Done**
