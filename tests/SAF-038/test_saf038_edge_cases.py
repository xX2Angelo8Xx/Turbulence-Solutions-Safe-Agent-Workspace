"""SAF-038 — Tester edge-case tests for memory and create_directory.

Supplements the developer test suite (test_saf038_memory_create_directory.py)
with adversarial and boundary scenarios the developer did not cover:

- Null byte injection (\x00) inside path strings
- Mixed/upper case tool names (Memory, CREATE_DIRECTORY) → denied by gate
- Unicode paths (accented characters, CJK, emoji) inside project folder
- Whitespace-only path strings → fail closed (deny)
- Relative path without workspace prefix → deny
- Deeply traversed path that resolves back inside project → allow
- Memory with dirPath key instead of filePath → deny (fail closed)
- create_directory with only filePath key (no dirPath) → deny
- C0 control character injection (tab, newline) in paths
- Z-list (very long) path traversal attack
- Tool input as a nested list → deny
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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WS = "/workspace"
WS_WIN = "c:/workspace"

PROJECT_FILE = f"{WS}/project/memories/session/notes.md"
PROJECT_DIR = f"{WS}/project/memories/session"
GITHUB_FILE = f"{WS}/.github/hooks/scripts/security_gate.py"
GITHUB_DIR = f"{WS}/.github/hooks"
NOAGENT_FILE = f"{WS}/NoAgentZone/secret.txt"


# ---------------------------------------------------------------------------
# Autouse fixture — fake workspace detection
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _patch_detect_project_folder():
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
# Null byte injection
# ===========================================================================

class TestNullByteInjection:
    """Null bytes in paths must be stripped before zone classification.

    zone_classifier.normalize_path strips C0 control chars (\x00–\x1f)
    before any comparison.  A path like /workspace/project/\x00../../.github/x
    must therefore be treated as /workspace/project/../.github/x (after strip)
    and denied — not allowed because the null byte appeared to put the
    traversal segment "inside" the project.
    """

    def test_memory_null_byte_traversal_to_github_deny(self):
        # Null byte between project/ and ../  must be stripped → traversal detected
        path = f"{WS}/project/\x00../../.github/secret"
        data = {"tool_input": {"filePath": path}}
        assert sg.validate_memory(data, WS) == "deny"

    def test_memory_null_byte_in_project_path_deny(self):
        # SAF-048 intentional security improvement (BUG-125 resolution):
        # Null bytes have no legitimate use in any file path. SAF-048 added
        # an early null-byte check in validate_memory() that fires before
        # zone_classifier is reached. Even a project-folder path with a null
        # byte is denied. The old 'allow' was an accidental weakness.
        path = f"{WS}/project/memories\x00/notes.md"
        data = {"tool_input": {"filePath": path}}
        assert sg.validate_memory(data, WS) == "deny"

    def test_create_directory_null_byte_traversal_deny(self):
        path = f"{WS}/project/\x00../../../.github/injected"
        data = {"tool_input": {"dirPath": path}}
        assert sg.validate_create_directory(data, WS) == "deny"

    def test_create_directory_null_byte_in_project_allow(self):
        path = f"{WS}/project/memories\x00/session"
        data = {"tool_input": {"dirPath": path}}
        assert sg.validate_create_directory(data, WS) == "allow"

    def test_decide_memory_null_byte_traversal_deny(self):
        data = {
            "tool_name": "memory",
            "tool_input": {"filePath": f"{WS}/project/\x00../../.github/secret"},
        }
        assert sg.decide(data, WS) == "deny"

    def test_decide_create_directory_null_byte_traversal_deny(self):
        data = {
            "tool_name": "create_directory",
            "tool_input": {"dirPath": f"{WS}/project/\x00../../.github/injected"},
        }
        assert sg.decide(data, WS) == "deny"


# ===========================================================================
# C0 control character injection (tab, newline, carriage return)
# ===========================================================================

class TestControlCharacterInjection:
    """Other C0 control characters (BUG-010 fix) must be stripped.

    A tab or newline immediately before a deny-zone segment could otherwise
    slip past a naive string-contains check.
    """

    def test_memory_tab_before_github_deny(self):
        path = f"{WS}/project/\t../../.github/secret"
        data = {"tool_input": {"filePath": path}}
        assert sg.validate_memory(data, WS) == "deny"

    def test_memory_newline_before_noagentzone_deny(self):
        path = f"{WS}/project/\n../../NoAgentZone/secret"
        data = {"tool_input": {"filePath": path}}
        assert sg.validate_memory(data, WS) == "deny"

    def test_create_directory_cr_before_vscode_deny(self):
        path = f"{WS}/project/\r../../.vscode/injected"
        data = {"tool_input": {"dirPath": path}}
        assert sg.validate_create_directory(data, WS) == "deny"


# ===========================================================================
# Mixed / upper case tool names
# ===========================================================================

class TestMixedCaseToolNames:
    """Tool names are matched case-sensitively.

    "Memory" and "CREATE_DIRECTORY" are not in _EXEMPT_TOOLS (which has
    "memory" and "create_directory") so they fall through to the unknown-tool
    denial branch → deny even with project-folder paths.
    """

    def test_Memory_uppercase_deny(self):
        # Tool sent as "Memory" — unknown to the gate, denied (fail safe)
        data = {
            "tool_name": "Memory",
            "tool_input": {"filePath": PROJECT_FILE},
        }
        assert sg.decide(data, WS) == "deny"

    def test_MEMORY_allcaps_deny(self):
        data = {
            "tool_name": "MEMORY",
            "tool_input": {"filePath": PROJECT_FILE},
        }
        assert sg.decide(data, WS) == "deny"

    def test_CREATE_DIRECTORY_allcaps_deny(self):
        data = {
            "tool_name": "CREATE_DIRECTORY",
            "tool_input": {"dirPath": PROJECT_DIR},
        }
        assert sg.decide(data, WS) == "deny"

    def test_Create_Directory_mixed_deny(self):
        data = {
            "tool_name": "Create_Directory",
            "tool_input": {"dirPath": PROJECT_DIR},
        }
        assert sg.decide(data, WS) == "deny"

    def test_Memory_with_github_path_deny(self):
        # Also deny with a restricted path — combined case
        data = {
            "tool_name": "Memory",
            "tool_input": {"filePath": GITHUB_FILE},
        }
        assert sg.decide(data, WS) == "deny"


# ===========================================================================
# Unicode paths
# ===========================================================================

class TestUnicodePaths:
    """Unicode characters in paths that resolve inside the project folder."""

    def test_memory_accented_name_inside_project_allow(self):
        path = f"{WS}/project/memories/café/notes.md"
        data = {"tool_input": {"filePath": path}}
        assert sg.validate_memory(data, WS) == "allow"

    def test_memory_cjk_inside_project_allow(self):
        path = f"{WS}/project/memories/文档/notes.md"
        data = {"tool_input": {"filePath": path}}
        assert sg.validate_memory(data, WS) == "allow"

    def test_memory_unicode_outside_project_deny(self):
        # Even with unicode name, path outside project is denied
        path = f"{WS}/données/outside.md"
        data = {"tool_input": {"filePath": path}}
        assert sg.validate_memory(data, WS) == "deny"

    def test_create_directory_unicode_inside_project_allow(self):
        path = f"{WS}/project/données/session"
        data = {"tool_input": {"dirPath": path}}
        assert sg.validate_create_directory(data, WS) == "allow"

    def test_create_directory_unicode_outside_project_deny(self):
        path = f"{WS}/données/session"
        data = {"tool_input": {"dirPath": path}}
        assert sg.validate_create_directory(data, WS) == "deny"


# ===========================================================================
# Whitespace-only paths
# ===========================================================================

class TestWhitespaceOnlyPaths:
    """Whitespace-only strings are truthy in Python but must be denied.

    A space (" ") passes the `if not raw_path` guard but resolves via
    posixpath.normpath to "." which does not match any project folder.
    """

    def test_memory_space_only_path_deny(self):
        data = {"tool_input": {"filePath": " "}}
        assert sg.validate_memory(data, WS) == "deny"

    def test_memory_tab_only_path_deny(self):
        data = {"tool_input": {"filePath": "\t"}}
        assert sg.validate_memory(data, WS) == "deny"

    def test_create_directory_space_only_deny(self):
        data = {"tool_input": {"dirPath": " "}}
        assert sg.validate_create_directory(data, WS) == "deny"

    def test_create_directory_newline_only_deny(self):
        data = {"tool_input": {"dirPath": "\n"}}
        assert sg.validate_create_directory(data, WS) == "deny"


# ===========================================================================
# Wrong field usage
# ===========================================================================

class TestWrongFieldUsage:
    """Using the wrong path key for each tool must fail closed."""

    def test_memory_with_dirPath_key_deny(self):
        # memory uses filePath, not dirPath — no valid path found → deny
        data = {"tool_input": {"dirPath": PROJECT_FILE}}
        assert sg.validate_memory(data, WS) == "deny"

    def test_memory_with_only_path_key_top_level_allow(self):
        # "path" is a valid fallback for validate_memory (top-level key)
        data = {"path": PROJECT_FILE}
        assert sg.validate_memory(data, WS) == "allow"

    def test_create_directory_with_only_filePath_top_level_deny(self):
        # create_directory uses dirPath only; filePath at top level is ignored
        data = {"filePath": PROJECT_DIR}
        assert sg.validate_create_directory(data, WS) == "deny"

    def test_create_directory_nested_filePath_wrong_key_deny(self):
        # filePath inside tool_input for create_directory → wrong key → deny
        data = {"tool_input": {"filePath": PROJECT_DIR}}
        assert sg.validate_create_directory(data, WS) == "deny"


# ===========================================================================
# Deep traversal that stays inside the project folder
# ===========================================================================

class TestTraversalInsideProject:
    """Traversal that resolves inside the project folder must be allowed."""

    def test_memory_traversal_stays_in_project_allow(self):
        # /workspace/project/subdir/../../project/notes.md → project/notes.md → allow
        path = f"{WS}/project/subdir/../../project/notes.md"
        data = {"tool_input": {"filePath": path}}
        assert sg.validate_memory(data, WS) == "allow"

    def test_create_directory_traversal_stays_in_project_allow(self):
        path = f"{WS}/project/a/b/../../c"
        data = {"tool_input": {"dirPath": path}}
        assert sg.validate_create_directory(data, WS) == "allow"


# ===========================================================================
# Relative paths (no workspace prefix)
# ===========================================================================

class TestRelativePaths:
    """Relative paths are resolved against the workspace root by zone_classifier.

    zone_classifier.classify() resolves bare relative paths against ws_root
    before any zone check (intentional by-design behaviour).  Therefore:
    - A relative path that maps inside the project folder → allow
    - A relative path that maps to a deny zone → deny
    - A relative path that escapes the workspace via '..' → deny
    """

    def test_memory_relative_project_path_allow(self):
        # 'project/memories/notes.md' resolves to ws_root/project/… → allow
        data = {"tool_input": {"filePath": "project/memories/notes.md"}}
        assert sg.validate_memory(data, WS) == "allow"

    def test_memory_relative_deny_zone_deny(self):
        # '.github/secret' resolves to ws_root/.github/secret → deny
        data = {"tool_input": {"filePath": ".github/secret"}}
        assert sg.validate_memory(data, WS) == "deny"

    def test_memory_relative_escape_workspace_deny(self):
        # '../../etc/passwd' escapes workspace → deny
        data = {"tool_input": {"filePath": "../../etc/passwd"}}
        assert sg.validate_memory(data, WS) == "deny"

    def test_create_directory_relative_project_allow(self):
        # 'project/memories/session' resolves inside project folder → allow
        data = {"tool_input": {"dirPath": "project/memories/session"}}
        assert sg.validate_create_directory(data, WS) == "allow"

    def test_create_directory_relative_deny_zone_deny(self):
        # '.vscode/themes' resolves to ws_root/.vscode/themes → deny
        data = {"tool_input": {"dirPath": ".vscode/themes"}}
        assert sg.validate_create_directory(data, WS) == "deny"

    def test_create_directory_relative_escape_deny(self):
        # '../etc' escapes workspace → deny
        data = {"tool_input": {"dirPath": "../etc"}}
        assert sg.validate_create_directory(data, WS) == "deny"


# ===========================================================================
# tool_input as nested list (malformed)
# ===========================================================================

class TestNestedListInput:
    """If tool_input is a list instead of a dict, fail closed."""

    def test_memory_tool_input_as_list_deny(self):
        data = {"tool_name": "memory", "tool_input": [{"filePath": PROJECT_FILE}]}
        assert sg.decide(data, WS) == "deny"

    def test_create_directory_tool_input_as_list_deny(self):
        data = {"tool_name": "create_directory", "tool_input": [{"dirPath": PROJECT_DIR}]}
        assert sg.decide(data, WS) == "deny"
