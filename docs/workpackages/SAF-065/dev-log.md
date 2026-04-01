# SAF-065 Dev Log — Increase parallel denial batch window from 100ms to 500ms

## Status
Done

## Assigned To
Developer Agent

## Date
2026-04-01

## Objective
Fix inconsistent parallel denial block coalescing (BUG-169). The 100ms batch window in `_DENY_BATCH_WINDOW_MS` was too tight — during v3.3.6 testing the second batch of 3 parallel denied calls split across Blocks 3 and 4 because OS scheduling delayed one hook invocation just past the 100ms boundary.

## Root Cause
`_DENY_BATCH_WINDOW_MS = 100` (SAF-061). Hook invocations are separate Python processes. When VS Code fires 3 tools in parallel, the OS may schedule the processes within a 100–300ms span rather than simultaneously. If the first invocation acquires the file lock at t=0 and records the timestamp, a third invocation arriving at t=120ms sees age_ms = 120 > 100 → new block. The 100ms window was documented as "parallel same batch" but was effectively too fragile for real-world OS scheduling jitter.

## Fix
Increased `_DENY_BATCH_WINDOW_MS` from `100` to `500` in `security_gate.py`.

500ms is:
- Large enough to absorb normal OS scheduling variance for parallel VS Code tool calls (typically 0–300ms spread)
- Small enough that two consecutive user responses (typically seconds apart) will always produce separate blocks
- Well within the ~2–5s typical gap between separate VS Code response batches

Also:
- Updated the SAF-061 tests that used the hardcoded value `200` (now within the window) to use `sg._DENY_BATCH_WINDOW_MS + 100` instead, making them window-size-agnostic.
- Ran `update_hashes.py` to regenerate `_KNOWN_GOOD_GATE_HASH` after modifying `security_gate.py`.

## Files Changed
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py` — `_DENY_BATCH_WINDOW_MS` 100 → 500, restored `_LOCK_FILE_NAME` adjacent constant, added SAF-065 comment
- `tests/SAF-061/test_saf061_denial_batching.py` — updated two `_ts_ago(200)` calls to `_ts_ago(sg._DENY_BATCH_WINDOW_MS + 100)`
- `tests/SAF-065/test_saf065_batch_window.py` (created)
- `docs/workpackages/workpackages.csv`
- `docs/bugs/bugs.csv` (BUG-169 closed)
