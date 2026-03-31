# Dev Log — FIX-090: Bump Version to 3.3.1

## WP Details
- **ID:** FIX-090
- **Type:** FIX
- **Title:** Bump Version to 3.3.1
- **Status:** In Progress
- **Assigned To:** Developer Agent
- **Branch:** FIX-090/bump-version-3.3.1

---

## Implementation Plan

Update the version string from `3.3.0` to `3.3.1` in all 5 locations:
1. `src/launcher/config.py` — `VERSION` constant
2. `pyproject.toml` — `version` field
3. `src/installer/windows/setup.iss` — `#define MyAppVersion`
4. `src/installer/macos/build_dmg.sh` — `APP_VERSION`
5. `src/installer/linux/build_appimage.sh` — `APP_VERSION`

---

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/config.py` | `VERSION = "3.3.0"` → `VERSION = "3.3.1"` |
| `pyproject.toml` | `version = "3.3.0"` → `version = "3.3.1"` |
| `src/installer/windows/setup.iss` | `#define MyAppVersion "3.3.0"` → `#define MyAppVersion "3.3.1"` |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION="3.3.0"` → `APP_VERSION="3.3.1"` |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION="3.3.0"` → `APP_VERSION="3.3.1"` |

---

## Tests Written

- `tests/FIX-090/test_fix090_version_bump.py`
  - Verifies `src/launcher/config.py` contains `VERSION = "3.3.1"`
  - Verifies `pyproject.toml` contains `version = "3.3.1"`
  - Verifies `src/installer/windows/setup.iss` contains `#define MyAppVersion "3.3.1"`
  - Verifies `src/installer/macos/build_dmg.sh` contains `APP_VERSION="3.3.1"`
  - Verifies `src/installer/linux/build_appimage.sh` contains `APP_VERSION="3.3.1"`

---

## Test Results

- All 5 version bump tests passed.

---

## Summary

Version incremented from 3.3.0 to 3.3.1 in all required locations. No logic or behavioral changes; purely a version string update.
