# Dev Log — FIX-012: Fix macOS PyInstaller target-arch and Windows Inno Setup directives

**WP ID:** FIX-012  
**Category:** Fix  
**Status:** Review  
**Assigned To:** Developer Agent  
**Date:** 2026-03-14  

---

## Summary

Fixed two CI/CD build failures affecting macOS ARM and Windows jobs:

1. **BUG-040** — `build_dmg.sh` passed `--target-arch "${TARGET_ARCH}"` as a CLI flag to PyInstaller, but PyInstaller does not allow makespec options when a `.spec` file is provided. This caused the `macos-arm-build` CI job to fail with `ERROR: option(s) not allowed: --target-architecture/--target-arch`.

2. **BUG-041** — `setup.iss` contained `ArchitecturesAllowed=x64compatible` and `ArchitecturesInstallMode=x64compatible` directives not recognized by the Inno Setup version installed by Chocolatey on GitHub Actions. This caused the `windows-build` CI job to fail with `Unrecognized [Setup] section directive "ArchitecturesInstallMode"`.

---

## Files Changed

| File | Change |
|------|--------|
| `src/installer/macos/build_dmg.sh` | Removed `--target-arch "${TARGET_ARCH}"` line from PyInstaller invocation |
| `src/installer/windows/setup.iss` | Removed `ArchitecturesAllowed=x64compatible` and `ArchitecturesInstallMode=x64compatible` lines |
| `tests/INS-005/test_ins005_edge_cases.py` | Updated `test_architecture_restricted_to_x64` → `test_architecture_directives_not_present` to assert directives are absent |
| `tests/INS-006/test_ins006_build_dmg.py` | Updated `test_target_arch_passed_to_pyinstaller` → `test_target_arch_not_passed_to_pyinstaller` to assert flag is absent |
| `tests/FIX-012/test_fix012_ci_build_fixes.py` | New regression tests for BUG-040 and BUG-041 |
| `docs/bugs/bugs.csv` | Added BUG-040 and BUG-041 |
| `docs/workpackages/workpackages.csv` | Added FIX-012 row |

---

## Implementation Details

### build_dmg.sh fix

The `--target-arch` flag is a "makespec option" in PyInstaller terminology — it's only valid when generating a `.spec` file from scratch (the `pyi-makespec` / `pyinstaller --name ...` path). When PyInstaller receives an existing `.spec` file, it ignores makespec options and rejects them with an error.

Since `macos-arm-build` runs on an ARM runner (`macos-14`), PyInstaller automatically builds for the host architecture (arm64) without any explicit flag. The `TARGET_ARCH` variable and `uname -m` fallback remain intact for DMG naming; only the PyInstaller CLI invocation was changed.

### setup.iss fix

`ArchitecturesAllowed` and `ArchitecturesInstallMode` with the `x64compatible` value are directives introduced in Inno Setup 6.3. While the Chocolatey package installs Inno Setup 6.x, the CI version on GitHub Actions runners does not support `x64compatible` syntax. These directives are optional — the app functions correctly without them, and GitHub Actions Windows runners are exclusively 64-bit. Removing both lines eliminates the compilation error with no functional regression.

---

## Tests Written

**File:** `tests/FIX-012/test_fix012_ci_build_fixes.py`  
**Count:** 15 tests

| Test | Category | Description |
|------|----------|-------------|
| `test_target_arch_flag_absent` | Regression | `--target-arch` absent from build_dmg.sh (BUG-040) |
| `test_pyinstaller_command_present` | Unit | PyInstaller invocation still exists |
| `test_distpath_flag_present` | Unit | `--distpath` still passed |
| `test_workpath_flag_present` | Unit | `--workpath` still passed |
| `test_noconfirm_flag_present` | Unit | `--noconfirm` still passed |
| `test_spec_file_passed_to_pyinstaller` | Unit | `${SPEC_FILE}` still referenced |
| `test_spec_file_variable_defined` | Unit | `SPEC_FILE="launcher.spec"` defined |
| `test_architectures_install_mode_absent` | Regression | `ArchitecturesInstallMode` absent (BUG-041) |
| `test_architectures_allowed_absent` | Regression | `ArchitecturesAllowed` absent (BUG-041) |
| `test_setup_section_present` | Unit | `[Setup]` section still exists |
| `test_app_id_present` | Unit | `AppId=` still present |
| `test_app_name_present` | Unit | `AppName=` still present |
| `test_app_version_present` | Unit | `AppVersion=` still present |
| `test_output_base_filename_present` | Unit | `OutputBaseFilename=` still present |
| `test_privileges_required_admin` | Unit | `PrivilegesRequired=admin` still set |

**Also updated:**
- `tests/INS-005/test_ins005_edge_cases.py` — `test_architecture_directives_not_present` now asserts both directives absent
- `tests/INS-006/test_ins006_build_dmg.py` — `test_target_arch_not_passed_to_pyinstaller` now asserts flag absent

---

## Test Results

- **FIX-012 suite:** 15/15 passed
- **Full suite:** 1869 passed, 29 skipped, 0 failed
- Run on: Windows 11, Python 3.11
- Date: 2026-03-14
