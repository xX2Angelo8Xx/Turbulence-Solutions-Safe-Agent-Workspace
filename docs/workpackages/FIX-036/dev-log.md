# Dev Log — FIX-036: Bump version to V2.1.0

**WP ID:** FIX-036  
**Branch:** fix-036  
**Assigned To:** Developer Agent  
**Date:** 2026-03-18  
**Status:** Review

---

## Summary

Updated all 5 canonical version string locations from `2.0.1` to `2.1.0` and
added the FIX-036 entry to `docs/architecture.md`.

---

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/config.py` | `VERSION` constant: `"2.0.1"` → `"2.1.0"` |
| `pyproject.toml` | `version`: `"2.0.1"` → `"2.1.0"` |
| `src/installer/windows/setup.iss` | `MyAppVersion`: `"2.0.1"` → `"2.1.0"` |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION`: `"2.0.1"` → `"2.1.0"` |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION`: `"2.0.1"` → `"2.1.0"` |
| `docs/architecture.md` | Added `FIX-036` entry to tests directory listing |
| `docs/workpackages/workpackages.csv` | FIX-036 status: `Open` → `Review` |
| `docs/test-results/test-results.csv` | Added TST-1810 run record |

---

## Tests Written

**Location:** `tests/FIX-036/test_fix036_version_consistency.py`

| Test | Description |
|------|-------------|
| `test_config_py_version` | Verifies `VERSION` in config.py is `"2.1.0"` |
| `test_pyproject_toml_version` | Verifies `version` in pyproject.toml is `"2.1.0"` |
| `test_setup_iss_version` | Verifies `MyAppVersion` in setup.iss is `"2.1.0"` |
| `test_build_dmg_version` | Verifies `APP_VERSION` in build_dmg.sh is `"2.1.0"` |
| `test_build_appimage_version` | Verifies `APP_VERSION` in build_appimage.sh is `"2.1.0"` |
| `test_all_versions_identical` | Cross-checks all 5 locations are identical |
| `test_architecture_md_references_new_version` | Verifies architecture.md contains FIX-036 and 2.1.0 |

**Test run result:** 7 passed / 0 failures (2026-03-18, Windows 11 + Python 3.11)

---

## Decisions

- Only the single-line version string in each file was modified; no other lines were touched.
- `docs/architecture.md` received a new FIX-036 directory entry in the tests listing.
- No new dependencies introduced.

---

## Known Limitations

None.
