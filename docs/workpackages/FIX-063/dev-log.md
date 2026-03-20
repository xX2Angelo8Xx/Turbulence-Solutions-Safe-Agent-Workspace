# Dev Log — FIX-063

**WP:** FIX-063 — Move _internal/ to Contents/Resources/ with symlink for codesign
**Developer:** Developer Agent
**Branch:** FIX-063/relocate-internal-to-resources
**Date Started:** 2026-03-20

---

## Objective

Restructure `src/installer/macos/build_dmg.sh` so that `_internal/` lives at
`Contents/Resources/_internal/` instead of `Contents/MacOS/_internal/`. Place a
symlink `Contents/MacOS/_internal` → `../Resources/_internal`. This ensures
`Contents/MacOS/` only contains the launcher executable — macOS codesign does
not traverse symlinks, so no non-code file in `_internal/` can trigger
"code object is not signed at all".

Supersedes FIX-062 (which only relocated TS-Logo.png/ico — whack-a-mole).

---

## Implementation

### Files Changed

- `src/installer/macos/build_dmg.sh`

### Changes Made

1. **Step 2.1 (new):** After the `cp -R` that copies PyInstaller output into
   `Contents/MacOS/`, add `mv` + `ln -s` to relocate `_internal/` to
   `Contents/Resources/` and symlink back from `Contents/MacOS/`.

2. **Step 3.1:** Updated `find` path from `Contents/MacOS/_internal` to
   `Contents/Resources/_internal` for `.dist-info` removal.

3. **Step 3.2:** Removed entirely — the per-file TS-Logo relocation loop is no
   longer needed since the entire `_internal/` directory now lives in
   `Contents/Resources/`.

4. **Step 3.5:** Updated all `find` commands and paths:
   - `.dylib` signing: `Contents/MacOS/_internal` → `Contents/Resources/_internal`
   - `.so` signing: `Contents/MacOS/_internal` → `Contents/Resources/_internal`
   - `Python.framework` signing path: `Contents/MacOS/_internal` → `Contents/Resources/_internal`
   - `Python.framework` verification path: `Contents/MacOS/_internal` → `Contents/Resources/_internal`

### Why This Works

- `Contents/MacOS/` only contains `launcher` (executable) and `_internal` (symlink).
- macOS codesign does NOT traverse symlinks — they are recorded as symlinks in
  CodeResources.
- No non-code file can be encountered as a code subcomponent.
- At runtime, `launcher` accesses `_internal/` via the symlink transparently.
- Individually signed `.so`/`.dylib` files retain their signatures regardless of location.

---

## Tests Written

All tests in `tests/FIX-063/test_fix063_internal_relocation.py`:

| Test | Category | Description |
|------|----------|-------------|
| `test_script_exists` | Regression | build_dmg.sh is present |
| `test_no_crlf_line_endings` | Regression | LF line endings throughout file |
| `test_step21_mv_command` | Regression | mv _internal MacOS/ → Resources/ |
| `test_step21_symlink_command` | Regression | ln -s creates symlink in MacOS/ |
| `test_step21_symlink_target` | Regression | symlink target is ../Resources/_internal |
| `test_step31_uses_resources_path` | Regression | .dist-info removal targets Resources/_internal |
| `test_step31_no_macos_path` | Regression | .dist-info removal does NOT reference MacOS/_internal |
| `test_step32_removed` | Regression | FIX-062 per-file loop block is gone |
| `test_step32_ts_logo_loop_gone` | Regression | No for-loop over TS-Logo files |
| `test_step35_dylib_signs_resources` | Regression | .dylib signing targets Resources/_internal |
| `test_step35_so_signs_resources` | Regression | .so signing targets Resources/_internal |
| `test_step35_framework_condition_resources` | Regression | Python.framework check uses Resources/ path |
| `test_step35_framework_sign_resources` | Regression | Python.framework signing uses Resources/ path |
| `test_verify_framework_resources` | Regression | Python.framework verification uses Resources/ path |
| `test_no_signing_path_macos_internal` | Regression | No signing/verify step references MacOS/_internal |
| `test_symlink_relative_not_absolute` | Regression | Symlink path is relative (no leading /) |

---

## Iteration 1

Implementation complete. All 16 tests pass.

---

## Iteration 2 — Fixing FIX-062 Test Compatibility

**Date:** 2026-03-20
**Trigger:** Tester returned WP with 16 FIX-062 tests failing after FIX-063 removed Step 3.2.

### Problem

`tests/FIX-062/test_fix062_resource_relocation.py` contained 16 tests asserting that
Step 3.2 (and related constructs) *exist* in `build_dmg.sh`.  FIX-063 removed Step 3.2
entirely, causing these tests to fail.

### Changes Made

**File:** `tests/FIX-062/test_fix062_resource_relocation.py`

All 16 affected tests were updated to reflect the new post-FIX-063 reality:

| Original test | Action taken |
|---|---|
| `test_step_32_header_present` | Renamed → `test_step_32_header_absent`, assertion flipped |
| `test_step_32_moves_png` | Renamed → `test_step_32_moves_png_absent`, assertions flipped |
| `test_step_32_moves_ico` | Renamed → `test_step_32_moves_ico_absent`, assertion flipped |
| `test_step_32_symlink_relative_path` | Renamed → `test_step21_symlink_relative_path`; verifies `../../` absent and `../Resources/_internal` present |
| `test_step_32_symlink_points_to_png` | Renamed → `test_step_32_symlink_points_to_png_absent`, assertion flipped |
| `test_step_32_loop_over_files` | Renamed → `test_step_32_loop_over_files_absent`, assertion flipped |
| `test_step_32_guarded_by_file_check` | Renamed → `test_step_32_file_guard_absent`, assertion flipped |
| `test_step_ordering_31_before_32_before_35` | Renamed → `test_step_ordering_31_before_35`; asserts Step 3.2 absent, Step 3.1 before Step 3.5 |
| `_extract_step32_block` helper | Replaced with `_extract_step21_block` (extracts Step 2.1 region) |
| `test_for_loop_has_done` | Renamed → `test_for_loop_absent`, asserts loop is gone |
| `test_if_block_has_fi` | Renamed → `test_ts_logo_if_guard_absent`, asserts guard is gone |
| `test_step_32_uses_app_bundle_variable` | Renamed → `test_step21_uses_app_bundle_variable`; uses new helper |
| `test_echo_diagnostic_message_in_step_32` | Renamed → `test_echo_diagnostic_message_in_step21`; uses new helper |
| `test_symlink_depth_exactly_two_levels` | Renamed → `test_symlink_depth_exactly_one_level`; verifies 1 `..` not 2 |
| `test_loop_guard_prevents_abort_on_single_missing_file` | Renamed → `test_ts_logo_loop_and_guard_absent`, both absent |
| `test_loop_handles_neither_file_present` | Renamed → `test_ts_logo_references_entirely_absent` |
| `test_no_crlf_in_step32_block` | Renamed → `test_step32_absent_in_raw_bytes`; verifies b"Step 3.2" not in raw bytes |

Module docstring also updated to reflect the new purpose of these tests.

### Test Results

- `tests/FIX-062/` — 22/22 PASS
- `tests/FIX-063/` — 28/28 PASS
- Combined: **50/50 PASS** (TST-1963)
- Full suite: 4136 pass, 88 pre-existing failures (unchanged)
