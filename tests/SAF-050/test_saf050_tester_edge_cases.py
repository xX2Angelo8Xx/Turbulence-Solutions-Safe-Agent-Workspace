"""SAF-050 Tester edge-case tests.

These tests cover scenarios the Developer missed:

1. Deny zones nested inside the agent's project folder must be ALLOWED via
   a grep_search includePattern because the concrete path prefix (e.g. "project")
   scopes the pattern to the agent's own work area — NOT the workspace-root
   deny zone.

2. Wildcard-prefixed deny zone references (e.g. ``**/.github/**``) must be DENIED
   because the wildcard expands to zero or more path segments, meaning it CAN
   match the workspace-root deny zone.

3. ``search.exclude`` provides defence-in-depth for no-includePattern calls.

The regression fixed by SAF-050 introduced a NEW regression: the
``_include_pattern_targets_deny_zone`` helper uses ``any()`` over ALL path
components, which blocks ``project/.github/**`` (allow-case) the same as
``.github/**`` (deny-case). The fix should only deny when the deny zone
component is reachable at the workspace-root level, i.e. when no concrete
(non-wildcard, non-deny-zone) directory name precedes it.

Failing tests in this file document required Developer fixes.
"""
from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

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

WS = "c:/workspace"


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# ===========================================================================
# Regression: deny-zone nested inside concrete project prefix must be ALLOWED
# ===========================================================================

def test_edge_project_github_nested_allow():
    """includePattern 'project/.github/**' must be ALLOWED.

    'project' is the agent's project folder.  A .github/ inside it is under
    the agent's control and is NOT the workspace-root .github/ deny zone.
    The ONLY path that must be denied is .github at the workspace root.

    This test is EXPECTED TO FAIL with the current implementation (regression
    introduced by SAF-050 — see test-report.md).
    """
    data = {
        "tool_name": "grep_search",
        "query": "workflow",
        "includePattern": "project/.github/**",
    }
    assert sg.validate_grep_search(data, WS) == "allow"


def test_edge_project_vscode_nested_allow():
    """includePattern 'project/.vscode/**' must be ALLOWED.

    .vscode inside the project folder is the agent's own VS Code settings —
    NOT the workspace-root .vscode/ deny zone.

    This test is EXPECTED TO FAIL with the current implementation (regression
    introduced by SAF-050 — see test-report.md).
    """
    data = {
        "tool_name": "grep_search",
        "query": "linter",
        "includePattern": "project/.vscode/**",
    }
    assert sg.validate_grep_search(data, WS) == "allow"


def test_edge_project_noagentzone_nested_allow():
    """includePattern 'project/NoAgentZone/**' must be ALLOWED.

    A NoAgentZone/ directory created inside the project folder is inside the
    agent's work area.  The deny zone protection covers only workspace-root
    NoAgentZone/, not a sub-folder the agent created.

    This test is EXPECTED TO FAIL with the current implementation (regression
    introduced by SAF-050 — see test-report.md).
    """
    data = {
        "tool_name": "grep_search",
        "query": "docs",
        "includePattern": "project/NoAgentZone/**",
    }
    assert sg.validate_grep_search(data, WS) == "allow"


def test_edge_deep_concrete_prefix_vscode_allow():
    """includePattern 'project/src/.vscode/**' must be ALLOWED.

    Multiple concrete path components before the deny-zone name still scope
    the pattern inside the project folder.

    This test is EXPECTED TO FAIL with the current implementation (regression
    introduced by SAF-050 — see test-report.md).
    """
    data = {
        "tool_name": "grep_search",
        "query": "config",
        "includePattern": "project/src/.vscode/**",
    }
    assert sg.validate_grep_search(data, WS) == "allow"


# ===========================================================================
# Bypass guard: wildcard prefix before deny zone must still be DENIED
# ===========================================================================

def test_edge_double_star_github_deny():
    """includePattern '**/.github/**' must be DENIED.

    '**' expands to ZERO or more path segments, so '**/.github/**' matches
    '.github/**' at the workspace root.  The security gate must deny this.
    """
    data = {
        "tool_name": "grep_search",
        "query": "hook",
        "includePattern": "**/.github/**",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


def test_edge_double_star_vscode_deny():
    """includePattern '**/.vscode/**' must be DENIED.

    Same reasoning as '**/.github/**' — a leading '**' means the workspace-root
    .vscode/ is reachable.
    """
    data = {
        "tool_name": "grep_search",
        "query": "settings",
        "includePattern": "**/.vscode/**",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


def test_edge_double_star_noagentzone_deny():
    """includePattern '**/NoAgentZone/**' must be DENIED.

    'NoAgentZone' behind a '**' can resolve to the workspace-root deny zone.
    """
    data = {
        "tool_name": "grep_search",
        "query": "secret",
        "includePattern": "**/NoAgentZone/**",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


def test_edge_single_star_github_deny():
    """includePattern '*/.github/**' must be DENIED.

    '*' matches any single path component, so '*/.github/**' matches
    '<anydirectory>/.github/**' — including any top-level folder that might
    sit beside .github at the workspace root (and the '*' could match the
    string '.github' itself on case-insensitive filesystems).
    Deny conservatively.
    """
    data = {
        "tool_name": "grep_search",
        "query": "token",
        "includePattern": "*/.github/**",
    }
    # Conservative: single wildcard before deny zone should also be denied
    # because '*' could match ANY directory, exposing the deny zone indirectly.
    assert sg.validate_grep_search(data, WS) == "deny"
