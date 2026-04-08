"""SAF-080 — Tests for trailing-comma stripping in batch Remove-Item.

PowerShell treats the comma as an array operator, so
``Remove-Item file1.py, file2.py`` is passed verbatim to the security gate.
``shlex`` tokenises the space-separated stream without special-casing the
comma, producing tokens like ``['remove-item', 'file1.py,', 'file2.py']``.

Without the fix the trailing comma on ``file1.py,`` can:
  * cause ``_is_path_like()`` to return False for bare names (no slash/dot),
    skipping zone checks entirely; or
  * break the deny-zone guard in ``_try_project_fallback()`` for bare
    deny-zone names like ``.github,`` (the comma makes the string-equality
    check miss the entry in the deny set), allowing deletion of protected
    directories.

The fix: ``stripped = stripped.rstrip(",")`` immediately after
``stripped = tok.strip("\\\"'")`` in ``_validate_args()`` step 5.

Test coverage:
    Batch delete — both project files:
        Remove-Item project/file1.py, project/file2.py → allowed
    Batch delete — one path in deny zone (.github sub-path):
        Remove-Item project/file.py, .github/secrets.txt → denied
    Batch delete — deny-zone path is the first argument:
        Remove-Item .github/secrets.txt, project/file.py → denied
    rm alias batch delete:
        rm project/file1.py, project/file2.py → allowed
    del alias batch delete:
        del project/file1.py, project/file2.py → allowed
    Critical security bypass — bare deny-zone name with trailing comma:
        Remove-Item .github, → denied (was allowed before fix)
    Non-Remove-Item command with comma token unaffected:
        echo hello, world → allowed
    Regression — Remove-Item without trailing commas still works:
        Remove-Item project/file1.py project/file2.py → allowed
    Regression — single file no comma:
        Remove-Item project/file.py → allowed
    Path with comma in middle (not trailing) is handled correctly:
        Remove-Item project/file,name.py → allowed
"""
from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Add the agent-workbench hook scripts to sys.path so security_gate is
# importable without installation.
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

WS = "c:/workspace"


@pytest.fixture(autouse=True)
def mock_project_folder():
    """Pin the detected project folder to 'project' for all tests."""
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


def allow(cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "allow"


def deny(cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "deny"


# ===========================================================================
# Batch Remove-Item — both arguments in the project folder
# ===========================================================================

def test_remove_item_batch_both_project_files_allowed():
    """SAF-080: Remove-Item project/file1.py, project/file2.py → both in project folder → allowed.

    Without the fix 'project/file1.py,' has its trailing comma included in the
    path classification, causing zone_classifier to use the fallback path.
    With the fix the comma is stripped before zone checks run.
    """
    assert allow("Remove-Item project/file1.py, project/file2.py")


def test_remove_item_batch_three_project_files_allowed():
    """SAF-080: Three comma-separated project-folder files → all allowed."""
    assert allow("Remove-Item project/a.py, project/b.py, project/c.py")


# ===========================================================================
# Batch Remove-Item — one argument in deny zone → must be denied
# ===========================================================================

def test_remove_item_batch_second_arg_deny_zone_denied():
    """SAF-080: Remove-Item project/file.py, .github/secrets.txt → denied (.github is deny zone)."""
    assert deny("Remove-Item project/file.py, .github/secrets.txt")


def test_remove_item_batch_first_arg_deny_zone_denied():
    """SAF-080: Remove-Item .github/secrets.txt, project/file.py → denied (.github is deny zone)."""
    assert deny("Remove-Item .github/secrets.txt, project/file.py")


def test_remove_item_batch_vscode_deny_zone_denied():
    """SAF-080: Remove-Item .vscode/settings.json, project/file.py → denied (.vscode is deny zone)."""
    assert deny("Remove-Item .vscode/settings.json, project/file.py")


# ===========================================================================
# Critical security test — bare deny-zone directory name with trailing comma
# ===========================================================================

def test_remove_item_bare_github_with_trailing_comma_denied():
    """SAF-080: Remove-Item .github, → CRITICAL — must be denied.

    Root cause: shlex produces '.github,' as a single token.  The trailing
    comma causes _try_project_fallback's deny-zone guard to miss it
    ('.github,' != '.github') and then zone_classifier mis-classifies the
    project-prefixed path as 'allow'.

    The fix strips the comma so '.github' reaches _try_project_fallback
    intact and is correctly blocked.
    """
    assert deny("Remove-Item .github,")


def test_remove_item_bare_vscode_with_trailing_comma_denied():
    """SAF-080: Remove-Item .vscode, → must be denied (same bypass as .github,)."""
    assert deny("Remove-Item .vscode,")


def test_remove_item_bare_noagentzone_with_trailing_comma_denied():
    """SAF-080: Remove-Item noagentzone/file.txt, project/ok.py → denied.

    noagentzone as a bare name (no slash) is not caught by _is_path_like()
    both with and without the trailing comma — that is pre-existing behaviour
    outside this WP's scope.  This test validates the multi-segment form
    (noagentzone/file.txt,) which IS path-like and must be denied.
    """
    assert deny("Remove-Item noagentzone/file.txt, project/ok.py")


# ===========================================================================
# rm and del aliases — batch syntax must also be allowed
# ===========================================================================

def test_rm_alias_batch_allowed():
    """SAF-080: rm project/file1.py, project/file2.py → rm alias, both project paths → allowed."""
    assert allow("rm project/file1.py, project/file2.py")


def test_del_alias_batch_allowed():
    """SAF-080: del project/file1.py, project/file2.py → del alias, both project paths → allowed."""
    assert allow("del project/file1.py, project/file2.py")


# ===========================================================================
# Non-Remove-Item commands with comma tokens — fix must not break them
# ===========================================================================

def test_echo_with_comma_unaffected():
    """SAF-080: echo hello, world → echo has allow_arbitrary_paths=True → still allowed.

    Confirms the fix is surgical: it only affects step-5 path zone checks,
    not commands exempt from path validation.
    """
    assert allow("echo hello, world")


# ===========================================================================
# Regression — Remove-Item without trailing commas still works
# ===========================================================================

def test_remove_item_without_commas_still_allowed():
    """SAF-080 regression: Remove-Item project/file1.py project/file2.py (no commas) → allowed."""
    assert allow("Remove-Item project/file1.py project/file2.py")


def test_remove_item_single_file_no_comma_allowed():
    """SAF-080 regression: Remove-Item project/file.py (no comma) → single file → allowed."""
    assert allow("Remove-Item project/file.py")


def test_remove_item_deny_zone_without_comma_still_denied():
    """SAF-080 regression: Remove-Item .github/file.py (no comma) → deny zone → still denied."""
    assert deny("Remove-Item .github/file.py")


# ===========================================================================
# Edge case — comma in the middle of a filename (not trailing)
# ===========================================================================

def test_remove_item_path_with_middle_comma_allowed():
    """SAF-080: Remove-Item project/file,name.py → comma in middle of filename → allowed.

    rstrip(',') only removes TRAILING commas; an embedded comma like
    'file,name.py' is left untouched.  The path resolves normally via
    zone_classifier (first component 'project' → allow).
    """
    assert allow("Remove-Item project/file,name.py")


def test_remove_item_path_with_middle_comma_deny_zone_denied():
    """SAF-080: Remove-Item .github/file,name.py → middle comma, deny zone → denied."""
    assert deny("Remove-Item .github/file,name.py")


# ===========================================================================
# Tester edge cases — not covered by Developer's tests
# ===========================================================================

def test_remove_item_multiple_trailing_commas_github_denied():
    """Tester: Remove-Item .github,,, → multiple trailing commas → still denied.

    rstrip(',') removes ALL trailing commas, so '.github,,,' → '.github',
    which must still be rejected by the deny-zone guard.
    """
    assert deny("Remove-Item .github,,,")


def test_remove_item_multiple_trailing_commas_vscode_denied():
    """Tester: Remove-Item .vscode,, → two trailing commas → still denied."""
    assert deny("Remove-Item .vscode,,")


def test_remove_item_github_mixed_case_with_trailing_comma_denied():
    """Tester: Remove-Item .GitHub, → case-insensitive deny-zone match with trailing comma.

    _try_project_fallback does p.lower() comparison, so '.GitHub' (after
    comma strip) must be caught identically to '.github'.
    """
    assert deny("Remove-Item .GitHub,")


def test_remove_item_quoted_path_with_trailing_comma_allowed():
    """Tester: Remove-Item 'project/file.py', project/file2.py → quoted path, trailing comma
    on first token 'project/file.py' (after quote stripping, then comma stripping) → allowed.

    shlex: ["'project/file.py',", 'project/file2.py']
    strip("\"'") → "project/file.py,"  then  rstrip(",") → "project/file.py" → allowed.
    """
    assert allow("Remove-Item 'project/file.py', project/file2.py")


def test_remove_item_quoted_github_with_trailing_comma_denied():
    """Tester: Remove-Item '.github', → quoted deny-zone bare name with trailing comma.

    shlex: ["'.github',"]
    strip("\"'") → ".github,"  then  rstrip(",") → ".github" → denied.
    """
    assert deny("Remove-Item '.github',")


def test_remove_item_comma_only_token_no_crash():
    """Tester: Remove-Item , project/file.py → lone comma token reduces to empty string.

    rstrip(',') on ',' → '' (empty).  Empty string is not path-like, not a
    flag, not env-assign, and contains no '$'/'*'/'?' → the loop skips it
    cleanly.  The project path in the second arg is allowed.
    """
    assert allow("Remove-Item , project/file.py")
