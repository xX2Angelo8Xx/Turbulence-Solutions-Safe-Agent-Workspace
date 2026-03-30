# SAF-061 Test Report — Make parallel denial batching deterministic

**Tester:** Tester Agent  
**Date:** 2026-03-30  
**Branch:** SAF-061/denial-batching  
**Verdict:** ✅ PASS

---

## Summary

| Category | Count |
|---|---|
| Developer tests (SAF-061) | 15 |
| Tester edge-case tests (SAF-061) | 16 |
| SAF-035 regression | ~60 |
| SAF-036 regression | ~26 |
| **SAF-061 total** | **31** |
| Full suite (all WPs) | 7164 passed, 74 pre-existing failures |
| New failures introduced by SAF-061 | **0** |

---

## Code Review

### Files Changed
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py`
- `tests/SAF-061/test_saf061_denial_batching.py`
- `tests/SAF-035/test_saf035_denial_counter.py` (reference fix: `_DENY_THRESHOLD` → `_DENY_THRESHOLD_DEFAULT`)
- `tests/SAF-035/test_saf035_tester_edge_cases.py` (same reference fix)
- `tests/SAF-036/test_saf036_counter_config.py` (similar reference fix)

### Implementation Assessment

**`_state_lock(lock_path)` context manager:**
- Correct: uses `os.open(O_CREAT|O_EXCL|O_WRONLY)` which is atomic on all local filesystems
- Correct: `finally` block closes the fd and unlinks the lock file — no orphan risk
- Correct: fail-open (yields even without lock) after `_LOCK_ACQUIRE_RETRIES` exhausted — preserves non-blocking best-effort contract
- Correct: retries with configurable sleep delay

**`_increment_deny_counter()` batch window logic:**
- Correct: `age_ms < _DENY_BATCH_WINDOW_MS` (strictly less than) — boundary case well-defined and tested
- Correct: only updates timestamp on actual increment, not on batch-skip
- Correct: session initialised on first call; corrupt/empty timestamps degrade gracefully
- Correct: `now_locked` check is correct (`>= threshold`)

**`main()` deny path:**
- Correct: re-reads state inside the lock to pick up any writes from parallel process that won the lock first — enables the batch window to work across processes
- Correct: lock path uses `scripts_dir` (same dir as state file) — isolation is appropriate

### Security Assessment
- The lock mechanism does **not** introduce any denial-of-service escalation path — the fail-open behaviour is appropriate (worst case: counter may skip a dedup, not a security bypass)
- No secrets, no hardcoded paths, no shell injection vectors
- Path traversal: `os.path.join(scripts_dir, _LOCK_FILE_NAME)` — scripts_dir is resolved via `os.path.dirname(os.path.abspath(__file__))`, safe
- The `O_CREAT|O_EXCL` combination provides correct atomicity on local POSIX/NTFS filesystems

---

## Test Results

### TST-2259 — Developer tests (15 passed)
All developer-written tests passed:
- Single deny increments by one
- Two rapid denials share one block (batch window)
- Two spaced denials get separate blocks
- Counter reaches threshold, session locked
- Lock file released after context
- Lock file released on exception
- Sequential lock acquisitions no deadlock
- Stale lock graceful fallback
- Batch window boundary (exact, below)
- Uninitialized session created
- In-memory concurrent increments consistent
- File-based concurrent lock serializes writes

### TST-2260 — Tester edge-case tests (16 passed)
Added edge cases covering tester's additional scenarios:

| Test Class | Tests | Finding |
|---|---|---|
| `TestAlreadyLockedSession` | 2 | Already-locked sessions return `now_locked=True`, state is JSON-serializable ✓ |
| `TestCorruptStateInsideLock` | 3 | Corrupt/truncated state file: `_load_state` returns `{}`, counter re-initialises at 1 ✓ |
| `TestThreeConcurrentThreadsLock` | 1 | 3 threads, no deadlock, lock file absent after all complete, final count 1–3 ✓ |
| `TestStaleLockFallthrough` | 1 | Stale lock + retries=1: falls through in < 200 ms, execution continues ✓ |
| `TestNoOrphanedLockFile` | 2 | 5 sequential acquisitions and 3 exception-raising acquisitions — no orphan lock ✓ |
| `TestBatchWindowBoundaryStrict` | 3 | Exact boundary increments; 1 ms inside does not; 1 ms past boundary does ✓ |
| `TestSaveStateBestEffort` | 1 | State path is a directory: `_save_state` absorbs error silently, no exception ✓ |
| `TestSessionIdEdgeCases` | 3 | Whitespace, numeric, unicode session IDs all roundtrip through JSON correctly ✓ |

**Note:** Tests that call `sg._load_state` / `sg._save_state` correctly avoid the
`conftest.py` autouse patch (`_prevent_hook_state_writes`) by using `json.dumps/loads`
directly for JSON-serialization assertions. This is the correct pattern.

### TST-2261 — SAF-035 + SAF-036 regression (86 passed)
Zero regressions in denial counter or counter config functionality.

### TST-2262 — Full suite regression
7164 passed. 74 pre-existing failures confirmed not related to SAF-061 (failing
WPs: FIX-039, FIX-042, FIX-049, INS-004, INS-014, INS-015, INS-017, INS-019,
MNT-002, SAF-010, SAF-025). None of these files appear in `git diff main --name-only`.

---

## Edge Case Analysis

### Attack Vectors
- **Stale lock DoS**: Tested — fail-open after retries, execution always continues
- **Lock file as directory**: Not explicitly tested but `os.open(...|O_EXCL)` would raise `IsADirectoryError` which triggers the fallback

### Boundary Conditions
- **Exactly at boundary**: `age_ms < 100` is strictly less than → tested and confirmed increments
- **1 ms inside window**: does not increment → tested
- **Empty / corrupt timestamp**: increments normally → tested

### Race Conditions
- **Two threads, in-process**: one returns count 1 (shared batch), or both return count 2 (sequential) — both valid → tested
- **Two threads, file-based lock**: exactly serialized, final count 1–2 → tested
- **Three threads, file-based lock**: no deadlock, lock cleaned up → tested

### Platform Notes
- Tested on Windows 11 / Python 3.11
- `O_CREAT|O_EXCL` atomicity holds on NTFS local drives (the supported VS Code usage scenario)
- NFS/network filesystems acknowledged as out-of-scope in dev-log — acceptable

### Resource Leaks
- Lock fd is closed in `finally` → verified no leak
- Temp file in `_save_state` is unlinked on error → verified
- No threading.Lock objects retained across test boundaries

---

## Known Pre-existing Issues (not introduced by SAF-061)

None of the 74 pre-existing test failures are caused by this WP.

---

## Bugs Found

None. No new bugs logged.

---

## Pre-Done Checklist

- [x] `docs/workpackages/SAF-061/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/SAF-061/test-report.md` written by Tester
- [x] Test files exist in `tests/SAF-061/` with 31 tests total
- [x] All test results logged via `scripts/add_test_result.py` (TST-2259 – TST-2262)
- [x] `scripts/validate_workspace.py --wp SAF-061` returns exit code 0
- [x] No tmp_ files in WP folder or test folder

**Verdict: PASS → WP status set to Done**
