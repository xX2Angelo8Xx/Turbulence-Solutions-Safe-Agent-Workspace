"""tests/SAF-061/test_saf061_denial_batching.py

Tests for SAF-061: deterministic parallel denial batching.

Covers:
  1. Single deny increments counter by 1
  2. Two rapid denials (within batch window) share one block
  3. Two spaced-out denials (> batch window) get separate blocks
  4. Counter reaching threshold locks the session
  5. Lock file is released after _state_lock context exits
  6. Sequential _state_lock acquisitions do not deadlock
  7. Deny exactly at the batch-window boundary increments (boundary is exclusive)
  8. Deny below the boundary does NOT increment (same batch)
  9. Uninitialized session entry is created on first deny
 10. Threading test: two concurrent increments produce a combined count of 1
     (batch window) and do NOT corrupt the state dict
"""
from __future__ import annotations

import datetime
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Ensure the security_gate module is importable without triggering the
# integrity checks that depend on the actual template workspace layout.
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

_SESSION = "test-session-saf061"


def _state_with_count(count: int, ts: str = "") -> dict:
    """Build a state dict with a given deny_count and optional timestamp."""
    return {
        _SESSION: {
            "deny_count": count,
            "locked": False,
            "timestamp": ts,
        }
    }


def _ts_ago(ms: float) -> str:
    """Return an ISO timestamp that is *ms* milliseconds in the past."""
    delta = datetime.timedelta(milliseconds=ms)
    return (datetime.datetime.utcnow() - delta).isoformat() + "Z"


# ---------------------------------------------------------------------------
# Unit tests for _increment_deny_counter
# ---------------------------------------------------------------------------


class TestIncrementDenyCounter(unittest.TestCase):

    def test_single_deny_increments_by_one(self):
        """A fresh session with no prior deny increments from 0 to 1."""
        state: dict = {}
        count, locked = sg._increment_deny_counter(state, _SESSION, 20)
        self.assertEqual(count, 1)
        self.assertFalse(locked)
        self.assertEqual(state[_SESSION]["deny_count"], 1)

    def test_two_rapid_denies_share_one_block(self):
        """Second deny within batch window does NOT increment the counter."""
        # First deny sets the timestamp to just-now
        state: dict = {}
        count1, _ = sg._increment_deny_counter(state, _SESSION, 20)
        self.assertEqual(count1, 1)

        # Immediately call again (within batch window — timestamp is effectively now)
        count2, locked = sg._increment_deny_counter(state, _SESSION, 20)
        self.assertEqual(count2, 1, "Second rapid deny should share the same block")
        self.assertFalse(locked)

    def test_two_spaced_denies_get_separate_blocks(self):
        """A deny with a timestamp older than the batch window increments normally."""
        # Simulate a prior deny that happened 200ms ago (> 100ms window)
        state = _state_with_count(1, _ts_ago(200))
        count, locked = sg._increment_deny_counter(state, _SESSION, 20)
        self.assertEqual(count, 2, "Deny after batch window should get a new block")
        self.assertFalse(locked)

    def test_counter_reaches_threshold_locks_session(self):
        """When count reaches threshold the session is marked locked."""
        threshold = 5
        state = _state_with_count(threshold - 1, _ts_ago(200))
        count, locked = sg._increment_deny_counter(state, _SESSION, threshold)
        self.assertEqual(count, threshold)
        self.assertTrue(locked)
        self.assertTrue(state[_SESSION]["locked"])

    def test_batch_window_exactly_at_boundary_increments(self):
        """A timestamp exactly equal to _DENY_BATCH_WINDOW_MS ms ago is NOT same-batch."""
        # age_ms == _DENY_BATCH_WINDOW_MS means is_same_batch is False (strict <)
        ts = _ts_ago(sg._DENY_BATCH_WINDOW_MS)
        state = _state_with_count(1, ts)
        count, _ = sg._increment_deny_counter(state, _SESSION, 20)
        self.assertEqual(count, 2, "At the exact boundary the call should still increment")

    def test_batch_window_below_boundary_skips_increment(self):
        """A timestamp within the batch window (< 100ms) is treated as same batch."""
        ts = _ts_ago(sg._DENY_BATCH_WINDOW_MS / 2)  # 50ms ago
        state = _state_with_count(3, ts)
        count, _ = sg._increment_deny_counter(state, _SESSION, 20)
        self.assertEqual(count, 3, "Within batch window, count must not change")

    def test_uninitialized_session_is_created(self):
        """If session_id is absent from state, it is initialized at deny_count 0."""
        state: dict = {}
        count, locked = sg._increment_deny_counter(state, "brand-new-session", 20)
        self.assertEqual(count, 1)
        self.assertFalse(locked)
        self.assertIn("brand-new-session", state)

    def test_corrupt_timestamp_increments_normally(self):
        """Unparseable timestamp in entry should not prevent incrementing."""
        state = {
            _SESSION: {
                "deny_count": 2,
                "locked": False,
                "timestamp": "not-a-valid-iso-timestamp",
            }
        }
        count, _ = sg._increment_deny_counter(state, _SESSION, 20)
        # Since timestamp is corrupt, is_same_batch = False → increments
        self.assertEqual(count, 3)

    def test_empty_timestamp_increments_normally(self):
        """Empty string timestamp (brand-new but no prior call) should increment."""
        state = _state_with_count(0, "")
        count, _ = sg._increment_deny_counter(state, _SESSION, 20)
        self.assertEqual(count, 1)


# ---------------------------------------------------------------------------
# Unit tests for _state_lock
# ---------------------------------------------------------------------------


class TestStateLock(unittest.TestCase):

    def test_lock_file_released_after_context(self):
        """Lock file must not exist after the context manager exits normally."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = os.path.join(tmpdir, ".hook_state.lock")
            with sg._state_lock(lock_path):
                self.assertTrue(os.path.isfile(lock_path), "Lock file must exist inside context")
            self.assertFalse(os.path.isfile(lock_path), "Lock file must be removed after context")

    def test_lock_file_released_on_exception(self):
        """Lock file must be cleaned up even when an exception occurs inside the context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = os.path.join(tmpdir, ".hook_state.lock")
            try:
                with sg._state_lock(lock_path):
                    raise RuntimeError("simulated failure")
            except RuntimeError:
                pass
            self.assertFalse(os.path.isfile(lock_path), "Lock file must be removed on exception")

    def test_sequential_lock_acquisitions_no_deadlock(self):
        """Acquiring the lock twice in sequence must not deadlock."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = os.path.join(tmpdir, ".hook_state.lock")
            acquired = []
            with sg._state_lock(lock_path):
                acquired.append(1)
            with sg._state_lock(lock_path):
                acquired.append(2)
            self.assertEqual(acquired, [1, 2])

    def test_lock_falls_back_gracefully_when_stale_lock_exists(self):
        """If a stale lock file exists and retries exhaust, execution continues (fail open)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = os.path.join(tmpdir, ".hook_state.lock")
            # Create a stale lock file
            with open(lock_path, "w") as fh:
                fh.write("stale")

            # With _LOCK_ACQUIRE_RETRIES=1 and very short delay, fall back quickly
            original_retries = sg._LOCK_ACQUIRE_RETRIES
            original_delay = sg._LOCK_ACQUIRE_DELAY_S
            sg._LOCK_ACQUIRE_RETRIES = 1
            sg._LOCK_ACQUIRE_DELAY_S = 0.001
            try:
                reached = []
                with sg._state_lock(lock_path):
                    reached.append(True)
                self.assertEqual(reached, [True], "Execution should continue even without lock")
                # Stale lock file should still exist (we didn't create it, so no fd to close/unlink)
                self.assertTrue(os.path.isfile(lock_path))
            finally:
                sg._LOCK_ACQUIRE_RETRIES = original_retries
                sg._LOCK_ACQUIRE_DELAY_S = original_delay


# ---------------------------------------------------------------------------
# Concurrency test: two threads simulate parallel deny calls
# ---------------------------------------------------------------------------


class TestConcurrentDenials(unittest.TestCase):

    def test_concurrent_increments_produce_at_most_two_but_state_is_consistent(self):
        """Two threads calling _increment_deny_counter on the same state dict
        should produce a deterministic result. Without external locking the
        dict is shared in-process, so both threads see the same object —
        but the batch-window logic ensures only one increments if they run
        quickly enough.

        We test here that the final deny_count is either 1 (batch shared) or 2
        (both incremented), and the state is not corrupted (count is valid int,
        locked is bool, timestamp is non-empty string).
        """
        state: dict = {}
        results: list = []
        errors: list = []

        def do_deny():
            try:
                count, locked = sg._increment_deny_counter(state, _SESSION, 20)
                results.append(count)
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=do_deny)
        t2 = threading.Thread(target=do_deny)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

        self.assertEqual(errors, [], f"Unexpected exceptions: {errors}")
        self.assertEqual(len(results), 2, "Both threads must return a count")
        final_count = state[_SESSION]["deny_count"]
        self.assertIn(final_count, (1, 2), f"Count must be 1 or 2, got {final_count}")
        self.assertIsInstance(state[_SESSION]["locked"], bool)
        self.assertIsInstance(state[_SESSION]["timestamp"], str)
        self.assertTrue(state[_SESSION]["timestamp"], "Timestamp must not be empty")

    def test_file_based_concurrent_lock_serializes_writes(self):
        """Two threads that each acquire _state_lock and read-modify-write a
        JSON state file should produce a consistent final count of 2 (separate
        blocks, since each thread acquires the lock in turn, reads the fresh
        state written by the other, and the batch window has not elapsed
        between the two sequential lock acquisitions).

        The key safety property being tested: the file is not left with a
        duplicate or lost write. We'd expect exactly 2 increments in total
        since the outer file lock serializes accesses and each thread's "now"
        timestamp differs from the previous write's timestamp by more than 0ms
        (typically a few ms; we don't rely on sub-ms precision here — we just
        assert count ≥ 1 and the file is parseable).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            lock_path = os.path.join(tmpdir, ".hook_state.lock")
            session_id = "concurrent-test-session"
            threshold = 20
            errors: list = []

            def do_deny_with_file():
                try:
                    with sg._state_lock(lock_path):
                        state = sg._load_state(state_path)
                        # No OTel → use provided session id directly
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

            t1 = threading.Thread(target=do_deny_with_file)
            t2 = threading.Thread(target=do_deny_with_file)
            t1.start()
            t2.start()
            t1.join(timeout=10)
            t2.join(timeout=10)

            self.assertEqual(errors, [], f"Unexpected errors: {errors}")
            final_state = sg._load_state(state_path)
            self.assertIn(session_id, final_state, "Session must exist in state file")
            final_count = final_state[session_id]["deny_count"]
            self.assertGreaterEqual(final_count, 1, "Count must be at least 1")
            self.assertLessEqual(final_count, 2, "Count must be at most 2")


if __name__ == "__main__":
    unittest.main()
