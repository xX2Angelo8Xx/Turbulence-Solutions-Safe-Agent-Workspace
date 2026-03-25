# FIX-077 — Dev Log

## Workpackage
- **ID:** FIX-077
- **Name:** Bump version to 3.2.2 and rebuild release
- **Branch:** FIX-077/version-bump-322
- **Assigned To:** Developer Agent
- **Status:** Review

## Implementation Summary

Updated the VERSION string from `3.2.1` to `3.2.2` in all 5 canonical version locations and updated the
FIX-070 version checkpoint test to assert `3.2.2`.

### Root Cause (BUG-131, BUG-133, BUG-134)
The v3.2.2 GitHub release tag was created before the version constants were bumped. As a result:
- Deployed launcher reported `VERSION=3.2.1` causing permanent "update available" loop (BUG-131).
- The binary was built before SAF-047/SAF-048 fixes were merged, leaving Get-ChildItem blocked (BUG-133)
  and memory tool blocked (BUG-134) in the deployed binary. Rebuilding from HEAD resolves both.

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/config.py` | `VERSION = "3.2.1"` → `"3.2.2"` |
| `pyproject.toml` | `version = "3.2.1"` → `"3.2.2"` |
| `src/installer/windows/setup.iss` | `MyAppVersion "3.2.1"` → `"3.2.2"` |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION="3.2.1"` → `"3.2.2"` |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION="3.2.1"` → `"3.2.2"` |
| `tests/FIX-070/test_fix070_version_bump.py` | Updated `STALE_VERSION`, `test_current_version_is_3_2_2`, `test_no_stale_3_2_1_in_version_files` |
| `docs/workpackages/workpackages.csv` | FIX-077 set to `In Progress` → `Review`, `Assigned To = Developer Agent` |

## Tests Written

- `tests/FIX-077/test_fix077_version_322.py` — 7 tests covering:
  1. `test_config_py_is_322` — VERSION constant in config.py equals 3.2.2
  2. `test_pyproject_toml_is_322` — version in pyproject.toml equals 3.2.2
  3. `test_setup_iss_is_322` — MyAppVersion in setup.iss equals 3.2.2
  4. `test_build_dmg_sh_is_322` — APP_VERSION in build_dmg.sh equals 3.2.2
  5. `test_build_appimage_sh_is_322` — APP_VERSION in build_appimage.sh equals 3.2.2
  6. `test_no_stale_321_in_any_version_file` — none of the 5 files contain 3.2.1
  7. `test_all_version_files_agree` — all 5 files agree on 3.2.2

## Test Results

- `tests/FIX-077/`: 7 passed
- `tests/FIX-070/`: 8 passed (all FIX-070 tests now reflect 3.2.2)
- Total: 15 passed, 0 failed

## Known Limitations

None. This is a version string bump with no logic changes.

## Referenced Bugs

- **BUG-131** — Fixed In WP: FIX-077 (VERSION constant now 3.2.2, eliminating update loop)
- **BUG-133** — Fixed In WP: FIX-077 (rebuild from HEAD includes Get-ChildItem allowlist fix)
- **BUG-134** — Fixed In WP: FIX-077 (rebuild from HEAD includes SAF-048 validate_memory() fix)
