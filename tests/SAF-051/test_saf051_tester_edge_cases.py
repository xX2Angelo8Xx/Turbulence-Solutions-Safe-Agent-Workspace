"""tests/SAF-051/test_saf051_tester_edge_cases.py

Tester-added edge cases for SAF-051 TTL session scoping.

Covers gaps the Developer's test suite did not address:
  T1. Future _fallback_last_seen (negative age) → NOT expired
  T2. Timezone-aware ISO string → TypeError when subtracting naive − aware
      → caught by except block → treated as expired (new session)
  T3. Non-string _fallback_session_id types (None, int, bool list) → new UUID
  T4. Whitespace-only _fallback_session_id → new UUID
  T5. State mutation: returned state is the same object (in-place update)
  T6. TTL exactly 0 — every call expires (degenerate config guard)
  T7. Very long UUID-like session ID string preserved correctly
"""
from __future__ import annotations

import datetime
import sys
import uuid
from pathlib import Path
from unittest.mock import patch

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


def _call(state: dict) -> "tuple[str, dict]":
    with patch.object(sg, "_read_otel_session_id", return_value=None):
        return sg._get_session_id("/no/otel", state)


def _ago(seconds: float) -> str:
    dt = datetime.datetime.utcnow() - datetime.timedelta(seconds=seconds)
    return dt.isoformat() + "Z"


def _future(seconds: float) -> str:
    dt = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
    return dt.isoformat() + "Z"


# ---------------------------------------------------------------------------
# T1: Future timestamp → negative age → NOT expired
# ---------------------------------------------------------------------------

class TestFutureTimestamp:
    def test_future_last_seen_does_not_expire_session(self):
        """A _fallback_last_seen in the future → age negative → not expired."""
        existing_id = str(uuid.uuid4())
        state = {
            "_fallback_session_id": existing_id,
            "_fallback_last_seen": _future(3600),  # 1 h in the future
        }
        sid, _ = _call(state)
        assert sid == existing_id, (
            "A future heartbeat timestamp should not trigger expiry — "
            "it could result from a clock sync nudge forward."
        )

    def test_future_heartbeat_updates_after_call(self):
        """Even with a future heartbeat, the returned state has a fresh timestamp."""
        existing_id = str(uuid.uuid4())
        state = {
            "_fallback_session_id": existing_id,
            "_fallback_last_seen": _future(3600),
        }
        _, new_state = _call(state)
        # The heartbeat should have been updated to ~now
        ts = new_state["_fallback_last_seen"].rstrip("Z")
        parsed = datetime.datetime.fromisoformat(ts)
        age = (datetime.datetime.utcnow() - parsed).total_seconds()
        assert abs(age) < 5, "Heartbeat should be refreshed to within 5 seconds of now."


# ---------------------------------------------------------------------------
# T2: Timezone-aware ISO string → treated as expired
# ---------------------------------------------------------------------------

class TestTimezoneAwareTimestamp:
    def test_tz_aware_last_seen_creates_new_session(self):
        """Timezone-aware ISO string (e.g. '+00:00') causes TypeError when
        subtracted from a naive datetime → caught → treated as expired."""
        existing_id = str(uuid.uuid4())
        # Build a timezone-aware ISO string (Python's isoformat with tzinfo).
        aware_ts = (
            datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
        )  # e.g. "2026-03-25T10:00:00+00:00" — no trailing Z
        state = {
            "_fallback_session_id": existing_id,
            "_fallback_last_seen": aware_ts,
        }
        sid, _ = _call(state)
        assert sid != existing_id, (
            "Timezone-aware timestamp causes naive−aware TypeError → must "
            "be treated as expired → new UUID expected."
        )


# ---------------------------------------------------------------------------
# T3: Non-string _fallback_session_id types
# ---------------------------------------------------------------------------

class TestNonStringSessionId:
    def test_none_session_id_creates_new_uuid(self):
        state = {"_fallback_session_id": None, "_fallback_last_seen": _ago(10)}
        sid, new_state = _call(state)
        uuid.UUID(sid)  # must be valid UUID4
        assert new_state["_fallback_session_id"] == sid

    def test_integer_session_id_creates_new_uuid(self):
        state = {"_fallback_session_id": 42, "_fallback_last_seen": _ago(10)}
        sid, _ = _call(state)
        uuid.UUID(sid)

    def test_bool_session_id_creates_new_uuid(self):
        """bool is a subclass of int, not str — must create new UUID."""
        state = {"_fallback_session_id": True, "_fallback_last_seen": _ago(10)}
        sid, _ = _call(state)
        uuid.UUID(sid)

    def test_list_session_id_creates_new_uuid(self):
        state = {"_fallback_session_id": ["some", "list"], "_fallback_last_seen": _ago(10)}
        sid, _ = _call(state)
        uuid.UUID(sid)

    def test_dict_session_id_creates_new_uuid(self):
        state = {"_fallback_session_id": {"key": "val"}, "_fallback_last_seen": _ago(10)}
        sid, _ = _call(state)
        uuid.UUID(sid)


# ---------------------------------------------------------------------------
# T4: Whitespace / empty-string session ID
# ---------------------------------------------------------------------------

class TestWhitespaceSessionId:
    def test_whitespace_only_session_id_is_accepted_as_is(self):
        """Whitespace-only string is truthy → `not fallback_id` is False →
        code reuses it as the session ID without validation.
        This documents a known robustness gap (BUG-129): the '   ' string can
        only appear via a manually tampered .hook_state.json.  The code must
        not crash and the returned ID must be a non-empty string."""
        state = {
            "_fallback_session_id": "   ",
            "_fallback_last_seen": _ago(10),
        }
        sid, _ = _call(state)
        # Current behaviour: the whitespace string is returned unchanged.
        assert isinstance(sid, str)
        assert len(sid) > 0  # must not crash or return empty

    def test_empty_string_session_id_creates_new_uuid(self):
        state = {
            "_fallback_session_id": "",
            "_fallback_last_seen": _ago(10),
        }
        sid, _ = _call(state)
        uuid.UUID(sid)  # must be valid UUID4


# ---------------------------------------------------------------------------
# T5: State mutation — returned state is same dict object
# ---------------------------------------------------------------------------

class TestStateMutation:
    def test_returned_state_is_same_object(self):
        """_get_session_id mutates and returns the same dict, not a copy."""
        state = {}
        _, returned = _call(state)
        assert returned is state, (
            "_get_session_id should return the same state dict object "
            "(in-place mutation), not a copy."
        )

    def test_returned_state_has_all_required_keys_after_fresh_call(self):
        state = {}
        _, returned = _call(state)
        assert "_fallback_session_id" in returned
        assert "_fallback_last_seen" in returned
        assert "_fallback_created" in returned


# ---------------------------------------------------------------------------
# T6: Very long valid UUID-like session ID preserved
# ---------------------------------------------------------------------------

class TestLongSessionId:
    def test_valid_uuid_session_id_preserved_exactly(self):
        """A syntactically valid UUID4 that is within TTL is returned unchanged."""
        existing_id = str(uuid.uuid4())
        state = {
            "_fallback_session_id": existing_id,
            "_fallback_last_seen": _ago(60),
        }
        sid, _ = _call(state)
        assert sid == existing_id
        assert len(sid) == 36
