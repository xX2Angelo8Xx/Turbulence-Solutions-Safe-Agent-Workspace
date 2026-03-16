"""SAF-020 — Tests for Detect and Block Terminal Wildcard Patterns

Covers:
  - Unit tests for _wildcard_prefix_matches_deny_zone helper
  - Integration tests via sanitize_terminal_command (key audit scenarios)
  - Wildcard bypass attempt scenarios
  - Allowed wildcard paths (inside safe parent directories)
  - Mirror test: both security_gate.py copies have the same wildcard behavior

Deny zones under test: .github, .vscode, noagentzone
"""
from __future__ import annotations

import importlib.util
import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Make security_gate importable from its non-standard location
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
_SCRIPTS_DIR = os.path.join(
    _REPO_ROOT, "Default-Project", ".github", "hooks", "scripts"
)
_TEMPLATES_SCRIPTS_DIR = os.path.join(
    _REPO_ROOT, "templates", "coding", ".github", "hooks", "scripts"
)

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

# Fake workspace root shared by all integration tests
WS = "c:/workspace"


# ===========================================================================
# Unit tests — _wildcard_prefix_matches_deny_zone
# ===========================================================================

class TestWildcardPrefixMatchesDenyZone:
    """Unit tests for the SAF-020 wildcard helper (no zone classifier needed)."""

    # --- Deny cases ---

    def test_dotg_star_denied(self):
        """.g* prefix '.g' matches '.github'."""
        assert sg._wildcard_prefix_matches_deny_zone(".g*") is True

    def test_capital_n_star_denied(self):
        """N* is normalized to 'n', which matches 'noagentzone'."""
        assert sg._wildcard_prefix_matches_deny_zone("N*") is True

    def test_lowercase_n_star_denied(self):
        """n* prefix 'n' matches 'noagentzone'."""
        assert sg._wildcard_prefix_matches_deny_zone("n*") is True

    def test_dotv_star_denied(self):
        """.v* prefix '.v' matches '.vscode'."""
        assert sg._wildcard_prefix_matches_deny_zone(".v*") is True

    def test_dot_star_denied(self):
        """.* prefix '.' matches both '.github' and '.vscode'."""
        assert sg._wildcard_prefix_matches_deny_zone(".*") is True

    def test_bare_star_denied(self):
        """* with empty prefix matches every deny zone (conservative)."""
        assert sg._wildcard_prefix_matches_deny_zone("*") is True

    def test_noagent_star_denied(self):
        """NoAgent* (lowercased prefix 'noagent') matches 'noagentzone'."""
        assert sg._wildcard_prefix_matches_deny_zone("NoAgent*") is True

    def test_dotgithub_subpath_star_denied(self):
        """.github/* — parent IS .github (explicit deny zone) → deny."""
        assert sg._wildcard_prefix_matches_deny_zone(".github/*") is True

    def test_noagentzone_subpath_star_denied(self):
        """NoAgentZone/* — parent is deny zone → deny."""
        assert sg._wildcard_prefix_matches_deny_zone("NoAgentZone/*") is True

    def test_question_mark_github_denied(self):
        """.githu? — prefix '.githu' matches '.github'."""
        assert sg._wildcard_prefix_matches_deny_zone(".githu?") is True

    def test_question_mark_noagentzone_denied(self):
        """NoAgentZon? — prefix 'noagentzon' matches 'noagentzone'."""
        assert sg._wildcard_prefix_matches_deny_zone("NoAgentZon?") is True

    def test_question_mark_vscode_denied(self):
        """.vscod? — prefix '.vscod' matches '.vscode'."""
        assert sg._wildcard_prefix_matches_deny_zone(".vscod?") is True

    def test_mixed_wildcards_dotg_first_denied(self):
        """.g*t?ub — first wildcard at index 2, prefix '.g' → deny."""
        assert sg._wildcard_prefix_matches_deny_zone(".g*t?ub") is True

    def test_dotg_question_mark_denied(self):
        """.g?thub — prefix '.g' matches '.github'."""
        assert sg._wildcard_prefix_matches_deny_zone(".g?thub") is True

    def test_dotgithub_hooks_star_denied(self):
        """.github/hooks/* — first component is .github → deny immediately."""
        assert sg._wildcard_prefix_matches_deny_zone(".github/hooks/*") is True

    def test_noagentzone_readme_star_denied(self):
        """NoAgentZone/READ* — parent is deny zone → deny."""
        assert sg._wildcard_prefix_matches_deny_zone("NoAgentZone/READ*") is True

    # --- Allow cases ---

    def test_project_wildcard_allowed(self):
        """Project/*.py — safe parent 'project' → wildcard is inside safe dir."""
        assert sg._wildcard_prefix_matches_deny_zone("Project/*.py") is False

    def test_project_deep_wildcard_allowed(self):
        """Project/src/*.py — wildcard inside nested safe dir → allow."""
        assert sg._wildcard_prefix_matches_deny_zone("Project/src/*.py") is False

    def test_no_wildcard_returns_false(self):
        """No wildcard characters → always False (no-op)."""
        assert sg._wildcard_prefix_matches_deny_zone("Project/main.py") is False

    def test_no_wildcard_deny_path_returns_false(self):
        """.github/hooks/security_gate.py has no wildcard → False."""
        assert sg._wildcard_prefix_matches_deny_zone(".github/hooks/security_gate.py") is False

    def test_z_star_safe(self):
        """z* prefix 'z' doesn't match any deny zone → False."""
        assert sg._wildcard_prefix_matches_deny_zone("z*") is False

    def test_github_star_safe(self):
        """github* (no leading dot) prefix 'github' doesn't match → False."""
        assert sg._wildcard_prefix_matches_deny_zone("github*") is False

    def test_abc_star_safe(self):
        """abc* → safe prefix, no deny zone starts with 'abc'."""
        assert sg._wildcard_prefix_matches_deny_zone("abc*") is False

    def test_src_wildcard_allowed(self):
        """src/*.py — safe parent 'src' → allow."""
        assert sg._wildcard_prefix_matches_deny_zone("src/*.py") is False

    def test_tests_wildcard_allowed(self):
        """tests/*.py — safe parent 'tests' → allow."""
        assert sg._wildcard_prefix_matches_deny_zone("tests/*.py") is False

    def test_dotdot_safe_parent_wildcard_allowed(self):
        """../Project/*.py — '..' is transparent; 'project' is safe parent → allow."""
        assert sg._wildcard_prefix_matches_deny_zone("../Project/*.py") is False


# ===========================================================================
# Integration tests — sanitize_terminal_command (key audit scenarios)
# ===========================================================================

class TestWildcardBlockingInSanitize:
    """Key scenarios from the security audit: exact commands listed in the WP."""

    def test_get_childitem_dotg_star_denied(self):
        """Get-ChildItem .g* → blocked (matches .github)."""
        decision, reason = sg.sanitize_terminal_command("Get-ChildItem .g*", WS)
        assert decision == "deny"
        assert reason is not None

    def test_get_childitem_n_star_denied(self):
        """Get-ChildItem N* → blocked (matches NoAgentZone)."""
        decision, reason = sg.sanitize_terminal_command("Get-ChildItem N*", WS)
        assert decision == "deny"

    def test_get_childitem_dotv_star_denied(self):
        """Get-ChildItem .v* → blocked (matches .vscode)."""
        decision, reason = sg.sanitize_terminal_command("Get-ChildItem .v*", WS)
        assert decision == "deny"

    def test_ls_dotg_star_denied(self):
        """ls .g* → blocked."""
        decision, reason = sg.sanitize_terminal_command("ls .g*", WS)
        assert decision == "deny"

    def test_cat_n_star_slash_denied(self):
        """cat N*/* → blocked (N* prefix matches noagentzone)."""
        decision, reason = sg.sanitize_terminal_command("cat N*/*", WS)
        assert decision == "deny"

    def test_dir_dotg_star_denied(self):
        """dir .g* → blocked."""
        decision, reason = sg.sanitize_terminal_command("dir .g*", WS)
        assert decision == "deny"

    def test_ls_dotstar_denied(self):
        """ls .* → blocked (prefix '.' matches .github and .vscode)."""
        decision, reason = sg.sanitize_terminal_command("ls .*", WS)
        assert decision == "deny"

    def test_ls_bare_star_denied(self):
        """ls * → blocked (empty prefix is conservative deny)."""
        decision, reason = sg.sanitize_terminal_command("ls *", WS)
        assert decision == "deny"

    def test_gci_dotg_star_denied(self):
        """gci .g* (alias for Get-ChildItem) → blocked."""
        decision, reason = sg.sanitize_terminal_command("gci .g*", WS)
        assert decision == "deny"

    def test_get_content_dotg_star_denied(self):
        """Get-Content .g* → blocked."""
        decision, reason = sg.sanitize_terminal_command("Get-Content .g*", WS)
        assert decision == "deny"

    def test_project_py_allowed(self):
        """ls Project/*.py → allowed (wildcard inside safe project parent)."""
        decision, _ = sg.sanitize_terminal_command("ls Project/*.py", WS)
        assert decision == "allow"

    def test_project_app_star_allowed(self):
        """cat Project/app.* → allowed."""
        decision, _ = sg.sanitize_terminal_command("cat Project/app.*", WS)
        assert decision == "allow"

    def test_project_deep_wildcard_allowed(self):
        """ls Project/src/*.py → allowed."""
        decision, _ = sg.sanitize_terminal_command("ls Project/src/*.py", WS)
        assert decision == "allow"

    def test_no_wildcard_ls_project_allowed(self):
        """ls Project/ (no wildcard) → unaffected, allowed."""
        decision, _ = sg.sanitize_terminal_command("ls Project/", WS)
        assert decision == "allow"

    def test_no_wildcard_echo_allowed(self):
        """echo hello → unaffected by wildcard check."""
        decision, _ = sg.sanitize_terminal_command("echo hello", WS)
        assert decision == "allow"

    def test_deny_reason_contains_blocked(self):
        """Deny decision must include a human-readable reason with 'BLOCKED'."""
        _, reason = sg.sanitize_terminal_command("Get-ChildItem .g*", WS)
        assert reason is not None
        assert "BLOCKED" in reason


# ===========================================================================
# Wildcard bypass attempts
# ===========================================================================

class TestWildcardBypassAttempts:
    """Explicit bypass scenarios that must be caught by the wildcard guard."""

    def test_question_mark_github(self):
        """.githu? — ? expands to 'b', covering .github."""
        decision, _ = sg.sanitize_terminal_command("ls .githu?", WS)
        assert decision == "deny"

    def test_question_mark_vscode(self):
        """.vscod? — ? expands to 'e', covering .vscode."""
        decision, _ = sg.sanitize_terminal_command("ls .vscod?", WS)
        assert decision == "deny"

    def test_question_mark_noagentzone(self):
        """NoAgentZon? — ? expands to 'e', covering NoAgentZone."""
        decision, _ = sg.sanitize_terminal_command("cat NoAgentZon?", WS)
        assert decision == "deny"

    def test_multiple_wildcards_deny_prefix_first(self):
        """.g*/hooks/*.py — first wildcard component has deny-zone prefix."""
        decision, _ = sg.sanitize_terminal_command("cat .g*/hooks/*.py", WS)
        assert decision == "deny"

    def test_dotgithub_explicit_star(self):
        """.github/* — parent is explicit deny zone."""
        decision, _ = sg.sanitize_terminal_command("ls .github/*", WS)
        assert decision == "deny"

    def test_noagentzone_explicit_star(self):
        """NoAgentZone/* — parent is explicit deny zone."""
        decision, _ = sg.sanitize_terminal_command("ls NoAgentZone/*", WS)
        assert decision == "deny"

    def test_noagent_star_mixed(self):
        """NoAgent* → denied."""
        decision, _ = sg.sanitize_terminal_command("ls NoAgent*", WS)
        assert decision == "deny"

    def test_dotg_question_star(self):
        """.g?thub — first wildcard is ?, prefix '.g' → deny."""
        decision, _ = sg.sanitize_terminal_command("cat .g?thub", WS)
        assert decision == "deny"

    def test_dotv_star_via_cat(self):
        """cat .v* → denied (matches .vscode)."""
        decision, _ = sg.sanitize_terminal_command("cat .v*", WS)
        assert decision == "deny"

    def test_path_traversal_then_wildcard_denied(self):
        """../../.g* — '..' components are transparent, '.g' still matches."""
        decision, _ = sg.sanitize_terminal_command("ls ../../.g*", WS)
        assert decision == "deny"

    def test_star_py_at_root_denied(self):
        """*.py — empty prefix before '*' matches every deny zone."""
        decision, _ = sg.sanitize_terminal_command("ls *.py", WS)
        assert decision == "deny"

    def test_dotgithub_wildcard_get_childitem(self):
        """Get-ChildItem .githu? → denied via question-mark wildcard."""
        decision, _ = sg.sanitize_terminal_command("Get-ChildItem .githu?", WS)
        assert decision == "deny"

    def test_mixed_case_dotg_star(self):
        """.G* — uppercased, still normalized to .g, matches .github."""
        decision, _ = sg.sanitize_terminal_command("ls .G*", WS)
        assert decision == "deny"

    def test_noagentzone_n_star_via_dir(self):
        """dir N* → denied."""
        decision, _ = sg.sanitize_terminal_command("dir N*", WS)
        assert decision == "deny"


# ===========================================================================
# Allowed wildcard paths — inside safe parent directories
# ===========================================================================

class TestWildcardAllowedPaths:
    """Wildcards nested inside non-deny parent directories must be allowed."""

    def test_project_py_files(self):
        """ls Project/*.py → allowed."""
        decision, _ = sg.sanitize_terminal_command("ls Project/*.py", WS)
        assert decision == "allow"

    def test_project_app_star(self):
        """cat Project/app.* → allowed."""
        decision, _ = sg.sanitize_terminal_command("cat Project/app.*", WS)
        assert decision == "allow"

    def test_project_src_deep(self):
        """cat Project/src/*.py → allowed."""
        decision, _ = sg.sanitize_terminal_command("cat Project/src/*.py", WS)
        assert decision == "allow"

    def test_z_star_safe(self):
        """ls z* — 'z' prefix matches no deny zone, non-path-like → allowed."""
        decision, _ = sg.sanitize_terminal_command("ls z*", WS)
        assert decision == "allow"

    def test_no_wildcard_project(self):
        """ls Project/ — no wildcard, unaffected."""
        decision, _ = sg.sanitize_terminal_command("ls Project/", WS)
        assert decision == "allow"

    def test_project_question_mark_allowed(self):
        """ls Project/?.py — ? inside project folder → allowed."""
        decision, _ = sg.sanitize_terminal_command("ls Project/?.py", WS)
        assert decision == "allow"


# ===========================================================================
# Mirror test — templates/coding copy has identical wildcard behavior
# ===========================================================================

class TestMirrorSync:
    """Verify the templates/coding copy of security_gate.py is properly synced."""

    @pytest.fixture(scope="class")
    def tsg(self):
        """Import templates security_gate under a private module name.

        The module must be registered in sys.modules before exec_module so
        that @dataclasses.dataclass can resolve cls.__module__ at decoration time.
        sys.dont_write_bytecode is temporarily set to True so that no .pyc file
        is written to templates/coding/.../__pycache__, keeping the templates/
        directory clean and the INS-004 bundling tests green.
        """
        _MOD_NAME = "_saf020_tsg"
        templates_path = os.path.join(_TEMPLATES_SCRIPTS_DIR, "security_gate.py")
        spec = importlib.util.spec_from_file_location(_MOD_NAME, templates_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[_MOD_NAME] = mod  # required for @dataclass decorator to work
        prev_dont_write = sys.dont_write_bytecode
        sys.dont_write_bytecode = True  # prevent __pycache__ in templates/
        try:
            spec.loader.exec_module(mod)
        except Exception:
            sys.modules.pop(_MOD_NAME, None)
            raise
        finally:
            sys.dont_write_bytecode = prev_dont_write
        return mod

    def test_templates_wildcard_deny_zones_constant(self, tsg):
        """templates copy has the same _WILDCARD_DENY_ZONES entries."""
        assert set(tsg._WILDCARD_DENY_ZONES) == set(sg._WILDCARD_DENY_ZONES)

    def test_templates_blocks_dotg_star(self, tsg):
        """templates copy blocks Get-ChildItem .g*."""
        decision, _ = tsg.sanitize_terminal_command("Get-ChildItem .g*", WS)
        assert decision == "deny"

    def test_templates_blocks_n_star(self, tsg):
        """templates copy blocks Get-ChildItem N*."""
        decision, _ = tsg.sanitize_terminal_command("Get-ChildItem N*", WS)
        assert decision == "deny"

    def test_templates_blocks_dotv_star(self, tsg):
        """templates copy blocks Get-ChildItem .v*."""
        decision, _ = tsg.sanitize_terminal_command("Get-ChildItem .v*", WS)
        assert decision == "deny"

    def test_templates_allows_project_wildcard(self, tsg):
        """templates copy allows ls Project/*.py."""
        decision, _ = tsg.sanitize_terminal_command("ls Project/*.py", WS)
        assert decision == "allow"

    def test_templates_helper_dotg_star(self, tsg):
        """templates _wildcard_prefix_matches_deny_zone('.g*') == True."""
        assert tsg._wildcard_prefix_matches_deny_zone(".g*") is True

    def test_templates_helper_project_wildcard(self, tsg):
        """templates _wildcard_prefix_matches_deny_zone('Project/*.py') == False."""
        assert tsg._wildcard_prefix_matches_deny_zone("Project/*.py") is False
