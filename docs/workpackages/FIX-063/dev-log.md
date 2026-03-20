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
