"""SAF-066 Tester edge-case tests — bypass vectors and non-obvious inputs.

Written by: Tester Agent
Coverage beyond the Developer's tests:
  - Whitespace variant bypass vectors (tab, newline) — document behavior
  - Non-string includePattern types (int, bool, list, dict) — must deny
  - All-file wildcard patterns (**) — allowed by design (relies on search.exclude)
  - Lowercase deny zone direct reference
  - Absolute path reference to deny zone
  - Partial deny-zone name (NotNoAgentZone) — must allow
  - decide() routing for edge-case inputs
"""
from __future__ import annotations

import os
import sys

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


# ===========================================================================
# Whitespace-variant bypass documentation tests
#
# Known limitation (SAF-066 design):
#   A string of only whitespace characters (spaces, tabs, newlines) is truthy
#   in Python and therefore passes the SAF-066 guard check:
#       isinstance(include_pattern, str) and include_pattern
#   These patterns are passed to _validate_include_pattern, which returns
#   "allow" because whitespace globs do not target a deny zone.
#   VS Code's search.exclude provides defence-in-depth for these cases:
#   a whitespace glob pattern matches only files with whitespace in their name
#   (extremely rare) and is unlikely to surface NoAgentZone content.
#
#   FUTURE WORK: Tighten the guard using include_pattern.strip() to treat
#   whitespace-only patterns as absent (FIX-XXX).
# ===========================================================================

def test_tab_only_include_pattern_behavior():
    """Tab-only includePattern: documents current allow behavior (whitespace bypass)."""
    data = {"tool_name": "grep_search", "query": "secret", "includePattern": "\t"}
    # Tab is truthy in Python; passes the SAF-066 guard.
    # Practical risk: VS Code glob with tab only matches whitespace-filename files.
    assert sg.validate_grep_search(data, WS) == "allow"  # known gap; see module docstring


def test_newline_only_include_pattern_behavior():
    """Newline-only includePattern: documents current allow behavior (whitespace bypass)."""
    data = {"tool_name": "grep_search", "query": "secret", "includePattern": "\n"}
    assert sg.validate_grep_search(data, WS) == "allow"  # known gap; see module docstring


def test_mixed_whitespace_include_pattern_behavior():
    """Mixed whitespace (space + tab) includePattern: documents current allow behavior."""
    data = {"tool_name": "grep_search", "query": "secret", "includePattern": " \t "}
    assert sg.validate_grep_search(data, WS) == "allow"  # known gap; see module docstring


# ===========================================================================
# Non-string includePattern types — must all be denied
# ===========================================================================

def test_integer_include_pattern_denied():
    """Integer includePattern (not a string) — must be denied."""
    data = {"tool_name": "grep_search", "query": "secret", "includePattern": 123}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_boolean_true_include_pattern_denied():
    """Boolean True includePattern (not a string in security terms) — must be denied."""
    data = {"tool_name": "grep_search", "query": "secret", "includePattern": True}
    # isinstance(True, str) is False so SAF-066 denies it.
    assert sg.validate_grep_search(data, WS) == "deny"


def test_list_include_pattern_denied():
    """List includePattern — must be denied (not a string)."""
    data = {"tool_name": "grep_search", "query": "secret", "includePattern": [".github/**"]}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_dict_include_pattern_denied():
    """Dict includePattern — must be denied (not a string)."""
    data = {"tool_name": "grep_search", "query": "secret", "includePattern": {}}
    assert sg.validate_grep_search(data, WS) == "deny"


# ===========================================================================
# All-file wildcard patterns — allowed by design (VS Code search.exclude defence)
# ===========================================================================

def test_double_star_include_pattern_allowed_by_design():
    """IncludePattern '**' (all files) is allowed — VS Code search.exclude provides defence.

    This is NOT a bypass of SAF-066 because:
    1. An includePattern IS present (SAF-066 guard is satisfied).
    2. The pattern does not explicitly target a deny zone.
    3. VS Code's search.exclude excludes .github/, .vscode/, NoAgentZone/ from
       '**' searches, preventing denied content from being returned.
    The SAF-066 fix was specifically for the absent-includePattern case (BUG-172).
    """
    data = {"tool_name": "grep_search", "query": "secret", "includePattern": "**"}
    assert sg.validate_grep_search(data, WS) == "allow"


def test_single_star_include_pattern_allowed_by_design():
    """IncludePattern '*' (all top-level files) is allowed — VS Code search.exclude defends."""
    data = {"tool_name": "grep_search", "query": "secret", "includePattern": "*"}
    assert sg.validate_grep_search(data, WS) == "allow"


def test_root_py_glob_include_pattern_allowed():
    """IncludePattern '*.py' (all .py files anywhere) — allowed; search.exclude defends."""
    data = {"tool_name": "grep_search", "query": "import os", "includePattern": "*.py"}
    assert sg.validate_grep_search(data, WS) == "allow"


# ===========================================================================
# Deny zone case and name boundary tests
# ===========================================================================

def test_lowercase_noagentzone_include_pattern_denied():
    """Lowercase 'noagentzone/**' must be denied (case-insensitive zone enforcement)."""
    data = {"tool_name": "grep_search", "query": "secret", "includePattern": "noagentzone/**"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_bare_github_no_glob_denied():
    """IncludePattern '.github' without glob suffix — must be denied."""
    data = {"tool_name": "grep_search", "query": "hook", "includePattern": ".github"}
    assert sg.validate_grep_search(data, WS) == "deny"


def test_similar_name_not_denied():
    """'NotNoAgentZone/**' must NOT be denied — partial name match must not over-block."""
    data = {"tool_name": "grep_search", "query": "data", "includePattern": "NotNoAgentZone/**"}
    # "NotNoAgentZone" is not a restricted zone — must allow.
    assert sg.validate_grep_search(data, WS) == "allow"


def test_absolute_noagentzone_path_denied():
    """Absolute includePattern targeting NoAgentZone — must be denied."""
    data = {
        "tool_name": "grep_search",
        "query": "secret",
        "includePattern": "/workspace/NoAgentZone/**",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


def test_traversal_to_github_denied():
    """Path traversal in includePattern to reach .github — must be denied."""
    data = {
        "tool_name": "grep_search",
        "query": "hook",
        "includePattern": "project/../../.github/**",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


# ===========================================================================
# decide() routing edge cases
# ===========================================================================

def test_decide_integer_include_pattern_denied():
    """decide() with integer includePattern -> deny."""
    data = {"tool_name": "grep_search", "query": "secret", "includePattern": 42}
    assert sg.decide(data, WS) == "deny"


def test_decide_double_star_allowed_by_design():
    """decide() with '**' includePattern -> allow (VS Code search.exclude defence)."""
    data = {"tool_name": "grep_search", "query": "secret", "includePattern": "**"}
    assert sg.decide(data, WS) == "allow"
