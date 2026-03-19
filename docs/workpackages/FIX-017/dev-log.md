# Dev Log — FIX-017: Bump Version to 1.0.2

| Field | Value |
|---|---|
| WP ID | FIX-017 |
| Status | Review |
| Assigned To | Developer Agent |
| Branch | FIX-015/add-logo-fix-tracking |
| Date | 2026-03-16 |

---

## Summary

Version bump from `1.0.1` to `1.0.2` across all 5 canonical version locations.
This is the hotfix release version for BUG-043 (TS Logo aspect ratio fix via FIX-015)
and BUG-044 (Windows app icon .ico fix via FIX-016).

---

## Files Changed

| File | Change |
|---|---|
| `src/launcher/config.py` | `VERSION: str = "1.0.1"` → `"1.0.2"` |
| `pyproject.toml` | `version = "1.0.1"` → `"1.0.2"` |
| `src/installer/windows/setup.iss` | `#define MyAppVersion "1.0.1"` → `"1.0.2"` |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION="1.0.1"` → `"1.0.2"` |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION="1.0.1"` → `"1.0.2"` |

## Existing Tests Updated

The following permanent test files contained hard-coded `"1.0.1"` assertions
that serve as consistency guards for the *current* version. Updated to `"1.0.2"`:

| File | Lines Updated |
|---|---|
| `tests/INS-005/test_ins005_setup_iss.py` | `test_app_version` |
| `tests/INS-006/test_ins006_build_dmg.py` | `test_app_version` |
| `tests/INS-007/test_ins007_build_appimage.py` | `test_app_version_embedded` |
| `tests/FIX-010/test_fix010_cicd_pipeline.py` | `test_setup_iss_version_is_1_0_0`, `test_build_dmg_version_is_1_0_0`, `test_build_appimage_version_is_1_0_0` |
| `tests/FIX-014/test_fix014_version_bump.py` | `EXPECTED_VERSION` constant and all docstrings |
| `tests/FIX-014/test_fix014_edge_cases.py` | `EXPECTED_VERSION` constant |

---

## New Tests

`tests/FIX-017/test_fix017_version_bump.py` — 12 tests covering:

1. `TestConfigVersion` — `config.py` VERSION constant and source text
2. `TestPyprojectVersion` — `pyproject.toml` version field; no old version remains
3. `TestSetupIssVersion` — `setup.iss` MyAppVersion; no old version remains
4. `TestBuildDmgVersion` — `build_dmg.sh` APP_VERSION; no old version remains
5. `TestBuildAppimageVersion` — `build_appimage.sh` APP_VERSION; no old version remains
6. `TestVersionConsistency` — all 5 versions are identical; all equal `"1.0.2"`

---

## Test Results

- FIX-017 suite: **12/12 passed** (2026-03-16, Windows 11 + Python 3.11)
- Full regression suite: see test-results.csv for final run entry

---

## Known Limitations

None. Pure version string update — no logic changes.
