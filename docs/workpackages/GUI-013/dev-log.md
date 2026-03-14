# Dev Log — GUI-013

**Developer:** Developer Agent
**Date started:** 2026-03-14
**Iteration:** 1

## Objective
Add the TS-Logo (TS-Logo.png at repo root) to the launcher GUI: display it as a header image inside the window, set it as the application icon (window icon via `iconphoto`), bundle it in the PyInstaller spec, and add the Pillow dependency.

## Implementation Summary

### `src/launcher/config.py`
- Added `LOGO_PATH` constant with dual-mode resolution:
  - PyInstaller bundle: `Path(sys._MEIPASS) / "TS-Logo.png"`
  - Development mode: `Path(__file__).resolve().parent.parent.parent / "TS-Logo.png"` (repo root)

### `src/launcher/gui/app.py`
- Imported `LOGO_PATH` from `launcher.config`.
- In `_build_ui()`: Added a logo header at row 0 using `CTkImage` and `CTkLabel` (colspan=3, padx=20, pady=(12,4)). All subsequent grid rows shifted by +1 (was rows 0–8, now rows 1–9).
- In `__init__()`: Added post-build icon setup — opens `TS-Logo.png` with Pillow, creates a `PhotoImage`, calls `self._window.iconphoto(True, self._icon_photo)`, and stores the reference as `self._icon_photo` to prevent GC.
- Both logo operations are wrapped in a `try/except Exception: pass` so the app runs even if Pillow is missing or the image file is absent.

### `launcher.spec`
- Added `(os.path.join(SPECPATH, 'TS-Logo.png'), '.')` to the `datas` list so the logo is bundled in the PyInstaller output root.
- Set `icon=os.path.join(SPECPATH, 'TS-Logo.png')` in the `EXE` block for the desktop/taskbar icon.

### `pyproject.toml`
- Added `Pillow>=10.0.0` to `[project] dependencies`.

### Row shift fixes (adjusted by previous developer)
The following test files were updated to account for grid row numbers shifting +1 due to the new logo row:
- `tests/FIX-007/test_fix007_mock_pattern.py` — row expectations updated
- `tests/GUI-004/test_gui004_destination_validation.py` — row expectations updated
- `tests/GUI-012/test_gui012_spacing.py` — window height updated from 440 to 590 (logo adds height) and row expectations updated

### Encoding fix (applied during finalization)
`docs/test-results/test-results.csv` was saved as Windows-1252 (CP1252) which caused 6 FIX-009 regression failures. Converted back to UTF-8.

## Files Changed
- `src/launcher/config.py` — LOGO_PATH constant added
- `src/launcher/gui/app.py` — logo header row + window iconphoto + grid row shifts
- `launcher.spec` — TS-Logo.png in datas + icon= set
- `pyproject.toml` — Pillow dependency added
- `tests/FIX-007/test_fix007_mock_pattern.py` — row number adjustments
- `tests/GUI-004/test_gui004_destination_validation.py` — row number adjustments
- `tests/GUI-012/test_gui012_spacing.py` — row number and height adjustments
- `docs/test-results/test-results.csv` — re-encoded to UTF-8

## Tests Written
- `tests/GUI-013/test_gui013_logo.py`
  - `test_logo_path_dev_mode_points_to_repo_root` — LOGO_PATH resolves to repo root in dev mode
  - `test_logo_path_dev_mode_file_exists` — TS-Logo.png exists at repo root
  - `test_logo_path_meipass_mode` — LOGO_PATH resolves to _MEIPASS/TS-Logo.png in bundle mode
  - `test_spec_datas_includes_ts_logo` — launcher.spec datas list contains TS-Logo.png
  - `test_spec_datas_bundles_logo_to_root` — launcher.spec places image in bundle root
  - `test_spec_exe_has_icon_parameter` — launcher.spec EXE block has icon= parameter
  - `test_app_init_sets_icon_photo` — App.__init__ calls iconphoto(True, photo) and stores _icon_photo
  - `test_app_build_ui_creates_logo_label` — App._build_ui() creates logo_label attribute

## Test Results
8/8 GUI-013 tests pass. Full suite: 1897 passed / 29 skipped / 1 pre-existing fail (INS-005 test_uninstall_delete_type_is_filesandirs — introduced by FIX-010 tag v1.0.0 commit, unrelated to this WP).

## Known Limitations
- `icon=` in launcher.spec points to a `.png` file. On Windows, PyInstaller typically expects a `.ico` file for the best icon quality. The PNG will be auto-converted by PyInstaller but may result in lower quality icons. Converting to `.ico` is deferred as a future improvement.
- The logo is hidden at runtime if Pillow is not installed or the image file is missing (silent fallback).
