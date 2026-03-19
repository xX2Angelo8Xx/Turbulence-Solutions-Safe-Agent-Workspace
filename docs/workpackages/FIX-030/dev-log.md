# FIX-030 Dev Log — Bump Version to 2.0.1

**WP ID:** FIX-030  
**Branch:** fix/FIX-030-version-bump  
**Assigned To:** Developer Agent  
**Date:** 2026-03-17  
**Linked User Story:** US-025  
**Status:** Review  

---

## Summary

Updated the version string from `2.0.0` to `2.0.1` in all 5 required locations.
This is the macOS code signing hotfix release for BUG-061, following the same pattern as
FIX-014 (→1.0.1), FIX-017 (→1.0.2), FIX-019 (→1.0.3), and FIX-020 (→2.0.0).

---

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/config.py` | `VERSION: str = "2.0.0"` → `"2.0.1"` |
| `pyproject.toml` | `version = "2.0.0"` → `"2.0.1"` |
| `src/installer/windows/setup.iss` | `#define MyAppVersion "2.0.0"` → `"2.0.1"` |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION="2.0.0"` → `"2.0.1"` |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION="2.0.0"` → `"2.0.1"` |

---

## Tests Written

- `tests/FIX-030/test_fix030_version_bump.py` — 6 tests verifying:
  1. `config.py` VERSION constant is `2.0.1`
  2. `pyproject.toml` version field is `2.0.1`
  3. `setup.iss` MyAppVersion is `2.0.1`
  4. `build_dmg.sh` APP_VERSION is `2.0.1`
  5. `build_appimage.sh` APP_VERSION is `2.0.1`
  6. None of the 5 files contains the old version `2.0.0` in version-assignment lines

---

## Test Results

All 6 FIX-030 tests pass. See `docs/test-results/test-results.csv` (TST-1774).

---

## Decisions

- Bumped only the 5 locations specified in the WP. No other files modified.
- Version lines that reference `2.0.0` in comments/docs are not version-assignment lines and are intentionally not changed (they describe the previous release).
- Followed the exact same pattern as FIX-020 (`test_fix020_version_bump.py`).
