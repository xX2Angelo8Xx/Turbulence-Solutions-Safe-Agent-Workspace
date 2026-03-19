# Test Report — INS-005

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 1

## Summary

The Inno Setup script `src/installer/windows/setup.iss` satisfies all review checklist items and
all structural requirements. Metadata is consistent with `pyproject.toml` and `launcher.spec`.
No hardcoded paths, no secrets, and no regressions introduced. All 41 INS-005 tests pass.

**Verdict: PASS**

---

## Review Checklist

| Item | Expected | Actual | Result |
|------|----------|--------|--------|
| AppName | "Agent Environment Launcher" | "Agent Environment Launcher" | ✅ Pass |
| AppVersion | "0.1.0" (from pyproject.toml) | "0.1.0" | ✅ Pass |
| AppPublisher | "Turbulence Solutions" | "Turbulence Solutions" | ✅ Pass |
| Source path | `dist\launcher\*` (matches COLLECT name='launcher') | `dist\launcher\*` | ✅ Pass |
| Uses `{autopf}` | Yes – no hardcoded `Program Files` | DefaultDirName={autopf}\\ | ✅ Pass |
| AppId GUID | RFC-4122 GUID in Inno Setup `{{...}` format | `{{B8F4E5A2-7C3D-4E6F-…}` | ✅ Pass |
| Admin privileges | PrivilegesRequired=admin | PrivilegesRequired=admin | ✅ Pass |
| Start Menu shortcut | {group} macro in [Icons] | `{group}\\{#MyAppName}` | ✅ Pass |
| Uninstaller | [UninstallDelete] with filesandirs | Type: filesandirs; Name: "{app}" | ✅ Pass |
| No secrets / hardcoded absolute paths | None | None found | ✅ Pass |
| Compression | lzma + SolidCompression=yes | Compression=lzma, SolidCompression=yes | ✅ Pass |
| Wizard style | modern | WizardStyle=modern | ✅ Pass |
| Architecture guard | x64compatible | ArchitecturesAllowed=x64compatible | ✅ Pass |
| Desktop icon default | Opt-in (unchecked) | Flags: unchecked | ✅ Pass |
| Exe name consistency | launcher.exe (matches spec name='launcher') | MyAppExeName "launcher.exe" | ✅ Pass |

---

## Tests Executed

### Developer Tests (15 tests — test_ins005_setup_iss.py)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_file_exists | Unit | Pass | setup.iss present at src/installer/windows/ |
| test_file_non_empty | Unit | Pass | File has content |
| test_required_section_present[Setup] | Unit | Pass | [Setup] section present |
| test_required_section_present[Files] | Unit | Pass | [Files] section present |
| test_required_section_present[Icons] | Unit | Pass | [Icons] section present |
| test_required_section_present[Run] | Unit | Pass | [Run] section present |
| test_required_section_present[UninstallDelete] | Unit | Pass | [UninstallDelete] section present |
| test_app_name | Unit | Pass | AppName = "Agent Environment Launcher" |
| test_app_version | Unit | Pass | AppVersion = "0.1.0" |
| test_app_publisher | Unit | Pass | AppPublisher = "Turbulence Solutions" |
| test_uses_autopf_not_hardcoded | Unit | Pass | {autopf} used; C:\\Program Files not present |
| test_source_uses_dist_launcher_glob | Unit | Pass | Source = "dist\\launcher\\*" |
| test_source_has_recursesubdirs | Unit | Pass | recursesubdirs present |
| test_has_app_id | Unit | Pass | AppId declared |
| test_privileges_required_set | Unit | Pass | PrivilegesRequired declared |

### Tester Edge-Case Tests (26 tests — test_ins005_edge_cases.py)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_app_id_is_valid_guid_format | Unit | Pass | AppId uses Inno Setup {{GUID} format; GUID matches RFC-4122 |
| test_app_id_guid_is_not_all_zeros | Unit | Pass | GUID is not the null all-zeros sentinel |
| test_no_hardcoded_drive_letter[C:] | Unit | Pass | No hardcoded C:\\ path |
| test_no_hardcoded_drive_letter[D:] | Unit | Pass | No hardcoded D:\\ path |
| test_no_hardcoded_drive_letter[E:] | Unit | Pass | No hardcoded E:\\ path |
| test_no_hardcoded_drive_letter[F:] | Unit | Pass | No hardcoded F:\\ path |
| test_no_hardcoded_drive_letter[G:] | Unit | Pass | No hardcoded G:\\ path |
| test_source_path_is_relative_not_absolute | Unit | Pass | Source starts with dist\\ |
| test_default_dir_uses_autopf_not_direct_path | Unit | Pass | DefaultDirName={autopf} verified by regex |
| test_output_base_filename_declared | Unit | Pass | OutputBaseFilename present |
| test_output_base_filename_contains_setup | Unit | Pass | OutputBaseFilename = "AgentEnvironmentLauncher-Setup" |
| test_output_base_filename_no_spaces | Unit | Pass | Filename contains no spaces |
| test_createallsubdirs_flag_present | Unit | Pass | createallsubdirs flag present alongside recursesubdirs |
| test_ignoreversion_flag_present | Unit | Pass | ignoreversion flag present — required for PyInstaller bundles |
| test_compression_is_lzma | Unit | Pass | Compression=lzma on its own line |
| test_solid_compression_enabled | Unit | Pass | SolidCompression=yes on its own line |
| test_privileges_required_is_exactly_admin | Unit | Pass | PrivilegesRequired=admin exactly (not lowest) |
| test_architecture_restricted_to_x64 | Unit | Pass | ArchitecturesAllowed=x64compatible present |
| test_start_menu_shortcut_uses_group_macro | Unit | Pass | {group} macro used in [Icons] |
| test_desktop_shortcut_is_opt_in | Unit | Pass | desktopicon task has Flags: unchecked |
| test_uninstall_delete_type_is_filesandirs | Unit | Pass | Type: filesandirs in [UninstallDelete] |
| test_uninstall_targets_app_macro | Unit | Pass | Name: "{app}" — no hardcoded path |
| test_app_version_matches_pyproject_toml | Unit | Pass | AppVersion "0.1.0" == pyproject.toml version 0.1.0 |
| test_exe_name_matches_pyinstaller_spec_name | Unit | Pass | launcher.exe matches spec EXE name='launcher' |
| test_source_dir_matches_pyinstaller_collect_name | Unit | Pass | dist\\launcher\\* matches COLLECT name='launcher' |
| test_wizard_style_is_modern | Unit | Pass | WizardStyle=modern confirmed |

### Full Regression Suite

| Run | Type | Result | Notes |
|-----|------|--------|-------|
| Full suite — 936 total tests | Regression | Pass (no new failures) | 16 failures all pre-existing from GUI-008/INS-004/INS-012/SAF-010; none caused by INS-005 |

---

## Bugs Found

None. The implementation is correct and complete.

---

## TODOs for Developer

None. No action required.

---

## Verdict

**PASS** — mark INS-005 as Done.

All 41 INS-005 tests pass (15 developer + 26 Tester edge-case). No regressions introduced.
The script is correct, self-consistent, and secure.
