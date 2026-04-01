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
