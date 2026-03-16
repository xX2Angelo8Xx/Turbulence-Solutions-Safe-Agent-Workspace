"""Tests for Default-Project/.github/hooks/scripts/security_gate.py

Covers:
  - TST-033 to TST-081: 49 core tests (unit, integration, security, cross-platform)
  - TST-093 to TST-103: 11 additional edge-case tests required by Tester report
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

# ---------------------------------------------------------------------------
# Make security_gate importable from its non-standard location
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "Default-Project",
        ".github",
        "hooks",
        "scripts",
    )
)
_SCRIPT_PATH = os.path.join(_SCRIPTS_DIR, "security_gate.py")

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

# ---------------------------------------------------------------------------
# Workspace root constant used across zone / decide tests
# ---------------------------------------------------------------------------
WS = "/workspace"


# ===========================================================================
# parse_input  (TST-033 to TST-036)
# ===========================================================================

def test_parse_input_valid_json():
    data = sg.parse_input('{"tool_name": "read_file", "filePath": "project/x.py"}')
    assert isinstance(data, dict)
    assert data["tool_name"] == "read_file"


def test_parse_input_invalid_json():
    assert sg.parse_input("{bad json}") is None


def test_parse_input_not_a_dict():
    assert sg.parse_input("[1, 2, 3]") is None


def test_parse_input_empty_string():
    assert sg.parse_input("") is None


# ===========================================================================
# extract_tool_name  (TST-037 to TST-038)
# ===========================================================================

def test_extract_tool_name_present():
    assert sg.extract_tool_name({"tool_name": "read_file"}) == "read_file"


def test_extract_tool_name_missing():
    assert sg.extract_tool_name({}) == ""


# ===========================================================================
# extract_path  (TST-039 to TST-043)
# ===========================================================================

def test_extract_path_filepath():
    data = {"filePath": "project/x.py", "file_path": "other.py"}
    assert sg.extract_path(data) == "project/x.py"


def test_extract_path_file_path():
    data = {"file_path": "project/x.py"}
    assert sg.extract_path(data) == "project/x.py"


def test_extract_path_directory():
    data = {"directory": "project/src"}
    assert sg.extract_path(data) == "project/src"


def test_extract_path_none_when_absent():
    assert sg.extract_path({"tool_name": "read_file"}) is None


def test_extract_path_empty_value_skipped():
    data = {"filePath": "", "file_path": "project/x.py"}
    assert sg.extract_path(data) == "project/x.py"


# ===========================================================================
# normalize_path  (TST-044 to TST-049)
# ===========================================================================

def test_normalize_path_backslashes():
    # Single backslash → forward slash
    assert sg.normalize_path("project\\file.py") == "project/file.py"


def test_normalize_path_json_escaped_backslashes():
    # Two actual backslashes (\\) in the string → forward slash
    assert sg.normalize_path("project\\\\subdir") == "project/subdir"


def test_normalize_path_wsl_prefix():
    result = sg.normalize_path("/mnt/c/users/dev/project/x.py")
    assert result.startswith("c:/")


def test_normalize_path_gitbash_prefix():
    result = sg.normalize_path("/c/users/dev/project/x.py")
    assert result.startswith("c:/")


def test_normalize_path_lowercase():
    assert "A" not in sg.normalize_path("Project/File.Py")


def test_normalize_path_trailing_slash():
    result = sg.normalize_path("project/")
    assert not result.endswith("/")


# ===========================================================================
# build_response  (TST-050 to TST-052)
# ===========================================================================

def test_build_response_allow():
    resp = json.loads(sg.build_response("allow"))
    assert resp["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert resp["hookSpecificOutput"]["permissionDecision"] == "allow"
    assert "permissionDecisionReason" not in resp["hookSpecificOutput"]


def test_build_response_deny():
    resp = json.loads(sg.build_response("deny", "reason"))
    assert resp["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "permissionDecisionReason" in resp["hookSpecificOutput"]


def test_build_response_ask():
    resp = json.loads(sg.build_response("ask", "reason"))
    assert resp["hookSpecificOutput"]["permissionDecision"] == "ask"
    assert "permissionDecisionReason" in resp["hookSpecificOutput"]


# ===========================================================================
# get_zone  (TST-053 to TST-058)
# ===========================================================================

def test_zone_deny_github_path():
    assert sg.get_zone(f"{WS}/.github/secret", WS) == "deny"


def test_zone_deny_vscode_path():
    assert sg.get_zone(f"{WS}/.vscode/settings.json", WS) == "deny"


def test_zone_deny_noagentzone_path():
    assert sg.get_zone(f"{WS}/noagentzone/private.md", WS) == "deny"


def test_zone_allow_project_path():
    assert sg.get_zone(f"{WS}/project/main.py", WS) == "allow"


def test_zone_ask_unknown_path():
    assert sg.get_zone(f"{WS}/docs/readme.md", WS) == "deny"


def test_zone_deny_github_pattern_based():
    # Path under a different root — Method 1 won't match; Method 2 (pattern) must catch it
    assert sg.get_zone("/other-root/.github/secret", WS) == "deny"


# ===========================================================================
# Always-allow tools  (TST-059 to TST-061)
# ===========================================================================

def test_always_allow_ask_questions():
    # ask_questions must be allowed even when a blocked path is present in the input
    data = {"tool_name": "ask_questions", "filePath": f"{WS}/.github/secret"}
    assert sg.decide(data, WS) == "allow"


def test_always_allow_todo_write():
    data = {"tool_name": "TodoWrite", "filePath": f"{WS}/.github/x"}
    assert sg.decide(data, WS) == "allow"


def test_always_allow_subagent():
    data = {"tool_name": "runSubagent", "filePath": f"{WS}/.github/x"}
    assert sg.decide(data, WS) == "allow"


# ===========================================================================
# Terminal tools  (TST-062 to TST-065)
# ===========================================================================

def test_terminal_blocked_path_denied():
    data = {"tool_name": "run_in_terminal", "command": "cat .github/hooks/secret.sh"}
    assert sg.decide(data, WS) == "deny"


def test_terminal_no_blocked_path_asked():
    data = {"tool_name": "run_in_terminal", "command": "echo hello"}
    assert sg.decide(data, WS) == "allow"


def test_terminal_bypass_mixed_case():
    # Mixed-case .GITHUB must be lowercased and denied
    data = {"tool_name": "run_in_terminal", "command": "cat .GITHUB/hooks/secret.sh"}
    assert sg.decide(data, WS) == "deny"


def test_terminal_bypass_vscode_ref():
    data = {"tool_name": "run_in_terminal", "command": "cat .vscode/settings.json"}
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# decide — exempt tools  (TST-066 to TST-069)
# ===========================================================================

def test_decide_exempt_tool_project_path_allowed():
    data = {"tool_name": "read_file", "filePath": f"{WS}/project/main.py"}
    assert sg.decide(data, WS) == "allow"


def test_decide_exempt_tool_github_path_denied():
    data = {"tool_name": "read_file", "filePath": f"{WS}/.github/secret"}
    assert sg.decide(data, WS) == "deny"


def test_decide_non_exempt_tool_always_asks():
    data = {"tool_name": "some_custom_tool", "filePath": f"{WS}/project/main.py"}
    assert sg.decide(data, WS) == "deny"


def test_decide_no_path_asks():
    data = {"tool_name": "read_file"}
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# Fail-closed behaviour  (TST-070 to TST-072)
# ===========================================================================

def test_fail_closed_on_malformed_input():
    # parse_input must return None for malformed JSON — caller returns deny
    assert sg.parse_input("{bad}") is None


def test_fail_closed_on_empty_input():
    assert sg.parse_input("") is None


def test_fail_closed_on_null_json():
    # JSON null (not a dict) → None → deny
    assert sg.parse_input("null") is None


# ===========================================================================
# Path-traversal / bypass  (TST-073 to TST-074)
# ===========================================================================

def test_path_traversal_bypass_attempt():
    # ../../.github must resolve and be denied
    data = {"tool_name": "read_file", "filePath": "project/../../.github/x"}
    assert sg.decide(data, WS) == "deny"


def test_json_escaped_github_path_denied():
    # Double-backslash path targeting .github must be denied after normalization
    data = {"tool_name": "read_file", "filePath": ".github\\\\secret"}
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# Cross-platform paths  (TST-075 to TST-078)
# ===========================================================================

def test_cross_platform_windows_path_zone():
    ws_win = sg.normalize_path("C:\\workspace")
    data = {"tool_name": "read_file", "filePath": "C:\\workspace\\project\\file.py"}
    assert sg.decide(data, ws_win) == "allow"


def test_cross_platform_windows_blocked_path():
    ws_win = sg.normalize_path("C:\\workspace")
    data = {"tool_name": "read_file", "filePath": "C:\\workspace\\.github\\secret"}
    assert sg.decide(data, ws_win) == "deny"


def test_cross_platform_wsl_path_allowed():
    ws_wsl = sg.normalize_path("/mnt/c/workspace")
    data = {"tool_name": "read_file", "filePath": "/mnt/c/workspace/project/file.py"}
    assert sg.decide(data, ws_wsl) == "allow"


def test_cross_platform_unix_path_denied():
    data = {"tool_name": "read_file", "filePath": "/home/user/.vscode/settings.json"}
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# Integration — run script as subprocess  (TST-079 to TST-081)
# ===========================================================================

def _run_script(stdin_text: str, timeout: int = 10) -> tuple[str, int]:
    result = subprocess.run(
        [sys.executable, _SCRIPT_PATH],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout.strip(), result.returncode


def test_integration_allow_response_format():
    payload = json.dumps({
        "tool_name": "read_file",
        "filePath": "project/main.py",
    })
    stdout, _ = _run_script(payload)
    resp = json.loads(stdout)
    assert resp["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert resp["hookSpecificOutput"]["permissionDecision"] in ("allow", "ask", "deny")


def test_integration_deny_response_format():
    stdout, _ = _run_script("{bad json}")
    resp = json.loads(stdout)
    assert resp["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "permissionDecisionReason" in resp["hookSpecificOutput"]


def test_integration_exit_code_always_zero():
    for payload in [
        "{bad json}",
        "null",
        "",
        '{"tool_name":"read_file","filePath":"project/x.py"}',
    ]:
        _, code = _run_script(payload)
        assert code == 0, f"Expected exit code 0, got {code} for input: {payload!r}"


# ===========================================================================
# Edge-case tests (Tester-required additions)  (TST-093 to TST-103)
# ===========================================================================

def test_null_byte_in_path():
    # Null byte before a blocked segment must be stripped then denied
    data = {"tool_name": "read_file", "filePath": "project\x00/../.github/x"}
    assert sg.decide(data, WS) == "deny"


def test_unc_path_always_denied():
    # Windows UNC path targeting .github must be denied
    # Python string: \\server\share\.github\secret
    data = {"tool_name": "read_file", "filePath": "\\\\server\\share\\.github\\secret"}
    assert sg.decide(data, WS) == "deny"


def test_unc_path_project_asks():
    # Windows UNC path targeting project/ on an external server — outside ws_root;
    # in the 2-tier model all paths outside the workspace root are denied
    data = {"tool_name": "read_file", "filePath": "\\\\server\\share\\project\\file.py"}
    result = sg.decide(data, WS)
    assert result == "deny", f"2-tier model: UNC path to external server must be denied; got {result!r}"


def test_very_large_input_fails_closed():
    # Input larger than _STDIN_MAX_BYTES must return deny and exit 0
    large_input = "x" * (sg._STDIN_MAX_BYTES + 1)
    stdout, code = _run_script(large_input, timeout=30)
    resp = json.loads(stdout)
    assert resp["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert code == 0


def test_query_field_not_treated_as_path():
    # grep_search with query=".github/secret" must NOT trigger a deny from zone classification;
    # only the filePath is used for zone decisions.
    data = {
        "tool_name": "grep_search",
        "query": ".github/secret",
        "filePath": f"{WS}/project/main.py",
    }
    result = sg.decide(data, WS)
    assert result != "deny", "query field must not trigger zone deny"


def test_empty_tool_name():
    # Empty tool name is treated as unknown → falls through to path-based zone check
    data = {"tool_name": "", "filePath": f"{WS}/project/x.py"}
    result = sg.decide(data, WS)
    assert result in ("allow", "ask")


def test_tool_name_not_string():
    # Non-string tool_name must not raise; extract_tool_name returns ""
    data = {"tool_name": 42, "filePath": f"{WS}/project/x.py"}
    result = sg.decide(data, WS)
    assert result in ("allow", "ask", "deny")


def test_ws_root_with_trailing_slash():
    # get_zone must handle ws_root with a trailing slash correctly
    ws_trailing = WS + "/"
    assert sg.get_zone(f"{WS}/.github/secret", ws_trailing) == "deny"
    assert sg.get_zone(f"{WS}/project/x.py", ws_trailing) == "allow"


def test_response_hookSpecificOutput_exact_structure():
    # allow: no permissionDecisionReason key
    allow_resp = json.loads(sg.build_response("allow"))
    assert list(allow_resp.keys()) == ["hookSpecificOutput"]
    assert allow_resp["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert allow_resp["hookSpecificOutput"]["permissionDecision"] == "allow"
    assert "permissionDecisionReason" not in allow_resp["hookSpecificOutput"]
    # deny and ask: permissionDecisionReason must be present
    deny_resp = json.loads(sg.build_response("deny", "reason"))
    assert "permissionDecisionReason" in deny_resp["hookSpecificOutput"]
    ask_resp = json.loads(sg.build_response("ask", "reason"))
    assert "permissionDecisionReason" in ask_resp["hookSpecificOutput"]


def test_decide_project_sibling_prefix_bypass():
    # "project-evil" shares the prefix "project" but must NOT match the allow zone
    # The .github segment inside it must be caught by Method 2 pattern scan
    data = {"tool_name": "read_file", "filePath": "project-evil/.github/x"}
    assert sg.decide(data, WS) == "deny"


def test_normalize_deep_traversal():
    # Deep traversal that escapes workspace root must still be denied
    data = {"tool_name": "read_file", "filePath": "project/../../../../.github/x"}
    assert sg.decide(data, WS) == "deny"
