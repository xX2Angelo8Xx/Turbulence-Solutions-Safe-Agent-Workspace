"""SAF-038 — Tests for memory and create_directory Tool Zone Enforcement.

Covers:
- Unit: validate_memory() direct calls — allowed in project, denied outside
- Unit: validate_create_directory() direct calls — allowed in project, denied outside
- Security: decide() dispatches both tools correctly (before _EXEMPT_TOOLS fallback)
- Bypass: adversarial payloads (no path, wrong type, traversal, deny zones)
- Cross-platform: Windows/POSIX/WSL path variants
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Make security_gate (and zone_classifier) importable
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

# Paths — project folder (allow zone)
PROJECT_FILE_1 = f"{WS}/project/memories/session/notes.md"
PROJECT_FILE_2 = f"{WS}/project/memories/repo/arch.md"
PROJECT_DIR_1 = f"{WS}/project/memories/session"
PROJECT_DIR_2 = f"{WS}/project/src/utils"
PROJECT_WIN = f"{WS_WIN}/project/memories/session/notes.md"
PROJECT_DIR_WIN = f"{WS_WIN}/project/memories/session"

# Paths — restricted zones (deny)
GITHUB_FILE = f"{WS}/.github/hooks/scripts/security_gate.py"
NOAGENT_FILE = f"{WS}/NoAgentZone/secret.txt"
VSCODE_FILE = f"{WS}/.vscode/settings.json"
GITHUB_DIR = f"{WS}/.github/hooks"
NOAGENT_DIR = f"{WS}/NoAgentZone"

# Paths — outside project (docs, tests, src — deny in 2-tier model)
DOCS_FILE = f"{WS}/docs/architecture.md"
TESTS_DIR = f"{WS}/tests/SAF-038"

# Path — git internals (deny even if inside project zone)
GIT_FILE = f"{WS}/project/.git/config"
GIT_DIR = f"{WS}/project/.git/refs"


# ---------------------------------------------------------------------------
# conftest-style zone_classifier patch for fake workspace
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _patch_detect_project_folder():
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
# Unit — validate_memory()
# ===========================================================================

class TestValidateMemory:
    """Direct unit tests for validate_memory()."""

    # --- Project folder paths → allow

    def test_project_path_top_level_allow(self):
        # filePath at top level (flat / legacy format) → allow
        data = {"filePath": PROJECT_FILE_1}
        assert sg.validate_memory(data, WS) == "allow"

    def test_project_path_nested_tool_input_allow(self):
        # filePath inside tool_input (VS Code hook format) → allow
        data = {"tool_input": {"filePath": PROJECT_FILE_1}}
        assert sg.validate_memory(data, WS) == "allow"

    def test_project_path_nested_wins_over_top_level(self):
        # tool_input.filePath takes precedence over top-level key
        data = {
            "filePath": GITHUB_FILE,       # top-level is restricted
            "tool_input": {"filePath": PROJECT_FILE_1},  # nested is project
        }
        assert sg.validate_memory(data, WS) == "allow"

    def test_project_path_via_path_key_allow(self):
        # "path" top-level key (fallback) → allow
        data = {"path": PROJECT_FILE_2}
        assert sg.validate_memory(data, WS) == "allow"

    def test_project_path_windows_allow(self):
        # Windows-style project path → allow
        data = {"filePath": PROJECT_WIN}
        assert sg.validate_memory(data, WS_WIN) == "allow"

    # --- Missing / empty path → deny (fail closed)

    def test_no_path_key_deny(self):
        # No filePath or path key at all → deny
        data = {}
        assert sg.validate_memory(data, WS) == "deny"

    def test_empty_file_path_deny(self):
        # filePath is empty string → deny
        data = {"filePath": ""}
        assert sg.validate_memory(data, WS) == "deny"

    def test_none_file_path_deny(self):
        # filePath is None → deny
        data = {"filePath": None}
        assert sg.validate_memory(data, WS) == "deny"

    def test_nested_missing_file_path_deny(self):
        # tool_input present but no filePath inside → deny
        data = {"tool_input": {}}
        assert sg.validate_memory(data, WS) == "deny"

    def test_non_string_file_path_deny(self):
        # filePath is an integer → deny
        data = {"filePath": 42}
        assert sg.validate_memory(data, WS) == "deny"

    # --- Restricted zones → deny

    def test_github_path_deny(self):
        data = {"filePath": GITHUB_FILE}
        assert sg.validate_memory(data, WS) == "deny"

    def test_noagentzone_path_deny(self):
        data = {"filePath": NOAGENT_FILE}
        assert sg.validate_memory(data, WS) == "deny"

    def test_vscode_path_deny(self):
        data = {"filePath": VSCODE_FILE}
        assert sg.validate_memory(data, WS) == "deny"

    def test_docs_path_deny(self):
        # Paths outside project folder (but not an explicit deny zone) are denied
        data = {"filePath": DOCS_FILE}
        assert sg.validate_memory(data, WS) == "deny"

    def test_tests_path_deny(self):
        # tests/ is outside project folder → deny
        data = {"filePath": TESTS_DIR + "/test_something.py"}
        assert sg.validate_memory(data, WS) == "deny"

    # --- Git internals (inside project folder) → deny

    def test_git_internals_deny(self):
        # .git/ inside project folder → deny even though zone == "allow"
        data = {"filePath": GIT_FILE}
        assert sg.validate_memory(data, WS) == "deny"

    # --- Path traversal → deny

    def test_traversal_to_github_deny(self):
        data = {"filePath": f"{WS}/project/../.github/passwd"}
        assert sg.validate_memory(data, WS) == "deny"

    def test_traversal_to_noagentzone_deny(self):
        data = {"filePath": f"{WS}/project/../../NoAgentZone/secret.txt"}
        assert sg.validate_memory(data, WS) == "deny"


# ===========================================================================
# Unit — validate_create_directory()
# ===========================================================================

class TestValidateCreateDirectory:
    """Direct unit tests for validate_create_directory()."""

    # --- Project folder paths → allow

    def test_project_dir_top_level_allow(self):
        # dirPath at top level → allow
        data = {"dirPath": PROJECT_DIR_1}
        assert sg.validate_create_directory(data, WS) == "allow"

    def test_project_dir_nested_tool_input_allow(self):
        # dirPath inside tool_input (VS Code hook format) → allow
        data = {"tool_input": {"dirPath": PROJECT_DIR_1}}
        assert sg.validate_create_directory(data, WS) == "allow"

    def test_project_dir_nested_wins_over_top_level(self):
        # tool_input.dirPath takes precedence over top-level dirPath
        data = {
            "dirPath": GITHUB_DIR,          # top-level is restricted
            "tool_input": {"dirPath": PROJECT_DIR_1},  # nested is project
        }
        assert sg.validate_create_directory(data, WS) == "allow"

    def test_project_dir_deep_nested_allow(self):
        # Deep path inside project folder → allow
        data = {"dirPath": PROJECT_DIR_2}
        assert sg.validate_create_directory(data, WS) == "allow"

    def test_project_dir_windows_allow(self):
        # Windows-style project dir path → allow
        data = {"dirPath": PROJECT_DIR_WIN}
        assert sg.validate_create_directory(data, WS_WIN) == "allow"

    # --- Missing / empty dirPath → deny (fail closed)

    def test_no_dir_path_key_deny(self):
        # No dirPath key at all → deny
        data = {}
        assert sg.validate_create_directory(data, WS) == "deny"

    def test_empty_dir_path_deny(self):
        # dirPath is empty string → deny
        data = {"dirPath": ""}
        assert sg.validate_create_directory(data, WS) == "deny"

    def test_none_dir_path_deny(self):
        # dirPath is None → deny
        data = {"dirPath": None}
        assert sg.validate_create_directory(data, WS) == "deny"

    def test_nested_missing_dir_path_deny(self):
        # tool_input present but no dirPath inside → deny
        data = {"tool_input": {}}
        assert sg.validate_create_directory(data, WS) == "deny"

    def test_non_string_dir_path_deny(self):
        # dirPath is a list → deny
        data = {"dirPath": ["/workspace/project/some/dir"]}
        assert sg.validate_create_directory(data, WS) == "deny"

    # --- Restricted zones → deny

    def test_github_dir_deny(self):
        data = {"dirPath": GITHUB_DIR}
        assert sg.validate_create_directory(data, WS) == "deny"

    def test_noagentzone_dir_deny(self):
        data = {"dirPath": NOAGENT_DIR}
        assert sg.validate_create_directory(data, WS) == "deny"

    def test_vscode_subdir_deny(self):
        data = {"dirPath": f"{WS}/.vscode/themes"}
        assert sg.validate_create_directory(data, WS) == "deny"

    def test_docs_dir_deny(self):
        # Outside project folder → deny
        data = {"dirPath": f"{WS}/docs/new_section"}
        assert sg.validate_create_directory(data, WS) == "deny"

    # --- Git internals (inside project folder) → deny

    def test_git_internals_deny(self):
        data = {"dirPath": GIT_DIR}
        assert sg.validate_create_directory(data, WS) == "deny"

    # --- Path traversal → deny

    def test_traversal_to_github_deny(self):
        data = {"dirPath": f"{WS}/project/../.github/newdir"}
        assert sg.validate_create_directory(data, WS) == "deny"

    def test_traversal_to_noagentzone_deny(self):
        data = {"dirPath": f"{WS}/project/../../NoAgentZone/newdir"}
        assert sg.validate_create_directory(data, WS) == "deny"

    def test_filePath_key_not_used_deny(self):
        # Only filePath key present (wrong key for create_directory) → deny
        data = {"filePath": PROJECT_DIR_1}
        assert sg.validate_create_directory(data, WS) == "deny"


# ===========================================================================
# Security — decide() dispatches memory correctly
# ===========================================================================

class TestDecideMemory:
    """Security tests: decide() intercepts memory before exempt-tool fallback."""

    def _payload(self, file_path=None, use_nested=True):
        """Build a memory tool hook payload."""
        if use_nested:
            tool_input = {}
            if file_path is not None:
                tool_input["filePath"] = file_path
            return {"tool_name": "memory", "tool_input": tool_input}
        payload = {"tool_name": "memory"}
        if file_path is not None:
            payload["filePath"] = file_path
        return payload

    def test_decide_project_path_allow(self):
        # decide() allows memory targeting Project/
        assert sg.decide(self._payload(PROJECT_FILE_1), WS) == "allow"

    def test_decide_no_path_deny(self):
        # decide() denies memory with no filePath (fail closed)
        assert sg.decide(self._payload(), WS) == "deny"

    def test_decide_github_path_deny(self):
        # decide() denies memory targeting .github/
        assert sg.decide(self._payload(GITHUB_FILE), WS) == "deny"

    def test_decide_noagentzone_path_deny(self):
        # decide() denies memory targeting NoAgentZone/
        assert sg.decide(self._payload(NOAGENT_FILE), WS) == "deny"

    def test_decide_vscode_path_deny(self):
        # decide() denies memory targeting .vscode/
        assert sg.decide(self._payload(VSCODE_FILE), WS) == "deny"

    def test_decide_flat_format_project_allow(self):
        # Flat (non-nested) format with project path → allow
        assert sg.decide(self._payload(PROJECT_FILE_2, use_nested=False), WS) == "allow"

    def test_decide_flat_format_deny_zone_deny(self):
        # Flat format with restricted path → deny
        assert sg.decide(self._payload(GITHUB_FILE, use_nested=False), WS) == "deny"

    def test_decide_docs_path_deny(self):
        # docs/ is outside project folder in 2-tier model → deny
        assert sg.decide(self._payload(DOCS_FILE), WS) == "deny"


# ===========================================================================
# Security — decide() dispatches create_directory correctly
# ===========================================================================

class TestDecideCreateDirectory:
    """Security tests: decide() intercepts create_directory before exempt-tool fallback."""

    def _payload(self, dir_path=None, use_nested=True):
        """Build a create_directory tool hook payload."""
        if use_nested:
            tool_input = {}
            if dir_path is not None:
                tool_input["dirPath"] = dir_path
            return {"tool_name": "create_directory", "tool_input": tool_input}
        payload = {"tool_name": "create_directory"}
        if dir_path is not None:
            payload["dirPath"] = dir_path
        return payload

    def test_decide_project_dir_allow(self):
        # decide() allows create_directory targeting Project/
        assert sg.decide(self._payload(PROJECT_DIR_1), WS) == "allow"

    def test_decide_no_dir_path_deny(self):
        # decide() denies create_directory with no dirPath (fail closed)
        assert sg.decide(self._payload(), WS) == "deny"

    def test_decide_github_dir_deny(self):
        # decide() denies create_directory targeting .github/
        assert sg.decide(self._payload(GITHUB_DIR), WS) == "deny"

    def test_decide_noagentzone_dir_deny(self):
        # decide() denies create_directory targeting NoAgentZone/
        assert sg.decide(self._payload(NOAGENT_DIR), WS) == "deny"

    def test_decide_vscode_dir_deny(self):
        # decide() denies create_directory targeting .vscode/
        assert sg.decide(self._payload(f"{WS}/.vscode/themes"), WS) == "deny"

    def test_decide_flat_format_project_allow(self):
        # Flat (non-nested) format with project path → allow
        assert sg.decide(self._payload(PROJECT_DIR_2, use_nested=False), WS) == "allow"

    def test_decide_flat_format_deny_zone_deny(self):
        # Flat format with restricted zone → deny
        assert sg.decide(self._payload(GITHUB_DIR, use_nested=False), WS) == "deny"

    def test_decide_docs_dir_deny(self):
        # docs/ is outside project folder in 2-tier model → deny
        assert sg.decide(self._payload(f"{WS}/docs/new_section"), WS) == "deny"


# ===========================================================================
# Bypass attempts — both tools
# ===========================================================================

class TestBypassAttempts:
    """Adversarial inputs that must be denied for both tools."""

    # --- memory traversal bypasses

    def test_memory_traversal_github(self):
        data = {
            "tool_name": "memory",
            "tool_input": {"filePath": f"{WS}/project/../.github/hooks/secret"},
        }
        assert sg.decide(data, WS) == "deny"

    def test_memory_traversal_noagentzone(self):
        data = {
            "tool_name": "memory",
            "tool_input": {"filePath": f"{WS}/project/../../NoAgentZone/secret"},
        }
        assert sg.decide(data, WS) == "deny"

    def test_memory_null_tool_input_deny(self):
        # tool_input is None (malformed) → fail closed
        data = {"tool_name": "memory", "tool_input": None}
        assert sg.decide(data, WS) == "deny"

    def test_memory_tool_input_wrong_type_deny(self):
        # tool_input is a string (malformed) → no filePath found → deny
        data = {"tool_name": "memory", "tool_input": "not_a_dict"}
        assert sg.decide(data, WS) == "deny"

    def test_memory_git_internals_deny(self):
        # .git/ inside project folder → deny
        data = {"tool_name": "memory", "tool_input": {"filePath": GIT_FILE}}
        assert sg.decide(data, WS) == "deny"

    # --- create_directory traversal bypasses

    def test_create_directory_traversal_github(self):
        data = {
            "tool_name": "create_directory",
            "tool_input": {"dirPath": f"{WS}/project/../.github/injected"},
        }
        assert sg.decide(data, WS) == "deny"

    def test_create_directory_traversal_noagentzone(self):
        data = {
            "tool_name": "create_directory",
            "tool_input": {"dirPath": f"{WS}/project/../../NoAgentZone/injected"},
        }
        assert sg.decide(data, WS) == "deny"

    def test_create_directory_null_tool_input_deny(self):
        data = {"tool_name": "create_directory", "tool_input": None}
        assert sg.decide(data, WS) == "deny"

    def test_create_directory_tool_input_wrong_type_deny(self):
        # tool_input is an integer → no dirPath found → deny
        data = {"tool_name": "create_directory", "tool_input": 99}
        assert sg.decide(data, WS) == "deny"

    def test_create_directory_git_internals_deny(self):
        data = {"tool_name": "create_directory", "tool_input": {"dirPath": GIT_DIR}}
        assert sg.decide(data, WS) == "deny"

    def test_create_directory_wrong_field_name_deny(self):
        # filePath instead of dirPath → no dirPath found → deny
        data = {
            "tool_name": "create_directory",
            "tool_input": {"filePath": PROJECT_DIR_1},  # wrong key
        }
        assert sg.decide(data, WS) == "deny"


# ===========================================================================
# Cross-platform — Windows / POSIX / WSL paths
# ===========================================================================

class TestCrossPlatform:
    """Both tools must pass/fail consistently on Windows, POSIX, and WSL paths."""

    # --- memory — Windows paths

    def test_memory_windows_project_path_allow(self):
        data = {"tool_input": {"filePath": f"{WS_WIN}/project/memories/notes.md"}}
        assert sg.validate_memory(data, WS_WIN) == "allow"

    def test_memory_windows_github_deny(self):
        data = {"tool_input": {"filePath": f"{WS_WIN}/.github/secret"}}
        assert sg.validate_memory(data, WS_WIN) == "deny"

    def test_memory_windows_backslash_path_allow(self):
        data = {"tool_input": {"filePath": r"c:\workspace\project\memories\notes.md"}}
        assert sg.validate_memory(data, WS_WIN) == "allow"

    def test_memory_windows_backslash_github_deny(self):
        data = {"tool_input": {"filePath": r"c:\workspace\.github\secret"}}
        assert sg.validate_memory(data, WS_WIN) == "deny"

    # --- create_directory — Windows paths

    def test_create_directory_windows_project_allow(self):
        data = {"tool_input": {"dirPath": f"{WS_WIN}/project/memories/session"}}
        assert sg.validate_create_directory(data, WS_WIN) == "allow"

    def test_create_directory_windows_github_deny(self):
        data = {"tool_input": {"dirPath": f"{WS_WIN}/.github/hooks"}}
        assert sg.validate_create_directory(data, WS_WIN) == "deny"

    def test_create_directory_windows_backslash_project_allow(self):
        data = {"tool_input": {"dirPath": r"c:\workspace\project\memories\session"}}
        assert sg.validate_create_directory(data, WS_WIN) == "allow"

    def test_create_directory_windows_backslash_noagentzone_deny(self):
        data = {"tool_input": {"dirPath": r"c:\workspace\NoAgentZone\injected"}}
        assert sg.validate_create_directory(data, WS_WIN) == "deny"
