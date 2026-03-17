# Test Report — FIX-020: Bump Version to 2.0.0

## Verdict: PASS

**Tester:** Tester Agent  
**Date:** 2026-03-17  
**Branch:** `FIX-020/bump-version-2.0.0`

---

## 1. Code Review

All 5 version locations confirmed updated to `"2.0.0"`:

| File | Field | Value |
|------|-------|-------|
| `src/launcher/config.py` | `VERSION: str` | `"2.0.0"` ✓ |
| `pyproject.toml` | `version` | `"2.0.0"` ✓ |
| `src/installer/windows/setup.iss` | `#define MyAppVersion` | `"2.0.0"` ✓ |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION` | `"2.0.0"` ✓ |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION` | `"2.0.0"` ✓ |

No logic, structure, or formatting changes outside the version string values — implementation is minimal and correct.

Regression test files updated in `tests/FIX-010/`, `tests/FIX-014/`, `tests/FIX-017/`, `tests/FIX-019/`, `tests/INS-005/`, `tests/INS-006/`, `tests/INS-007/` — all correctly reflect the new version.

---

## 2. Test Execution

### FIX-020 suite (developer + tester)
- **Run:** `pytest tests/FIX-020/ --tb=short -q`
- **Result:** 21 passed / 0 failures
- **Logged:** TST-1652

### Full regression suite
- **Run:** `pytest tests/ --tb=short -q`
- **Result:** 3156 passed / 2 pre-existing failures / 29 skipped / 1 xfailed
- **Logged:** TST-1653
- Pre-existing failures (not caused by FIX-020, unchanged from prior WPs):
  - `tests/FIX-009/test_fix009_no_duplicate_tst_ids.py` — TST-1557 duplicate (introduced by GUI-017)
  - `tests/INS-005/test_ins005_edge_cases.py::test_uninstall_delete_type_is_filesandirs` — BUG-045

---

## 3. Tester Edge-Case Tests Added

File: `tests/FIX-020/test_fix020_edge_cases.py` — 15 tests

| Test | Description |
|------|-------------|
| `test_config_py_version_is_semver` | VERSION in config.py matches `MAJOR.MINOR.PATCH` regex |
| `test_pyproject_toml_version_is_semver` | pyproject.toml version matches semver format |
| `test_setup_iss_version_is_semver` | setup.iss MyAppVersion matches semver format |
| `test_build_dmg_sh_version_is_semver` | build_dmg.sh APP_VERSION matches semver format |
| `test_build_appimage_sh_version_is_semver` | build_appimage.sh APP_VERSION matches semver format |
| `test_all_five_locations_are_consistent` | All 5 locations return the same version string |
| `test_version_major_component_is_2` | Major component is exactly 2 in all locations |
| `test_version_minor_component_is_0` | Minor component is 0 (reset on major bump) in all locations |
| `test_version_patch_component_is_0` | Patch component is 0 (reset on major bump) in all locations |
| `test_no_stale_version_in_config_py` | No stale 1.0.0/1.0.1/1.0.2/1.0.3 in VERSION line |
| `test_no_stale_version_in_pyproject_toml` | No stale versions in pyproject.toml version line |
| `test_no_stale_version_in_setup_iss` | No stale versions in MyAppVersion define |
| `test_no_stale_version_in_build_dmg_sh` | No stale versions in APP_VERSION assignment |
| `test_no_stale_version_in_build_appimage_sh` | No stale versions in APP_VERSION assignment |
| `test_config_module_version_importable` | config.py is importable as Python module; VERSION attribute returns `"2.0.0"` |

All 15 pass.

---

## 4. Security / Risk Analysis

- No attack surface changes — pure version string update.
- No new dependencies, no logic changes, no runtime risk.
- Build scripts are never executed during tests — file content is read-only.

---

## 5. Pre-Done Checklist

- [x] `docs/workpackages/FIX-020/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/FIX-020/test-report.md` written by Tester Agent
- [x] Test files exist in `tests/FIX-020/` (2 files, 21 tests)
- [x] All test runs logged in `docs/test-results/test-results.csv` (TST-1652, TST-1653)
- [x] `git add -A` staged
- [x] Commit: `FIX-020: Tester PASS`
- [x] Push: `git push origin FIX-020/bump-version-2.0.0`
