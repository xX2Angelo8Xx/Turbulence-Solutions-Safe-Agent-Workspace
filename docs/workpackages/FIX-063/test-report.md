# Test Report — FIX-063

**Tester:** Tester Agent
**Date:** 2026-03-20
**Iteration:** 1
**Verdict:** ❌ FAIL — Return to Developer

---

## Summary

FIX-063 restructures the `.app` bundle by moving the entire `_internal/` directory from `Contents/MacOS/` to `Contents/Resources/` and placing a relative symlink at `Contents/MacOS/_internal → ../Resources/_internal`. This correctly resolves the root cause of BUG-089 (codesign encountering non-code files as subcomponents).

The `build_dmg.sh` implementation is **architecturally correct and complete**. All 28 FIX-063 tests pass (16 developer + 12 tester edge-cases). However, the developer **removed Step 3.2 without updating `tests/FIX-062/test_fix062_resource_relocation.py`**, causing **16 pre-existing FIX-062 tests to regress**. The tester policy prohibits approving work that fails any existing test.

---

## Code Review: `src/installer/macos/build_dmg.sh`

| Check | Result |
|-------|--------|
| Step 2.1 `mv` placed AFTER `cp -R` (bundle must exist first) | ✅ Correct |
| Step 2.1 `mv` placed BEFORE Step 3.1 dist-info removal | ✅ Correct |
| Step 2.1 `mv` placed BEFORE Step 3.5 signing | ✅ Correct |
| `mkdir -p Contents/Resources` precedes `mv _internal` | ✅ Correct (Step 2) |
| `mv "${APP_BUNDLE}/Contents/MacOS/_internal" "${APP_BUNDLE}/Contents/Resources/_internal"` | ✅ Present |
| `ln -s "../Resources/_internal" "${APP_BUNDLE}/Contents/MacOS/_internal"` | ✅ Present |
| Symlink target is relative (no leading `/`) | ✅ Verified |
| Symlink depth: exactly 1 `..` segment (correct from Contents/MacOS/) | ✅ Correct |
| Step 3.1 `.dist-info` removal uses `Contents/Resources/_internal` | ✅ Correct |
| Step 3.1 does NOT reference `Contents/MacOS/_internal` | ✅ Correct |
| Step 3.2 header and loop completely removed | ✅ Removed |
| `TS-Logo.png` / `TS-Logo.ico` not referenced anywhere in script | ✅ Correct |
| Step 3.5 `.dylib` signing uses `Contents/Resources/_internal` | ✅ Correct |
| Step 3.5 `.so` signing uses `Contents/Resources/_internal` | ✅ Correct |
| Python.framework existence check uses `Contents/Resources/_internal` | ✅ Correct |
| Python.framework signing uses `Contents/Resources/_internal` | ✅ Correct |
| Python.framework verification uses `Contents/Resources/_internal` | ✅ Correct |
| No signing/verify step references `Contents/MacOS/_internal` | ✅ Confirmed |
| `set -euo pipefail` still set (mv failure = build abort) | ✅ Present |
| Diagnostic echo in Step 2.1 | ✅ Present |
| LF line endings — no CRLF | ✅ Verified |

### Symlink Path Correctness

```
Contents/MacOS/_internal (symlink) → ../Resources/_internal

Resolution from Contents/MacOS/:
  ../  → Contents/
  ../Resources/_internal → Contents/Resources/_internal  ✅
```

One `..` segment is correct. (FIX-062 used two `..` segments because its per-file symlinks were created _inside_ `Contents/MacOS/_internal/`; FIX-063 creates the symlink at the `Contents/MacOS/` level.)

---

## Test Results

| Run | Tests | Pass | Fail | Status |
|-----|-------|------|------|--------|
| TST-1960: FIX-063 developer suite | 16 | 16 | 0 | ✅ PASS |
| TST-1961: FIX-063 tester edge-cases | 12 | 12 | 0 | ✅ PASS |
| TST-1962: FIX-062 regression check | 22 | 6 | **16** | ❌ FAIL |

### FIX-063 Tests: 28/28 PASS

All 16 developer tests pass. 12 additional tester edge-case tests added to `tests/FIX-063/test_fix063_edge_cases.py`, all passing:

- `test_step21_mv_after_cp_r` — mv appears after cp -R
- `test_step21_mv_before_step31` — mv before Step 3.1
- `test_step21_mv_before_step35` — mv before Step 3.5
- `test_mkdir_resources_before_mv_internal` — mkdir -p before mv
- `test_symlink_one_dotdot_from_macos_dir` — symlink target depth is exactly 1 `..`
- `test_no_macos_internal_outside_relocation` — comprehensive MacOS/_internal check
- `test_echo_in_step21_region` — diagnostic echo present
- `test_pipefail_still_active` — set -euo pipefail verified
- `test_ts_logo_png_not_referenced` — TS-Logo.png fully gone
- `test_ts_logo_ico_not_referenced` — TS-Logo.ico fully gone
- `test_python_framework_sign_guard_resources` — framework guard uses Resources
- `test_python_framework_verify_guard_resources` — verify guard uses Resources

### FIX-062 Tests: 6/22 PASS — **16 FAIL** 🔴

FIX-063 removed Step 3.2 from `build_dmg.sh` but did NOT update `tests/FIX-062/test_fix062_resource_relocation.py`. This file contains 16 tests that assert Step 3.2 is present. All 16 now fail.

Failing tests:
1. `test_step_32_header_present` — asserts "Step 3.2" in script
2. `test_step_32_moves_png` — asserts "TS-Logo.png" in script
3. `test_step_32_moves_ico` — asserts "TS-Logo.ico" in script
4. `test_step_32_symlink_relative_path` — asserts `../../Resources/` symlink pattern
5. `test_step_32_symlink_points_to_png` — asserts per-file symlink for logos
6. `test_step_32_loop_over_files` — asserts `for f in TS-Logo.png TS-Logo.ico`
7. `test_step_32_guarded_by_file_check` — asserts `[ -f .../${f} ]` guard
8. `test_step_ordering_31_before_32_before_35` — asserts Step 3.2 exists between 3.1 and 3.5
9. `test_for_loop_has_done` — Step 3.2 marker not found
10. `test_if_block_has_fi` — Step 3.2 marker not found
11. `test_step_32_uses_app_bundle_variable` — Step 3.2 marker not found
12. `test_echo_diagnostic_message_in_step_32` — Step 3.2 marker not found
13. `test_symlink_depth_exactly_two_levels` — expects 2 `..` segments; FIX-063 correctly uses 1
14. `test_loop_guard_prevents_abort_on_single_missing_file` — Step 3.2 marker not found
15. `test_loop_handles_neither_file_present` — Step 3.2 marker not found
16. `test_no_crlf_in_step32_block` — Step 3.2 marker not found

### Pre-existing Failures (not caused by FIX-063)

FIX-028 (7 tests) and FIX-031 (8 tests) have failures that were **confirmed pre-existing** by running the same test logic against the HEAD~1 script. Root cause: these tests check for multi-argument predicates (e.g., `"find" in line and "*.dylib" in line and "codesign" in line`) applied to individual lines, but the script uses multi-line `\`-continuation commands where the arguments span multiple lines. This made these assertions impossible to satisfy in both old and new versions of the script.

---

## Edge Case Analysis

| Edge Case | Analysis |
|-----------|----------|
| `_internal/` missing after PyInstaller | `set -euo pipefail` is active — `mv` failure will abort the build with a clear error. No extra guard needed. |
| Symlink path correctness | `../Resources/_internal` from `Contents/MacOS/` → `Contents/Resources/_internal` ✓ Confirmed 1 `..` correct. |
| `mv` handles nested directories | `mv dir1 dir2` works for entire directory trees on macOS. No issue. |
| FIX-062 Step 3.2 completely gone | Confirmed: "Step 3.2", "TS-Logo.png", "TS-Logo.ico", `for f in TS-Logo.png TS-Logo.ico` all absent. |
| FIX-062 tests updated | ❌ NOT DONE — 16 failures in tests/FIX-062/ |
| Line endings | LF throughout — confirmed. |
| No MacOS/_internal outside mv+ln-s | ✅ Tester test `test_no_macos_internal_outside_relocation` passes. |

---

## Bugs Found

- **BUG-090** (High): FIX-063 removes Step 3.2 but does not update `tests/FIX-062/test_fix062_resource_relocation.py` — 16 tests now fail.

---

## TODO for Developer (Iteration 2)

**Required to unblock PASS:**

### TODO-1 — Update `tests/FIX-062/test_fix062_resource_relocation.py`

FIX-063 removes Step 3.2 and supersedes FIX-062's per-file relocation. The FIX-062 test file must be updated to reflect the new reality:

1. **Replace all Step-3.2-presence assertions with Step-3.2-ABSENCE assertions.** The 16 failing tests that assert "Step 3.2" exists in the script must instead assert it does NOT exist. Example:
   ```python
   def test_step_32_header_absent():
       """FIX-063 supersedes FIX-062: Step 3.2 must NOT be present."""
       assert "Step 3.2" not in _read_script()
   ```

2. **Update `test_step_ordering_31_before_32_before_35` → remove Step 3.2 from ordering check.** The test should only check 3.1 before 3.5.

3. **Update `test_symlink_depth_exactly_two_levels` → assert 1 `..` segment** (not 2). FIX-063 creates the symlink at `Contents/MacOS/` level (1 `..` = correct), NOT inside `Contents/MacOS/_internal/` (2 `..`).

4. **Remove tests for `TS-Logo.png`, `TS-Logo.ico`, the per-file for-loop, and the `[ -f ]` guard.** These implementation details no longer exist. Replace with assertions that these patterns are ABSENT (verifying FIX-063 superseded them).

5. **Verify `test_step_32_resources_dir_pre_exists`, `test_no_absolute_symlink_path`, `test_script_exists`, `test_no_crlf_line_endings`, `test_mv_target_is_resources_dir`, `test_step_32_symlink_command_present`** still pass with updated logic (these 6 did not fail but may need logic updates after the above changes).

**The complete updated FIX-062 test suite must pass with 0 failures before FIX-063 can be marked Done.**
