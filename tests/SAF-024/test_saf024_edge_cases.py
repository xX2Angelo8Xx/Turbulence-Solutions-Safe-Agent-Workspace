"""Edge-case tests for SAF-024: Implement Generic Deny Messages

Tester additions — covers tool types not exercised by developer tests and
verifies the full main() pipeline for every tool category.

Test IDs:
  TST-611  test_main_write_tool_deny_is_generic
  TST-612  test_main_multi_replace_deny_is_generic
  TST-613  test_main_get_errors_deny_is_generic
  TST-614  test_main_grep_search_deny_is_generic
  TST-615  test_main_semantic_search_deny_is_generic
  TST-616  test_sanitize_terminal_all_paths_generic
  TST-617  test_internal_comments_still_reference_zones
  TST-618  test_main_unknown_tool_deny_is_generic
  TST-619  test_deny_reason_same_both_copies
  TST-620  test_sanitize_terminal_f_string_prefixes_no_zone_names
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

import pytest

# ---------------------------------------------------------------------------
# Path setup — same as developer test
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "Default-Project",
        ".github",
        "hooks",
        "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

_TEMPLATE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "templates",
        "coding",
        ".github",
        "hooks",
        "scripts",
        "security_gate.py",
    )
)

WS = "c:/workspace"
_GENERIC_MESSAGE = "Access denied. This action has been blocked by the workspace security policy."
_ZONE_NAMES = (".github", ".vscode", "noagentzone", "NoAgentZone")


def _get_stdout_reason(monkeypatch, capsys, payload: dict) -> str:
    """Helper: run main() with the given payload and return the deny reason."""
    monkeypatch.setattr(sg, "verify_file_integrity", lambda: True)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setattr(os, "getcwd", lambda: WS)
    with pytest.raises(SystemExit):
        sg.main()
    data = json.loads(capsys.readouterr().out)
    return data["hookSpecificOutput"].get("permissionDecisionReason", "")


def _assert_no_zones(reason: str, ctx: str = "") -> None:
    """Assert that *reason* contains none of the restricted zone names."""
    reason_lower = reason.lower()
    for zone in _ZONE_NAMES:
        assert zone.lower() not in reason_lower, (
            f"{ctx}Deny reason reveals restricted zone '{zone}': {reason!r}"
        )


# ===========================================================================
# TST-611: write tool targeting .vscode → main() JSON output is generic
# ===========================================================================

def test_main_write_tool_deny_is_generic(monkeypatch, capsys):
    # TST-611 — create_file targeting .vscode must produce a generic deny
    payload = {
        "tool_name": "create_file",
        "filePath": f"{WS}/.vscode/settings.json",
    }
    reason = _get_stdout_reason(monkeypatch, capsys, payload)
    assert reason == _GENERIC_MESSAGE, (
        f"write-tool deny reason is not the generic message.\n"
        f"  Expected: {_GENERIC_MESSAGE!r}\n"
        f"  Actual:   {reason!r}"
    )
    _assert_no_zones(reason, "write tool: ")


# ===========================================================================
# TST-612: multi_replace_string_in_file targeting .github → generic deny
# ===========================================================================

def test_main_multi_replace_deny_is_generic(monkeypatch, capsys):
    # TST-612 — multi_replace targeting .github must produce a generic deny
    payload = {
        "tool_name": "multi_replace_string_in_file",
        "replacements": [
            {"filePath": f"{WS}/.github/hooks/scripts/security_gate.py"},
        ],
    }
    reason = _get_stdout_reason(monkeypatch, capsys, payload)
    assert reason == _GENERIC_MESSAGE, (
        f"multi_replace deny reason is not the generic message.\n"
        f"  Actual: {reason!r}"
    )
    _assert_no_zones(reason, "multi_replace: ")


# ===========================================================================
# TST-613: get_errors with .vscode path → generic deny
# ===========================================================================

def test_main_get_errors_deny_is_generic(monkeypatch, capsys):
    # TST-613 — get_errors with a .vscode filePath must produce a generic deny
    payload = {
        "tool_name": "get_errors",
        "filePaths": [f"{WS}/.vscode/settings.json"],
    }
    reason = _get_stdout_reason(monkeypatch, capsys, payload)
    assert reason == _GENERIC_MESSAGE, (
        f"get_errors deny reason is not the generic message.\n"
        f"  Actual: {reason!r}"
    )
    _assert_no_zones(reason, "get_errors: ")


# ===========================================================================
# TST-614: grep_search with .github includePattern → generic deny
# ===========================================================================

def test_main_grep_search_deny_is_generic(monkeypatch, capsys):
    # TST-614 — grep_search with an includePattern targeting .github must deny
    payload = {
        "tool_name": "grep_search",
        "query": "password",
        "includePattern": ".github/**",
        "filePath": WS,
    }
    reason = _get_stdout_reason(monkeypatch, capsys, payload)
    assert reason == _GENERIC_MESSAGE, (
        f"grep_search deny reason is not the generic message.\n"
        f"  Actual: {reason!r}"
    )
    _assert_no_zones(reason, "grep_search: ")


# ===========================================================================
# TST-615: semantic_search → always denied, reason must be generic
# ===========================================================================

def test_main_semantic_search_deny_is_generic(monkeypatch, capsys):
    # TST-615 \u2014 FIX-021: semantic_search is now allowed; VS Code search.exclude hides
    # restricted content. Verify that decide() returns "allow" for semantic_search.
    payload = {
        "tool_name": "semantic_search",
        "query": "NoAgentZone contents",
        "filePath": WS,
    }
    monkeypatch.setattr(sg, "verify_file_integrity", lambda: True)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setattr(os, "getcwd", lambda: WS)
    with pytest.raises(SystemExit):
        sg.main()
    data = json.loads(capsys.readouterr().out)
    decision = data["hookSpecificOutput"]["permissionDecision"]
    assert decision == "allow", (
        f"semantic_search should return allow after FIX-021.\n"
        f"  Actual decision: {decision!r}"
    )


# ===========================================================================
# TST-616: sanitize_terminal_command — extended deny path coverage
# ===========================================================================

def test_sanitize_terminal_all_paths_generic():
    # TST-616 — exercise deny paths not hit by TST-608:
    #   - empty command after normalization
    #   - command that cannot be tokenized (shlex error)
    #   - dynamic primary verb with $
    #   - redirect to .vscode path
    #   - explicit destructive pattern
    from unittest.mock import patch

    test_cases = [
        ("", "empty command"),
        ("$VAR_COMMAND arg", "variable primary verb"),
        (f"cat {WS}/.vscode/settings.json", "read of .vscode"),
        (f"ls {WS}/NoAgentZone", "ls of NoAgentZone"),
        ("format c:", "destructive pattern (format)"),
        ("sudo rm -rf /", "sudo command"),
    ]

    for cmd, label in test_cases:
        decision, reason = sg.sanitize_terminal_command(cmd, WS)
        assert decision == "deny", (
            f"[{label}] Expected deny for {cmd!r}, got {decision!r}"
        )
        if reason is not None:
            reason_lower = reason.lower()
            for zone in _ZONE_NAMES:
                assert zone.lower() not in reason_lower, (
                    f"[{label}] Deny reason reveals zone '{zone}': {reason!r}"
                )


# ===========================================================================
# TST-617: Internal comments in security_gate.py still reference zone names
# ===========================================================================

def test_internal_comments_still_reference_zones():
    # TST-617 — zone names must still appear in source code comments/strings
    # so maintainability is preserved.  Only the _DENY_REASON VALUE must be
    # generic; internal code is allowed (and expected) to name the zones.
    gate_path = os.path.join(_SCRIPTS_DIR, "security_gate.py")
    with open(gate_path, encoding="utf-8") as fh:
        content = fh.read()

    # Verify key zone identifiers are still present in the source (comments,
    # variable names, f-strings, zone lists, etc.)
    assert ".github" in content, (
        "'.github' has been completely removed from security_gate.py — "
        "internal comments/references should still exist for maintainability"
    )
    assert ".vscode" in content, (
        "'.vscode' has been completely removed from security_gate.py — "
        "internal comments/references should still exist for maintainability"
    )
    assert "noagentzone" in content.lower(), (
        "'noagentzone' has been completely removed from security_gate.py — "
        "internal references should still exist for maintainability"
    )

    # But _DENY_REASON assignment line must NOT contain zone names
    for line in content.splitlines():
        stripped = line.strip()
        if "_DENY_REASON" in stripped and "=" in stripped and not stripped.startswith("#"):
            line_lower = stripped.lower()
            for zone in _ZONE_NAMES:
                assert zone.lower() not in line_lower, (
                    f"_DENY_REASON assignment line reveals zone '{zone}': {stripped!r}"
                )


# ===========================================================================
# TST-618: Unknown non-exempt tool targeting deny zone → generic JSON deny
# ===========================================================================

def test_main_unknown_tool_deny_is_generic(monkeypatch, capsys):
    # TST-618 — a completely unknown tool name not in any allow/exempt set
    # must produce a generic deny, not one that names the zone
    payload = {
        "tool_name": "mystery_exfiltration_tool",
        "filePath": f"{WS}/.github/secret_key",
    }
    reason = _get_stdout_reason(monkeypatch, capsys, payload)
    assert reason == _GENERIC_MESSAGE, (
        f"unknown-tool deny reason is not the generic message.\n"
        f"  Actual: {reason!r}"
    )
    _assert_no_zones(reason, "unknown tool: ")


# ===========================================================================
# TST-619: _DENY_REASON is byte-for-byte identical in both security_gate.py
# ===========================================================================

def test_deny_reason_same_both_copies():
    # TST-619 — the templates copy must have the EXACT same _DENY_REASON text
    # (byte-for-byte, not just substring match as TST-610 does)
    assert os.path.isfile(_TEMPLATE_PATH), (
        f"templates security_gate.py not found at: {_TEMPLATE_PATH}"
    )
    with open(_TEMPLATE_PATH, encoding="utf-8") as fh:
        template_content = fh.read()

    # Extract _DENY_REASON assignment from templates file
    match = re.search(r'^_DENY_REASON\s*=\s*"([^"]*)"', template_content, re.MULTILINE)
    assert match is not None, (
        "Could not find _DENY_REASON assignment line in templates security_gate.py"
    )
    template_deny_reason = match.group(1)
    assert template_deny_reason == sg._DENY_REASON, (
        f"templates _DENY_REASON differs from Default-Project.\n"
        f"  Default-Project: {sg._DENY_REASON!r}\n"
        f"  templates:       {template_deny_reason!r}"
    )


# ===========================================================================
# TST-620: All sanitize_terminal f-string prefixes contain no zone names
# ===========================================================================

def test_sanitize_terminal_f_string_prefixes_no_zone_names():
    # TST-620 — the textual prefixes in every f-string returned by
    # sanitize_terminal_command() must not mention restricted zone names.
    # We test every deny code path and assert the returned reason string
    # (which IS visible to direct callers of the function) has no zone leaks.
    test_cases = [
        # obfuscation pre-scan
        ("iex .github/evil", "obfuscation pre-scan"),
        # parse failure: unterminated quote → shlex raises ValueError
        ("cat 'unterminated", "parse failure"),
        # variable primary verb
        ("$({cmd})", "dynamic verb"),
        # not on allowlist
        ("notallowed arg", "not on allowlist"),
        # argument validation failure  
        (f"git push --force {WS}/Project/", "argument validation"),
        # destructive pattern (format)
        ("format c:", "destructive pattern"),
        # path zone check for allowed command
        (f"cat {WS}/.github/settings.json", "zone check in allowed command"),
    ]
    for cmd, label in test_cases:
        decision, reason = sg.sanitize_terminal_command(cmd, WS)
        if decision != "deny":
            continue  # some may allow; only check deny paths
        if reason is None:
            continue
        reason_lower = reason.lower()
        for zone in _ZONE_NAMES:
            assert zone.lower() not in reason_lower, (
                f"[{label}] sanitize_terminal_command reason leaks zone "
                f"'{zone}': {reason!r}"
            )
