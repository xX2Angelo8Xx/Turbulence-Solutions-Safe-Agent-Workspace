# Dev Log — FIX-126: Harden Python runtime path persistence

## Status
In Progress → Review

## WP Summary
This workpackage hardens Python runtime path persistence to address regression cases
where ts-python.cmd fails when python-path.txt is missing or corrupt between
launcher sessions (original issue previously reported and addressed in the runtime
path recovery work). Three improvements:

## ADRs Checked
No ADRs found in docs/decisions/index.jsonl related to shim, python-path, or runtime configuration.

## Implementation

### 1. ts-python.cmd — Self-healing fallback
**File:** `src/installer/shims/ts-python.cmd`

Added two fallback candidate paths after the normal python-path.txt read fails:
- `%ProgramFiles%\TurbulenceSolutions\python-embed\python.exe`
- `%LOCALAPPDATA%\Programs\TurbulenceSolutions\python-embed\python.exe`

If a candidate exists, it is written back to python-path.txt (auto-heal) and execution proceeds. Only if all fallbacks fail does the shim emit the deny JSON.

### 2. shim_config.py — CREATE_NO_WINDOW flag
**File:** `src/launcher/core/shim_config.py`

In `verify_ts_python()`, the `subprocess.run()` call now includes
`creationflags=subprocess.CREATE_NO_WINDOW` when `sys.platform == "win32"`.
This prevents a console window from flashing during project creation pre-flight.

### 3. app.py — Re-validate before every workspace creation
**File:** `src/launcher/gui/app.py`

Added a call to `ensure_python_path_valid()` inside `_on_create_project`'s
background `_create()` thread, before the `verify_ts_python()` call.
This ensures the python path is re-checked before every workspace creation,
not just at launcher startup.

## Files Changed
- `src/installer/shims/ts-python.cmd`
- `src/launcher/core/shim_config.py`
- `src/launcher/gui/app.py`
- `tests/FIX-126/test_fix126_python_path_hardening.py`
- `docs/workpackages/FIX-126/dev-log.md`
- `docs/workpackages/workpackages.jsonl`

## Tests Written
- `tests/FIX-126/test_fix126_python_path_hardening.py`
  - `test_shim_cmd_uses_python_path_when_valid` — shim works with valid python-path.txt
  - `test_shim_cmd_fallback_progfiles` — fallback to %ProgramFiles% path
  - `test_shim_cmd_fallback_localappdata_programs` — fallback to %LOCALAPPDATA%\Programs
  - `test_shim_cmd_deny_when_all_fail` — deny JSON when all paths fail
  - `test_shim_cmd_self_heal_writes_back` — healed path written back to python-path.txt
  - `test_verify_ts_python_no_window_flag_on_windows` — CREATE_NO_WINDOW in subprocess call
  - `test_verify_ts_python_no_window_flag_skipped_on_non_windows` — not added on non-Windows
  - `test_ensure_python_path_called_before_verify_in_create` — app calls ensure_python_path_valid before verify_ts_python in bg thread

## Known Limitations
- The fallback paths in ts-python.cmd are hard-coded to two common install locations. A custom install path is not discoverable without a registry query.
- ts-python.cmd auto-heal writes back using `echo ... > file` which always adds a trailing CRLF; `read_python_path()` already strips whitespace so this is safe.
