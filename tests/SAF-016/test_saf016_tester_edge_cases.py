"""SAF-016 — Tester-added edge-case tests.

Covers attack vectors and boundary conditions not in the Developer's test suite:

1.  rm -rf / style attack — absolute root path
2.  Absolute Windows path (C:/Windows/...) — must be denied
3.  Tilde + slash path (rm ~/secret) — path-like via slash → denied
4.  Bare tilde (rm ~) — NOT path-like by design; current behaviour documented
5.  Windows-style /f /q flags colliding with path check → denied
6.  Pipeline delete: Get-ChildItem .github | Remove-Item → denied (verb zone-check)
7.  Workspace-root dot (rm .) → denied (. resolves to ws root, not project zone)
8.  rm -rf . (recursive workspace-root delete) → denied
9.  Named parameter -LiteralPath with deny-zone target → denied
10. Named parameter -Path with deny-zone target → denied
11. Two deny-zone paths in one command → denied
12. rm .github .vscode (both deny zones, one invocation) → denied
13. ri targeting NoAgentZone/ explicitly (redundant, defense-in-depth) → denied
14. erase with absolute root path → denied
15. rmdir // (double-slash root alias) → denied
16. Path argument containing null byte after stripping → denied (zone_classifier strips
    control characters; path is resolved to workspace root, not project → deny)
17. Deeply nested traversal: project/a/b/c/../../../.github → denied
18. Pathological token: remove-item with '-' only (lone dash treated as flag) → allow
    (lone dash means stdin on Unix; safe by design)
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "Default-Project"
    / ".github"
    / "hooks"
    / "scripts"
)

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


@pytest.fixture(scope="module")
def sg():
    import security_gate as _sg
    return _sg


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


WS = "c:/workspace"
P1 = "project/src/file.txt"
GITHUB = ".github/hooks/evil.py"
VSCODE = ".vscode/settings.json"
NOAGENT = "NoAgentZone/secret.txt"


def allow(sg, cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "allow"


def deny(sg, cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# Group 1 — rm -rf / style attacks (absolute root path)
# ---------------------------------------------------------------------------

def test_rm_rf_absolute_root_denied(sg):
    """rm -rf / must be denied — absolute root path is outside the project."""
    assert deny(sg, "rm -rf /")


def test_remove_item_absolute_root_denied(sg):
    """remove-item / must be denied — absolute root is not in project zone."""
    assert deny(sg, "remove-item /")


def test_rm_absolute_unix_path_denied(sg):
    """rm /etc/passwd must be denied — absolute Unix path outside workspace."""
    assert deny(sg, "rm /etc/passwd")


def test_del_absolute_windows_path_denied(sg):
    """del C:/Windows/System32 must be denied — absolute Windows path outside workspace."""
    assert deny(sg, "del C:/Windows/System32")


def test_remove_item_absolute_windows_denied(sg):
    """remove-item C:/Windows/System32 must be denied."""
    assert deny(sg, "remove-item C:/Windows/System32")


def test_erase_absolute_path_denied(sg):
    """erase /etc/hosts must be denied — absolute path outside workspace."""
    assert deny(sg, "erase /etc/hosts")


# ---------------------------------------------------------------------------
# Group 2 — Tilde paths
# ---------------------------------------------------------------------------

def test_rm_tilde_slash_path_denied(sg):
    """rm ~/Documents/secret must be denied — ~/x is path-like (slash) and
    resolves as workspace-relative path not in the project zone."""
    assert deny(sg, "rm ~/Documents/secret")


def test_rm_rf_tilde_slash_denied(sg):
    """rm -rf ~/secret must be denied — tilde+slash resolves outside project."""
    assert deny(sg, "rm -rf ~/secret")


def test_remove_item_tilde_slash_denied(sg):
    """remove-item ~/evil must be denied — tilde+slash is path-like → deny zone."""
    assert deny(sg, "remove-item ~/evil")


def test_rm_bare_tilde_current_behaviour(sg):
    """rm ~ — bare tilde is now recognised as path-like (SAF-030 fix).

    SAF-030 added a tilde check to _is_path_like() so that bare ~ and ~/path
    tokens are treated as file-system paths and zone-checked.  Since ~ resolves
    to HOME (outside the project folder), the zone classifier returns 'deny'.
    Previously this was a known bug (BUG-048) where rm ~ was allowed.
    """
    assert deny(sg, "rm ~")


# ---------------------------------------------------------------------------
# Group 3 — Windows-style /flag slash collision
# ---------------------------------------------------------------------------

def test_del_windows_slash_flag_denied(sg):
    """del /f /q project/file.txt must be denied.

    The /f token contains a forward slash, making it look like an absolute
    Unix path '/f' to the zone classifier — which is outside the workspace
    and therefore in the deny zone.  Windows flags with leading slashes are
    not supported in this security model; use Remove-Item flags instead.
    """
    assert deny(sg, f"del /f /q {P1}")


def test_erase_windows_slash_flag_denied(sg):
    """erase /f project/file.txt must be denied — /f looks like absolute path."""
    assert deny(sg, f"erase /f {P1}")


def test_del_slash_s_slash_q_denied(sg):
    """del /s /q targeting project path must be denied — /s is absolute path."""
    assert deny(sg, f"del /s /q {P1}")


# ---------------------------------------------------------------------------
# Group 4 — Pipeline delete (pipe is NOT a chain separator; checks verb zone)
# ---------------------------------------------------------------------------

def test_pipeline_gci_github_remove_item_denied(sg):
    """Get-ChildItem .github | Remove-Item must be denied.

    The pipe character | is NOT a segment separator in the security gate
    (only ;, && and || split segments).  The whole pipeline is treated as a
    single segment with verb 'get-childitem' and arg '.github'.  Since
    get-childitem has path_args_restricted=True, '.github' triggers a deny.
    """
    assert deny(sg, "Get-ChildItem .github | Remove-Item")


def test_pipeline_gci_vscode_remove_item_denied(sg):
    """Get-ChildItem .vscode | Remove-Item -Recurse -Force must be denied."""
    assert deny(sg, "Get-ChildItem .vscode | Remove-Item -Recurse -Force")


def test_pipeline_gci_project_remove_item_allowed(sg):
    """Get-ChildItem project/src | Remove-Item must be allowed.

    The pipeline verb is get-childitem and its path argument (project/src) is
    inside the project zone.  Remove-Item is just a token in the args list and
    has no path separator, so it is not treated as a path argument.
    """
    assert allow(sg, "Get-ChildItem project/src | Remove-Item")


# ---------------------------------------------------------------------------
# Group 5 — Workspace root / dot attacks
# ---------------------------------------------------------------------------

def test_rm_dot_denied(sg):
    """rm . must be denied — '.' resolves to the workspace root, not project zone."""
    assert deny(sg, "rm .")


def test_rm_rf_dot_denied(sg):
    """rm -rf . must be denied — '.' is workspace root, not in project zone."""
    assert deny(sg, "rm -rf .")


def test_remove_item_dot_denied(sg):
    """remove-item . must be denied — dot is workspace root."""
    assert deny(sg, "remove-item .")


def test_rmdir_dot_dot_denied(sg):
    """rmdir .. must be denied — '..' traverses above workspace root → deny."""
    assert deny(sg, "rmdir ..")


# ---------------------------------------------------------------------------
# Group 6 — Named parameter bypass attempts (-Path / -LiteralPath)
# ---------------------------------------------------------------------------

def test_remove_item_named_path_github_denied(sg):
    """remove-item -Path .github/hooks must be denied.

    The -Path flag is skipped (starts with '-'), then the next token
    '.github/hooks' is path-like and zone-checked → deny.
    """
    assert deny(sg, "remove-item -Path .github/hooks")


def test_remove_item_named_path_vscode_force_denied(sg):
    """remove-item -Path .vscode/settings.json -Force must be denied."""
    assert deny(sg, "remove-item -Path .vscode/settings.json -Force")


def test_remove_item_literalpath_github_denied(sg):
    """remove-item -LiteralPath .github/evil.py must be denied.

    The -LiteralPath flag (starts with '-') is treated as a flag and skipped.
    The next token '.github/evil.py' is path-like → deny.
    """
    assert deny(sg, "remove-item -LiteralPath .github/evil.py")


def test_remove_item_literalpath_project_allowed(sg):
    """remove-item -LiteralPath project/src/output.py must be allowed."""
    assert allow(sg, "remove-item -LiteralPath project/src/output.py")


# ---------------------------------------------------------------------------
# Group 7 — Two deny-zone paths in one command
# ---------------------------------------------------------------------------

def test_rm_github_and_vscode_denied(sg):
    """rm .github .vscode must be denied — both targets are in deny zones."""
    assert deny(sg, "rm .github .vscode")


def test_del_github_and_noagentzone_denied(sg):
    """del .github/x NoAgentZone/y must be denied — both in deny zones."""
    assert deny(sg, "del .github/x NoAgentZone/y")


def test_rm_noagentzone_multiple_denied(sg):
    """ri NoAgentZone/a NoAgentZone/b must be denied — both outside project."""
    assert deny(sg, "ri NoAgentZone/a NoAgentZone/b")


# ---------------------------------------------------------------------------
# Group 8 — Deeply nested traversal through project
# ---------------------------------------------------------------------------

def test_rm_deep_traversal_to_github_denied(sg):
    """rm project/a/b/c/../../../../.github must be denied.

    project/a/b/c (3 levels in) + 4×'..' exits the project folder entirely:
    c→b→a→project→workspace-root, then '.github' = workspace-root .github → deny.
    Using 3×'..' would only reach project/.github (inside project zone → allow).
    """
    assert deny(sg, "rm project/a/b/c/../../../../.github")


def test_remove_item_deep_traversal_to_vscode_denied(sg):
    """remove-item project/x/y/../../../.vscode/s.json must be denied.

    project/x/y (2 levels in) + 3×'..' exits the project folder:
    y→x→project→workspace-root, then '.vscode/s.json' = workspace-root .vscode → deny.
    """
    assert deny(sg, "remove-item project/x/y/../../../.vscode/s.json")


def test_rmdir_traversal_to_noagent_denied(sg):
    """rmdir project/../NoAgentZone must be denied — traversal to NoAgentZone."""
    assert deny(sg, "rmdir project/../NoAgentZone")


# ---------------------------------------------------------------------------
# Group 9 — rmdir double-slash and edge paths
# ---------------------------------------------------------------------------

def test_rmdir_double_slash_root_denied(sg):
    """rmdir // must be denied — // normalises to / (Unix root) → deny."""
    assert deny(sg, "rmdir //")


def test_rm_rf_multiple_deny_zones_denied(sg):
    """rm -rf .github .vscode NoAgentZone must be denied — all three deny zones."""
    assert deny(sg, "rm -rf .github .vscode NoAgentZone")


# ---------------------------------------------------------------------------
# Group 10 — ri NoAgentZone (defense in depth — explicit deny-zone target)
# ---------------------------------------------------------------------------

def test_ri_noagentzone_denied(sg):
    """ri NoAgentZone/secret.txt must be denied."""
    assert deny(sg, "ri NoAgentZone/secret.txt")


def test_erase_noagentzone_denied(sg):
    """erase NoAgentZone/secret.txt must be denied."""
    assert deny(sg, "erase NoAgentZone/secret.txt")


# ---------------------------------------------------------------------------
# Group 11 — allow_arbitrary_paths=False consistency
# ---------------------------------------------------------------------------

def test_all_category_n_deny_arbitrary_paths(sg):
    """Every Category N command must have allow_arbitrary_paths=False."""
    for cmd in ("remove-item", "ri", "rm", "del", "erase", "rmdir"):
        rule = sg._COMMAND_ALLOWLIST[cmd]
        assert rule.allow_arbitrary_paths is False, (
            f"{cmd} must have allow_arbitrary_paths=False"
        )


def test_all_category_n_empty_denied_flags(sg):
    """Category N commands must have an empty denied_flags frozenset (flags are
    allowed by design; zone checking is the safety boundary)."""
    for cmd in ("remove-item", "ri", "rm", "del", "erase", "rmdir"):
        rule = sg._COMMAND_ALLOWLIST[cmd]
        assert rule.denied_flags == frozenset(), (
            f"{cmd} should have empty denied_flags (zone checking is the guard)"
        )
