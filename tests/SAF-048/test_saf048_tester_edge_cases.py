"""SAF-048 — Tester edge-case tests for validate_memory().

Focuses on attack vectors the Developer's suite does not cover:
- Path traversal attacks via ``..`` in virtual memory paths
- Null bytes embedded in memory paths
- Case variation (e.g. /MEMORIES/session/)
- Unicode homoglyph tricks
- session/.. write bypass (resolves outside /memories/session/)
- Deep traversal write bypass through session prefix

Written by: Tester Agent
Date: 2026-03-25
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


def _payload(path: str, command: str = "") -> dict:
    """Return a minimal memory tool payload."""
    ti: dict = {"filePath": path}
    if command:
        ti["command"] = command
    return {"tool_input": ti}


# ===========================================================================
# Path traversal attacks — read
# ===========================================================================

class TestPathTraversalRead:
    """Paths that start with /memories/ but escape via .. must be denied on read."""

    def test_traversal_to_security_gate_read(self) -> None:
        """READ /memories/../../.github/hooks/scripts/security_gate.py → deny."""
        result = sg.validate_memory(
            _payload("/memories/../../.github/hooks/scripts/security_gate.py"),
            WS,
        )
        assert result == "deny", (
            "Path traversal via .. in virtual memory path must be denied; "
            "current impl returns 'allow' because startswith('/memories/') "
            "passes without dot-dot resolution."
        )

    def test_traversal_to_etc_passwd_read(self) -> None:
        """READ /memories/../../../etc/passwd → deny."""
        result = sg.validate_memory(_payload("/memories/../../../etc/passwd"), WS)
        assert result == "deny", (
            "Traversal to /etc/passwd via /memories/../../../ must be denied."
        )

    def test_traversal_to_env_file_read(self) -> None:
        """READ /memories/../../.env → deny."""
        result = sg.validate_memory(_payload("/memories/../../.env"), WS)
        assert result == "deny", "Traversal to .env via /memories/../../ must be denied."

    def test_traversal_deep_in_session_read(self) -> None:
        """READ /memories/session/../../../../etc/passwd → deny."""
        result = sg.validate_memory(
            _payload("/memories/session/../../../../etc/passwd"),
            WS,
        )
        assert result == "deny", (
            "Deep traversal starting with session prefix must still be denied."
        )


# ===========================================================================
# Path traversal attacks — write
# ===========================================================================

class TestPathTraversalWrite:
    """session/../ prefix bypasses the /memories/session/ write restriction."""

    def test_session_dotdot_write_denied(self) -> None:
        """/memories/session/../preferences.md save → deny (resolves to user memory)."""
        result = sg.validate_memory(
            _payload("/memories/session/../preferences.md", "save"),
            WS,
        )
        assert result == "deny", (
            "/memories/session/../preferences.md must be denied for writes — "
            "it lexically matches startswith('/memories/session/') but "
            "dot-dot resolution takes it outside session."
        )

    def test_session_dotdot_write_to_repo_memory(self) -> None:
        """/memories/session/../repo/creds.md write → deny (outside session)."""
        result = sg.validate_memory(
            _payload("/memories/session/../repo/creds.md", "write"),
            WS,
        )
        assert result == "deny"

    def test_session_deep_traversal_to_github_write(self) -> None:
        """/memories/session/../../.github/secrets write → deny."""
        result = sg.validate_memory(
            _payload("/memories/session/../../.github/secrets", "write"),
            WS,
        )
        assert result == "deny", (
            "Deep traversal through session prefix must not allow writing "
            "to .github or any path outside /memories/session/."
        )

    def test_session_traversal_create_command(self) -> None:
        """/memories/session/../preferences.md create → deny."""
        result = sg.validate_memory(
            _payload("/memories/session/../preferences.md", "create"),
            WS,
        )
        assert result == "deny"

    def test_session_traversal_update_command(self) -> None:
        """/memories/session/../preferences.md update → deny."""
        result = sg.validate_memory(
            _payload("/memories/session/../preferences.md", "update"),
            WS,
        )
        assert result == "deny"

    def test_session_traversal_delete_command(self) -> None:
        """/memories/session/../preferences.md delete → deny."""
        result = sg.validate_memory(
            _payload("/memories/session/../preferences.md", "delete"),
            WS,
        )
        assert result == "deny"


# ===========================================================================
# Null bytes in memory paths
# ===========================================================================

class TestNullBytesInPaths:
    """Null bytes embedded in paths must cause a deny."""

    def test_null_byte_in_session_path(self) -> None:
        """/memories/session/\x00passwd → deny."""
        result = sg.validate_memory(
            _payload("/memories/session/\x00passwd"),
            WS,
        )
        assert result == "deny", (
            "Null bytes in memory paths must be rejected. "
            "Current impl allows /memories/session/ paths with embedded nulls."
        )

    def test_null_byte_in_user_memory_path(self) -> None:
        """/memories/\x00evil → deny."""
        result = sg.validate_memory(_payload("/memories/\x00evil"), WS)
        assert result == "deny"

    def test_null_byte_write_to_session(self) -> None:
        """/memories/session/\x00 write → deny."""
        result = sg.validate_memory(
            _payload("/memories/session/\x00", "save"),
            WS,
        )
        assert result == "deny"


# ===========================================================================
# Case variations
# ===========================================================================

class TestCaseVariations:
    """Mixed-case /MEMORIES/ paths should be treated identically to lowercase."""

    def test_upper_memories_session_read(self) -> None:
        """/MEMORIES/session/notes.md read → allow (case-insensitive normalization)."""
        result = sg.validate_memory(_payload("/MEMORIES/session/notes.md"), WS)
        assert result == "allow", (
            "/MEMORIES/session/ must be recognized as a virtual memory path "
            "after case normalization and allowed for reads."
        )

    def test_mixed_case_memories_session_read(self) -> None:
        """/Memories/Session/notes.md read → allow."""
        result = sg.validate_memory(_payload("/Memories/Session/notes.md"), WS)
        assert result == "allow"

    def test_upper_memories_session_write(self) -> None:
        """/MEMORIES/session/notes.md write → allow."""
        result = sg.validate_memory(_payload("/MEMORIES/session/notes.md", "save"), WS)
        assert result == "allow", (
            "/MEMORIES/session/ write must be allowed after case normalization."
        )

    def test_upper_memories_user_write_denied(self) -> None:
        """/MEMORIES/preferences.md write → deny (non-session write, user memory)."""
        result = sg.validate_memory(_payload("/MEMORIES/preferences.md", "save"), WS)
        assert result == "deny"


# ===========================================================================
# Unicode tricks
# ===========================================================================

class TestUnicodeTricks:
    """Unicode homoglyphs and other Unicode tricks must not bypass the check."""

    def test_unicode_lookalike_m(self) -> None:
        """ɱemories path (Unicode 'm' substitute) → deny (not a valid memory path)."""
        # U+0271 LATIN SMALL LETTER M WITH HOOK — not regular 'm'
        result = sg.validate_memory(
            _payload("/\u0271emories/session/notes.md"),
            WS,
        )
        # Must deny — not a real virtual path, zone classifier will deny
        assert result == "deny"

    def test_rtl_override_in_path(self) -> None:
        """Right-to-left override character in path → deny."""
        result = sg.validate_memory(
            _payload("/memories/session/\u202enotes.md"),
            WS,
        )
        # This starts with /memories/session/ so will currently allow —
        # but the RLO character should be rejected as suspicious.
        # The gate should deny paths with control/format characters.
        assert result == "deny", (
            "Right-to-left override (U+202E) in a memory path must be denied; "
            "such characters are used to disguise filenames."
        )

    def test_zero_width_no_break_space_in_path(self) -> None:
        """Zero-width no-break space in path → deny."""
        result = sg.validate_memory(
            _payload("/memories/session/\ufeffnotes.md"),
            WS,
        )
        assert result == "deny", (
            "BOM/ZWNBSP character (U+FEFF) in a memory path must be denied."
        )


# ===========================================================================
# Empty path after normalization (additional fail-closed checks)
# ===========================================================================

class TestEmptyAfterNormalization:
    """Edge cases around paths that become empty or degenerate after processing."""

    def test_whitespace_only_path(self) -> None:
        """Path containing only whitespace → deny."""
        result = sg.validate_memory(_payload("   "), WS)
        assert result == "deny"

    def test_path_with_only_slashes(self) -> None:
        """Path '////' → deny (not a valid memory path or filesystem path)."""
        result = sg.validate_memory(_payload("////"), WS)
        assert result == "deny"

    def test_path_is_dot(self) -> None:
        """Path '.' → deny (degenerate relative path)."""
        result = sg.validate_memory(_payload("."), WS)
        assert result == "deny"

    def test_path_is_dotdot(self) -> None:
        """Path '..' → deny (traversal)."""
        result = sg.validate_memory(_payload(".."), WS)
        assert result == "deny"
