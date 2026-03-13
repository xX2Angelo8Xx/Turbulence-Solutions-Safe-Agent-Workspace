# Dev Log — INS-007

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective
Create `src/installer/linux/build_appimage.sh` — a bash script that:
1. Runs PyInstaller using the existing `launcher.spec` to produce bundled output in `dist/launcher/`.
2. Creates a compliant AppDir structure (AppDir/usr/bin/, .desktop, AppRun, icon).
3. Downloads `appimagetool` if not present (from official GitHub releases, HTTPS only).
4. Runs `appimagetool` to produce the final `.AppImage` file for the target architecture.
5. Supports both x86_64 and aarch64 architectures via auto-detection or explicit argument.
6. Prints the output path on success; exits on failure with a descriptive error message.
7. Makes the resulting AppImage executable.

## Implementation Summary

### Pattern followed
The script follows the exact same structure as `src/installer/macos/build_dmg.sh`:
- Same variable naming conventions (APP_NAME, APP_VERSION, PUBLISHER, SPEC_FILE, DIST_DIR, BUILD_DIR, TARGET_ARCH).
- Same PyInstaller invocation pattern (skip if `dist/launcher/` already present).
- Same `echo "==>"` progress reporting format.
- Same `set -euo pipefail` safety flags.

### Key decisions
- Architecture auto-detected via `uname -m` when no argument supplied; `x86_64` and `aarch64` supported explicitly.
- AppDir structure follows the AppImage specification: `AppDir/usr/bin/`, `AppDir/usr/share/applications/`, `AppDir/usr/share/icons/`, `AppDir/AppRun`, `AppDir/<app-id>.desktop`, `AppDir/<app-id>.svg`.
- AppRun is a minimal `exec` wrapper that resolves its own location via `readlink -f` for relocatability.
- The `.desktop` file uses the canonical reverse-domain `APP_ID` as the `Icon` field so the bundled SVG is found.
- A minimal SVG placeholder icon is embedded in the script using the brand colours (#0A1D4E background, #5BC5F2 text) from `config.py`.
- `appimagetool` is downloaded via `curl -fsSL --proto '=https' --tlsv1.2` (TLS 1.2+, HTTPS only, no HTTP fallback) from the official AppImageKit GitHub releases.
- PyInstaller output existence is validated before proceeding to AppDir creation (fail-fast if build step was skipped but `dist/launcher/` is missing).
- Output filename: `TurbulenceSolutionsLauncher-<arch>.AppImage` in `dist/`.
- `ARCH` environment variable is passed to `appimagetool` to ensure the correct ELF architecture is embedded in the AppImage header.

## Files Changed
- `src/installer/linux/build_appimage.sh` — created (new file)
- `docs/workpackages/workpackages.csv` — INS-007 status → In Progress, Assigned To → Developer Agent

## Tests Written
- `tests/INS-007/__init__.py` — empty init for pytest discovery
- `tests/INS-007/test_ins007_build_appimage.py` — 32 unit tests covering:

### TestFileExists (2 tests)
- `test_file_exists` — script exists at expected path
- `test_file_is_non_empty` — script has content

### TestShebangAndSafety (2 tests)
- `test_shebang_line` — first line is `#!/usr/bin/env bash`
- `test_set_pipefail` — `set -euo pipefail` present

### TestArchitectureSupport (3 tests)
- `test_x86_64_arch_referenced` — x86_64 explicitly mentioned
- `test_aarch64_arch_referenced` — aarch64 explicitly mentioned
- `test_uname_m_fallback` — `uname -m` used for auto-detection

### TestAppDirStructure (4 tests)
- `test_appdir_usr_bin_created` — `AppDir/usr/bin` directory created
- `test_appdir_usr_share_applications_created` — `AppDir/usr/share/applications` created
- `test_apprun_created` — `AppRun` entry point created
- `test_apprun_made_executable` — `chmod +x` applied to AppRun

### TestDesktopFile (5 tests)
- `test_desktop_file_created_in_applications` — .desktop written inside applications/
- `test_desktop_file_copied_to_appdir_root` — .desktop copied to AppDir root
- `test_desktop_entry_name` — Name field contains app name
- `test_desktop_entry_exec` — Exec field is `launcher`
- `test_desktop_entry_type` — Type=Application present

### TestIconFile (3 tests)
- `test_icon_at_appdir_root` — SVG icon at AppDir root
- `test_icon_uses_brand_colors` — SVG contains company colours
- `test_icon_in_hicolor_dir` — icon also placed in hicolor dir

### TestAppRunContent (2 tests)
- `test_apprun_uses_readlink` — `readlink -f` used for self-location
- `test_apprun_execs_launcher` — `exec` used to launch the binary

### TestAppImageTool (5 tests)
- `test_references_appimagetool` — appimagetool command referenced
- `test_appimagetool_download_uses_https` — download URL starts with https://
- `test_appimagetool_download_no_plain_http` — no http:// URLs in download
- `test_appimagetool_download_uses_curl` — curl command used for download
- `test_download_uses_tlsv12` — `--tlsv1.2` flag present

### TestAppImageOutput (2 tests)
- `test_appimage_filename_contains_appbundlename` — output filename contains bundle name
- `test_appimage_chmod_executable` — chmod +x applied to final AppImage

### TestSecurity (4 tests)
- `test_no_eval_or_unsafe_constructs` — no `eval` usage
- `test_no_hardcoded_home_path` — no `/home/` in script
- `test_no_hardcoded_absolute_dist_path` — dist/ referenced relatively
- `test_pyinstaller_output_validated` — validation check before AppDir creation

### TestMetadata (3 tests)
- `test_app_version_embedded` — version 0.1.0 present
- `test_publisher_referenced` — Turbulence Solutions present
- `test_references_launcher_spec` — launcher.spec referenced

## Known Limitations
- The placeholder icon is a minimal SVG with the two brand colours; a real PNG icon would be needed for production use.
- `appimagetool` does not support cross-architecture builds without QEMU; `--target-arch` is therefore not passed to PyInstaller (unlike the macOS DMG script).
- The script must be run from the repository root (same constraint as `build_dmg.sh`).
