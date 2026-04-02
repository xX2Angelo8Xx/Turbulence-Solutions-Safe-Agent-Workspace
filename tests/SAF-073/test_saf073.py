"""
SAF-073 — Harden require-approval.sh fallback hook

Tests verify that the hardened terminal command handler in require-approval.sh
denies: env-var exfiltration, command substitution, obfuscation patterns, and
sensitive system paths. Safe commands continue to receive "ask".

Uses subprocess with Git Bash to invoke the real bash script so the actual
regex logic is exercised end-to-end.
"""
import json
import os
import platform
import subprocess
import pytest

# ---------------------------------------------------------------------------
# Helper — locate bash and the hook script
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
    """Pipe a JSON terminal-command payload to require-approval.sh, return parsed JSON."""
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
        f"Hook exited with code {result.returncode}. stderr: {result.stderr.decode()}"
    )
    raw = result.stdout.decode().strip()
    return json.loads(raw)


def _decision(command: str) -> str:
    return _run_hook(command)["hookSpecificOutput"]["permissionDecision"]


# ---------------------------------------------------------------------------
# Skip entire module if bash is unavailable
# ---------------------------------------------------------------------------
pytestmark = pytest.mark.skipif(
    BASH is None,
    reason="bash not found — cannot run bash hook tests on this platform",
)


# ---------------------------------------------------------------------------
# TC-SAF-073-01  Environment variable exfiltration — $env:USERNAME (PowerShell)
# ---------------------------------------------------------------------------
def test_deny_env_var_powershell():
    assert _decision("echo $env:USERNAME") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-02  Environment variable exfiltration — ${env:SECRET} (PowerShell)
# ---------------------------------------------------------------------------
def test_deny_env_var_powershell_braced():
    assert _decision("echo ${env:SECRET}") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-03  Environment variable exfiltration — $HOME (Unix)
# ---------------------------------------------------------------------------
def test_deny_env_var_home():
    assert _decision("cat $HOME/.ssh/id_rsa") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-04  Command substitution — $(whoami)
# ---------------------------------------------------------------------------
def test_deny_command_substitution_dollar_paren():
    assert _decision("echo $(whoami)") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-05  Command substitution — backtick `id`
# ---------------------------------------------------------------------------
def test_deny_command_substitution_backtick():
    assert _decision("echo `id`") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-06  Obfuscation — eval rm -rf
# ---------------------------------------------------------------------------
def test_deny_eval():
    assert _decision("eval rm -rf /") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-07  Obfuscation — base64 --decode
# ---------------------------------------------------------------------------
def test_deny_base64_decode():
    assert _decision("echo aGVsbG8= | base64 --decode") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-08  Sensitive system path — /etc/passwd
# ---------------------------------------------------------------------------
def test_deny_sensitive_path_etc():
    assert _decision("cat /etc/passwd") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-09  Sensitive system path — c:/users/angel/secret.txt
# ---------------------------------------------------------------------------
def test_deny_sensitive_path_windows_users():
    assert _decision("type c:/users/angel/secret.txt") == "deny"


# ---------------------------------------------------------------------------
# TC-SAF-073-10  Safe command — echo hello → ask (not deny)
# ---------------------------------------------------------------------------
def test_ask_safe_command():
    assert _decision("echo hello") == "ask"


# ---------------------------------------------------------------------------
# TC-SAF-073-11  Existing behavior — .github/ reference → deny
# ---------------------------------------------------------------------------
def test_deny_github_folder_regression():
    assert _decision("ls .github/hooks") == "deny"
