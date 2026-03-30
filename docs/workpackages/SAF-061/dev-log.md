# SAF-061 Dev Log — Make parallel denial batching deterministic

**WP ID:** SAF-061  
**Branch:** SAF-061/denial-batching  
**Assigned To:** Developer Agent  
**Status:** Review

---

## Root Cause Analysis

The `_increment_deny_counter()` function in `security_gate.py` operates on an
in-memory `state` dict that was loaded from `.hook_state.json` earlier in
`main()`. When two parallel tool calls are denied simultaneously (each spawns a
separate Python process), both processes:

1. Read `.hook_state.json` and get the same `deny_count` value (e.g., 5)
2. Both increment to 6 in memory
3. Both write back via `_save_state()` — last writer wins
4. Result: counter only moves by 1 instead of 2 (or whichever write wins)

Additionally, the desired behavior (per BUG-144 and the WP spec) is that
**parallel denied operations in the same VS Code batch should share one block
increment** — not necessarily increment twice.

---

## Fix Approach

Two complementary mechanisms:

### 1. File-level exclusive lock (`_state_lock`)
A cross-platform context manager using `os.open(path, O_CREAT | O_EXCL)` for
atomic lock file creation. If the lock file already exists (another process
holds the lock), retry up to `_LOCK_ACQUIRE_RETRIES` times with
`_LOCK_ACQUIRE_DELAY_S` sleep between attempts. Falls back to unlocked operation
on timeout (counter is non-blocking, best-effort). This prevents two processes
from corrupting each other's writes.

### 2. Batch window (`_DENY_BATCH_WINDOW_MS = 100 ms`)
Inside the locked region, `_increment_deny_counter()` checks the timestamp of
the last deny. If the last deny was within 100 ms, the current call is treated
as part of the same parallel batch and the counter is **not** incremented again
— it returns the current count. If > 100 ms have passed, the counter increments
normally.

Together, these ensure:
- Parallel batch → one lock acquirer increments, the other(s) see the fresh
  state after the lock owner writes, detect "same batch", and skip incrementing.
- Sequential denials > 100 ms apart → each increments independently.

---

## Implementation

### New constants (SAF-035 section in `security_gate.py`)
```
_LOCK_FILE_NAME: str = ".hook_state.lock"
_DENY_BATCH_WINDOW_MS: int = 100
_LOCK_ACQUIRE_RETRIES: int = 20
_LOCK_ACQUIRE_DELAY_S: float = 0.05
```

### New imports
- `contextlib` (for `@contextlib.contextmanager`)
- `time` (for `time.sleep`)

### New function `_state_lock(lock_path: str)`
Cross-platform context manager that acquires an exclusive lock via `O_CREAT|O_EXCL`
and releases it in the `finally` block. Located after `_save_state()`.

### Modified `_increment_deny_counter()`
- Added batch-window check: compares `datetime.datetime.utcnow()` to the stored
  `entry["timestamp"]`; skips incrementing if within `_DENY_BATCH_WINDOW_MS`.
- Only updates `entry["timestamp"]` when actually incrementing.

### Modified `main()` — deny path
Wrapped the read-increment-write in a `_state_lock()` context:
```python
lock_path = os.path.join(scripts_dir, _LOCK_FILE_NAME)
with _state_lock(lock_path):
    state = _load_state(state_path)
    session_id, state = _get_session_id(scripts_dir, state)
    deny_count, now_locked = _increment_deny_counter(state, session_id, threshold)
    _save_state(state_path, state)
```
The pre-lockout check before `decide()` remains unlocked (read-only, benign race).

---

## Files Changed
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py`

---

## Tests Written
Location: `tests/SAF-061/test_saf061_denial_batching.py`

| Test | Description |
|------|-------------|
| `test_single_deny_increments_by_one` | Single deny call increments counter from 0→1 |
| `test_two_rapid_denies_share_one_block` | Two calls within batch window → same count |
| `test_two_spaced_denies_get_separate_blocks` | Calls > 100ms apart → separate counts |
| `test_counter_reaches_threshold_locks_session` | At threshold → `now_locked` is True |
| `test_lock_file_released_after_context` | Lock file removed after context exits |
| `test_lock_no_deadlock_sequential` | Sequential lock acquisitions don't deadlock |
| `test_batch_window_exactly_at_boundary` | Call exactly at 100ms boundary increments |
| `test_batch_window_below_boundary` | Call at 50ms does not increment |
| `test_increment_without_existing_session` | Session not in state → initialized correctly |
| `test_concurrent_increment_deterministic` | Threading test: two threads → combined count by 1 |

---

## Known Limitations
- The lock uses `O_CREAT|O_EXCL` which relies on filesystem atomicity. On some
  network filesystems (NFS without lockd) this may not be atomic, but for local
  VS Code usage this is always a local filesystem.
- The batch window (100ms) is tuned for VS Code's parallel tool dispatch. If a
  future VS Code version dispatches more slowly, this window may need adjustment.
