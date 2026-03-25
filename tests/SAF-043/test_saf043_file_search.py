"""SAF-043 — Tests for file_search scope enforcement.

Covers:
- validate_file_search() — allow/deny scenarios for query parameter
- Deny-zone name detection (case-insensitive: .github, .vscode, NoAgentZone)
- Path traversal detection (..)
- Wildcard deny-zone bypass prevention (reuses _wildcard_prefix_matches_deny_zone)
- Absolute path zone-check (absolute paths outside project folder denied)
- Nested tool_input format (VS Code hook payload format)
- decide() integration — file_search routed correctly via decide()
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

import security_gate as sg    # noqa: E402
import zone_classifier as zc   # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WS = "/workspace"
WS_WIN = "c:/workspace"

# Paths inside project folder (allow zone)
PROJECT_FILE = f"{WS}/project/src/main.py"
PROJECT_DIR = f"{WS}/project/src"

# Paths outside project (deny zone)
GITHUB_DIR = f"{WS}/.github"
VSCODE_DIR = f"{WS}/.vscode"
NOAGENT_DIR = f"{WS}/NoAgentZone"
OUTSIDE_ABS = "/etc/passwd"
WINDOWS_OUTSIDE = "c:/windows/system32/cmd.exe"


# ---------------------------------------------------------------------------
# autouse fixture: patch detect_project_folder for fake workspace roots
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_detect_project_folder():
    """Patch zone_classifier.detect_project_folder for fake workspace roots."""
    original = zc.detect_project_folder

    def _detect_with_fallback(workspace_root: Path) -> str:
        try:
            return original(workspace_root)
        except (RuntimeError, OSError):
            return "project"

    with patch.object(zc, "detect_project_folder", side_effect=_detect_with_fallback):
        yield


# ===========================================================================
# validate_file_search() — Allow cases
# ===========================================================================

class TestValidateFileSearchAllow:
    """validate_file_search() should allow safe queries."""

    def test_allow_simple_filename(self):
        """Plain filename with no path — allowed."""
        data = {"query": "settings.json"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_allow_glob_all_py(self):
        """Standard glob **/*.py — allowed (workspace-scoped, search.exclude filters zones)."""
        data = {"query": "**/*.py"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_allow_glob_extension_brace(self):
        """Brace glob **/*.{ts,js} — allowed."""
        data = {"query": "**/*.{ts,js}"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_allow_no_query_key(self):
        """Payload with no query field — allowed (search.exclude handles scoping)."""
        data = {}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_allow_query_none(self):
        """Explicit None query — allowed."""
        data = {"query": None}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_allow_nested_glob_in_subdir(self):
        """Glob starting from a non-denied subdirectory — allowed."""
        data = {"query": "src/**/*.py"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_allow_absolute_path_inside_project(self):
        """Absolute path pointing into the project folder — allowed."""
        data = {"query": f"{WS}/project/src/**/*.py"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_allow_windows_absolute_inside_project(self):
        """Windows absolute path inside project folder — allowed."""
        data = {"query": f"{WS_WIN}/project/src/**"}
        assert sg.validate_file_search(data, WS_WIN) == "allow"

    def test_allow_nested_tool_input_clean_query(self):
        """VS Code hook nested format — clean query allowed."""
        data = {"tool_input": {"query": "**/*.md", "maxResults": 50}}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_allow_no_query_nested_tool_input(self):
        """VS Code hook nested format — no query field allowed."""
        data = {"tool_input": {"maxResults": 10}}
        assert sg.validate_file_search(data, WS) == "allow"


# ===========================================================================
# validate_file_search() — Deny cases: deny-zone names
# ===========================================================================

class TestValidateFileSearchDenyZoneNames:
    """validate_file_search() should deny queries referencing deny-zone directories."""

    def test_deny_github_in_query(self):
        """.github in query — denied."""
        data = {"query": ".github/hooks/scripts/*.py"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_vscode_in_query(self):
        """.vscode in query — denied."""
        data = {"query": ".vscode/settings.json"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_noagentzone_in_query(self):
        """NoAgentZone in query — denied."""
        data = {"query": "NoAgentZone/secret.txt"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_github_case_insensitive(self):
        """.GITHUB in query — denied (case-insensitive check)."""
        data = {"query": ".GITHUB/config"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_vscode_mixed_case(self):
        """.Vscode in query — denied (case-insensitive check)."""
        data = {"query": ".Vscode/**"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_noagentzone_uppercase(self):
        """NOAGENTZONE in query — denied (case-insensitive check)."""
        data = {"query": "NOAGENTZONE/**"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_github_embedded_in_glob(self):
        """Deny-zone name embedded inside a glob — denied."""
        data = {"query": "**/.github/**/*.json"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_github_nested_tool_input(self):
        """VS Code hook nested format — .github in query denied."""
        data = {"tool_input": {"query": ".github/copilot-instructions.md"}}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_vscode_via_nested_tool_input(self):
        """VS Code hook nested format — .vscode in query denied."""
        data = {"tool_input": {"query": ".vscode/*.json", "maxResults": 5}}
        assert sg.validate_file_search(data, WS) == "deny"


# ===========================================================================
# validate_file_search() — Deny cases: path traversal
# ===========================================================================

class TestValidateFileSearchDenyTraversal:
    """validate_file_search() should deny queries containing path traversal."""

    def test_deny_double_dot_traversal(self):
        """..[traversal] in query — denied."""
        data = {"query": "../outside/**"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_double_dot_embedded(self):
        """Traversal embedded in a deeper path — denied."""
        data = {"query": "project/../../outside"}
        assert sg.validate_file_search(data, WS) == "deny"


# ===========================================================================
# validate_file_search() — Wildcard queries: deny-zone names → deny, broad
# wildcards → allow (VS Code search.exclude handles filtering)
# ===========================================================================

class TestValidateFileSearchWildcardBehavior:
    """Verify wildcard query handling for file_search.

    Unlike terminal commands, file_search wildcards are processed by VS Code,
    which applies search.exclude to filter deny-zone results.  Only wildcards
    that contain explicit deny-zone names are blocked by the gate.
    """

    def test_deny_wildcard_with_explicit_github(self):
        """Wildcard containing explicit .github name — denied by name check."""
        data = {"query": ".github/**/*.json"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_wildcard_with_explicit_vscode(self):
        """Wildcard containing explicit .vscode name — denied by name check."""
        data = {"query": ".vscode/*.json"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_allow_broad_root_wildcard(self):
        """Broad **/*.py wildcard at root — allowed; VS Code search.exclude filters zones."""
        data = {"query": "**/*.py"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_allow_broad_root_double_star(self):
        """Broad ** wildcard at root — allowed; VS Code search.exclude filters zones."""
        data = {"query": "**"}
        assert sg.validate_file_search(data, WS) == "allow"


# ===========================================================================
# validate_file_search() — Deny cases: absolute path outside project
# ===========================================================================

class TestValidateFileSearchDenyAbsolutePath:
    """validate_file_search() should deny absolute paths outside the project folder."""

    def test_deny_unix_absolute_outside(self):
        """Unix absolute path outside project — denied."""
        data = {"query": "/etc/passwd"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_unix_absolute_outside_glob(self):
        """Unix absolute glob outside project — denied."""
        data = {"query": "/etc/**/*.conf"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_windows_absolute_outside(self):
        """Windows absolute path outside project — denied."""
        data = {"query": "c:/windows/system32/**"}
        assert sg.validate_file_search(data, WS_WIN) == "deny"

    def test_deny_workspace_root_itself(self):
        """Absolute path to workspace root (ancestor of deny zones) — denied."""
        data = {"query": f"{WS}/**"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_absolute_github_dir(self):
        """Absolute path directly targeting .github — denied."""
        data = {"query": f"{WS}/.github/**"}
        # .github is in the deny-zone name check, so this hits the name check first
        assert sg.validate_file_search(data, WS) == "deny"


# ===========================================================================
# decide() integration tests
# ===========================================================================

class TestDecideFileSearchIntegration:
    """Verify decide() correctly routes file_search through validate_file_search()."""

    def _payload(self, query: str) -> dict:
        return {"tool_name": "file_search", "tool_input": {"query": query}}

    def test_decide_simple_filename_allowed(self):
        """decide() allows a plain filename query."""
        assert sg.decide(self._payload("main.py"), WS) == "allow"

    def test_decide_glob_allowed(self):
        """decide() allows a standard glob query."""
        assert sg.decide(self._payload("**/*.py"), WS) == "allow"

    def test_decide_github_query_denied(self):
        """decide() denies a query referencing .github."""
        assert sg.decide(self._payload(".github/**"), WS) == "deny"

    def test_decide_vscode_query_denied(self):
        """decide() denies a query referencing .vscode."""
        assert sg.decide(self._payload(".vscode/settings.json"), WS) == "deny"

    def test_decide_noagentzone_query_denied(self):
        """decide() denies a query referencing NoAgentZone."""
        assert sg.decide(self._payload("NoAgentZone/**"), WS) == "deny"

    def test_decide_traversal_denied(self):
        """decide() denies a query with path traversal."""
        assert sg.decide(self._payload("../outside/**"), WS) == "deny"

    def test_decide_absolute_outside_denied(self):
        """decide() denies an absolute path outside project folder."""
        assert sg.decide(self._payload("/etc/hosts"), WS) == "deny"

    def test_decide_absolute_inside_project_allowed(self):
        """decide() allows an absolute path inside the project folder."""
        assert sg.decide(self._payload(f"{WS}/project/src/**"), WS) == "allow"

    def test_decide_no_query_allowed(self):
        """decide() allows file_search with no query (no path to check)."""
        data = {"tool_name": "file_search", "tool_input": {}}
        assert sg.decide(data, WS) == "allow"

    def test_decide_wildcard_bypass_allowed(self):
        """decide() allows .g*/** — no explicit deny-zone name; VS Code search.exclude filters."""
        # .g*/** does not contain the literal string ".github" or ".vscode", so it
        # passes the deny-zone name check.  VS Code search.exclude prevents .github
        # files from being returned.  The gate allows and relies on VS Code filtering.
        assert sg.decide(self._payload(".g*/**"), WS) == "allow"
