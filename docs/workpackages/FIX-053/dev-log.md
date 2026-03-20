# Dev Log — FIX-053: Fix INS-011 os._exit killing pytest process

**Agent:** Developer Agent  
**Branch:** FIX-053/fix-os-exit-mock  
**Date:** 2026-03-20  

## Problem

`_apply_windows()` in `src/launcher/core/applier.py` calls `os._exit(0)` (not
`sys.exit`) so that the launcher process is terminated from any thread.  Tests
in `tests/INS-011/test_ins011_applier.py` that exercise `_apply_windows()`
patched `sys.exit` but left `os._exit` unpatched.  Because `os._exit` bypasses
Python's exception machinery it cannot be blocked by a try/except — when the
real call fires it kills the entire pytest process, causing the suite to abort
at ~49%.

## Root Cause

`TestNoShellTrue.test_windows_subprocess_no_shell_true` called `_apply_windows`
with only `patch("launcher.core.applier.sys.exit")` active.  `os._exit` was
never mocked, so the first test that reached that code path terminated the
runner.

## Fix

Added `patch("launcher.core.applier.os._exit")` to
`TestNoShellTrue.test_windows_subprocess_no_shell_true`, making it consistent
with `TestWindowsApply._run_windows_apply` and
`TestWindowsApply.test_windows_installer_path_first_arg`, both of which already
patched `os._exit` correctly.

**No production code was changed.**

## Files Changed

| File | Change |
|------|--------|
| `tests/INS-011/test_ins011_applier.py` | Added `patch("launcher.core.applier.os._exit")` to `test_windows_subprocess_no_shell_true` |
| `docs/workpackages/workpackages.csv` | Status → In Progress / Review |

## Tests Written

No new test files. The fix corrects existing mocking in the pre-existing test
`tests/INS-011/test_ins011_applier.py`.

## Test Results

All tests in `tests/INS-011/` pass after the fix (logged via
`scripts/add_test_result.py`).
