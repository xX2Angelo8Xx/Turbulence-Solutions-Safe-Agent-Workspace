# Dev Log — FIX-014: Bump Version to 1.0.1

| Field | Value |
|---|---|
| WP ID | FIX-014 |
| Status | In Progress |
| Assigned To | Developer Agent |
| Branch | fix-014-version-bump |
| Date | 2026-03-14 |

---

## Summary

Version bump from `1.0.0` to `1.0.1` across all 5 canonical version locations.
This is the hotfix release version for BUG-042 (PyInstaller template path resolution)
and UI improvements (GUI-013, GUI-014).

---

## Files Changed

| File | Change |
|---|---|
| `src/launcher/config.py` | `VERSION: str = "1.0.0"` → `"1.0.1"` |
| `pyproject.toml` | `version = "1.0.0"` → `"1.0.1"` |
| `src/installer/windows/setup.iss` | `#define MyAppVersion "1.0.0"` → `"1.0.1"` |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION="1.0.0"` → `"1.0.1"` |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION="1.0.0"` → `"1.0.1"` |

## Existing Tests Updated

The following permanent test files contained hard-coded `"1.0.0"` assertions
that now serve as consistency guards for the *current* version. Updated to `"1.0.1"`:

| File | Lines Updated |
|---|---|
| `tests/INS-005/test_ins005_setup_iss.py` | `test_app_version` |
| `tests/INS-006/test_ins006_build_dmg.py` | `test_app_version` |
| `tests/INS-007/test_ins007_build_appimage.py` | `test_app_version_embedded` |
| `tests/FIX-010/test_fix010_cicd_pipeline.py` | `test_setup_iss_version_is_1_0_0`, `test_build_dmg_version_is_1_0_0`, `test_build_appimage_version_is_1_0_0` |

---

## New Tests

`tests/FIX-014/test_fix014_version_bump.py` — 12 tests covering:

1. `TestConfigVersion` — `config.py` VERSION constant and source text
2. `TestPyprojectVersion` — `pyproject.toml` version field; no old version remains
3. `TestSetupIssVersion` — `setup.iss` MyAppVersion; no old version remains
4. `TestBuildDmgVersion` — `build_dmg.sh` APP_VERSION; no old version remains
5. `TestBuildAppimageVersion` — `build_appimage.sh` APP_VERSION; no old version remains
6. `TestVersionConsistency` — all 5 versions are identical; all equal `"1.0.1"`

---

## Test Results

- FIX-014 suite: **12/12 passed** (2026-03-14, Windows 11 + Python 3.11)
- Full regression suite: **1946 passed, 29 skipped, 1 pre-existing failure**
  - Pre-existing failure: `INS-005/test_ins005_edge_cases.py::test_uninstall_delete_type_is_filesandirs` (unrelated to this WP)

---

## Known Limitations

None. Pure version string update — no logic changes.
