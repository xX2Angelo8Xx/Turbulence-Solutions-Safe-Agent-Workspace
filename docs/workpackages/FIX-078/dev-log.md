# Dev Log — FIX-078: Version bump to 3.2.3

## Workpackage Info

| Field | Value |
|-------|-------|
| WP ID | FIX-078 |
| Type | FIX |
| Status | In Progress |
| Assigned To | Developer Agent |
| Branch | FIX-078/version-bump-323 |

## Summary

Bump the application version from 3.2.2 to 3.2.3 in all 5 canonical version files. Update the FIX-070 and FIX-077 regression test suites to reflect the new current version (3.2.3) and stale version (3.2.2).

## Implementation

### Version Files Changed (3.2.2 → 3.2.3)

1. `src/launcher/config.py` — `VERSION: str = "3.2.3"`
2. `pyproject.toml` — `version = "3.2.3"`
3. `src/installer/windows/setup.iss` — `#define MyAppVersion "3.2.3"`
4. `src/installer/macos/build_dmg.sh` — `APP_VERSION="3.2.3"`
5. `src/installer/linux/build_appimage.sh` — `APP_VERSION="3.2.3"`

### Test Updates

- `tests/FIX-070/test_fix070_version_bump.py`:
  - `STALE_VERSION` updated from `"3.2.1"` to `"3.2.2"`
  - `test_current_version_is_3_2_2` renamed to `test_current_version_is_3_2_3` with assertion updated to `"3.2.3"`
  - `test_no_stale_3_2_1_in_version_files` renamed to `test_no_stale_3_2_2_in_version_files`

- `tests/FIX-077/test_fix077_version_322.py`:
  - `EXPECTED_VERSION` updated from `"3.2.2"` to `"3.2.3"`
  - `STALE_VERSION` updated from `"3.2.1"` to `"3.2.2"`
  - All `_is_322` function names updated to `_is_323`
  - Docstrings updated to reference 3.2.3
  - Updater tests: no-update mock uses `v3.2.3`; detect-newer mock uses `v3.2.4`
  - `test_parse_version_322_correct` → `test_parse_version_323_correct`, assertion `(3, 2, 3)`
  - `test_no_stale_321_in_docs_version_bump_wp` → `test_no_stale_322_in_docs_version_bump_wp`, now checks FIX-078 dev-log for `"3.2.3"`

### New Tests

- `tests/FIX-078/test_fix078_version_323.py` — 7 tests:
  - Individual assertions for each of the 5 canonical files
  - `test_no_stale_322_in_any_version_file` — confirms 3.2.2 is absent from all version files
  - `test_all_version_files_agree` — confirms all 5 files agree on 3.2.3

## Files Changed

- `src/launcher/config.py`
- `pyproject.toml`
- `src/installer/windows/setup.iss`
- `src/installer/macos/build_dmg.sh`
- `src/installer/linux/build_appimage.sh`
- `tests/FIX-070/test_fix070_version_bump.py`
- `tests/FIX-077/test_fix077_version_322.py`
- `tests/FIX-078/test_fix078_version_323.py` (new)
- `docs/workpackages/FIX-078/dev-log.md` (this file)
- `docs/workpackages/workpackages.csv`

## Test Results

All tests in `tests/FIX-078/`, `tests/FIX-077/`, and `tests/FIX-070/` passed. See test-results.csv for logged run.
