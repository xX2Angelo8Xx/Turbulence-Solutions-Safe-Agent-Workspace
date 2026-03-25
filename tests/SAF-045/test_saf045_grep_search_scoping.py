"""SAF-045 — Verify grep_search scoping and search.exclude.

Covers:
  validate_grep_search() / decide() — deny cases:
    - includePattern targeting .github/ -> deny
    - includePattern targeting .vscode/ -> deny
    - includePattern targeting NoAgentZone/ -> deny
    - includePattern bare .github -> deny
    - includePattern bare NoAgentZone -> deny
    - includePattern with path traversal -> deny
    - traversal resolving into .github -> deny
    - includeIgnoredFiles=True -> deny
    - includeIgnoredFiles="true" -> deny
    - includeIgnoredFiles=1 -> deny
    - Nested tool_input with .github includePattern -> deny
    - Nested tool_input with NoAgentZone includePattern -> deny
    - Nested tool_input with includeIgnoredFiles=True -> deny
    - decide() integration: .github, .vscode, NoAgentZone, includeIgnoredFiles -> deny

  validate_grep_search() / decide() — allow cases:
    - No parameters -> allow
    - Query only (no includePattern) -> allow
    - includePattern scoped to project folder -> allow
    - includePattern project/**/*.py -> allow
    - Nested tool_input with project-scoped includePattern -> allow
    - includeIgnoredFiles=False with project includePattern -> allow
    - decide() integration: no params, project includePattern -> allow

  settings.json verification:
    - files.exclude contains .github -> True
    - files.exclude contains .vscode -> True
    - files.exclude contains NoAgentZone entry -> True  (SAF-045 gap fix)
    - search.exclude contains .github -> True
    - search.exclude contains .vscode -> True
    - search.exclude contains NoAgentZone -> True
    - files.exclude covers all three restricted zones -> True
    - search.exclude covers all three restricted zones -> True
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Make security_gate importable from its non-standard location
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

# Workspace root used across all tests.  The mock_project_folder fixture removes
# the requirement for this directory to exist on disk.
WS = "c:/workspace"


@pytest.fixture(autouse=True)
def mock_project_folder():
    """Patch detect_project_folder so tests do not need the workspace on disk."""
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# ===========================================================================
# validate_grep_search — deny: restricted-zone includePattern
# ===========================================================================

def test_grep_search_github_include_pattern_deny():
    """grep_search with .github/** includePattern -> deny."""
    data = {"tool_name": "grep_search", "query": "hook", "includePattern": ".github/**"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_vscode_include_pattern_deny():
    """grep_search with .vscode/** includePattern -> deny."""
    data = {"tool_name": "grep_search", "query": "settings", "includePattern": ".vscode/**"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_noagentzone_include_pattern_deny():
    """grep_search with NoAgentZone/** includePattern -> deny."""
    data = {"tool_name": "grep_search", "query": "secret", "includePattern": "NoAgentZone/**"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_noagentzone_bare_include_pattern_deny():
    """grep_search with bare NoAgentZone includePattern -> deny."""
    data = {"tool_name": "grep_search", "query": "credential", "includePattern": "NoAgentZone"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_github_bare_include_pattern_deny():
    """grep_search with bare .github includePattern -> deny."""
    data = {"tool_name": "grep_search", "query": "hooks", "includePattern": ".github"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_traversal_include_pattern_deny():
    """grep_search with path traversal in includePattern -> deny."""
    data = {"tool_name": "grep_search", "query": "password", "includePattern": "../../../etc/**"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_traversal_to_github_deny():
    """grep_search with traversal resolving into .github -> deny."""
    data = {"tool_name": "grep_search", "query": "token", "includePattern": "project/../../.github/**"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_include_ignored_files_bool_deny():
    """grep_search with includeIgnoredFiles=True -> deny."""
    data = {"tool_name": "grep_search", "query": "password", "includeIgnoredFiles": True}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_include_ignored_files_string_deny():
    """grep_search with includeIgnoredFiles='true' -> deny."""
    data = {"tool_name": "grep_search", "query": "secret", "includeIgnoredFiles": "true"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_include_ignored_files_int_deny():
    """grep_search with includeIgnoredFiles=1 -> deny."""
    data = {"tool_name": "grep_search", "query": "key", "includeIgnoredFiles": 1}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_nested_github_include_pattern_deny():
    """grep_search nested tool_input format with .github/** includePattern -> deny."""
    data = {
        "tool_name": "grep_search",
        "tool_input": {
            "query": "config",
            "includePattern": ".github/**",
        },
    }
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_nested_noagentzone_include_pattern_deny():
    """grep_search nested tool_input format with NoAgentZone/** includePattern -> deny."""
    data = {
        "tool_name": "grep_search",
        "tool_input": {
            "query": "restricted",
            "includePattern": "NoAgentZone/**",
        },
    }
    assert sg.validate_grep_search(data, WS) == "deny"


def test_grep_search_nested_include_ignored_files_deny():
    """grep_search nested tool_input format with includeIgnoredFiles=True -> deny."""
    data = {
        "tool_name": "grep_search",
        "tool_input": {
            "query": "anything",
            "includeIgnoredFiles": True,
        },
    }
    assert sg.validate_grep_search(data, WS) == "deny"


# --- deny via decide() integration ---

def test_grep_search_github_via_decide_deny():
    """decide() with grep_search + .github includePattern -> deny."""
    data = {"tool_name": "grep_search", "query": "hook", "includePattern": ".github/**"}
    assert sg.decide(data, WS) == "deny"


def test_grep_search_vscode_via_decide_deny():
    """decide() with grep_search + .vscode includePattern -> deny."""
    data = {"tool_name": "grep_search", "query": "settings", "includePattern": ".vscode/**"}
    assert sg.decide(data, WS) == "deny"


def test_grep_search_noagentzone_via_decide_deny():
    """decide() with grep_search + NoAgentZone includePattern -> deny."""
    data = {"tool_name": "grep_search", "query": "private", "includePattern": "NoAgentZone/**"}
    assert sg.decide(data, WS) == "deny"


def test_grep_search_include_ignored_via_decide_deny():
    """decide() with grep_search + includeIgnoredFiles=True -> deny."""
    data = {"tool_name": "grep_search", "query": "creds", "includeIgnoredFiles": True}
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# validate_grep_search — allow: safe project-folder usage
# ===========================================================================

def test_grep_search_no_params_allow():
    """grep_search with no includePattern and no restricted params -> allow."""
    data = {"tool_name": "grep_search", "query": "TODO"}
    assert sg.validate_grep_search(data, WS) == "allow"


def test_grep_search_query_only_allow():
    """grep_search with only a query field (no includePattern) -> allow."""
    data = {"tool_name": "grep_search", "query": "import os"}
    assert sg.validate_grep_search(data, WS) == "allow"


def test_grep_search_project_include_pattern_allow():
    """grep_search with project/** includePattern (project folder) -> allow."""
    data = {"tool_name": "grep_search", "query": "class", "includePattern": "project/**"}
    assert sg.validate_grep_search(data, WS) == "allow"


def test_grep_search_project_py_glob_allow():
    """grep_search with project/**/*.py includePattern -> allow."""
    data = {"tool_name": "grep_search", "query": "def main", "includePattern": "project/**/*.py"}
    assert sg.validate_grep_search(data, WS) == "allow"


def test_grep_search_nested_safe_allow():
    """grep_search nested tool_input with project-scoped includePattern -> allow."""
    data = {
        "tool_name": "grep_search",
        "tool_input": {
            "query": "error handling",
            "includePattern": "project/**/*.py",
        },
    }
    assert sg.validate_grep_search(data, WS) == "allow"


def test_grep_search_include_ignored_false_allow():
    """grep_search with includeIgnoredFiles=False and project includePattern -> allow."""
    data = {
        "tool_name": "grep_search",
        "query": "logging",
        "includeIgnoredFiles": False,
        "includePattern": "project/**",
    }
    assert sg.validate_grep_search(data, WS) == "allow"


# --- allow via decide() integration ---

def test_grep_search_no_params_via_decide_allow():
    """decide() with grep_search + no params -> allow."""
    data = {"tool_name": "grep_search", "query": "TODO"}
    assert sg.decide(data, WS) == "allow"


def test_grep_search_project_include_via_decide_allow():
    """decide() with grep_search + project/**/*.py includePattern -> allow."""
    data = {"tool_name": "grep_search", "query": "function", "includePattern": "project/**/*.py"}
    assert sg.decide(data, WS) == "allow"


# ===========================================================================
# settings.json verification — files.exclude and search.exclude
# ===========================================================================

def _load_settings() -> dict:
    """Load templates/coding/.vscode/settings.json."""
    with open(_SETTINGS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def test_settings_files_exclude_github():
    """settings.json files.exclude hides .github."""
    settings = _load_settings()
    files_exclude = settings.get("files.exclude", {})
    assert ".github" in files_exclude, "files.exclude must contain .github"
    assert files_exclude[".github"] is True, "files.exclude['.github'] must be true"


def test_settings_files_exclude_vscode():
    """settings.json files.exclude hides .vscode."""
    settings = _load_settings()
    files_exclude = settings.get("files.exclude", {})
    assert ".vscode" in files_exclude, "files.exclude must contain .vscode"
    assert files_exclude[".vscode"] is True, "files.exclude['.vscode'] must be true"


def test_settings_files_exclude_noagentzone():
    """settings.json files.exclude hides NoAgentZone (SAF-045 gap fix)."""
    settings = _load_settings()
    files_exclude = settings.get("files.exclude", {})
    noagentzone_covered = any(
        "noagentzone" in k.lower() for k, v in files_exclude.items() if v is True
    )
    assert noagentzone_covered, (
        "files.exclude must contain a NoAgentZone entry — "
        f"current keys: {list(files_exclude.keys())}"
    )


def test_settings_search_exclude_github():
    """settings.json search.exclude excludes .github from search."""
    settings = _load_settings()
    search_exclude = settings.get("search.exclude", {})
    github_covered = any(
        ".github" in k.lower() for k, v in search_exclude.items() if v is True
    )
    assert github_covered, "search.exclude must contain a .github entry"


def test_settings_search_exclude_vscode():
    """settings.json search.exclude excludes .vscode from search."""
    settings = _load_settings()
    search_exclude = settings.get("search.exclude", {})
    vscode_covered = any(
        ".vscode" in k.lower() for k, v in search_exclude.items() if v is True
    )
    assert vscode_covered, "search.exclude must contain a .vscode entry"


def test_settings_search_exclude_noagentzone():
    """settings.json search.exclude excludes NoAgentZone from search."""
    settings = _load_settings()
    search_exclude = settings.get("search.exclude", {})
    noagentzone_covered = any(
        "noagentzone" in k.lower() for k, v in search_exclude.items() if v is True
    )
    assert noagentzone_covered, (
        "search.exclude must contain a NoAgentZone entry — "
        f"current keys: {list(search_exclude.keys())}"
    )


def test_settings_files_exclude_all_three_zones():
    """settings.json files.exclude covers all three restricted zones."""
    settings = _load_settings()
    files_exclude = settings.get("files.exclude", {})
    enabled_keys = {k.lower() for k, v in files_exclude.items() if v is True}
    for zone in (".github", ".vscode", "noagentzone"):
        covered = any(zone in k for k in enabled_keys)
        assert covered, (
            f"files.exclude does not cover zone '{zone}' — "
            f"keys: {list(files_exclude.keys())}"
        )


def test_settings_search_exclude_all_three_zones():
    """settings.json search.exclude covers all three restricted zones."""
    settings = _load_settings()
    search_exclude = settings.get("search.exclude", {})
    enabled_keys = {k.lower() for k, v in search_exclude.items() if v is True}
    for zone in (".github", ".vscode", "noagentzone"):
        covered = any(zone in k for k in enabled_keys)
        assert covered, (
            f"search.exclude does not cover zone '{zone}' — "
            f"keys: {list(search_exclude.keys())}"
        )
