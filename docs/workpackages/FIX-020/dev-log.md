# Dev Log — FIX-020: Bump Version to 2.0.0

## Status
In Progress → (to be set to Review after tests pass)

## Assigned To
Developer Agent

## Date
2026-03-17

---

## Summary

Updated the version string from `1.0.3` to `2.0.0` in all 5 required locations.

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/config.py` | `VERSION: str = "1.0.3"` → `"2.0.0"` |
| `pyproject.toml` | `version = "1.0.3"` → `"2.0.0"` |
| `src/installer/windows/setup.iss` | `#define MyAppVersion "1.0.3"` → `"2.0.0"` |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION="1.0.3"` → `"2.0.0"` |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION="1.0.3"` → `"2.0.0"` |

## Implementation Notes

- Only version string values were changed; no logic, structure, or formatting was modified.
- No new dependencies introduced.
- Git tag `v2.0.0` is intentionally NOT created here — that will be done separately after merge per the WP spec.

## Tests Written

- `tests/FIX-020/test_fix020_version_bump.py`
  - `test_config_py_version`: asserts `VERSION == "2.0.0"` from config.py
  - `test_pyproject_toml_version`: parses pyproject.toml and asserts version field is "2.0.0"
  - `test_setup_iss_version`: reads setup.iss and asserts MyAppVersion define is "2.0.0"
  - `test_build_dmg_sh_version`: reads build_dmg.sh and asserts APP_VERSION line is "2.0.0"
  - `test_build_appimage_sh_version`: reads build_appimage.sh and asserts APP_VERSION line is "2.0.0"
  - `test_no_old_version_in_installer_files`: asserts "1.0.3" does not appear in any of the 5 files

## Test Results

All 6 FIX-020 tests pass. See `docs/test-results/test-results.csv` for logged run.

---

## Iteration 2 — Fix 33 version-related regressions in older test suites

### Problem
After bumping the version to 2.0.0, 33 tests from older version-bump workpackages
failed because they hardcoded the previous version strings (1.0.0 / 1.0.1 / 1.0.2 / 1.0.3).
These tests verify that the version files contain the *current* version, so they must always
be updated to reflect the latest version.

### Files Updated

| File | Change |
|------|--------|
| `tests/FIX-010/test_fix010_cicd_pipeline.py` | Updated 3 assertions: `"1.0.3"` → `"2.0.0"` |
| `tests/FIX-014/test_fix014_version_bump.py` | `EXPECTED_VERSION = "1.0.3"` → `"2.0.0"` |
| `tests/FIX-014/test_fix014_edge_cases.py` | `EXPECTED_VERSION = "1.0.3"` → `"2.0.0"` |
| `tests/FIX-017/test_fix017_version_bump.py` | `EXPECTED_VERSION = "1.0.3"` → `"2.0.0"` |
| `tests/FIX-017/test_fix017_edge_cases.py` | `EXPECTED_VERSION` → `"2.0.0"`, `PREVIOUS_VERSION` → `"1.0.3"` |
| `tests/FIX-019/test_fix019_version_bump.py` | `EXPECTED_VERSION = "1.0.3"` → `"2.0.0"` |
| `tests/FIX-019/test_fix019_edge_cases.py` | `EXPECTED_VERSION` → `"2.0.0"`, `PREVIOUS_VERSION` → `"1.0.3"`, updated version ordering test to check major bump |
| `tests/INS-005/test_ins005_setup_iss.py` | `'MyAppVersion "1.0.3"'` → `'MyAppVersion "2.0.0"'` |
| `tests/INS-006/test_ins006_build_dmg.py` | `"1.0.3"` → `"2.0.0"` |
| `tests/INS-007/test_ins007_build_appimage.py` | `"1.0.3"` → `"2.0.0"` |

### Notes
- `tests/FIX-019/test_fix019_edge_cases.py`: `test_new_version_patch_incremented_by_one` was
  renamed to `test_new_version_major_incremented_by_one` and updated to verify the major
  component is incremented by 1 and minor/patch are reset to 0 (FIX-020 is a major bump).
- `SKIP_VERSION_1` in FIX-019 edge cases updated from "1.0.1" to "1.0.2" to capture the
  directly preceding patch version as a skip regression check.

### Test Results After Fix

Full regression suite: **3141 passed, 2 pre-existing failures, 29 skipped, 1 xfailed**

Pre-existing failures (not caused by FIX-020; unchanged from prior workpackages):
- `tests/FIX-009/test_fix009_no_duplicate_tst_ids.py` — TST-1557 dup introduced by GUI-017
- `tests/INS-005/test_ins005_edge_cases.py::test_uninstall_delete_type_is_filesandirs` — BUG-045

## Known Limitations

None. This is a straightforward version bump with no runtime risk.
