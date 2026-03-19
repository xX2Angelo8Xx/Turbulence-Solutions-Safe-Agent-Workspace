"""Tests for SAF-024: Implement Generic Deny Messages

Verifies that _DENY_REASON contains the approved generic text and does NOT
reveal any restricted zone names (.github, .vscode, NoAgentZone).  Also
confirms the JSON response written to stdout by main() carries only the
generic message, not zone-specific text.

Test IDs:
  TST-601  test_deny_reason_is_generic_text
  TST-602  test_deny_reason_no_github_reference
  TST-603  test_deny_reason_no_vscode_reference
  TST-604  test_deny_reason_no_noagentzone_reference
  TST-605  test_deny_reason_no_blocked_prefix
  TST-606  test_main_stdout_generic_on_deny
  TST-607  test_main_stdout_no_zone_names_on_deny
  TST-608  test_sanitize_terminal_deny_reason_no_zone_names
  TST-609  test_deny_reason_constant_is_str
  TST-610  test_templates_deny_reason_matches
"""
from __future__ import annotations

import io
import json
import os
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
        "templates", "coding",
        ".github",
        "hooks",
        "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

# Templates version — for sync verification
_TEMPLATE_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "templates",
        "coding",
        ".github",
        "hooks",
        "scripts",
    )
)

WS = "c:/workspace"
_GENERIC_MESSAGE = "Access denied. This action has been blocked by the workspace security policy."
_ZONE_NAMES = (".github", ".vscode", "noagentzone", "NoAgentZone")


# ===========================================================================
# TST-601: _DENY_REASON contains the approved generic text
# ===========================================================================

def test_deny_reason_is_generic_text():
    # TST-601 — _DENY_REASON must equal the approved generic message exactly
    assert sg._DENY_REASON == _GENERIC_MESSAGE, (
        f"_DENY_REASON does not match the required generic message.\n"
        f"  Expected: {_GENERIC_MESSAGE!r}\n"
        f"  Actual:   {sg._DENY_REASON!r}"
    )


# ===========================================================================
# TST-602: _DENY_REASON does not reference .github
# ===========================================================================

def test_deny_reason_no_github_reference():
    # TST-602 — zone name ".github" must not appear in _DENY_REASON
    assert ".github" not in sg._DENY_REASON.lower(), (
        "_DENY_REASON reveals '.github' zone name to the agent"
    )


# ===========================================================================
# TST-603: _DENY_REASON does not reference .vscode
# ===========================================================================

def test_deny_reason_no_vscode_reference():
    # TST-603 — zone name ".vscode" must not appear in _DENY_REASON
    assert ".vscode" not in sg._DENY_REASON.lower(), (
        "_DENY_REASON reveals '.vscode' zone name to the agent"
    )


# ===========================================================================
# TST-604: _DENY_REASON does not reference NoAgentZone
# ===========================================================================

def test_deny_reason_no_noagentzone_reference():
    # TST-604 — zone name "noagentzone" must not appear in _DENY_REASON
    assert "noagentzone" not in sg._DENY_REASON.lower(), (
        "_DENY_REASON reveals 'NoAgentZone' zone name to the agent"
    )


# ===========================================================================
# TST-605: _DENY_REASON does not start with "BLOCKED:" (old format gone)
# ===========================================================================

def test_deny_reason_no_blocked_prefix():
    # TST-605 — the old "BLOCKED: .github, .vscode..." prefix must be gone
    assert not sg._DENY_REASON.startswith("BLOCKED:"), (
        "_DENY_REASON still starts with 'BLOCKED:' from the old format"
    )


# ===========================================================================
# TST-606: main() writes generic deny message to stdout
# ===========================================================================

def test_main_stdout_generic_on_deny(monkeypatch, capsys):
    # TST-606 — when a deny decision is reached, main() must output the
    # exact generic message (protection test via full pipeline)
    monkeypatch.setattr(sg, "verify_file_integrity", lambda: True)
    # Provide a payload that targets a deny zone to trigger deny
    payload = json.dumps({
        "tool_name": "read_file",
        "filePath": f"{WS}/.github/settings.json",
    })
    monkeypatch.setattr(sys, "stdin", io.StringIO(payload))
    monkeypatch.setattr(os, "getcwd", lambda: WS)

    with pytest.raises(SystemExit):
        sg.main()

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    reason = data["hookSpecificOutput"].get("permissionDecisionReason", "")
    assert reason == _GENERIC_MESSAGE, (
        f"main() deny reason does not match generic message.\n"
        f"  Expected: {_GENERIC_MESSAGE!r}\n"
        f"  Actual:   {reason!r}"
    )


# ===========================================================================
# TST-607: main() stdout deny message contains no zone names
# ===========================================================================

def test_main_stdout_no_zone_names_on_deny(monkeypatch, capsys):
    # TST-607 — the deny message sent to stdout must not contain any
    # restricted zone name (bypass-attempt test)
    monkeypatch.setattr(sg, "verify_file_integrity", lambda: True)
    payload = json.dumps({
        "tool_name": "run_in_terminal",
        "command": "cat .github/settings.json",
    })
    monkeypatch.setattr(sys, "stdin", io.StringIO(payload))
    monkeypatch.setattr(os, "getcwd", lambda: WS)

    with pytest.raises(SystemExit):
        sg.main()

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    reason = data["hookSpecificOutput"].get("permissionDecisionReason", "")
    reason_lower = reason.lower()
    for zone in _ZONE_NAMES:
        assert zone.lower() not in reason_lower, (
            f"Deny reason reveals restricted zone '{zone}' to the agent: {reason!r}"
        )


# ===========================================================================
# TST-608: sanitize_terminal_command deny reasons contain no zone names
# ===========================================================================

def test_sanitize_terminal_deny_reason_no_zone_names():
    # TST-608 — all deny reasons from sanitize_terminal_command must not
    # mention restricted zone names.  Tests several deny code paths.
    test_commands = [
        "iex malicious",                          # obfuscation pre-scan
        "unknown_tool_xyz",                       # not on allowlist
        f"cat {WS}/.github/secret",               # path zone check
        "python -m evil_module",                  # python -m check
        "git push --force",                       # denied flag
    ]
    for cmd in test_commands:
        decision, reason = sg.sanitize_terminal_command(cmd, WS)
        assert decision == "deny", f"Expected deny for {cmd!r}, got {decision!r}"
        if reason is not None:
            reason_lower = reason.lower()
            for zone in _ZONE_NAMES:
                assert zone.lower() not in reason_lower, (
                    f"Deny reason for {cmd!r} reveals zone '{zone}': {reason!r}"
                )


# ===========================================================================
# TST-609: _DENY_REASON is a plain string (not a tuple or multi-line)
# ===========================================================================

def test_deny_reason_constant_is_str():
    # TST-609 — _DENY_REASON must be a str, not a tuple or bytes
    assert isinstance(sg._DENY_REASON, str), (
        f"_DENY_REASON is not a str: {type(sg._DENY_REASON)}"
    )


# ===========================================================================
# TST-610: templates/coding/ security_gate.py _DENY_REASON is correct
# ===========================================================================

def test_templates_deny_reason_matches():
    # TST-610 — the templates version must contain the same generic _DENY_REASON
    # (sync check via file content inspection)
    template_gate = os.path.join(_TEMPLATE_SCRIPTS_DIR, "security_gate.py")
    assert os.path.isfile(template_gate), (
        f"templates/coding/ security_gate.py not found at: {template_gate}"
    )
    with open(template_gate, encoding="utf-8") as fh:
        content = fh.read()
    # The generic message must appear verbatim in the templates file
    assert _GENERIC_MESSAGE in content, (
        "templates/coding/ security_gate.py does not contain the generic _DENY_REASON message.\n"
        f"  Expected to find: {_GENERIC_MESSAGE!r}"
    )
    # Restricted zone names must NOT appear on the _DENY_REASON line
    for line in content.splitlines():
        if "_DENY_REASON" in line and "=" in line and not line.strip().startswith("#"):
            # This is the assignment line; ensure it has no zone names
            line_lower = line.lower()
            for zone in _ZONE_NAMES:
                assert zone.lower() not in line_lower, (
                    f"templates security_gate.py _DENY_REASON line references zone '{zone}': {line!r}"
                )
