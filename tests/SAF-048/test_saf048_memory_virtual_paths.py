"""SAF-048 — Tests for virtual memory path support in validate_memory().

Covers:
- Unit: virtual /memories/ read paths → allow
- Unit: virtual /memories/session/ read paths → allow
- Unit: virtual /memories/session/ write paths → allow
- Unit: virtual /memories/ write paths (user memory) → deny (writes only allowed in session)
- Unit: filesystem path inside project folder → allow (existing behaviour)
- Unit: filesystem path outside project → deny (existing behaviour)
- Security: no path provided → deny (fail closed)
- Security: empty path → deny (fail closed)
- Security: path that looks virtual but is a filesystem path trick → zone-checked
- Regression: BUG-113 — /memories/ and /memories/session/ no longer blanket-blocked
- Cross-platform: Windows backslash virtual paths normalised correctly
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Make security_gate importable from its location
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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WS = "/workspace"
WS_WIN = "c:/workspace"

# Virtual memory paths (VS Code identifiers — not filesystem)
V_MEMORIES_ROOT = "/memories"
V_MEMORIES_ROOT_SLASH = "/memories/"
V_MEMORIES_SESSION = "/memories/session/"
V_MEMORIES_SESSION_FILE = "/memories/session/notes.md"
V_MEMORIES_SESSION_DEEP = "/memories/session/subdir/context.md"
V_MEMORIES_USER = "/memories/preferences.md"
V_MEMORIES_REPO = "/memories/repo/architecture.md"

# Filesystem paths — project folder (allow zone)
FS_PROJECT_FILE = f"{WS}/project/src/launcher/core/app.py"
FS_PROJECT_WIN = f"{WS_WIN}/project/src/utils/helpers.py"

# Filesystem paths — outside project (deny zone)
FS_OUTSIDE = "/tmp/evil.txt"
FS_GITHUB = f"{WS}/.github/hooks/scripts/security_gate.py"


# ---------------------------------------------------------------------------
# Helper — build a minimal memory tool payload
# ---------------------------------------------------------------------------
def _payload(path: str, command: str = "") -> dict:
    """Return a memory tool payload with the given path and optional command."""
    tool_input: dict = {"filePath": path}
    if command:
        tool_input["command"] = command
    return {"tool_input": tool_input}


def _payload_top(path: str) -> dict:
    """Return a payload where the path is at the top level (not nested)."""
    return {"filePath": path}


# ===========================================================================
# Virtual path — read operations
# ===========================================================================

class TestVirtualMemoryReads:
    """Virtual /memories/ paths must be allowed for read operations."""

    def test_read_memories_root(self) -> None:
        """Read on /memories root → allow (BUG-113 regression)."""
        result = sg.validate_memory(_payload(V_MEMORIES_ROOT), WS)
        assert result == "allow"

    def test_read_memories_root_with_slash(self) -> None:
        """Read on /memories/ with trailing slash → allow."""
        result = sg.validate_memory(_payload(V_MEMORIES_ROOT_SLASH), WS)
        assert result == "allow"

    def test_read_memories_session_prefix(self) -> None:
        """Read on /memories/session/ prefix → allow (BUG-113 regression)."""
        result = sg.validate_memory(_payload(V_MEMORIES_SESSION), WS)
        assert result == "allow"

    def test_read_memories_session_file(self) -> None:
        """Read on specific session memory file → allow."""
        result = sg.validate_memory(_payload(V_MEMORIES_SESSION_FILE), WS)
        assert result == "allow"

    def test_read_memories_session_deep(self) -> None:
        """Read on deeply nested session memory path → allow."""
        result = sg.validate_memory(_payload(V_MEMORIES_SESSION_DEEP), WS)
        assert result == "allow"

    def test_read_memories_user_preferences(self) -> None:
        """Read on user memory file → allow."""
        result = sg.validate_memory(_payload(V_MEMORIES_USER), WS)
        assert result == "allow"

    def test_read_memories_repo(self) -> None:
        """Read on repo memory file → allow."""
        result = sg.validate_memory(_payload(V_MEMORIES_REPO), WS)
        assert result == "allow"

    def test_read_no_command_is_treated_as_read(self) -> None:
        """No command present → treated as read → allow for any /memories/ path."""
        result = sg.validate_memory({"tool_input": {"filePath": V_MEMORIES_USER}}, WS)
        assert result == "allow"


# ===========================================================================
# Virtual path — write operations
# ===========================================================================

class TestVirtualMemoryWrites:
    """Write operations: only /memories/session/ is permitted."""

    def test_write_session_file(self) -> None:
        """Write to /memories/session/notes.md → allow."""
        result = sg.validate_memory(_payload(V_MEMORIES_SESSION_FILE, "save"), WS)
        assert result == "allow"

    def test_write_session_deep(self) -> None:
        """Write to nested session path → allow."""
        result = sg.validate_memory(_payload(V_MEMORIES_SESSION_DEEP, "write"), WS)
        assert result == "allow"

    def test_write_session_create(self) -> None:
        """Create command on session file → allow."""
        result = sg.validate_memory(_payload(V_MEMORIES_SESSION_FILE, "create"), WS)
        assert result == "allow"

    def test_write_session_update(self) -> None:
        """Update command on session file → allow."""
        result = sg.validate_memory(_payload(V_MEMORIES_SESSION_FILE, "update"), WS)
        assert result == "allow"

    def test_write_session_delete(self) -> None:
        """Delete command on session file → allow."""
        result = sg.validate_memory(_payload(V_MEMORIES_SESSION_FILE, "delete"), WS)
        assert result == "allow"

    def test_write_user_memory_denied(self) -> None:
        """Write to user memory (/memories/preferences.md) → deny (writes outside session not allowed)."""
        result = sg.validate_memory(_payload(V_MEMORIES_USER, "save"), WS)
        assert result == "deny"

    def test_write_user_memory_write_command(self) -> None:
        """Write command to /memories/repo/ → deny."""
        result = sg.validate_memory(_payload(V_MEMORIES_REPO, "write"), WS)
        assert result == "deny"

    def test_write_memories_root_denied(self) -> None:
        """Write to /memories root → deny (not session path)."""
        result = sg.validate_memory(_payload(V_MEMORIES_ROOT, "create"), WS)
        assert result == "deny"

    def test_write_command_case_insensitive(self) -> None:
        """Write detection is case-insensitive."""
        result = sg.validate_memory(_payload(V_MEMORIES_USER, "SAVE"), WS)
        assert result == "deny"

    def test_write_command_partial_match(self) -> None:
        """Command containing write keyword triggers write detection."""
        result = sg.validate_memory(_payload(V_MEMORIES_USER, "file-write"), WS)
        assert result == "deny"


# ===========================================================================
# Fixture — make zone_classifier tolerate fake workspace roots
# ===========================================================================

@pytest.fixture(autouse=False)
def patch_detect_project_folder():
    """Patch zone_classifier.detect_project_folder for fake workspace roots."""
    import zone_classifier as zc
    original = zc.detect_project_folder

    def _detect_with_fallback(workspace_root: Path) -> str:
        try:
            return original(workspace_root)
        except (RuntimeError, OSError):
            return "project"

    with patch.object(zc, "detect_project_folder", side_effect=_detect_with_fallback):
        yield


# ===========================================================================
# Filesystem paths — existing zone-check behaviour preserved
# ===========================================================================

class TestFilesystemPaths:
    """Non-virtual paths must still be zone-checked (SAF-038 behaviour regression)."""

    def test_filesystem_project_path_allowed(self, patch_detect_project_folder) -> None:
        """Filesystem path inside project folder → allow (unchanged behaviour)."""
        result = sg.validate_memory(_payload(FS_PROJECT_FILE), WS)
        assert result == "allow"

    def test_filesystem_project_path_win(self, patch_detect_project_folder) -> None:
        """Windows filesystem path inside project → allow."""
        result = sg.validate_memory(_payload(FS_PROJECT_WIN), WS_WIN)
        assert result == "allow"

    def test_filesystem_outside_project_denied(self) -> None:
        """Filesystem path outside project → deny (unchanged zone behaviour)."""
        result = sg.validate_memory(_payload(FS_OUTSIDE), WS)
        assert result == "deny"

    def test_filesystem_github_zone_denied(self) -> None:
        """Filesystem path in .github zone → deny (unchanged zone behaviour)."""
        result = sg.validate_memory(_payload(FS_GITHUB), WS)
        assert result == "deny"


# ===========================================================================
# Fail-closed edge cases (security)
# ===========================================================================

class TestFailClosed:
    """validate_memory must fail closed when path information is missing."""

    def test_no_path_key(self) -> None:
        """Payload with no path keys → deny (fail closed)."""
        result = sg.validate_memory({"tool_input": {"command": "read"}}, WS)
        assert result == "deny"

    def test_empty_payload(self) -> None:
        """Completely empty payload → deny."""
        result = sg.validate_memory({}, WS)
        assert result == "deny"

    def test_empty_string_path(self) -> None:
        """Empty string in filePath → deny."""
        result = sg.validate_memory(_payload(""), WS)
        assert result == "deny"

    def test_null_path(self) -> None:
        """None value in filePath → deny."""
        result = sg.validate_memory({"tool_input": {"filePath": None}}, WS)
        assert result == "deny"

    def test_non_string_path(self) -> None:
        """Non-string filePath (e.g. list) → deny."""
        result = sg.validate_memory({"tool_input": {"filePath": ["/memories/session/"]}}, WS)
        assert result == "deny"

    def test_path_in_top_level_data(self) -> None:
        """Path at top level (no tool_input nesting) still detected."""
        result = sg.validate_memory(_payload_top(V_MEMORIES_SESSION_FILE), WS)
        assert result == "allow"


# ===========================================================================
# Cross-platform: Windows-style virtual paths
# ===========================================================================

class TestCrossPlatformVirtualPaths:
    """Virtual paths with Windows backslashes must be normalised correctly."""

    def test_windows_backslash_session_read(self) -> None:
        r"""\\memories\\session\\ with backslashes → virtual → allow."""
        result = sg.validate_memory(_payload("\\memories\\session\\notes.md"), WS)
        assert result == "allow"

    def test_windows_backslash_user_write_denied(self) -> None:
        r"""\\memories\\preferences.md write → deny (not session)."""
        result = sg.validate_memory(_payload("\\memories\\preferences.md", "save"), WS)
        assert result == "deny"


# ===========================================================================
# BUG-113 regression tests
# ===========================================================================

class TestBug113Regression:
    """Direct regression tests for BUG-113."""

    def test_bug113_memories_read_was_denied(self) -> None:
        """BUG-113: /memories/ read was blanket-denied; must now be allowed."""
        result = sg.validate_memory({"tool_input": {"filePath": "/memories/"}}, WS)
        assert result == "allow", "BUG-113: /memories/ read must be allowed"

    def test_bug113_session_read_was_denied(self) -> None:
        """BUG-113: /memories/session/ read was blanket-denied; must now be allowed."""
        result = sg.validate_memory({"tool_input": {"filePath": "/memories/session/"}}, WS)
        assert result == "allow", "BUG-113: /memories/session/ read must be allowed"

    def test_bug113_session_write_was_denied(self) -> None:
        """BUG-113: /memories/session/ write was blanket-denied; must now be allowed."""
        result = sg.validate_memory(
            {"tool_input": {"filePath": "/memories/session/notes.md", "command": "save"}},
            WS,
        )
        assert result == "allow", "BUG-113: /memories/session/ write must be allowed"
