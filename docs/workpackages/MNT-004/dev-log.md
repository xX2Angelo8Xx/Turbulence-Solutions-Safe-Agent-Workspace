# MNT-004 Dev Log — Create release.py version bump and tag script

## Overview

**WP ID:** MNT-004  
**Branch:** MNT-004/release-script  
**Status:** In Progress  
**Assigned To:** Developer Agent  
**User Story:** US-068 — Automate Release Version Management  

## Requirements

1. `scripts/release.py` accepts a version string argument (e.g. `3.2.7`) — validated against semver `X.Y.Z`.
2. Updates all 5 version files:
   - `src/launcher/config.py` — `VERSION: str = "X.Y.Z"`
   - `pyproject.toml` — `version = "X.Y.Z"`
   - `src/installer/windows/setup.iss` — `#define MyAppVersion "X.Y.Z"`
   - `src/installer/macos/build_dmg.sh` — `APP_VERSION="X.Y.Z"`
   - `src/installer/linux/build_appimage.sh` — `APP_VERSION="X.Y.Z"`
3. Validates all 5 files were actually updated (reads back and confirms).
4. Creates a git commit `release: bump version to vX.Y.Z`.
5. Creates an annotated git tag `vX.Y.Z` with message `Release vX.Y.Z`.
6. Pushes both commit and tag to origin.
7. Aborts cleanly on any failure — no partial state.
8. `--dry-run` flag: shows what would happen without making changes.
9. Verifies on `main` branch before proceeding.
10. Verifies working tree is clean before proceeding.
11. Also fixes BUG-164: `build_appimage.sh` is now included in the version file list.

## Implementation

### Files Created / Modified

| File | Change |
|------|--------|
| `scripts/release.py` | New file — version bump and tag script |
| `src/installer/linux/build_appimage.sh` | Fixed: `APP_VERSION` from `3.2.4` to `3.2.6` (BUG-164) |
| `docs/bugs/bugs.csv` | Updated BUG-164 `Fixed In WP` to include `MNT-004` |
| `docs/workpackages/workpackages.csv` | MNT-004 status set to `In Progress` |
| `tests/MNT-004/test_mnt004_release.py` | New test file |

### Design Decisions

- `release.py` uses Python's `subprocess` module to invoke git commands (no GitPython dependency).
- All file updates are done in-memory first; only written to disk after all patterns are validated.
- Rollback: if any file update fails validation after write, the script exits with an error message before any git operations.
- The `--dry-run` flag skips all file writes and git operations, only prints what would happen.
- Branch check and clean-tree check happen before any file modifications.
- Version regex: `^\d+\.\d+\.\d+$` (strict semver X.Y.Z only, no v-prefix, no pre-release).

### Bugs Fixed

- **BUG-164**: `src/installer/linux/build_appimage.sh` had `APP_VERSION="3.2.4"` while all other files were at `3.2.6`. Fixed the file directly and now `release.py` includes it in all future version updates.

## Test Summary

Tests located in `tests/MNT-004/test_mnt004_release.py`.

| Test | Description |
|------|-------------|
| `test_valid_versions` | Valid semver strings pass regex |
| `test_invalid_versions` | Invalid strings (no v-prefix, missing patch, etc.) fail regex |
| `test_update_config_py` | Updates VERSION in config.py with realistic content |
| `test_update_pyproject_toml` | Updates version in pyproject.toml |
| `test_update_setup_iss` | Updates #define MyAppVersion in setup.iss |
| `test_update_build_dmg_sh` | Updates APP_VERSION= in build_dmg.sh |
| `test_update_build_appimage_sh` | Updates APP_VERSION= in build_appimage.sh |
| `test_dry_run_no_modification` | --dry-run does not modify any file |
| `test_abort_not_on_main` | Script aborts if not on main branch |
| `test_abort_dirty_tree` | Script aborts if working tree is dirty |
| `test_rollback_on_update_failure` | Script aborts if file update validation fails |
| `test_validate_version_file_confirms_update` | validate_version_file returns True when version present |
| `test_validate_version_file_fails_on_missing` | validate_version_file returns False when version not present |

## Iteration History

*(No iterations — initial implementation.)*
