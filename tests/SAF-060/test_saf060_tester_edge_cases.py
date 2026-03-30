"""SAF-060 Tester edge-case tests — added by Tester Agent.

Covers boundary conditions and security vectors beyond the Developer's test suite:

1. Path traversal via "path" key: /memories/../.github/ → deny
2. Deep traversal: /memories/session/../../.github/ → deny
3. Empty string path → deny (fail closed)
4. None as path value → deny
5. Integer as path value → deny
6. Conflicting filePath+path — filePath wins when valid safe value
7. Conflicting filePath+path — filePath wins when dangerous value (no bypass via "path")
8. Empty filePath + malicious "path" key → falls through to "path" key → deny
9. System-level path /etc/passwd → deny
10. Windows system path C:\\Windows\\system.ini → deny
11. "data" key not used as fallback path extraction
12. tool_input with only "data" key (no path key) → deny (fail closed)
13. Path traversal that resolves back to /memories/ still allowed (not false positive)
14. Slash-only path "/" → deny
15. Mixed-case traversal /MEMORIES/../.GITHUB/ → deny (after normpath + lower)
"""
from __future__ import annotations

import sys
from pathlib import Path

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

def _path_payload(path, command: str = "") -> dict:
    """Build a memory tool payload with 'path' key in tool_input."""
    ti: dict = {"path": path}
    if command:
        ti["command"] = command
    return {"tool_name": "memory", "tool_input": ti}


def _filepath_payload(fp, path_val=None, command: str = "") -> dict:
    """Build a payload with filePath (and optionally also 'path') in tool_input."""
    ti: dict = {"filePath": fp}
    if path_val is not None:
        ti["path"] = path_val
    if command:
        ti["command"] = command
    return {"tool_name": "memory", "tool_input": ti}


# ===========================================================================
# Path traversal — "path" key
# ===========================================================================

class TestPathTraversal:
    """Path traversal attempts via the new 'path' key must be denied."""

    def test_traversal_memories_to_github(self) -> None:
        """memory create /memories/../.github/hooks/security_gate.py → deny."""
        result = sg.validate_memory(
            _path_payload("/memories/../.github/hooks/security_gate.py", "create"), WS
        )
        assert result == "deny", (
            "Path traversal escaping /memories/ via .. must be denied after normpath."
        )

    def test_deep_traversal_session_to_github(self) -> None:
        """memory create /memories/session/../../.github/ → deny."""
        result = sg.validate_memory(
            _path_payload("/memories/session/../../.github/", "create"), WS
        )
        assert result == "deny"

    def test_traversal_to_system_etc(self) -> None:
        """/memories/../etc/passwd traversal → deny."""
        result = sg.validate_memory(_path_payload("/memories/../etc/passwd"), WS)
        assert result == "deny"

    def test_mixed_case_traversal_to_github(self) -> None:
        """/MEMORIES/../.GITHUB/ (mixed case) traversal → deny."""
        result = sg.validate_memory(
            _path_payload("/MEMORIES/../.GITHUB/hooks/script.py", "create"), WS
        )
        assert result == "deny"

    def test_traversal_resolves_back_to_memories_allowed(self) -> None:
        """/memories/session/../preferences.md resolves to /memories/preferences.md → allow (read)."""
        result = sg.validate_memory(_path_payload("/memories/session/../preferences.md"), WS)
        assert result == "allow", (
            "Traversal within /memories/ that resolves to /memories/ is still a valid read."
        )

    def test_traversal_resolves_back_to_non_session_write_denied(self) -> None:
        """/memories/session/../preferences.md write → deny (resolves outside session)."""
        result = sg.validate_memory(
            _path_payload("/memories/session/../preferences.md", "save"), WS
        )
        assert result == "deny", (
            "Write that traverses to /memories/... (not /memories/session/) must be denied."
        )


# ===========================================================================
# Boundary — invalid and empty path values
# ===========================================================================

class TestInvalidPathValues:
    """None, empty string, non-string path values must fail closed."""

    def test_empty_string_path_deny(self) -> None:
        """Empty string path → deny (fail closed)."""
        result = sg.validate_memory(_path_payload(""), WS)
        assert result == "deny"

    def test_none_path_value_deny(self) -> None:
        """None as path value → deny (fail closed)."""
        result = sg.validate_memory(_path_payload(None), WS)
        assert result == "deny"

    def test_integer_path_value_deny(self) -> None:
        """Integer 42 as path value → deny (fail closed)."""
        result = sg.validate_memory(_path_payload(42), WS)
        assert result == "deny"

    def test_list_path_value_deny(self) -> None:
        """List as path value → deny (fail closed)."""
        result = sg.validate_memory(_path_payload(["/memories/"]), WS)
        assert result == "deny"

    def test_slash_only_path_deny(self) -> None:
        """Path '/' → deny (not under /memories/)."""
        result = sg.validate_memory(_path_payload("/"), WS)
        assert result == "deny"

    def test_whitespace_only_path_deny(self) -> None:
        """Whitespace-only path '   ' → deny (treated as non-path)."""
        # posixpath.normpath("   ") = "   " which doesn't start with /memories/
        # zone_classifier won't match it to an allowed zone either
        result = sg.validate_memory(_path_payload("   "), WS)
        assert result == "deny"


# ===========================================================================
# Conflicting filePath + path keys — priority validation
# ===========================================================================

class TestConflictingPathKeys:
    """When both filePath and path are in tool_input, filePath takes priority."""

    def test_safe_filepath_wins_over_malicious_path_key(self) -> None:
        """filePath=/memories/ (safe) + path=/etc/passwd (malicious) → allow (filePath wins)."""
        result = sg.validate_memory(
            _filepath_payload("/memories/notes.md", path_val="/etc/passwd"), WS
        )
        assert result == "allow", (
            "filePath key must have priority over 'path' key."
        )

    def test_dangerous_filepath_wins_over_safe_path_key(self) -> None:
        """filePath=/etc/passwd (dangerous) + path=/memories/ (safe) → deny (filePath wins)."""
        result = sg.validate_memory(
            _filepath_payload("/etc/passwd", path_val="/memories/"), WS
        )
        assert result == "deny", (
            "A malicious 'path' key must NOT override a denied filePath."
        )

    def test_dangerous_filepath_wins_write_bypass_attempt(self) -> None:
        """filePath=/workspace/.github/config (dangerous) + path=/memories/session/ → deny."""
        result = sg.validate_memory(
            _filepath_payload(f"{WS}/.github/config", path_val="/memories/session/", command="create"),
            WS,
        )
        assert result == "deny"

    def test_empty_filepath_falls_through_to_path_key(self) -> None:
        """Empty filePath + safe path key → path key is used → allow."""
        result = sg.validate_memory(
            _filepath_payload("", path_val="/memories/session/notes.md"), WS
        )
        assert result == "allow", (
            "Empty filePath should fall through to 'path' key fallback."
        )

    def test_none_filepath_falls_through_to_malicious_path_key(self) -> None:
        """None filePath + malicious path=/etc/passwd → deny (path key used as fallback)."""
        result = sg.validate_memory(
            _filepath_payload(None, path_val="/etc/passwd"), WS
        )
        assert result == "deny"


# ===========================================================================
# System-level paths
# ===========================================================================

class TestSystemPaths:
    """Out-of-scope system paths must be denied."""

    def test_etc_passwd_path_key_deny(self) -> None:
        """/etc/passwd via 'path' key → deny."""
        result = sg.validate_memory(_path_payload("/etc/passwd"), WS)
        assert result == "deny"

    def test_etc_shadow_path_key_deny(self) -> None:
        """/etc/shadow via 'path' key → deny."""
        result = sg.validate_memory(_path_payload("/etc/shadow"), WS)
        assert result == "deny"

    def test_windows_system_path_deny(self) -> None:
        """C:\\Windows\\system.ini via 'path' key → deny."""
        result = sg.validate_memory(_path_payload("C:\\Windows\\system.ini"), WS)
        assert result == "deny"

    def test_windows_system32_path_deny(self) -> None:
        """C:\\Windows\\System32 via 'path' key → deny."""
        result = sg.validate_memory(_path_payload("C:\\Windows\\System32"), WS)
        assert result == "deny"


# ===========================================================================
# "data" field not used as path extraction fallback
# ===========================================================================

class TestDataFieldNotFallback:
    """The 'data' key must NOT be used for path extraction — fails closed."""

    def test_data_key_with_memories_path_deny(self) -> None:
        """tool_input with only 'data': /memories/ (not path/filePath) → deny."""
        payload = {"tool_name": "memory", "tool_input": {"data": "/memories/"}}
        result = sg.validate_memory(payload, WS)
        assert result == "deny", (
            "'data' key must not be used for path extraction — fail closed."
        )

    def test_toplevel_data_key_deny(self) -> None:
        """Top-level 'data' key with /memories/ → deny."""
        payload = {"tool_name": "memory", "data": "/memories/"}
        result = sg.validate_memory(payload, WS)
        assert result == "deny", (
            "Top-level 'data' key must not be used for path extraction."
        )

    def test_data_key_cannot_bypass_to_allowed_zone(self) -> None:
        """Even a valid memory path in the 'data' field doesn't grant access."""
        payload = {
            "tool_name": "memory",
            "tool_input": {"data": "/memories/session/notes.md", "command": "create"},
        }
        result = sg.validate_memory(payload, WS)
        assert result == "deny"
