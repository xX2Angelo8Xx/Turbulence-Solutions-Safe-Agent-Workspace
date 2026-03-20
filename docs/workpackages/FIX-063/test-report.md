# Test Report — FIX-063

**Tester:** Tester Agent
**Date:** 2026-03-20
**Iteration:** 2
**Verdict:** ✅ PASS

---

## Summary

**Iteration 2 resolves the only blocker from Iteration 1.** The developer updated `tests/FIX-062/test_fix062_resource_relocation.py` — flipping 16 presence assertions to absence assertions plus related refactors. All 22 FIX-062 tests now pass. All 28 FIX-063 tests continue to pass. Full suite shows 88 pre-existing failures (unchanged from baseline) and zero new regressions.

FIX-063 restructures the `.app` bundle by moving the entire `_internal/` directory from `Contents/MacOS/` to `Contents/Resources/` and placing a relative symlink at `Contents/MacOS/_internal → ../Resources/_internal`. This correctly resolves the root cause of BUG-089 (codesign encountering non-code files as subcomponents).

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

| Run | TST-ID | Tests | Pass | Fail | Status |
|-----|--------|-------|------|------|--------|
| FIX-063 developer suite (Iteration 1) | TST-1960 | 16 | 16 | 0 | ✅ PASS |
| FIX-063 tester edge-cases (Iteration 1) | TST-1961 | 12 | 12 | 0 | ✅ PASS |
| FIX-062 regression check (Iteration 1) | TST-1962 | 22 | 6 | **16** | ❌ FAIL |
| FIX-062 regression (Iteration 2) | TST-1964 | 22 | 22 | 0 | ✅ PASS |
| FIX-063 full suite (Iteration 2) | TST-1965 | 28 | 28 | 0 | ✅ PASS |
| Full suite regression check (Iteration 2) | TST-1966 | 4100+ | 4100+ | 88 pre-existing | ✅ PASS |

### FIX-063 Tests: 28/28 PASS ✅

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

### FIX-062 Tests: 22/22 PASS ✅ (Iteration 2)

Developer updated `tests/FIX-062/test_fix062_resource_relocation.py`:

| Original test (Iteration 1) | Updated test (Iteration 2) |
|-----------------------------|---------------------------|
| `test_step_32_header_present` | `test_step_32_header_absent` — asserts Step 3.2 absent |
| `test_step_32_moves_png` | `test_step_32_moves_png_absent` — asserts TS-Logo.png absent |
| `test_step_32_moves_ico` | `test_step_32_moves_ico_absent` — asserts TS-Logo.ico absent |
| `test_step_32_symlink_relative_path` | `test_step21_symlink_relative_path` — asserts `../../` absent, `../Resources/_internal` present |
| `test_step_32_symlink_points_to_png` | `test_step_32_symlink_points_to_png_absent` — asserts per-file symlink absent |
| `test_step_32_loop_over_files` | `test_step_32_loop_over_files_absent` — asserts for-loop absent |
| `test_step_32_guarded_by_file_check` | `test_step_32_file_guard_absent` — asserts `[ -f ]` guard absent |
| `test_step_ordering_31_before_32_before_35` | `test_step_ordering_31_before_35` — Step 3.2 absent, 3.1 before 3.5 |
| `_extract_step32_block` helper | `_extract_step21_block` helper — extracts Step 2.1 region |
| `test_for_loop_has_done` | `test_for_loop_absent` — asserts loop gone |
| `test_if_block_has_fi` | `test_ts_logo_if_guard_absent` — asserts if-guard gone |
| `test_step_32_uses_app_bundle_variable` | `test_step21_uses_app_bundle_variable` — checks Step 2.1 block |
| `test_echo_diagnostic_message_in_step_32` | `test_echo_diagnostic_message_in_step21` — checks Step 2.1 block |
| `test_symlink_depth_exactly_two_levels` | `test_symlink_depth_exactly_one_level` — asserts 1 `..` not 2 |
| `test_loop_guard_prevents_abort_on_single_missing_file` | `test_ts_logo_loop_and_guard_absent` — both absent |
| `test_no_crlf_in_step32_block` | `test_step32_absent_in_raw_bytes` — raw bytes check |

### Pre-existing Failures (not caused by FIX-063)

88 tests fail that are unrelated to FIX-063. Confirmed pre-existing by running FIX-028 and FIX-031 tests against the main-branch script (same failures). Root cause: multi-line `\`-continuation commands prevent single-line pattern matching. FIX-028/FIX-031, FIX-009, FIX-015, FIX-016, FIX-019, SAF-022, SAF-025, and others all fail for reasons pre-dating this WP.

---

## Edge Case Analysis

| Edge Case | Analysis |
|-----------|----------|
| `_internal/` missing after PyInstaller | `set -euo pipefail` is active — `mv` failure aborts the build cleanly. No extra guard needed. |
| Symlink path correctness | `../Resources/_internal` from `Contents/MacOS/` → `Contents/Resources/_internal` ✓ Exactly 1 `..` verified. |
| `mv` handles nested directories | `mv dir1 dir2` moves entire directory trees on macOS. No issue. |
| Step 3.2 completely gone | Confirmed: "Step 3.2", "TS-Logo.png", "TS-Logo.ico", `for f in TS-Logo.png TS-Logo.ico` all absent. |
| FIX-062 tests updated correctly | ✅ All 16 assertions flipped; all 22 tests pass. |
| Line endings | LF throughout — confirmed. |
| No `MacOS/_internal` outside mv+ln-s | ✅ `test_no_macos_internal_outside_relocation` passes. |
| `test_symlink_depth_exactly_one_level` correctness | Old FIX-062 symlinks were inside `_internal/` (2 `..` to reach `Contents/`). FIX-063 symlink is at `MacOS/` level (1 `..` correct). Test logic verified. |

---

## Bugs Found

None new in Iteration 2. BUG-090 (filed in Iteration 1) resolved by Developer in Iteration 2.

---
