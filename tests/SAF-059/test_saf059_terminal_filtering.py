"""SAF-059 — Tests for four terminal command filtering inconsistencies.

Regression tests for:
  BUG-140: Remove-Item blocked but del allowed (Stage 3 false-positive on
           path arguments containing words like 'exec', 'iex', 'source')
  BUG-141: dir -Name blocked (-Name flag incorrectly treated as path argument)
  BUG-142: Parenthesized subexpressions blocked
           ((Get-Content file).Count, (echo hello).Length)
  BUG-143: Test-Path not in _COMMAND_ALLOWLIST

Security regression tests also verify that:
  - Pipe-to-interpreter is still blocked (echo | bash, cat | python3)
  - Backtick/dollar-paren subshells still blocked
  - Process substitution still blocked (diff <(cat f) <(cat g))
  - Deny-zone paths still blocked for all new/fixed commands
  - Parenthesized expressions with deny-zone inner paths are denied
  - (iex exploit).Length is denied (iex not in allowlist)
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
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
PROJECT_PATH = "project/src/output.txt"
PROJECT_DIR = "project/src/"


def allow(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "allow"


def deny(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# BUG-140: Remove-Item vs del — Stage 3 false-positive on path arguments
# ---------------------------------------------------------------------------

class TestBug140RemoveItemVsDel:
    """BUG-140: Remove-Item and del must behave identically.

    The root cause was Stage 3 obfuscation pre-scan running on full segment
    text including path arguments.  Paths containing words that match Stage 3
    patterns (e.g. 'exec', 'iex', 'source') caused false positives only when
    the corresponding P-21/P-11/P-22 patterns fired.

    Fix: allowlisted-verb segments skip non-critical Stage 3 patterns.
    """

    def test_remove_item_project_path_allowed(self, sg):
        """Remove-Item targeting the project folder is allowed."""
        assert allow(sg, f"remove-item {PROJECT_PATH}")

    def test_del_project_path_allowed(self, sg):
        """del targeting the project folder is allowed."""
        assert allow(sg, f"del {PROJECT_PATH}")

    def test_remove_item_and_del_identical_behavior(self, sg):
        """Remove-Item and del must give the same allow/deny result for any path."""
        paths = [
            PROJECT_PATH,
            "project/exec-scripts/file.txt",
            "project/source/main.py",
            "project/eval-results/data.csv",
            "project/iex-helper.txt",
        ]
        for p in paths:
            ri_result, _ = sg.sanitize_terminal_command(f"remove-item {p}", WS)
            del_result, _ = sg.sanitize_terminal_command(f"del {p}", WS)
            assert ri_result == del_result, (
                f"Inconsistency for path {p!r}: "
                f"remove-item={ri_result}, del={del_result}"
            )

    def test_remove_item_exec_path_allowed(self, sg):
        """Remove-Item with 'exec' in path is allowed (BUG-140 regression)."""
        assert allow(sg, "remove-item project/exec-scripts/file.txt")

    def test_del_exec_path_allowed(self, sg):
        """del with 'exec' in path is allowed."""
        assert allow(sg, "del project/exec-scripts/file.txt")

    def test_remove_item_source_subdir_allowed(self, sg):
        """Remove-Item project/source/main.py is allowed."""
        assert allow(sg, "remove-item project/source/main.py")

    def test_del_source_subdir_allowed(self, sg):
        """del project/source/main.py is allowed."""
        assert allow(sg, "del project/source/main.py")

    def test_remove_item_eval_path_allowed(self, sg):
        """Remove-Item project/eval-results/ is allowed."""
        assert allow(sg, "remove-item project/eval-results/")

    def test_remove_item_github_denied(self, sg):
        """Remove-Item targeting .github/ is denied."""
        assert deny(sg, "remove-item .github/hooks/secret.txt")

    def test_del_github_denied(self, sg):
        """del targeting .github/ is denied."""
        assert deny(sg, "del .github/config.json")

    def test_remove_item_vscode_denied(self, sg):
        """Remove-Item targeting .vscode/ is denied."""
        assert deny(sg, "remove-item .vscode/settings.json")

    def test_del_noagentzone_denied(self, sg):
        """del targeting NoAgentZone/ is denied."""
        assert deny(sg, "del NoAgentZone/secret.txt")

    # Security: pipe-to-interpreter must still be blocked even when the
    # leading verb is allowlisted (critical Stage 3 patterns always apply)
    def test_pipe_to_bash_still_denied(self, sg):
        """echo hello | bash is still denied (critical Stage 3 pattern P-16)."""
        assert deny(sg, "echo hello | bash")

    def test_pipe_to_python_still_denied(self, sg):
        """cat project/f.txt | python3 is still denied."""
        assert deny(sg, f"cat {PROJECT_PATH} | python3")

    def test_dollar_paren_subshell_denied(self, sg):
        """$( ) subshell in an arg is still denied (critical P-19)."""
        assert deny(sg, "remove-item $(malicious)")

    def test_backtick_subshell_denied(self, sg):
        """Backtick subshell in command is still denied (critical P-18)."""
        assert deny(sg, "del `rm -rf /`")


# ---------------------------------------------------------------------------
# BUG-141: dir -Name — flag not path argument
# ---------------------------------------------------------------------------

class TestBug141DirName:
    """BUG-141: dir -Name must be allowed.

    -Name is a PowerShell output-format parameter, not a path argument.
    Tokens starting with '-' are recognized as flags in both Step 5 and
    Step 8 of _validate_args; they are never added to the path-args list.
    """

    def test_dir_name_alone_allowed(self, sg):
        """dir -Name (no explicit path) is allowed."""
        assert allow(sg, "dir -Name")

    def test_dir_name_is_not_treated_as_path(self, sg):
        """dir with only output-format flags behaves the same as bare dir."""
        result_bare, _ = sg.sanitize_terminal_command("dir", WS)
        result_name, _ = sg.sanitize_terminal_command("dir -Name", WS)
        assert result_bare == result_name, (
            f"dir and 'dir -Name' must behave identically from the same CWD; "
            f"bare={result_bare}, -Name={result_name}"
        )

    def test_dir_name_with_project_path_allowed(self, sg):
        """dir -Name project/ is allowed."""
        assert allow(sg, "dir -Name project/")

    def test_dir_name_with_project_subdir_allowed(self, sg):
        """dir -Name project/src/ is allowed."""
        assert allow(sg, "dir -Name project/src/")

    def test_dir_name_github_denied(self, sg):
        """dir -Name .github/ is denied (deny zone)."""
        assert deny(sg, "dir -Name .github/")

    def test_dir_name_vscode_denied(self, sg):
        """dir -Name .vscode/ is denied (deny zone)."""
        assert deny(sg, "dir -Name .vscode/")

    def test_dir_multiple_format_flags_allowed(self, sg):
        """dir -Name -Force combines multiple output-format flags — allowed."""
        assert allow(sg, "dir -Name -Force")

    def test_dir_filter_flag_allowed(self, sg):
        """dir -Name -Filter *.py is allowed (wildcard in flag value)."""
        assert allow(sg, "dir -Name -Filter *.py")


# ---------------------------------------------------------------------------
# BUG-142: Parenthesized subexpressions — (cmd).Property
# ---------------------------------------------------------------------------

class TestBug142ParenSubexpressions:
    """BUG-142: (Get-Content file).Count and similar expressions must be allowed.

    The outer parentheses cause the tokenizer to produce a verb of '(Get-Content'
    which is not in the allowlist.  Fix: detect (inner_cmd).property patterns and
    unwrap them before verb extraction and Stage 3 analysis.
    """

    def test_get_content_dot_count_allowed(self, sg):
        """(Get-Content project/file.txt).Count is allowed."""
        assert allow(sg, "(Get-Content project/file.txt).Count")

    def test_echo_dot_length_allowed(self, sg):
        """(echo hello).Length is allowed."""
        assert allow(sg, "(echo hello).Length")

    def test_get_content_dot_length_allowed(self, sg):
        """(Get-Content project/file.txt).Length is allowed."""
        assert allow(sg, "(Get-Content project/file.txt).Length")

    def test_echo_dot_count_allowed(self, sg):
        """(echo test).Count is allowed."""
        assert allow(sg, "(echo test).Count")

    def test_chained_property_access_allowed(self, sg):
        """(Get-Content project/file.txt).Count.ToString() — chained access allowed."""
        assert allow(sg, "(Get-Content project/file.txt).Count.ToString")

    def test_get_content_deny_zone_denied(self, sg):
        """(Get-Content .github/secret).Count is denied (deny zone path)."""
        assert deny(sg, "(Get-Content .github/secret).Count")

    def test_get_content_vscode_denied(self, sg):
        """(Get-Content .vscode/settings.json).Length is denied."""
        assert deny(sg, "(Get-Content .vscode/settings.json).Length")

    def test_get_content_noagentzone_denied(self, sg):
        """(Get-Content NoAgentZone/secret).Count is denied."""
        assert deny(sg, "(Get-Content NoAgentZone/secret).Count")

    def test_iex_in_parens_denied(self, sg):
        """(iex exploit).Length is denied — iex is not in the allowlist."""
        assert deny(sg, "(iex exploit).Length")

    def test_invoke_expression_in_parens_denied(self, sg):
        """(Invoke-Expression exploit).Count is denied."""
        assert deny(sg, "(Invoke-Expression exploit).Count")

    def test_dollar_paren_not_confused(self, sg):
        """$($malicious).Count is denied — $( is a subshell (P-19), not grouping."""
        assert deny(sg, "$($malicious).Count")

    def test_process_substitution_still_denied(self, sg):
        """diff <(cat f) <(cat g) is still denied (process substitution P-28)."""
        assert deny(sg, "diff <(cat f) <(cat g)")


# ---------------------------------------------------------------------------
# BUG-143: Test-Path added to allowlist
# ---------------------------------------------------------------------------

class TestBug143TestPath:
    """BUG-143: Test-Path must be allowed for paths inside the project folder.

    Test-Path is a read-only PowerShell diagnostic cmdlet that checks whether
    a path exists.  It was absent from _COMMAND_ALLOWLIST.  Added to Category G
    (read-only file inspection) with path_args_restricted=True.
    """

    def test_test_path_project_dir_allowed(self, sg):
        """Test-Path project/ is allowed."""
        assert allow(sg, "Test-Path project/")

    def test_test_path_project_git_allowed(self, sg):
        """Test-Path project/.git is allowed (read-only existence check)."""
        assert allow(sg, "Test-Path project/.git")

    def test_test_path_project_src_allowed(self, sg):
        """Test-Path project/src/ is allowed."""
        assert allow(sg, "Test-Path project/src/")

    def test_test_path_project_file_allowed(self, sg):
        """Test-Path project/pyproject.toml is allowed."""
        assert allow(sg, "Test-Path project/pyproject.toml")

    def test_test_path_github_denied(self, sg):
        """Test-Path .github/hooks is denied (deny zone)."""
        assert deny(sg, "Test-Path .github/hooks")

    def test_test_path_vscode_denied(self, sg):
        """Test-Path .vscode/settings.json is denied."""
        assert deny(sg, "Test-Path .vscode/settings.json")

    def test_test_path_noagentzone_denied(self, sg):
        """Test-Path NoAgentZone/ is denied."""
        assert deny(sg, "Test-Path NoAgentZone/")

    def test_test_path_in_allowlist(self, sg):
        """test-path must appear in _COMMAND_ALLOWLIST."""
        assert "test-path" in sg._COMMAND_ALLOWLIST

    def test_test_path_path_args_restricted(self, sg):
        """test-path must have path_args_restricted=True."""
        rule = sg._COMMAND_ALLOWLIST["test-path"]
        assert rule.path_args_restricted is True

    def test_test_path_no_arbitrary_paths(self, sg):
        """test-path must have allow_arbitrary_paths=False."""
        rule = sg._COMMAND_ALLOWLIST["test-path"]
        assert rule.allow_arbitrary_paths is False


# ---------------------------------------------------------------------------
# Additional security regression: critical Stage 3 patterns always active
# ---------------------------------------------------------------------------

class TestCriticalStage3AlwaysActive:
    """Verify that critical Stage 3 patterns cannot be bypassed by using an
    allowlisted verb as the leading command in a chained or piped expression.
    """

    def test_allowlisted_verb_with_pipe_to_bash_denied(self, sg):
        """rm project/f.txt | bash — pipe-to-bash denied even after allowlisted rm."""
        assert deny(sg, "rm project/f.txt | bash")

    def test_allowlisted_verb_with_pipe_to_iex_denied(self, sg):
        """del project/f.txt | iex — pipe-to-iex denied."""
        assert deny(sg, "del project/f.txt | iex")

    def test_allowlisted_verb_with_dollar_paren_denied(self, sg):
        """cat project/f.txt; $( malicious ) — $( subshell denied."""
        assert deny(sg, "cat project/f.txt; $(malicious)")

    def test_process_substitution_denied(self, sg):
        """diff <(cat project/a.txt) <(cat project/b.txt) denied (process substitution)."""
        assert deny(sg, "diff <(cat project/a.txt) <(cat project/b.txt)")

    def test_paren_expr_with_iex_inner_denied(self, sg):
        """(iex exploit).Property — iex not allowlisted, denied at verb check."""
        assert deny(sg, "(iex exploit).Property")
