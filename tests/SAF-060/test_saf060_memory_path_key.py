"""SAF-060 — Tests for memory tool path key fix in validate_memory().

Root cause: validate_memory() checked tool_input.get("filePath") but never
checked tool_input.get("path"). The VS Code memory tool sends the path under
the "path" key inside tool_input, causing all memory operations to fail closed
with "deny" because no path was found.

Covers:
- Regression: tool_input["path"] key now extracted correctly → allow for /memories/
- Regression: tool_input["path"] for /memories/session/ → allow
- Regression: decide() + tool_input["path"] for memory tool → allow
- Security: tool_input["path"] pointing outside /memories/ is zone-checked → deny
- Security: tool_input["path"] write to /memories/ (not session) → deny
- Security: tool_input["path"] write to /memories/session/ → allow
- Compatibility: existing tool_input["filePath"] format still works → allow
- Compatibility: top-level "path" key fallback still works → allow
- BUG-137 regression: memory view /memories/ works end-to-end
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Make security_gate importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
    / ".github"
    / "hooks"
    / "scripts"
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

WS = "/workspace"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _path_key_payload(path: str, command: str = "") -> dict:
    """Payload using 'path' key inside tool_input (actual VS Code memory tool format)."""
    ti: dict = {"path": path}
    if command:
        ti["command"] = command
    return {"tool_name": "memory", "tool_input": ti}


def _filepath_key_payload(path: str, command: str = "") -> dict:
    """Payload using 'filePath' key inside tool_input (legacy format)."""
    ti: dict = {"filePath": path}
    if command:
        ti["command"] = command
    return {"tool_name": "memory", "tool_input": ti}


def _toplevel_path_payload(path: str) -> dict:
    """Payload using 'path' at top level (no tool_input nesting)."""
    return {"tool_name": "memory", "path": path}


# ===========================================================================
# BUG-137 Regression — "path" key in tool_input now works
# ===========================================================================

class TestPathKeyExtraction:
    """SAF-060 root cause fix: tool_input['path'] is now read correctly."""

    def test_memories_root_path_key_allow(self) -> None:
        """memory view /memories/ using 'path' key → allow (BUG-137 regression)."""
        result = sg.validate_memory(_path_key_payload("/memories/"), WS)
        assert result == "allow", (
            "validate_memory() must accept 'path' key in tool_input; "
            "this was the root cause of BUG-137."
        )

    def test_memories_session_path_key_allow(self) -> None:
        """memory view /memories/session/ using 'path' key → allow."""
        result = sg.validate_memory(_path_key_payload("/memories/session/"), WS)
        assert result == "allow"

    def test_memories_session_file_path_key_allow(self) -> None:
        """memory view /memories/session/notes.md using 'path' key → allow."""
        result = sg.validate_memory(_path_key_payload("/memories/session/notes.md"), WS)
        assert result == "allow"

    def test_memories_user_path_key_allow(self) -> None:
        """memory view /memories/preferences.md using 'path' key → allow."""
        result = sg.validate_memory(_path_key_payload("/memories/preferences.md"), WS)
        assert result == "allow"

    def test_memories_session_write_path_key_allow(self) -> None:
        """memory create /memories/session/ using 'path' key + create command → allow."""
        result = sg.validate_memory(_path_key_payload("/memories/session/test.md", "create"), WS)
        assert result == "allow"


# ===========================================================================
# Security — path key with denied targets
# ===========================================================================

class TestPathKeyDenied:
    """tool_input['path'] pointing outside /memories/ must still be denied."""

    def test_outside_memories_path_key_deny(self) -> None:
        """'path' key pointing to /etc/passwd → deny."""
        result = sg.validate_memory(_path_key_payload("/etc/passwd"), WS)
        assert result == "deny"

    def test_github_path_key_deny(self) -> None:
        """'path' key pointing to .github/ → deny."""
        result = sg.validate_memory(_path_key_payload(f"{WS}/.github/hooks/security_gate.py"), WS)
        assert result == "deny"

    def test_write_to_memories_root_path_key_deny(self) -> None:
        """'path' key write to /memories/ (not session) → deny."""
        result = sg.validate_memory(_path_key_payload("/memories/preferences.md", "save"), WS)
        assert result == "deny"

    def test_no_path_at_all_deny(self) -> None:
        """Empty tool_input with no path → deny (fail closed)."""
        result = sg.validate_memory({"tool_name": "memory", "tool_input": {}}, WS)
        assert result == "deny"


# ===========================================================================
# Compatibility — existing formats still work
# ===========================================================================

class TestBackwardCompatibility:
    """Existing filePath and top-level path formats must still be accepted."""

    def test_filepath_key_still_works(self) -> None:
        """filePath key in tool_input still accepted → allow."""
        result = sg.validate_memory(_filepath_key_payload("/memories/session/notes.md"), WS)
        assert result == "allow"

    def test_toplevel_path_still_works(self) -> None:
        """Top-level 'path' key still accepted → allow."""
        result = sg.validate_memory(_toplevel_path_payload("/memories/session/"), WS)
        assert result == "allow"


# ===========================================================================
# decide() integration — full flow with 'path' key (BUG-137)
# ===========================================================================

class TestDecideIntegration:
    """decide() must route memory tool through validate_memory() and allow /memories/."""

    def test_decide_memory_view_root(self) -> None:
        """decide(): memory tool + 'path'=/memories/ → allow (BUG-137)."""
        result = sg.decide(_path_key_payload("/memories/"), WS)
        assert result == "allow", (
            "decide() must allow 'memory view /memories/' end-to-end after SAF-060 fix."
        )

    def test_decide_memory_view_session(self) -> None:
        """decide(): memory tool + 'path'=/memories/session/ → allow."""
        result = sg.decide(_path_key_payload("/memories/session/"), WS)
        assert result == "allow"

    def test_decide_memory_create_session(self) -> None:
        """decide(): memory tool + 'path'=/memories/session/new.md + create → allow."""
        result = sg.decide(_path_key_payload("/memories/session/new.md", "create"), WS)
        assert result == "allow"

    def test_decide_memory_outside_denied(self) -> None:
        """decide(): memory tool + 'path' outside /memories/ → deny."""
        result = sg.decide(_path_key_payload("/etc/passwd"), WS)
        assert result == "deny"
