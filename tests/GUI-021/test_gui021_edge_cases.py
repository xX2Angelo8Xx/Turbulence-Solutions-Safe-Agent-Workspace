"""Tester edge-case tests for GUI-021 — Reset Agent Blocks button.

Covers scenarios the Developer's tests did not exercise:
- Reset idempotency (double-reset same workspace)
- Workspace path containing spaces
- Very large state file (1 000 sessions)
- Empty JSON object as state file (no sessions, still succeeds)
- State file with only non-session entries (0 reset, confirmation shown)
- Locked / permission-denied atomic write (PermissionError caught as OSError)
- State root is a JSON array (corrupt → replaced with empty dict)
- State entry with deny_count but additional extra keys (removed correctly)
- Workspace path with leading/trailing whitespace handled by strip()
- _atomic_write_hook_state cleans up temp file when os.replace raises
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

_CTK_MOCK = sys.modules["customtkinter"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_settings_dialog():
    """Return a fresh SettingsDialog with all widgets mocked."""
    from launcher.gui.app import SettingsDialog
    _CTK_MOCK.reset_mock()
    return SettingsDialog(MagicMock())


# ---------------------------------------------------------------------------
# 1. Idempotency — resetting an already-empty workspace still shows confirmation
# ---------------------------------------------------------------------------

class TestResetIdempotency:
    def test_double_reset_shows_confirmation_both_times(self, tmp_path: Path) -> None:
        """Calling reset twice on the same workspace succeeds both times."""
        import tkinter.messagebox as mb

        scripts_dir = tmp_path / ".github" / "hooks" / "scripts"
        scripts_dir.mkdir(parents=True)
        state_file = scripts_dir / ".hook_state.json"
        state_file.write_text(
            json.dumps({"session-1": {"deny_count": 3, "blocked": False}}),
            encoding="utf-8",
        )

        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)

        # First reset
        with patch.object(mb, "showinfo") as mock_info1, \
             patch.object(mb, "showerror") as mock_err1:
            dialog._on_reset_agent_blocks()
        mock_err1.assert_not_called()
        mock_info1.assert_called_once()

        # Second reset (state file already empty)
        with patch.object(mb, "showinfo") as mock_info2, \
             patch.object(mb, "showerror") as mock_err2:
            dialog._on_reset_agent_blocks()
        mock_err2.assert_not_called()
        mock_info2.assert_called_once()

    def test_state_file_stays_empty_after_second_reset(self, tmp_path: Path) -> None:
        """State file remains empty (no sessions) after a second reset."""
        import tkinter.messagebox as mb

        scripts_dir = tmp_path / ".github" / "hooks" / "scripts"
        scripts_dir.mkdir(parents=True)
        state_file = scripts_dir / ".hook_state.json"
        state_file.write_text(
            json.dumps({"sess": {"deny_count": 1}}), encoding="utf-8"
        )

        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)

        with patch.object(mb, "showinfo"), patch.object(mb, "showerror"):
            dialog._on_reset_agent_blocks()  # first
            dialog._on_reset_agent_blocks()  # second

        remaining = json.loads(state_file.read_text(encoding="utf-8"))
        assert remaining == {}


# ---------------------------------------------------------------------------
# 2. Workspace path with spaces
# ---------------------------------------------------------------------------

class TestWorkspacePathWithSpaces:
    def test_path_with_spaces_resets_successfully(self, tmp_path: Path) -> None:
        """Workspace directories containing spaces are handled correctly."""
        import tkinter.messagebox as mb

        spaced = tmp_path / "my work space folder"
        scripts_dir = spaced / ".github" / "hooks" / "scripts"
        scripts_dir.mkdir(parents=True)
        state_file = scripts_dir / ".hook_state.json"
        state_file.write_text(
            json.dumps({"s": {"deny_count": 2, "blocked": True}}),
            encoding="utf-8",
        )

        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(spaced)

        with patch.object(mb, "showinfo") as mock_info, \
             patch.object(mb, "showerror") as mock_err:
            dialog._on_reset_agent_blocks()

        mock_err.assert_not_called()
        mock_info.assert_called_once()
        remaining = json.loads(state_file.read_text(encoding="utf-8"))
        assert remaining == {}


# ---------------------------------------------------------------------------
# 3. Very large state file (1 000 sessions)
# ---------------------------------------------------------------------------

class TestLargeStateFile:
    def test_resets_one_thousand_sessions(self, tmp_path: Path) -> None:
        """_reset_hook_state removes all 1 000 session entries."""
        from launcher.gui.app import _reset_hook_state

        state: dict = {
            f"session-{i}": {"deny_count": i % 30, "blocked": i > 20}
            for i in range(1000)
        }
        state_file = tmp_path / ".hook_state.json"
        state_file.write_text(json.dumps(state), encoding="utf-8")

        count, _msg = _reset_hook_state(state_file)

        assert count == 1000
        remaining = json.loads(state_file.read_text(encoding="utf-8"))
        assert remaining == {}

    def test_large_file_preserves_non_session_keys(self, tmp_path: Path) -> None:
        """Non-session keys survive when clearing 1 000 session entries."""
        from launcher.gui.app import _reset_hook_state

        state: dict = {f"session-{i}": {"deny_count": i} for i in range(1000)}
        state["_schema_version"] = {"version": 2}
        state["_config"] = {"threshold": 20}
        state_file = tmp_path / ".hook_state.json"
        state_file.write_text(json.dumps(state), encoding="utf-8")

        count, _msg = _reset_hook_state(state_file)

        assert count == 1000
        remaining = json.loads(state_file.read_text(encoding="utf-8"))
        assert "_schema_version" in remaining
        assert "_config" in remaining
        assert not any(k.startswith("session-") for k in remaining)


# ---------------------------------------------------------------------------
# 4. Empty JSON object — valid state, nothing to reset
# ---------------------------------------------------------------------------

class TestEmptyStateFile:
    def test_empty_state_returns_zero_count(self, tmp_path: Path) -> None:
        """State file with {} contains no sessions → count 0."""
        from launcher.gui.app import _reset_hook_state

        state_file = tmp_path / ".hook_state.json"
        state_file.write_text("{}", encoding="utf-8")

        count, _msg = _reset_hook_state(state_file)
        assert count == 0

    def test_empty_state_still_shows_confirmation(self, tmp_path: Path) -> None:
        """Even with 0 sessions reset, the confirmation dialog is shown."""
        import tkinter.messagebox as mb

        scripts_dir = tmp_path / ".github" / "hooks" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / ".hook_state.json").write_text("{}", encoding="utf-8")

        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)

        with patch.object(mb, "showinfo") as mock_info, \
             patch.object(mb, "showerror") as mock_err:
            dialog._on_reset_agent_blocks()

        mock_err.assert_not_called()
        mock_info.assert_called_once()
        msg = mock_info.call_args[0][1]
        assert "reset" in msg.lower()


# ---------------------------------------------------------------------------
# 5. State with only non-session keys
# ---------------------------------------------------------------------------

class TestOnlyNonSessionKeys:
    def test_non_session_only_returns_zero(self, tmp_path: Path) -> None:
        """State with only non-session keys returns count=0 and preserves them."""
        from launcher.gui.app import _reset_hook_state

        state = {
            "metadata": {"version": 1},
            "config": {"threshold": 20},
            "string_value": "hello",
        }
        state_file = tmp_path / ".hook_state.json"
        state_file.write_text(json.dumps(state), encoding="utf-8")

        count, _msg = _reset_hook_state(state_file)

        assert count == 0
        remaining = json.loads(state_file.read_text(encoding="utf-8"))
        assert remaining["metadata"] == {"version": 1}
        assert remaining["config"] == {"threshold": 20}


# ---------------------------------------------------------------------------
# 6. Locked file / PermissionError propagated as OSError
# ---------------------------------------------------------------------------

class TestLockedFile:
    def test_permission_error_shown_as_reset_failed(self, tmp_path: Path) -> None:
        """PermissionError during atomic write is caught and shown as error."""
        import tkinter.messagebox as mb
        from launcher.gui import app as app_module

        scripts_dir = tmp_path / ".github" / "hooks" / "scripts"
        scripts_dir.mkdir(parents=True)
        state_file = scripts_dir / ".hook_state.json"
        state_file.write_text(
            json.dumps({"s": {"deny_count": 1}}), encoding="utf-8"
        )

        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = str(tmp_path)

        with patch.object(
            app_module,
            "_reset_hook_state",
            side_effect=PermissionError("Access is denied"),
        ):
            with patch.object(mb, "showerror") as mock_err, \
                 patch.object(mb, "showinfo") as mock_info:
                dialog._on_reset_agent_blocks()

        mock_info.assert_not_called()
        mock_err.assert_called_once()
        title, msg = mock_err.call_args[0][0], mock_err.call_args[0][1]
        assert "Reset Failed" in title
        assert "Access is denied" in msg or "denied" in msg.lower()

    def test_atomic_write_cleans_up_temp_on_os_replace_failure(
        self, tmp_path: Path
    ) -> None:
        """If os.replace raises, the temp file is deleted and the error re‑raised."""
        from launcher.gui.app import _atomic_write_hook_state

        dest = tmp_path / "state.json"
        with patch("os.replace", side_effect=OSError("replace failed")):
            with pytest.raises(OSError, match="replace failed"):
                _atomic_write_hook_state(dest, {"key": "val"})

        # No leftover temp files should remain
        tmp_files = list(tmp_path.glob(".hook_state_*.tmp"))
        assert tmp_files == [], f"Temp files not cleaned up: {tmp_files}"


# ---------------------------------------------------------------------------
# 7. State root is a JSON array (corrupt → replaced with empty dict)
# ---------------------------------------------------------------------------

class TestCorruptStateVariants:
    def test_json_array_root_treated_as_corrupt(self, tmp_path: Path) -> None:
        """A JSON array at root level is considered corrupt and replaced with {}."""
        from launcher.gui.app import _reset_hook_state

        state_file = tmp_path / ".hook_state.json"
        state_file.write_text("[1, 2, 3]", encoding="utf-8")

        count, msg = _reset_hook_state(state_file)
        assert count == 0
        assert "corrupt" in msg.lower() or "Warning" in msg
        restored = json.loads(state_file.read_text(encoding="utf-8"))
        assert restored == {}

    def test_json_null_root_treated_as_corrupt(self, tmp_path: Path) -> None:
        """A JSON null root value is considered corrupt and replaced with {}."""
        from launcher.gui.app import _reset_hook_state

        state_file = tmp_path / ".hook_state.json"
        state_file.write_text("null", encoding="utf-8")

        count, msg = _reset_hook_state(state_file)
        assert count == 0
        restored = json.loads(state_file.read_text(encoding="utf-8"))
        assert restored == {}

    def test_json_string_root_treated_as_corrupt(self, tmp_path: Path) -> None:
        """A JSON string as root is considered corrupt and replaced with {}."""
        from launcher.gui.app import _reset_hook_state

        state_file = tmp_path / ".hook_state.json"
        state_file.write_text('"just a string"', encoding="utf-8")

        count, msg = _reset_hook_state(state_file)
        assert count == 0
        restored = json.loads(state_file.read_text(encoding="utf-8"))
        assert restored == {}


# ---------------------------------------------------------------------------
# 8. Session entry with extra keys beyond deny_count + blocked
# ---------------------------------------------------------------------------

class TestSessionEntryExtraKeys:
    def test_session_with_extra_fields_is_removed(self, tmp_path: Path) -> None:
        """Session entries with extra keys are still identified and removed."""
        from launcher.gui.app import _reset_hook_state

        state = {
            "session-x": {
                "deny_count": 7,
                "blocked": True,
                "extra_field": "ignored",
                "timestamp": "2026-01-01T00:00:00Z",
            },
            "config": {"threshold": 20},
        }
        state_file = tmp_path / ".hook_state.json"
        state_file.write_text(json.dumps(state), encoding="utf-8")

        count, _msg = _reset_hook_state(state_file)

        assert count == 1
        remaining = json.loads(state_file.read_text(encoding="utf-8"))
        assert "session-x" not in remaining
        assert remaining.get("config") == {"threshold": 20}


# ---------------------------------------------------------------------------
# 9. Leading/trailing whitespace in path is stripped
# ---------------------------------------------------------------------------

class TestPathWhitespaceStripping:
    def test_path_with_leading_trailing_whitespace_is_stripped(
        self, tmp_path: Path
    ) -> None:
        """Workspace paths with surrounding whitespace are stripped before use."""
        import tkinter.messagebox as mb

        scripts_dir = tmp_path / ".github" / "hooks" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / ".hook_state.json").write_text(
            json.dumps({"s": {"deny_count": 1}}), encoding="utf-8"
        )

        dialog = _make_settings_dialog()
        # Wrap the real path in whitespace — should be stripped by the handler
        dialog.workspace_entry.get.return_value = f"  {tmp_path}  "

        with patch.object(mb, "showinfo") as mock_info, \
             patch.object(mb, "showerror") as mock_err:
            dialog._on_reset_agent_blocks()

        mock_err.assert_not_called()
        mock_info.assert_called_once()

    def test_path_with_only_whitespace_is_rejected(self) -> None:
        """A path consisting only of whitespace is rejected with an error."""
        import tkinter.messagebox as mb

        dialog = _make_settings_dialog()
        dialog.workspace_entry.get.return_value = "\t  \n"

        with patch.object(mb, "showerror") as mock_err:
            dialog._on_reset_agent_blocks()

        mock_err.assert_called_once()
