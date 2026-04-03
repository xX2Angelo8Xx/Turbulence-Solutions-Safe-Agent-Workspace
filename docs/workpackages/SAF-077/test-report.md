# Test Report — SAF-077

**Tester:** Tester Agent  
**Date:** 2026-04-04  
**Iteration:** 1

## Summary

SAF-077 delivers `scripts/verify_parity.py` — a standalone parity-check script
that confirms a freshly installed workspace and an upgraded workspace produce
byte-identical security-critical files. The implementation is clean, well-tested,
and meets all acceptance criteria. The CI job is correctly wired. No bugs found.
**PASS.**

## Code Review Findings

| Area | Assessment |
|------|-----------|
| `verify_parity.py` overall design | Clean single-responsibility script, ~230 lines, no dead code |
| `_ensure_src_on_path()` | Correct guard (`if src_dir not in sys.path`) — idempotent under normal use |
| `create_fresh_workspace()` / `create_upgraded_workspace()` | Intentional deviation from `create_project()` justified in dev-log and docstrings |
| Sentinel byte approach | Effective — unique sentinel bytes guarantee upgrade detection |
| Error filtering (`Post-upgrade verification` substring) | Correctly isolates stale-MANIFEST noise from real copy errors |
| `compare_workspaces()` | Full-scan (no early exit), byte-level SHA-256, clear mismatch messages |
| `main()` exception catching | Catches `FileNotFoundError`, `ValueError`, `RuntimeError` → exit 1 |
| CI `parity-check` job | Correct placement, uses `--verbose`, runs on push/PR to main and `workflow_dispatch` |
| Security design (no manifest hash trust) | `compare_workspaces()` reads actual file bytes, NOT manifest hashes — correct |

**Design deviation acknowledged:** `shutil.copytree()` instead of `create_project()` is
correct given the stated goal: `create_project()` post-copy modifications (counter_config
line endings, placeholder substitution) would produce artificial parity failures unrelated to
the upgrade mechanism. The deviation is fully documented in both the dev-log and the script
docstring.

## Tests Executed

### Developer's 31 tests (all passed)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| `test_manifest_loads_without_error` | Unit | PASS | Real MANIFEST.json loads cleanly |
| `test_manifest_has_files_section` | Unit | PASS | |
| `test_load_manifest_raises_on_missing_file` | Unit | PASS | FileNotFoundError path |
| `test_load_manifest_raises_on_invalid_json` | Unit | PASS | ValueError path |
| `test_get_security_critical_files_returns_list` | Unit | PASS | |
| `test_get_security_critical_files_not_empty` | Unit | PASS | At least 1 SC file in real manifest |
| `test_get_security_critical_files_only_marked_true` | Unit | PASS | Integrity of filter |
| `test_get_security_critical_files_excludes_non_critical` | Unit | PASS | |
| `test_get_security_critical_files_empty_manifest` | Unit | PASS | Edge: empty manifest |
| `test_sha256_consistent` | Unit | PASS | Deterministic digest |
| `test_sha256_known_value` | Unit | PASS | Empty-file known digest |
| `test_sha256_different_for_different_content` | Unit | PASS | |
| `test_sha256_single_byte_difference` | Unit | PASS | 1-byte sensitivity |
| `test_compare_workspaces_all_match` | Unit | PASS | |
| `test_compare_workspaces_detects_mismatch` | Unit | PASS | HASH MISMATCH reported |
| `test_compare_workspaces_missing_in_fresh` | Unit | PASS | |
| `test_compare_workspaces_missing_in_upgraded` | Unit | PASS | |
| `test_compare_workspaces_both_absent_no_mismatch` | Unit | PASS | Correct "both absent" semantics |
| `test_compare_workspaces_multiple_files` | Unit | PASS | Full-scan, all files checked |
| `test_verify_parity_passes` | Integration | PASS | Real workspace creation + upgrade |
| `test_verify_parity_returns_false_on_mismatch` | Unit | PASS | Mocked mismatch path |
| `test_verify_parity_returns_true_on_empty_mismatches` | Unit | PASS | Mocked pass path |
| `test_verify_parity_no_security_files_returns_true` | Unit | PASS | Empty SC list → True |
| `test_cli_exits_zero_on_parity` | Integration | PASS | Subprocess, --verbose, exit 0 |
| `test_cli_exits_one_on_missing_manifest` | Integration | PASS | FileNotFoundError → exit 1 |
| `test_sentinel_content_is_detected_as_mismatch` | Security | PASS | PROTECTION: sentinel detected |
| `test_bypass_attempt_all_files_must_be_checked` | Security | PASS | BYPASS: no short-circuit |
| `test_tampered_hash_in_manifest_does_not_help_attacker` | Security | PASS | Manifest hashes not trusted |
| `test_verify_parity_script_exists` | Unit | PASS | |
| `test_verify_parity_has_main` | Unit | PASS | |
| `test_verify_parity_has_verify_parity` | Unit | PASS | |

### Tester's 8 additional edge-case tests (all passed)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| `test_ensure_src_on_path_idempotent` | Unit | PASS | Relative idempotency: second call adds 0 entries |
| `test_compare_workspaces_verbose_does_not_change_results` | Unit | PASS | verbose flag is pure I/O |
| `test_compare_workspaces_path_traversal_both_absent_not_a_mismatch` | Security | PASS | Traversal paths absent from both → not flagged |
| `test_create_upgraded_workspace_raises_on_copy_error` | Unit | PASS | Copy errors propagate as RuntimeError |
| `test_create_upgraded_workspace_ignores_post_upgrade_verification_errors` | Unit | PASS | Stale-manifest errors are filtered |
| `test_verify_parity_exits_one_on_runtime_error` | Integration | PASS | RuntimeError → CLI exit 1 with ERROR |
| `test_sha256_reads_file_in_binary_chunks` | Unit | PASS | 20 KB file spans multiple 8192-byte chunks |
| `test_get_security_critical_files_missing_key` | Unit | PASS | Absent `security_critical` key → not included |

**Total: 39 tests — 39 passed, 0 failed.**

### Regression check

Full test suite (8001 passed, 37 skipped, 5 xfailed). 634 failures + 50 errors are all
documented in `tests/regression-baseline.json` (680 known failures). Zero new regressions
introduced by SAF-077.

Logged as TST-2496 (full suite — run by Developer) and TST-2497 (tester edge cases).

## Bugs Found

None. No new bugs logged.

## ADR Compliance

- **ADR-003 (Template Manifest and Upgrade System):** Fully compliant. WP operationalises
  the parity guarantee stated in ADR-003's positive consequences.
- **ADR-002 (Mandatory CI Gate):** Fully compliant. New `parity-check` job extends the CI
  gate without weakening it.

## Security Assessment

| Threat | Mitigation | Verified |
|--------|-----------|---------|
| Sentinel survives upgrade (upgrader didn't restore file) | `compare_workspaces()` byte comparison catches mismatch | ✓ |
| Short-circuit attack (good first file masks bad second) | Full-scan loop, no early exit | ✓ |
| Manifest hash tampering (attacker changes MANIFEST.json hashes) | `compare_workspaces()` does NOT consult manifest hashes | ✓ |
| RuntimeError swallowed (upgrade failure undetected) | `create_upgraded_workspace()` raises, `main()` exits 1 | ✓ |
| Stale MANIFEST produces false failures | Post-upgrade verification errors filtered; byte comparison is authoritative | ✓ |

## Verdict

**PASS — mark WP as Done.**

All 39 tests pass. Implementation is correct, well-documented, and security-complete.
CI job is properly integrated. No bugs found. No regressions introduced.
