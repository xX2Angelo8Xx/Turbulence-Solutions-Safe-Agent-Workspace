# Dev Log — FIX-019: Bump Version to 1.0.3

| Field | Value |
|---|---|
| WP ID | FIX-019 |
| Status | Review |
| Assigned To | Developer Agent |
| Branch | FIX-018/auto-update-private-repo |
| Date | 2026-03-16 |

---

## Summary

Version bump from `1.0.2` to `1.0.3` across all 5 canonical version locations.
This is the release version for BUG-046 (GitHub auth for private repo auto-update via FIX-018).

---

## Files Changed

| File | Change |
|---|---|
| `src/launcher/config.py` | `VERSION: str = "1.0.2"` → `"1.0.3"` |
| `pyproject.toml` | `version = "1.0.2"` → `"1.0.3"` |
| `src/installer/windows/setup.iss` | `#define MyAppVersion "1.0.2"` → `"1.0.3"` |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION="1.0.2"` → `"1.0.3"` |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION="1.0.2"` → `"1.0.3"` |

## Existing Tests Updated

The following permanent test files contained hard-coded `"1.0.2"` assertions
that serve as consistency guards for the *current* version. Updated to `"1.0.3"`:

| File | Lines Updated |
|---|---|
| `tests/INS-005/test_ins005_setup_iss.py` | `test_app_version` |
| `tests/INS-006/test_ins006_build_dmg.py` | `test_app_version` |
| `tests/INS-007/test_ins007_build_appimage.py` | `test_app_version_embedded` |
| `tests/FIX-010/test_fix010_cicd_pipeline.py` | `test_setup_iss_version_is_1_0_0`, `test_build_dmg_version_is_1_0_0`, `test_build_appimage_version_is_1_0_0` |
| `tests/FIX-014/test_fix014_version_bump.py` | `EXPECTED_VERSION` constant |
| `tests/FIX-017/test_fix017_version_bump.py` | `EXPECTED_VERSION` constant and all negative-test old-version strings updated to reference `1.0.2` as the old version |
| `tests/FIX-017/test_fix017_edge_cases.py` | `EXPECTED_VERSION`, `PREVIOUS_VERSION`, `SKIP_ONE_VERSION` constants |

---

## New Tests

`tests/FIX-019/test_fix019_version_bump.py` — 12 tests covering:

1. `TestConfigVersion` — `config.py` VERSION constant and source text
2. `TestPyprojectVersion` — `pyproject.toml` version field; no old version remains
3. `TestSetupIssVersion` — `setup.iss` MyAppVersion; no old version remains
4. `TestBuildDmgVersion` — `build_dmg.sh` APP_VERSION; no old version remains
5. `TestBuildAppimageVersion` — `build_appimage.sh` APP_VERSION; no old version remains
6. `TestVersionConsistency` — all 5 versions are identical; all equal `"1.0.3"`

---

## Test Results

- FIX-019 suite: **12/12 passed** (2026-03-16, Windows 11 + Python 3.11)
- Full regression suite: see test-results.csv for final run entry

---

## Known Limitations

None. Pure version string update — no logic changes.
