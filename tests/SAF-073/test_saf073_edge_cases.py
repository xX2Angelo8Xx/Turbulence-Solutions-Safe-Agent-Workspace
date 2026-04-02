"""
SAF-073 — Edge-case tests added by Tester Agent

Covers boundary conditions and potential bypass vectors beyond the Developer's
original 11 tests.  All tests use the same subprocess helper as test_saf073.py
so the *real* bash script is exercised end-to-end.
"""
import json
import os
import subprocess
import pytest

# ---------------------------------------------------------------------------
# Re-use the same bash / hook resolver as test_saf073.py
# ---------------------------------------------------------------------------
BASH_PATHS = [
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    "/bin/bash",
    "/usr/bin/bash",
]

HOOK_REL = os.path.join(
    "templates", "agent-workbench", ".github", "hooks", "scripts", "require-approval.sh"
)

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
HOOK_PATH = os.path.join(REPO_ROOT, HOOK_REL)


def _find_bash():
    for p in BASH_PATHS:
        if os.path.isfile(p):
            return p
    return None


BASH = _find_bash()


def _run_hook(command: str) -> dict:
    payload = json.dumps({
        "tool_name": "run_in_terminal",
        "tool_input": {"command": command},
    })
    result = subprocess.run(
        [BASH, HOOK_PATH],
        input=payload.encode(),
        capture_output=True,
        timeout=10,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"Hook exited {result.returncode}. stderr: {result.stderr.decode()}"
    )
    raw = result.stdout.decode().strip()
    return json.loads(raw)


def _decision(command: str) -> str:
    return _run_hook(command)["hookSpecificOutput"]["permissionDecision"]


pytestmark = pytest.mark.skipif(
    BASH is None,
    reason="bash not found — cannot run bash hook tests on this platform",
)


# ---------------------------------------------------------------------------
# TC-SAF-073-E01  Lowercase sensitive var — $home (already lowercase input)
# The hook lowercases input, so both $HOME and $home must deny.
# ---------------------------------------------------------------------------
def test_deny_env_var_home_lowercase():
    """$home (already lowercase) must be denied — env-var check is case-insensitive."""
    assert _decision("echo $home") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-E02  Curly-brace env var — ${HOME}
# ${HOME} is valid bash syntax equivalent to $HOME.  The pattern \$(home|...)
# does NOT match when braces are present — this exposes a security gap.
# Expected: deny (curly-brace form must also be blocked).
# ---------------------------------------------------------------------------
def test_deny_env_var_home_curly_braces():
    """${HOME} must be denied — curly-brace syntax is equivalent to $HOME."""
    assert _decision("echo ${HOME}") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-E03  Non-sensitive variable — $RANDOM
# $RANDOM is not in the sensitive-var list; should not be blocked.
# ---------------------------------------------------------------------------
def test_ask_non_sensitive_var_random():
    """$RANDOM is not sensitive — hook must NOT deny it (no false positive)."""
    assert _decision("echo $RANDOM") == "ask"


# ---------------------------------------------------------------------------
# TC-SAF-073-E04  printenv without $ — printenv HOME
# No $ prefix; hook should not deny (it cannot catch every env-print method).
# This is an acknowledged limitation, not a bug.
# ---------------------------------------------------------------------------
def test_ask_printenv_no_dollar():
    """printenv HOME has no $ — acceptable to return ask rather than deny."""
    assert _decision("printenv HOME") == "ask"


# ---------------------------------------------------------------------------
# TC-SAF-073-E05  Semicolons — echo hello; cat /etc/passwd
# Multi-statement commands must be evaluated as a whole; /etc/ path triggers deny.
# ---------------------------------------------------------------------------
def test_deny_semicolon_chained_sensitive_path():
    """Semicolons do not let dangerous commands hide after safe ones."""
    assert _decision("echo hello; cat /etc/passwd") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-E06  Piped base64 --decode
# Full-form flag already covered by existing tests; keep as integration check.
# ---------------------------------------------------------------------------
def test_deny_piped_base64_decode():
    """Piped command with base64 --decode must be denied."""
    assert _decision("echo aGVsbG8= | base64 --decode") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-E07  base64 -d short flag
# `base64 -d` is the POSIX short form and is functionally identical to
# `base64 --decode`.  The pattern `base64.*decode` does NOT match.
# Expected: deny (short flag must also be blocked).
# ---------------------------------------------------------------------------
def test_deny_base64_short_flag():
    """base64 -d must be denied — short flag is equivalent to --decode."""
    assert _decision("echo aGVsbG8= | base64 -d") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-E08  Safe relative path in project/ — no false positive
# A workspace-relative path should never trigger deny in terminal handler
# (terminal handler doesn't do path checks; anything not blocked → ask).
# ---------------------------------------------------------------------------
def test_ask_relative_project_path():
    """cat ./project/file.txt should return ask, not deny."""
    assert _decision("cat ./project/file.txt") == "ask"


# ---------------------------------------------------------------------------
# TC-SAF-073-E09  $PATH sensitive variable — deny
# ---------------------------------------------------------------------------
def test_deny_env_var_path():
    """$PATH is in the sensitive-var list and must be denied."""
    assert _decision("echo $PATH") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-E10  $TOKEN sensitive variable — deny
# ---------------------------------------------------------------------------
def test_deny_env_var_token():
    """$TOKEN is in the sensitive-var list and must be denied."""
    assert _decision("export $TOKEN") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-E11  eval without trailing space — eval(cmd)
# Tests the `eval(` branch of the obfuscation regex.
# ---------------------------------------------------------------------------
def test_deny_eval_paren():
    """eval( must be denied — parenthesised eval is an obfuscation vector."""
    assert _decision("eval(rm -rf /)") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-E12  Sensitive Windows path — c:/windows/system32
# ---------------------------------------------------------------------------
def test_deny_sensitive_windows_path():
    """c:/windows/system32 must be denied."""
    assert _decision("dir c:/windows/system32") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-E13  /tmp/ sensitive path
# ---------------------------------------------------------------------------
def test_deny_sensitive_path_tmp():
    """Writing to /tmp/ must be denied."""
    assert _decision("cp secret.txt /tmp/exfil") == "deny"
