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
