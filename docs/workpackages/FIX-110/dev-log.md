# Dev Log — FIX-110: Fix FIX-050 cross-platform shim tests

## WP Details
- **ID:** FIX-110
- **Status:** Review
- **Assigned To:** Developer Agent
- **Date Started:** 2026-04-05

## Prior Art Check
No relevant ADRs found in docs/decisions/index.jsonl for this test-fix domain.

## Problem Statement
Tests in `tests/FIX-050/` create only `ts-python.cmd` (Windows shim) in their `tmp_path`, but `verify_ts_python()` in `src/launcher/core/shim_config.py` checks for `ts-python` (no extension) on non-Windows platforms. The function returns early with "shim not found" before reaching `subprocess.run`, so mock assertions fail on macOS and Linux.

## Implementation Plan
For every test in `test_fix050.py` and `test_fix050_edge.py` that creates `fake_shim = tmp_path / "ts-python.cmd"`, also create `tmp_path / "ts-python"` so that both Windows and Unix shim names exist.

## Files Changed
- `tests/FIX-050/test_fix050.py` — added Unix shim creation in 5 tests
- `tests/FIX-050/test_fix050_edge.py` — added Unix shim creation in 5 tests
- `tests/FIX-110/test_fix110.py` — new test file verifying the fix

## Tests Written
- `tests/FIX-110/test_fix110.py` — 10 tests verifying both shim files exist after fix

## Implementation Summary
Added `fake_shim_unix = tmp_path / "ts-python"; fake_shim_unix.write_text("#!/bin/sh\n")` after each Windows shim creation in the affected tests. This ensures `verify_ts_python()` finds the shim on all platforms.

### Affected tests in test_fix050.py:
1. `test_verify_calls_python_directly_not_cmd_exe`
2. `test_verify_success_valid_config`
3. `test_verify_timeout_says_30_seconds`
4. `test_verify_handles_os_error`
5. `test_verify_path_with_spaces_and_parens`

### Affected tests in test_fix050_edge.py:
1. `test_verify_ts_python_passes_stdin_devnull`
2. `test_verify_ts_python_passes_timeout_30`
3. `test_verify_ts_python_nonzero_exit_code_in_message`
4. `test_verify_ts_python_file_not_found_after_precheck`
5. `test_verify_ts_python_strips_multiple_trailing_newlines`
