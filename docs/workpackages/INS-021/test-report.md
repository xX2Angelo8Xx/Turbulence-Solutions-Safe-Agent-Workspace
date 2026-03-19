# Test Report — INS-021: Update Inno Setup for shim installation and PATH

**Tester:** Tester Agent  
**Date:** 2026-03-19  
**Branch:** `INS-021/update-inno-setup-shim-and-path`  
**Verdict:** ✅ PASS

---

## Scope

Reviewed `src/installer/windows/setup.iss` for all changes described in the WP:
1. `[Files]` entry deploying `ts-python.cmd` to `{localappdata}\TurbulenceSolutions\bin` with `ignoreversion`
2. `[Registry]` entry appending the bin dir to `HKCU\Environment\Path` (expandsz, `{olddata}`, guarded by `NeedsAddPath`)
3. `[Code]` — `NeedsAddPath()`: case-insensitive duplicate-entry guard with semicolon wrapping
4. `[Code]` — `CurStepChanged(ssPostInstall)`: writes `python-path.txt` via `SaveStringToFile` with `Append=False`
5. `[Code]` — `CurUninstallStepChanged(usPostUninstall)`: removes the bin dir from PATH, strips leading/trailing semicolons, writes back via `RegWriteExpandStringValue`
6. `[UninstallDelete]` entry: `filesandordirs` for `{localappdata}\TurbulenceSolutions`
7. INS-018 `PythonEmbedExists` function preserved (regression check)

---

## Code Review Findings

| Area | Finding | Status |
|------|---------|--------|
| `[Files]` shim entry | Correct source path (`installer\shims\ts-python.cmd`), correct DestDir, `ignoreversion` present | ✅ |
| `[Registry]` root | Uses `HKCU` (per-user), not `HKLM` (machine-wide) — correct for a user-level shim | ✅ |
| `[Registry]` ValueType | `expandsz` — correct for a PATH value containing `%LOCALAPPDATA%` expansion | ✅ |
| `[Registry]` Check guard | `NeedsAddPath(ExpandConstant(...))` — `ExpandConstant` correctly resolves `{localappdata}` | ✅ |
| `NeedsAddPath` | Semicolon-wraps both needle and haystack — prevents false partial matches (e.g. `\bin` vs `\bin2`) | ✅ |
| `NeedsAddPath` | Returns `True` + `Exit` when registry key is absent — safe first-install path | ✅ |
| `NeedsAddPath` | Uses `Pos()` for substring search + `Lowercase()` for case-insensitive comparison | ✅ |
| `CurStepChanged` | `DirExists(ConfigDir)` check before `CreateDir` — avoids error on reinstall | ✅ |
| `CurStepChanged` | `SaveStringToFile(ConfigFile, PythonPath, False)` — `Append=False` overwrites on reinstall/update | ✅ |
| `CurStepChanged` | `ConfigDir` expands `{localappdata}` not `{app}` — correct user-local placement | ✅ |
| `CurUninstallStepChanged` | `StartPos = 0` early-exit — safe when entry was never added or already removed | ✅ |
| `CurUninstallStepChanged` | `while NewPath[1] = ';'` + `while NewPath[Length(NewPath)] = ';'` — strips residual semicolons | ✅ |
| `CurUninstallStepChanged` | Writes back via `RegWriteExpandStringValue` — preserves expandsz type | ✅ |
| `[UninstallDelete]` | `Type: filesandordirs` for `{localappdata}\TurbulenceSolutions` — removes shim + config file | ✅ |
| INS-018 regression | `PythonEmbedExists` function still present, python-embed `[Files]` entry retained | ✅ |

No security issues found. PATH modification is user-scoped (HKCU), never machine-wide. No injection vectors in the Pascal code — all paths are hardcoded using Inno Setup constants.

---

## Tests Run

### INS-021 unit suite (Developer — 26 tests)

| Test | Result |
|------|--------|
| `test_iss_file_exists` | PASS |
| `test_shim_files_entry_source` | PASS |
| `test_shim_files_entry_dest` | PASS |
| `test_shim_source_path_references_shims_dir` | PASS |
| `test_shim_flags_ignoreversion` | PASS |
| `test_registry_section_exists` | PASS |
| `test_registry_hkcu_environment_path` | PASS |
| `test_registry_expandsz_value_type` | PASS |
| `test_registry_olddata_preserved` | PASS |
| `test_registry_needs_add_path_check` | PASS |
| `test_needs_add_path_function_defined` | PASS |
| `test_needs_add_path_queries_registry` | PASS |
| `test_needs_add_path_case_insensitive` | PASS |
| `test_cur_step_changed_defined` | PASS |
| `test_cur_step_changed_ss_post_install` | PASS |
| `test_python_path_txt_written` | PASS |
| `test_save_string_to_file_used` | PASS |
| `test_python_path_txt_overwrite_mode` | PASS |
| `test_python_path_contains_app_python_embed` | PASS |
| `test_cur_uninstall_step_changed_defined` | PASS |
| `test_cur_uninstall_step_us_post_uninstall` | PASS |
| `test_reg_write_expand_string_value_called` | PASS |
| `test_uninstall_delete_turbulence_dir` | PASS |
| `test_uninstall_delete_type_files_and_dirs` | PASS |
| `test_python_embed_exists_function_preserved` | PASS |
| `test_python_embed_files_entry_present` | PASS |

**Result: 26/26 passed**

### INS-021 Tester edge-case suite (9 tests added)

| Test | Covers | Result |
|------|--------|--------|
| `test_needs_add_path_semicolon_wrapping` | Semicolon wrapping prevents partial path match (e.g. `\bin` vs `\bin2`) | PASS |
| `test_needs_add_path_early_exit_when_registry_missing` | `Result := True` + `Exit` on absent registry key — safe first install | PASS |
| `test_needs_add_path_uses_pos_function` | `Pos()` used for substring search | PASS |
| `test_registry_root_is_hkcu_not_hklm` | PATH modified in HKCU only, never HKLM (machine-wide) | PASS |
| `test_python_path_txt_written_to_localappdata` | `ConfigDir` expands `{localappdata}` via `ExpandConstant` | PASS |
| `test_config_dir_exists_check_before_create_dir` | `DirExists` checked before `CreateDir`; `DirExists` appears before `CreateDir` | PASS |
| `test_uninstall_strips_leading_and_trailing_semicolons` | Both while-loops trim residual leading and trailing semicolons | PASS |
| `test_uninstall_exits_early_if_path_not_found` | `if StartPos = 0 then Exit` guard in uninstall PATH removal | PASS |
| `test_registry_check_uses_expand_constant` | `ExpandConstant` present in `[Registry]` Check line | PASS |

**Result: 9/9 passed**

### INS-021 combined suite

**35/35 passed** (26 developer + 9 Tester edge-case)

### Full regression suite

**Exit code: 0 — no new failures introduced.**  
All pre-existing test states are unchanged. INS-021 changes are isolated to `setup.iss` (installer configuration file) with no impact on Python source modules.

---

## Acceptance Criteria Check (US-032)

| Criterion | Status |
|-----------|--------|
| Installer bundles the Python Embeddable Distribution | ✅ (INS-018, unchanged) |
| `ts-python` shim installed at a well-known fixed location | ✅ `{localappdata}\TurbulenceSolutions\bin\ts-python.cmd` |
| Shim added to PATH | ✅ `[Registry]` HKCU `Environment\Path` via `NeedsAddPath` guard |
| Shim reads from `python-path.txt` config file | ✅ `python-path.txt` written by `CurStepChanged(ssPostInstall)` |
| Config points to bundled Python exe | ✅ `{app}\python-embed\python.exe` |
| Uninstall removes shim and PATH entry | ✅ `[UninstallDelete]` + `CurUninstallStepChanged(usPostUninstall)` |
| Reinstall overwrites `python-path.txt` with updated path | ✅ `SaveStringToFile(..., False)` (overwrite mode) |
| No duplicate PATH entries on reinstall | ✅ `NeedsAddPath` dedup guard |

All 8 acceptance criteria met.

---

## Bugs Filed

None. No defects found.

---

## Verdict

**PASS** — All tests pass, all acceptance criteria met, no regressions, no security issues. WP set to `Done`.
