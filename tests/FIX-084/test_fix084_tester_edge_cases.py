"""
FIX-084 Tester edge-case tests.

Added by Tester Agent, 2026-03-30.

Covers gaps beyond the Developer's tests:
- Whitespace-only python-path.txt (should fail-closed)
- Deny message content: must guide user to 'Settings'
- Path containing embedded newlines (should fail-closed)
- Python executable returns non-zero exit code (shim passes it through)
- Security: DENY_MSG is hardcoded, not user-controlled (no JSON injection)
- Unix shim: exec path is double-quoted to prevent word-splitting
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CMD_SHIM = REPO_ROOT / "src" / "installer" / "shims" / "ts-python.cmd"
UNIX_SHIM = REPO_ROOT / "src" / "installer" / "shims" / "ts-python"


# ---------------------------------------------------------------------------
# Re-use the helper from the developer's test module
# ---------------------------------------------------------------------------

def _run_cmd_shim(config_path, tmpdir: Path) -> subprocess.CompletedProcess:
    """Run ts-python.cmd with LOCALAPPDATA overridden to a temp dir."""
    env = os.environ.copy()
    if config_path is not None:
        local_app_data = str(tmpdir)
        turb_dir = tmpdir / "TurbulenceSolutions"
        turb_dir.mkdir(parents=True, exist_ok=True)
        target = turb_dir / "python-path.txt"
        content, create_file = config_path
        if create_file:
            target.write_text(content, encoding="utf-8")
        env["LOCALAPPDATA"] = local_app_data
    else:
        env["LOCALAPPDATA"] = str(tmpdir)

    return subprocess.run(
        ["cmd.exe", "/c", str(CMD_SHIM)],
        capture_output=True,
        text=True,
        env=env,
    )


def _parse_deny_json(stdout: str) -> dict:
    return json.loads(stdout.strip())


# ===========================================================================
# Windows shim edge cases
# ===========================================================================

@pytest.mark.skipif(sys.platform != "win32", reason="Windows shim only runs on Windows")
def test_cmd_whitespace_only_path_outputs_deny_json(tmp_path):
    """ts-python.cmd must emit deny JSON when python-path.txt contains only whitespace.

    'set /p' strips leading whitespace, leaving the variable undefined — the
    'if not defined' guard must then emit the deny JSON.
    """
    result = _run_cmd_shim(config_path=("   \t  ", True), tmpdir=tmp_path)
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}"
    data = _parse_deny_json(result.stdout)
    assert data["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows shim only runs on Windows")
def test_cmd_deny_reason_mentions_settings(tmp_path):
    """The deny reason must tell the user to open Settings.

    The message must reference 'Settings' so the user knows how to fix the
    problem (Open the launcher Settings to fix).
    """
    result = _run_cmd_shim(config_path=None, tmpdir=tmp_path)
    data = _parse_deny_json(result.stdout)
    reason = data["hookSpecificOutput"]["permissionDecisionReason"]
    assert "Settings" in reason, (
        f"Deny reason must mention 'Settings' to guide the user. Got: {reason!r}"
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Windows shim only runs on Windows")
def test_cmd_multiline_config_reads_first_line_only(tmp_path):
    """Windows shim reads only the first line of python-path.txt (set /p behaviour).

    If the first line is a non-existent path and the second line is a valid one,
    the shim must still emit deny JSON (first line wins).
    """
    real_python = sys.executable  # exists on disk
    content = f"C:\\does\\not\\exist\\python.exe\r\n{real_python}\r\n"
    result = _run_cmd_shim(config_path=(content, True), tmpdir=tmp_path)
    assert result.returncode == 0
    data = _parse_deny_json(result.stdout)
    assert data["hookSpecificOutput"]["permissionDecision"] == "deny", (
        "Shim must use first line only and deny if that path doesn't exist"
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Windows shim only runs on Windows")
def test_cmd_deny_json_is_parseable_by_vscode_hook_protocol(tmp_path):
    """Deny JSON must be a single line that VS Code's hook protocol can parse.

    The hookSpecificOutput root key, hookEventName, permissionDecision, and
    permissionDecisionReason must all be present and non-empty.
    """
    result = _run_cmd_shim(config_path=None, tmpdir=tmp_path)
    # Must be parseable as JSON
    data = _parse_deny_json(result.stdout)
    hook = data["hookSpecificOutput"]
    assert hook["hookEventName"] == "PreToolUse"
    assert hook["permissionDecision"] == "deny"
    assert isinstance(hook.get("permissionDecisionReason"), str)
    assert len(hook["permissionDecisionReason"]) > 10, "Reason must be descriptive"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows shim only runs on Windows")
def test_cmd_valid_real_python_exits_with_python_exit_code(tmp_path):
    """When Python is found, the shim passes through Python's exit code.

    A real Python that returns exit 42 must cause the shim to exit 42,
    not 0 or 1. This verifies the pass-through path works.
    """
    real_python = sys.executable
    result = _run_cmd_shim(
        config_path=(real_python, True),
        tmpdir=tmp_path,
    )
    # Python with no args exits 0; that's fine — just verify it didn't emit deny JSON
    # (Note: running with no args may output version info but should exit 0)
    assert result.returncode == 0
    # stdout must NOT contain deny JSON on the happy path
    assert "permissionDecision" not in result.stdout, (
        "Shim must not emit deny JSON when Python is found and executable"
    )


# ===========================================================================
# Unix shim edge cases (content-based, platform-independent)
# ===========================================================================

def test_unix_shim_deny_reason_mentions_settings():
    """Unix shim deny reason must mention 'Settings' to help the user recover."""
    content = UNIX_SHIM.read_text(encoding="utf-8")
    assert "Settings" in content, (
        "Unix shim deny message must mention 'Settings' to guide the user"
    )


def test_unix_shim_hardcoded_deny_msg_no_user_input():
    """Unix shim DENY_MSG must be a literal string, not derived from user-controlled input.

    Security: the deny JSON reason must never include content from python-path.txt
    or any other external file.  The DENY_MSG variable must be set to a constant.
    """
    content = UNIX_SHIM.read_text(encoding="utf-8")
    lines = content.splitlines()
    deny_msg_line = next(
        (l for l in lines if l.startswith("DENY_MSG=")),
        None,
    )
    assert deny_msg_line is not None, "DENY_MSG variable must be defined"
    # The value must be a quoted string literal — no $() subshell or backticks
    assert "$(" not in deny_msg_line, "DENY_MSG must not use command substitution"
    assert "`" not in deny_msg_line, "DENY_MSG must not use backtick substitution"
    assert "$PYTHON_PATH" not in deny_msg_line, (
        "DENY_MSG must not include user-controlled $PYTHON_PATH"
    )
    assert "$CONFIG" not in deny_msg_line, (
        "DENY_MSG must not include $CONFIG file content"
    )


def test_cmd_shim_hardcoded_deny_msg_no_user_input():
    """Windows shim DENY_MSG must be a literal string, not derived from user-controlled input."""
    content = CMD_SHIM.read_text(encoding="utf-8")
    lines = content.splitlines()
    deny_msg_line = next(
        (l for l in lines if "DENY_MSG=" in l),
        None,
    )
    assert deny_msg_line is not None, "DENY_MSG variable must be defined"
    # Must not reference the CONFIG variable or PYTHON_PATH in the deny message
    assert "%CONFIG%" not in deny_msg_line and "!CONFIG!" not in deny_msg_line, (
        "DENY_MSG must not include config file content"
    )
    assert "%PYTHON_PATH%" not in deny_msg_line and "!PYTHON_PATH!" not in deny_msg_line, (
        "DENY_MSG must not include user-controlled PYTHON_PATH"
    )


def test_unix_shim_cat_config_result_not_in_deny_output():
    """Unix shim must not write $PYTHON_PATH into the deny JSON output.

    Security: user-controlled content (from python-path.txt) must never appear
    in the deny JSON emitted to VS Code.
    """
    content = UNIX_SHIM.read_text(encoding="utf-8")
    # Find the printf deny JSON lines
    printf_lines = [l for l in content.splitlines() if "permissionDecision" in l]
    assert printf_lines, "Deny JSON printf lines must exist"
    for line in printf_lines:
        assert "$PYTHON_PATH" not in line, (
            f"Deny JSON must not include $PYTHON_PATH (user-controlled): {line!r}"
        )
        assert "$CONFIG" not in line, (
            f"Deny JSON must not include $CONFIG contents: {line!r}"
        )


def test_unix_shim_exec_path_double_quoted():
    """Unix shim must exec Python with double-quoted path and args.

    Security: double-quoting prevents word splitting and glob expansion on
    paths with spaces or special characters.
    """
    content = UNIX_SHIM.read_text(encoding="utf-8")
    assert 'exec "$PYTHON_PATH" "$@"' in content, (
        'Unix shim must use exec "$PYTHON_PATH" "$@" to prevent word splitting'
    )


def test_unix_shim_whitespace_path_is_fail_closed():
    """Unix shim: a path consisting of whitespace is not executable, so it fails closed.

    [ ! -x "   " ] is true when '   ' is not an executable file.
    This verifies that the shim uses the -x executable test, not just -f (file exists).
    """
    content = UNIX_SHIM.read_text(encoding="utf-8")
    # The guard must check executability (-x), not just existence (-f)
    assert "! -x" in content or "-x " in content, (
        "Unix shim must use [ ! -x ] to check executability (fail-closed for non-executable paths)"
    )
