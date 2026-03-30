# FIX-085 — Fix python-path.txt corruption during in-app update

## Status
In Progress

## Assigned To
Developer Agent

## Summary
Diagnose and fix the root cause of python-path.txt being corrupted or overwritten with an invalid path
when the user updates the launcher via the GUI. Add a startup validation that auto-recovers the path
if it is missing, empty, or points to a non-existent executable. Fixes BUG-156.

## Root Cause Analysis
The Inno Setup `CurStepChanged(ssPostInstall)` writes `python-path.txt` with
`{app}\python-embed\python.exe`. The `{app}` variable correctly resolves to the new install
directory on a first install. However, during a silent update (`/SILENT`), `SaveStringToFile`
writes the path with **no newline and no verification** that the target file was created successfully.
More critically, if the old launcher process still holds the file or if any race condition occurs
between exit and installer execution, the write may succeed but the path it writes can differ
from the actual extraction location on some Windows configurations.

Additionally, the Inno Setup script lacked:
1. Any verification that `python-embed\python.exe` actually exists after writing.
2. Any logging of the written path for debugging.

The launcher itself had no self-healing logic — on startup it never checked whether
`python-path.txt` was valid, so a corrupted file from a previous update would persist
until the user manually clicked "Auto-detect" in Settings.

## Implementation

### 1. `src/launcher/core/shim_config.py` — `ensure_python_path_valid()`
Added a new public function that:
- Reads `python-path.txt`.
- Returns `True` immediately if the configured path exists.
- If missing/empty/invalid: attempts auto-recovery by searching for `python-embed/python.exe`
  relative to `sys.executable` (same logic used by `SettingsDialog._find_bundled_python()`).
- Writes the recovered path via `write_python_path()` if auto-detect succeeds.
- Returns `False` if auto-recovery also fails.

### 2. `src/launcher/gui/app.py` — startup validation
In `App.__init__()`, after the GUI is built, calls `ensure_python_path_valid()`.
If it returns `False`, shows a `messagebox.showwarning` directing the user to
Settings → Relocate Python Runtime.

### 3. `src/installer/windows/setup.iss` — improved post-install
The `CurStepChanged(ssPostInstall)` procedure now:
- Logs the path it is about to write (via `Log()`).
- Calls `SaveStringToFile` as before.
- Verifies that `python-embed\python.exe` actually exists at `{app}` after writing,
  and logs a warning if it does not.

## Files Changed
- `src/launcher/core/shim_config.py`
- `src/launcher/gui/app.py`
- `src/installer/windows/setup.iss`
- `tests/FIX-085/test_fix085_python_path_validation.py` (new)
- `docs/workpackages/FIX-085/dev-log.md` (this file)
- `docs/workpackages/workpackages.csv`
- `docs/bugs/bugs.csv`

## Tests Written
See `tests/FIX-085/test_fix085_python_path_validation.py`:
1. `test_valid_path_returns_true` — returns True for a valid existing path
2. `test_missing_file_auto_recovers` — auto-recovers when python-path.txt is absent
3. `test_empty_file_auto_recovers` — auto-recovers when python-path.txt is empty
4. `test_invalid_path_auto_recovers` — auto-recovers when path points to non-existent file
5. `test_no_bundled_python_returns_false` — returns False when auto-recovery also fails
6. `test_app_startup_calls_validation` — App.__init__ calls ensure_python_path_valid
7. `test_app_startup_warns_on_invalid_path` — warning shown when validation returns False
8. `test_inno_setup_writes_correct_path_format` — setup.iss contains correct path-writing logic

## Known Limitations
- The Inno Setup improvement only adds log verification; it cannot forcibly
  prevent a race condition at the OS level. The self-healing startup validation
  in the launcher is the primary fix.
- On macOS/Linux, `ensure_python_path_valid()` uses `_find_bundled_python_exe()`
  from `shim_config.py` which checks for `python3/python` in `python-embed/`.
