"""SAF-048 — Iteration 3 tester edge-case tests for validate_memory().

New edge cases added during Iteration 3 review:
- False-positive prefix boundary: /memoriesX/ must not be treated as virtual
- Write to the /memories/session directory itself (no file) → deny
- Non-string command field handling (integer, list, None)
- BUG-125 verification: null byte in project-folder path now denied
- Case normalization: /MEMORIES (no slash) exact match
- Very long valid session path → allow (no artificial length restriction)
- Command substring matching precision (read-only vs save)

Written by: Tester Agent (Iteration 3)
Date: 2026-03-25
"""
from __future__ import annotations

import sys
from pathlib import Path

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
# False-positive prefix boundary
# ===========================================================================

class TestFalsePrefixBoundary:
    """Paths that look like /memories/ but are not must not be allowed."""

    def test_memories_with_extra_char_read(self) -> None:
        """/memoriesX/session/notes.md must not be treated as virtual → deny."""
        result = sg.validate_memory(_payload("/memoriesX/session/notes.md"), WS)
        assert result == "deny", (
            "/memoriesX/ must not be treated as a virtual memory path; "
            "only paths starting with /memories/ (with slash) qualify."
        )

    def test_memories_hyphen_read(self) -> None:
        """/memories-backup/notes.md → deny (not virtual memory)."""
        result = sg.validate_memory(_payload("/memories-backup/notes.md"), WS)
        assert result == "deny"

    def test_memories_dot_prefix_read(self) -> None:
        """/memories.evil/notes.md → deny (not virtual memory)."""
        result = sg.validate_memory(_payload("/memories.evil/notes.md"), WS)
        assert result == "deny"


# ===========================================================================
# Write to directory path (/memories/session without file)
# ===========================================================================

class TestWriteToDirectoryPath:
    """Writing to the session DIRECTORY itself (no filename) must be denied."""

    def test_write_to_session_dir_exact_no_slash(self) -> None:
        """/memories/session write (bare directory, no trailing slash) → deny.

        posixpath.normpath('/memories/session/') == '/memories/session';
        startswith('/memories/session/') is False for the normalized form.
        Writes to a bare directory path are not legitimate.
        """
        result = sg.validate_memory(
            {"tool_input": {"filePath": "/memories/session/", "command": "save"}},
            WS,
        )
        assert result == "deny", (
            "Writing to /memories/session/ (directory) must be denied; "
            "normpath strips the trailing slash so startswith('/memories/session/') "
            "is False."
        )

    def test_read_session_dir_exact_still_allowed(self) -> None:
        """READ /memories/session/ (directory path) → allow (reads always allowed)."""
        result = sg.validate_memory(
            {"tool_input": {"filePath": "/memories/session/"}},
            WS,
        )
        assert result == "allow", (
            "Reading the session directory itself must be allowed for reads."
        )


# ===========================================================================
# Non-string command field
# ===========================================================================

class TestNonStringCommandField:
    """validate_memory must tolerate non-string command values without crashing."""

    def test_command_is_none_treated_as_read(self) -> None:
        """command=None → treated as read → deny for user memory write path is irrelevant.

        None or '' → '' → no write ops → read → allowed for session.
        """
        result = sg.validate_memory(
            {"tool_input": {"filePath": "/memories/session/notes.md", "command": None}},
            WS,
        )
        assert result == "allow", "None command defaults to read; session path read allowed."

    def test_command_is_integer_treated_as_read(self) -> None:
        """command=42 (int) → str(42)='42' → no write ops → read → allow for session."""
        result = sg.validate_memory(
            {"tool_input": {"filePath": "/memories/session/notes.md", "command": 42}},
            WS,
        )
        assert result == "allow", "Integer command treated as read; session read allowed."

    def test_command_is_list_save_treated_as_write_user_memory_denied(self) -> None:
        """command=['save'] → str(['save'])="['save']" contains 'save' → write → user memory denied."""
        result = sg.validate_memory(
            {"tool_input": {"filePath": "/memories/preferences.md", "command": ["save"]}},
            WS,
        )
        assert result == "deny", (
            "List command containing 'save' substring is treated as write; "
            "user memory writes are denied."
        )

    def test_command_is_false_treated_as_read(self) -> None:
        """command=False → str(False or '')='' → read → allow for session."""
        result = sg.validate_memory(
            {"tool_input": {"filePath": "/memories/session/notes.md", "command": False}},
            WS,
        )
        assert result == "allow", "False command treated as read; session read allowed."


# ===========================================================================
# BUG-125 verification — null bytes in any path now denied
# ===========================================================================

class TestBug125PolicyVerification:
    """Null bytes in filesystem paths are now denied by SAF-048 (intentional).

    Before SAF-048, null bytes in non-virtual filesystem paths went to
    zone_classifier.normalize_path() which stripped them. SAF-048 adds an
    early null-byte rejection that applies to ALL paths, including project-folder
    paths. This is intentional: null bytes are never legitimate in paths.
    """

    def test_null_byte_in_project_folder_path_denied(self) -> None:
        """Filesystem path with null byte inside project folder → deny (BUG-125 policy)."""
        path = f"{WS}/project/memories\x00/notes.md"
        result = sg.validate_memory({"tool_input": {"filePath": path}}, WS)
        assert result == "deny", (
            "SAF-048: null bytes in any path are denied early before zone_classifier. "
            "The old allow behavior was an accidental weakness in zone_classifier."
        )

    def test_null_byte_in_session_virtual_path_denied(self) -> None:
        """/memories/session/\x00notes.md → deny (null byte check fires before virtual check)."""
        result = sg.validate_memory(
            {"tool_input": {"filePath": "/memories/session/\x00notes.md"}},
            WS,
        )
        assert result == "deny"


# ===========================================================================
# Case normalization: /MEMORIES (no slash, exact match)
# ===========================================================================

class TestCaseNormalizationExactMatch:
    """Case normalization also applies to the bare /MEMORIES exact match."""

    def test_upper_memories_exact_read(self) -> None:
        """/MEMORIES (bare, no slash) → allow after .lower() → '/memories' match."""
        result = sg.validate_memory(_payload("/MEMORIES"), WS)
        assert result == "allow", (
            "/MEMORIES after normpath+lower becomes /memories, "
            "which matches the exact == check."
        )

    def test_upper_memories_exact_write_denied(self) -> None:
        """/MEMORIES write → deny (not session path)."""
        result = sg.validate_memory(_payload("/MEMORIES", "save"), WS)
        assert result == "deny"


# ===========================================================================
# Long path in session memory
# ===========================================================================

class TestLongSessionPath:
    """Very long session memory paths must be allowed — no artificial length cap."""

    def test_very_long_valid_session_path_read(self) -> None:
        """A 1000-char session path → allow (no path length restriction)."""
        long_part = "a" * 900
        path = f"/memories/session/{long_part}/notes.md"
        result = sg.validate_memory(_payload(path), WS)
        assert result == "allow", "No artificial path length cap on virtual memory paths."

    def test_very_long_valid_session_path_write(self) -> None:
        """A 1000-char session path write → allow."""
        long_part = "b" * 900
        path = f"/memories/session/{long_part}/notes.md"
        result = sg.validate_memory(_payload(path, "save"), WS)
        assert result == "allow"


# ===========================================================================
# Command substring precision
# ===========================================================================

class TestCommandSubstringPrecision:
    """Verify that command matching precision is correct for read-adjacent words."""

    def test_command_readonly_is_read(self) -> None:
        """command='readonly' → no write ops → read → user memory allowed."""
        result = sg.validate_memory(_payload("/memories/preferences.md", "readonly"), WS)
        assert result == "allow", "'readonly' contains no write-op substrings."

    def test_command_view_is_read(self) -> None:
        """command='view' → no write ops → allow for /memories/ read."""
        result = sg.validate_memory(_payload("/memories/repo/arch.md", "view"), WS)
        assert result == "allow"

    def test_command_overwrite_is_write_user_denied(self) -> None:
        """command='overwrite' contains 'write' → is_write=True → user memory denied."""
        result = sg.validate_memory(_payload("/memories/preferences.md", "overwrite"), WS)
        assert result == "deny", "'overwrite' contains 'write' so treated as write op."

    def test_command_recreate_is_write_user_denied(self) -> None:
        """command='recreate' contains 'create' → is_write=True → user memory denied."""
        result = sg.validate_memory(_payload("/memories/preferences.md", "recreate"), WS)
        assert result == "deny", "'recreate' contains 'create' so treated as write op."

    def test_command_recreation_is_read_user_memory_allowed(self) -> None:
        """command='recreation' does NOT contain 'create' → read → user memory allowed.

        'recreation' = r-e-c-r-e-a-t-i-o-n; the substring 'create' (c-r-e-a-t-e)
        is not present — 'creati' ends with 'i' not 'e'.
        """
        result = sg.validate_memory(_payload("/memories/preferences.md", "recreation"), WS)
        assert result == "allow", "'recreation' has no write-op substring; treated as read."
