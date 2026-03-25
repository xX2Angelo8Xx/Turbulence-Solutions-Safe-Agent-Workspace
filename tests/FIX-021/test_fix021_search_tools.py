"""Tests for FIX-021 — Fix Search Tools Blocking for Project Folder

Covers:
  - grep_search with no params -> allow
  - grep_search with project includePattern -> allow
  - grep_search with includeIgnoredFiles=True -> deny (unchanged)
  - grep_search with .github includePattern -> deny (unchanged)
  - semantic_search -> allow
  - file_search basic query -> allow
  - file_search with .github in query -> deny
  - file_search with noagentzone in query -> deny
  - file_search with .. in query -> deny
"""
from __future__ import annotations

import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Make security_gate importable from its non-standard location
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "templates", "agent-workbench",
        ".github",
        "hooks",
        "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

WS = "/workspace"


# ===========================================================================
# grep_search — no parameters (FIX-021: allow when no path)
# ===========================================================================

def test_grep_search_no_params_allow():
    """grep_search with no includePattern and no filePath -> allow (FIX-021)."""
    data = {"tool_name": "grep_search", "query": "TODO"}
    assert sg.decide(data, WS) == "allow"


def test_grep_search_no_params_via_validate():
    """validate_grep_search with no path -> allow (FIX-021)."""
    data = {"tool_name": "grep_search", "query": "hello world"}
    assert sg.validate_grep_search(data, WS) == "allow"


# ===========================================================================
# grep_search — project-scoped includePattern
# ===========================================================================

def test_grep_search_project_include_pattern_allow():
    """grep_search without includeIgnoredFiles and with no filePath -> allow."""
    data = {
        "tool_name": "grep_search",
        "query": "def main",
    }
    assert sg.decide(data, WS) == "allow"


def test_grep_search_nested_project_include_pattern_allow():
    """grep_search in VS Code nested format with no flagged params -> allow."""
    data = {
        "tool_name": "grep_search",
        "tool_input": {
            "query": "import os",
        },
    }
    assert sg.decide(data, WS) == "allow"


# ===========================================================================
# grep_search — includeIgnoredFiles=True still denied (unchanged)
# ===========================================================================

def test_grep_search_include_ignored_files_true_denied():
    """grep_search with includeIgnoredFiles=True -> deny (bypass protection unchanged)."""
    data = {
        "tool_name": "grep_search",
        "query": "password",
        "includeIgnoredFiles": True,
    }
    assert sg.decide(data, WS) == "deny"


def test_grep_search_include_ignored_files_string_true_denied():
    """grep_search with includeIgnoredFiles='true' -> deny."""
    data = {
        "tool_name": "grep_search",
        "query": "secret",
        "includeIgnoredFiles": "true",
    }
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# grep_search — .github includePattern still denied (unchanged)
# ===========================================================================

def test_grep_search_github_include_pattern_denied():
    """grep_search with .github includePattern -> deny (protection unchanged)."""
    data = {
        "tool_name": "grep_search",
        "query": "hook",
        "includePattern": ".github/**",
    }
    assert sg.decide(data, WS) == "deny"


def test_grep_search_vscode_include_pattern_denied():
    """grep_search with .vscode includePattern -> deny (protection unchanged)."""
    data = {
        "tool_name": "grep_search",
        "query": "settings",
        "includePattern": ".vscode/**",
    }
    assert sg.decide(data, WS) == "deny"


def test_grep_search_noagentzone_include_pattern_denied():
    """grep_search with NoAgentZone includePattern -> deny (protection unchanged)."""
    data = {
        "tool_name": "grep_search",
        "query": "private",
        "includePattern": "NoAgentZone/**",
    }
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# semantic_search — now allowed (FIX-021)
# ===========================================================================

def test_semantic_search_allow():
    """semantic_search -> allow (FIX-021: VS Code search.exclude hides restricted content)."""
    data = {"tool_name": "semantic_search", "query": "utility functions"}
    assert sg.decide(data, WS) == "allow"


def test_semantic_search_validate_allow():
    """validate_semantic_search -> allow (FIX-021)."""
    data = {"tool_name": "semantic_search", "query": "security gate logic"}
    assert sg.validate_semantic_search(data, WS) == "allow"


def test_semantic_search_nested_format_allow():
    """semantic_search in VS Code nested tool_input format -> allow (FIX-021)."""
    data = {
        "tool_name": "semantic_search",
        "tool_input": {"query": "project module imports"},
    }
    assert sg.decide(data, WS) == "allow"


def test_semantic_search_with_protected_query_allow():
    """semantic_search query text (not a path) mentioning restricted names -> allow.

    The query is search text fed to the semantic index; VS Code's search.exclude
    settings prevent .github/.vscode/NoAgentZone from being indexed.
    """
    data = {"tool_name": "semantic_search", "query": "find .github references"}
    assert sg.decide(data, WS) == "allow"


# ===========================================================================
# file_search — basic query -> allow (FIX-021)
# ===========================================================================

def test_file_search_basic_query_allow():
    """file_search with a plain query -> allow (FIX-021)."""
    data = {"tool_name": "file_search", "query": "**/*.py"}
    assert sg.decide(data, WS) == "allow"


def test_file_search_nested_format_allow():
    """file_search in VS Code nested tool_input format -> allow."""
    data = {
        "tool_name": "file_search",
        "tool_input": {"query": "src/**/*.py"},
    }
    assert sg.decide(data, WS) == "allow"


def test_file_search_no_query_allow():
    """file_search with no query field -> allow (no restricted content)."""
    data = {"tool_name": "file_search"}
    assert sg.decide(data, WS) == "allow"


# ===========================================================================
# file_search — .github in query -> deny
# ===========================================================================

def test_file_search_github_in_query_denied():
    """file_search with .github in query -> deny."""
    data = {"tool_name": "file_search", "query": ".github/**"}
    assert sg.decide(data, WS) == "deny"


def test_file_search_github_nested_denied():
    """file_search with .github in nested tool_input query -> deny."""
    data = {
        "tool_name": "file_search",
        "tool_input": {"query": ".github/hooks/**"},
    }
    assert sg.decide(data, WS) == "deny"


def test_file_search_github_mixed_case_denied():
    """file_search with .GITHUB in query (case-insensitive) -> deny."""
    data = {"tool_name": "file_search", "query": ".GITHUB/scripts"}
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# file_search — noagentzone in query -> deny
# ===========================================================================

def test_file_search_noagentzone_in_query_denied():
    """file_search with noagentzone in query -> deny."""
    data = {"tool_name": "file_search", "query": "NoAgentZone/**"}
    assert sg.decide(data, WS) == "deny"


def test_file_search_noagentzone_lowercase_denied():
    """file_search with noagentzone (all lowercase) in query -> deny."""
    data = {"tool_name": "file_search", "query": "noagentzone/secret.txt"}
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# file_search — .vscode in query -> deny
# ===========================================================================

def test_file_search_vscode_in_query_denied():
    """file_search with .vscode in query -> deny."""
    data = {"tool_name": "file_search", "query": ".vscode/**"}
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# file_search — .. in query -> deny
# ===========================================================================

def test_file_search_dotdot_in_query_denied():
    """file_search with .. (path traversal) in query -> deny."""
    data = {"tool_name": "file_search", "query": "../other-project/**"}
    assert sg.decide(data, WS) == "deny"


def test_file_search_dotdot_nested_denied():
    """file_search with .. in nested tool_input query -> deny."""
    data = {
        "tool_name": "file_search",
        "tool_input": {"query": "project/../../.vscode"},
    }
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# TESTER edge-case additions (TST-1682 – TST-1690)
# ===========================================================================

# TST-1682: file_search — .VSCODE (fully uppercase) must still be denied
def test_file_search_vscode_mixed_case_denied():
    """TST-1682: file_search with .VSCODE in query (uppercase) -> deny (case-insensitive check)."""
    data = {"tool_name": "file_search", "query": ".VSCODE/settings.json"}
    assert sg.decide(data, WS) == "deny"


# TST-1683: file_search — .GitHub (camelCase) must still be denied
def test_file_search_github_camelcase_denied():
    """TST-1683: file_search with .GitHub in query (camelCase) -> deny (case-insensitive check)."""
    data = {"tool_name": "file_search", "query": ".GitHub/workflows/**"}
    assert sg.decide(data, WS) == "deny"


# TST-1684: file_search — empty string query -> allow
def test_file_search_empty_string_query_allow():
    """TST-1684: file_search with empty string query -> allow (no restricted names present)."""
    data = {"tool_name": "file_search", "query": ""}
    assert sg.decide(data, WS) == "allow"


# TST-1685: file_search — whitespace-only query -> allow
def test_file_search_whitespace_query_allow():
    """TST-1685: file_search with whitespace-only query -> allow."""
    data = {"tool_name": "file_search", "query": "   "}
    assert sg.decide(data, WS) == "allow"


# TST-1686: file_search — tool_input present but empty dict -> allow
def test_file_search_tool_input_empty_dict_allow():
    """TST-1686: file_search with tool_input={} and no top-level query -> allow."""
    data = {"tool_name": "file_search", "tool_input": {}}
    assert sg.decide(data, WS) == "allow"


# TST-1687: grep_search — explicit project-scoped includePattern -> allow
def test_grep_search_explicit_project_include_pattern_allow(tmp_path):
    """TST-1687: grep_search with includePattern='Project/**' -> allow (project zone).

    Uses a real temporary workspace so detect_project_folder can scan the directory.
    """
    (tmp_path / "Project").mkdir()
    ws = str(tmp_path).replace("\\", "/").lower()
    data = {
        "tool_name": "grep_search",
        "query": "def test_",
        "includePattern": "Project/**",
    }
    assert sg.decide(data, ws) == "allow"


# TST-1688: grep_search — uppercase .GITHUB/** includePattern -> deny
def test_grep_search_uppercase_github_include_pattern_denied():
    """TST-1688: grep_search with includePattern='.GITHUB/**' -> deny (zone_classifier normalizes to lowercase)."""
    data = {
        "tool_name": "grep_search",
        "query": "secret",
        "includePattern": ".GITHUB/**",
    }
    assert sg.decide(data, WS) == "deny"


# TST-1689: file_search — path traversal combined with .github -> deny
def test_file_search_traversal_combined_with_github_denied():
    """TST-1689: file_search with 'src/../.github/hooks' -> deny (both .. and .github trigger)."""
    data = {"tool_name": "file_search", "query": "src/../.github/hooks"}
    assert sg.decide(data, WS) == "deny"


# TST-1690: grep_search — nested tool_input with .vscode includePattern -> deny
def test_grep_search_nested_vscode_include_pattern_denied():
    """TST-1690: grep_search with .vscode includePattern in nested tool_input -> deny."""
    data = {
        "tool_name": "grep_search",
        "tool_input": {
            "query": "editor settings",
            "includePattern": ".vscode/**",
        },
    }
    assert sg.decide(data, WS) == "deny"
