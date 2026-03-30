# FIX-084: Make ts-python shim fail-closed with deny JSON

## Status
In Progress

## Assigned To
Developer Agent

## Workpackage Summary
When python-path.txt is missing, empty, or points to a non-existent executable, the ts-python shim must output a valid JSON deny response to stdout instead of just printing to stderr. This ensures VS Code blocks all tool calls when Python runtime is unavailable. Fixes BUG-157.

## Linked User Story
US-066 — Fail-Closed Security Gate When Python Runtime Unavailable

## Bugs Fixed
- BUG-157

## Implementation Plan
1. Modify `src/installer/shims/ts-python.cmd` to output deny JSON to stdout on all error paths (missing config, empty config, non-existent executable).
2. Modify `src/installer/shims/ts-python` (Unix shim) to do the same.
3. Check for and update any template copies.
4. Write tests in `tests/FIX-084/`.

## Deny JSON Format
Based on `build_response()` in `security_gate.py`:
```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "..."}}
```

## Files Changed
- `src/installer/shims/ts-python.cmd`
- `src/installer/shims/ts-python`
- `tests/FIX-084/test_fix084_shim_fail_closed.py`

## Implementation Notes
- Deny JSON is emitted to stdout before exit code 0 on all error paths.
- Diagnostic messages are kept on stderr for debugging.
- The message informs the user to open the launcher Settings to fix.
- Exit code is 0 when emitting deny JSON so VS Code treats it as a valid hook response rather than a crashed hook.
- No `templates/coding` directory exists in this repo — nothing to sync there.

## Tests Written
- `tests/FIX-084/test_fix084_shim_fail_closed.py` (6 tests)
  - test_cmd_missing_config_outputs_deny_json
  - test_cmd_empty_config_outputs_deny_json
  - test_cmd_invalid_executable_outputs_deny_json
  - test_cmd_deny_json_is_valid_and_correct_format
  - test_unix_shim_denies_on_missing_config
  - test_unix_shim_denies_on_empty_config

## Test Results
All 6 tests passed.

## Known Limitations
- The Windows shim uses `set /p` which strips leading whitespace from the path file. This is existing behaviour; we do not change it in this WP.
- The Unix shim test reads the script content rather than executing it (avoids cross-platform shell execution issues in CI).
