"""SAF-069 — Tests for universal $env: exfiltration guard in _validate_args().

BUG-174: Commands with allow_arbitrary_paths=True (echo, write-output, etc.)
skipped the step-5 dollar-sign check, allowing $env:VARNAME to leak credentials.

Fix: A universal $env: guard was inserted BEFORE the step-5 path_args_restricted
gate so ALL commands are checked, regardless of allow_arbitrary_paths.

Tests:
  T01 - Write-Output $env:USERNAME is denied
  T02 - echo $env:GITHUB_TOKEN is denied
  T03 - Write-Host $env:PATH is denied
  T04 - echo "hello world" is allowed (no $env:)
  T05 - echo price is $5 is allowed ($ present but not $env:)
  T06 - write-output $ENV:SECRET is denied (case-insensitive)
  T07 - Get-Content $env:USERPROFILE\file.txt is denied (double-covered)
  T08 - echo ${env:USERNAME} (alternate PS syntax) is denied
  T09 - echo "$env:HOME/path" (embedded in quoted string) is denied
  T10 - echo hello is allowed (baseline safe command)
  T11 - Write-Output normal_text is allowed (allow_arbitrary_paths, no $env:)
  T12 - $environment (no colon) is allowed (no false positive)
  T13 - Multiple args where only one has $env: is denied
  T07 - Get-Content $env:USERPROFILE\\file.txt is denied (double-covered)
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

WS = "c:/workspace"


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# ---------------------------------------------------------------------------
# T01: Write-Output $env:USERNAME must be denied
# ---------------------------------------------------------------------------

def test_write_output_env_username_denied():
    """SAF-069/BUG-174: Write-Output $env:USERNAME must be denied."""
    decision, reason = sg.sanitize_terminal_command(
        "Write-Output $env:USERNAME", WS
    )
    assert decision == "deny", (
        f"Expected deny for Write-Output $env:USERNAME, got {decision!r}; reason={reason!r}"
    )


# ---------------------------------------------------------------------------
# T02: echo $env:GITHUB_TOKEN must be denied
# ---------------------------------------------------------------------------

def test_echo_env_github_token_denied():
    """SAF-069/BUG-174: echo $env:GITHUB_TOKEN must be denied."""
    decision, reason = sg.sanitize_terminal_command(
        "echo $env:GITHUB_TOKEN", WS
    )
    assert decision == "deny", (
        f"Expected deny for echo $env:GITHUB_TOKEN, got {decision!r}; reason={reason!r}"
    )


# ---------------------------------------------------------------------------
# T03: Write-Host $env:PATH must be denied
# ---------------------------------------------------------------------------

def test_write_host_env_path_denied():
    """SAF-069/BUG-174: Write-Host $env:PATH must be denied."""
    decision, reason = sg.sanitize_terminal_command(
        "Write-Host $env:PATH", WS
    )
    assert decision == "deny", (
        f"Expected deny for Write-Host $env:PATH, got {decision!r}; reason={reason!r}"
    )


# ---------------------------------------------------------------------------
# T04: echo "hello world" must be allowed (no $env:)
# ---------------------------------------------------------------------------

def test_echo_hello_world_allowed():
    """SAF-069: echo \"hello world\" must still be allowed."""
    decision, reason = sg.sanitize_terminal_command(
        'echo "hello world"', WS
    )
    assert decision != "deny", (
        f"Expected allow for echo hello world, got {decision!r}; reason={reason!r}"
    )


# ---------------------------------------------------------------------------
# T05: echo price is $5 must be allowed ($ but not $env:)
# ---------------------------------------------------------------------------

def test_echo_dollar_number_allowed():
    """SAF-069: $5 must NOT be caught by the $env: guard (avoid false positives)."""
    decision, reason = sg.sanitize_terminal_command(
        "echo price is $5", WS
    )
    assert decision != "deny", (
        f"Expected allow for 'echo price is $5', got {decision!r}; reason={reason!r}"
    )


# ---------------------------------------------------------------------------
# T06: write-output $ENV:SECRET must be denied (case-insensitive)
# ---------------------------------------------------------------------------

def test_write_output_env_upper_case_denied():
    """SAF-069/BUG-174: $ENV:SECRET (uppercase) must be caught by case-insensitive check."""
    decision, reason = sg.sanitize_terminal_command(
        "write-output $ENV:SECRET", WS
    )
    assert decision == "deny", (
        f"Expected deny for write-output $ENV:SECRET, got {decision!r}; reason={reason!r}"
    )


# ---------------------------------------------------------------------------
# T07: Get-Content $env:USERPROFILE\file.txt must be denied (double-covered)
# ---------------------------------------------------------------------------

def test_get_content_env_userprofile_denied():
    """SAF-069/BUG-174: $env:USERPROFILE path must be denied by universal guard."""
    decision, reason = sg.sanitize_terminal_command(
        r"Get-Content $env:USERPROFILE\file.txt", WS
    )
    assert decision == "deny", (
        f"Expected deny for Get-Content $env:USERPROFILE..., got {decision!r}; reason={reason!r}"
    )


# ---------------------------------------------------------------------------
# Tester edge cases (T08–T13)
# ---------------------------------------------------------------------------

# T08: Alternate PowerShell syntax ${env:USERNAME} must be denied
def test_echo_brace_env_syntax_denied():
    """SAF-069/T08: echo ${env:USERNAME} — alternate PS brace syntax must be denied."""
    decision, reason = sg.sanitize_terminal_command(
        "echo ${env:USERNAME}", WS
    )
    assert decision == "deny", (
        f"Expected deny for echo ${{env:USERNAME}}, got {decision!r}; reason={reason!r}"
    )


# T09: $env: embedded inside a quoted string must be denied
def test_echo_env_embedded_in_string_denied():
    """SAF-069/T09: echo \"$env:HOME/path\" — $env: embedded in string token must be denied."""
    decision, reason = sg.sanitize_terminal_command(
        'echo "$env:HOME/path"', WS
    )
    assert decision == "deny", (
        f"Expected deny for echo \"$env:HOME/path\", got {decision!r}; reason={reason!r}"
    )


# T10: echo hello (pure safe baseline) must be allowed
def test_echo_hello_allowed():
    """SAF-069/T10: echo hello — completely safe command must be allowed."""
    decision, reason = sg.sanitize_terminal_command("echo hello", WS)
    assert decision != "deny", (
        f"Expected allow for 'echo hello', got {decision!r}; reason={reason!r}"
    )


# T11: Write-Output with plain text (allow_arbitrary_paths command) must be allowed
def test_write_output_plain_text_allowed():
    """SAF-069/T11: Write-Output normal_text — allow_arbitrary_paths command with no $env: must pass."""
    decision, reason = sg.sanitize_terminal_command(
        "Write-Output normal_text", WS
    )
    assert decision != "deny", (
        f"Expected allow for Write-Output normal_text, got {decision!r}; reason={reason!r}"
    )


# T12: $environment (dollar-sign but no colon) must NOT be caught — avoid false positive
def test_echo_dollar_environment_no_colon_allowed():
    """SAF-069/T12: echo $environment — no colon means it is not an env-var token; must be allowed."""
    decision, reason = sg.sanitize_terminal_command(
        "echo $environment", WS
    )
    assert decision != "deny", (
        f"Expected allow for 'echo $environment' (no colon), got {decision!r}; reason={reason!r}"
    )


# T13: Multiple args where only one contains $env: must be denied
def test_multi_arg_one_env_var_denied():
    """SAF-069/T13: echo safe_word $env:SECRET another_word — deny when any single arg is $env:."""
    decision, reason = sg.sanitize_terminal_command(
        "echo safe_word $env:SECRET another_word", WS
    )
    assert decision == "deny", (
        f"Expected deny when one of multiple args contains $env:, got {decision!r}; reason={reason!r}"
    )
