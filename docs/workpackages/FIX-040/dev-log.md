# Dev Log — FIX-040: Fix Windows update restart and stale version label

**Agent:** Developer Agent  
**Date:** 2026-03-18  
**Branch:** fix/FIX-040-windows-update-restart  
**Bugs Fixed:** BUG-073, BUG-074  

---

## Problem Summary

Two related bugs on Windows 11:

- **BUG-073**: Version label still shows the old version after a successful in-app update.
- **BUG-074**: The app does not restart after a successful in-app update.

Both bugs share the same root cause: the old launcher process never terminates, so the new version never launches, so the version label is never refreshed.

---

## Root Cause Analysis

### Root Cause 1 — `sys.exit(0)` from daemon thread (applier.py)

`_apply_windows()` in `src/launcher/core/applier.py` called `sys.exit(0)`. This function is invoked from a daemon thread (spawned by `_on_install_update` in `app.py`). Python's `sys.exit()` raises `SystemExit`, which only terminates the **current thread** when called from a non-main thread. The main thread (running `tkinter.mainloop()`) continues unaffected. The Inno Setup installer ran in the background but the old launcher process never exited.

### Root Cause 2 — `skipifsilent` flag prevents relaunch (setup.iss)

In `src/installer/windows/setup.iss`, the `[Run]` entry had `Flags: nowait postinstall skipifsilent`. The in-app update invokes the installer with `/SILENT`, and `skipifsilent` means the `[Run]` entry is skipped entirely in silent mode. The new launcher never relaunched after install.

---

## Changes Made

### 1. `src/launcher/core/applier.py`

- Replaced `sys.exit(0)` with `os._exit(0)` in `_apply_windows()`.
- `os._exit()` terminates the entire process from any thread, bypassing Python cleanup. This is safe here because the installer subprocess is already running independently.
- Added a comment explaining the reasoning.

### 2. `src/installer/windows/setup.iss`

- Kept the original `postinstall skipifsilent` entry for interactive installs (user sees the launch checkbox).
- Added a second `[Run]` entry with `Flags: nowait skipifnotsilent` for silent/in-app installs, which unconditionally launches the app.
- Result: interactive installs behave as before; silent installs (in-app update) now relaunch the app automatically.

### 3. `src/launcher/gui/app.py`

- Added `_on_install_starting()` method that updates the button text to "Installing..." and updates the banner to "Installing update... App will restart."
- In `_download_and_apply()`, after a successful download, post `_on_install_starting()` to the main thread via `self._window.after(0, ...)`, then sleep 0.5 s to allow the UI to render before `apply_update()` is called (which will immediately terminate the process via `os._exit(0)`).

---

## Tests Written

Location: `tests/FIX-040/test_fix040_update_restart.py`

10 test cases covering:
1. `_apply_windows` uses `os._exit` not `sys.exit` (source code inspection)
2. `_apply_windows` uses `subprocess.Popen` with list args (no `shell=True`)
3. `_apply_windows` passes `/SILENT` and `/CLOSEAPPLICATIONS`
4. `setup.iss` `[Run]` has a `postinstall skipifsilent` entry for interactive installs
5. `setup.iss` `[Run]` has a second entry with `skipifnotsilent` for silent installs
6. `setup.iss` silent entry launches `{app}\{#MyAppExeName}`
7. `setup.iss` silent entry has `nowait` flag
8. `app.py` `_download_and_apply` updates UI (`_on_install_starting`) before `apply_update`
9. No `shell=True` anywhere in applier.py
10. `_apply_macos` and `_apply_linux` are not changed (regression check)

---

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/core/applier.py` | `sys.exit(0)` → `os._exit(0)` in `_apply_windows()` |
| `src/installer/windows/setup.iss` | Added second `[Run]` entry for silent relaunch |
| `src/launcher/gui/app.py` | Added `_on_install_starting()`, updated `_download_and_apply()` |
| `tests/FIX-040/test_fix040_update_restart.py` | New test file (10 tests) |
| `docs/workpackages/FIX-040/dev-log.md` | This file |

---

## Known Limitations

- The 0.5 s sleep in `_download_and_apply` is a best-effort UI refresh; if the system is under heavy load the label may not render before `os._exit(0)` fires. This is acceptable because the primary goal (process termination and relaunch) is guaranteed regardless.
- macOS and Linux update paths are unchanged and unaffected.
