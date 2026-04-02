"""
SAF-074 — Harden require-approval.ps1 fallback hook
Tests invoke the PowerShell script via subprocess on Windows.
BUG-176: Bash/PS1 fallback hooks share same vulnerabilities as Python gate.
"""
import json
import subprocess
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts" / "require-approval.ps1"
_WS_ROOT = Path(__file__).resolve().parents[2]


def run_ps1_hook(tool_name: str, command_or_path: str, ws_root: Path) -> str:
    """Invoke require-approval.ps1 with the given tool input and return the decision."""
    if tool_name in ("run_in_terminal", "terminal", "run_command"):
        payload = json.dumps({"tool_name": tool_name, "tool_input": {"command": command_or_path}})
    else:
        payload = json.dumps({"tool_name": tool_name, "tool_input": {"filePath": command_or_path}})

    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(_SCRIPT)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=str(ws_root),
        timeout=15,
    )
    raw = result.stdout.strip()
    output = json.loads(raw)
    return output["hookSpecificOutput"]["permissionDecision"]


# ---------------------------------------------------------------------------
# Environment variable exfiltration — must all be DENY
# ---------------------------------------------------------------------------

def test_env_username_deny():
    """$env:USERNAME must be denied."""
    decision = run_ps1_hook("run_in_terminal", "Write-Output $env:USERNAME", _WS_ROOT)
    assert decision == "deny", f"Expected deny, got {decision!r}"


def test_env_secret_curly_deny():
    """${env:SECRET} must be denied."""
    decision = run_ps1_hook("run_in_terminal", "echo ${env:SECRET}", _WS_ROOT)
    assert decision == "deny", f"Expected deny, got {decision!r}"


def test_home_dollar_deny():
    """$HOME must be denied."""
    decision = run_ps1_hook("run_in_terminal", "echo $HOME", _WS_ROOT)
    assert decision == "deny", f"Expected deny, got {decision!r}"


def test_home_curly_deny():
    """${HOME} must be denied."""
    decision = run_ps1_hook("run_in_terminal", "echo ${HOME}", _WS_ROOT)
    assert decision == "deny", f"Expected deny, got {decision!r}"


# ---------------------------------------------------------------------------
# Dynamic execution / command substitution — must all be DENY
# ---------------------------------------------------------------------------

def test_invoke_expression_deny():
    """Invoke-Expression must be denied."""
    decision = run_ps1_hook("run_in_terminal", 'Invoke-Expression "Get-Content secret.txt"', _WS_ROOT)
    assert decision == "deny", f"Expected deny, got {decision!r}"


def test_iex_deny():
    """iex must be denied."""
    decision = run_ps1_hook("run_in_terminal", 'iex "malicious"', _WS_ROOT)
    assert decision == "deny", f"Expected deny, got {decision!r}"


def test_dollar_paren_substitution_deny():
    """$(whoami) dollar-paren substitution must be denied."""
    decision = run_ps1_hook("run_in_terminal", "echo $(whoami)", _WS_ROOT)
    assert decision == "deny", f"Expected deny, got {decision!r}"


# ---------------------------------------------------------------------------
# .NET type accelerators — must all be DENY
# ---------------------------------------------------------------------------

def test_io_file_short_deny():
    """[IO.File]::ReadAllText must be denied."""
    decision = run_ps1_hook("run_in_terminal", '[IO.File]::ReadAllText("secret.txt")', _WS_ROOT)
    assert decision == "deny", f"Expected deny, got {decision!r}"


def test_system_io_file_deny():
    """[System.IO.File]::ReadAllText must be denied."""
    decision = run_ps1_hook("run_in_terminal", '[System.IO.File]::ReadAllText("secret.txt")', _WS_ROOT)
    assert decision == "deny", f"Expected deny, got {decision!r}"


def test_add_type_deny():
    """Add-Type must be denied."""
    decision = run_ps1_hook("run_in_terminal", 'Add-Type -TypeDefinition "..."', _WS_ROOT)
    assert decision == "deny", f"Expected deny, got {decision!r}"


# ---------------------------------------------------------------------------
# Obfuscation patterns — must all be DENY
# ---------------------------------------------------------------------------

def test_base64_decode_long_deny():
    """base64 --decode must be denied."""
    decision = run_ps1_hook("run_in_terminal", "echo payload | base64 --decode", _WS_ROOT)
    assert decision == "deny", f"Expected deny, got {decision!r}"


def test_base64_d_short_deny():
    """base64 -d must be denied."""
    decision = run_ps1_hook("run_in_terminal", "echo payload | base64 -d", _WS_ROOT)
    assert decision == "deny", f"Expected deny, got {decision!r}"


# ---------------------------------------------------------------------------
# Sensitive system paths — must all be DENY
# ---------------------------------------------------------------------------

def test_etc_passwd_deny():
    """cat /etc/passwd must be denied."""
    decision = run_ps1_hook("run_in_terminal", "cat /etc/passwd", _WS_ROOT)
    assert decision == "deny", f"Expected deny, got {decision!r}"


def test_windows_users_deny():
    """type c:/users/angel/secret.txt must be denied."""
    decision = run_ps1_hook("run_in_terminal", r"type c:\users\angel\secret.txt", _WS_ROOT)
    assert decision == "deny", f"Expected deny, got {decision!r}"


# ---------------------------------------------------------------------------
# Safe commands — must be ASK (no false positives)
# ---------------------------------------------------------------------------

def test_safe_echo_ask():
    """echo hello world should be ASK (not denied)."""
    decision = run_ps1_hook("run_in_terminal", "echo hello world", _WS_ROOT)
    assert decision == "ask", f"Expected ask, got {decision!r}"


# ---------------------------------------------------------------------------
# Existing behavior preserved — .github reference must still DENY
# ---------------------------------------------------------------------------

def test_github_folder_deny():
    """.github reference must still be denied (existing behavior)."""
    decision = run_ps1_hook("run_in_terminal", "ls .github/hooks/", _WS_ROOT)
    assert decision == "deny", f"Expected deny, got {decision!r}"
