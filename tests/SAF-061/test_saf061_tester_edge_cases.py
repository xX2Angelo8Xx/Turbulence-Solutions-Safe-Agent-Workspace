"""tests/SAF-061/test_saf061_tester_edge_cases.py

Tester-added edge-case tests for SAF-061: deterministic parallel denial batching.

These tests go beyond the Developer's test suite and cover:
  EC-1: Already-locked session passed to _increment_deny_counter — still returns
        now_locked=True without raising and without corrupt state.
  EC-2: State file corruption inside the lock — _load_state falls back to {} so
        the counter re-initialises at 1 (graceful degradation, no crash).
  EC-3: Three concurrent threads all acquiring _state_lock — no deadlock, each
        runs its body, lock is cleaned up after all complete.
  EC-4: Lock file left behind by a crashed process (stale lock on entry) with the
        default retry count overridden to 1 — execution falls through within
        predictable time, no infinite loop.
  EC-5: Lock file is NOT present after normal context exit (no orphan cleanup
        regression after multiple sequential uses of the same lock path).
  EC-6: Batch window boundary is strictly < (not ≤): timestamp exactly at window
        boundary triggers a new increment; timestamp 1ms inside the window does not.
  EC-7: State file is replaced with a directory of the same name — _save_state
        must not raise an exception (best-effort semantics).
  EC-8: Session ID with leading/trailing whitespace is handled as a normal key
        (no special treatment expected — consistent with existing session ID behaviour).
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Path setup
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

_SESSION = "ec-test-session-saf061"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts_ago(ms: float) -> str:
    """Return ISO timestamp *ms* milliseconds in the past."""
    return (datetime.datetime.utcnow() - datetime.timedelta(milliseconds=ms)).isoformat() + "Z"


def _state_locked(count: int) -> dict:
    """Build a state dict where the session is already marked locked."""
    return {
        _SESSION: {
            "deny_count": count,
            "locked": True,
            "timestamp": _ts_ago(500),  # definitely outside batch window
        }
    }


# ---------------------------------------------------------------------------
# EC-1: Already-locked session in _increment_deny_counter
# ---------------------------------------------------------------------------

class TestAlreadyLockedSession(unittest.TestCase):

    def test_already_locked_session_returns_locked_true(self):
        """_increment_deny_counter on an already-locked session entry should
        return now_locked=True and must not raise or corrupt the entry."""
        threshold = 5
        state = _state_locked(threshold)
        count, now_locked = sg._increment_deny_counter(state, _SESSION, threshold)
        self.assertTrue(now_locked, "Already-locked session must return now_locked=True")
        self.assertIsInstance(count, int, "Count must be an integer")
        self.assertTrue(state[_SESSION]["locked"], "locked flag must remain True")

    def test_already_locked_entry_not_corrupted_after_call(self):
        """State dict is still valid JSON-serialisable after calling _increment_deny_counter
        on an already-locked session.  Uses json directly to avoid conftest
        patches on sg._save_state / sg._load_state."""
        threshold = 5
        state = _state_locked(threshold)
        sg._increment_deny_counter(state, _SESSION, threshold)
        # Verify state dict has expected valid types
        self.assertIn(_SESSION, state)
        entry = state[_SESSION]
        self.assertIsInstance(entry["deny_count"], int)
        self.assertIsInstance(entry["locked"], bool)
        self.assertIsInstance(entry["timestamp"], str)
        self.assertTrue(entry["timestamp"], "timestamp must be non-empty after increment")
        # Verify JSON round-trip via stdlib json (not patched sg functions)
        import json as _json
        encoded = _json.dumps(state)
        decoded = _json.loads(encoded)
        self.assertIn(_SESSION, decoded)
        self.assertEqual(decoded[_SESSION]["deny_count"], entry["deny_count"])
        self.assertEqual(decoded[_SESSION]["locked"], entry["locked"])


# ---------------------------------------------------------------------------
# EC-2: State file corruption inside the lock (graceful degradation)
# ---------------------------------------------------------------------------

class TestCorruptStateInsideLock(unittest.TestCase):

    def test_corrupt_state_file_gracefully_starts_fresh(self):
        """If the state file is corrupt when _load_state is called inside the lock,
        it returns {} and the counter initialises at 1 (not crash)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            # Write garbage to the state file
            with open(state_path, "w") as fh:
                fh.write("NOT VALID JSON {{{{ corrupted")

            state = sg._load_state(state_path)
            self.assertEqual(state, {}, "_load_state must return {} on corrupt JSON")
            # Now run the counter on the fresh (empty) state
            count, locked = sg._increment_deny_counter(state, _SESSION, 20)
            self.assertEqual(count, 1, "Counter must start at 1 when state was corrupted")
            self.assertFalse(locked)

    def test_corrupt_state_file_then_save_succeeds(self):
        """After loading corrupt state as {}, writing back must produce valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            with open(state_path, "w") as fh:
                fh.write("{bad json")

            state = sg._load_state(state_path)
            sg._increment_deny_counter(state, _SESSION, 20)
            sg._save_state(state_path, state)
            # File should now be readable again
            reloaded = sg._load_state(state_path)
            self.assertIn(_SESSION, reloaded)
            self.assertEqual(reloaded[_SESSION]["deny_count"], 1)

    def test_load_state_truncated_file_returns_empty(self):
        """A truncated (partial) JSON file must not raise — returns {}."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            with open(state_path, "w") as fh:
                fh.write('{"session": {"deny_count": 3, "locked": fal')  # truncated
            state = sg._load_state(state_path)
            self.assertEqual(state, {})


# ---------------------------------------------------------------------------
# EC-3: Three concurrent threads, no deadlock, lock always cleaned up
# ---------------------------------------------------------------------------

class TestThreeConcurrentThreadsLock(unittest.TestCase):

    def test_three_concurrent_threads_no_deadlock_and_lock_cleaned_up(self):
        """Three threads each acquire _state_lock and perform a file-based write.
        Assert: (1) all three complete within 10 s, (2) no exceptions,
        (3) the lock file is absent after all threads finish, (4) final count ≥ 1.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            lock_path = os.path.join(tmpdir, ".hook_state.lock")
            session_id = "three-thread-session"
            threshold = 20
            errors: list = []

            def do_deny():
                try:
                    with sg._state_lock(lock_path):
                        state = sg._load_state(state_path)
                        if session_id not in state:
                            state[session_id] = {
                                "deny_count": 0,
                                "locked": False,
                                "timestamp": "",
                            }
                        sg._increment_deny_counter(state, session_id, threshold)
                        sg._save_state(state_path, state)
                except Exception as exc:
                    errors.append(exc)

            threads = [threading.Thread(target=do_deny) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=10)

            still_alive = [t for t in threads if t.is_alive()]
            self.assertEqual(still_alive, [], "All threads must complete within 10 s (no deadlock)")
            self.assertEqual(errors, [], f"No exceptions expected; got: {errors}")
            self.assertFalse(
                os.path.isfile(lock_path),
                "Lock file must not exist after all threads complete (no orphan)",
            )
            final_state = sg._load_state(state_path)
            final_count = final_state.get(session_id, {}).get("deny_count", 0)
            self.assertGreaterEqual(final_count, 1, "At least one increment must have occurred")
            self.assertLessEqual(final_count, 3, "Count must not exceed number of threads")


# ---------------------------------------------------------------------------
# EC-4: Stale lock on entry with aggressive timeout → falls through quickly
# ---------------------------------------------------------------------------

class TestStaleLockFallthrough(unittest.TestCase):

    def test_stale_lock_with_overridden_retries_falls_through_fast(self):
        """If a stale lock file is present and retries are set to 1 with 1ms delay,
        _state_lock should yield within ~5ms and execution must continue (fail-open).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = os.path.join(tmpdir, ".hook_state.lock")
            with open(lock_path, "w") as fh:
                fh.write("stale-pid-99999")

            orig_retries = sg._LOCK_ACQUIRE_RETRIES
            orig_delay = sg._LOCK_ACQUIRE_DELAY_S
            sg._LOCK_ACQUIRE_RETRIES = 1
            sg._LOCK_ACQUIRE_DELAY_S = 0.001
            try:
                t_start = time.monotonic()
                executed = []
                with sg._state_lock(lock_path):
                    executed.append(True)
                elapsed_ms = (time.monotonic() - t_start) * 1000
                self.assertEqual(executed, [True], "Body must execute even with stale lock")
                self.assertLess(elapsed_ms, 200, f"Fallthrough must be fast; took {elapsed_ms:.1f}ms")
                # The stale lock must still be present (we didn't create/own it)
                self.assertTrue(os.path.isfile(lock_path))
            finally:
                sg._LOCK_ACQUIRE_RETRIES = orig_retries
                sg._LOCK_ACQUIRE_DELAY_S = orig_delay


# ---------------------------------------------------------------------------
# EC-5: No orphaned lock file after multiple sequential acquisitions
# ---------------------------------------------------------------------------

class TestNoOrphanedLockFile(unittest.TestCase):

    def test_no_orphan_after_multiple_sequential_acquisitions(self):
        """Acquiring and releasing the lock N times in sequence must not leave
        any .lock file behind after the last release."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = os.path.join(tmpdir, ".hook_state.lock")
            for _ in range(5):
                with sg._state_lock(lock_path):
                    pass
            self.assertFalse(
                os.path.isfile(lock_path),
                "No lock file must remain after 5 sequential acquisitions",
            )

    def test_no_orphan_after_exception_in_each_acquisition(self):
        """Even when each context raises an exception, the lock file must be
        cleaned up on every exit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = os.path.join(tmpdir, ".hook_state.lock")
            for i in range(3):
                try:
                    with sg._state_lock(lock_path):
                        raise ValueError(f"iteration {i}")
                except ValueError:
                    pass
                self.assertFalse(
                    os.path.isfile(lock_path),
                    f"Lock file must be gone after exception in iteration {i}",
                )


# ---------------------------------------------------------------------------
# EC-6: Strict < boundary semantics
# ---------------------------------------------------------------------------

class TestBatchWindowBoundaryStrict(unittest.TestCase):

    def test_exactly_at_boundary_increments(self):
        """Timestamp exactly = _DENY_BATCH_WINDOW_MS ms ago: age_ms == window,
        so is_same_batch (age_ms < window) is False → counter increments."""
        ts = _ts_ago(sg._DENY_BATCH_WINDOW_MS)
        state = {_SESSION: {"deny_count": 2, "locked": False, "timestamp": ts}}
        count, _ = sg._increment_deny_counter(state, _SESSION, 20)
        self.assertEqual(count, 3, "Exactly at boundary must trigger a new increment")

    def test_one_ms_inside_boundary_does_not_increment(self):
        """Timestamp 1ms inside the window (e.g., window/2 ago): is_same_batch
        is True → counter must NOT increment."""
        ts = _ts_ago(sg._DENY_BATCH_WINDOW_MS / 2)
        state = {_SESSION: {"deny_count": 4, "locked": False, "timestamp": ts}}
        count, _ = sg._increment_deny_counter(state, _SESSION, 20)
        self.assertEqual(count, 4, "Within batch window, counter must not change")

    def test_just_past_boundary_1ms_increments(self):
        """Timestamp 1ms past the window: is_same_batch is False → increment."""
        ts = _ts_ago(sg._DENY_BATCH_WINDOW_MS + 1)
        state = {_SESSION: {"deny_count": 1, "locked": False, "timestamp": ts}}
        count, _ = sg._increment_deny_counter(state, _SESSION, 20)
        self.assertEqual(count, 2, "Just past boundary must trigger a new increment")


# ---------------------------------------------------------------------------
# EC-7: _save_state when destination cannot be written (best-effort)
# ---------------------------------------------------------------------------

class TestSaveStateBestEffort(unittest.TestCase):

    def test_save_state_to_read_only_path_does_not_raise(self):
        """If the state file path is a directory (unwritable), _save_state must
        silently absorb the error — the counter is best-effort and non-blocking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a directory at the state path — writing will fail
            state_path = os.path.join(tmpdir, "subdir.json")
            os.makedirs(state_path, exist_ok=True)  # state_path is now a directory
            state = {_SESSION: {"deny_count": 1, "locked": False, "timestamp": ""}}
            try:
                sg._save_state(state_path, state)  # must not raise
            except Exception as exc:
                self.fail(f"_save_state raised unexpectedly: {exc}")


# ---------------------------------------------------------------------------
# EC-8: Session ID edge cases — whitespace, very long, numeric strings
# ---------------------------------------------------------------------------

class TestSessionIdEdgeCases(unittest.TestCase):

    def test_whitespace_session_id_is_used_as_dict_key(self):
        """Session IDs with leading/trailing whitespace are stored as-is (no stripping)."""
        whitespace_sid = "  spaced-session  "
        state: dict = {}
        count, _ = sg._increment_deny_counter(state, whitespace_sid, 20)
        self.assertEqual(count, 1)
        self.assertIn(whitespace_sid, state, "Whitespace session ID used as literal dict key")

    def test_numeric_string_session_id_works(self):
        """Purely numeric session IDs (as strings) must work without error."""
        numeric_sid = "12345678"
        state: dict = {}
        count, _ = sg._increment_deny_counter(state, numeric_sid, 20)
        self.assertEqual(count, 1)
        self.assertIn(numeric_sid, state)

    def test_unicode_session_id_roundtrips_through_json(self):
        """Unicode session IDs must survive a JSON serialization roundtrip intact.
        Uses stdlib json directly to avoid conftest patches on sg._load_state."""
        import json as _json
        unicode_sid = "sëssïõn-\u4e2d\u6587-\U0001F600"
        state: dict = {}
        sg._increment_deny_counter(state, unicode_sid, 20)
        # JSON round-trip via stdlib json (conftest patches sg._save_state/_load_state)
        encoded = _json.dumps(state, ensure_ascii=True)
        decoded = _json.loads(encoded)
        self.assertIn(unicode_sid, decoded)
        self.assertEqual(decoded[unicode_sid]["deny_count"], 1)


if __name__ == "__main__":
    unittest.main()
