# FIX-075 — Dev Log: Fix launcher window title to "TS - Safe Agent Environment"

## WP Overview
- **WP ID:** FIX-075
- **Type:** FIX
- **Branch:** FIX-075/window-title
- **Linked Bug:** BUG-117
- **User Story:** US-053

## Problem
`APP_NAME` in `src/launcher/config.py` was set to `"Turbulence Solutions Launcher"`.
The window title in `src/launcher/gui/app.py` calls `self._window.title(APP_NAME)`, so
the incorrect string propagated directly to the OS window title bar.

## Implementation

### Files Changed
| File | Change |
|------|--------|
| `src/launcher/config.py` | Changed `APP_NAME` from `"Turbulence Solutions Launcher"` to `"TS - Safe Agent Environment"` |
| `docs/bugs/bugs.csv` | Closed BUG-117 (status → Fixed) |
| `docs/workpackages/workpackages.csv` | Set FIX-075 status to In Progress → Review |

### Approach
Single-line constant change. `APP_NAME` is the sole source of truth for the
application window title. `src/launcher/gui/app.py` line 93 already references
`APP_NAME` directly, so no further changes are needed in the GUI code.

Installer shell scripts (`build_dmg.sh`, `build_appimage.sh`) define their own
local `APP_NAME` shell variable for packaging purposes — these are separate from
the Python constant and are out of scope for this WP.

## Tests Written
- `tests/FIX-075/test_fix075_window_title.py`
  - `test_app_name_value` — asserts `APP_NAME == "TS - Safe Agent Environment"`
  - `test_app_name_not_old_value` — regression: asserts old string is not present
  - `test_window_title_uses_app_name` — asserts `app.py` sets window title to `APP_NAME`
  - `test_no_old_title_in_config` — asserts old string absent from config source

## Test Results
All 4 tests passed. See `docs/test-results/test-results.csv`.

## Known Limitations
None.

## Iteration History
| Date | Author | Notes |
|------|--------|-------|
| 2026-03-25 | Developer Agent | Initial implementation |
