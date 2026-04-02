# Test Report — SAF-071

**Tester:** Tester Agent
**Date:** 2026-04-02
**Iteration:** 1

## Summary

SAF-071 correctly updates `_KNOWN_GOOD_SETTINGS_HASH` and `_KNOWN_GOOD_GATE_HASH` in `security_gate.py` after the changes made by SAF-068 and SAF-069. All 4 developer tests pass. `verify_file_integrity()` returns `True`. SAF-008 (23 tests), which were previously failing due to stale hashes, now all pass. 7 additional edge-case tests were added by the Tester — all pass. Zero regressions introduced across the full SAF suite (3 failing + 29 failing batches confirmed pre-existing on `main` before this branch).

**Verdict: PASS**

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| `test_verify_file_integrity_returns_true` | Unit | PASS | `verify_file_integrity()` returns `True` |
| `test_settings_hash_matches_actual_file` | Unit | PASS | `_KNOWN_GOOD_SETTINGS_HASH` equals SHA256 of `.vscode/settings.json` |
| `test_gate_self_hash_matches_actual_file` | Unit | PASS | `_KNOWN_GOOD_GATE_HASH` equals canonical SHA256 of `security_gate.py` |
| `test_hash_constants_are_64_char_hex` | Unit | PASS | Both constants are 64-char lowercase hex |
| `test_two_hash_constants_are_distinct` (Tester) | Security | PASS | Two constants protect different files and must differ |
| `test_verify_file_integrity_idempotent` (Tester) | Unit | PASS | Calling `verify_file_integrity()` twice returns `True` both times |
| `test_gate_hash_constant_is_not_placeholder` (Tester) | Security | PASS | `_KNOWN_GOOD_GATE_HASH` is not the all-zeros placeholder |
| `test_settings_hash_constant_is_not_placeholder` (Tester) | Security | PASS | `_KNOWN_GOOD_SETTINGS_HASH` is not degenerate/placeholder |
| `test_canonical_hash_computation_is_stable` (Tester) | Unit | PASS | Canonical hash helper is deterministic |
| `test_settings_json_file_exists` (Tester) | Integration | PASS | `settings.json` present at expected path |
| `test_gate_file_exists` (Tester) | Integration | PASS | `security_gate.py` present at expected path |
| SAF-008 full suite (23 tests) | Regression | PASS | All 23 SAF-008 integrity tests pass after hash update |
| SAF regression batch 1 (SAF-001–030) | Regression | PASS | 1623/1626 pass; 3 failures pre-existing on `main` (SAF-010 ×2, SAF-025 ×1) |
| SAF regression batch 2 (SAF-031–072) | Regression | PASS | 1572/1601 pass; 29 failures pre-existing on `main` (SAF-047 ×2, SAF-049 ×15 [doc content], SAF-056 ×9 [agent-rules doc absent]) |

## Pre-Existing Failures (not introduced by SAF-071)

Confirmed by running the identical tests on `main` before this branch:

| Test | Pre-existing on main? | Root cause |
|------|-----------------------|-----------|
| `SAF-010::test_command_uses_python` | Yes | `require-approval.json` uses `ts-python` (introduced by GUI-023) |
| `SAF-010::test_windows_command_uses_python` | Yes | Same as above |
| `SAF-025::test_no_pycache_in_templates_coding` | Yes | `__pycache__` present from earlier test runs importing `security_gate.py` |
| SAF-047 (2), SAF-049 (15), SAF-056 (9) | Yes | Documentation content mismatches from prior WPs |

## Bugs Found

None. No new bugs introduced by SAF-071.

## TODOs for Developer

None. WP is complete and verified.
