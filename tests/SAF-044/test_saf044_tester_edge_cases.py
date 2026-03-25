"""SAF-044 Tester — Edge-case tests for validate_semantic_search and validate_search_subagent.

Covers tester-identified boundary conditions not included in the Developer suite:

  validate_semantic_search (allow edge cases):
    - Percent-encoded traversal (%2e%2e) — no literal '..', not absolute → allow by design
    - Unicode natural language query → allow
    - Very long (5000-char) safe query → allow
    - Non-string (integer) query value → allow (treated as missing query)
    - Empty string query → allow

  validate_search_subagent (allow edge cases):
    - .git directory path (not .github) → allow
    - Unicode natural language query → allow
    - Very long (5000-char) safe query → allow
    - Non-string (integer) query value → allow
    - Empty string query → allow
    - Percent-encoded zone name (%2egithub) → allow [design limitation: literal check only]
    - Percent-encoded traversal (%2e%2e) → allow [design limitation: literal '..' check only]

  validate_search_subagent (deny edge cases):
    - Very long query with .github embedded mid-string → deny
    - .GITHUB in all-uppercase → deny (case-insensitive check)
    - Query that is exactly the zone name .github → deny
    - Tab character before .github in query → deny (substring still present)

  decide() edge cases:
    - search_subagent with percent-encoded zone name → allow (no literal .github)
    - search_subagent with Unicode safe query → allow

Notes:
  Percent-encoded zone names (%2egithub, %2evscode) are a known design limitation:
  the deny-zone name check uses raw literal string matching only.  The underlying
  VS Code search.exclude settings provide the real protection — the semantic index
  and search_subagent infrastructure do not surface files from excluded zones even
  when the agent queries for them by name (BUG logged separately).
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
        "templates", "agent-workbench",
        ".github", "hooks", "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

WS = "/workspace"
WS_WIN = "C:/workspace"


# ===========================================================================
# validate_semantic_search — allow edge cases
# ===========================================================================

def test_semantic_search_pct_encoded_traversal_allow():
    """validate_semantic_search: percent-encoded '..' does not trigger deny.

    '%2e%2e' contains no literal '..', and the string is not an absolute path,
    so neither defence fires.  Semantic_search is safe by design because VS Code
    search.exclude already scopes the index.
    """
    data = {"query": "%2e%2e/.github/hooks.py"}
    assert sg.validate_semantic_search(data, WS) == "allow"


def test_semantic_search_unicode_query_allow():
    """validate_semantic_search: Unicode natural language query → allow."""
    data = {"query": "найти вспомогательные функции в src"}
    assert sg.validate_semantic_search(data, WS) == "allow"


def test_semantic_search_very_long_safe_query_allow():
    """validate_semantic_search: 5000-character safe query → allow (no buffer issue)."""
    data = {"query": "utility function " * 294}  # ~5000 chars, no deny indicators
    assert sg.validate_semantic_search(data, WS) == "allow"


def test_semantic_search_non_string_query_int_allow():
    """validate_semantic_search: integer query value → allow (treated as absent query)."""
    data = {"query": 42}
    assert sg.validate_semantic_search(data, WS) == "allow"


def test_semantic_search_empty_string_query_allow():
    """validate_semantic_search: empty string query → allow (no path to evaluate)."""
    data = {"query": ""}
    assert sg.validate_semantic_search(data, WS) == "allow"


# ===========================================================================
# validate_search_subagent — allow edge cases
# ===========================================================================

def test_search_subagent_git_dir_not_github_allow():
    """.git directory path (without 'hub') is NOT a deny zone → allow."""
    data = {"query": "src/.git/COMMIT_EDITMSG"}
    assert sg.validate_search_subagent(data, WS) == "allow"


def test_search_subagent_unicode_query_allow():
    """validate_search_subagent: Unicode natural language query → allow."""
    data = {"query": "найти обработчики ошибок в проекте"}
    assert sg.validate_search_subagent(data, WS) == "allow"


def test_search_subagent_very_long_safe_query_allow():
    """validate_search_subagent: 5000-character safe query → allow."""
    data = {"query": "find tests " * 455}  # ~5000 chars, no deny indicators
    assert sg.validate_search_subagent(data, WS) == "allow"


def test_search_subagent_non_string_query_int_allow():
    """validate_search_subagent: integer query value → allow (treated as absent)."""
    data = {"query": 42}
    assert sg.validate_search_subagent(data, WS) == "allow"


def test_search_subagent_empty_string_allow():
    """validate_search_subagent: empty string query → allow."""
    data = {"query": ""}
    assert sg.validate_search_subagent(data, WS) == "allow"


def test_search_subagent_pct_encoded_zone_allow():
    """validate_search_subagent: '%2egithub/hooks.py' → allow (design limitation).

    The literal string '.github' is not present in the percent-encoded form;
    only raw string matching is performed.  VS Code search.exclude prevents any
    .github content from being returned regardless.
    See BUG logged during SAF-044 testing.
    """
    data = {"query": "%2egithub/hooks.py"}
    assert sg.validate_search_subagent(data, WS) == "allow"


def test_search_subagent_pct_encoded_traversal_allow():
    """validate_search_subagent: '%2e%2e/secrets' → allow (design limitation).

    '%2e%2e' contains no literal '..' so the traversal check does not fire.
    The path is not absolute so the zone check does not fire either.
    """
    data = {"query": "%2e%2e/secrets"}
    assert sg.validate_search_subagent(data, WS) == "allow"


# ===========================================================================
# validate_search_subagent — deny edge cases
# ===========================================================================

def test_search_subagent_very_long_query_with_github_deny():
    """validate_search_subagent: 5000-char query with .github embedded → deny."""
    payload = "find docs " * 200 + ".github" + " workflows" * 200
    data = {"query": payload}
    assert sg.validate_search_subagent(data, WS) == "deny"


def test_search_subagent_uppercase_github_deny():
    """validate_search_subagent: '.GITHUB' in all-caps → deny (case-insensitive)."""
    data = {"query": "search .GITHUB for configuration files"}
    assert sg.validate_search_subagent(data, WS) == "deny"


def test_search_subagent_exact_github_zone_name_deny():
    """validate_search_subagent: query is exactly the zone name '.github' → deny."""
    data = {"query": ".github"}
    assert sg.validate_search_subagent(data, WS) == "deny"


def test_search_subagent_tab_before_github_deny():
    """validate_search_subagent: tab character before '.github' → deny (substring present)."""
    data = {"query": "path:\t.github\thooks"}
    assert sg.validate_search_subagent(data, WS) == "deny"


# ===========================================================================
# decide() edge cases
# ===========================================================================

def test_decide_search_subagent_pct_encoded_zone_allow():
    """decide(): search_subagent with percent-encoded zone name → allow (design limitation)."""
    data = {"tool_name": "search_subagent", "query": "%2egithub/hooks.py"}
    assert sg.decide(data, WS) == "allow"


def test_decide_search_subagent_unicode_safe_allow():
    """decide(): search_subagent with Unicode safe query → allow."""
    data = {"tool_name": "search_subagent", "query": "API функции в src"}
    assert sg.decide(data, WS) == "allow"
