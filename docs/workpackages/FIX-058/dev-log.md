# FIX-058 Dev Log — Bump version to 3.0.3

## Status
In Progress → Review

## Assigned To
Developer Agent

## Date
2026-03-20

---

## Summary

Bumped version string from `3.0.2` to `3.0.3` in all 5 required locations to mark the release containing FIX-055, FIX-056, and FIX-057.

---

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/config.py` | `VERSION: str = "3.0.3"` |
| `pyproject.toml` | `version = "3.0.3"` |
| `src/installer/windows/setup.iss` | `#define MyAppVersion "3.0.3"` |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION="3.0.3"` |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION="3.0.3"` |
| `docs/workpackages/workpackages.csv` | Status set to `In Progress` / `Review` |

---

## Tests Written

- `tests/FIX-058/__init__.py`
- `tests/FIX-058/test_fix058.py`

Uses `CURRENT_VERSION` from `tests/shared/version_utils.py` (FIX-049 dynamic pattern) — no hardcoded version strings.

Tests verify all 5 files contain the current version string.

---

## Test Results

All 5 tests passed. See `docs/test-results/test-results.csv`.

---

## Notes

No code logic changes. Pure version-string bump only.
