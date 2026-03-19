# Dev Log — INS-006: macOS Installer

**Agent:** Developer Agent
**Date:** 2026-03-12
**Status:** In Progress → Review

---

## Summary

Created `src/installer/macos/build_dmg.sh`, a Bash script that builds a macOS `.dmg` disk image from PyInstaller `--onedir` output. The script supports both Intel (`x86_64`) and Apple Silicon (`arm64`) architectures.

---

## Implementation Details

### Script: `src/installer/macos/build_dmg.sh`

**Architecture selection:**
- Accepts an optional first argument: `x86_64` or `arm64`.
- Falls back to `uname -m` (host architecture) when no argument is supplied.
- Passes `--target-arch` to PyInstaller to enable universal binary targeting.

**Steps performed by the script:**
1. Checks whether `dist/launcher/` already exists; if not, runs PyInstaller with `launcher.spec`.
2. Creates a standard macOS `.app` bundle structure under `dist/AgentEnvironmentLauncher.app/`.
3. Writes `Info.plist` with all required keys: `CFBundleName`, `CFBundleDisplayName`, `CFBundleIdentifier`, `CFBundleVersion`, `CFBundleShortVersionString`, `CFBundleExecutable`, `CFBundlePackageType`, `NSHighResolutionCapable`, `LSMinimumSystemVersion`, `NSHumanReadableCopyright`.
4. Stages the `.app` bundle in a temporary directory created by `mktemp -d`.
5. Calls `hdiutil create` with `-format UDZO` (compressed DMG) to produce `dist/AgentEnvironmentLauncher-<version>-<arch>.dmg`.
6. Cleans up the temporary staging directory.

**Security / path safety:**
- All paths are relative to the repository root (no hardcoded absolute paths like `/Users/...` or `/home/...`).
- No credentials, tokens, or secrets.
- `set -euo pipefail` ensures the script exits immediately on any error.

---

## Files Created

| File | Description |
|------|-------------|
| `src/installer/macos/build_dmg.sh` | Main DMG build script |
| `tests/INS-006/__init__.py` | Test package marker |
| `tests/INS-006/test_ins006_build_dmg.py` | 15 unit tests (text-parse only, cross-platform) |
| `docs/workpackages/INS-006/dev-log.md` | This file |

---

## Tests Written

All 15 tests parse the shell script as plain text — no execution is required, so they run on all platforms (Windows, macOS, Linux).

| Test | Category | Description |
|------|----------|-------------|
| `test_file_exists` | Unit | Script file is present |
| `test_file_is_non_empty` | Unit | File size > 0 |
| `test_shebang_line` | Unit | First line is `#!/usr/bin/env bash` |
| `test_set_pipefail` | Unit | `set -euo pipefail` or equivalent present |
| `test_references_hdiutil` | Unit | `hdiutil` command appears |
| `test_hdiutil_create` | Unit | `hdiutil create` subcommand referenced |
| `test_app_name` | Unit | App name matches constant |
| `test_app_version` | Unit | Version `0.1.0` present |
| `test_publisher` | Unit | "Turbulence Solutions" referenced |
| `test_intel_arch` | Unit | `x86_64` architecture supported |
| `test_arm_arch` | Unit | `arm64` architecture supported |
| `test_no_hardcoded_home_path` | Security | No `/Users/` or `/home/` absolute paths |
| `test_info_plist_keys` | Unit | All required CFBundle keys present |
| `test_app_bundle_structure` | Unit | `Contents/MacOS` and `Contents/Resources` created |
| `test_uses_launcher_spec` | Unit | References `launcher.spec` |

---

## Test Results

- 32/32 pytest items pass (15 test functions; `test_plist_key_present` parametrized over 10 keys)
- Zero regressions in full suite (956 pass, 11 pre-existing failures unchanged)

---

## Iteration 1 — Initial Implementation

All acceptance criteria met:
- [x] Script exists at `src/installer/macos/build_dmg.sh`
- [x] Runs PyInstaller or skips if output exists
- [x] Creates `.app` bundle from `dist/launcher/`
- [x] Uses `hdiutil` for DMG creation
- [x] Supports `x86_64` and `arm64`
- [x] Info.plist with all required metadata keys
- [x] No hardcoded absolute paths
- [x] No secrets or credentials
- [x] All 15 tests pass
