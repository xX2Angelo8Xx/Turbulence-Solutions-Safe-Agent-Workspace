"""
FIX-084: Tests that ts-python shim outputs deny JSON on all error paths.

The shim must output a valid hookSpecificOutput deny JSON to stdout when:
- python-path.txt does not exist
- python-path.txt exists but is empty
- python-path.txt points to a non-existent executable

Tests for the Windows shim (ts-python.cmd) execute it via cmd.exe.
Tests for the Unix shim (ts-python) verify the script content/logic since
we cannot run a /bin/sh script on Windows CI without additional tooling.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CMD_SHIM = REPO_ROOT / "src" / "installer" / "shims" / "ts-python.cmd"
UNIX_SHIM = REPO_ROOT / "src" / "installer" / "shims" / "ts-python"

EXPECTED_HOOK_EVENT = "PreToolUse"
EXPECTED_DECISION = "deny"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_cmd_shim(config_path: str | None, tmpdir: Path) -> subprocess.CompletedProcess:
    """
    Run ts-python.cmd with LOCALAPPDATA overridden so it reads from a
    test-specific TurbulenceSolutions/python-path.txt.  We set LOCALAPPDATA to
    a temp dir that we control so the real user config is never touched.
    """
    env = os.environ.copy()
    if config_path is not None:
        # config_path is already the full path to python-path.txt;
        # the shim appends \TurbulenceSolutions\python-path.txt to LOCALAPPDATA,
        # so we put python-path.txt at that exact sub-path.
        local_app_data = str(tmpdir)
        turb_dir = tmpdir / "TurbulenceSolutions"
        turb_dir.mkdir(parents=True, exist_ok=True)
        target = turb_dir / "python-path.txt"
        # config_path is (content, exists) tuple
        content, create_file = config_path
        if create_file:
            target.write_text(content, encoding="utf-8")
        env["LOCALAPPDATA"] = local_app_data
    else:
        # No config provided — point LOCALAPPDATA to an empty tmpdir so the
        # file is definitely absent.
        env["LOCALAPPDATA"] = str(tmpdir)

    result = subprocess.run(
        ["cmd.exe", "/c", str(CMD_SHIM)],
        capture_output=True,
        text=True,
        env=env,
    )
    return result


def _parse_deny_json(stdout: str) -> dict:
    """Parse the deny JSON from shim stdout, allowing for trailing whitespace."""
    line = stdout.strip()
    return json.loads(line)


# ---------------------------------------------------------------------------
# Windows shim tests (requires cmd.exe — Windows only)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(sys.platform != "win32", reason="Windows shim only runs on Windows")
def test_cmd_missing_config_outputs_deny_json(tmp_path):
    """ts-python.cmd must output deny JSON when python-path.txt does not exist."""
    result = _run_cmd_shim(config_path=None, tmpdir=tmp_path)
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}"
    data = _parse_deny_json(result.stdout)
    assert "hookSpecificOutput" in data
    assert data["hookSpecificOutput"]["permissionDecision"] == EXPECTED_DECISION


@pytest.mark.skipif(sys.platform != "win32", reason="Windows shim only runs on Windows")
def test_cmd_empty_config_outputs_deny_json(tmp_path):
    """ts-python.cmd must output deny JSON when python-path.txt is empty."""
    result = _run_cmd_shim(config_path=("", True), tmpdir=tmp_path)
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}"
    data = _parse_deny_json(result.stdout)
    assert "hookSpecificOutput" in data
    assert data["hookSpecificOutput"]["permissionDecision"] == EXPECTED_DECISION


@pytest.mark.skipif(sys.platform != "win32", reason="Windows shim only runs on Windows")
def test_cmd_invalid_executable_outputs_deny_json(tmp_path):
    """ts-python.cmd must output deny JSON when python-path.txt points to a non-existent path."""
    result = _run_cmd_shim(
        config_path=(r"C:\does\not\exist\python.exe", True),
        tmpdir=tmp_path,
    )
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}"
    data = _parse_deny_json(result.stdout)
    assert "hookSpecificOutput" in data
    assert data["hookSpecificOutput"]["permissionDecision"] == EXPECTED_DECISION


@pytest.mark.skipif(sys.platform != "win32", reason="Windows shim only runs on Windows")
def test_cmd_deny_json_is_valid_and_correct_format(tmp_path):
    """The deny JSON must have hookEventName=PreToolUse, permissionDecision=deny, and a non-empty reason."""
    result = _run_cmd_shim(config_path=None, tmpdir=tmp_path)
    data = _parse_deny_json(result.stdout)
    hook_output = data["hookSpecificOutput"]
    assert hook_output["hookEventName"] == EXPECTED_HOOK_EVENT
    assert hook_output["permissionDecision"] == EXPECTED_DECISION
    reason = hook_output.get("permissionDecisionReason", "")
    assert len(reason) > 0, "permissionDecisionReason must not be empty"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows shim only runs on Windows")
def test_cmd_stderr_still_contains_diagnostic(tmp_path):
    """The shim must still emit diagnostic text to stderr (for debugging)."""
    result = _run_cmd_shim(config_path=None, tmpdir=tmp_path)
    assert "ERROR" in result.stderr, "stderr must contain diagnostic ERROR message"


# ---------------------------------------------------------------------------
# Unix shim content tests (platform-independent — test the script logic)
# ---------------------------------------------------------------------------

def test_unix_shim_denies_on_missing_config():
    """ts-python (Unix) script must contain deny JSON output for missing config case."""
    content = UNIX_SHIM.read_text(encoding="utf-8")
    # Verify deny JSON output path exists for missing config
    assert 'permissionDecision' in content
    assert '"deny"' in content


def test_unix_shim_denies_on_empty_config():
    """ts-python (Unix) script must handle the empty/non-executable path case with deny JSON."""
    content = UNIX_SHIM.read_text(encoding="utf-8")
    # Both error paths print deny JSON
    assert content.count('permissionDecision') >= 2, (
        "Expected at least 2 deny JSON outputs in Unix shim (missing file + non-executable)"
    )


def test_unix_shim_deny_json_format():
    """ts-python (Unix) must output hookSpecificOutput JSON matching the security gate protocol."""
    content = UNIX_SHIM.read_text(encoding="utf-8")
    assert "hookSpecificOutput" in content
    assert "PreToolUse" in content
    assert '"deny"' in content


def test_unix_shim_exits_zero_on_error():
    """ts-python (Unix) must exit 0 (not 1) when outputting deny JSON."""
    content = UNIX_SHIM.read_text(encoding="utf-8")
    # After each deny JSON printf, there must be an 'exit 0'
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if "permissionDecision" in line and "deny" in line:
            # Check the next non-empty line is 'exit 0'
            for j in range(i + 1, min(i + 4, len(lines))):
                stripped = lines[j].strip()
                if stripped:
                    assert stripped == "exit 0", (
                        f"After deny JSON at line {i+1}, expected 'exit 0' but got: {stripped!r}"
                    )
                    break


def test_unix_shim_stderr_diagnostic_present():
    """ts-python (Unix) must still emit diagnostic messages to stderr."""
    content = UNIX_SHIM.read_text(encoding="utf-8")
    assert ">&2" in content, "Unix shim must redirect diagnostic messages to stderr"
    assert "ERROR" in content
