"""SAF-020 — Tester Edge-Case Tests

Additional edge cases added by the Tester beyond the Developer's suite.
These tests probe boundary conditions, bypass attempts, and patterns
specifically requested in the SAF-020 testing task:

  1. Double wildcards (**/*.py at root and inside safe parents)
  2. Bracket expression wildcards [.g]* — BYPASS VECTORS (tests will FAIL
     until the implementation is fixed to handle bracket expressions)
  3. Wildcard in middle of path component
  4. Backslash paths with wildcards (Windows-style)
  5. Wildcards after pipe operator (|)
  6. Empty string / bare wildcard edge cases
  7. Quoted wildcards in commands

Deny-zone names under test: .github, .vscode, noagentzone
Fixture (conftest.py): detect_project_folder returns "project" for fake WS.
"""
from __future__ import annotations

import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Path setup — resolve security_gate from its non-standard location
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_SCRIPTS_DIR = os.path.join(_REPO_ROOT, "templates", "agent-workbench", ".github", "hooks", "scripts")

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

# Fake workspace root shared by all integration tests (conftest patches
# detect_project_folder so zone_classifier returns "allow" for Project/ paths)
WS = "c:/workspace"


# ===========================================================================
# 1. Double wildcards (**  globstar)
# ===========================================================================

class TestDoubleStarWildcards:
    """Globstar (**) patterns: at root they should be denied; inside safe parent
    they are allowed by the wildcard helper (zone_classifier decides the rest).
    """

    def test_double_star_root_helper_denied(self):
        """**/*.py at root — first component ** has empty prefix → deny."""
        assert sg._wildcard_prefix_matches_deny_zone("**/*.py") is True

    def test_double_star_root_sanitize_denied(self):
        """ls **/*.py — globstar at root could enumerate deny zones → deny."""
        decision, _ = sg.sanitize_terminal_command("ls **/*.py", WS)
        assert decision == "deny"

    def test_double_star_safe_parent_helper_allowed(self):
        """Project/**/*.py — safe parent 'Project' entered before ** → helper False."""
        assert sg._wildcard_prefix_matches_deny_zone("Project/**/*.py") is False

    def test_double_star_safe_parent_sanitize_allowed(self):
        """cat Project/**/*.py — globstar inside Project/ → allowed."""
        decision, _ = sg.sanitize_terminal_command("cat Project/**/*.py", WS)
        assert decision == "allow"

    def test_bare_double_star_helper_denied(self):
        """** alone — empty prefix → deny (same as bare *)."""
        assert sg._wildcard_prefix_matches_deny_zone("**") is True


# ===========================================================================
# 2. Bracket expression wildcards [...]
#    These tests encode the EXPECTED SECURE behaviour.  The implementation
#    currently does NOT handle bracket expressions, so these tests will FAIL
#    until the developer adds bracket-expression detection.
# ===========================================================================

class TestBracketExpressionWildcards:
    """Bracket expression glob characters [...] are shell-expanded by bash,
    zsh, and PowerShell.  [.g]* matches any path whose first character is
    '.' or 'g', which includes .github and .vscode.  [Nn]* matches
    NoAgentZone.  These must be denied exactly like .g* and N*.

    EXPECTED RESULT: deny
    CURRENT RESULT: allow  ← BYPASS VECTOR — WP SAF-020 verdict: FAIL
    """

    def test_bracket_dotg_star_helper_denied(self):
        """[.g]* — bracket class matches '.' or 'g'; first match is .github.
        Expected: True (deny).  Currently returns False → bracket bypass exists.
        """
        assert sg._wildcard_prefix_matches_deny_zone("[.g]*") is True  # CURRENTLY FAILS

    def test_bracket_n_upper_lower_star_helper_denied(self):
        """[Nn]* — bracket class matches 'N' or 'n'; expands to NoAgentZone.
        Expected: True (deny).  Currently returns False → bracket bypass exists.
        """
        assert sg._wildcard_prefix_matches_deny_zone("[Nn]*") is True  # CURRENTLY FAILS

    def test_bracket_dotv_star_helper_denied(self):
        """[.v]* — bracket class can expand to .vscode.
        Expected: True (deny).  Currently returns False → bracket bypass exists.
        """
        assert sg._wildcard_prefix_matches_deny_zone("[.v]*") is True  # CURRENTLY FAILS

    def test_bracket_dotg_star_sanitize_denied(self):
        """ls [.g]* — bracket expression targeting .github must be blocked.
        Expected: deny.  Currently returns allow → active bypass vector.
        """
        decision, _ = sg.sanitize_terminal_command("ls [.g]*", WS)
        assert decision == "deny"  # CURRENTLY FAILS

    def test_bracket_n_star_via_gci_denied(self):
        """gci [Nn]* — bracket expression targeting NoAgentZone must be blocked.
        Expected: deny.  Currently returns allow → active bypass vector.
        """
        decision, _ = sg.sanitize_terminal_command("gci [Nn]*", WS)
        assert decision == "deny"  # CURRENTLY FAILS

    def test_bracket_dotv_star_via_dir_denied(self):
        """dir [.v]* — bracket expression targeting .vscode must be blocked.
        Expected: deny.  Currently returns allow → active bypass vector.
        """
        decision, _ = sg.sanitize_terminal_command("dir [.v]*", WS)
        assert decision == "deny"  # CURRENTLY FAILS


# ===========================================================================
# 3. Wildcard in middle of path
# ===========================================================================

class TestWildcardInMiddlePath:
    """Wildcards embedded midway through a multi-component path."""

    def test_dotg_star_inside_safe_parent_helper_allowed(self):
        """some/.g*/file — .g* is inside non-deny parent 'some' → helper False.
        The deny zones are only at the repository root; 'some/.g*/file' cannot
        expand to a root-level restrict zone.
        """
        assert sg._wildcard_prefix_matches_deny_zone("some/.g*/file") is False

    def test_safe_dotg_star_vs_root_dotg_star(self):
        """Contrast: root-level .g* (deny) vs. inside-parent some/.g* (not deny)."""
        assert sg._wildcard_prefix_matches_deny_zone(".g*") is True
        assert sg._wildcard_prefix_matches_deny_zone("some/.g*") is False

    def test_project_mid_wildcard_helper_allowed(self):
        """Project/src/*/utils.py — wildcard inside safe Project/ path → False."""
        assert sg._wildcard_prefix_matches_deny_zone("Project/src/*/utils.py") is False

    def test_project_mid_wildcard_sanitize_allowed(self):
        """cat Project/src/*/utils.py → allowed (safe parent Project/)."""
        decision, _ = sg.sanitize_terminal_command("cat Project/src/*/utils.py", WS)
        assert decision == "allow"


# ===========================================================================
# 4. Backslash paths with wildcards (Windows-style)
# ===========================================================================

class TestBackslashWindowsPaths:
    """The helper normalizes backslashes to forward slashes before checking.
    Windows-style wildcard paths must be caught the same as POSIX ones.
    """

    def test_backslash_dotg_star_denied(self):
        """.g*\\file — normalized to .g*/file; prefix .g matches .github → deny."""
        assert sg._wildcard_prefix_matches_deny_zone(".g*\\file") is True

    def test_backslash_n_star_subdir_denied(self):
        """N*\\subdir — normalized to N*/subdir; prefix n matches noagentzone → deny."""
        assert sg._wildcard_prefix_matches_deny_zone("N*\\subdir") is True

    def test_backslash_dotv_star_denied(self):
        """.v*\\settings.json — normalized; prefix .v matches .vscode → deny."""
        assert sg._wildcard_prefix_matches_deny_zone(".v*\\settings.json") is True

    def test_backslash_project_star_allowed(self):
        """Project\\*.py — safe parent Project on Windows → helper False."""
        assert sg._wildcard_prefix_matches_deny_zone("Project\\*.py") is False

    def test_backslash_dotg_star_sanitize_denied(self):
        """ls .g*\\file — Windows wildcard path denied via sanitizer."""
        decision, _ = sg.sanitize_terminal_command("ls .g*\\file", WS)
        assert decision == "deny"

    def test_backslash_n_star_sanitize_denied(self):
        """dir N*\\file — Windows wildcard targeting noagentzone denied."""
        decision, _ = sg.sanitize_terminal_command("dir N*\\file", WS)
        assert decision == "deny"


# ===========================================================================
# 5. Wildcards after pipe operator (|)
# ===========================================================================

class TestWildcardsAfterPipe:
    """The sanitizer does not split on the single pipe '|', so the entire
    command is one segment with the first verb.  Wildcard tokens that appear
    after '|' are still processed as arguments of the first command; if the
    first command has path_args_restricted=True the wildcard check fires.
    """

    def test_pipe_n_star_denied_via_ls(self):
        """ls | cat N* — N* is treated as ls arg; ls is path-restricted → deny."""
        decision, _ = sg.sanitize_terminal_command("ls | cat N*", WS)
        assert decision == "deny"

    def test_pipe_dotg_star_denied_via_cat(self):
        """cat file.txt | cat .g* — .g* caught as cat arg; cat is path-restricted → deny."""
        decision, _ = sg.sanitize_terminal_command("cat file.txt | cat .g*", WS)
        assert decision == "deny"

    def test_pipe_dotv_star_denied_via_dir(self):
        """dir . | cat .v* — .v* treated as dir arg; dir is path-restricted → deny."""
        decision, _ = sg.sanitize_terminal_command("dir . | cat .v*", WS)
        assert decision == "deny"

    def test_pipe_bracket_dotg_still_caught_by_ls(self):
        """ls | cat [.g]* — ls is path-restricted; [.g]* has '*' and IS caught by
        the wildcard check; however the bracket prefix '[.g]' is not recognized as
        a deny-zone prefix, so this currently returns allow.
        This test documents the combined pipe + bracket bypass.
        Expected: deny.  Currently: allow → BYPASS.
        """
        decision, _ = sg.sanitize_terminal_command("ls | cat [.g]*", WS)
        assert decision == "deny"  # CURRENTLY FAILS


# ===========================================================================
# 6. Empty string and bare wildcard edge cases
# ===========================================================================

class TestEmptyAndBareWildcards:
    """Boundary conditions for zero-length and single-character wildcards."""

    def test_empty_token_no_wildcard(self):
        """Empty string — no wildcard characters → helper returns False."""
        assert sg._wildcard_prefix_matches_deny_zone("") is False

    def test_bare_star_denied(self):
        """* alone — empty prefix before * matches every deny zone → deny."""
        assert sg._wildcard_prefix_matches_deny_zone("*") is True

    def test_bare_question_denied(self):
        """? alone — empty prefix before ? matches every deny zone → deny."""
        assert sg._wildcard_prefix_matches_deny_zone("?") is True

    def test_bare_star_sanitize_denied(self):
        """ls * — bare star must be blocked."""
        decision, _ = sg.sanitize_terminal_command("ls *", WS)
        assert decision == "deny"

    def test_bare_question_sanitize_denied(self):
        """ls ? — bare question mark must be blocked."""
        decision, _ = sg.sanitize_terminal_command("ls ?", WS)
        assert decision == "deny"

    def test_only_slashes_no_wildcard(self):
        """/ alone — path separator, no wildcard → helper returns False."""
        assert sg._wildcard_prefix_matches_deny_zone("/") is False

    def test_star_plus_extension_at_root_denied(self):
        """*.txt at root — empty prefix, conservative deny (could match .github)."""
        assert sg._wildcard_prefix_matches_deny_zone("*.txt") is True


# ===========================================================================
# 7. Quoted wildcards in commands
# ===========================================================================

class TestQuotedWildcards:
    """The wildcard check runs on the shlex-tokenized form of the command.
    Both single and double quotes are stripped before the check; quoted
    wildcards must be caught the same as unquoted ones.
    """

    def test_single_quoted_dotg_star_denied(self):
        """ls '.g*' — single quotes stripped by shlex; .g* still denied."""
        decision, _ = sg.sanitize_terminal_command("ls '.g*'", WS)
        assert decision == "deny"

    def test_double_quoted_n_star_denied(self):
        """cat \"N*\" — double quotes stripped; N* wildcard denied."""
        decision, _ = sg.sanitize_terminal_command('cat "N*"', WS)
        assert decision == "deny"

    def test_double_quoted_dotv_star_denied(self):
        """gci \".v*\" — double-quoted .v* targeting .vscode must be denied."""
        decision, _ = sg.sanitize_terminal_command('gci ".v*"', WS)
        assert decision == "deny"

    def test_single_quoted_project_star_allowed(self):
        """ls 'Project/*.py' — single-quoted safe wildcard → allowed after quotedstripping."""
        decision, _ = sg.sanitize_terminal_command("ls 'Project/*.py'", WS)
        assert decision == "allow"

    def test_double_quoted_project_star_allowed(self):
        """cat \"Project/*.py\" — double-quoted safe wildcard → allowed."""
        decision, _ = sg.sanitize_terminal_command('cat "Project/*.py"', WS)
        assert decision == "allow"

    def test_mixed_quoted_dotg_star_via_gci_denied(self):
        """Get-ChildItem '.g*' — quoted .g* targeting .github → denied."""
        decision, _ = sg.sanitize_terminal_command("Get-ChildItem '.g*'", WS)
        assert decision == "deny"
