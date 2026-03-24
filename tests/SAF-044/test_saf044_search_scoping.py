"""SAF-044 — Scope semantic_search and search_subagent.

Covers:
  validate_semantic_search():
    - General natural language query -> allow
    - Query mentioning zone name as text -> allow
    - Path traversal in query -> deny
    - Absolute path to deny zone -> deny
    - Nested tool_input format -> allow
    - No query field -> allow

  validate_search_subagent():
    - General natural language query -> allow
    - Query containing .github -> deny
    - Query containing .vscode -> deny
    - Query containing NoAgentZone (case-insensitive) -> deny
    - Path traversal in query -> deny
    - Absolute path to deny zone -> deny
    - Nested tool_input format -> deny (zone name)
    - No query field -> allow

  decide() integration:
    - search_subagent with safe query -> allow
    - search_subagent with deny-zone query -> deny
    - search_subagent with path traversal -> deny
    - semantic_search with path traversal -> deny
    - semantic_search with absolute deny-zone path -> deny
"""
from __future__ import annotations

import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Make security_gate importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "templates", "coding",
        ".github", "hooks", "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

WS = "/workspace"
WS_WIN = "C:/workspace"


# ===========================================================================
# validate_semantic_search — allow cases
# ===========================================================================

def test_semantic_search_general_query_allow():
    """validate_semantic_search: general natural language query -> allow."""
    data = {"tool_name": "semantic_search", "query": "utility functions in src"}
    assert sg.validate_semantic_search(data, WS) == "allow"


def test_semantic_search_zone_name_as_text_allow():
    """validate_semantic_search: query mentioning .github as text -> allow.

    The query is natural language; VS Code search.exclude prevents .github
    content from appearing in the semantic index regardless.
    """
    data = {"tool_name": "semantic_search", "query": "find .github references"}
    assert sg.validate_semantic_search(data, WS) == "allow"


def test_semantic_search_vscode_text_allow():
    """validate_semantic_search: query mentioning .vscode as text -> allow."""
    data = {"tool_name": "semantic_search", "query": "settings in .vscode folder"}
    assert sg.validate_semantic_search(data, WS) == "allow"


def test_semantic_search_no_query_allow():
    """validate_semantic_search: no query field -> allow."""
    data = {"tool_name": "semantic_search"}
    assert sg.validate_semantic_search(data, WS) == "allow"


def test_semantic_search_nested_format_allow():
    """validate_semantic_search: nested tool_input format -> allow."""
    data = {
        "tool_name": "semantic_search",
        "tool_input": {"query": "error handling patterns"},
    }
    assert sg.validate_semantic_search(data, WS) == "allow"


def test_semantic_search_absolute_project_path_allow():
    """validate_semantic_search: absolute path inside project -> allow."""
    data = {"tool_name": "semantic_search", "query": "/workspace/src/main.py"}
    assert sg.validate_semantic_search(data, WS) == "allow"


# ===========================================================================
# validate_semantic_search — deny cases
# ===========================================================================

def test_semantic_search_path_traversal_deny():
    """validate_semantic_search: path traversal in query -> deny."""
    data = {"tool_name": "semantic_search", "query": "../.github/hooks"}
    assert sg.validate_semantic_search(data, WS) == "deny"


def test_semantic_search_double_dot_deny():
    """validate_semantic_search: embedded .. sequence -> deny."""
    data = {"tool_name": "semantic_search", "query": "search in /workspace/../../etc"}
    assert sg.validate_semantic_search(data, WS) == "deny"


def test_semantic_search_absolute_deny_zone_unix_deny():
    """validate_semantic_search: absolute Unix path into deny zone -> deny."""
    data = {"tool_name": "semantic_search", "query": "/workspace/.github/hooks.py"}
    assert sg.validate_semantic_search(data, WS) == "deny"


def test_semantic_search_absolute_deny_zone_windows_deny():
    """validate_semantic_search: absolute Windows path into deny zone -> deny."""
    data = {"tool_name": "semantic_search", "query": "C:/workspace/.vscode/settings.json"}
    assert sg.validate_semantic_search(data, WS_WIN) == "deny"


# ===========================================================================
# validate_search_subagent — allow cases
# ===========================================================================

def test_search_subagent_general_query_allow():
    """validate_search_subagent: generic natural language query -> allow."""
    data = {"tool_name": "search_subagent", "query": "how does error handling work"}
    assert sg.validate_search_subagent(data, WS) == "allow"


def test_search_subagent_glob_pattern_allow():
    """validate_search_subagent: safe glob pattern -> allow."""
    data = {"tool_name": "search_subagent", "query": "src/components/**/*.tsx"}
    assert sg.validate_search_subagent(data, WS) == "allow"


def test_search_subagent_no_query_allow():
    """validate_search_subagent: no query field -> allow."""
    data = {"tool_name": "search_subagent"}
    assert sg.validate_search_subagent(data, WS) == "allow"


def test_search_subagent_nested_safe_query_allow():
    """validate_search_subagent: nested tool_input with safe query -> allow."""
    data = {
        "tool_name": "search_subagent",
        "tool_input": {"query": "find all test files"},
    }
    assert sg.validate_search_subagent(data, WS) == "allow"


def test_search_subagent_absolute_project_path_allow():
    """validate_search_subagent: absolute path inside project -> allow."""
    data = {"tool_name": "search_subagent", "query": "/workspace/src/**/*.py"}
    assert sg.validate_search_subagent(data, WS) == "allow"


# ===========================================================================
# validate_search_subagent — deny cases: deny-zone names
# ===========================================================================

def test_search_subagent_github_query_deny():
    """validate_search_subagent: query containing .github -> deny."""
    data = {"tool_name": "search_subagent", "query": "search .github for hook scripts"}
    assert sg.validate_search_subagent(data, WS) == "deny"


def test_search_subagent_vscode_query_deny():
    """validate_search_subagent: query containing .vscode -> deny."""
    data = {"tool_name": "search_subagent", "query": "find files in .vscode"}
    assert sg.validate_search_subagent(data, WS) == "deny"


def test_search_subagent_noagentzone_query_deny():
    """validate_search_subagent: query containing NoAgentZone -> deny."""
    data = {"tool_name": "search_subagent", "query": "search NoAgentZone directory"}
    assert sg.validate_search_subagent(data, WS) == "deny"


def test_search_subagent_noagentzone_lowercase_deny():
    """validate_search_subagent: noagentzone in lowercase -> deny (case-insensitive)."""
    data = {"tool_name": "search_subagent", "query": "find content in noagentzone"}
    assert sg.validate_search_subagent(data, WS) == "deny"


def test_search_subagent_github_glob_deny():
    """validate_search_subagent: glob explicitly targeting .github -> deny."""
    data = {"tool_name": "search_subagent", "query": ".github/**/*.yml"}
    assert sg.validate_search_subagent(data, WS) == "deny"


def test_search_subagent_nested_github_query_deny():
    """validate_search_subagent: nested tool_input with .github query -> deny."""
    data = {
        "tool_name": "search_subagent",
        "tool_input": {"query": "find hooks in .github"},
    }
    assert sg.validate_search_subagent(data, WS) == "deny"


# ===========================================================================
# validate_search_subagent — deny cases: path traversal
# ===========================================================================

def test_search_subagent_path_traversal_deny():
    """validate_search_subagent: path traversal sequence -> deny."""
    data = {"tool_name": "search_subagent", "query": "../../etc/passwd"}
    assert sg.validate_search_subagent(data, WS) == "deny"


def test_search_subagent_traversal_embedded_deny():
    """validate_search_subagent: embedded .. in query -> deny."""
    data = {"tool_name": "search_subagent", "query": "/workspace/../secrets"}
    assert sg.validate_search_subagent(data, WS) == "deny"


# ===========================================================================
# validate_search_subagent — deny cases: absolute paths to deny zones
# ===========================================================================

def test_search_subagent_absolute_deny_zone_deny():
    """validate_search_subagent: absolute path into deny zone -> deny."""
    data = {"tool_name": "search_subagent", "query": "/workspace/.vscode/settings.json"}
    assert sg.validate_search_subagent(data, WS) == "deny"


def test_search_subagent_absolute_deny_zone_windows_deny():
    """validate_search_subagent: absolute Windows path into deny zone -> deny."""
    data = {"tool_name": "search_subagent", "query": "C:/workspace/.github/**"}
    assert sg.validate_search_subagent(data, WS_WIN) == "deny"


# ===========================================================================
# decide() integration — search_subagent
# ===========================================================================

def test_decide_search_subagent_safe_query_allow():
    """decide(): search_subagent with safe query -> allow."""
    data = {"tool_name": "search_subagent", "query": "how does authentication work"}
    assert sg.decide(data, WS) == "allow"


def test_decide_search_subagent_github_deny():
    """decide(): search_subagent with .github in query -> deny."""
    data = {"tool_name": "search_subagent", "query": "find .github workflows"}
    assert sg.decide(data, WS) == "deny"


def test_decide_search_subagent_vscode_deny():
    """decide(): search_subagent with .vscode in query -> deny."""
    data = {"tool_name": "search_subagent", "query": "settings in .vscode"}
    assert sg.decide(data, WS) == "deny"


def test_decide_search_subagent_traversal_deny():
    """decide(): search_subagent with path traversal -> deny."""
    data = {"tool_name": "search_subagent", "query": "../../secrets"}
    assert sg.decide(data, WS) == "deny"


def test_decide_search_subagent_no_query_allow():
    """decide(): search_subagent with no query -> allow."""
    data = {"tool_name": "search_subagent"}
    assert sg.decide(data, WS) == "allow"


# ===========================================================================
# decide() integration — semantic_search (SAF-044 upgrades)
# ===========================================================================

def test_decide_semantic_search_path_traversal_deny():
    """decide(): semantic_search with path traversal -> deny."""
    data = {"tool_name": "semantic_search", "query": "../.github/config"}
    assert sg.decide(data, WS) == "deny"


def test_decide_semantic_search_absolute_deny_zone_deny():
    """decide(): semantic_search with absolute deny-zone path -> deny."""
    data = {"tool_name": "semantic_search", "query": "/workspace/.vscode/settings.json"}
    assert sg.decide(data, WS) == "deny"


def test_decide_semantic_search_general_allow():
    """decide(): semantic_search with general query -> allow."""
    data = {"tool_name": "semantic_search", "query": "module initialization code"}
    assert sg.decide(data, WS) == "allow"
