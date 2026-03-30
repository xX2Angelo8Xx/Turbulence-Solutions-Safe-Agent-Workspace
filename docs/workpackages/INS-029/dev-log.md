# Dev Log — INS-029: Bump version to 3.2.4 and tag release

## Summary

Bumped the application version from `3.2.3` to `3.2.4` across all 5 canonical version files. Updated FIX-078 regression test assertions to reflect the new version (following the precedent set by FIX-078 itself, which updated FIX-070 and FIX-077 assertions when bumping to 3.2.3).

## Status

Review

## Files Changed

| File | Change |
|------|--------|
| `pyproject.toml` | `version = "3.2.3"` → `version = "3.2.4"` |
| `src/launcher/config.py` | `VERSION: str = "3.2.3"` → `VERSION: str = "3.2.4"` |
| `src/installer/windows/setup.iss` | `#define MyAppVersion "3.2.3"` → `"3.2.4"` |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION="3.2.3"` → `APP_VERSION="3.2.4"` |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION="3.2.3"` → `APP_VERSION="3.2.4"` |
| `tests/FIX-078/test_fix078_version_323.py` | Updated `EXPECTED_VERSION` to `"3.2.4"`, `STALE_VERSION` to `"3.2.3"` |
| `tests/FIX-078/test_fix078_edge_cases.py` | Updated `EXPECTED_VERSION`, `STALE_VERSION`, `STALE_PREV`, and tuple assertions |
| `tests/INS-029/test_ins029_version_bump.py` | New — 11 tests verifying all 5 files at 3.2.4 |
| `docs/workpackages/workpackages.csv` | INS-029 status: `Open` → `Review` |
| `docs/workpackages/INS-029/dev-log.md` | This file |

## Tests Written

- `tests/INS-029/test_ins029_version_bump.py` — 11 unit tests:
  - `test_config_py_version` — verifies VERSION constant in config.py
  - `test_pyproject_toml_version` — verifies version field in pyproject.toml
  - `test_setup_iss_version` — verifies MyAppVersion in setup.iss
  - `test_build_dmg_version` — verifies APP_VERSION in build_dmg.sh
  - `test_build_appimage_version` — verifies APP_VERSION in build_appimage.sh
  - `test_all_version_files_agree` — all 5 files must agree on 3.2.4
  - `test_no_stale_version_in_config_py` — config.py must not contain 3.2.3 constant
  - `test_no_stale_version_in_pyproject_toml` — pyproject.toml must not contain 3.2.3 version
  - `test_version_import_from_config` — runtime import check
  - `test_version_semver_format` — validates MAJOR.MINOR.PATCH format
  - `test_single_version_define_in_iss` — exactly one define in setup.iss

## Test Results

- TST-2277: 11 passed, 0 failed (INS-029 tests)
- FIX-078 tests: 16 passed, 0 failed (updated assertions)
- No new regressions in the full suite (pre-existing failures unchanged at 80+1)

## Decisions

- Also updated FIX-078 test assertions (`EXPECTED_VERSION`, `STALE_VERSION`, tuples) to reflect 3.2.4, following the established pattern from FIX-078 WP which updated FIX-070 and FIX-077 tests when bumping to 3.2.3.
- Git tag `v3.2.4` will be created after this WP is merged to `main` (as instructed).

## Known Limitations

None.
