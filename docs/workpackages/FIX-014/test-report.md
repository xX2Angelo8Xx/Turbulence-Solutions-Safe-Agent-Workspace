# Test Report — FIX-014: Bump Version to 1.0.1

| Field | Value |
|---|---|
| WP ID | FIX-014 |
| Tester | Tester Agent |
| Date | 2026-03-14 |
| Verdict | **PASS** |

---

## Summary

Version bump from `1.0.0` to `1.0.1` has been correctly applied to all 5 canonical
version locations. All tests pass. No regressions introduced. No stale `1.0.0`
references remain in any source file in `src/launcher/` or in the 3 installer scripts.

---

## Files Reviewed

| File | Expected | Found | Status |
|---|---|---|---|
| `src/launcher/config.py` | `VERSION: str = "1.0.1"` | ✓ | PASS |
| `pyproject.toml` | `version = "1.0.1"` | ✓ | PASS |
| `src/installer/windows/setup.iss` | `#define MyAppVersion "1.0.1"` | ✓ | PASS |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION="1.0.1"` | ✓ | PASS |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION="1.0.1"` | ✓ | PASS |

---

## Updated Test Files Reviewed

The Developer updated these pre-existing test files to assert the new version:

| File | Update | Status |
|---|---|---|
| `tests/INS-005/test_ins005_setup_iss.py` | `test_app_version` → asserts `1.0.1` | PASS |
| `tests/INS-006/test_ins006_build_dmg.py` | `test_app_version` → asserts `1.0.1` | PASS |
| `tests/INS-007/test_ins007_build_appimage.py` | `test_app_version_embedded` → asserts `1.0.1` | PASS |
| `tests/FIX-010/test_fix010_cicd_pipeline.py` | 3 assertion bodies updated to `1.0.1` | PASS |

**Minor naming note (non-blocking):** The FIX-010 test functions are still named
`test_setup_iss_version_is_1_0_0`, `test_build_dmg_version_is_1_0_0`,
`test_build_appimage_version_is_1_0_0` but their docstrings and assertions now
reference `1.0.1`. The function names are misleading but the tests pass and
correctly enforce the current version. This is a cosmetic issue only — the
version-tracking logic is sound.

---

## Developer Test Suite (12 tests)

| File | Tests | Result |
|---|---|---|
| `tests/FIX-014/test_fix014_version_bump.py` | 12 | 12/12 PASS |

Covers: VERSION constant import, source text presence, pyproject.toml field,
setup.iss MyAppVersion, build_dmg.sh APP_VERSION, build_appimage.sh APP_VERSION,
negative "old version absent" checks for all 5 files, and cross-file consistency
assertions.

---

## Tester Edge-Case Tests Added (13 tests)

New file: `tests/FIX-014/test_fix014_edge_cases.py`

| Test | Category | Result |
|---|---|---|
| `test_get_display_version_fallback_when_package_not_installed` | Unit | PASS |
| `test_get_display_version_returns_non_empty_string` | Unit | PASS |
| `test_config_version_is_semver` | Unit | PASS |
| `test_pyproject_version_is_semver` | Unit | PASS |
| `test_setup_iss_version_is_semver` | Unit | PASS |
| `test_build_dmg_version_is_semver` | Unit | PASS |
| `test_build_appimage_version_is_semver` | Unit | PASS |
| `test_no_stale_version_in_config_py` | Unit | PASS |
| `test_no_stale_version_in_pyproject` | Unit | PASS |
| `test_no_stale_version_in_setup_iss` | Unit | PASS |
| `test_no_stale_version_in_build_dmg` | Unit | PASS |
| `test_no_stale_version_in_build_appimage` | Unit | PASS |
| `test_no_stale_version_across_launcher_python_sources` | Unit | PASS |

Rationale:
- **`get_display_version()` fallback:** The function falls back to the `VERSION`
  constant when the package is not installed. Confirming the fallback path returns
  `"1.0.1"` is critical since the egg-info generated metadata may lag behind pyproject.toml.
- **Semver format:** Validates all 5 version strings are `X.Y.Z` (future regression
  guard if someone accidentally introduces a non-semver string).
- **Broad stale-version grep:** Per-file and whole-`src/launcher/` scans guarantee
  no `1.0.0` survived elsewhere (e.g. in comments, string literals, or future files).

---

## Full Regression Run

| Run | Passed | Skipped | Failed | Notes |
|---|---|---|---|---|
| Developer (pre-handoff) | 1946 | 29 | 1 | Pre-existing INS-005 failure |
| Tester (FIX-014 suite) | 25 | 0 | 0 | 12 Developer + 13 Tester edge-cases |
| Tester (full suite) | 1959 | 29 | 1 | Same pre-existing INS-005 failure |

**Pre-existing failure:** `tests/INS-005/test_ins005_edge_cases.py::TestShortcutsAndUninstaller::test_uninstall_delete_type_is_filesandirs`
— The test expects `Type: filesandirs` but `setup.iss` uses `Type: filesandordirs`.
This bug predates FIX-014 and is unrelated to the version bump.

---

## Security Observations

No security implications. This WP changes only version string constants in source
files and build scripts. No logic, user input handling, or network code was modified.

---

## Verdict

**PASS.** All 5 version locations correctly read `"1.0.1"`. All 25 FIX-014 tests
pass. Full regression suite shows no new failures. WP set to `Done`.
