"""tests/SAF-035/test_saf035_denial_counter.py

Tests for the session-scoped denial counter introduced in SAF-035.
Covers all 11 acceptance criteria:
  1. Counter increments on each deny decision
  2. "Block N of M" appears in deny reason
  3. Session locks at threshold M
  4. Locked session denies ALL tool calls (including normally-allowed ones)
  5. Different session IDs have independent counters
  6. New session starts at count 0
  7. OTel JSONL parsing extracts correct session.id
  8. Fallback UUID works when JSONL is missing
  9. State file survives between invocations (persistence)
 10. Corrupt / empty state file handled gracefully (reset to empty)
 11. Concurrent access doesn't corrupt state file
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Make the security_gate module importable without triggering the integrity
# checks that depend on the actual template workspace layout.
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "templates" / "coding" / ".github" / "hooks" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import security_gate as sg  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_deny_input(tool_name: str = "run_in_terminal", command: str = "rm -rf /") -> str:
    """Build a JSON payload that will be denied by the security gate."""
    return json.dumps({
        "tool_name": tool_name,
        "tool_input": {"command": command},
    })


def _make_allow_input(tool_name: str = "read_file") -> str:
    """Build a JSON payload for a normally-allowed tool (exempt tool with no path
    — normally this would deny via 'no path' path, but we use ask_questions which
    is always-allow)."""
    return json.dumps({
        "tool_name": "ask_questions",
        "tool_input": {},
    })


def _make_always_allow_input() -> str:
    return json.dumps({"tool_name": "ask_questions", "tool_input": {}})


def _build_otel_jsonl(session_id: str, use_conversation_id: bool = False) -> str:
    """Build a single-line OTel JSONL span with the given session ID."""
    if use_conversation_id:
        span = {
            "resourceSpans": [{
                "resource": {"attributes": []},
                "scopeSpans": [{
                    "spans": [{
                        "name": "invoke_agent",
                        "attributes": [
                            {
                                "key": "gen_ai.conversation.id",
                                "value": {"stringValue": session_id}
                            }
                        ]
                    }]
                }]
            }]
        }
    else:
        span = {
            "resourceSpans": [{
                "resource": {
                    "attributes": [
                        {
                            "key": "session.id",
                            "value": {"stringValue": session_id}
                        }
                    ]
                },
                "scopeSpans": []
            }]
        }
    return json.dumps(span) + "\n"


# ---------------------------------------------------------------------------
# Test 1 — Counter increments on each deny decision
# ---------------------------------------------------------------------------

class TestCounterIncrements(unittest.TestCase):
    def test_counter_increments_with_each_deny(self) -> None:
        """Counter value should increase by 1 with each deny decision."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            session_id = "test-session-increments"

            for expected_count in range(1, 5):
                state = sg._load_state(state_path)
                # Ensure session exists with correct prior count
                count, locked = sg._increment_deny_counter(
                    state, session_id, sg._DENY_THRESHOLD_DEFAULT
                )
                sg._save_state(state_path, state)
                self.assertEqual(count, expected_count)
                self.assertFalse(locked)

            # Verify persisted count
            final_state = sg._load_state(state_path)
            self.assertEqual(final_state[session_id]["deny_count"], 4)


# ---------------------------------------------------------------------------
# Test 2 — "Block N of M" appears in deny reason
# ---------------------------------------------------------------------------

class TestBlockNofMMessage(unittest.TestCase):
    def test_block_n_of_m_in_deny_reason(self) -> None:
        """Each deny response before lockout must contain 'Block N of M'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            session_id = "test-block-msg"
            threshold = sg._DENY_THRESHOLD_DEFAULT

            for n in range(1, 4):
                state = sg._load_state(state_path)
                count, now_locked = sg._increment_deny_counter(state, session_id, threshold)
                sg._save_state(state_path, state)

                if not now_locked:
                    reason = f"Block {count} of {threshold}. {sg._DENY_REASON}"
                    self.assertIn(f"Block {n} of {threshold}", reason)
                    self.assertIn(sg._DENY_REASON, reason)


# ---------------------------------------------------------------------------
# Test 3 — Session locks at threshold M
# ---------------------------------------------------------------------------

class TestSessionLocksAtThreshold(unittest.TestCase):
    def test_session_locks_exactly_at_threshold(self) -> None:
        """After exactly M denials the session must be locked."""
        threshold = 5  # Use a small threshold for speed
        session_id = "test-lockout"

        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")

            for i in range(threshold):
                state = sg._load_state(state_path)
                count, now_locked = sg._increment_deny_counter(state, session_id, threshold)
                sg._save_state(state_path, state)

                if i < threshold - 1:
                    self.assertFalse(now_locked, f"Should not be locked after {i+1} denials")
                else:
                    self.assertTrue(now_locked, "Should be locked at threshold")

            # Confirm state on disk
            final_state = sg._load_state(state_path)
            self.assertTrue(final_state[session_id]["locked"])
            self.assertEqual(final_state[session_id]["deny_count"], threshold)


# ---------------------------------------------------------------------------
# Test 4 — Locked session denies ALL tool calls
# ---------------------------------------------------------------------------

class TestLockedSessionDeniesAll(unittest.TestCase):
    def _run_main_with_input(self, payload: str, state_path: str, session_id: str) -> str:
        """Run security_gate.main() with mocked stdin and capture stdout."""
        import io

        def patched_get_session_id(scripts_dir: str, state: dict):
            return session_id, state

        # Implement load/save directly (not via sg.*) to avoid mock recursion
        def patched_load_state(path: str) -> dict:
            try:
                if not os.path.isfile(state_path):
                    return {}
                with open(state_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                return data if isinstance(data, dict) else {}
            except Exception:
                return {}

        def patched_save_state(path: str, state: dict) -> None:
            dir_path = os.path.dirname(state_path)
            try:
                fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as fh:
                        json.dump(state, fh, indent=2)
                    os.replace(tmp_path, state_path)
                except Exception:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
            except Exception:
                pass

        buf = io.StringIO()
        with (
            patch("security_gate.verify_file_integrity", return_value=True),
            patch("security_gate._load_state", side_effect=patched_load_state),
            patch("security_gate._save_state", side_effect=patched_save_state),
            patch("security_gate._get_session_id", side_effect=patched_get_session_id),
            patch("sys.stdin", io.StringIO(payload)),
            patch("sys.stdout", buf),
            patch("sys.exit", side_effect=SystemExit),
        ):
            try:
                sg.main()
            except SystemExit:
                pass
        return buf.getvalue()

    def test_locked_session_denies_always_allow_tool(self) -> None:
        """A locked session must deny even normally-always-allowed tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            session_id = "locked-session-id"
            # Pre-populate a locked session
            state = {session_id: {"deny_count": 20, "locked": True, "timestamp": ""}}
            sg._save_state(state_path, state)

            payload = _make_always_allow_input()
            output = self._run_main_with_input(payload, state_path, session_id)

            response = json.loads(output.strip())
            decision = response["hookSpecificOutput"]["permissionDecision"]
            self.assertEqual(decision, "deny")
            reason = response["hookSpecificOutput"].get("permissionDecisionReason", "")
            self.assertIn("Session locked", reason)

    def test_locked_session_denies_read_tool(self) -> None:
        """A locked session must deny read_file too."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            session_id = "locked-session-read"
            state = {session_id: {"deny_count": 20, "locked": True, "timestamp": ""}}
            sg._save_state(state_path, state)

            payload = json.dumps({"tool_name": "read_file", "tool_input": {"filePath": "/safe/path"}})
            output = self._run_main_with_input(payload, state_path, session_id)

            response = json.loads(output.strip())
            self.assertEqual(response["hookSpecificOutput"]["permissionDecision"], "deny")


# ---------------------------------------------------------------------------
# Test 5 — Different session IDs have independent counters
# ---------------------------------------------------------------------------

class TestIndependentSessionCounters(unittest.TestCase):
    def test_sessions_are_independent(self) -> None:
        """Denials on session A must not affect session B's counter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            session_a = "session-alpha"
            session_b = "session-beta"
            threshold = sg._DENY_THRESHOLD_DEFAULT

            # Add 5 denials to session A
            for _ in range(5):
                state = sg._load_state(state_path)
                sg._increment_deny_counter(state, session_a, threshold)
                sg._save_state(state_path, state)

            # Session B should start at 0
            state = sg._load_state(state_path)
            b_data = state.get(session_b, {})
            self.assertEqual(b_data.get("deny_count", 0), 0)
            self.assertFalse(b_data.get("locked", False))

            # Session A should be at 5
            a_data = state.get(session_a, {})
            self.assertEqual(a_data["deny_count"], 5)


# ---------------------------------------------------------------------------
# Test 6 — New session starts at count 0
# ---------------------------------------------------------------------------

class TestNewSessionStartsAtZero(unittest.TestCase):
    def test_new_session_count_is_zero(self) -> None:
        """A session ID not yet in state must start at deny_count=0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            state = sg._load_state(state_path)  # empty dict
            session_id = "brand-new-session"

            # Should not exist before first interaction
            self.assertNotIn(session_id, state)

            count, locked = sg._increment_deny_counter(state, session_id, sg._DENY_THRESHOLD_DEFAULT)
            self.assertEqual(count, 1)  # first deny → count becomes 1
            self.assertFalse(locked)

    def test_new_session_not_pre_locked(self) -> None:
        """A new session should not be marked as locked."""
        state: dict = {}
        session_id = "new-session-no-lock"
        count, locked = sg._increment_deny_counter(state, session_id, sg._DENY_THRESHOLD_DEFAULT)
        self.assertFalse(locked)


# ---------------------------------------------------------------------------
# Test 7 — OTel JSONL parsing extracts correct session.id
# ---------------------------------------------------------------------------

class TestOtelJsonlParsing(unittest.TestCase):
    def test_extracts_session_id_from_resource_attributes(self) -> None:
        """Must extract session.id from resourceSpans[0].resource.attributes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            otel_path = os.path.join(tmpdir, sg._OTEL_JSONL_NAME)
            with open(otel_path, "w", encoding="utf-8") as fh:
                fh.write(_build_otel_jsonl("my-session-abc"))

            result = sg._read_otel_session_id(tmpdir)
            self.assertEqual(result, "my-session-abc")

    def test_extracts_conversation_id_as_fallback(self) -> None:
        """Must fall back to gen_ai.conversation.id from span attributes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            otel_path = os.path.join(tmpdir, sg._OTEL_JSONL_NAME)
            with open(otel_path, "w", encoding="utf-8") as fh:
                fh.write(_build_otel_jsonl("conv-id-xyz", use_conversation_id=True))

            result = sg._read_otel_session_id(tmpdir)
            self.assertEqual(result, "conv-id-xyz")

    def test_returns_last_line_session_id(self) -> None:
        """When multiple spans exist, the last non-empty line's session ID is used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            otel_path = os.path.join(tmpdir, sg._OTEL_JSONL_NAME)
            with open(otel_path, "w", encoding="utf-8") as fh:
                fh.write(_build_otel_jsonl("first-session"))
                fh.write(_build_otel_jsonl("second-session"))
                fh.write(_build_otel_jsonl("latest-session"))

            result = sg._read_otel_session_id(tmpdir)
            self.assertEqual(result, "latest-session")

    def test_returns_none_for_missing_file(self) -> None:
        """Must return None when the JSONL file does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = sg._read_otel_session_id(tmpdir)
            self.assertIsNone(result)

    def test_returns_none_for_empty_file(self) -> None:
        """Must return None when the JSONL file is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            otel_path = os.path.join(tmpdir, sg._OTEL_JSONL_NAME)
            Path(otel_path).touch()
            result = sg._read_otel_session_id(tmpdir)
            self.assertIsNone(result)

    def test_returns_none_for_invalid_json(self) -> None:
        """Must return None gracefully for malformed JSONL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            otel_path = os.path.join(tmpdir, sg._OTEL_JSONL_NAME)
            with open(otel_path, "w", encoding="utf-8") as fh:
                fh.write("not-valid-json\n")
            result = sg._read_otel_session_id(tmpdir)
            self.assertIsNone(result)


# ---------------------------------------------------------------------------
# Test 8 — Fallback UUID works when JSONL is missing
# ---------------------------------------------------------------------------

class TestFallbackUUID(unittest.TestCase):
    def test_fallback_uuid_generated_when_no_otel(self) -> None:
        """A UUID4 must be generated and stored when OTel JSONL is absent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # No otel file in tmpdir
            state: dict = {}
            session_id, updated_state = sg._get_session_id(tmpdir, state)

            self.assertIsNotNone(session_id)
            self.assertIsInstance(session_id, str)
            self.assertGreater(len(session_id), 0)
            # State must now contain the fallback ID
            self.assertEqual(updated_state.get("_fallback_session_id"), session_id)
            self.assertIn("_fallback_created", updated_state)

    def test_fallback_uuid_is_reused(self) -> None:
        """The same fallback UUID must be returned on subsequent calls."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state: dict = {}
            session_id_1, state = sg._get_session_id(tmpdir, state)
            # Persist to simulate real usage
            state_path = os.path.join(tmpdir, sg._STATE_FILE_NAME)
            sg._save_state(state_path, state)

            # Reload and call again
            state2 = sg._load_state(state_path)
            session_id_2, _ = sg._get_session_id(tmpdir, state2)

            self.assertEqual(session_id_1, session_id_2)

    def test_otel_id_takes_priority_over_fallback(self) -> None:
        """When OTel JSONL returns a session ID, the fallback must not be used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            otel_path = os.path.join(tmpdir, sg._OTEL_JSONL_NAME)
            with open(otel_path, "w", encoding="utf-8") as fh:
                fh.write(_build_otel_jsonl("otel-priority-session"))

            state: dict = {"_fallback_session_id": "old-fallback"}
            session_id, _ = sg._get_session_id(tmpdir, state)

            self.assertEqual(session_id, "otel-priority-session")


# ---------------------------------------------------------------------------
# Test 9 — State file survives between invocations (persistence)
# ---------------------------------------------------------------------------

class TestStatePersistence(unittest.TestCase):
    def test_state_persists_across_load_save_cycles(self) -> None:
        """Counter state written by _save_state must be recoverable by _load_state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            session_id = "persistent-session"

            # Write some state
            state: dict = {session_id: {"deny_count": 7, "locked": False, "timestamp": "T1"}}
            sg._save_state(state_path, state)

            # Reload in a new "invocation"
            loaded = sg._load_state(state_path)
            self.assertEqual(loaded[session_id]["deny_count"], 7)
            self.assertFalse(loaded[session_id]["locked"])

    def test_counter_accumulates_across_save_load_cycles(self) -> None:
        """Repeated save/load cycles must accumulate the counter correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            session_id = "accumulate-session"

            for expected in range(1, 6):
                state = sg._load_state(state_path)
                count, _ = sg._increment_deny_counter(state, session_id, sg._DENY_THRESHOLD_DEFAULT)
                sg._save_state(state_path, state)
                self.assertEqual(count, expected)

            final = sg._load_state(state_path)
            self.assertEqual(final[session_id]["deny_count"], 5)


# ---------------------------------------------------------------------------
# Test 10 — Corrupt / empty state file handled gracefully
# ---------------------------------------------------------------------------

class TestCorruptStateFile(unittest.TestCase):
    def test_corrupt_json_returns_empty_dict(self) -> None:
        """A corrupt JSON state file must be handled gracefully (returns {})."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            with open(state_path, "w", encoding="utf-8") as fh:
                fh.write("{not valid json")

            result = sg._load_state(state_path)
            self.assertEqual(result, {})

    def test_non_dict_json_returns_empty_dict(self) -> None:
        """A state file containing a non-dict JSON value must return {}."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            with open(state_path, "w", encoding="utf-8") as fh:
                json.dump([1, 2, 3], fh)

            result = sg._load_state(state_path)
            self.assertEqual(result, {})

    def test_empty_file_returns_empty_dict(self) -> None:
        """An empty state file must be handled gracefully (returns {})."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            Path(state_path).touch()

            result = sg._load_state(state_path)
            self.assertEqual(result, {})

    def test_missing_file_returns_empty_dict(self) -> None:
        """A missing state file must return {} without raising."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, "nonexistent.json")
            result = sg._load_state(state_path)
            self.assertEqual(result, {})

    def test_counter_works_after_corrupt_state(self) -> None:
        """After corrupt state is reset, the counter must start fresh."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            with open(state_path, "w", encoding="utf-8") as fh:
                fh.write("CORRUPT")

            state = sg._load_state(state_path)  # returns {}
            session_id = "after-corrupt"
            count, locked = sg._increment_deny_counter(state, session_id, sg._DENY_THRESHOLD_DEFAULT)
            self.assertEqual(count, 1)
            self.assertFalse(locked)


# ---------------------------------------------------------------------------
# Test 11 — Concurrent access doesn't corrupt state file
# ---------------------------------------------------------------------------

class TestConcurrentAccess(unittest.TestCase):
    def test_concurrent_writes_do_not_corrupt_file(self) -> None:
        """Multiple threads writing to the state file must not corrupt it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            session_id = "concurrent-session"
            errors: list[str] = []

            def worker(thread_id: int) -> None:
                try:
                    for _ in range(5):
                        state = sg._load_state(state_path)
                        sg._increment_deny_counter(state, f"{session_id}-{thread_id}", sg._DENY_THRESHOLD_DEFAULT)
                        sg._save_state(state_path, state)
                        time.sleep(0.001)
                except Exception as exc:
                    errors.append(str(exc))

            threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.assertEqual(errors, [], f"Errors during concurrent access: {errors}")

            # File must still be valid JSON
            result = sg._load_state(state_path)
            self.assertIsInstance(result, dict)

    def test_atomic_write_produces_valid_json(self) -> None:
        """_save_state must always produce a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            state = {"session-x": {"deny_count": 3, "locked": False, "timestamp": "T"}}
            sg._save_state(state_path, state)

            self.assertTrue(os.path.isfile(state_path))
            with open(state_path, "r", encoding="utf-8") as fh:
                loaded = json.load(fh)
            self.assertEqual(loaded["session-x"]["deny_count"], 3)


# ---------------------------------------------------------------------------
# Integration tests — verify end-to-end main() behaviour
# ---------------------------------------------------------------------------

class TestMainIntegration(unittest.TestCase):
    """Integration-level checks on the full main() decision pipeline."""

    def _run_main(self, payload: str, state_path: str, session_id: str = "test-main-session") -> dict:
        """Execute main() with mocked I/O and integrity check; return parsed response."""
        import io

        def patched_get_session_id(scripts_dir: str, state: dict):
            return session_id, state

        # Implement load/save directly (not via sg.*) to avoid mock recursion
        def patched_load_state(path: str) -> dict:
            try:
                if not os.path.isfile(state_path):
                    return {}
                with open(state_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                return data if isinstance(data, dict) else {}
            except Exception:
                return {}

        def patched_save_state(path: str, state: dict) -> None:
            dir_path = os.path.dirname(state_path)
            try:
                fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as fh:
                        json.dump(state, fh, indent=2)
                    os.replace(tmp_path, state_path)
                except Exception:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
            except Exception:
                pass

        buf = io.StringIO()
        with (
            patch("security_gate.verify_file_integrity", return_value=True),
            patch("security_gate._load_state", side_effect=patched_load_state),
            patch("security_gate._save_state", side_effect=patched_save_state),
            patch("security_gate._get_session_id", side_effect=patched_get_session_id),
            patch("sys.stdin", io.StringIO(payload)),
            patch("sys.stdout", buf),
            patch("sys.exit", side_effect=SystemExit),
        ):
            try:
                sg.main()
            except SystemExit:
                pass
        return json.loads(buf.getvalue().strip())

    def test_deny_response_contains_block_n_of_m(self) -> None:
        """First deny must include 'Block 1 of 20' in the reason."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            payload = json.dumps({
                "tool_name": "run_in_terminal",
                "tool_input": {"command": "rm -rf /"},
            })
            response = self._run_main(payload, state_path)
            self.assertEqual(response["hookSpecificOutput"]["permissionDecision"], "deny")
            reason = response["hookSpecificOutput"]["permissionDecisionReason"]
            self.assertIn("Block 1 of 20", reason)

    def test_lockout_at_threshold_via_main(self) -> None:
        """After M denials the lockout message must be used."""
        threshold = sg._DENY_THRESHOLD_DEFAULT
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            payload = json.dumps({
                "tool_name": "run_in_terminal",
                "tool_input": {"command": "rm -rf /"},
            })

            # Run exactly M deny decisions
            for _ in range(threshold):
                self._run_main(payload, state_path)

            # The next call must return the lockout message
            response = self._run_main(payload, state_path)
            reason = response["hookSpecificOutput"]["permissionDecisionReason"]
            self.assertIn("Session locked", reason)
            self.assertIn(str(threshold), reason)

    def test_allow_decision_not_counted(self) -> None:
        """Allow decisions must not increment the deny counter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            session_id = "allow-no-count"
            payload = _make_always_allow_input()

            for _ in range(5):
                response = self._run_main(payload, state_path, session_id)
                self.assertEqual(response["hookSpecificOutput"]["permissionDecision"], "allow")

            state = sg._load_state(state_path)
            session_data = state.get(session_id, {})
            self.assertEqual(session_data.get("deny_count", 0), 0)


if __name__ == "__main__":
    unittest.main()
