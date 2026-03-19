# SAF-034 Dev Log — Verify ts-python before workspace creation

## Status
In Progress → Review

## Summary
Added a `verify_ts_python()` function to `src/launcher/core/shim_config.py` that actually executes the ts-python shim to confirm it is functional. Added a pre-flight call to this function in `app.py`'s `_on_create_project()` so that workspace creation is aborted with a clear error dialog if the shim is misconfigured.

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/core/shim_config.py` | Added `verify_ts_python()` function |
| `src/launcher/gui/app.py` | Added `verify_ts_python` import and pre-flight check in `_on_create_project()` |
| `docs/workpackages/workpackages.csv` | Status updated to In Progress → Review |

## Implementation Details

### `verify_ts_python()` in shim_config.py
- Determines the shim executable path:
  - **Windows**: checks `get_shim_dir() / "ts-python.cmd"` first, then falls back to `shutil.which("ts-python.cmd")` and `shutil.which("ts-python")`
  - **Unix/macOS**: uses `shutil.which("ts-python")`
- Runs `[shim_exe, "-c", "import sys; print(sys.version)"]` via `subprocess.run` — **no `shell=True`** (security rule)
- 5-second timeout
- Returns `(True, version_string)` on success or `(False, error_message)` on failure
- Catches: `TimeoutExpired`, `FileNotFoundError`, `OSError`

### `_on_create_project()` in app.py
- Pre-flight check inserted right before `create_project()` is called
- On failure: shows `messagebox.showerror` with the standard user-friendly message from the WP spec plus technical details
- On failure: returns without creating the workspace

## Security Notes
- `shell=True` is never used — `subprocess.run` is called with a list of arguments
- No user-supplied input is passed to the subprocess command

## Tests Written
- `tests/SAF-034/test_saf034.py`
- 18 test cases covering: verify_ts_python success, various failure modes (shim not found, non-zero exit, timeout, FileNotFoundError, OSError), platform-specific path detection (Windows/Unix), app.py pre-flight integration (blocks creation on failure, allows creation on success, passes error message to dialog)

## Test Results
All 18 tests pass. No regressions in the existing suite.

## Date
2026-03-19
