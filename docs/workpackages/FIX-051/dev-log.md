# FIX-051 Dev Log — Fix SAF-034 tests broken by FIX-048/FIX-050

## Summary

**WP ID:** FIX-051  
**Title:** Fix SAF-034 tests broken by FIX-048/FIX-050  
**Assigned To:** Developer Agent  
**Date:** 2026-03-20  

## Problem

FIX-048 changed `verify_ts_python()` to add a `cmd.exe /c` wrapper and increased
timeout from 5→30 seconds. Then FIX-050 rewrote `verify_ts_python()` entirely to
bypass the shim: it now calls `read_python_path()` to get the Python executable
path directly and then tests it via:

```python
subprocess.run([str(python_path), "-c", "import sys; print(sys.version)"], ...)
```

The old SAF-034 tests were mocking `shutil.which` + `subprocess.run` but NOT
`read_python_path()`, so `verify_ts_python()` returned early with
`(False, 'Python path configuration not found.')`.

## Root Cause Analysis

`verify_ts_python()` now starts by calling `read_python_path()`. If that returns
`None`, the function returns immediately with `(False, "Python path configuration
not found.")` — before any `shutil.which` or `subprocess.run` call. Tests that
only mocked `shutil.which` never reached the subprocess step.

## Implementation

Updated both test files to align with the FIX-050 implementation of
`verify_ts_python()`:

### Changes to `tests/SAF-034/test_saf034.py`

1. All tests that call `verify_ts_python()` directly now mock
   `launcher.core.shim_config.read_python_path` to return a `MagicMock` with
   `.exists()` returning `True`.
2. Timeout assertions updated from 5 → 30 seconds.
3. Subprocess arg assertions updated: no `cmd.exe` wrapper; the command is now
   `[python_path, "-c", "import sys; print(sys.version)"]`.
4. Tests 7, 8, 17 (Windows shim-dir) updated to verify `args[1] == "-c"` instead
   of old `cmd.exe /c` structure.
5. Test 2 and 10 (path not found) now patch `read_python_path` to return `None`.

### Changes to `tests/SAF-034/test_saf034_edge.py`

1. EC-01 (macOS), EC-02 (Windows PATH fail) — same `read_python_path` mock added.
2. EC-03 — `timeout=30` assertion (was `timeout=5`).
3. EC-06 — subprocess args assertion updated to `[python_path, "-c", "import sys; print(sys.version)"]`.
4. EC-09 (path with spaces) — uses real `fake_python` path object directly.
5. EC-10 (Windows stripped version) — `read_python_path` mock added.

## Files Changed

- `tests/SAF-034/test_saf034.py` — 18 tests updated
- `tests/SAF-034/test_saf034_edge.py` — 11 edge-case tests updated

## Test Results

All 29 SAF-034 tests pass:
- `tests/SAF-034/test_saf034.py`: 18 passed
- `tests/SAF-034/test_saf034_edge.py`: 11 passed

Full test suite checked for regressions — no new failures introduced.

## Bugs Addressed

- **BUG-078:** 19 SAF-034 test failures from FIX-048 shim changes
- **BUG-083:** 13 additional failures from FIX-050 direct-Python invocation

## Known Limitations

None. All acceptance criteria met.
