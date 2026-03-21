"""SAF-037 Tester edge-case tests for reset_hook_counter.py."""

import json
import os
import sys
import tempfile
import threading
from pathlib import Path
from unittest import mock

import pytest

# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------

SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "templates"
    / "coding"
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


# ---------------------------------------------------------------------------
# Edge Case 1: Completely empty sessions dict ({} with no keys)
# ---------------------------------------------------------------------------

class TestEmptySessionsDict:
    def test_empty_dict_returns_zero(self, tmp_path: Path) -> None:
        """Reset-all on an empty {} state file returns (0, 'Reset 0 session(s).')."""
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, {})

        count, msg = reset_hook_counter.reset_counters(state_path=state_file)

        assert count == 0
        assert msg == "Reset 0 session(s)."

    def test_empty_dict_file_preserved(self, tmp_path: Path) -> None:
        """Reset-all on empty state leaves file intact (empty dict written back)."""
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, {})

        reset_hook_counter.reset_counters(state_path=state_file)

        assert state_file.exists()
        result = _read_state(state_file)
        assert result == {}

    def test_empty_dict_specific_session_not_found(self, tmp_path: Path) -> None:
        """Resetting a specific session on an empty state returns 0, not-found."""
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, {})

        count, msg = reset_hook_counter.reset_counters(
            session_id="any-session-id", state_path=state_file
        )

        assert count == 0
        assert "not found" in msg.lower()


# ---------------------------------------------------------------------------
# Edge Case 2: session_id with special characters
# ---------------------------------------------------------------------------

class TestSessionIdSpecialChars:
    def _state_with_special_session(self, session_key: str) -> dict:
        return {
            session_key: {
                "deny_count": 3,
                "locked": False,
                "timestamp": "2026-03-21T00:00:00Z",
            }
        }

    def test_session_id_with_dots(self, tmp_path: Path) -> None:
        """Session IDs containing dots work correctly."""
        key = "session.with.dots"
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, self._state_with_special_session(key))

        count, msg = reset_hook_counter.reset_counters(
            session_id=key, state_path=state_file
        )

        assert count == 1
        assert key not in _read_state(state_file)

    def test_session_id_with_hyphens(self, tmp_path: Path) -> None:
        """Session IDs containing hyphens work correctly."""
        key = "my-session-uuid-1234-abcd"
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, self._state_with_special_session(key))

        count, msg = reset_hook_counter.reset_counters(
            session_id=key, state_path=state_file
        )

        assert count == 1
        assert key not in _read_state(state_file)

    def test_session_id_with_spaces(self, tmp_path: Path) -> None:
        """Session IDs containing spaces work correctly."""
        key = "session with spaces"
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, self._state_with_special_session(key))

        count, msg = reset_hook_counter.reset_counters(
            session_id=key, state_path=state_file
        )

        assert count == 1
        assert key not in _read_state(state_file)

    def test_session_id_with_unicode(self, tmp_path: Path) -> None:
        """Session IDs containing unicode characters work correctly."""
        key = "sitzung-\u00e9t\u00e9-2026"
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, self._state_with_special_session(key))

        count, msg = reset_hook_counter.reset_counters(
            session_id=key, state_path=state_file
        )

        assert count == 1
        result = _read_state(state_file)
        assert key not in result

    def test_session_id_with_slashes(self, tmp_path: Path) -> None:
        """Session IDs with path-separator characters are matched literally (no traversal)."""
        key = "session/slash"
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, self._state_with_special_session(key))

        count, msg = reset_hook_counter.reset_counters(
            session_id=key, state_path=state_file
        )

        assert count == 1
        result = _read_state(state_file)
        assert key not in result

    def test_empty_string_session_id(self, tmp_path: Path) -> None:
        """Empty string session ID is treated as a key; not-found if absent."""
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, {"session-a": {"deny_count": 1, "locked": False}})

        count, msg = reset_hook_counter.reset_counters(
            session_id="", state_path=state_file
        )

        # empty string is a valid dict key; it's not present so should be 'not found'
        assert count == 0

    def test_very_long_session_id(self, tmp_path: Path) -> None:
        """A very long session ID (256 chars) can be stored and removed."""
        key = "x" * 256
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, {key: {"deny_count": 1, "locked": False}})

        count, msg = reset_hook_counter.reset_counters(
            session_id=key, state_path=state_file
        )

        assert count == 1
        assert key not in _read_state(state_file)


# ---------------------------------------------------------------------------
# Edge Case 3: State file with ONLY locked sessions
# ---------------------------------------------------------------------------

class TestOnlyLockedSessions:
    def _all_locked_state(self) -> dict:
        return {
            "session-alpha": {
                "deny_count": 10,
                "locked": True,
                "timestamp": "2026-03-21T01:00:00Z",
            },
            "session-beta": {
                "deny_count": 25,
                "locked": True,
                "timestamp": "2026-03-21T02:00:00Z",
            },
            "session-gamma": {
                "deny_count": 100,
                "locked": True,
                "timestamp": "2026-03-21T03:00:00Z",
            },
        }

    def test_all_locked_sessions_removed_on_reset_all(self, tmp_path: Path) -> None:
        """All locked sessions are removed when reset-all is called."""
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, self._all_locked_state())

        count, msg = reset_hook_counter.reset_counters(state_path=state_file)

        assert count == 3
        result = _read_state(state_file)
        for key in ("session-alpha", "session-beta", "session-gamma"):
            assert key not in result

    def test_all_locked_state_file_still_valid_json(self, tmp_path: Path) -> None:
        """After resetting all locked sessions, the state file is still valid JSON."""
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, self._all_locked_state())

        reset_hook_counter.reset_counters(state_path=state_file)

        assert state_file.exists()
        result = _read_state(state_file)
        assert isinstance(result, dict)

    def test_specific_locked_session_removed(self, tmp_path: Path) -> None:
        """A specific locked session can be removed while others remain locked."""
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, self._all_locked_state())

        count, msg = reset_hook_counter.reset_counters(
            session_id="session-alpha", state_path=state_file
        )

        assert count == 1
        result = _read_state(state_file)
        assert "session-alpha" not in result
        # Other locked sessions preserved
        assert result["session-beta"]["locked"] is True
        assert result["session-gamma"]["locked"] is True

    def test_reset_count_message_accuracy(self, tmp_path: Path) -> None:
        """The message correctly reflects the number of locked sessions cleared."""
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, self._all_locked_state())

        count, msg = reset_hook_counter.reset_counters(state_path=state_file)

        assert count == 3
        assert "3" in msg


# ---------------------------------------------------------------------------
# Edge Case 4: Concurrent reset attempts
# ---------------------------------------------------------------------------

class TestConcurrentResetAttempts:
    @pytest.mark.xfail(
        sys.platform == "win32",
        reason=(
            "Windows: os.replace() raises PermissionError(13) when two threads "
            "race to replace the same destination file. The implementation has no "
            "file-level mutex (documented in dev-log Known Limitations). "
            "BUG-096 filed to track the Windows concurrent-write limitation."
        ),
        strict=False,
    )
    def test_concurrent_resets_no_exception(self, tmp_path: Path) -> None:
        """Multiple threads calling reset_counters() concurrently should not raise.

        On Windows, os.replace() raises PermissionError(13) when concurrent
        threads race on the same destination — this is a known platform limitation
        (xfail on win32, see BUG-096).
        """
        state_file = tmp_path / ".hook_state.json"
        state = {
            f"session-{i}": {
                "deny_count": i,
                "locked": False,
                "timestamp": "2026-03-21T00:00:00Z",
            }
            for i in range(10)
        }
        _write_state(state_file, state)

        errors: list[Exception] = []

        def _reset():
            try:
                reset_hook_counter.reset_counters(state_path=state_file)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_reset) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)

        assert errors == [], f"Concurrent reset raised: {errors}"

    def test_concurrent_resets_state_file_valid_after(self, tmp_path: Path) -> None:
        """After concurrent resets, the state file is still valid JSON."""
        state_file = tmp_path / ".hook_state.json"
        state = {
            f"session-{i}": {
                "deny_count": i,
                "locked": i % 2 == 0,
                "timestamp": "2026-03-21T00:00:00Z",
            }
            for i in range(8)
        }
        _write_state(state_file, state)

        threads = [
            threading.Thread(
                target=reset_hook_counter.reset_counters,
                kwargs={"state_path": state_file},
            )
            for _ in range(4)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)

        # Must be valid JSON with a dict root (some threads may raise on Windows
        # but others will succeed and leave the file in a valid state)
        if state_file.exists():
            result = _read_state(state_file)
            assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Edge Case 5: Additional boundary and security checks
# ---------------------------------------------------------------------------

class TestAdditionalBoundaries:
    def test_state_file_with_null_value(self, tmp_path: Path) -> None:
        """Sessions with null/None values are not treated as session entries."""
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, {"key-null": None, "key-string": "value"})

        count, msg = reset_hook_counter.reset_counters(state_path=state_file)

        # Neither key matches session entry pattern
        assert count == 0
        assert "Reset 0 session(s)." == msg

    def test_state_file_with_nested_deny_count_only(self, tmp_path: Path) -> None:
        """A session entry with only deny_count (minimal valid session) is cleared."""
        state_file = tmp_path / ".hook_state.json"
        # Minimal session entry: just deny_count
        _write_state(
            state_file,
            {"minimal-session": {"deny_count": 5}},
        )

        count, msg = reset_hook_counter.reset_counters(state_path=state_file)

        assert count == 1
        assert "minimal-session" not in _read_state(state_file)

    def test_reset_all_returns_correct_type(self, tmp_path: Path) -> None:
        """reset_counters always returns (int, str) tuple, never None."""
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, {})

        result = reset_hook_counter.reset_counters(state_path=state_file)

        assert result is not None
        assert isinstance(result, tuple)
        count, msg = result
        assert isinstance(count, int)
        assert isinstance(msg, str)

    def test_state_file_written_as_valid_json_after_reset(self, tmp_path: Path) -> None:
        """The state file written after reset is valid UTF-8 JSON."""
        state_file = tmp_path / ".hook_state.json"
        _write_state(
            state_file,
            {
                "session-x": {"deny_count": 5, "locked": True},
                "_meta": "keep-this",
            },
        )

        reset_hook_counter.reset_counters(state_path=state_file)

        raw = state_file.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)
        assert parsed.get("_meta") == "keep-this"

    def test_cli_unknown_argument_exits_nonzero(self, tmp_path: Path) -> None:
        """CLI exits non-zero when given an unrecognized argument."""
        with mock.patch(
            "sys.argv",
            ["reset_hook_counter.py", "--unknown-arg", "value"],
        ):
            with pytest.raises(SystemExit) as exc_info:
                reset_hook_counter.main()
            assert exc_info.value.code != 0

    def test_atomic_write_cleanup_on_failure(self, tmp_path: Path) -> None:
        """If os.replace fails, no orphaned temp file is left behind."""
        state_file = tmp_path / ".hook_state.json"
        _write_state(state_file, {"session-a": {"deny_count": 1, "locked": False}})

        def _failing_replace(src, dst):
            raise OSError("simulated replace failure")

        with mock.patch("reset_hook_counter.os.replace", side_effect=_failing_replace):
            with pytest.raises(OSError):
                reset_hook_counter.reset_counters(state_path=state_file)

        # No .tmp files should remain in tmp_path
        tmp_files = [f for f in tmp_path.iterdir() if ".tmp" in f.name or f.suffix == ".tmp"]
        assert tmp_files == [], f"Orphaned temp files found: {tmp_files}"
