# FIX-030 Test Report — Bump Version to 2.0.1

**WP ID:** FIX-030  
**Tester:** Tester Agent  
**Date:** 2026-03-17  
**Branch:** fix/FIX-030-version-bump  
**Verdict:** ✅ PASS (Iteration 2)  

---

## 1. Code Review Summary

All 5 version-file changes are correct:

| File | Expected | Actual | Result |
|------|----------|--------|--------|
| `src/launcher/config.py` | `VERSION = "2.0.1"` | `VERSION = "2.0.1"` | ✅ |
| `pyproject.toml` | `version = "2.0.1"` | `version = "2.0.1"` | ✅ |
| `src/installer/windows/setup.iss` | `#define MyAppVersion "2.0.1"` | `#define MyAppVersion "2.0.1"` | ✅ |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION="2.0.1"` | `APP_VERSION="2.0.1"` | ✅ |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION="2.0.1"` | `APP_VERSION="2.0.1"` | ✅ |

All version strings are valid semver (N.N.N), cross-consistent across all 5 locations, and free of BOM/trailing whitespace.

---

## 2. Tests Written

**Developer (6 tests):** `tests/FIX-030/test_fix030_version_bump.py`  
**Tester (11 edge-case tests):** `tests/FIX-030/test_fix030_tester_edge_cases.py`  
**Total FIX-030 suite: 17 tests**

Tester edge-case tests cover:
- Semver format validation (N.N.N regex) for each of the 5 files
- Cross-file consistency (all 5 sources agree on the same string)
- Strict bump verification (2.0.1 > 2.0.0 as version tuples)
- Trailing whitespace on version assignment lines
- BOM absence across all 5 files
- pyproject.toml version exactly matches config.py VERSION

**FIX-030 suite result: 17/17 PASS** ✅

---

## 3. Full Regression Suite

**Command:** `.venv\Scripts\python -m pytest tests/ -q --tb=no`  
**Result:** ❌ **41 failed, 3290 passed, 29 skipped, 1 xfailed**

### 3a. Pre-existing failures (unchanged from FIX-029 baseline)

These failures pre-date FIX-030 and are not caused by it:

| Test | Pre-existing Cause |
|------|-------------------|
| `tests/FIX-009/test_fix009_edge_cases.py::test_tst_ids_sequential_no_gaps_in_renumbered_range` | TST-ID gap 1662–1764 created by FIX-022 |
| `tests/FIX-009/test_fix009_no_duplicate_tst_ids.py::test_no_duplicate_tst_ids` | Duplicate TST-1557 and TST-599 predate FIX-030 |
| `tests/INS-005/test_ins005_edge_cases.py::TestShortcutsAndUninstaller::test_uninstall_delete_type_is_filesandirs` | BUG-045 (known, pre-existing) |

### 3b. NEW regressions introduced by FIX-030 — ❌ 38 tests

FIX-020 updated all version-snapshot tests from their original target versions to hardcode `"2.0.0"`. FIX-030 bumped the version to `"2.0.1"`, causing all 38 tests that assert `"2.0.0"` to fail.

**Affected test files and failure count:**

| Test File | Failures | Tests Checking For |
|-----------|----------|--------------------|
| `tests/FIX-010/test_fix010_cicd_pipeline.py` | 3 | `"2.0.0"` in setup.iss / build_dmg.sh / build_appimage.sh |
| `tests/FIX-014/test_fix014_version_bump.py` | 7 | `EXPECTED_VERSION = "2.0.0"` |
| `tests/FIX-014/test_fix014_edge_cases.py` | 1 | `get_display_version()` fallback `"2.0.0"` |
| `tests/FIX-017/test_fix017_version_bump.py` | 7 | `EXPECTED_VERSION = "2.0.0"` |
| `tests/FIX-019/test_fix019_version_bump.py` | 7 | `EXPECTED_VERSION = "2.0.0"` |
| `tests/FIX-019/test_fix019_edge_cases.py` | 3 | patch=0, display version `"2.0.0"`, tag `"v2.0.0"` |
| `tests/FIX-020/test_fix020_version_bump.py` | 5 | `EXPECTED_VERSION = "2.0.0"` (same WP) |
| `tests/FIX-020/test_fix020_edge_cases.py` | 2 | patch component=0, importable version `"2.0.0"` |
| `tests/INS-005/test_ins005_setup_iss.py` | 1 | `'MyAppVersion "2.0.0"'` |
| `tests/INS-006/test_ins006_build_dmg.py` | 1 | `APP_VERSION="2.0.0"` |
| `tests/INS-007/test_ins007_build_appimage.py` | 1 | `APP_VERSION="2.0.0"` |
| **Total** | **38** | |

Reference counts from the previous baseline:
- FIX-029 tester: **3307 pass / 7 fail** (version = 2.0.0 — all snapshot tests passed)
- FIX-030 Tester run: **3290 pass / 41 fail** (version = 2.0.1 — 38 snapshot tests fail, 3 pre-existing)

---

## 4. Developer Log Review

| Item | Status |
|------|--------|
| `docs/workpackages/FIX-030/dev-log.md` exists and is non-empty | ✅ |
| All 5 file changes described and correct | ✅ |
| 6 developer tests written and linked | ✅ |
| Dev-log references `TST-1772` for test results | ❌ Should be `TST-1774` (TST-1772 is a FIX-029 entry) |
| Full suite regression result logged | ❌ Missing — developer only ran and logged FIX-030 tests, not the full suite |

---

## 5. Verdict (Iteration 1): FAIL

**(See Iteration 2 below for final outcome.)**

Developer was returned the WP with the following TODOs:
- Update all 38 stale version-snapshot tests across 12 files from `"2.0.0"` to `"2.0.1"`.

---

## 6. Iteration 2 — Re-Review (2026-03-17)

**Developer fix:** Updated `EXPECTED_VERSION` constant (or direct assert value) to `"2.0.1"` in all 12 affected test files (38 tests total).

### 6a. Spot-check of fixed test files

| File | Key Change | Verified |
|------|-----------|---------|
| `tests/FIX-014/test_fix014_version_bump.py` | `EXPECTED_VERSION = "2.0.1"` | ✅ |
| `tests/FIX-017/test_fix017_version_bump.py` | `EXPECTED_VERSION = "2.0.1"` | ✅ |
| `tests/FIX-019/test_fix019_version_bump.py` | `EXPECTED_VERSION = "2.0.1"` | ✅ |
| `tests/FIX-019/test_fix019_edge_cases.py` | `EXPECTED_VERSION = "2.0.1"` | ✅ |
| `tests/FIX-020/test_fix020_version_bump.py` | `EXPECTED_VERSION = "2.0.1"` | ✅ |
| `tests/FIX-020/test_fix020_edge_cases.py` | `EXPECTED_VERSION = "2.0.1"` | ✅ |
| `tests/FIX-014/test_fix014_edge_cases.py` | `EXPECTED_VERSION = "2.0.1"` | ✅ |
| `tests/FIX-010/test_fix010_cicd_pipeline.py` | `'MyAppVersion "2.0.1"'`; `'APP_VERSION="2.0.1"'` | ✅ |
| `tests/INS-005/test_ins005_setup_iss.py` | `'MyAppVersion "2.0.1"'` | ✅ |
| `tests/INS-006/test_ins006_build_dmg.py` | `"2.0.1"` | ✅ |
| `tests/INS-007/test_ins007_build_appimage.py` | `"2.0.1"` | ✅ |

### 6b. Source version locations re-verified

| File | Value | Status |
|------|-------|--------|
| `src/launcher/config.py` | `VERSION: str = "2.0.1"` | ✅ |
| `pyproject.toml` | `version = "2.0.1"` | ✅ |
| `src/installer/windows/setup.iss` | `#define MyAppVersion "2.0.1"` | ✅ |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION="2.0.1"` | ✅ |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION="2.0.1"` | ✅ |

### 6c. Full Regression Suite — Iteration 2

**Command:** `.venv\Scripts\python -m pytest tests/ -q --tb=short`  
**Result:** ✅ **3 failed (all pre-existing), 3328 passed, 29 skipped, 1 xfailed**  
**TST logged:** TST-1777

| Failure | Pre-existing? |
|---------|--------------|
| `FIX-009::test_tst_ids_sequential_no_gaps_in_renumbered_range` | ✅ Pre-existing |
| `FIX-009::test_no_duplicate_tst_ids` | ✅ Pre-existing |
| `INS-005::test_uninstall_delete_type_is_filesandirs` | ✅ Pre-existing (BUG-045) |

All 38 version-snapshot regressions are resolved. No new failures introduced.

---

## 7. Final Verdict: ✅ PASS

### Reason

38 tests that passed before FIX-030 now fail. The root cause is that FIX-020 updated all old version-snapshot tests throughout the codebase to hardcode `"2.0.0"`. FIX-030 correctly bumped to `"2.0.1"`, but did not update those old tests accordingly. This is identical to what FIX-020 did when it bumped to `"2.0.0"` — it updated all tests hardcoded to the previous version. FIX-030 must do the same.

This follows the established precedent: every version bump WP is responsible for updating all old hardcoded version assertions so that the full test suite continues to pass.

### Testing Protocol Reference

> "DO NOT approve work that fails any existing test." — testing-protocol.md

---

## 6. Required Actions for Developer (Resubmit Checklist)

### TODO-1: Update tests hardcoding `"2.0.0"` → `"2.0.1"`

Update `EXPECTED_VERSION`, assertion strings, and assertion messages in all files listed below.
**IMPORTANT:** Change only the version string (e.g., `"2.0.0"` → `"2.0.1"`, `v2.0.0` → `v2.0.1`). Do NOT restructure the tests.

1. **`tests/FIX-010/test_fix010_cicd_pipeline.py`**  
   - `test_setup_iss_version_is_1_0_0`: change `'MyAppVersion "2.0.0"'` → `"2.0.1"` and update docstring/message  
   - `test_build_dmg_version_is_1_0_0`: change `'APP_VERSION="2.0.0"'` → `"2.0.1"` and update docstring/message  
   - `test_build_appimage_version_is_1_0_0`: change `'APP_VERSION="2.0.0"'` → `"2.0.1"` and update docstring/message  

2. **`tests/FIX-014/test_fix014_version_bump.py`**  
   - Change `EXPECTED_VERSION = "2.0.0"` → `"2.0.1"` (all 7 tests in this file inherit the constant)  

3. **`tests/FIX-014/test_fix014_edge_cases.py`**  
   - Update the `get_display_version()` fallback assertion from `"2.0.0"` → `"2.0.1"`  

4. **`tests/FIX-017/test_fix017_version_bump.py`**  
   - Change `EXPECTED_VERSION = "2.0.0"` → `"2.0.1"`  

5. **`tests/FIX-019/test_fix019_version_bump.py`**  
   - Change `EXPECTED_VERSION = "2.0.0"` → `"2.0.1"`  

6. **`tests/FIX-019/test_fix019_edge_cases.py`**  
   - `test_new_version_major_incremented_by_one`: update `"patch version must be reset to 0"` logic for new v2.0.1 (patch=1, not 0 — this test needs its assertion corrected for 2.0.1)  
   - `test_get_display_version_fallback_returns_expected`: change `"2.0.0"` → `"2.0.1"`  
   - `test_version_matches_expected_tag`: change `"v2.0.0"` → `"v2.0.1"`  

7. **`tests/FIX-020/test_fix020_version_bump.py`**  
   - Change `EXPECTED_VERSION = "2.0.0"` → `"2.0.1"`  

8. **`tests/FIX-020/test_fix020_edge_cases.py`**  
   - `test_version_patch_component_is_0`: update to expect patch=1 (since 2.0.**1**), or change assertion to verify patch >= 0  
   - `test_config_module_version_importable`: change expected from `"2.0.0"` → `"2.0.1"`  

9. **`tests/INS-005/test_ins005_setup_iss.py`**  
   - `test_app_version`: change `'MyAppVersion "2.0.0"'` → `'MyAppVersion "2.0.1"'`  

10. **`tests/INS-006/test_ins006_build_dmg.py`**  
    - `test_app_version`: change `"2.0.0"` → `"2.0.1"` in the assertion  

11. **`tests/INS-007/test_ins007_build_appimage.py`**  
    - `test_app_version_embedded`: change `"2.0.0"` → `"2.0.1"` in the assertion  

### TODO-2: Fix dev-log TST-ID reference

In `docs/workpackages/FIX-030/dev-log.md`, update the test result reference from `TST-1772` to `TST-1774`.

### TODO-3: Run full test suite before resubmitting

Run `.venv\Scripts\python -m pytest tests/ -q --tb=no` and verify the only failures are the known pre-existing ones:
- `tests/FIX-009` encoding-corruption tests (pre-existing)
- `tests/FIX-009/test_fix009_edge_cases.py::test_tst_ids_sequential_no_gaps_in_renumbered_range` (pre-existing gap)
- `tests/FIX-009/test_fix009_no_duplicate_tst_ids.py::test_no_duplicate_tst_ids` (pre-existing duplicates)
- `tests/INS-005/test_ins005_edge_cases.py::TestShortcutsAndUninstaller::test_uninstall_delete_type_is_filesandirs` (BUG-045)

Log this full-suite result in `docs/test-results/test-results.csv`.

---

## 7. Test Results Logged

See `docs/test-results/test-results.csv`:
- `TST-1775` — FIX-030 tester edge-case suite (17 tests all pass)
- `TST-1776` — FIX-030 full suite regression (41 failed / 38 new / 3 pre-existing)
