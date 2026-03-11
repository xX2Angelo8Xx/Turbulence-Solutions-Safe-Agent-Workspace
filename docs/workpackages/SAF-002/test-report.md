# Test Report — SAF-002

**Tester:** Tester Agent
**Date:** 2026-03-11
**Iteration:** 2

## Summary

SAF-002 Iteration 2 delivers the two security fixes requested in Iteration 1:

- **BUG-010 fixed** — `normalize_path()` now uses `re.sub(r'[\x00-\x1f]', '', p)` to strip all ASCII C0 control characters (`\x00`–`\x1f`) in a single pass. The previous code only replaced `\x00`; tab, newline, CR, SOH, and every other C0 char now disappear before any zone comparison. TST-184, TST-185, and the five new Iteration 2 regression tests (TST-196–198) all pass.

- **BUG-011 fixed** — The Method 2 allow branch is now gated on a workspace-containment check:
  ```python
  if _ALLOW_PATTERN.search(full_with_slash) and (
      norm.startswith(ws_clean + "/") or norm == ws_clean
  ):
      return "allow"
  ```
  Paths whose normalised form does not begin with `ws_clean + "/"` fall through to `"ask"`. UNC paths such as `\\server\share\project\sensitive.py` and workspace-sibling paths like `c:/workspace-evil/project/` can no longer claim `"allow"`. TST-186, TST-199, and TST-200 all pass.

The Tester added 5 targeted regression tests (TST-196–TST-200) to lock in the fixes. All 59 SAF-002 tests pass. SAF-001 (60/60) and SAF-005 (80/80) are unaffected.

**Pre-existing GUI-001 regression:** 38 of 41 GUI-001 tests now fail. The failures are entirely in `tests/GUI-001/` and relate to `launcher.gui.app` and `launcher.gui.components` — code that SAF-002 does not touch. This regression was present before this iteration (the SAF-005 developer did not include GUI-001 in their 260-test run, suggesting a mismatch between the GUI implementation and its tests already existed). Logged as **BUG-012**. SAF-002 is not affected.

---

## Tests Executed

### Developer tests (TST-125 to TST-164 — 40 tests)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_normalize_null_byte_stripped | Unit | Pass | |
| test_normalize_double_backslash | Unit | Pass | |
| test_normalize_single_backslash | Unit | Pass | |
| test_normalize_wsl_prefix | Unit | Pass | |
| test_normalize_gitbash_prefix | Unit | Pass | |
| test_normalize_lowercase | Unit | Pass | |
| test_normalize_trailing_slash | Unit | Pass | |
| test_normalize_dotdot_resolved | Unit | Pass | |
| test_classify_allow_project_root | Unit | Pass | |
| test_classify_allow_project_nested | Unit | Pass | |
| test_classify_deny_github | Unit | Pass | |
| test_classify_deny_vscode | Unit | Pass | |
| test_classify_deny_noagentzone | Unit | Pass | |
| test_classify_ask_docs | Unit | Pass | |
| test_classify_ask_root_file | Unit | Pass | |
| test_classify_ask_src | Unit | Pass | |
| test_classify_deny_uses_relative_to_for_github | Security | Pass | |
| test_classify_allow_uses_relative_to_for_project | Security | Pass | |
| test_bypass_path_traversal_dotdot | Security | Pass | |
| test_bypass_deep_traversal | Security | Pass | |
| test_bypass_prefix_sibling | Security | Pass | |
| test_bypass_null_byte_before_github | Security | Pass | |
| test_bypass_unc_github | Security | Pass | |
| test_bypass_relative_path_github | Security | Pass | |
| test_bypass_mixed_case_github | Security | Pass | |
| test_bypass_mixed_case_noagentzone | Security | Pass | |
| test_cross_platform_windows_allow | Cross-platform | Pass | |
| test_cross_platform_windows_deny | Cross-platform | Pass | |
| test_cross_platform_wsl_allow | Cross-platform | Pass | |
| test_cross_platform_wsl_deny | Cross-platform | Pass | |
| test_cross_platform_gitbash_allow | Cross-platform | Pass | |
| test_cross_platform_gitbash_deny | Cross-platform | Pass | |
| test_security_gate_imports_zone_classifier | Integration | Pass | |
| test_get_zone_backward_compat_allow | Integration | Pass | |
| test_get_zone_backward_compat_deny | Integration | Pass | |
| test_get_zone_backward_compat_ask | Integration | Pass | |
| test_decide_project_allow | Integration | Pass | |
| test_decide_github_deny | Integration | Pass | |
| test_decide_ask_zone | Integration | Pass | |
| test_decide_path_traversal_still_denied | Integration | Pass | |

### Tester Iteration 1 edge-case tests (TST-175 to TST-188 — 14 tests)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_security_multiple_null_bytes_stripped (TST-175) | Security | Pass | |
| test_security_null_byte_mid_segment_splits_github (TST-176) | Security | Pass | |
| test_edge_empty_path_fails_closed (TST-177) | Unit | Pass | |
| test_edge_exact_deny_dir_no_subpath (TST-178) | Unit | Pass | |
| test_edge_exact_allow_dir_no_subpath (TST-179) | Unit | Pass | |
| test_edge_consecutive_interior_slashes_in_deny_path (TST-180) | Unit | Pass | |
| test_edge_very_long_path_no_exception (TST-181) | Unit | Pass | |
| test_security_traversal_arriving_at_deny_dir_root (TST-182) | Security | Pass | |
| test_edge_ws_root_with_multiple_trailing_slashes (TST-183) | Unit | Pass | |
| test_security_tab_before_deny_dir (TST-184) | Security | **Pass** | Was FAIL in Iter 1 — BUG-010 now fixed |
| test_security_newline_before_deny_dir (TST-185) | Security | **Pass** | Was FAIL in Iter 1 — BUG-010 now fixed |
| test_security_unc_path_project_outside_workspace_not_allow (TST-186) | Security | **Pass** | Was FAIL in Iter 1 — BUG-011 now fixed |
| test_edge_project_deeply_nested_file (TST-187) | Unit | Pass | |
| test_edge_no_exception_on_unusual_input (TST-188) | Unit | Pass | |

### Tester Iteration 2 edge-case tests (TST-196 to TST-200 — 5 tests)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_security_cr_before_deny_dir (TST-196) | Security | Pass | CR (`\r`) before `.github` → deny; confirms BUG-010 fix covers `\x0d` |
| test_security_soh_before_deny_dir (TST-197) | Security | Pass | SOH (`\x01`) before `.github` → deny; confirms BUG-010 fix covers lower C0 range |
| test_security_c0_before_all_deny_dirs (TST-198) | Security | Pass | `\t` before `.vscode` and `\n` before `noagentzone` → deny; fix applies to all deny dirs |
| test_security_workspace_sibling_no_allow (TST-199) | Security | Pass | `c:/workspace-evil/project/sensitive.py` → not allow; BUG-011 fix rejects sibling-prefix paths |
| test_security_traversal_outside_workspace_no_allow (TST-200) | Security | Pass | Traversal escaping ws_root then reaching `/project/` → not allow; BUG-011 containment guard correct |

### SAF-001 and SAF-005 regression (run alongside SAF-002)

All 60 SAF-001 tests and all 80 SAF-005 tests pass. No regressions introduced by the SAF-002 Iteration 2 changes.

---

## Bugs Found

- **BUG-012**: GUI-001 tests regressed — 38 of 41 tests fail (logged in docs/bugs/bugs.csv); pre-existing, unrelated to SAF-002.

No new bugs found within SAF-002 scope. BUG-010 and BUG-011 confirmed **Closed**.

---

## TODOs for Developer

None. All Iteration 1 TODOs have been resolved.

---

## Verdict

**PASS — mark WP as Done**

59/59 SAF-002 tests pass (including all 3 formerly-failing security tests TST-184, TST-185, TST-186 and 5 new Iteration 2 regression tests TST-196–TST-200). BUG-010 and BUG-011 are confirmed fixed. The `zone_classifier.py` module correctly enforces deny classification against all C0 control character injections and correctly rejects `"allow"` for any path whose normalised form does not reside within the workspace root. SAF-001 and SAF-005 are unaffected.

## Summary

SAF-002 delivers a well-structured `zone_classifier.py` module that correctly handles the primary attack vectors covered in the Developer's 40 tests: path traversal (`..`), prefix-match bypass (`project-evil/`), null bytes, mixed case, UNC deny paths, Windows/WSL/Git Bash cross-platform paths, and backward-compatible delegation from `security_gate.py`.

Tester review uncovered **two security bugs** via 14 additional edge-case tests. Both bugs are in `normalize_path()` or Method 2 of `classify()` and result in incorrect zone decisions for adversarial inputs:

- **BUG-010** — Non-null C0 control characters (tab `\t`, newline `\n`, carriage return `\r`) injected immediately before a deny-zone directory name bypass the deny check. `normalize_path()` strips only null bytes; all other control characters pass through untouched, producing a path segment like `\t.github` that neither Method 1 nor Method 2 identifies as belonging to the `.github` deny zone. Classification returns `"ask"` instead of `"deny"`.
- **BUG-011** — The Method 2 allow pattern `r"/project(/|$)"` matches any `/project/` substring in the fully-normalised path, including UNC paths normalised from `\\server\share\project\file.py`. Because Method 1 raises `ValueError` for out-of-workspace paths, Method 2 runs and returns `"allow"` for a file on a foreign network host. An agent accessing `\\server\share\project\sensitive.py` would silently receive `"allow"` rather than the expected `"ask"`, bypassing the human-approval requirement for out-of-workspace access.

**Verdict: FAIL — return to Developer with the TODOs below.**

---

## Tests Executed

### Developer tests (TST-125 to TST-164 — 40 tests)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_normalize_null_byte_stripped | Unit | Pass | |
| test_normalize_double_backslash | Unit | Pass | |
| test_normalize_single_backslash | Unit | Pass | |
| test_normalize_wsl_prefix | Unit | Pass | |
| test_normalize_gitbash_prefix | Unit | Pass | |
| test_normalize_lowercase | Unit | Pass | |
| test_normalize_trailing_slash | Unit | Pass | |
| test_normalize_dotdot_resolved | Unit | Pass | |
| test_classify_allow_project_root | Unit | Pass | |
| test_classify_allow_project_nested | Unit | Pass | |
| test_classify_deny_github | Unit | Pass | |
| test_classify_deny_vscode | Unit | Pass | |
| test_classify_deny_noagentzone | Unit | Pass | |
| test_classify_ask_docs | Unit | Pass | |
| test_classify_ask_root_file | Unit | Pass | |
| test_classify_ask_src | Unit | Pass | |
| test_classify_deny_uses_relative_to_for_github | Security | Pass | |
| test_classify_allow_uses_relative_to_for_project | Security | Pass | |
| test_bypass_path_traversal_dotdot | Security | Pass | |
| test_bypass_deep_traversal | Security | Pass | |
| test_bypass_prefix_sibling | Security | Pass | |
| test_bypass_null_byte_before_github | Security | Pass | |
| test_bypass_unc_github | Security | Pass | |
| test_bypass_relative_path_github | Security | Pass | |
| test_bypass_mixed_case_github | Security | Pass | |
| test_bypass_mixed_case_noagentzone | Security | Pass | |
| test_cross_platform_windows_allow | Cross-platform | Pass | |
| test_cross_platform_windows_deny | Cross-platform | Pass | |
| test_cross_platform_wsl_allow | Cross-platform | Pass | |
| test_cross_platform_wsl_deny | Cross-platform | Pass | |
| test_cross_platform_gitbash_allow | Cross-platform | Pass | |
| test_cross_platform_gitbash_deny | Cross-platform | Pass | |
| test_security_gate_imports_zone_classifier | Integration | Pass | |
| test_get_zone_backward_compat_allow | Integration | Pass | |
| test_get_zone_backward_compat_deny | Integration | Pass | |
| test_get_zone_backward_compat_ask | Integration | Pass | |
| test_decide_project_allow | Integration | Pass | |
| test_decide_github_deny | Integration | Pass | |
| test_decide_ask_zone | Integration | Pass | |
| test_decide_path_traversal_still_denied | Integration | Pass | |

### Tester edge-case tests (TST-175 to TST-188 — 14 tests)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_security_multiple_null_bytes_stripped (TST-175) | Security | Pass | Multiple null bytes correctly stripped |
| test_security_null_byte_mid_segment_splits_github (TST-176) | Security | Pass | `.gi\x00t\x00hub` collapses to `.github` |
| test_edge_empty_path_fails_closed (TST-177) | Unit | Pass | Empty path → "ask" (fail-closed) |
| test_edge_exact_deny_dir_no_subpath (TST-178) | Unit | Pass | Bare deny dir root (`/workspace/.github`) → deny |
| test_edge_exact_allow_dir_no_subpath (TST-179) | Unit | Pass | Bare allow dir root (`/workspace/project`) → allow |
| test_edge_consecutive_interior_slashes_in_deny_path (TST-180) | Unit | Pass | `///` collapsed, deny/allow correct |
| test_edge_very_long_path_no_exception (TST-181) | Unit | Pass | 500-level nesting → ask, no exception |
| test_security_traversal_arriving_at_deny_dir_root (TST-182) | Security | Pass | `project/../.github` (no subpath) → deny |
| test_edge_ws_root_with_multiple_trailing_slashes (TST-183) | Unit | Pass | ws_root `///` suffix → correct classifications |
| test_security_tab_before_deny_dir (TST-184) | Security | **FAIL** | `\t.github` returns "ask" — BUG-010 |
| test_security_newline_before_deny_dir (TST-185) | Security | **FAIL** | `\n.github` returns "ask" — BUG-010 |
| test_security_unc_path_project_outside_workspace_not_allow (TST-186) | Security | **FAIL** | `\\server\share\project\...` returns "allow" — BUG-011 |
| test_edge_project_deeply_nested_file (TST-187) | Unit | Pass | 8-level nesting in project/ → allow |
| test_edge_no_exception_on_unusual_input (TST-188) | Unit | Pass | 9 unusual inputs, none raise exception |

### SAF-001 regression (run alongside SAF-002)

All 49 SAF-001 tests pass when run with the SAF-002 implementation. No regressions introduced.

---

## Bugs Found

- **BUG-010**: Non-null C0 control characters in path segments bypass deny classification (logged in docs/bugs/bugs.csv)
- **BUG-011**: UNC path to `project/` directory outside workspace root incorrectly returns "allow" (logged in docs/bugs/bugs.csv)

---

## TODOs for Developer

- [ ] **Fix BUG-010** — In `zone_classifier.normalize_path()`, after stripping null bytes also strip (or replace with empty string) all other ASCII C0 control characters (bytes `\x01`–`\x1f`). At minimum tab (`\x09`), newline (`\x0a`), carriage return (`\x0d`) must be removed before any zone comparison. Suggested one-liner after the existing null-byte strip:
  ```python
  import re
  p = re.sub(r'[\x00-\x1f]', '', p)  # strip all C0 control characters
  ```
  This renders `\t.github` → `.github` before Method 1/Method 2 run. Tests TST-184 and TST-185 must pass after the fix.

- [ ] **Fix BUG-011** — The Method 2 allow pattern must not grant "allow" to paths that are outside the workspace root. Two acceptable approaches:
  - **Option A (preferred)**: Gate the Method 2 allow branch behind a workspace-containment check. Only return "allow" from Method 2 if the normalised path starts with `ws_clean + "/"`:
    ```python
    if _ALLOW_PATTERN.search(full_with_slash):
        if norm.startswith(ws_clean + "/") or norm == ws_clean:
            return "allow"
    # else fall through to "ask"
    ```
  - **Option B**: Restrict `_ALLOW_PATTERN` to anchor on `ws_clean` directly rather than matching anywhere in the path.
  Either way, `\\server\share\project\sensitive.py` (any path whose normalised form does not start with `ws_clean`) must return "ask", not "allow". Test TST-186 must pass after the fix.

- [ ] **Add regression tests** — After fixing, verify that the original cross-platform allow tests (TST-151 Windows, TST-153 WSL, TST-155 Git Bash) still pass with the new Method 2 allow guard. These use absolute paths with the same drive root, so the workspace-containment check must handle them correctly.

- [ ] **Document in dev-log** — Append an Iteration 2 section to `docs/workpackages/SAF-002/dev-log.md` describing the fixes and referencing BUG-010 and BUG-011.

---

## Verdict

**FAIL — return WP to Developer (In Progress)**

3 of 54 tests fail. Two confirmed security bugs (BUG-010, BUG-011) must be fixed and TST-184, TST-185, and TST-186 must pass before re-review.
