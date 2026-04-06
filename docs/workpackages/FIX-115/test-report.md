# Test Report — FIX-115: Drop settings.json from Integrity Hash Check (Iteration 3)

**Tester:** Tester Agent  
**Date:** 2026-04-06  
**Branch:** FIX-115/drop-settings-hash  
**Verdict:** ✅ PASS

---

## Summary

**Iteration 3 result:** All 3 regressions identified in Iteration 2 are confirmed fixed. The
full test suite shows **8953 passed, 74 failed (all baseline), 344 skipped, 5 xfailed, 66
errors** — identical profile to what the Developer reported. Zero new regressions introduced
by FIX-115.

FIX-115's core implementation is correct and complete: `_KNOWN_GOOD_SETTINGS_HASH` removed from
`security_gate.py`, `verify_file_integrity()` verifies only the gate self-hash, `update_hashes.py`
no longer manages a settings hash, ADR-011 documents the decision. All dedicated FIX-115 tests
pass. No stale `_KNOWN_GOOD_SETTINGS_HASH` assertions remain in the test suite.

---

## Code Review Findings

### Correct
- `_KNOWN_GOOD_SETTINGS_HASH` constant removed from `security_gate.py` (only a comment remains).
- `verify_file_integrity()` checks only `_KNOWN_GOOD_GATE_HASH`; no settings.json reference.
- `_INTEGRITY_WARNING` message updated to reference only `security_gate.py`.
- `update_hashes.py`: `_SETTINGS_HASH_RE` removed, `_resolve_paths()` returns single `Path`,
  `update_hashes()` only re-embeds gate hash.
- ADR-011 created in `docs/decisions/ADR-011.md` and indexed in `docs/decisions/index.jsonl`.
- BUG-194 `Fixed In WP` field set to `FIX-115` in `bugs.jsonl`.
- 10 dedicated regression tests in `tests/FIX-115/` covering all key behaviors.
- All affected test files across SAF-008, SAF-009, SAF-011, SAF-022, SAF-025, SAF-071, SAF-075,
  FIX-042, FIX-079, DOC-053, FIX-114, MNT-028, MNT-029 correctly updated.

### Independent Stale-Reference Scan
Searched all files under `tests/` and `src/` for `_KNOWN_GOOD_SETTINGS_HASH`. All 20+
occurrences found in test files assert its **absence** — no remaining test asserts its
presence. No occurrences found in `src/`. Confirmed clean.

---

## Test Results

### Full Test Suite (`tests/`)

Run: `.venv\Scripts\python.exe -m pytest tests/ --tb=no -q`  
Result: **8953 passed, 74 failed, 344 skipped, 5 xfailed, 66 errors** in ~114s  
Logged: TST-2666

All 74 FAIL and 66 ERROR results are accounted for by `tests/regression-baseline.json`
or are pre-existing failures on `main` not introduced by FIX-115 (see Regression Baseline
Comparison below).

### Iteration-1 Regression Targets (Confirmed still passing)

| Suite | Result |
|-------|--------|
| `tests/FIX-079/` | ✅ ALL PASS |
| `tests/DOC-053/` | ✅ ALL PASS |
| `tests/FIX-114/` | ✅ ALL PASS |
| `tests/MNT-029/` | ✅ ALL PASS |

### Iteration-2 Regression Targets (4 tests in 3 files)

| Test | Result |
|------|--------|
| `SAF-009::test_af5_integrity_constants_not_zeroed` | ✅ PASS |
| `SAF-022::TestHashIntegrity::test_default_gate_settings_hash_matches` | ✅ PASS |
| `SAF-022::TestHashIntegrity::test_template_gate_settings_hash_matches` | ✅ PASS |
| `MNT-028::test_adr010_is_last_entry_in_index` | ✅ PASS |

All 4 Iteration-2 regressions are confirmed fixed.

---

## Regression Baseline Comparison

74 failing tests in current run. Cross-referenced against `tests/regression-baseline.json`
(141 known failures).

**Result:** 72 failures are listed in the regression baseline. 2 failures are **not** in the
baseline:

| Test | Status |
|------|--------|
| `FIX-004::test_shell_scripts_use_lf` | Pre-existing on `main` — `build_appimage.sh` has CRLF |
| `INS-007::TestLineEndings::test_no_crlf_line_endings` | Pre-existing on `main` — same file |

**Verification:** Both tests were run against the pre-FIX-115 `main` branch HEAD (`51cdcba`)
and confirmed to fail there too. FIX-115 does not touch `src/installer/linux/build_appimage.sh`.
These are pre-existing failures not introduced by FIX-115.

**Conclusion: Zero new regressions from FIX-115.**

---

## Edge Cases and Security Analysis

- **Missing settings.json at runtime:** The gate no longer references settings.json — a missing
  file cannot break the integrity check. Positive change.
- **Tampered settings.json:** No longer detected by the gate. Intended per ADR-011 —
  settings.json provides only cosmetic VS Code UI config, no security controls.
- **Gate hash zero-checking:** `_KNOWN_GOOD_GATE_HASH` is still verified as non-zeroed in
  SAF-009, SAF-022, and SAF-071. Cannot be accidentally zeroed without test failure.
- **`update_hashes.py` error paths:** The `--error-missing-settings` code path is removed.
  The script is simpler with one fewer failure mode.
- **ADR-011 conflict check:** Reviewed `docs/decisions/index.jsonl` — ADR-011 does not
  conflict with any prior ADR. ADR-008 (tests track current codebase state) is consistent:
  all affected tests have been updated to track the new state.
- **Stale reference scan:** All `_KNOWN_GOOD_SETTINGS_HASH` occurrences in `tests/` assert
  absence. None in `src/`. Confirmed clean.

---

## Pre-Done Checklist

- [x] `docs/workpackages/FIX-115/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/FIX-115/test-report.md` written by Tester
- [x] Test files exist in `tests/FIX-115/` (10 tests)
- [x] Test results logged via `scripts/add_test_result.py` (TST-2666)
- [x] No new bugs introduced by FIX-115 to log
- [x] `scripts/validate_workspace.py --wp FIX-115` returns clean (exit code 0)
- [x] Zero new regressions vs regression baseline
- [x] All 4 Iteration-2 regressions confirmed fixed
