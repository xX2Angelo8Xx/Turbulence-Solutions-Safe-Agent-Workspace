"""SAF-043 — Tester edge-case tests for validate_file_search.

Additional coverage beyond the developer test suite:
- Mixed-case deny-zone variations (.GitHub, .VSCODE) not covered by developer tests
- URL-encoded traversal (%2E%2E) — documents allowed behavior (not a real traversal)
- Windows-style backslash traversal (..\\ syntax) — denied
- Empty string query — allowed
- Single wildcard-only queries (* and ?) — allowed
- Unicode characters in query (Latin extended, CJK, mixed with zone name) — allowed/denied
- .git/ directory gap: relative queries allowed (search.exclude gap), absolute denied by classify()
- Additional absolute path edge cases (system dirs, cross-drive)
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
    / "coding"
    / ".github"
    / "hooks"
    / "scripts"
)

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg       # noqa: E402
import zone_classifier as zc    # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WS = "/workspace"
WS_WIN = "c:/workspace"


# ---------------------------------------------------------------------------
# autouse fixture: stable detect_project_folder for fake workspace roots
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
# Tester group 1 — Mixed-case deny-zone variations
# ===========================================================================

class TestMixedCaseDenyZones:
    """Case variations of deny-zone names not explicitly covered by developer tests.

    The developer tested .GITHUB, .Vscode, and NOAGENTZONE.  These tests add
    the .GitHub (capital G) and .VSCODE (full uppercase) variants requested
    in the Tester specification to confirm the case-insensitive check is
    complete.
    """

    def test_deny_dot_github_mixed_case_capital_g(self):
        """.GitHub (capital G, lowercase rest) — denied (case-insensitive)."""
        data = {"query": ".GitHub/hooks/scripts/*.py"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_dot_vscode_all_uppercase(self):
        """.VSCODE (all caps) — denied (case-insensitive)."""
        data = {"query": ".VSCODE/settings.json"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_noagentzone_all_lowercase(self):
        """noagentzone (all lowercase) — denied (case-insensitive)."""
        data = {"query": "noagentzone/secret.txt"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_noagentzone_camel_case(self):
        """NoAgentZone (original camel-case, developer already tests this form).

        Included here as a baseline reference alongside the mixed-case additions.
        """
        data = {"query": "NoAgentZone/**"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_dot_github_title_case(self):
        """.Github (title case) — denied."""
        data = {"query": ".Github/**/*.json"}
        assert sg.validate_file_search(data, WS) == "deny"


# ===========================================================================
# Tester group 2 — Encoded and escaped path traversal
# ===========================================================================

class TestEncodedAndEscapedTraversal:
    """URL-encoded and backslash-based traversal variant behaviour.

    file_search query strings are file-glob patterns processed by VS Code, not
    URL-decoded by the security gate.  %2E%2E is therefore NOT interpreted as
    the dot-dot traversal sequence and is allowed by the gate.  The test
    documents this intentional design boundary.

    Windows-style backslash traversal (..\\ syntax) still contains the literal
    '..' substring and is correctly denied.
    """

    def test_allow_percent_encoded_traversal(self):
        """%2E%2E not URL-decoded — not interpreted as path traversal, allowed.

        VS Code does not URL-decode file_search glob patterns.  An agent
        submitting %2E%2E cannot reach parent directories via this encoding.
        """
        data = {"query": "%2E%2E/outside/**"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_deny_windows_backslash_traversal(self):
        r"""project\..\outside — backslash-style traversal, '..' substring present, denied."""
        data = {"query": r"project\..\outside"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_traversal_before_deny_zone(self):
        """Traversal combined with deny-zone target — denied (.. check fires first)."""
        data = {"query": "../.github/hooks/*.py"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_multiple_double_dots(self):
        """Multiple .. sequences — denied on first occurrence."""
        data = {"query": "../../../../../../etc/passwd"}
        assert sg.validate_file_search(data, WS) == "deny"


# ===========================================================================
# Tester group 3 — Empty and wildcard-only queries
# ===========================================================================

class TestEmptyAndWildcardOnlyQueries:
    """Boundary cases: empty string and single-character wildcard queries."""

    def test_allow_empty_string_query(self):
        """Empty string query — allowed (no path to block; search.exclude applies)."""
        data = {"query": ""}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_allow_single_star_wildcard(self):
        """Single * wildcard — allowed; VS Code search.exclude handles deny zones."""
        data = {"query": "*"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_allow_question_mark_wildcard(self):
        """Single ? wildcard — allowed."""
        data = {"query": "?"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_allow_wildcard_extension_only(self):
        """*.json — allowed; extension-only glob has no path prefix."""
        data = {"query": "*.json"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_allow_wildcard_no_deny_zone_name(self):
        """?.py — single-char wildcard prefix, no deny-zone name — allowed."""
        data = {"query": "?.py"}
        assert sg.validate_file_search(data, WS) == "allow"


# ===========================================================================
# Tester group 4 — Unicode in query
# ===========================================================================

class TestUnicodeInQuery:
    """Unicode characters in file_search queries.

    Non-ASCII characters have no mapping to ASCII deny-zone names; the gate's
    case-fold (query.lower()) handles only standard ASCII folding for Latin
    letters.  Queries containing accented characters, CJK, or emoji are allowed.
    Queries that contain both Unicode and a deny-zone substring are still
    denied because the substring check operates on the lowercased query.
    """

    def test_allow_unicode_latin_extended(self):
        """Query with Latin extended characters — allowed."""
        data = {"query": "src/Ünïcödé_module.py"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_allow_cjk_characters(self):
        """Query containing CJK characters — allowed."""
        data = {"query": "src/日本語ファイル.py"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_allow_emoji_in_query(self):
        """Query with emoji — allowed (no deny-zone name match)."""
        data = {"query": "src/🚀_launcher.py"}
        assert sg.validate_file_search(data, WS) == "allow"

    def test_deny_zone_name_with_unicode_prefix(self):
        """Path containing Unicode prefix AND .github component — still denied.

        The deny-zone name check is a substring search, so the .github token
        is found regardless of surrounding Unicode characters.
        """
        data = {"query": "αβγ/.github/settings.json"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_zone_name_with_unicode_suffix(self):
        """Path ending in .vscode after Unicode prefix — still denied."""
        data = {"query": "αβ/.vscode/config.json"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_allow_unicode_resembles_deny_but_differs(self):
        """'\u0067ithub' (Cyrillic lookalike) that doesn't match .github — allowed.

        The zone name check operates on the query string; Cyrillic 'г' (U+0433)
        lowercased stays Cyrillic.  The ASCII string '.github' is not a substring
        of '.гithub'.
        """
        data = {"query": ".гithub/file.py"}
        assert sg.validate_file_search(data, WS) == "allow"


# ===========================================================================
# Tester group 5 — .git/ directory gap documentation
# ===========================================================================

class TestGitDirectoryHandling:
    """Document the .git/ scoping behaviour.

    .git/ is a deny zone for file read/write tools (SAF-032) but is NOT one of
    the three named deny-zones checked by validate_file_search, nor is it
    listed in VS Code's search.exclude settings.

    Absolute .git/ paths are denied because classify() defaults to deny for
    any path that is not inside the project folder.  Relative queries (e.g.
    **/.git/**) are allowed — this is an accepted scope boundary for SAF-043
    which explicitly targets .github, .vscode, and NoAgentZone only.
    """

    def test_git_dir_absolute_path_denied(self):
        """Absolute /workspace/.git/config — denied by zone classifier default-deny.

        Although .git is not in the named deny-zone list, an absolute path to
        /workspace/.git/ does not match the project sub-folder allow rule, so
        classify() returns deny.
        """
        data = {"query": f"{WS}/.git/config"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_git_dir_relative_allowed_documents_gap(self):
        """**/.git/** relative glob — ALLOWED (scope gap, documented).

        Relative .git/ queries bypass the gate's named-zone check (only
        .github/.vscode/noagentzone are tested) and bypass the absolute-path
        zone check (prefix before first * is empty).  VS Code does not have a
        default search.exclude for .git/, so results may include .git contents.
        This is an accepted limitation of SAF-043's scope.  A follow-on WP
        should add .git to the named-zone deny list or to search.exclude.
        """
        data = {"query": "**/.git/**"}
        # Documents current behavior: allowed. Track as gap in test report.
        assert sg.validate_file_search(data, WS) == "allow"

    def test_git_config_relative_allowed_documents_gap(self):
        """.git/config relative path — allowed (same gap as above)."""
        data = {"query": ".git/config"}
        assert sg.validate_file_search(data, WS) == "allow"


# ===========================================================================
# Tester group 6 — Additional absolute path edge cases
# ===========================================================================

class TestAdditionalAbsolutePathCases:
    """Absolute path edge cases beyond the developer test set."""

    def test_deny_unix_system_bin_directory(self):
        """/usr/bin absolute path — denied (outside project folder)."""
        data = {"query": "/usr/bin/**"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_unix_home_directory(self):
        """/root or /home absolute path — denied (outside project folder)."""
        data = {"query": "/home/user/secrets.txt"}
        assert sg.validate_file_search(data, WS) == "deny"

    def test_deny_windows_absolute_github_deny_zone(self):
        """Windows absolute path targeting .github — denied."""
        data = {"query": f"{WS_WIN}/.github/**"}
        assert sg.validate_file_search(data, WS_WIN) == "deny"

    def test_allow_windows_absolute_deep_inside_project(self):
        """Windows absolute path several levels deep inside project — allowed."""
        data = {"query": f"{WS_WIN}/project/src/components/**/*.ts"}
        assert sg.validate_file_search(data, WS_WIN) == "allow"

    def test_deny_windows_different_drive(self):
        """Absolute path on a different Windows drive — denied."""
        data = {"query": "d:/secrets/**"}
        assert sg.validate_file_search(data, WS_WIN) == "deny"


# ===========================================================================
# Tester group 7 — decide() integration edge cases
# ===========================================================================

class TestDecideEdgeCases:
    """decide() integration with tester edge-case inputs."""

    def _payload(self, query: str) -> dict:
        return {"tool_name": "file_search", "tool_input": {"query": query}}

    def test_decide_empty_string_allowed(self):
        """decide() allows empty string query."""
        assert sg.decide(self._payload(""), WS) == "allow"

    def test_decide_percent_encoded_traversal_allowed(self):
        """decide() allows %2E%2E (url-encoded, not real traversal)."""
        assert sg.decide(self._payload("%2E%2E/outside/**"), WS) == "allow"

    def test_decide_dot_github_capital_g_denied(self):
        """decide() denies .GitHub (mixed case capital G)."""
        assert sg.decide(self._payload(".GitHub/**"), WS) == "deny"

    def test_decide_dot_vscode_uppercase_denied(self):
        """decide() denies .VSCODE (all caps)."""
        assert sg.decide(self._payload(".VSCODE/**"), WS) == "deny"

    def test_decide_single_star_allowed(self):
        """decide() allows bare * wildcard query."""
        assert sg.decide(self._payload("*"), WS) == "allow"

    def test_decide_unicode_allowed(self):
        """decide() allows query with unicode characters."""
        assert sg.decide(self._payload("src/日本語ファイル.py"), WS) == "allow"
