# Dev Log — INS-005

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective

Create the Inno Setup 6 script (`src/installer/windows/setup.iss`) that wraps the
PyInstaller `--onedir` output into a Windows `.exe` installer. The installer must
place the app under `{autopf}`, create Start Menu and optional Desktop shortcuts,
and fully clean up on uninstall.

## Implementation Summary

- Created `src/installer/windows/setup.iss` as a standard Inno Setup 6 script.
- Defined preprocessor macros for `AppName`, `AppVersion`, `AppPublisher`, and `AppExeName`
  so version bumps only require changing the `#define` block.
- `DefaultDirName` uses the `{autopf}` macro (resolves to `Program Files` or
  `Program Files (x86)` depending on architecture), never a hardcoded path.
- `[Files]` section sources from `dist\launcher\*` with `recursesubdirs createallsubdirs`
  flags to capture the full PyInstaller `--onedir` output tree.
- `PrivilegesRequired=admin` ensures the installer can write to `Program Files`.
- `ArchitecturesAllowed=x64compatible` and `ArchitecturesInstallMode=x64compatible`
  restricts installation to 64-bit systems matching the PyInstaller target.
- `[UninstallDelete]` removes all bundled files on uninstall.
- Optional desktop icon is offered but unchecked by default (good UX practice).

## Files Changed

- `src/installer/windows/setup.iss` — new file; Inno Setup 6 installer script

## Tests Written

- `tests/INS-005/test_ins005_setup_iss.py`
  - `TestFileExists::test_file_exists` — verifies the .iss file exists on disk
  - `TestFileExists::test_file_non_empty` — verifies the file has content
  - `TestSections::test_required_section_present[Setup/Files/Icons/Run/UninstallDelete]` — all 5 required Inno sections present
  - `TestSetupValues::test_app_name` — AppName macro set to expected value
  - `TestSetupValues::test_app_version` — AppVersion macro set to "0.1.0"
  - `TestSetupValues::test_app_publisher` — AppPublisher macro set to "Turbulence Solutions"
  - `TestSetupValues::test_uses_autopf_not_hardcoded` — {autopf} used; no hardcoded paths
  - `TestSetupValues::test_source_uses_dist_launcher_glob` — Source is `dist\launcher\*`
  - `TestSetupValues::test_source_has_recursesubdirs` — recursesubdirs flag present
  - `TestSetupValues::test_has_app_id` — AppId declared
  - `TestSetupValues::test_privileges_required_set` — PrivilegesRequired=admin declared

## Known Limitations

- The script cannot be compiled or tested end-to-end in this environment (requires Inno
  Setup 6 compiler on Windows). Tests validate the script content/structure only.
- Signing (`SignTool`) is not configured; code-signing is out of scope for INS-005.
- The `AppId` GUID is hardcoded; must not change between releases (Inno Setup requirement).
