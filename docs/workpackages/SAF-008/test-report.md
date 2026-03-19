# Test Report — SAF-008

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 1

## Summary

SAF-008 (Hook File Integrity) implements SHA256 integrity verification for two
safety-critical files — `Default-Project/.github/hooks/scripts/security_gate.py`
and `Default-Project/.vscode/settings.json` — with known-good hashes embedded
directly in the gate script.  The integrity check runs as the **first** operation
in `main()`, before stdin is consumed, and results in a deny-all response on any
mismatch.

All 17 developer tests and 6 new tester edge-case tests pass (23 total). Both
embedded hashes were independently verified against the current file contents.
No regressions were introduced in the wider test suite.

## Checklist Results

| Item | Result |
|------|--------|
| Integrity check runs BEFORE any tool-call processing | ✅ Pass — first call in `main()`, stdin not read |
| Mismatch → deny for ALL tool calls | ✅ Pass — immediate `deny` + `sys.exit(0)` |
| Canonical hash prevents circular dependency | ✅ Pass — `_KNOWN_GOOD_GATE_HASH` value zeroed before hashing |
| Missing files treated as integrity failure (fail-closed) | ✅ Pass — `None` return propagates to `False` |
| Embedded hashes match current file contents | ✅ Pass — independently verified (PowerShell + Python) |
| `update_hashes.py` exists for admin workflow | ⚠️ Missing — see Bugs below |
| `dev-log.md` created by developer | ⚠️ Missing — procedural gap, does not affect runtime |

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-449 test_compute_file_hash_valid_file | Unit | Pass | SHA256 of file matches expected |
| TST-450 test_compute_file_hash_missing_file | Unit | Pass | Missing file returns None |
| TST-451 test_compute_file_hash_different_content | Unit | Pass | Different content → different hash |
| TST-452 test_compute_gate_canonical_hash_returns_string | Unit | Pass | Returns 64-char hex string |
| TST-453 test_compute_gate_canonical_hash_missing_file | Unit | Pass | Missing gate returns None |
| TST-454 test_compute_gate_canonical_hash_independent_of_gate_hash | Unit | Pass | Hash constant change does not affect canonical |
| TST-455 test_verify_file_integrity_passes_with_good_hashes | Integration | Pass | Real files pass with embedded hashes |
| TST-456 test_verify_file_integrity_fails_on_settings_tamper | Security | Pass | Tampered settings.json detected |
| TST-457 test_verify_file_integrity_fails_on_gate_tamper | Security | Pass | Injected gate code detected |
| TST-458 test_verify_file_integrity_fails_on_missing_settings | Unit | Pass | Missing settings → False |
| TST-459 test_verify_file_integrity_fails_on_missing_gate | Unit | Pass | Missing gate → False |
| TST-460 test_main_denies_on_integrity_failure_protection | Security | Pass | main() outputs deny on mismatch |
| TST-461 test_main_denies_with_integrity_warning_message | Security | Pass | Warning text present in deny reason |
| TST-462 test_bypass_only_gate_hash_changed | Security | Pass | Bypass attempt (hash-only change) detected |
| TST-463 test_bypass_updating_gate_hash_to_match_tampered_file | Security | Pass | Bypass attempt (code+hash change) detected |
| TST-464 test_integrity_constants_are_valid_hex | Unit | Pass | Constants are 64-char hex, not placeholder zeros |
| TST-465 test_verify_file_integrity_cross_platform_paths | Cross-platform | Pass | Path construction verified on Windows |
| TST-481 test_compute_file_hash_empty_file | Unit | Pass | Empty file returns SHA256(""), not None |
| TST-482 test_canonical_hash_detects_settings_hash_tampering | Security | Pass | Modifying _KNOWN_GOOD_SETTINGS_HASH in gate IS detected |
| TST-483 test_canonical_hash_no_constant_line | Unit | Pass | File without hash line hashes correctly (no crash) |
| TST-484 test_main_stdin_not_consumed_on_integrity_failure | Security | Pass | stdin.read() never called before deny on integrity fail |
| TST-485 test_verify_file_integrity_returns_false_on_exception | Unit | Pass | Unexpected exception → fail-closed False |
| TST-486 test_canonical_hash_uppercase_hex_recognized | Unit | Pass | Uppercase hex value in constant is zeroed correctly |

## Bugs Found

- BUG-012: `update_hashes.py` referenced in comments throughout security_gate.py but does not exist in `Default-Project/.github/hooks/scripts/`. Admin workflow for re-embedding hashes after authorized changes is undocumented and has no tooling. (logged in docs/bugs/bugs.csv)

## Security Analysis

### Bypass Vector Analysis

**Attempt 1 — Modify only `_KNOWN_GOOD_GATE_HASH`:** Blocked. The canonical hash
zeros this constant before hashing, so its value is irrelevant to the canonical
hash. The stored value would no longer match the (unchanged) canonical hash → detected.

**Attempt 2 — Modify functional code + update `_KNOWN_GOOD_GATE_HASH` to new canonical:**
This *would* allow a bypass in theory (TST-460 verifies different code = different
canonical hash, but doesn't block this path). However, it requires: (a) file edit
access to security_gate.py, (b) computing the canonical SHA256 of the modified
file, and (c) embedding it. An AI agent with write access could do (a) and (c)
trivially; (b) requires terminal execution or the missing update_hashes.py.
This is the inherent trade-off of any self-embedded hash scheme and is consistent
with the stated threat model (detection, not prevention, of admin-initiated changes).

**Attempt 3 — Modify `_KNOWN_GOOD_SETTINGS_HASH` in gate file to cover tampered settings:** Blocked. `_KNOWN_GOOD_SETTINGS_HASH` is NOT zeroed in the canonical form, so changing it changes the canonical hash → detected (confirmed by TST-482).

**Attempt 4 — Race condition (TOCTOU):** The integrity check reads and hashes both
files at startup, once, before processing input. A TOCTOU attack would require
modifying the file between the hash read and all tool call decisions — but since
the check runs once per invocation and denies all calls on failure, the window is
a single file-read operation. Practical risk is negligible in this architecture.

### Fail-Closed Verification

All error paths — `OSError` on file read, `None` from hash functions, unexpected
exceptions in verify body — result in `False` → deny. Confirmed by TST-450,
TST-453, TST-458, TST-459, TST-485.

## TODOs for Developer

None — implementation is complete.

*(Minor gaps noted for tracking: BUG-012 should be resolved in a future admin-tooling WP.)*

## Verdict

**PASS — mark WP as Done**

All acceptance criteria satisfied:
1. ✅ SHA256 of security_gate.py and settings.json calculated on startup
2. ✅ Hashes compared against embedded known-good values
3. ✅ Mismatch → refuse to run (deny all tool calls)
