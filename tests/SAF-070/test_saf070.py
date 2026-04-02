"""SAF-070 — Regression tests for terminal bypass scenarios.

Covers all bypass vectors found in the security-hook-report and fixed in:
  - SAF-068: unquoted Windows path bypass (BUG-173)
  - SAF-069: $env: exfiltration in unrestricted commands (BUG-174)

Tests:
  --- Windows Path Bypass (SAF-068 fixes) ---
  T01 - Get-Content C:\\Users\\angel\\secret.txt unquoted -> deny
  T02 - Get-ChildItem C:\\Users unquoted -> deny
  T03 - Get-Content C:\\path\\to\\NoAgentZone\\file.txt unquoted -> deny
  T04 - Select-String -Path C:\\Users\\angel\\file.txt -Pattern secret unquoted -> deny
  T05 - type C:\\Windows\\System32\\drivers\\etc\\hosts unquoted -> deny
  T06 - cat C:\\Users\\angel\\.ssh\\id_rsa unquoted -> deny

  --- Env Var Exfiltration (SAF-069 fixes) ---
  T07 - Write-Output $env:USERNAME -> deny
  T08 - echo $env:GITHUB_TOKEN -> deny
  T09 - Write-Host $env:PATH -> deny
  T10 - write-output $ENV:SECRET case-insensitive -> deny
  T11 - echo ${env:USERNAME} brace syntax -> deny
  T12 - echo ${ENV:SECRET} brace + uppercase -> deny

  --- Legitimate Commands (must still be allowed) ---
  T13 - echo "hello world" -> allow
  T14 - echo price is 5 dollars -> allow
  T15 - Get-Content ./project-file.txt relative path in workspace -> allow
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
        "templates", "agent-workbench", ".github", "hooks", "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

# A fixed ws_root that makes all absolute C:\ paths fall outside the workspace
WS = "c:/workspace"


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# ===========================================================================
# Windows Path Bypass Tests (SAF-068 regression)
# ===========================================================================

def test_t01_unquoted_get_content_user_path_denied():
    """T01: Get-Content C:\\Users\\angel\\secret.txt (unquoted) must be denied.

    Regression for BUG-173 — shlex consumed backslashes so the path escaped
    zone-checking before the fix.
    """
    decision, reason = sg.sanitize_terminal_command(
        r"Get-Content C:\Users\angel\secret.txt", WS
    )
    assert decision == "deny", (
        f"Expected deny for unquoted Windows user path, got {decision!r}; reason={reason!r}"
    )


def test_t02_unquoted_get_childitem_users_denied():
    """T02: Get-ChildItem C:\\Users (unquoted directory) must be denied.

    Regression for BUG-173 — directory listings outside workspace must be blocked.
    """
    decision, reason = sg.sanitize_terminal_command(
        r"Get-ChildItem C:\Users", WS
    )
    assert decision == "deny", (
        f"Expected deny for unquoted Get-ChildItem on C:\\Users, got {decision!r}; reason={reason!r}"
    )


def test_t03_unquoted_get_content_no_agent_zone_denied():
    """T03: Get-Content C:\\path\\to\\NoAgentZone\\file.txt (unquoted) must be denied.

    Regression for BUG-173 — unquoted paths to denied zones must be blocked.
    """
    decision, reason = sg.sanitize_terminal_command(
        r"Get-Content C:\path\to\NoAgentZone\file.txt", WS
    )
    assert decision == "deny", (
        f"Expected deny for unquoted NoAgentZone path, got {decision!r}; reason={reason!r}"
    )


def test_t04_unquoted_select_string_flag_path_denied():
    """T04: Select-String -Path C:\\Users\\angel\\file.txt -Pattern secret (unquoted) must be denied.

    Regression for BUG-173 — paths in named flags must also be zone-checked.
    """
    decision, reason = sg.sanitize_terminal_command(
        r"Select-String -Path C:\Users\angel\file.txt -Pattern secret", WS
    )
    assert decision == "deny", (
        f"Expected deny for Select-String with unquoted Windows path, got {decision!r}; reason={reason!r}"
    )


def test_t05_unquoted_type_system_file_denied():
    """T05: type C:\\Windows\\System32\\drivers\\etc\\hosts (unquoted) must be denied.

    Regression for BUG-173 — system file access outside workspace must be blocked.
    """
    decision, reason = sg.sanitize_terminal_command(
        r"type C:\Windows\System32\drivers\etc\hosts", WS
    )
    assert decision == "deny", (
        f"Expected deny for type accessing system file, got {decision!r}; reason={reason!r}"
    )


def test_t06_unquoted_cat_ssh_key_denied():
    """T06: cat C:\\Users\\angel\\.ssh\\id_rsa (unquoted) must be denied.

    Regression for BUG-173 — SSH key access outside workspace must be blocked.
    """
    decision, reason = sg.sanitize_terminal_command(
        r"cat C:\Users\angel\.ssh\id_rsa", WS
    )
    assert decision == "deny", (
        f"Expected deny for cat on SSH key path, got {decision!r}; reason={reason!r}"
    )


# ===========================================================================
# Environment Variable Exfiltration Tests (SAF-069 regression)
# ===========================================================================

def test_t07_write_output_env_username_denied():
    """T07: Write-Output $env:USERNAME must be denied.

    Regression for BUG-174 — allow_arbitrary_paths commands must still catch $env:.
    """
    decision, reason = sg.sanitize_terminal_command(
        "Write-Output $env:USERNAME", WS
    )
    assert decision == "deny", (
        f"Expected deny for Write-Output $env:USERNAME, got {decision!r}; reason={reason!r}"
    )


def test_t08_echo_env_github_token_denied():
    """T08: echo $env:GITHUB_TOKEN must be denied.

    Regression for BUG-174 — env var exfiltration via echo must be blocked.
    """
    decision, reason = sg.sanitize_terminal_command(
        "echo $env:GITHUB_TOKEN", WS
    )
    assert decision == "deny", (
        f"Expected deny for echo $env:GITHUB_TOKEN, got {decision!r}; reason={reason!r}"
    )


def test_t09_write_host_env_path_denied():
    """T09: Write-Host $env:PATH must be denied.

    Regression for BUG-174 — Write-Host is an allow_arbitrary_paths command.
    """
    decision, reason = sg.sanitize_terminal_command(
        "Write-Host $env:PATH", WS
    )
    assert decision == "deny", (
        f"Expected deny for Write-Host $env:PATH, got {decision!r}; reason={reason!r}"
    )


def test_t10_write_output_env_upper_case_denied():
    """T10: write-output $ENV:SECRET (case-insensitive) must be denied.

    Regression for BUG-174 — $ENV: (uppercase) must be caught by case-insensitive check.
    """
    decision, reason = sg.sanitize_terminal_command(
        "write-output $ENV:SECRET", WS
    )
    assert decision == "deny", (
        f"Expected deny for write-output $ENV:SECRET, got {decision!r}; reason={reason!r}"
    )


def test_t11_echo_brace_env_username_denied():
    """T11: echo ${env:USERNAME} (PowerShell brace syntax) must be denied.

    Regression for BUG-174 — alternate brace syntax for env vars must be caught.
    """
    decision, reason = sg.sanitize_terminal_command(
        "echo ${env:USERNAME}", WS
    )
    assert decision == "deny", (
        f"Expected deny for echo ${{env:USERNAME}}, got {decision!r}; reason={reason!r}"
    )


def test_t12_echo_brace_env_upper_secret_denied():
    """T12: echo ${ENV:SECRET} (brace syntax, uppercase) must be denied.

    Regression for BUG-174 — combined brace + uppercase variant must be caught.
    """
    decision, reason = sg.sanitize_terminal_command(
        "echo ${ENV:SECRET}", WS
    )
    assert decision == "deny", (
        f"Expected deny for echo ${{ENV:SECRET}}, got {decision!r}; reason={reason!r}"
    )


# ===========================================================================
# Legitimate Commands — must continue to be allowed (no regression)
# ===========================================================================

def test_t13_echo_hello_world_allowed():
    """T13: echo "hello world" must still be allowed.

    No $env: reference, no absolute path — baseline safe command.
    """
    decision, reason = sg.sanitize_terminal_command(
        'echo "hello world"', WS
    )
    assert decision != "deny", (
        f"Expected allow for echo hello world, got {decision!r}; reason={reason!r}"
    )


def test_t14_echo_plain_text_allowed():
    """T14: echo price is 5 dollars must still be allowed.

    Plain text with no env var references or absolute paths.
    """
    decision, reason = sg.sanitize_terminal_command(
        "echo price is 5 dollars", WS
    )
    assert decision != "deny", (
        f"Expected allow for 'echo price is 5 dollars', got {decision!r}; reason={reason!r}"
    )


def test_t15_get_content_relative_path_allowed():
    """T15: Get-Content project/project-file.txt (relative path inside workspace) must be allowed.

    A path prefixed with the project folder name resolves to the allow zone.
    Uses the same pattern as SAF-068 T05 (project/README.md on WS = "c:/workspace").
    """
    decision, reason = sg.sanitize_terminal_command(
        "Get-Content project/project-file.txt", WS
    )
    assert decision == "allow", (
        f"Expected allow for Get-Content on project-relative path, "
        f"got {decision!r}; reason={reason!r}"
    )


# ===========================================================================
# Tester Edge Cases — additional scenarios not covered by the Developer
# ===========================================================================

def test_t16_mixed_case_path_denied():
    """T16: get-content C:\\USERS\\ANGEL\\secret.txt (mixed-case command + uppercase path) must be denied.

    Case-insensitive command matching must still catch paths regardless of
    the character case used in the drive or directory names.
    """
    decision, reason = sg.sanitize_terminal_command(
        r"get-content C:\USERS\ANGEL\secret.txt", WS
    )
    assert decision == "deny", (
        f"Expected deny for mixed-case unquoted Windows path, got {decision!r}; reason={reason!r}"
    )


def test_t17_double_backslash_path_denied():
    """T17: type C:\\\\Users\\\\angel\\\\file.txt (double-backslash escape) must be denied.

    After backslash normalization, C:\\\\Users... collapses to C:\\Users...
    (a valid absolute path) and must be denied.
    """
    decision, reason = sg.sanitize_terminal_command(
        "type C:\\\\Users\\\\angel\\\\file.txt", WS
    )
    assert decision == "deny", (
        f"Expected deny for double-backslash Windows path, got {decision!r}; reason={reason!r}"
    )


def test_t18_unc_path_denied():
    """T18: type \\\\\\\\server\\\\share\\\\file.txt (UNC path) must be denied.

    UNC paths are absolute network paths outside the workspace and must be
    blocked by zone checking (validated by SAF-068 T06 pattern).
    """
    decision, reason = sg.sanitize_terminal_command(
        r"type \\server\share\file.txt", WS
    )
    assert decision == "deny", (
        f"Expected deny for UNC path, got {decision!r}; reason={reason!r}"
    )


def test_t19_quoted_path_with_spaces_denied():
    """T19: Get-Content "C:\\Program Files\\secret.txt" (quoted path with spaces) must be denied.

    Quoted paths with spaces must still be caught — quoting is not a bypass.
    """
    decision, reason = sg.sanitize_terminal_command(
        r'Get-Content "C:\Program Files\secret.txt"', WS
    )
    assert decision == "deny", (
        f"Expected deny for quoted path with spaces, got {decision!r}; reason={reason!r}"
    )


def test_t20_chained_env_and_path_denied():
    """T20: Write-Output $env:USERNAME; Get-Content C:\\Users\\file.txt (chained) must be denied.

    A command chain combining env-var exfiltration and a path read outside
    the workspace must be denied — either violation is sufficient.
    """
    decision, reason = sg.sanitize_terminal_command(
        r"Write-Output $env:USERNAME; Get-Content C:\Users\file.txt", WS
    )
    assert decision == "deny", (
        f"Expected deny for chained env+path command, got {decision!r}; reason={reason!r}"
    )
