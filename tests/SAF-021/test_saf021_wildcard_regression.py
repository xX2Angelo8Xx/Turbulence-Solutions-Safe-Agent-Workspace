"""SAF-021 — Wildcard Bypass Regression Tests

Comprehensive regression tests covering every wildcard bypass vector identified
in the security audit.  All tests assert the ALREADY-IMPLEMENTED SAF-020 behavior
(deny or allow) and serve as a permanent regression baseline.

Audit vectors covered (10 from WP description):
  1.  Get-ChildItem .g*                    — denied
  2.  Get-ChildItem N*                     — denied
  3.  Get-ChildItem .v*                    — denied
  4.  Get-ChildItem .g* | Get-Content      — denied (piped command)
  5.  Get-ChildItem .g* -Force -Recurse -Name — denied (flags after wildcard)
  6.  ls .g*                               — denied
  7.  cat N*/*                             — denied
  8.  Wildcards targeting project folder   — allowed
  9.  dir .g*                              — denied
 10.  Wildcards with path traversal        — denied

Additional bypass techniques:
  11. Bracket expression wildcards [.g]*, [Nn]*, [.v]*  — denied (BUG-051 fix)
  12. Double-star / globstar patterns                   — denied at root, allowed in Project/
  13. cmd.exe-style wildcard patterns                   — denied
"""
from __future__ import annotations

import os
import sys

# ---------------------------------------------------------------------------
# Path setup — resolve security_gate from its non-standard location
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_SCRIPTS_DIR = os.path.join(
    _REPO_ROOT, "Default-Project", ".github", "hooks", "scripts"
)

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

# Fake workspace root; conftest patches detect_project_folder so
# zone_classifier returns 'allow' for Project/ paths even though
# 'c:/workspace' does not exist on disk.
WS = "c:/workspace"


# ===========================================================================
# Audit Vector 1 — Get-ChildItem .g*
# ===========================================================================

class TestAuditVector1_GetChildItemDotGStar:
    """Audit report vector 1: Get-ChildItem .g* must be denied.

    Covers the exact command from the audit report plus GCI alias and
    uppercase variant.
    """

    def test_audit_v1_exact_command_denied(self):
        """Exact audit command: Get-ChildItem .g* → denied."""
        decision, reason = sg.sanitize_terminal_command("Get-ChildItem .g*", WS)
        assert decision == "deny"
        assert reason is not None

    def test_audit_v1_gci_alias_denied(self):
        """GCI alias: gci .g* → denied (same as Get-ChildItem)."""
        decision, _ = sg.sanitize_terminal_command("gci .g*", WS)
        assert decision == "deny"

    def test_audit_v1_uppercase_verb_denied(self):
        """Case-insensitive verb matching: GET-CHILDITEM .g* → denied."""
        decision, _ = sg.sanitize_terminal_command("GET-CHILDITEM .g*", WS)
        assert decision == "deny"

    def test_audit_v1_helper_dotg_star_true(self):
        """Helper unit check: _wildcard_prefix_matches_deny_zone('.g*') is True."""
        assert sg._wildcard_prefix_matches_deny_zone(".g*") is True


# ===========================================================================
# Audit Vector 2 — Get-ChildItem N*
# ===========================================================================

class TestAuditVector2_GetChildItemNStar:
    """Audit report vector 2: Get-ChildItem N* must be denied.

    N* expands to NoAgentZone; must be blocked regardless of case.
    """

    def test_audit_v2_exact_command_denied(self):
        """Exact audit command: Get-ChildItem N* → denied."""
        decision, _ = sg.sanitize_terminal_command("Get-ChildItem N*", WS)
        assert decision == "deny"

    def test_audit_v2_lowercase_n_star_denied(self):
        """Lowercase variant: gci n* → denied."""
        decision, _ = sg.sanitize_terminal_command("gci n*", WS)
        assert decision == "deny"

    def test_audit_v2_noagent_prefix_denied(self):
        """Longer prefix: Get-ChildItem NoAgent* → denied (prefix matches noagentzone)."""
        decision, _ = sg.sanitize_terminal_command("Get-ChildItem NoAgent*", WS)
        assert decision == "deny"

    def test_audit_v2_helper_n_star_true(self):
        """Helper unit check: _wildcard_prefix_matches_deny_zone('N*') is True."""
        assert sg._wildcard_prefix_matches_deny_zone("N*") is True


# ===========================================================================
# Audit Vector 3 — Get-ChildItem .v*
# ===========================================================================

class TestAuditVector3_GetChildItemDotVStar:
    """Audit report vector 3: Get-ChildItem .v* must be denied.

    .v* expands to .vscode; must be blocked.
    """

    def test_audit_v3_exact_command_denied(self):
        """Exact audit command: Get-ChildItem .v* → denied."""
        decision, _ = sg.sanitize_terminal_command("Get-ChildItem .v*", WS)
        assert decision == "deny"

    def test_audit_v3_dotvsode_star_denied(self):
        """Longer prefix: gci .vscode* → denied."""
        decision, _ = sg.sanitize_terminal_command("gci .vscode*", WS)
        assert decision == "deny"

    def test_audit_v3_helper_dotv_star_true(self):
        """Helper unit check: _wildcard_prefix_matches_deny_zone('.v*') is True."""
        assert sg._wildcard_prefix_matches_deny_zone(".v*") is True


# ===========================================================================
# Audit Vector 4 — Get-ChildItem .g* | Get-Content
# ===========================================================================

class TestAuditVector4_PipedWildcardCommands:
    """Audit report vector 4: piped wildcard commands must be denied.

    A single pipe '|' is NOT a chain separator (only ; && || are), so the
    whole command is one segment.  The wildcard '.g*' appears in the args
    of Get-ChildItem — which is path_args_restricted — and is caught before
    the pipe is evaluated.
    """

    def test_audit_v4_exact_piped_command_denied(self):
        """Exact audit command: Get-ChildItem .g* | Get-Content → denied."""
        decision, _ = sg.sanitize_terminal_command(
            "Get-ChildItem .g* | Get-Content", WS
        )
        assert decision == "deny"

    def test_audit_v4_gci_gc_aliases_denied(self):
        """Alias variant: gci .g* | gc → denied."""
        decision, _ = sg.sanitize_terminal_command("gci .g* | gc", WS)
        assert decision == "deny"

    def test_audit_v4_n_star_piped_select_object_denied(self):
        """N* piped: gci N* | Select-Object -First 5 → denied."""
        decision, _ = sg.sanitize_terminal_command(
            "gci N* | Select-Object -First 5", WS
        )
        assert decision == "deny"

    def test_audit_v4_dotv_star_piped_out_denied(self):
        """Piped output: Get-ChildItem .v* | Out-String → denied."""
        decision, _ = sg.sanitize_terminal_command(
            "Get-ChildItem .v* | Out-String", WS
        )
        assert decision == "deny"


# ===========================================================================
# Audit Vector 5 — Get-ChildItem .g* -Force -Recurse -Name
# ===========================================================================

class TestAuditVector5_WildcardWithFlags:
    """Audit report vector 5: flags AFTER the wildcard argument must not bypass.

    The wildcard token appears before the flags; it is evaluated first and
    triggers the deny before any flag processing changes the outcome.
    """

    def test_audit_v5_exact_command_denied(self):
        """Exact audit command: Get-ChildItem .g* -Force -Recurse -Name → denied."""
        decision, _ = sg.sanitize_terminal_command(
            "Get-ChildItem .g* -Force -Recurse -Name", WS
        )
        assert decision == "deny"

    def test_audit_v5_force_only_denied(self):
        """Shorter form: Get-ChildItem .g* -Force → denied."""
        decision, _ = sg.sanitize_terminal_command("Get-ChildItem .g* -Force", WS)
        assert decision == "deny"

    def test_audit_v5_n_star_recurse_filter_denied(self):
        """N* with flags: gci N* -Recurse -Filter *.json → denied."""
        decision, _ = sg.sanitize_terminal_command(
            "gci N* -Recurse -Filter *.json", WS
        )
        assert decision == "deny"

    def test_audit_v5_dotv_star_depth_denied(self):
        """Depth flag: Get-ChildItem .v* -Depth 10 → denied."""
        decision, _ = sg.sanitize_terminal_command(
            "Get-ChildItem .v* -Depth 10", WS
        )
        assert decision == "deny"


# ===========================================================================
# Audit Vector 6 — ls .g*
# ===========================================================================

class TestAuditVector6_LsDotGStar:
    """Audit report vector 6: ls .g* must be denied."""

    def test_audit_v6_exact_command_denied(self):
        """Exact audit command: ls .g* → denied."""
        decision, _ = sg.sanitize_terminal_command("ls .g*", WS)
        assert decision == "deny"

    def test_audit_v6_ls_la_flag_denied(self):
        """With flags: ls -la .g* → denied (wildcard after flags still caught)."""
        decision, _ = sg.sanitize_terminal_command("ls -la .g*", WS)
        assert decision == "deny"

    def test_audit_v6_ls_dotgithub_star_denied(self):
        """Full prefix: ls .github* → denied (would match .github exactly)."""
        decision, _ = sg.sanitize_terminal_command("ls .github*", WS)
        assert decision == "deny"

    def test_audit_v6_ls_n_star_denied(self):
        """ls N* → denied (N* matches NoAgentZone)."""
        decision, _ = sg.sanitize_terminal_command("ls N*", WS)
        assert decision == "deny"


# ===========================================================================
# Audit Vector 7 — cat N*/*
# ===========================================================================

class TestAuditVector7_CatNStarSlash:
    """Audit report vector 7: cat N*/* must be denied.

    The first wildcard component 'N*' has prefix 'n' (lowercased) which
    matches 'noagentzone'.
    """

    def test_audit_v7_exact_command_denied(self):
        """Exact audit command: cat N*/* → denied."""
        decision, _ = sg.sanitize_terminal_command("cat N*/*", WS)
        assert decision == "deny"

    def test_audit_v7_noagent_star_denied(self):
        """cat noagent* → denied."""
        decision, _ = sg.sanitize_terminal_command("cat noagent*", WS)
        assert decision == "deny"

    def test_audit_v7_noagentzone_star_denied(self):
        """cat NoAgentZone* → denied (full zone name as prefix)."""
        decision, _ = sg.sanitize_terminal_command("cat NoAgentZone*", WS)
        assert decision == "deny"

    def test_audit_v7_helper_n_slash_star_true(self):
        """Helper: _wildcard_prefix_matches_deny_zone('N*/*') is True."""
        assert sg._wildcard_prefix_matches_deny_zone("N*/*") is True


# ===========================================================================
# Audit Vector 8 — Wildcards targeting project folder are allowed
# ===========================================================================

class TestAuditVector8_ProjectFolderAllowed:
    """Audit report vector 8: wildcards inside Project/ must NOT be denied.

    The wildcard guard only fires when a wildcard could expand to a deny zone.
    Wildcards safely inside Project/ (or other non-deny parents) are allowed.
    """

    def test_audit_v8_ls_project_py_allowed(self):
        """ls Project/*.py → allowed (safe parent Project)."""
        decision, _ = sg.sanitize_terminal_command("ls Project/*.py", WS)
        assert decision == "allow"

    def test_audit_v8_cat_project_app_star_allowed(self):
        """cat Project/app.* → allowed."""
        decision, _ = sg.sanitize_terminal_command("cat Project/app.*", WS)
        assert decision == "allow"

    def test_audit_v8_gci_project_json_allowed(self):
        """Get-ChildItem Project/*.json → allowed."""
        decision, _ = sg.sanitize_terminal_command(
            "Get-ChildItem Project/*.json", WS
        )
        assert decision == "allow"

    def test_audit_v8_project_deep_wildcard_allowed(self):
        """ls Project/src/*.py → allowed (wildcard nested inside safe parent)."""
        decision, _ = sg.sanitize_terminal_command("ls Project/src/*.py", WS)
        assert decision == "allow"

    def test_audit_v8_helper_project_star_false(self):
        """Helper: _wildcard_prefix_matches_deny_zone('Project/*.py') is False."""
        assert sg._wildcard_prefix_matches_deny_zone("Project/*.py") is False

    def test_audit_v8_helper_project_src_star_false(self):
        """Helper: nested Project/src/*.py → False."""
        assert sg._wildcard_prefix_matches_deny_zone("Project/src/*.py") is False


# ===========================================================================
# Audit Vector 9 — dir .g*
# ===========================================================================

class TestAuditVector9_DirDotGStar:
    """Audit report vector 9: dir .g* must be denied.

    'dir' is the Windows CMD listing command and is in the allowlist with
    path_args_restricted=True.
    """

    def test_audit_v9_exact_command_denied(self):
        """Exact audit command: dir .g* → denied."""
        decision, _ = sg.sanitize_terminal_command("dir .g*", WS)
        assert decision == "deny"

    def test_audit_v9_dir_dotvsode_star_denied(self):
        """dir .vscode* → denied."""
        decision, _ = sg.sanitize_terminal_command("dir .vscode*", WS)
        assert decision == "deny"

    def test_audit_v9_dir_n_star_denied(self):
        """dir N* → denied."""
        decision, _ = sg.sanitize_terminal_command("dir N*", WS)
        assert decision == "deny"

    def test_audit_v9_dir_dotv_star_denied(self):
        """dir .v* → denied (same as Get-ChildItem .v*)."""
        decision, _ = sg.sanitize_terminal_command("dir .v*", WS)
        assert decision == "deny"


# ===========================================================================
# Audit Vector 10 — Wildcards with path traversal combinations
# ===========================================================================

class TestAuditVector10_PathTraversalCombinations:
    """Audit report vector 10: combining path traversal ('..' / '.') with
    wildcard patterns must not bypass the deny-zone check.

    The helper treats '..' and '.' as transparent components, so a wildcard
    following only dots is still treated as root-level and denied if the
    prefix matches a deny zone.
    """

    def test_audit_v10_double_dot_dotg_star_denied(self):
        """ls ../../.g* — dots transparent; .g* at effective root → denied."""
        decision, _ = sg.sanitize_terminal_command("ls ../../.g*", WS)
        assert decision == "deny"

    def test_audit_v10_dot_slash_dotg_star_denied(self):
        """ls ./.g* — leading dot transparent; .g* at effective root → denied."""
        decision, _ = sg.sanitize_terminal_command("ls ./.g*", WS)
        assert decision == "deny"

    def test_audit_v10_dot_dotdot_n_star_denied(self):
        """cat ./../N* — dot and double-dot transparent; N* denied."""
        decision, _ = sg.sanitize_terminal_command("cat ./../N*", WS)
        assert decision == "deny"

    def test_audit_v10_dotdot_n_star_denied(self):
        """ls ../N* — double-dot transparent; N* at effective root → denied."""
        decision, _ = sg.sanitize_terminal_command("ls ../N*", WS)
        assert decision == "deny"

    def test_audit_v10_helper_dotdot_dotg_star_true(self):
        """Helper: _wildcard_prefix_matches_deny_zone('../../.g*') is True."""
        assert sg._wildcard_prefix_matches_deny_zone("../../.g*") is True

    def test_audit_v10_helper_dot_slash_dotg_star_true(self):
        """Helper: _wildcard_prefix_matches_deny_zone('./.g*') is True."""
        assert sg._wildcard_prefix_matches_deny_zone("./.g*") is True


# ===========================================================================
# Additional — Bracket Expression Wildcard Bypass (BUG-051 fix)
# ===========================================================================

class TestBracketWildcardBypass:
    """Bracket expression wildcards [...]  are a known shell-expansion bypass.

    [.g]* could expand to .github or .vscode; [Nn]* expands to NoAgentZone.
    These were fixed in SAF-020 iteration 2 (BUG-051) by adding '[' to the
    wildcard trigger characters.  All tests here must PASS.
    """

    def test_bracket_dotg_helper_true(self):
        """[.g]* — bracket class contains '.', which starts .github → deny."""
        assert sg._wildcard_prefix_matches_deny_zone("[.g]*") is True

    def test_bracket_n_upper_lower_helper_true(self):
        """[Nn]* — bracket class matches N/n; prefix starts noagentzone → deny."""
        assert sg._wildcard_prefix_matches_deny_zone("[Nn]*") is True

    def test_bracket_dotv_helper_true(self):
        """[.v]* — bracket class contains '.', matching .vscode → deny."""
        assert sg._wildcard_prefix_matches_deny_zone("[.v]*") is True

    def test_bracket_dotg_star_gci_denied(self):
        """Get-ChildItem [.g]* → denied (bracket bypass blocked)."""
        decision, _ = sg.sanitize_terminal_command("Get-ChildItem [.g]*", WS)
        assert decision == "deny"

    def test_bracket_n_star_ls_denied(self):
        """ls [Nn]* → denied (bracket bracket bypass blocked)."""
        decision, _ = sg.sanitize_terminal_command("ls [Nn]*", WS)
        assert decision == "deny"

    def test_bracket_dotv_star_dir_denied(self):
        """dir [.v]* → denied (bracket bypass blocked)."""
        decision, _ = sg.sanitize_terminal_command("dir [.v]*", WS)
        assert decision == "deny"


# ===========================================================================
# Additional — Double-Star / Globstar Bypass
# ===========================================================================

class TestDoubleStarBypass:
    """Globstar (**) patterns at root level must be denied because the empty
    prefix before '**' conservatively matches every deny zone.  Inside a
    safe parent (Project/) they are allowed.
    """

    def test_double_star_helper_true(self):
        """** alone — empty prefix → deny (helper returns True)."""
        assert sg._wildcard_prefix_matches_deny_zone("**") is True

    def test_ls_double_star_denied(self):
        """ls ** — globstar at root denied."""
        decision, _ = sg.sanitize_terminal_command("ls **", WS)
        assert decision == "deny"

    def test_gci_double_star_denied(self):
        """Get-ChildItem ** → denied."""
        decision, _ = sg.sanitize_terminal_command("Get-ChildItem **", WS)
        assert decision == "deny"

    def test_double_star_py_root_denied(self):
        """ls **/*.py — globstar at root could enumerate deny zones → denied."""
        decision, _ = sg.sanitize_terminal_command("ls **/*.py", WS)
        assert decision == "deny"

    def test_project_double_star_helper_false(self):
        """Project/**/*.py — safe parent Project entered before ** → helper False."""
        assert sg._wildcard_prefix_matches_deny_zone("Project/**/*.py") is False

    def test_project_double_star_allowed(self):
        """cat Project/**/*.py → allowed (globstar inside Project/)."""
        decision, _ = sg.sanitize_terminal_command("cat Project/**/*.py", WS)
        assert decision == "allow"


# ===========================================================================
# Additional — cmd.exe-style Wildcard Patterns
# ===========================================================================

class TestCmdExeWildcardPatterns:
    """Windows CMD-style listing patterns that must not bypass the deny gate."""

    def test_dir_dotg_star_denied(self):
        """dir .g* — CMD dir command targeting .github prefix → denied."""
        decision, _ = sg.sanitize_terminal_command("dir .g*", WS)
        assert decision == "deny"

    def test_dir_n_star_denied(self):
        """dir N* — CMD dir command targeting NoAgentZone prefix → denied."""
        decision, _ = sg.sanitize_terminal_command("dir N*", WS)
        assert decision == "deny"

    def test_dir_dotv_star_denied(self):
        """dir .v* — CMD dir command targeting .vscode prefix → denied."""
        decision, _ = sg.sanitize_terminal_command("dir .v*", WS)
        assert decision == "deny"

    def test_dir_slash_b_dotg_star_denied(self):
        """dir /b .g* — Windows /b flag before wildcard must not skip wildcard check."""
        decision, _ = sg.sanitize_terminal_command("dir /b .g*", WS)
        assert decision == "deny"

    def test_dir_slash_s_n_star_denied(self):
        """dir /s N* — Windows /s (recursive) flag before wildcard → denied."""
        decision, _ = sg.sanitize_terminal_command("dir /s N*", WS)
        assert decision == "deny"

    def test_dir_slash_b_dotv_star_denied(self):
        """dir /b .v* — Windows bare-format flag before .vscode wildcard → denied."""
        decision, _ = sg.sanitize_terminal_command("dir /b .v*", WS)
        assert decision == "deny"


# ===========================================================================
# Tester additions — Question-mark single-character wildcard bypass
# ===========================================================================

class TestQuestionMarkWildcard:
    """The ? wildcard replaces exactly one character.

    A rogue agent could use '?' to avoid matching literal deny zone names
    while still having the pattern expand to a restricted folder at runtime.
    e.g. '.githu?' expands to '.github', 'N?' expands to 'No' (prefix still
    matches 'noagentzone').

    SAF-020 includes '?' in its wildcard trigger characters.  All tests here
    verify ? patterns are correctly denied.
    """

    def test_question_mark_dotgithu_denied(self):
        """ls .githu? — single char wildcard resolving to .github → denied."""
        decision, _ = sg.sanitize_terminal_command("ls .githu?", WS)
        assert decision == "deny"

    def test_question_mark_n_single_denied(self):
        """ls N? — one-char wildcard; prefix 'n' matches noagentzone → denied."""
        decision, _ = sg.sanitize_terminal_command("ls N?", WS)
        assert decision == "deny"

    def test_question_mark_dotvsco_double_denied(self):
        """ls .vsco?? — two ? wildcards; prefix '.vsco' matches '.vscode' → denied."""
        decision, _ = sg.sanitize_terminal_command("ls .vsco??", WS)
        assert decision == "deny"

    def test_question_mark_gci_dotgithu_denied(self):
        """Get-ChildItem .githu? → denied (GCI alias, ? wildcard)."""
        decision, _ = sg.sanitize_terminal_command("Get-ChildItem .githu?", WS)
        assert decision == "deny"

    def test_question_mark_mixed_star_and_qmark_denied(self):
        """ls .g?* — ? then * wildcard; prefix '.g' matches .github → denied."""
        decision, _ = sg.sanitize_terminal_command("ls .g?*", WS)
        assert decision == "deny"

    def test_question_mark_helper_dotgithu_qmark_true(self):
        """Helper: _wildcard_prefix_matches_deny_zone('.githu?') is True."""
        assert sg._wildcard_prefix_matches_deny_zone(".githu?") is True

    def test_question_mark_helper_n_qmark_true(self):
        """Helper: _wildcard_prefix_matches_deny_zone('N?') is True."""
        assert sg._wildcard_prefix_matches_deny_zone("N?") is True

    def test_question_mark_project_config_allowed(self):
        """ls Project/?onfig.py — ? wildcard inside safe Project/ parent → allowed."""
        decision, _ = sg.sanitize_terminal_command("ls Project/?onfig.py", WS)
        assert decision == "allow"

    def test_question_mark_helper_project_qmark_false(self):
        """Helper: _wildcard_prefix_matches_deny_zone('Project/?onfig.py') is False."""
        assert sg._wildcard_prefix_matches_deny_zone("Project/?onfig.py") is False


# ===========================================================================
# Tester additions — Chained commands with wildcard in second segment
# ===========================================================================

class TestChainedCommandsWithWildcard:
    """When a terminal command uses ; or && to chain segments, the wildcard
    check must fire on the LATER segment too.

    A rogue agent might prepend an innocuous safe command to make the first
    segment pass, hiding the dangerous wildcard in the second segment.
    """

    def test_semicolon_chain_ls_dotg_star_denied(self):
        """echo ok; ls .g* — semicolon chain; second segment must be denied."""
        decision, _ = sg.sanitize_terminal_command("echo ok; ls .g*", WS)
        assert decision == "deny"

    def test_and_chain_cat_dotg_star_denied(self):
        """cd Project && cat .g* — AND-chain; second segment wildcard denied."""
        decision, _ = sg.sanitize_terminal_command("cd Project && cat .g*", WS)
        assert decision == "deny"

    def test_semicolon_chain_gci_n_star_denied(self):
        """echo safe; gci N* — N* in later segment must trigger deny."""
        decision, _ = sg.sanitize_terminal_command("echo safe; gci N*", WS)
        assert decision == "deny"

    def test_and_chain_gci_g_star_with_flags_denied(self):
        """cd Project && Get-ChildItem .g* -Name — flags after wildcard, chained."""
        decision, _ = sg.sanitize_terminal_command(
            "cd Project && Get-ChildItem .g* -Name", WS
        )
        assert decision == "deny"

    def test_semicolon_chain_dir_dotv_star_denied(self):
        """cd Project; dir .v* — semicolon chain; .v* in second segment denied."""
        decision, _ = sg.sanitize_terminal_command("cd Project; dir .v*", WS)
        assert decision == "deny"


# ===========================================================================
# Tester additions — Get-Content / Select-String with wildcard path
# ===========================================================================

class TestAllowlistedReadCommandsWithWildcard:
    """Get-Content and Select-String are in the allowlist (SAF-014) with
    path_args_restricted=True.  Wildcard paths targeting deny zones must still
    be blocked even though these commands are 'allowed' for normal use.
    """

    def test_get_content_dotg_star_denied(self):
        """Get-Content .g* — read contents of wildcard expansions → denied."""
        decision, _ = sg.sanitize_terminal_command("Get-Content .g*", WS)
        assert decision == "deny"

    def test_get_content_n_star_path_denied(self):
        """Get-Content N*\\README.md — deny zone wildcard in sub-path → denied."""
        decision, _ = sg.sanitize_terminal_command(r"Get-Content N*\README.md", WS)
        assert decision == "deny"

    def test_select_string_dotg_star_denied(self):
        """Select-String -Path .g*\\* -Pattern 'pass' → denied."""
        decision, _ = sg.sanitize_terminal_command(
            r"Select-String -Path .g*\* -Pattern pass", WS
        )
        assert decision == "deny"

    def test_gc_alias_dotv_star_denied(self):
        """gc .v*\\settings.json — 'gc' alias for Get-Content with wildcard → denied."""
        decision, _ = sg.sanitize_terminal_command(r"gc .v*\settings.json", WS)
        assert decision == "deny"

    def test_get_content_project_star_allowed(self):
        """Get-Content Project\\*.py — wildcard inside Project/ zone → allowed."""
        decision, _ = sg.sanitize_terminal_command(r"Get-Content Project\*.py", WS)
        assert decision == "allow"
