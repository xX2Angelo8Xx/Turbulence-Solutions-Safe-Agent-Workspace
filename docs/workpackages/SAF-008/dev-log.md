# Dev Log — SAF-008

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective

On startup, verify SHA256 hashes of `security_gate.py` and `settings.json` against
known-good values embedded in the script. Alert or refuse to run if modified.
Addresses audit finding 5.

Goal: Tampering with safety-critical files is detectable at hook startup.

## Implementation Summary

Integrity verification functions were injected into `security_gate.py`:

- `compute_file_hash(path)` — computes SHA256 of a file, returns 64-char hex string or `None` if missing.
- `compute_gate_canonical_hash()` — computes SHA256 of `security_gate.py` itself with the embedded hash constant zeroed out, eliminating the circular-dependency problem.
- `verify_file_integrity(project_root)` — compares both files against the `_KNOWN_GOOD_GATE_HASH` and `_KNOWN_GOOD_SETTINGS_HASH` constants embedded in the script.
- Integrity check runs as the **first** operation in `main()`, before stdin is consumed.
- On mismatch the gate outputs a `deny` JSON response and exits immediately (fail-closed).

Known-good hash constants (`_KNOWN_GOOD_GATE_HASH` and `_KNOWN_GOOD_SETTINGS_HASH`) were computed from the current files and embedded directly.

## Files Changed

- `Default-Project/.github/hooks/scripts/security_gate.py` — integrity verification functions added; constants embedded; `main()` updated to call `verify_file_integrity()` first.

## Tests Written

Tests located in `tests/SAF-008/`:

- `test_compute_file_hash_valid_file` — SHA256 of file matches expected
- `test_compute_file_hash_missing_file` — Missing file returns None
- `test_compute_file_hash_different_content` — Different content → different hash
- `test_compute_gate_canonical_hash_returns_string` — Returns 64-char hex string
- `test_compute_gate_canonical_hash_missing_file` — Missing gate returns None
- `test_compute_gate_canonical_hash_independent_of_gate_hash` — Hash constant change does not affect canonical
- `test_verify_file_integrity_passes_with_good_hashes` — Real files pass with embedded hashes
- `test_verify_file_integrity_fails_on_settings_tamper` — Tampered settings.json detected
- `test_verify_file_integrity_fails_on_gate_tamper` — Injected gate code detected
- `test_verify_file_integrity_fails_on_missing_settings` — Missing settings → False
- `test_verify_file_integrity_fails_on_missing_gate` — Missing gate → False
- `test_main_denies_on_integrity_failure_protection` — main() outputs deny on mismatch
- `test_main_denies_with_integrity_warning_message` — Warning text present in deny reason
- `test_bypass_only_gate_hash_changed` — Bypass attempt (hash-only change) detected
- `test_bypass_updating_gate_hash_to_match_tampered_file` — Bypass attempt (code+hash change) detected
- `test_integrity_constants_are_valid_hex` — Constants are 64-char hex, not placeholder zeros
- `test_verify_file_integrity_cross_platform_paths` — Path construction verified on Windows

## Known Limitations

- `update_hashes.py` (admin tool for re-embedding hashes after authorised changes) was
  referenced in comments but not created as part of this WP. Follow-up tracked as BUG-027
  and SAF-011.
- Backfilled during maintenance 2026-03-13 — original dev-log was not created during
  implementation.
