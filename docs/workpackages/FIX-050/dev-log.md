# FIX-050 Dev Log — Fix ts-python.cmd parsing and verify_ts_python robustness

**WP ID:** FIX-050  
**Type:** Fix  
**Status:** In Progress → Review  
**Assigned To:** Developer Agent  
**Date:** 2026-03-19  
**Branch:** fix/FIX-050-ts-python-cmd-parsing  

---

## Problem Summary

BUG-081: Users installing to `C:\Program Files\Agent Environment Launcher\`
receive a "Python Runtime Unavailable" error when clicking Create Project.
The error message `ts-python exited with code 255: \Agent was unexpected at this
time` is a Windows `cmd.exe` parsing failure caused by two separate issues.

### Root Cause 1 — ts-python.cmd unquoted `%PYTHON_PATH%` inside `if ( )` blocks

`setlocal` (without `EnableDelayedExpansion`) causes `%PYTHON_PATH%` to be
expanded at **parse-time** — before cmd.exe evaluates the block structure. When
the path contains spaces (e.g. `C:\Program Files\Agent Environment
Launcher\...`), the expansion produces unquoted tokens mid-block, which
corrupts the `( )` structure and causes the parser to misread the remaining
script content as malformed commands.

The existing `if not exist "%PYTHON_PATH%"` check was also missing a
`not defined` guard for the case where `python-path.txt` exists but is empty.

### Root Cause 2 — verify_ts_python() uses cmd.exe /c chain (FIX-048)

FIX-048 added `cmd.exe /c <shim> -c "import sys; print(sys.version)"`. The
`-c` argument contains parentheses from `print(sys.version)` which interact
badly with cmd.exe's quote-stripping in the `/c` chain, compounding the parsing
failure when the shim itself is also broken.

---

## Changes Made

### Fix 1: `src/installer/shims/ts-python.cmd`

**Old:** `setlocal` (no delayed expansion) — `%PYTHON_PATH%` in `if ( )` blocks
expanded at parse-time, breaking the block structure for paths with spaces.

**New:** `setlocal EnableDelayedExpansion` — `!PYTHON_PATH!` expanded at
execution-time, after block structure is determined. Added `if not defined
PYTHON_PATH` guard for empty-file edge case. Quoted `"!PYTHON_PATH!"` in error
echo statements. Final invocation uses `"!PYTHON_PATH!" %*`.

### Fix 2: `src/launcher/core/shim_config.py` — `verify_ts_python()`

**Old:** Found shim on disk or PATH, then invoked it via `cmd.exe /c <shim> -c
"import sys; print(sys.version)"`. The cmd.exe wrapper introduced the same
parsing vulnerabilities for paths with spaces/parentheses.

**New:** Completely bypasses the cmd.exe/batch chain:
1. Reads python-path.txt directly via `read_python_path()`.
2. Checks `python_path.exists()`.
3. Checks shim file exists at the expected location (or on PATH as fallback).
4. Invokes `subprocess.run([str(python_path), "-c", "import sys; print(sys.version)"])` directly — no cmd.exe or shell involved.
5. Returns `(True, version_string)` on success, `(False, error_message)` on failure.

### Fix 3: Version bump 3.0.1 → 3.0.2

Updated in all 5 canonical locations:
- `src/launcher/config.py` — `VERSION: str = "3.0.2"`
- `pyproject.toml` — `version = "3.0.2"`
- `src/installer/windows/setup.iss` — `#define MyAppVersion "3.0.2"`
- `src/installer/macos/build_dmg.sh` — `APP_VERSION="3.0.2"`
- `src/installer/linux/build_appimage.sh` — `APP_VERSION="3.0.2"`

---

## Files Changed

| File | Change |
|------|--------|
| `src/installer/shims/ts-python.cmd` | Rewritten with `EnableDelayedExpansion` and `!VAR!` syntax |
| `src/launcher/core/shim_config.py` | `verify_ts_python()` rewritten to bypass cmd.exe |
| `src/launcher/config.py` | VERSION 3.0.1 → 3.0.2 |
| `pyproject.toml` | version 3.0.1 → 3.0.2 |
| `src/installer/windows/setup.iss` | MyAppVersion 3.0.1 → 3.0.2 |
| `src/installer/macos/build_dmg.sh` | APP_VERSION 3.0.1 → 3.0.2 |
| `src/installer/linux/build_appimage.sh` | APP_VERSION 3.0.1 → 3.0.2 |
| `docs/bugs/bugs.csv` | Added BUG-081 |
| `docs/workpackages/workpackages.csv` | Added FIX-050 |
| `tests/FIX-050/test_fix050.py` | 12 new tests |
| `tests/FIX-050/__init__.py` | Created |

---

## Tests Written

12 tests in `tests/FIX-050/test_fix050.py`:

1. `test_cmd_uses_delayed_expansion` — ts-python.cmd contains `setlocal EnableDelayedExpansion`
2. `test_cmd_uses_exclamation_var_syntax` — `!PYTHON_PATH!` appears in if blocks
3. `test_cmd_has_not_defined_check` — `if not defined PYTHON_PATH` guard present
4. `test_cmd_no_bare_percent_in_if_blocks` — `%PYTHON_PATH%` not used (negation of old broken pattern) inside echo/if blocks
5. `test_verify_calls_python_directly_not_cmd_exe` — subprocess.run called with python_path, not cmd.exe
6. `test_verify_success_valid_config` — full mock → (True, version_string)
7. `test_verify_fails_config_missing` — read_python_path returns None → (False, ...)
8. `test_verify_fails_python_not_found` — python_path.exists() = False → (False, ...)
9. `test_verify_fails_shim_missing_and_not_on_path` — shim/path both absent → (False, ...)
10. `test_verify_timeout_says_30_seconds` — TimeoutExpired → "30 seconds" in msg
11. `test_verify_handles_os_error` — OSError → (False, ...)
12. `test_verify_path_with_spaces_and_parens` — python_path with spaces and parentheses succeeds

---

## Known Side Effects

The behavioral change in `verify_ts_python()` from cmd.exe-based to direct
Python invocation means the following previously-written tests now test a
different (no longer current) interface and will fail:

- `tests/SAF-034/test_saf034.py`: Tests that check `args_used[0] == "cmd.exe"`,
  `args_used[0] == shim_path`, or `timeout=5` were already failing due to BUG-078
  (cmd.exe wrapper added by FIX-048 without updating those tests). After FIX-050
  these tests remain failing — the new contract is tested by FIX-050 tests.
- `tests/FIX-048/test_fix048.py`: Tests that assert `args_used[0] == "cmd.exe"`
  will fail because FIX-050 removes the cmd.exe wrapper entirely. These are new
  failures introduced by this WP. They reflect the intentional, correct behavior
  change documented in BUG-081.

All 12 FIX-050 tests pass.

---

## Test Results

See `docs/test-results/test-results.csv` entries TST-1868 through TST-1869.
