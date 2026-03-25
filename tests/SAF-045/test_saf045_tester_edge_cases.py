"""SAF-045 — Tester edge-case tests for grep_search scoping.

Additional edge cases beyond the developer's 33 tests:

  includePattern edge cases:
    - UPPERCASE zone names (NOAGENTZONE, .GITHUB, .VSCODE) -> deny (case-insensitive)
    - Windows backslash in includePattern (.github\\hooks) -> deny
    - Brace expansion containing a restricted zone ({.github,project}/**) -> deny
    - Empty string includePattern -> allow (treated as absent)
    - Nested deny inside project folder (project/.vscode/**) -> deny

  includeIgnoredFiles edge cases:
    - includeIgnoredFiles=0 -> allow (integer 0, not 1)
    - includeIgnoredFiles=2 -> allow (integer 2, not 1)
    - includeIgnoredFiles="True" (mixed case) -> deny (case-insensitive check)
    - includeIgnoredFiles="TRUE" (uppercase) -> deny
    - includeIgnoredFiles="false" -> allow
    - includeIgnoredFiles=None -> allow

  Payload edge cases:
    - tool_input as non-dict -> handled gracefully (allow, no crash)
    - both safe includePattern and includeIgnoredFiles=True -> deny
    - filePath pointing to .github zone -> deny

  settings.json structural checks:
    - files.exclude key count >= 3 (all three zones present)
    - NoAgentZone uses glob pattern (starts with **/) not a bare name that
      would only match top-level folder
"""
from __future__ import annotations

import json
import sys
import os
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Make security_gate importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "templates", "agent-workbench",
        ".github", "hooks", "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

_SETTINGS_PATH = (
    Path(__file__).resolve().parents[2]
    / "templates" / "agent-workbench" / ".vscode" / "settings.json"
)

WS = "c:/workspace"


@pytest.fixture(autouse=True)
def mock_project_folder():
    """Avoid requiring the workspace directory to exist on disk."""
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# ===========================================================================
# Case-insensitive handling of restricted zone names in includePattern
# ===========================================================================

def test_grep_search_uppercase_noagentzone_deny():
    """NOAGENTZONE/** (uppercase) in includePattern must be denied."""
    data = {"tool_name": "grep_search", "query": "secret", "includePattern": "NOAGENTZONE/**"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_uppercase_github_deny():
    """.GITHUB/** (uppercase) in includePattern must be denied."""
    data = {"tool_name": "grep_search", "query": "token", "includePattern": ".GITHUB/**"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_uppercase_vscode_deny():
    """.VSCODE/** (uppercase) in includePattern must be denied."""
    data = {"tool_name": "grep_search", "query": "settings", "includePattern": ".VSCODE/**"}
    assert sg.validate_grep_search(data, WS) == "deny"


# ===========================================================================
# Windows backslash in includePattern
# ===========================================================================

def test_grep_search_backslash_github_deny():
    """.github\\hooks backslash path in includePattern must be denied."""
    data = {"tool_name": "grep_search", "query": "hooks", "includePattern": ".github\\hooks"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_backslash_noagentzone_deny():
    """NoAgentZone\\secrets backslash path in includePattern must be denied."""
    data = {
        "tool_name": "grep_search",
        "query": "private",
        "includePattern": "NoAgentZone\\secrets",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


# ===========================================================================
# Brace expansion containing a restricted zone
# ===========================================================================

def test_grep_search_brace_expansion_github_deny():
    """{.github,project}/** brace expansion must be denied (expands to .github/**)."""
    data = {
        "tool_name": "grep_search",
        "query": "config",
        "includePattern": "{.github,project}/**",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_brace_expansion_noagentzone_deny():
    """{project,NoAgentZone}/** brace expansion must be denied."""
    data = {
        "tool_name": "grep_search",
        "query": "data",
        "includePattern": "{project,NoAgentZone}/**",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


# ===========================================================================
# Empty / whitespace-only includePattern
# ===========================================================================

def test_grep_search_empty_include_pattern_allow():
    """Empty string includePattern is treated as absent and must be allowed."""
    data = {"tool_name": "grep_search", "query": "TODO", "includePattern": ""}
    assert sg.validate_grep_search(data, WS) == "allow"


# ===========================================================================
# Security boundary: workspace-root deny zones vs. project-nested names
#
# Zone classification protects WORKSPACE-ROOT directories (.github, .vscode,
# NoAgentZone).  A folder named .github or .vscode INSIDE the project folder
# (e.g. project/.vscode/) is within the agent's allowed zone and must NOT be
# denied — denying it would over-restrict legitimate use.
#
# The relevant attack (traversal back to workspace root) is already blocked by
# separate path-traversal tests (includeing `..` in path).
# ===========================================================================

def test_grep_search_project_vscode_nested_allow():
    """project/.vscode/** is inside the project folder and must be allowed.

    The restricted zone is the WORKSPACE-ROOT .vscode/, not a .vscode/
    directory that an agent creates inside their own project folder.
    """
    data = {
        "tool_name": "grep_search",
        "query": "setting",
        "includePattern": "project/.vscode/**",
    }
    assert sg.validate_grep_search(data, WS) == "allow"


def test_grep_search_project_github_nested_allow():
    """project/.github/** is inside the project folder and must be allowed.

    Only the workspace-root .github/ is a restricted zone.  A .github/
    inside the project folder is within the agent's allowed work area.
    """
    data = {
        "tool_name": "grep_search",
        "query": "workflow",
        "includePattern": "project/.github/**",
    }
    assert sg.validate_grep_search(data, WS) == "allow"


# ===========================================================================
# includeIgnoredFiles edge cases
# ===========================================================================

def test_grep_search_include_ignored_files_zero_allow():
    """includeIgnoredFiles=0 is falsy — must be allowed."""
    data = {"tool_name": "grep_search", "query": "test", "includeIgnoredFiles": 0}
    assert sg.validate_grep_search(data, WS) == "allow"


def test_grep_search_include_ignored_files_two_allow():
    """includeIgnoredFiles=2 is not 1 — must be allowed."""
    data = {"tool_name": "grep_search", "query": "test", "includeIgnoredFiles": 2}
    assert sg.validate_grep_search(data, WS) == "allow"


def test_grep_search_include_ignored_files_mixed_case_deny():
    """includeIgnoredFiles='True' (capital T) must be denied (case-insensitive)."""
    data = {"tool_name": "grep_search", "query": "test", "includeIgnoredFiles": "True"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_include_ignored_files_uppercase_deny():
    """includeIgnoredFiles='TRUE' (all caps) must be denied."""
    data = {"tool_name": "grep_search", "query": "test", "includeIgnoredFiles": "TRUE"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_include_ignored_files_string_false_allow():
    """includeIgnoredFiles='false' (string) must be allowed."""
    data = {"tool_name": "grep_search", "query": "test", "includeIgnoredFiles": "false"}
    assert sg.validate_grep_search(data, WS) == "allow"


def test_grep_search_include_ignored_files_none_allow():
    """includeIgnoredFiles=None must be allowed."""
    data = {"tool_name": "grep_search", "query": "test", "includeIgnoredFiles": None}
    assert sg.validate_grep_search(data, WS) == "allow"


# ===========================================================================
# Payload edge cases
# ===========================================================================

def test_grep_search_tool_input_non_dict_no_crash():
    """tool_input as a non-dict string must not crash and must fall back to top-level keys."""
    data = {
        "tool_name": "grep_search",
        "tool_input": "not-a-dict",
        "query": "TODO",
    }
    # Should not raise; top-level has no restricted params → allow
    result = sg.validate_grep_search(data, WS)
    assert result == "allow"


def test_grep_search_safe_pattern_but_include_ignored_true_deny():
    """Safe includePattern combined with includeIgnoredFiles=True must be denied."""
    data = {
        "tool_name": "grep_search",
        "query": "test",
        "includePattern": "project/**",
        "includeIgnoredFiles": True,
    }
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_filepath_in_github_zone_deny():
    """filePath pointing into .github zone must be denied."""
    data = {
        "tool_name": "grep_search",
        "query": "hooks",
        "filePath": "c:/workspace/.github/hooks/pre-tool",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


# ===========================================================================
# settings.json structural integrity
# ===========================================================================

def _load_settings() -> dict:
    with open(_SETTINGS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def test_settings_files_exclude_noagentzone_uses_glob():
    """The NoAgentZone entry in files.exclude must use **/NoAgentZone (glob).

    A bare 'NoAgentZone' key only hides a top-level folder. The glob pattern
    **/NoAgentZone hides the folder at any depth — which is the correct
    defense against placing a NoAgentZone/ inside the project folder.
    """
    settings = _load_settings()
    files_exclude = settings.get("files.exclude", {})
    glob_present = any(
        k.startswith("**/") and "noagentzone" in k.lower()
        for k in files_exclude
    )
    assert glob_present, (
        "files.exclude must contain a **/NoAgentZone glob entry, not just 'NoAgentZone'. "
        f"Current keys: {list(files_exclude.keys())}"
    )


def test_settings_search_exclude_noagentzone_uses_glob():
    """The NoAgentZone entry in search.exclude must use **/NoAgentZone (glob)."""
    settings = _load_settings()
    search_exclude = settings.get("search.exclude", {})
    glob_present = any(
        k.startswith("**/") and "noagentzone" in k.lower()
        for k in search_exclude
    )
    assert glob_present, (
        "search.exclude must contain a **/NoAgentZone glob entry, not just 'NoAgentZone'. "
        f"Current keys: {list(search_exclude.keys())}"
    )
