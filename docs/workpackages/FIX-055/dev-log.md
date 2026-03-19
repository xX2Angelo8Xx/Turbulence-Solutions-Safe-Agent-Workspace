# FIX-055 Dev Log — Fix Inno Setup PythonEmbedExists runtime check

## Status
In Progress → Review

## Root Cause
`setup.iss` used `Check: PythonEmbedExists` on the python-embed [Files] entry. This Check function runs at **install time** on the user's machine, where `{src}` resolves to the download/temp directory — not the source tree where `python-embed\` lives. The function always returns False on user machines, so python-embed is **never installed**, breaking the bundled Python shim system (BUG-077, BUG-081).

Additionally, `{autopf}` without `ArchitecturesInstallIn64BitMode=x64compatible` resolves to `C:\Program Files (x86)\` on 64-bit Windows for 32-bit-aware installers, causing the wrong install path.

## Changes Made

### `src/installer/windows/setup.iss`
1. **[Setup] section**: Added `ArchitecturesInstallIn64BitMode=x64compatible` and `ArchitecturesAllowed=x64compatible` after `PrivilegesRequired=admin` — ensures `{autopf}` resolves to `C:\Program Files\` on 64-bit and ARM64 Windows.
2. **[Files] python-embed entry**: Removed `Check: PythonEmbedExists` (runtime check that always fails on user machines). Added `skipifsourcedoesntexist` flag — this is a compile-time flag that allows dev builds (where `python-embed\` is absent) to compile without error, while CI builds (where the directory is present) always extract the files.
3. **[Code] section**: Removed the now-unused `PythonEmbedExists()` Pascal function entirely.
4. **Comments**: Updated comments to explain the `skipifsourcedoesntexist` approach.

## Tests Written
`tests/FIX-055/test_fix055.py` — 8 tests verifying:
1. `skipifsourcedoesntexist` present in the python-embed [Files] Flags
2. `Check:` parameter absent from python-embed [Files] entry
3. `PythonEmbedExists` function absent from [Code] section
4. `ArchitecturesInstallIn64BitMode=x64compatible` in [Setup]
5. `ArchitecturesAllowed=x64compatible` in [Setup]
6. `CurStepChanged` function still present (writes python-path.txt)
7. Source path `..\python-embed\*` still present
8. DestDir `{app}\python-embed` still present

## Test Results
All 8 tests pass.

## Files Changed
- `src/installer/windows/setup.iss`
- `docs/workpackages/workpackages.csv`
- `docs/workpackages/FIX-055/dev-log.md` (this file)
- `tests/FIX-055/__init__.py`
- `tests/FIX-055/test_fix055.py`
- `docs/test-results/test-results.csv`

---

## Iteration 2 — Fix Regression Tests

**Date:** 2026-03-19

### Issue
Tester found 6 test regressions in pre-existing test suites (FIX-012 ×2, INS-005 ×1, INS-018 ×2, INS-021 ×1). These tests encoded old behavior that FIX-055 intentionally changed.

### Changes Made

#### `tests/FIX-012/test_fix012_ci_build_fixes.py`
- Renamed `test_architectures_allowed_absent` → `test_architectures_allowed_present`
- Updated assertion: `ArchitecturesAllowed=x64compatible` **must be present** (FIX-055 re-introduced it with correct key name now that CI Inno Setup is up-to-date)
- Added comment documenting the BUG-041 history

#### `tests/FIX-012/test_fix012_edge_cases.py`
- Renamed `test_architectures_allowed_absent_case_insensitive` → `test_architectures_allowed_present_case_insensitive`
- Updated assertion: `architecturesallowed` **must appear** (case-insensitive)
- Added comment explaining FIX-055 rationale

#### `tests/INS-005/test_ins005_edge_cases.py`
- Renamed `test_architecture_directives_not_present` → `test_architecture_directives_present`
- Updated to assert `ArchitecturesAllowed=x64compatible` AND `ArchitecturesInstallIn64BitMode=x64compatible` are present
- Also asserts the obsolete `ArchitecturesInstallMode` key remains absent

#### `tests/INS-018/test_ins018_bundle_python_embed.py`
- Replaced `test_setup_iss_python_embed_check_function` with `test_setup_iss_python_embed_skipifsourcedoesntexist` — asserts `skipifsourcedoesntexist` flag is present
- Replaced `test_setup_iss_python_embed_exists_uses_file_exists` with `test_setup_iss_python_embed_no_check_parameter` — asserts `Check:` is absent from the python-embed [Files] line

#### `tests/INS-021/test_ins021_setup_iss.py`
- Replaced `test_python_embed_exists_function_preserved` with `test_python_embed_exists_function_removed` — asserts `function PythonEmbedExists` is absent AND `skipifsourcedoesntexist` is present

### Test Results (Iteration 2)
- Targeted: 169 passed, 0 failed (FIX-055 + FIX-012 + INS-005 + INS-018 + INS-021)
- Full regression: 3961 passed, 55 failed (all pre-existing), 3 skipped
- Pre-existing failure count matches Tester's baseline (55). 6 regressions resolved.

### Files Changed
- `tests/FIX-012/test_fix012_ci_build_fixes.py`
- `tests/FIX-012/test_fix012_edge_cases.py`
- `tests/INS-005/test_ins005_edge_cases.py`
- `tests/INS-018/test_ins018_bundle_python_embed.py`
- `tests/INS-021/test_ins021_setup_iss.py`
- `docs/workpackages/FIX-055/dev-log.md` (this file)
- `docs/test-results/test-results.csv`
