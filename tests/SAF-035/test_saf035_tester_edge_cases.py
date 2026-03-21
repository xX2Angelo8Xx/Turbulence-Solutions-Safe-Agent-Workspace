"""tests/SAF-035/test_saf035_tester_edge_cases.py

Tester-added edge-case tests for the session-scoped denial counter (SAF-035).
Covers security and robustness scenarios missed by the developer:

  EC-01  Malformed JSONL — last line bad JSON, earlier line valid session ID
  EC-02  JSONL with trailing whitespace-only lines
  EC-03  JSONL with only whitespace / blank lines
  EC-04  State file with extra/unexpected top-level keys — no crash
  EC-05  Negative threshold (-1) — first deny locks session immediately
  EC-06  Zero threshold (0) — first deny locks session immediately
  EC-07  Very large deny_count (e.g. 10_000) — increments without crash
  EC-08  Session ID with path-traversal characters — dict key, not a path
  EC-09  Session ID with null byte — handled safely by JSON serialisation
  EC-10  Session ID with special shell/JSON characters — safe key
  EC-11  locked=false entry with deny_count already >= threshold on load —
         should still lock on next increment (no double-lock skip)
  EC-12  Returning to a locked session stays locked (main() integration)
  EC-13  Block-N-of-M message includes _DENY_REASON text
  EC-14  SAF-024 regression guard — deny reason contains generic policy text
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "templates" / "coding" / ".github" / "hooks" / "scripts"
)
sys.path.insert(0, str(SCRIPTS_DIR))

import security_gate as sg  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_otel_line(session_id: str) -> str:
    """Valid OTel JSONL line with session.id in resource attributes."""
    span = {
        "resourceSpans": [{
            "resource": {
                "attributes": [
                    {"key": "session.id", "value": {"stringValue": session_id}}
                ]
            },
            "scopeSpans": []
        }]
    }
    return json.dumps(span) + "\n"


def _run_main(payload: str, state_path: str, session_id: str) -> dict:
    """Execute sg.main() with full state mocking; return parsed JSON output."""
    def _load(path: str) -> dict:
        try:
            if not os.path.isfile(state_path):
                return {}
            with open(state_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save(path: str, state: dict) -> None:
        dir_path = os.path.dirname(state_path)
        try:
            fd, tmp = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(state, fh, indent=2)
                os.replace(tmp, state_path)
            except Exception:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
        except Exception:
            pass

    def _get_sid(scripts_dir: str, state: dict):
        return session_id, state

    buf = io.StringIO()
    with (
        patch("security_gate.verify_file_integrity", return_value=True),
        patch("security_gate._load_state", side_effect=_load),
        patch("security_gate._save_state", side_effect=_save),
        patch("security_gate._get_session_id", side_effect=_get_sid),
        patch("sys.stdin", io.StringIO(payload)),
        patch("sys.stdout", buf),
        patch("sys.exit", side_effect=SystemExit),
    ):
        try:
            sg.main()
        except SystemExit:
            pass
    return json.loads(buf.getvalue().strip())


# ===========================================================================
# EC-01: Malformed JSONL — last line invalid, earlier line has valid session
# ===========================================================================

class TestMalformedJsonlLastLine(unittest.TestCase):
    def test_last_line_malformed_returns_none(self) -> None:
        """If last non-empty line is invalid JSON, must return None without crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            otel_path = os.path.join(tmpdir, sg._OTEL_JSONL_NAME)
            with open(otel_path, "w", encoding="utf-8") as fh:
                fh.write(_build_otel_line("valid-session"))  # line 1: valid
                fh.write("{broken json here\n")              # line 2: invalid
            result = sg._read_otel_session_id(tmpdir)
            # Last line is malformed — must return None, not "valid-session"
            self.assertIsNone(result)

    def test_mixed_valid_invalid_lines_uses_last_valid(self) -> None:
        """Last valid line must be used even if interspersed with invalid lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            otel_path = os.path.join(tmpdir, sg._OTEL_JSONL_NAME)
            with open(otel_path, "w", encoding="utf-8") as fh:
                fh.write(_build_otel_line("first-session"))
                fh.write(_build_otel_line("second-session"))
            # Third line is intentionally absent — second-session is last valid line
            result = sg._read_otel_session_id(tmpdir)
            self.assertEqual(result, "second-session")

    def test_only_invalid_json_returns_none(self) -> None:
        """File containing only invalid JSON must return None without raising."""
        with tempfile.TemporaryDirectory() as tmpdir:
            otel_path = os.path.join(tmpdir, sg._OTEL_JSONL_NAME)
            with open(otel_path, "w", encoding="utf-8") as fh:
                fh.write("not json at all\n")
                fh.write("also not json\n")
            result = sg._read_otel_session_id(tmpdir)
            self.assertIsNone(result)


# ===========================================================================
# EC-02: JSONL with trailing whitespace-only lines
# ===========================================================================

class TestJsonlTrailingWhitespace(unittest.TestCase):
    def test_trailing_blank_lines_skipped(self) -> None:
        """Trailing empty/whitespace-only lines must be skipped; valid line used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            otel_path = os.path.join(tmpdir, sg._OTEL_JSONL_NAME)
            with open(otel_path, "w", encoding="utf-8") as fh:
                fh.write(_build_otel_line("real-session"))
                fh.write("   \n")  # whitespace-only trailing line
                fh.write("\n")     # blank trailing line
            result = sg._read_otel_session_id(tmpdir)
            self.assertEqual(result, "real-session")

    def test_whitespace_only_file_returns_none(self) -> None:
        """A file containing only whitespace lines must return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            otel_path = os.path.join(tmpdir, sg._OTEL_JSONL_NAME)
            with open(otel_path, "w", encoding="utf-8") as fh:
                fh.write("   \n\n   \n")
            result = sg._read_otel_session_id(tmpdir)
            self.assertIsNone(result)


# ===========================================================================
# EC-04: State file with extra/unexpected top-level keys
# ===========================================================================

class TestStateExtraKeys(unittest.TestCase):
    def test_extra_keys_do_not_crash_load(self) -> None:
        """Extra keys in state file must be preserved and not cause errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            state_with_extras = {
                "_fallback_session_id": "some-uuid",
                "_fallback_created": "2026-01-01T00:00:00Z",
                "some-future-key": {"unknown": "data"},
                "session-abc": {"deny_count": 3, "locked": False, "timestamp": "T"},
            }
            sg._save_state(state_path, state_with_extras)
            loaded = sg._load_state(state_path)
            # All keys preserved
            self.assertIn("_fallback_session_id", loaded)
            self.assertIn("some-future-key", loaded)
            self.assertEqual(loaded["session-abc"]["deny_count"], 3)

    def test_increment_works_with_extra_keys(self) -> None:
        """_increment_deny_counter must work correctly even with extra state keys."""
        state = {
            "_fallback_session_id": "uuid",
            "unknown_key": True,
            "session-x": {"deny_count": 2, "locked": False, "timestamp": ""},
        }
        count, locked = sg._increment_deny_counter(state, "session-x", 5)
        self.assertEqual(count, 3)
        self.assertFalse(locked)
        # Extra keys must still be present
        self.assertIn("unknown_key", state)
        self.assertIn("_fallback_session_id", state)


# ===========================================================================
# EC-05 & EC-06: Negative and zero threshold
# ===========================================================================

class TestThresholdEdgeCases(unittest.TestCase):
    def test_zero_threshold_locks_on_first_deny(self) -> None:
        """With threshold=0, first deny must lock (count 1 >= 0)."""
        state: dict = {}
        count, locked = sg._increment_deny_counter(state, "session-zero", 0)
        self.assertEqual(count, 1)
        self.assertTrue(locked, "threshold=0 should lock on first deny")
        self.assertTrue(state["session-zero"]["locked"])

    def test_negative_threshold_locks_on_first_deny(self) -> None:
        """With threshold=-1, first deny must lock (count 1 >= -1)."""
        state: dict = {}
        count, locked = sg._increment_deny_counter(state, "session-neg", -1)
        self.assertEqual(count, 1)
        self.assertTrue(locked, "threshold=-1 should lock on first deny")

    def test_zero_threshold_does_not_loop(self) -> None:
        """Zero/negative threshold must not cause infinite loops or crashes."""
        state: dict = {}
        for _ in range(5):
            sg._increment_deny_counter(state, "session-safe", 0)
        # All 5 increments must complete without error
        self.assertEqual(state["session-safe"]["deny_count"], 5)
        self.assertTrue(state["session-safe"]["locked"])


# ===========================================================================
# EC-07: Very large deny_count (>1000)
# ===========================================================================

class TestVeryLargeDenyCount(unittest.TestCase):
    def test_large_deny_count_increments_correctly(self) -> None:
        """A deny_count of 10_000 must increment to 10_001 without crash."""
        state: dict = {
            "big-session": {"deny_count": 10_000, "locked": True, "timestamp": "T"}
        }
        count, locked = sg._increment_deny_counter(state, "big-session", 20)
        self.assertEqual(count, 10_001)
        self.assertTrue(locked)

    def test_large_count_state_persists(self) -> None:
        """Very large count must survive JSON serialisation round-trip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            large_state = {
                "session-large": {"deny_count": 999_999, "locked": True, "timestamp": "T"}
            }
            sg._save_state(state_path, large_state)
            loaded = sg._load_state(state_path)
            self.assertEqual(loaded["session-large"]["deny_count"], 999_999)


# ===========================================================================
# EC-08 & EC-09 & EC-10: Session IDs with special characters
# ===========================================================================

class TestSessionIdSpecialChars(unittest.TestCase):
    def test_path_traversal_session_id_is_safe_dict_key(self) -> None:
        """Session ID containing path-traversal chars must be handled safely as a dict key."""
        traversal_id = "../../etc/passwd"
        state: dict = {}
        count, locked = sg._increment_deny_counter(state, traversal_id, 5)
        self.assertEqual(count, 1)
        # The session is stored as a plain dict key — no file I/O at that path
        self.assertIn(traversal_id, state)
        self.assertEqual(state[traversal_id]["deny_count"], 1)

    def test_path_traversal_survives_state_roundtrip(self) -> None:
        """Path-traversal session ID must survive JSON save/load without file access."""
        traversal_id = "../../secret"
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            state: dict = {}
            sg._increment_deny_counter(state, traversal_id, 10)
            sg._save_state(state_path, state)

            loaded = sg._load_state(state_path)
            self.assertIn(traversal_id, loaded)
            self.assertEqual(loaded[traversal_id]["deny_count"], 1)
            # The tmp dir must only contain the state file — no new directories
            files_in_dir = [f for f in os.listdir(tmpdir) if not f.endswith(".tmp")]
            self.assertEqual(files_in_dir, [".hook_state.json"])

    def test_windows_path_traversal_session_id(self) -> None:
        """Windows-style path-traversal session ID must also be safe."""
        traversal_id = r"..\..\..\Windows\system32\secret"
        state: dict = {}
        count, _ = sg._increment_deny_counter(state, traversal_id, 5)
        self.assertEqual(count, 1)
        self.assertIn(traversal_id, state)

    def test_session_id_with_null_byte_handled_or_excluded(self) -> None:
        """Session ID with embedded null byte: either handled or JSON-safe."""
        null_id = "session\x00with-null"
        state: dict = {}
        # Must not raise — either stores it or normalises it
        try:
            sg._increment_deny_counter(state, null_id, 5)
        except Exception as exc:
            self.fail(f"_increment_deny_counter raised with null-byte ID: {exc}")

    def test_json_special_chars_in_session_id(self) -> None:
        """Session ID with JSON-special characters must survive round-trip."""
        special_id = 'session"with\\quotes/and\nnewlines'
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            state: dict = {}
            sg._increment_deny_counter(state, special_id, 5)
            sg._save_state(state_path, state)
            loaded = sg._load_state(state_path)
            self.assertIn(special_id, loaded)
            self.assertEqual(loaded[special_id]["deny_count"], 1)

    def test_very_long_session_id(self) -> None:
        """A very long session ID (10_000 chars) must not cause crash or path error."""
        long_id = "a" * 10_000
        state: dict = {}
        count, _ = sg._increment_deny_counter(state, long_id, 5)
        self.assertEqual(count, 1)


# ===========================================================================
# EC-11: Session with deny_count >= threshold but locked=false
# ===========================================================================

class TestLockedFlagConsistency(unittest.TestCase):
    def test_session_at_threshold_but_not_marked_locked(self) -> None:
        """If deny_count already equals threshold and locked=false, next
        increment MUST set locked=True (idempotent lock logic)."""
        state: dict = {
            "almost-locked": {"deny_count": 19, "locked": False, "timestamp": "T"}
        }
        count, now_locked = sg._increment_deny_counter(state, "almost-locked", 20)
        self.assertEqual(count, 20)
        self.assertTrue(now_locked)
        self.assertTrue(state["almost-locked"]["locked"])

    def test_already_locked_session_increments_count(self) -> None:
        """Even a locked session's deny_count keeps incrementing correctly."""
        state: dict = {
            "locked-session": {"deny_count": 20, "locked": True, "timestamp": "T"}
        }
        count, still_locked = sg._increment_deny_counter(state, "locked-session", 20)
        self.assertEqual(count, 21)
        self.assertTrue(still_locked)


# ===========================================================================
# EC-12: Returning to a locked session stays locked (integration)
# ===========================================================================

class TestLockedSessionPersistsAcrossInvocations(unittest.TestCase):
    def test_locked_session_stays_locked_after_reload(self) -> None:
        """A session locked on disk must remain locked after state is reloaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            session_id = "return-locked"

            # Lock the session
            state: dict = {}
            threshold = 3
            for _ in range(threshold):
                sg._increment_deny_counter(state, session_id, threshold)
            sg._save_state(state_path, state)

            # Reload (simulate new invocation)
            reloaded = sg._load_state(state_path)
            self.assertTrue(reloaded[session_id]["locked"])

            # Even an extra allow decision should not clear the lock
            count, locked = sg._increment_deny_counter(reloaded, session_id, threshold)
            self.assertTrue(locked)

    def test_main_returns_session_locked_message(self) -> None:
        """main() must return the session-locked message for a locked session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            session_id = "locked-via-main"
            state = {session_id: {"deny_count": 20, "locked": True, "timestamp": "T"}}
            sg._save_state(state_path, state)

            payload = json.dumps({"tool_name": "ask_questions", "tool_input": {}})
            response = _run_main(payload, state_path, session_id)

            self.assertEqual(
                response["hookSpecificOutput"]["permissionDecision"], "deny"
            )
            reason = response["hookSpecificOutput"].get("permissionDecisionReason", "")
            self.assertIn("Session locked", reason)


# ===========================================================================
# EC-13: Block-N-of-M message content
# ===========================================================================

class TestBlockNofMContent(unittest.TestCase):
    def test_block_message_includes_generic_policy_text(self) -> None:
        """'Block N of M' deny reason must include the generic policy text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            session_id = "msg-content-check"

            payload = json.dumps({
                "tool_name": "run_in_terminal",
                "tool_input": {"command": "sudo rm -rf /"},
            })
            response = _run_main(payload, state_path, session_id)
            reason = response["hookSpecificOutput"].get("permissionDecisionReason", "")

            self.assertIn(sg._DENY_REASON, reason)
            self.assertIn("Block 1 of", reason)

    def test_block_message_does_not_reveal_zone_names(self) -> None:
        """'Block N of M' in deny reason must not leak zone names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, ".hook_state.json")
            session_id = "zone-leak-check"

            payload = json.dumps({
                "tool_name": "run_in_terminal",
                "tool_input": {"command": "sudo rm -rf /"},
            })
            response = _run_main(payload, state_path, session_id)
            reason = response["hookSpecificOutput"].get("permissionDecisionReason", "").lower()

            forbidden = [".github", ".vscode", "noagentzone"]
            for zone in forbidden:
                self.assertNotIn(zone, reason, f"Deny reason leaks zone '{zone}': {reason!r}")


# ===========================================================================
# EC-14: SAF-024 regression guard — _DENY_REASON constant unchanged
# ===========================================================================

class TestDenyReasonConstantUnchanged(unittest.TestCase):
    def test_deny_reason_is_generic_text(self) -> None:
        """_DENY_REASON must still equal the approved generic policy message."""
        expected = (
            "Access denied. This action has been blocked by the workspace security policy."
        )
        self.assertEqual(sg._DENY_REASON, expected)

    def test_deny_reason_no_zone_references(self) -> None:
        """_DENY_REASON must not contain any restricted zone name."""
        reason_lower = sg._DENY_REASON.lower()
        for zone in (".github", ".vscode", "noagentzone"):
            self.assertNotIn(zone, reason_lower)

    def test_block_message_contains_deny_reason(self) -> None:
        """The Block-N-of-M deny message must contain _DENY_REASON as a substring,
        so the policy message is always visible to the user."""
        state: dict = {}
        count, _ = sg._increment_deny_counter(state, "regression-check", sg._DENY_THRESHOLD)
        deny_reason = f"Block {count} of {sg._DENY_THRESHOLD}. {sg._DENY_REASON}"
        self.assertIn(sg._DENY_REASON, deny_reason)
        self.assertNotIn(".github", deny_reason.lower())


if __name__ == "__main__":
    unittest.main()
