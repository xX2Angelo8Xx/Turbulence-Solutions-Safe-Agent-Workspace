"""Tests for FIX-076: Fix Reset Agent Blocks button visibility and functionality.

Tests cover:
- _reset_hook_state() unit tests (state file manipulation)
- _on_reset_agent_blocks() handler tests (error / success paths)
- SettingsDialog geometry and grid configuration (FIX: 480x280 → 480x480)
- Widget existence checks (regression: button was hidden, not absent)

All GUI tests run headlessly using the customtkinter MagicMock in conftest.py.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# customtkinter is mocked by conftest.py before any launcher module is imported.
from launcher.gui.app import (
    SettingsDialog,
    _atomic_write_hook_state,
    _reset_hook_state,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_APP_PATH = Path(__file__).resolve().parent.parent.parent / "src" / "launcher" / "gui" / "app.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_settings_dialog() -> SettingsDialog:
    """Return a SettingsDialog backed by a MagicMock parent window."""
    parent = MagicMock()
    with patch("launcher.gui.app.read_python_path", return_value=None):
        return SettingsDialog(parent)


# ===========================================================================
# _reset_hook_state unit tests
# ===========================================================================

class TestResetHookState:
    def test_no_file_returns_zero(self, tmp_path: Path) -> None:
        """When the state file does not exist, return (0, …)."""
        missing = tmp_path / ".hook_state.json"
        count, msg = _reset_hook_state(missing)
        assert count == 0
        assert "nothing" in msg.lower() or "no state" in msg.lower()

    def test_clears_session_entries(self, tmp_path: Path) -> None:
        """Session entries with deny_count are removed; return count equals len(sessions)."""
        state_file = tmp_path / ".hook_state.json"
        state = {
            "sess-abc": {"deny_count": 3, "last_ts": 1234},
            "sess-def": {"deny_count": 0},
        }
        state_file.write_text(json.dumps(state), encoding="utf-8")
        count, msg = _reset_hook_state(state_file)
        assert count == 2
        remaining = json.loads(state_file.read_text(encoding="utf-8"))
        assert remaining == {}

    def test_empty_state_returns_zero(self, tmp_path: Path) -> None:
        """An existing but empty JSON object results in 0 sessions reset."""
        state_file = tmp_path / ".hook_state.json"
        state_file.write_text("{}", encoding="utf-8")
        count, _ = _reset_hook_state(state_file)
        assert count == 0

    def test_multiple_sessions_all_cleared(self, tmp_path: Path) -> None:
        """All session entries are removed in one call."""
        state_file = tmp_path / ".hook_state.json"
        state = {f"sess-{i}": {"deny_count": i} for i in range(5)}
        state_file.write_text(json.dumps(state), encoding="utf-8")
        count, _ = _reset_hook_state(state_file)
        assert count == 5
        assert json.loads(state_file.read_text(encoding="utf-8")) == {}

    def test_preserves_non_session_keys(self, tmp_path: Path) -> None:
        """Keys without deny_count (non-session metadata) are retained."""
        state_file = tmp_path / ".hook_state.json"
        state = {
            "sess-abc": {"deny_count": 1},
            "meta": {"version": "1.0"},
        }
        state_file.write_text(json.dumps(state), encoding="utf-8")
        _reset_hook_state(state_file)
        remaining = json.loads(state_file.read_text(encoding="utf-8"))
        assert "meta" in remaining
        assert "sess-abc" not in remaining

    def test_corrupt_file_replaced_with_empty(self, tmp_path: Path) -> None:
        """A corrupt (non-JSON) state file is replaced with an empty JSON object."""
        state_file = tmp_path / ".hook_state.json"
        state_file.write_text("NOT JSON {{{{", encoding="utf-8")
        count, msg = _reset_hook_state(state_file)
        assert count == 0
        assert "corrupt" in msg.lower() or "warning" in msg.lower()
        result = json.loads(state_file.read_text(encoding="utf-8"))
        assert result == {}

    def test_corrupt_non_object_root_replaced(self, tmp_path: Path) -> None:
        """A root JSON value that is not an object is replaced with an empty object."""
        state_file = tmp_path / ".hook_state.json"
        state_file.write_text("[1, 2, 3]", encoding="utf-8")
        count, msg = _reset_hook_state(state_file)
        assert count == 0
        result = json.loads(state_file.read_text(encoding="utf-8"))
        assert result == {}


# ===========================================================================
# _on_reset_agent_blocks handler tests
# ===========================================================================

class TestOnResetAgentBlocks:
    def test_no_workspace_shows_error(self) -> None:
        """Empty workspace entry triggers showerror."""
        dlg = _make_settings_dialog()
        dlg.workspace_entry.get.return_value = "   "
        with patch("tkinter.messagebox.showerror") as mock_err:
            dlg._on_reset_agent_blocks()
        mock_err.assert_called_once()
        args = mock_err.call_args[0]
        assert "workspace" in args[0].lower() or "workspace" in args[1].lower()

    def test_invalid_path_shows_error(self, tmp_path: Path) -> None:
        """A path that does not point to a directory triggers showerror."""
        non_dir = tmp_path / "does_not_exist"
        dlg = _make_settings_dialog()
        dlg.workspace_entry.get.return_value = str(non_dir)
        with patch("tkinter.messagebox.showerror") as mock_err:
            dlg._on_reset_agent_blocks()
        mock_err.assert_called_once()

    def test_success_shows_info(self, tmp_path: Path) -> None:
        """Successful reset shows showinfo confirmation."""
        # Create the expected directory structure
        hook_dir = tmp_path / ".github" / "hooks" / "scripts"
        hook_dir.mkdir(parents=True)
        state_file = hook_dir / ".hook_state.json"
        state = {"sess-1": {"deny_count": 2}}
        state_file.write_text(json.dumps(state), encoding="utf-8")

        dlg = _make_settings_dialog()
        dlg.workspace_entry.get.return_value = str(tmp_path)
        with patch("tkinter.messagebox.showinfo") as mock_info:
            dlg._on_reset_agent_blocks()
        mock_info.assert_called_once()
        # Verify the state file was actually reset
        remaining = json.loads(state_file.read_text(encoding="utf-8"))
        assert remaining == {}

    def test_os_error_shows_error(self, tmp_path: Path) -> None:
        """OSError during reset shows showerror."""
        dlg = _make_settings_dialog()
        dlg.workspace_entry.get.return_value = str(tmp_path)
        with patch("launcher.gui.app._reset_hook_state", side_effect=OSError("disk full")), \
             patch("tkinter.messagebox.showerror") as mock_err:
            dlg._on_reset_agent_blocks()
        mock_err.assert_called_once()
        args = mock_err.call_args[0]
        assert "disk full" in args[1] or "reset failed" in args[0].lower()


# ===========================================================================
# Dialog geometry / grid tests (regression for BUG-119)
# ===========================================================================

class TestDialogGeometry:
    """Verify SettingsDialog is sized large enough to show all sections."""

    def _get_geometry_string(self) -> str:
        """Extract the geometry string from the SettingsDialog __init__ via AST."""
        source = _APP_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "geometry"):
                continue
            if len(node.args) == 1 and isinstance(node.args[0], ast.Constant):
                return str(node.args[0].value)
        return ""

    def test_dialog_height_at_least_400(self) -> None:
        """Dialog height must be >= 400px so the Reset Agent Blocks rows are visible.

        BUG-119 root cause: original height was 280px, hiding rows 4-6.
        """
        geo = self._get_geometry_string()
        assert geo, "No geometry() call found in SettingsDialog"
        # geometry format: WIDTHxHEIGHT
        parts = geo.lower().split("x")
        assert len(parts) == 2, f"Unexpected geometry format: {geo}"
        height = int(parts[1])
        assert height >= 400, (
            f"SettingsDialog height {height}px is too small to show Reset Agent Blocks "
            f"section. Must be >= 400px."
        )

    def test_dialog_width_unchanged(self) -> None:
        """Dialog width should remain 480px (or at least != 0)."""
        geo = self._get_geometry_string()
        width = int(geo.lower().split("x")[0])
        assert width == 480


class TestDialogColumnConfigure:
    """Verify grid columnconfigure(1, weight=1) is present for proper stretching."""

    def test_columnconfigure_in_source(self) -> None:
        """_build_ui must call grid_columnconfigure with column 1 and weight=1."""
        source = _APP_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)

        found = False
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "grid_columnconfigure"):
                continue
            # Args: (col, weight=N) or positional
            args = node.args
            kwargs = {kw.arg: kw.value for kw in node.keywords}
            col_arg = args[0] if args else kwargs.get("index")
            weight_kw = kwargs.get("weight")
            if (
                col_arg is not None
                and isinstance(col_arg, ast.Constant)
                and col_arg.value == 1
                and weight_kw is not None
                and isinstance(weight_kw, ast.Constant)
                and weight_kw.value == 1
            ):
                found = True
                break

        assert found, (
            "SettingsDialog._build_ui does not call "
            "self._dialog.grid_columnconfigure(1, weight=1)"
        )


# ===========================================================================
# Widget existence (regression: ensure button was not removed)
# ===========================================================================

class TestWidgetExistence:
    def test_reset_agent_blocks_button_exists(self) -> None:
        """reset_agent_blocks_button must be an attribute of SettingsDialog."""
        dlg = _make_settings_dialog()
        assert hasattr(dlg, "reset_agent_blocks_button"), (
            "SettingsDialog missing reset_agent_blocks_button attribute"
        )

    def test_workspace_entry_exists(self) -> None:
        """workspace_entry must be an attribute of SettingsDialog."""
        dlg = _make_settings_dialog()
        assert hasattr(dlg, "workspace_entry"), (
            "SettingsDialog missing workspace_entry attribute"
        )

    def test_browse_workspace_button_exists(self) -> None:
        """browse_workspace_button must be an attribute of SettingsDialog."""
        dlg = _make_settings_dialog()
        assert hasattr(dlg, "browse_workspace_button"), (
            "SettingsDialog missing browse_workspace_button attribute"
        )
