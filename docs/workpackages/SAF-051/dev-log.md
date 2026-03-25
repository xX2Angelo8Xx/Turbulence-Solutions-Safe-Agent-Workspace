# SAF-051 Dev Log — Fix denial counter session ID resolution

**WP:** SAF-051  
**Branch:** SAF-051/denial-counter-session  
**Developer:** Developer Agent  
**Date:** 2026-03-25  

---

## Problem Statement

`_get_session_id()` in `security_gate.py` falls back to a UUID4 persisted in
`.hook_state.json` when no OTel JSONL session ID is available. This UUID never
changes between conversations, making the denial counter workspace-wide instead
of per-conversation (BUG-118).

## Root Cause

The fallback logic only created a new UUID if no UUID existed yet. Once created,
the UUID was reused indefinitely across all conversations:

```python
fallback_id = state.get("_fallback_session_id")
if not isinstance(fallback_id, str) or not fallback_id:
    fallback_id = str(uuid.uuid4())
    state["_fallback_session_id"] = fallback_id
```

## Fix

Added TTL-based session expiry to the fallback path:

1. Added constant `_FALLBACK_SESSION_TTL_SECONDS = 1800` (30 minutes) in the
   SAF-035 constants block.
2. Modified `_get_session_id()` to track `_fallback_last_seen` timestamp.
3. On each call, if `_fallback_last_seen` is older than TTL → new conversation
   → generate fresh UUID, reset timestamps.
4. On each call, update `_fallback_last_seen` as the heartbeat so active
   conversations keep their session ID.

This means:
- Active conversation (tool calls within 30 min): same session ID, counter accumulates.
- New conversation (gap > 30 min): new UUID, counter resets to 0.

The OTel JSONL method (primary) is unchanged.

## Files Changed

- `templates/agent-workbench/.github/hooks/scripts/security_gate.py`
  - Added `_FALLBACK_SESSION_TTL_SECONDS` constant
  - Modified `_get_session_id()` to expire fallback session after TTL

## Tests Written

Location: `tests/SAF-051/`

- `test_saf051_session_scoping.py` — 14 tests covering:
  - Fresh state creates new UUID
  - Active session reuses UUID
  - Session expires after TTL
  - Expired session resets deny counter
  - Corrupt `_fallback_last_seen` triggers new session
  - Missing timestamp triggers new session
  - OTel path still takes priority when available
  - Cross-session independence (counter isolation)
  - TTL boundary conditions (just before and just after expiry)

## Referenced Bugs

- BUG-118: Denial counter falls back to workspace-wide UUID instead of per-conversation

## Known Limitations

- The TTL (30 min) is pragmatic. A very long conversation pause could falsely
  trigger a new session. This is an acceptable trade-off per the WP requirements.
- The OTel method (primary path) is unaffected — when VS Code OTel is enabled,
  per-conversation scoping is exact.
