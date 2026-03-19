# Dev Log — SAF-010

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective

Create `require-approval.json` in `Default-Project/.github/hooks/` pointing to the
Python security gate (`scripts/security_gate.py`). Ensure VS Code discovers and
invokes this hook for every PreToolUse event on all platforms (Windows, macOS, Linux).

## Implementation Summary

The file `Default-Project/.github/hooks/require-approval.json` already existed,
but it pointed to the legacy shell scripts (`require-approval.sh` and
`require-approval.ps1`). SAF-001 delivered the Python security gate
(`security_gate.py`) as the intended replacement.

This WP updates the config to:
- Use `python3` as the command on Unix/macOS
- Use `python` as the command on Windows (via the `"windows"` field)
- Keep `"timeout": 15` unchanged
- Cover ALL PreToolUse events (no tool-type filtering)

The `"windows"` override field in the require-approval format allows a
platform-specific command while keeping the cross-platform structure intact.
No changes were made to `security_gate.py` or `settings.json` (already correct).

## Files Changed

- `Default-Project/.github/hooks/require-approval.json` — updated command from legacy shell scripts to `python3`/`python security_gate.py`

## Tests Written

- `test_config_file_exists` — require-approval.json exists at the correct path
- `test_config_is_valid_json` — file is well-formed JSON
- `test_hooks_key_present` — top-level "hooks" key exists
- `test_pretooluse_key_present` — "PreToolUse" array is present under "hooks"
- `test_pretooluse_is_non_empty_list` — PreToolUse list has at least one entry
- `test_entry_type_is_command` — first entry has "type": "command"
- `test_command_references_security_gate` — "command" field references security_gate.py
- `test_command_does_not_reference_legacy_sh` — "command" no longer references require-approval.sh
- `test_command_uses_python` — "command" starts with python/python3
- `test_windows_field_present` — "windows" override field present
- `test_windows_command_references_security_gate` — "windows" field references security_gate.py
- `test_windows_command_does_not_reference_legacy_ps1` — "windows" field no longer references require-approval.ps1
- `test_windows_command_uses_python` — "windows" command starts with python
- `test_script_path_resolves` — security_gate.py exists on disk at the expected path
- `test_security_gate_is_python_script` — referenced script has .py extension
- `test_timeout_is_present` — timeout field exists
- `test_timeout_is_positive_integer` — timeout > 0
- `test_no_tool_filter` — no "matcher" or "tools" restriction (covers ALL tools)
- `test_settings_json_auto_approve_disabled` — settings.json has autoApprove: false (guard)

## Test Results

- SAF-010 suite: **19/19 pass** (TST-269 to TST-288)
- Full regression (excl. pre-existing INS-009 import error): **466/469 pass**
  - 3 pre-existing failures in GUI-003 and INS-012 — unrelated to SAF-010
  - Zero regressions introduced

## Known Limitations

- Cross-platform invocation relies on `python3` (Unix) and `python` (Windows) being on PATH.
  If the Python executable is not on PATH in the VS Code process environment, the hook will
  not fire. This is a deployment concern, not a code defect.
- VS Code hook discovery requires the workspace to be opened at the root of `Default-Project/`.
  The path `.github/hooks/require-approval.json` is relative to the workspace root.
