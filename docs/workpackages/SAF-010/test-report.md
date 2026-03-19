# Test Report — SAF-010

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 1

## Verdict: PASS

## Summary

`require-approval.json` correctly points to `security_gate.py` for all PreToolUse
events on both Unix/macOS (`python3`) and Windows (`python`). The file is
well-formed, BOM-free UTF-8, uses a relative script path, has a sane timeout,
and imposes no tool-type filtering. The referenced `security_gate.py` has a
proper `main()` entry point and an `if __name__ == "__main__"` guard. All 29
tests (19 developer + 10 Tester edge-cases) pass; no regressions introduced.

**Observation (non-blocking):** The developer's dev-log references TST-269–TST-288
as the SAF-010 test log entries, but those IDs in `test-results.csv` are all
INS-009 entries. The SAF-010 developer test runs were never logged in the CSV.
Tester logs are authoritative for this handoff.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_config_file_exists | Unit | Pass | require-approval.json exists at correct path |
| test_config_is_valid_json | Unit | Pass | File is well-formed JSON |
| test_hooks_key_present | Unit | Pass | Top-level "hooks" key present |
| test_pretooluse_key_present | Unit | Pass | PreToolUse array present under hooks |
| test_pretooluse_is_non_empty_list | Unit | Pass | At least one entry in PreToolUse |
| test_entry_type_is_command | Unit | Pass | Entry type is "command" |
| test_command_references_security_gate | Security | Pass | Unix command references security_gate.py |
| test_command_does_not_reference_legacy_sh | Security | Pass | Legacy .sh not referenced |
| test_command_uses_python | Cross-platform | Pass | Unix command starts with python3 |
| test_windows_field_present | Cross-platform | Pass | "windows" override field present |
| test_windows_command_references_security_gate | Security | Pass | Windows command references security_gate.py |
| test_windows_command_does_not_reference_legacy_ps1 | Security | Pass | Legacy .ps1 not referenced |
| test_windows_command_uses_python | Cross-platform | Pass | Windows command starts with python |
| test_script_path_resolves | Unit | Pass | security_gate.py exists on disk |
| test_security_gate_is_python_script | Unit | Pass | Unix command references .py file |
| test_timeout_is_present | Unit | Pass | "timeout" field present |
| test_timeout_is_positive_integer | Unit | Pass | Timeout is a positive integer |
| test_no_tool_filter | Security | Pass | No matcher/tools restriction; covers ALL tools |
| test_settings_json_auto_approve_disabled | Security | Pass | autoApprove still false in settings.json |
| test_no_bom_encoding | Unit | Pass | File is BOM-free UTF-8 |
| test_json_round_trip | Unit | Pass | Load+dump produces equivalent JSON; no duplicate keys |
| test_top_level_only_hooks_key | Security | Pass | No unexpected extra top-level keys |
| test_only_pretooluse_event_registered | Security | Pass | Only PreToolUse registered; no unexpected event hooks |
| test_command_uses_relative_path | Security | Pass | Unix command uses relative path |
| test_windows_command_uses_relative_path | Security | Pass | Windows command uses relative path |
| test_windows_security_gate_is_python_script | Unit | Pass | Windows command references .py file |
| test_timeout_within_reasonable_range | Unit | Pass | Timeout 15 s is within [1, 60] seconds |
| test_security_gate_has_main_function | Unit | Pass | security_gate.py defines main() |
| test_security_gate_has_name_guard | Unit | Pass | security_gate.py has __name__ == "__main__" guard |
| Full regression suite (551 pass / 2 pre-existing fail) | Regression | Pass | INS-004 + INS-012 failures are pre-existing; zero regressions from SAF-010 |

## Bugs Found

None — no new bugs introduced by this workpackage.

## TODOs for Developer

None — all acceptance criteria met.

## Test Summary
- Total tests run: 551 (full suite) / 29 (SAF-010 suite)
- Passed: 551 / 29
- Failed: 2 (pre-existing INS-004, INS-012 — unrelated to SAF-010)
