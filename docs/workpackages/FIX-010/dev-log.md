# Dev Log — FIX-010: Fix CI/CD Release Pipeline Failures

**WP ID:** FIX-010  
**Branch:** fix/FIX-010-cicd-release-pipeline  
**Date:** 2026-03-14  
**Developer:** Developer Agent  
**Status:** Review

---

## Summary

Fixed all issues preventing the release.yml CI/CD pipeline from building successfully on all 4 platforms. The workflow had never been run on actual CI before; this iteration addresses the real-world failures discovered when the v1.0.0 tag was pushed.

---

## Bugs Addressed

| Bug | Title | Fix |
|-----|-------|-----|
| BUG-036 | macos-13 runner no longer available | Updated to macos-15 + architecture: x64 |
| BUG-037 | Inno Setup Source path resolves from .iss directory | Added ..\..\..\  prefix to navigate to repo root |
| BUG-038 | Build script versions hardcoded to 0.1.0 | Updated all 3 scripts to 1.0.0 |

---

## Changes Made

### `.github/workflows/release.yml`

1. **macos-intel-build runner:** `runs-on: macos-13` → `runs-on: macos-15`  
   Rationale: GitHub Actions removed macos-13 support. macos-15 is the current Intel x64 runner.

2. **macos-intel-build setup-python:** Added `architecture: x64`  
   Rationale: Without explicit arch, the runner may install ARM Python on macos-15.

3. **Removed standalone `Build with PyInstaller` step** from macos-intel-build, macos-arm-build, and linux-build.  
   Rationale: These jobs use build scripts (build_dmg.sh / build_appimage.sh) that invoke PyInstaller internally with `--target-arch`. A standalone `pyinstaller launcher.spec` step before the script would pre-populate `dist/launcher/`, causing the script to skip the `--target-arch` build entirely — producing the wrong architecture binary silently.  
   Windows-build retains its standalone PyInstaller step (Windows has no build script for this).

### `src/installer/windows/setup.iss`

- **Source path:** `"dist\launcher\*"` → `"..\..\..\dist\launcher\*"`  
  Rationale: Without SourceDir, Inno Setup resolves Source paths relative to the .iss file's directory (`src/installer/windows/`). Three `..` naviagte to the repo root where PyInstaller places its output.

- **Version:** `0.1.0` → `1.0.0`  
  Rationale: Matches pyproject.toml and config.py project version.

### `src/installer/macos/build_dmg.sh`

- **APP_VERSION:** `0.1.0` → `1.0.0`

### `src/installer/linux/build_appimage.sh`

- **APP_VERSION:** `0.1.0` → `1.0.0`

---

## Tests Written

### New: `tests/FIX-010/test_fix010_cicd_pipeline.py` (24 tests)

Covers all acceptance criteria for BUG-036, BUG-037, BUG-038:
- Runner is macos-15 (not macos-13)
- setup-python has architecture: x64 for Intel build
- macOS and Linux jobs have NO standalone PyInstaller step
- Windows job DOES retain its PyInstaller step
- setup.iss Source path navigates 3 levels up to repo root
- All 3 build scripts use version 1.0.0
- Version consistency across all build scripts and pyproject.toml

### Updated Existing Tests

| Test File | Change |
|-----------|--------|
| tests/INS-013/test_ins013_ci_workflow.py | Updated macos-13 check to macos-15 |
| tests/INS-015/test_ins015_macos_build_jobs.py | Updated runner check to macos-15; updated step count 6→5; replaced PyInstaller presence checks with absence assertions |
| tests/INS-016/test_ins016_linux_build_job.py | Updated step count 7→6; replaced PyInstaller presence checks with absence assertions; updated ordering tests |
| tests/INS-005/test_ins005_setup_iss.py | Updated version check 0.1.0→1.0.0 |
| tests/INS-005/test_ins005_edge_cases.py | Updated Source path check to verify ..\..\..\  navigation |
| tests/INS-006/test_ins006_build_dmg.py | Updated version check 0.1.0→1.0.0 |
| tests/INS-007/test_ins007_build_appimage.py | Updated version check 0.1.0→1.0.0 |

---

## Test Results

Full suite: **1846 passed, 2 skipped, 0 failed**  
FIX-010 tests: **24 passed**  
See `docs/test-results/test-results.csv` entries TST-947 to TST-970.

---

## Decisions Made

1. Used `macos-15` (not `macos-14`) for the Intel build: macos-14 is the Apple Silicon runner (used by macos-arm-build). macos-15 is the appropriate replacement for the deprecated Intel macos-13 runner.
2. Kept the `--target-arch` PyInstaller calls inside the build scripts (no change): they already handle the case where `dist/launcher/` doesn't exist by calling PyInstaller with the right arch flag.
3. Applied path-splitting approach (not regex) for .iss Source path tests: avoids Python/JSON backslash escaping complexity while remaining correct and readable.
