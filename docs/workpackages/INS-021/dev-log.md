# Dev Log — INS-021: Update Inno Setup for shim installation and PATH

**Status:** In Progress  
**Branch:** `INS-021/update-inno-setup-shim-and-path`  
**Date Started:** 2026-03-19  
**Developer:** Developer Agent  
**User Story:** US-032

---

## Objective

Update `src/installer/windows/setup.iss` so the Windows installer:
1. Deploys `ts-python.cmd` shim to `%LOCALAPPDATA%\TurbulenceSolutions\bin\`
2. Writes `%LOCALAPPDATA%\TurbulenceSolutions\python-path.txt` with `{app}\python-embed\python.exe`
3. Adds `%LOCALAPPDATA%\TurbulenceSolutions\bin` to the user's PATH (HKCU registry)
4. Removes the shim directory and PATH entry on uninstall
5. Rewrites `python-path.txt` on reinstall/update with the new install path

---

## Implementation

### `src/installer/windows/setup.iss` changes

**[Files] section — new entry:**
- Source: `..\..\installer\shims\ts-python.cmd` → DestDir: `{localappdata}\TurbulenceSolutions\bin`
- Flags: `ignoreversion` (overwrites on reinstall/update)

**[Registry] section — new section:**
- `HKCU\Environment\Path` extended via `{olddata};{localappdata}\TurbulenceSolutions\bin`
- Guarded by `NeedsAddPath()` to prevent duplicate entries on reinstall

**[UninstallDelete] section — new entry:**
- Removes `{localappdata}\TurbulenceSolutions` (entire config directory) on uninstall

**[Code] section — new Pascal functions/procedures:**
- `NeedsAddPath(PathToAdd: String): Boolean` — case-insensitive check whether the bin dir is already in HKCU PATH; returns True only if it needs to be added
- `CurStepChanged(CurStep: TSetupStep)` — on `ssPostInstall`, writes `python-path.txt` with `{app}\python-embed\python.exe` using `SaveStringToFile` with `Append=False` (overwrites on reinstall)
- `CurUninstallStepChanged(CurUninstallStep: TUninstallStep)` — on `usPostUninstall`, reads HKCU PATH, removes the bin dir entry (case-insensitive), and writes back via `RegWriteExpandStringValue`

### Design Decisions
- Using `{olddata}` in `[Registry]` ValueData is idiomatic Inno Setup; the old PATH value is preserved and the new entry is appended.
- `NeedsAddPath` wraps both the current PATH and the target with semicolons for reliable substring match.
- Uninstall PATH cleanup is done in `CurUninstallStepChanged(usPostUninstall)` rather than relying on Inno Setup's automatic registry restore (which would blindly restore the old value and could strip other PATH entries added after install).
- `[UninstallDelete]` removes the full `{localappdata}\TurbulenceSolutions` tree, cleaning up both the shim (bin\ts-python.cmd) and the config file (python-path.txt).

---

## Files Changed

| File | Change |
|------|--------|
| `src/installer/windows/setup.iss` | Added [Registry] section, ts-python.cmd [Files] entry, NeedsAddPath function, CurStepChanged procedure, CurUninstallStepChanged procedure, UninstallDelete entry |
| `docs/workpackages/workpackages.csv` | INS-021 status → In Progress |

---

## Tests Written

| Test File | Description |
|-----------|-------------|
| `tests/INS-021/test_ins021_setup_iss.py` | Validates all INS-021 changes are present in setup.iss |

Tests verify:
- `ts-python.cmd` files entry with correct DestDir
- `[Registry]` section exists with correct HKCU/Environment/Path entry
- `NeedsAddPath` function defined and referenced
- `CurStepChanged` procedure with `ssPostInstall`, `python-path.txt`, `SaveStringToFile`
- `SaveStringToFile` uses `Append=False` (overwrite on reinstall)
- `CurUninstallStepChanged` procedure with `usPostUninstall` and `RegWriteExpandStringValue`
- `[UninstallDelete]` entry for `{localappdata}\TurbulenceSolutions`
- INS-018 `PythonEmbedExists` function preserved
- `{olddata}` used in registry entry

---

## Test Results

**INS-021 suite:** 26/26 passed  
**Related suites (INS-018, INS-019, INS-020):** 152/152 passed  
**Logged in:** `docs/test-results/test-results.csv` (TST-1854)

---

## Iteration 1 — Implementation Complete

All planned changes applied to `setup.iss`. Tests written and passing.
