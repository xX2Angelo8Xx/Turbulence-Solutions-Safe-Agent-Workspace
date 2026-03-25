"""tests/SAF-051/test_saf051_session_scoping.py

Tests for SAF-051: TTL-based fallback session expiry in _get_session_id().

Acceptance criteria verified:
  1. Fresh state produces a new UUID
  2. Active session (heartbeat < TTL) reuses the same UUID
  3. Inactive session (heartbeat >= TTL) produces a new UUID
  4. After expiry the denial counter resets (new session starts at 0)
  5. Corrupt _fallback_last_seen triggers new session
  6. Missing _fallback_last_seen (legacy state) triggers new session
  7. OTel path still takes priority when the JSONL file provides a valid ID
  8. Two distinct TTL-expired sessions are independent (no counter bleed)
  9. Boundary: exactly TTL seconds ago triggers expiry
 10. Boundary: one second before TTL does NOT trigger expiry
 11. _fallback_last_seen is updated (heartbeat) on every successful call
 12. Fresh UUID is a valid UUID4 string
 13. Regression: old state without _fallback_last_seen is migrated gracefully
 14. Regression: deny counter does not bleed across TTL-expired sessions
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Make security_gate importable without triggering integrity checks.
# ---------------------------------------------------------------------------
SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "templates"
    / "agent-workbench"
    / ".github"
    / "hooks"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS_DIR))
import security_gate as sg  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso(dt: datetime.datetime) -> str:
    return dt.isoformat() + "Z"


def _ago(seconds: float) -> str:
    """Return ISO timestamp for `seconds` before now."""
    return _iso(datetime.datetime.utcnow() - datetime.timedelta(seconds=seconds))


def _fresh_state() -> dict:
    return {}


def _state_with_session(session_id: str, last_seen_seconds_ago: float) -> dict:
    return {
        "_fallback_session_id": session_id,
        "_fallback_last_seen": _ago(last_seen_seconds_ago),
        "_fallback_created": _ago(last_seen_seconds_ago + 60),
    }


def _call_get_session_id(state: dict, scripts_dir: str = "/no/otel") -> "tuple[str, dict]":
    """Call _get_session_id with OTel disabled (no JSONL file present)."""
    with patch.object(sg, "_read_otel_session_id", return_value=None):
        return sg._get_session_id(scripts_dir, state)


# ---------------------------------------------------------------------------
# Test: fresh state
# ---------------------------------------------------------------------------

class TestFreshState:
    def test_fresh_state_creates_uuid(self):
        """Fresh empty state yields a valid UUID4."""
        state = _fresh_state()
        sid, new_state = _call_get_session_id(state)
        assert isinstance(sid, str)
        assert len(sid) == 36  # UUID4 canonical form
        # Must be parseable as UUID
        uuid.UUID(sid)

    def test_fresh_state_stores_session_id(self):
        state = _fresh_state()
        sid, new_state = _call_get_session_id(state)
        assert new_state.get("_fallback_session_id") == sid

    def test_fresh_state_stores_last_seen(self):
        state = _fresh_state()
        _, new_state = _call_get_session_id(state)
        assert "_fallback_last_seen" in new_state
        # Should be parseable as ISO datetime
        ts = new_state["_fallback_last_seen"].rstrip("Z")
        datetime.datetime.fromisoformat(ts)  # raises if invalid

    def test_fresh_state_stores_created_timestamp(self):
        state = _fresh_state()
        _, new_state = _call_get_session_id(state)
        assert "_fallback_created" in new_state


# ---------------------------------------------------------------------------
# Test: active session (within TTL)
# ---------------------------------------------------------------------------

class TestActiveSession:
    def test_active_session_reuses_id(self):
        """Session seen 1 minute ago reuses the same UUID."""
        existing_id = str(uuid.uuid4())
        state = _state_with_session(existing_id, last_seen_seconds_ago=60)
        sid, _ = _call_get_session_id(state)
        assert sid == existing_id

    def test_active_session_updates_heartbeat(self):
        """_fallback_last_seen is refreshed on each call."""
        existing_id = str(uuid.uuid4())
        old_ts = _ago(120)  # 2 min ago
        state = _state_with_session(existing_id, last_seen_seconds_ago=120)
        _, new_state = _call_get_session_id(state)
        # Heartbeat should be newer than old_ts
        new_ts = new_state["_fallback_last_seen"]
        assert new_ts > old_ts

    def test_boundary_just_before_ttl_does_not_expire(self):
        """1 second before TTL → same session."""
        ttl = sg._FALLBACK_SESSION_TTL_SECONDS
        existing_id = str(uuid.uuid4())
        state = _state_with_session(existing_id, last_seen_seconds_ago=ttl - 1)
        sid, _ = _call_get_session_id(state)
        assert sid == existing_id


# ---------------------------------------------------------------------------
# Test: expired session (past TTL)
# ---------------------------------------------------------------------------

class TestExpiredSession:
    def test_expired_session_creates_new_id(self):
        """Session older than TTL → new UUID."""
        ttl = sg._FALLBACK_SESSION_TTL_SECONDS
        existing_id = str(uuid.uuid4())
        state = _state_with_session(existing_id, last_seen_seconds_ago=ttl + 1)
        sid, _ = _call_get_session_id(state)
        assert sid != existing_id

    def test_boundary_exactly_ttl_triggers_expiry(self):
        """Exactly TTL seconds ago → new session (>= comparison)."""
        ttl = sg._FALLBACK_SESSION_TTL_SECONDS
        existing_id = str(uuid.uuid4())
        # Construct state where age == TTL exactly
        last_seen = datetime.datetime.utcnow() - datetime.timedelta(seconds=ttl)
        state = {
            "_fallback_session_id": existing_id,
            "_fallback_last_seen": _iso(last_seen),
        }
        sid, _ = _call_get_session_id(state)
        assert sid != existing_id

    def test_expired_session_updates_created_timestamp(self):
        ttl = sg._FALLBACK_SESSION_TTL_SECONDS
        existing_id = str(uuid.uuid4())
        state = _state_with_session(existing_id, last_seen_seconds_ago=ttl + 60)
        _, new_state = _call_get_session_id(state)
        assert new_state["_fallback_session_id"] != existing_id
        assert "_fallback_created" in new_state


# ---------------------------------------------------------------------------
# Test: corrupt / missing timestamps
# ---------------------------------------------------------------------------

class TestCorruptTimestamp:
    def test_corrupt_last_seen_creates_new_session(self):
        """Non-ISO _fallback_last_seen → treat as expired → new UUID."""
        existing_id = str(uuid.uuid4())
        state = {
            "_fallback_session_id": existing_id,
            "_fallback_last_seen": "not-a-date",
        }
        sid, _ = _call_get_session_id(state)
        assert sid != existing_id

    def test_missing_last_seen_creates_new_session(self):
        """Legacy state with no _fallback_last_seen → new UUID (migration)."""
        existing_id = str(uuid.uuid4())
        # Old-style state: only has _fallback_session_id (no timestamp)
        state = {"_fallback_session_id": existing_id}
        sid, _ = _call_get_session_id(state)
        assert sid != existing_id

    def test_empty_last_seen_creates_new_session(self):
        existing_id = str(uuid.uuid4())
        state = {
            "_fallback_session_id": existing_id,
            "_fallback_last_seen": "",
        }
        sid, _ = _call_get_session_id(state)
        assert sid != existing_id


# ---------------------------------------------------------------------------
# Test: OTel priority
# ---------------------------------------------------------------------------

class TestOtelPriority:
    def test_otel_id_takes_priority_over_fallback(self):
        """When OTel returns a session ID, it must be used regardless of state."""
        otel_session = "otel-session-abc-123"
        state = _state_with_session(str(uuid.uuid4()), last_seen_seconds_ago=10)
        with patch.object(sg, "_read_otel_session_id", return_value=otel_session):
            sid, new_state = sg._get_session_id("/scripts", state)
        assert sid == otel_session
        # State must not have been mutated by the OTel path
        assert new_state.get("_fallback_session_id") != otel_session

    def test_otel_id_returns_unchanged_state(self):
        """OTel path returns state dict unmodified."""
        state = {"_fallback_session_id": "old-id", "some_key": "value"}
        with patch.object(sg, "_read_otel_session_id", return_value="otel-sid"):
            _, new_state = sg._get_session_id("/scripts", state)
        assert new_state == state


# ---------------------------------------------------------------------------
# Test: counter isolation across sessions
# ---------------------------------------------------------------------------

class TestCounterIsolation:
    def test_deny_counter_does_not_bleed_to_new_session(self):
        """After TTL expiry the new session has deny_count=0."""
        ttl = sg._FALLBACK_SESSION_TTL_SECONDS
        old_id = str(uuid.uuid4())
        state = _state_with_session(old_id, last_seen_seconds_ago=ttl + 60)
        # Simulate old session had deny_count=5
        state[old_id] = {"deny_count": 5, "locked": False, "timestamp": _ago(ttl + 60)}

        with patch.object(sg, "_read_otel_session_id", return_value=None):
            new_id, updated_state = sg._get_session_id("/scripts", state)

        assert new_id != old_id
        # New session entry should not exist yet (deny_count will be set on first deny)
        assert new_id not in updated_state or updated_state.get(new_id, {}).get("deny_count", 0) == 0

    def test_two_expired_sessions_are_independent(self):
        """Two calls after expiry produce two different UUIDs."""
        ttl = sg._FALLBACK_SESSION_TTL_SECONDS
        state1 = _state_with_session(str(uuid.uuid4()), last_seen_seconds_ago=ttl + 60)
        state2 = _state_with_session(str(uuid.uuid4()), last_seen_seconds_ago=ttl + 60)

        with patch.object(sg, "_read_otel_session_id", return_value=None):
            sid1, _ = sg._get_session_id("/scripts", state1)
            sid2, _ = sg._get_session_id("/scripts", state2)

        assert sid1 != sid2
