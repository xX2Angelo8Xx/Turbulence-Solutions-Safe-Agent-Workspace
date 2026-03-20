# Dev Log — FIX-061: Bump version to 3.1.0

## Status
In Progress → Review

## Assigned To
Developer Agent

## Date
2026-03-20

## Summary
Bumped version string from 3.0.3 to 3.1.0 in all 5 canonical locations.

## Files Changed
1. `src/launcher/config.py` — VERSION constant: "3.0.3" → "3.1.0"
2. `pyproject.toml` — version field: "3.0.3" → "3.1.0"
3. `src/installer/windows/setup.iss` — MyAppVersion: "3.0.3" → "3.1.0"
4. `src/installer/macos/build_dmg.sh` — APP_VERSION: "3.0.3" → "3.1.0"
5. `src/installer/linux/build_appimage.sh` — APP_VERSION: "3.0.3" → "3.1.0"

## Tests Written
- `tests/FIX-061/__init__.py`
- `tests/FIX-061/test_fix061.py` — 5 tests, one per version location, using CURRENT_VERSION from `tests/shared/version_utils.py`

## Test Results
All 5 tests pass.

## Decisions
- Followed the same pattern as FIX-058 (and other prior version bumps).
- Tests use `CURRENT_VERSION` from `tests/shared/version_utils.py` — no hardcoded version strings in assertions.

## Known Limitations
None.
