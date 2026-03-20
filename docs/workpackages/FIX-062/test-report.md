# Test Report — FIX-062

**Tester:** Tester Agent
**Date:** 2026-03-20
**Iteration:** 1

## Summary

FIX-062 adds Step 3.2 to `src/installer/macos/build_dmg.sh` which relocates
`TS-Logo.png` and `TS-Logo.ico` from `Contents/MacOS/_internal/` to
`Contents/Resources/` and creates relative symlinks back so `sys._MEIPASS`
lookups continue to work at runtime.

The implementation is **correct and complete**. All 22 tests (13 Developer + 9
Tester edge-cases) pass. Zero regressions were introduced — the pre-existing
failures in the full suite are all unrelated to FIX-062.

---

## Review Findings

### Code Review: `src/installer/macos/build_dmg.sh`

| Check | Result |
|-------|--------|
| Step 3.2 placed between Step 3.1 and Step 3.5 | ✅ Correct |
| Loop covers TS-Logo.png and TS-Logo.ico | ✅ Correct |
| Per-file `[ -f ]` guard (handles missing files individually) | ✅ Correct |
| `mv` moves to `Contents/Resources/` | ✅ Correct |
| `ln -s "../../Resources/${f}"` — relative path | ✅ Correct |
| Symlink depth: exactly 2 `..` levels from `_internal/` | ✅ Correct |
| `done` closes the `for` loop | ✅ Present |
| `fi` closes the `if` block | ✅ Present |
| `${APP_BUNDLE}` used throughout (no hardcoded paths) | ✅ Correct |
| `Contents/Resources/` pre-created in Step 2 (no redundant mkdir) | ✅ Correct |
| LF line endings — no CRLF | ✅ Verified |
| `set -euo pipefail` compatible (no silent failures) | ✅ Compatible |
| Diagnostic echo message present | ✅ Present |

### Symlink Path Correctness

The relative path `../../Resources/<filename>` resolves correctly from
`Contents/MacOS/_internal/`:

```
_internal/ → .. → MacOS/ → .. → Contents/ + Resources/<file>
```

This is exactly 2 `..` segments, pointing to `Contents/Resources/<file>`. ✅

### Edge-Case Analysis

| Scenario | Handled? | How |
|----------|----------|-----|
| Only TS-Logo.png present, TS-Logo.ico absent | ✅ | `[ -f ]` guard skips missing file |
| Only TS-Logo.ico present, TS-Logo.png absent | ✅ | `[ -f ]` guard skips missing file |
| Neither file present | ✅ | Loop completes silently; no `exit`/`|| false` |
| Both files present | ✅ | Both relocated with symlinks created |
| Correct symlink depth | ✅ | Exactly 2 `..` levels verified by test |
| Absolute symlink path risk | ✅ | Test verifies no absolute paths |
| CRLF in Step 3.2 block | ✅ | Binary-level check confirms LF only |
| `for` loop syntax correctness | ✅ | `done` keyword confirmed present |
| `if` block syntax correctness | ✅ | `fi` keyword confirmed present |

### Known Limitation (not a blocker)

The fix only covers the two known resource files. If other non-code files
(e.g. `.json`, `.xml`, `.pdf`, `.ttf`) are added to the PyInstaller bundle in
the future they will need to be added to the loop's file list. This is expected
behaviour for a targeted bug-fix; a broader "relocate all non-code files by
extension" approach was not in scope for this WP.

### Regression Analysis

| Scope | Failures Before FIX-062 | Failures After FIX-062 | Delta |
|-------|------------------------|------------------------|-------|
| FIX-028 / FIX-031 / FIX-037 / FIX-038 / FIX-039 suite | 38 | 37 | -1 (improvement) |
| Full suite (excl. pre-existing yaml import errors) | Baseline | Same | 0 regressions |
| FIX-062 targeted suite | N/A | 22 passed | ✅ |

The 14 pre-existing `ModuleNotFoundError: No module named 'yaml'` collection
errors are environment issues unrelated to this WP (missing optional dependency).
They were present on `main` before FIX-062 was applied.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| `test_script_exists` | Regression | Pass | |
| `test_no_crlf_line_endings` | Regression | Pass | Full file check |
| `test_step_32_header_present` | Regression | Pass | |
| `test_step_32_moves_png` | Regression | Pass | mv pattern verified |
| `test_step_32_moves_ico` | Regression | Pass | |
| `test_step_32_symlink_command_present` | Regression | Pass | |
| `test_step_32_symlink_relative_path` | Regression | Pass | `../../Resources/` |
| `test_step_32_symlink_points_to_png` | Regression | Pass | |
| `test_step_32_loop_over_files` | Regression | Pass | Both files in loop |
| `test_step_32_guarded_by_file_check` | Regression | Pass | `[ -f ]` guard |
| `test_step_ordering_31_before_32_before_35` | Regression | Pass | |
| `test_step_32_resources_dir_pre_exists` | Regression | Pass | mkdir in Step 2 |
| `test_no_absolute_symlink_path` | Regression | Pass | |
| `test_for_loop_has_done` *(edge-case)* | Regression | Pass | Syntax correctness |
| `test_if_block_has_fi` *(edge-case)* | Regression | Pass | Syntax correctness |
| `test_step_32_uses_app_bundle_variable` *(edge-case)* | Regression | Pass | No hardcoded paths |
| `test_echo_diagnostic_message_in_step_32` *(edge-case)* | Regression | Pass | CI traceability |
| `test_symlink_depth_exactly_two_levels` *(edge-case)* | Regression | Pass | Exactly 2 `..` levels |
| `test_loop_guard_prevents_abort_on_single_missing_file` *(edge-case)* | Regression | Pass | Guard inside loop body |
| `test_loop_handles_neither_file_present` *(edge-case)* | Regression | Pass | No unconditional exit |
| `test_mv_target_is_resources_dir` *(edge-case)* | Regression | Pass | Correct mv target |
| `test_no_crlf_in_step32_block` *(edge-case)* | Regression | Pass | Binary-level LF check |
| **Full suite (Tester run)** | Regression | Logged TST-1957 | Pre-exist yaml errors (unrelated) |
| **Targeted FIX-062 suite** | Regression | Logged TST-1958 | 22 passed |

---

## Bugs Found

None. No new bugs introduced by this WP.

---

## TODOs for Developer

None.

---

## Verdict

**PASS — mark WP as Done**

The fix is correctly implemented. The `for` loop, `[ -f ]` guard, `mv` command,
`ln -s` with the correct relative path `../../Resources/${f}`, and `done`/`fi`
keywords are all present and syntactically correct. Zero regressions. 22/22
tests pass (13 Developer + 9 Tester edge-cases).
