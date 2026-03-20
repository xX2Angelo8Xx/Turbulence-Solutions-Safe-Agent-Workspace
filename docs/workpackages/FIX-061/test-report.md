# Test Report — FIX-061

**Tester:** Tester Agent
**Date:** 2026-03-20
**Iteration:** 1

## Summary

FIX-061 bumps the version from 3.0.3 to 3.1.0 across all 5 canonical version locations. The implementation is correct and complete. All 5 files contain "3.1.0", no source file retains "3.0.3", the version string is valid semver, and all 5 locations are consistent with each other. The developer's 5 tests pass. 4 Tester edge-case tests were added and also pass. The full regression suite (4086 tests) introduces zero new failures — all 88 observed failures are pre-existing and documented in prior test runs.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_config_py_version | Unit | PASS | config.py VERSION = "3.1.0" |
| test_pyproject_toml_version | Unit | PASS | pyproject.toml version = "3.1.0" |
| test_setup_iss_version | Unit | PASS | setup.iss MyAppVersion = "3.1.0" |
| test_build_dmg_sh_version | Unit | PASS | build_dmg.sh APP_VERSION = "3.1.0" |
| test_build_appimage_sh_version | Unit | PASS | build_appimage.sh APP_VERSION = "3.1.0" |
| test_version_semver_format (edge) | Unit | PASS | "3.1.0" matches \d+\.\d+\.\d+ |
| test_all_five_files_consistent (edge) | Unit | PASS | All 5 locations agree on same version |
| test_version_greater_than_predecessor (edge) | Unit | PASS | 3.1.0 > 3.0.3 via packaging.version |
| test_no_old_version_in_source_files (edge) | Unit | PASS | No source file contains "3.0.3" |
| FIX-061 Tester: targeted suite (9 tests) | Unit | PASS | TST-1954: 9/9 pass |
| FIX-061 Tester: full regression suite | Regression | PASS | TST-1955: 4086 passed / 88 pre-existing failures / 8 skipped |

## Manual Verification

All 5 canonical version files confirmed to contain "3.1.0":
- `src/launcher/config.py` → `VERSION: str = "3.1.0"` ✓
- `pyproject.toml` → `version = "3.1.0"` ✓
- `src/installer/windows/setup.iss` → `#define MyAppVersion "3.1.0"` ✓
- `src/installer/macos/build_dmg.sh` → `APP_VERSION="3.1.0"` ✓
- `src/installer/linux/build_appimage.sh` → `APP_VERSION="3.1.0"` ✓

No source file contains the old version string "3.0.3". All 3.0.3 references in the repository are in documentation/history files (maintenance notes, workpackages CSV descriptions, bugs.csv).

## Regression Check

88 failures observed in the full suite are **all pre-existing**:
- FIX-019 `test_new_version_major_incremented_by_one`: pre-existing since v3.0.1 (documented in TST-1866)
- FIX-050 (5 tests hardcoding "3.0.2"): pre-existing since FIX-058 (BUG-086)
- FIX-028/031/037/038/039 codesign tests: pre-existing superseded tests (documented TST-1838/TST-1828)
- FIX-009, FIX-015/016, GUI-008/013, INS-004/019, SAF-010/022/025: all documented pre-existing
- 14 yaml-import errors (FIX-010/011/029, INS-013–017): pre-existing collection errors, excluded from run

`scripts/validate_workspace.py --wp FIX-061` → exit code 0, "All checks passed."

## Tests Use CURRENT_VERSION ✓

Both the developer's tests and the Tester's edge-case tests import `CURRENT_VERSION` from `tests/shared/version_utils.py` (which reads dynamically from `config.py`). No hardcoded version strings in test assertions.

## Bugs Found

None.

## TODOs for Developer

None.

## Verdict

**PASS — mark WP as Done.**
