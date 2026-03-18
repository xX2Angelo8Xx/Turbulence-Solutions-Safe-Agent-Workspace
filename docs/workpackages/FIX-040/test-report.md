# Test Report — FIX-040

**WP:** FIX-040 — Fix Windows update restart and stale version label  
**Verdict:** PASS  
**Tester:** Tester Agent  
**Date:** 2026-03-18  
**Branch:** fix/FIX-040-windows-update-restart  
**Bug References:** BUG-073, BUG-074

---

## Summary

FIX-040 is approved. The implementation correctly fixes BUG-074 (app doesn't restart
after Windows in-app update) and its symptom BUG-073 (version label shows old version).
Three targeted changes address all root causes: `os._exit(0)` forces process termination
from the daemon thread; a second `[Run]` entry in `setup.iss` relaunches the app after
silent installs; and `_on_install_starting()` provides visible UI feedback before exit.
All 23 FIX-040 tests pass (12 developer + 11 Tester edge-case).

---

## Code Review

### `src/launcher/core/applier.py`

| Check | Result |
|-------|--------|
| `_apply_windows()` uses `os._exit(0)` not `sys.exit(0)` | ✓ CORRECT |
| `os` module imported at module level | ✓ PRESENT |
| `subprocess.Popen` receives list (not string) as first arg | ✓ LIST |
| `shell=False` explicitly set on `Popen` | ✓ SECURE |
| `/SILENT` and `/CLOSEAPPLICATIONS` flags passed | ✓ CORRECT |
| `_apply_macos()` unchanged | ✓ UNAFFECTED |
| `_apply_linux()` unchanged | ✓ UNAFFECTED |
| Explanatory comment about daemon-thread behaviour present | ✓ DOCUMENTED |

**Assessment:** The `os._exit(0)` fix is correct. `sys.exit()` raises `SystemExit` only
in the calling thread; when called from a daemon thread the main tkinter loop continues.
`os._exit(0)` terminates the whole process immediately, which is safe here because the
installer subprocess is already detached and running independently.

### `src/installer/windows/setup.iss`

| Check | Result |
|-------|--------|
| Original `postinstall skipifsilent` entry preserved for interactive installs | ✓ PRESERVED |
| Second `[Run]` entry with `skipifnotsilent` added for silent relaunch | ✓ PRESENT |
| Silent entry references `{app}\{#MyAppExeName}` | ✓ CORRECT |
| Silent entry has `nowait` flag | ✓ CORRECT |
| No single entry carries both `skipifsilent` and `skipifnotsilent` | ✓ SAFE |
| Exactly two active `Filename:` entries in `[Run]` | ✓ CORRECT |
| Comment explaining the split for silent vs interactive installs | ✓ DOCUMENTED |

**Assessment:** The two-entry approach is the correct Inno Setup pattern for this
scenario. Interactive installs show the "Launch" checkbox as before; silent installs
(the in-app update path) unconditionally relaunch the app.

### `src/launcher/gui/app.py`

| Check | Result |
|-------|--------|
| `import time` added at module level | ✓ PRESENT |
| `_on_install_starting()` method defined inside `App` class | ✓ CORRECT |
| `_on_install_starting()` sets button text to `"Installing..."` with `state="disabled"` | ✓ CORRECT |
| `_on_install_starting()` sets banner text to `"Installing update... App will restart."` | ✓ CORRECT |
| `_on_install_starting()` calls `update_banner.grid()` (shows, does not hide) | ✓ CORRECT |
| `_on_install_starting()` dispatched via `self._window.after(0, ...)` from daemon thread | ✓ THREAD-SAFE |
| `time.sleep(0.5)` called after dispatching `_on_install_starting` | ✓ PRESENT |
| Order: `_on_install_starting` → `time.sleep` → `apply_update` | ✓ CORRECT |

**Assessment:** The 0.5 s sleep gives the tkinter event loop time to process the
`.after(0, ...)` callback so the "Installing..." / "App will restart." text is rendered
before `os._exit(0)` terminates the process. This is a best-effort UI flush and is safe:
the restart is guaranteed regardless of whether the label text renders.

---

## Tests Run

### FIX-040 Developer Test Suite (TST-1829) — pre-existing

12 developer tests in `tests/FIX-040/test_fix040_update_restart.py`. All pass. Verified
by re-running.

| # | Test | Result |
|---|------|--------|
| 1 | `test_apply_windows_uses_os_exit` | PASS |
| 2 | `test_apply_windows_no_sys_exit` | PASS |
| 3 | `test_apply_windows_popen_list_no_shell` | PASS |
| 4 | `test_apply_windows_correct_flags` | PASS |
| 5 | `test_setup_iss_has_postinstall_skipifsilent_entry` | PASS |
| 6 | `test_setup_iss_has_skipifnotsilent_entry` | PASS |
| 7 | `test_setup_iss_silent_entry_launches_exe` | PASS |
| 8 | `test_setup_iss_silent_entry_has_nowait` | PASS |
| 9 | `test_app_ui_update_before_apply_update` | PASS |
| 10 | `test_applier_no_shell_true_anywhere` | PASS |
| 11 | `test_apply_macos_unchanged` | PASS |
| 12 | `test_apply_linux_unchanged` | PASS |

**Result: 12/12 PASS**

### FIX-040 Tester Edge-Case Suite (TST-1830)

11 Tester-added edge-case tests in `tests/FIX-040/test_fix040_edge_cases.py`:

| # | Test | Covers |
|---|------|--------|
| EC-1 | `test_apply_windows_popen_first_arg_is_list` | AST-level: Popen first arg is a list literal (not string) |
| EC-2 | `test_apply_windows_popen_args_exactly_three_elements` | Popen list has exactly 3 elements |
| EC-3 | `test_setup_iss_no_entry_has_both_skip_flags` | No single [Run] line carries both skip flags (mutually exclusive) |
| EC-4 | `test_setup_iss_exactly_two_run_filename_entries` | Exactly 2 active Filename entries (not 1, not 3) |
| EC-5 | `test_on_install_starting_sets_button_installing_disabled` | Button text "Installing...", state="disabled" |
| EC-6 | `test_on_install_starting_sets_restart_banner_text` | Banner text includes "Installing update" and "App will restart" |
| EC-7 | `test_on_install_starting_shows_banner_not_hides` | `update_banner.grid()` called, not `grid_remove()` |
| EC-8 | `test_on_install_starting_defined_inside_app_class` | Method defined inside the App class |
| EC-9 | `test_on_install_starting_dispatched_via_window_after` | Dispatched via `.after(0, self._on_install_starting)` for thread safety |
| EC-10 | `test_download_and_apply_ordering_starting_sleep_apply` | Ordering: _on_install_starting → time.sleep → apply_update |
| EC-11 | `test_applier_imports_os_module` | `os` module imported at module level in applier.py |

**Result: 11/11 PASS**

### Combined FIX-040 Suite

**23/23 PASS** — 0 failures, 0 skipped.

---

## Pre-existing Failures (not introduced by FIX-040)

Two test suites show failures that pre-date this workpackage and are not caused by FIX-040:

| Suite | Pre-existing Failures | Root Cause |
|-------|-----------------------|------------|
| `tests/INS-005/` | ~2 failures (BUG-045) | `filesandirs` test structure mismatch — open bug |
| `tests/INS-011/` | Version-pin failures | Stale version pin `"2.0.1"` vs current `"2.1.0"` |

These failures existed before FIX-040 and are unrelated to the changes in this WP.

---

## Verdict

**PASS** — All 23 FIX-040 tests pass. Implementation is minimal, correct, and secure.
BUG-073 and BUG-074 are fixed. Status updated to `Done`.
