# SAF-065 Test Report — Increase parallel denial batch window

## Verdict: PASS

**Date:** 2026-04-01  
**Tester:** Developer Agent  
**Branch:** `SAF-065/denial-batch-window`  
**Test ID logged:** TST-2417

---

## Summary

| Tests | Result |
|-------|--------|
| SAF-065 new tests (5) | 5 passed |
| SAF-061 regression (31) | 31 passed |
| SAF-008 integrity (16) | 16 passed |
| SAF-036 config (37) | 37 passed |
| **Total** | **89 passed, 0 failed** |

---

## Change Verification

### Batch window value ✓
`test_deny_batch_window_is_500` — PASS: `_DENY_BATCH_WINDOW_MS == 500`  
`test_deny_batch_window_greater_than_100` — PASS  

### _LOCK_FILE_NAME preserved ✓
`test_lock_file_name_still_defined` — PASS  

### SAF-065 documented in source ✓
`test_gate_source_mentions_saf065` — PASS  

### Hash regenerated ✓
`test_gate_hash_is_non_trivial` — PASS: hash is non-zero  

### SAF-061 regression ✓
All 31 SAF-061 parallel batching tests pass with no regressions.
The two tests that used `_ts_ago(200)` were updated to `_ts_ago(sg._DENY_BATCH_WINDOW_MS + 100)`.

### Integrity ✓
SAF-008 hash integrity tests pass — `update_hashes.py` was run and hash is consistent.
