"""Tests for SAF-037: reset_hook_counter.py — reset denial counter state."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# ---------------------------------------------------------------------------
# Import the module under test
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

import reset_hook_counter  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_state(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def _read_state(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sample_state() -> dict:
    """Return a realistic state dict with two sessions + metadata."""
    return {
        "_fallback_session_id": "fb-uuid-1234",
        "_fallback_created": "2026-03-21T00:00:00Z",
        "session-aaa": {
            "deny_count": 5,
            "locked": False,
            "timestamp": "2026-03-21T01:00:00Z",
        },
        "session-bbb": {
            "deny_count": 20,
            "locked": True,
            "timestamp": "2026-03-21T02:00:00Z",
        },
    }


# ---------------------------------------------------------------------------
# 1. Reset all sessions: empties the sessions dict
# ---------------------------------------------------------------------------

class TestResetAllSessions:
    def test_reset_all_removes_sessions(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, _sample_state())

        count, msg = reset_hook_counter.reset_counters(state_path=state_file)

        assert count == 2
        assert "Reset 2 session(s)." == msg

        result = _read_state(state_file)
        # No session entries should remain
        for v in result.values():
            assert not isinstance(v, dict) or "deny_count" not in v

    def test_reset_all_preserves_metadata(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, _sample_state())

        reset_hook_counter.reset_counters(state_path=state_file)

        result = _read_state(state_file)
        assert result.get("_fallback_session_id") == "fb-uuid-1234"
        assert result.get("_fallback_created") == "2026-03-21T00:00:00Z"

    def test_reset_all_empty_state(self, tmp_path: Path) -> None:
        """Resetting an empty state file with no sessions."""
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, {"_fallback_session_id": "x"})

        count, msg = reset_hook_counter.reset_counters(state_path=state_file)

        assert count == 0
        assert "Reset 0 session(s)." == msg


# ---------------------------------------------------------------------------
# 2. Reset specific session: removes only that session
# ---------------------------------------------------------------------------

class TestResetSpecificSession:
    def test_removes_only_target(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, _sample_state())

        count, msg = reset_hook_counter.reset_counters(
            session_id="session-aaa", state_path=state_file
        )

        assert count == 1
        assert msg == "Session session-aaa reset."

        result = _read_state(state_file)
        assert "session-aaa" not in result
        # session-bbb still present
        assert "session-bbb" in result
        assert result["session-bbb"]["deny_count"] == 20


# ---------------------------------------------------------------------------
# 3. Reset specific session not found: appropriate message
# ---------------------------------------------------------------------------

class TestResetSessionNotFound:
    def test_not_found_message(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, _sample_state())

        count, msg = reset_hook_counter.reset_counters(
            session_id="nonexistent", state_path=state_file
        )

        assert count == 0
        assert msg == "Session nonexistent not found."

    def test_metadata_key_not_treated_as_session(self, tmp_path: Path) -> None:
        """_fallback_session_id is not a session entry and should not be resetable."""
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, _sample_state())

        count, msg = reset_hook_counter.reset_counters(
            session_id="_fallback_session_id", state_path=state_file
        )

        assert count == 0
        assert "not found" in msg


# ---------------------------------------------------------------------------
# 4. Missing state file: graceful message, exit 0
# ---------------------------------------------------------------------------

class TestMissingStateFile:
    def test_missing_file_message(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"
        # file does not exist

        count, msg = reset_hook_counter.reset_counters(state_path=state_file)

        assert count == 0
        assert msg == "No state file found. Nothing to reset."

    def test_missing_file_no_file_created(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"

        reset_hook_counter.reset_counters(state_path=state_file)

        assert not state_file.exists()


# ---------------------------------------------------------------------------
# 5. Corrupt state file: warning, creates fresh state
# ---------------------------------------------------------------------------

class TestCorruptStateFile:
    def test_corrupt_json(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"
        state_file.write_text("{invalid json!!", encoding="utf-8")

        count, msg = reset_hook_counter.reset_counters(state_path=state_file)

        assert count == 0
        assert "corrupt" in msg.lower()

        # file should now contain a fresh empty state
        result = _read_state(state_file)
        assert result == {}

    def test_non_dict_json(self, tmp_path: Path) -> None:
        """A JSON file that is valid JSON but not a dict."""
        state_file = tmp_path / ".hook_state.json"
        state_file.write_text("[1, 2, 3]", encoding="utf-8")

        count, msg = reset_hook_counter.reset_counters(state_path=state_file)

        assert count == 0
        assert "corrupt" in msg.lower()
        result = _read_state(state_file)
        assert result == {}


# ---------------------------------------------------------------------------
# 6. Programmatic API: reset_counters() returns correct tuple
# ---------------------------------------------------------------------------

class TestProgrammaticAPI:
    def test_return_type(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, _sample_state())

        result = reset_hook_counter.reset_counters(state_path=state_file)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], int)
        assert isinstance(result[1], str)

    def test_importable_function(self) -> None:
        """reset_counters is importable and callable."""
        assert callable(reset_hook_counter.reset_counters)


# ---------------------------------------------------------------------------
# 7. CLI invocation: correct stdout messages
# ---------------------------------------------------------------------------

class TestCLI:
    def test_cli_reset_all(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, _sample_state())

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "reset_hook_counter.py")],
            capture_output=True,
            text=True,
            env={**os.environ, "HOOK_STATE_PATH": "unused"},
        )

        # We can't easily override STATE_FILE from CLI, so test via
        # the main() function with mocking instead.

    def test_cli_main_reset_all(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, _sample_state())

        with mock.patch.object(
            reset_hook_counter, "STATE_FILE", state_file
        ), mock.patch("sys.argv", ["reset_hook_counter.py"]):
            with pytest.raises(SystemExit) as exc_info:
                reset_hook_counter.main()
            assert exc_info.value.code == 0

    def test_cli_main_reset_specific(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, _sample_state())

        with mock.patch.object(
            reset_hook_counter, "STATE_FILE", state_file
        ), mock.patch(
            "sys.argv",
            ["reset_hook_counter.py", "--session-id", "session-aaa"],
        ):
            with pytest.raises(SystemExit) as exc_info:
                reset_hook_counter.main()
            assert exc_info.value.code == 0

        result = _read_state(state_file)
        assert "session-aaa" not in result
        assert "session-bbb" in result

    def test_cli_main_missing_file(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"

        with mock.patch.object(
            reset_hook_counter, "STATE_FILE", state_file
        ), mock.patch("sys.argv", ["reset_hook_counter.py"]):
            with pytest.raises(SystemExit) as exc_info:
                reset_hook_counter.main()
            assert exc_info.value.code == 0

    def test_cli_stdout_message(self, tmp_path: Path, capsys) -> None:
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, _sample_state())

        with mock.patch.object(
            reset_hook_counter, "STATE_FILE", state_file
        ), mock.patch("sys.argv", ["reset_hook_counter.py"]):
            with pytest.raises(SystemExit):
                reset_hook_counter.main()

        captured = capsys.readouterr()
        assert "Reset 2 session(s)." in captured.out


# ---------------------------------------------------------------------------
# 8. Atomic write: temp file + rename pattern used
# ---------------------------------------------------------------------------

class TestAtomicWrite:
    def test_atomic_write_uses_temp_and_replace(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, _sample_state())

        calls: list[str] = []

        original_mkstemp = tempfile.mkstemp
        original_replace = os.replace

        def mock_mkstemp(**kwargs):
            result = original_mkstemp(**kwargs)
            calls.append("mkstemp")
            return result

        def mock_replace(src, dst):
            calls.append("replace")
            return original_replace(src, dst)

        with mock.patch("reset_hook_counter.tempfile.mkstemp", side_effect=mock_mkstemp), \
             mock.patch("reset_hook_counter.os.replace", side_effect=mock_replace):
            reset_hook_counter.reset_counters(state_path=state_file)

        assert "mkstemp" in calls
        assert "replace" in calls

    def test_no_leftover_temp_files(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, _sample_state())

        reset_hook_counter.reset_counters(state_path=state_file)

        # Only the state file should exist; no .tmp leftovers
        files = list(tmp_path.iterdir())
        assert len(files) == 1
        assert files[0].name == ".hook_state.json"


# ---------------------------------------------------------------------------
# 9. After reset, previously locked sessions are unlocked (removed)
# ---------------------------------------------------------------------------

class TestLockedSessionsCleared:
    def test_locked_session_removed_by_reset_all(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, _sample_state())

        # session-bbb is locked
        pre_state = _read_state(state_file)
        assert pre_state["session-bbb"]["locked"] is True

        reset_hook_counter.reset_counters(state_path=state_file)

        post_state = _read_state(state_file)
        assert "session-bbb" not in post_state

    def test_locked_session_removed_by_specific_reset(self, tmp_path: Path) -> None:
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, _sample_state())

        count, msg = reset_hook_counter.reset_counters(
            session_id="session-bbb", state_path=state_file
        )

        assert count == 1
        assert "session-bbb" in msg

        post_state = _read_state(state_file)
        assert "session-bbb" not in post_state
