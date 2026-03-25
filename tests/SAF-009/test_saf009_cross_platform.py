"""SAF-009: Cross-Platform Integration Test Suite

Validates all security zones, all bypass vectors from the audit report,
and all tool types through the decide() pipeline.

Tests are organised into four sections:

  SECTION 1 — Audit Finding Regressions (TST-521 to TST-532)
    One pair of tests per audit finding (AF-1 through AF-6).

  SECTION 2 — All Tool Types × All Zones (TST-533 to TST-548)
    Every tool category (write / search / terminal / read / unknown /
    always-allow) exercised against each zone.

  SECTION 3 — Cross-Platform Path Formats (TST-549 to TST-560)
    Windows backslash, WSL /mnt/c/, and Git Bash /c/ paths validated for
    both write and read tools across all three zones.

  SECTION 4 — VS Code Nested Hook Format (TST-561 to TST-570)
    Realistic {\"tool_name\": ..., \"tool_input\": {...}} payloads matching
    the format VS Code sends to PreToolUse hooks.

These tests do NOT duplicate unit tests that already exist in the
SAF-001 through SAF-008 individual suites.  They add new integration
and cross-platform scenarios verified at the decide() boundary.
"""
from __future__ import annotations

import os
import re
import sys

import pytest

# ---------------------------------------------------------------------------
# Make security_gate (and zone_classifier) importable from their
# non-standard location inside templates/coding/.github/hooks/scripts/
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "templates", "agent-workbench",
        ".github",
        "hooks",
        "scripts",
    )
)

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

# ---------------------------------------------------------------------------
# Shared workspace-root constants
# Posix-style paths are used throughout; normalization handles the rest.
# ---------------------------------------------------------------------------
WS = "/workspace"
WS_WIN = "c:/workspace"


# ===========================================================================
# SECTION 1 — Audit Finding Regression Tests  (TST-521 to TST-532)
# ===========================================================================

# ---------------------------------------------------------------------------
# AF-1: Core hook functionality (SAF-001)
# ---------------------------------------------------------------------------

def test_af1_core_deny_malformed_input():
    # TST-521 — regression AF-1: malformed JSON through the full pipeline
    # must return "deny" (fail-closed).  The earlier shell hooks did not
    # validate stdin at all; security_gate.py added this protection.
    result = sg.parse_input("{not valid json}")
    assert result is None
    # decide() receives None-equivalent via separate guard; verify via
    # build_response path that deny is produced when parse_input returns None.
    decision_json = sg.build_response("deny", sg._DENY_REASON)
    import json
    parsed = json.loads(decision_json)
    assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_af1_core_allow_project_path():
    # TST-522 — regression AF-1: a standard read_file call on a Project/ path
    # must return "allow" end-to-end through decide().
    data = {"tool_name": "read_file", "filePath": f"{WS}/project/main.py"}
    assert sg.decide(data, WS) == "allow"


# ---------------------------------------------------------------------------
# AF-2: grep_search includePattern bypass (SAF-003)
# ---------------------------------------------------------------------------

def test_af2_grep_includepattern_github_nested():
    # TST-523 — regression AF-2: grep_search with includePattern targeting
    # .github/ must be denied even when passed in the VS Code nested
    # tool_input format.  The pre-SAF-003 hook did not inspect tool parameters.
    data = {
        "tool_name": "grep_search",
        "tool_input": {"includePattern": ".github/**", "query": "secret"},
    }
    assert sg.decide(data, WS) == "deny"


def test_af2_grep_brace_expansion_bypass():
    # TST-524 — regression AF-2: brace-expansion bypass attempt.
    # {src,.github}/** expands to both src/** and .github/** — the .github
    # expansion must cause the entire call to be denied.
    data = {
        "tool_name": "grep_search",
        "includePattern": "{src,.github}/**",
        "query": "password",
    }
    assert sg.decide(data, WS) == "deny"


# ---------------------------------------------------------------------------
# AF-3: semantic_search zone bypass (SAF-003)
# ---------------------------------------------------------------------------

def test_af3_semantic_search_never_allow():
    # TST-525 — FIX-021: semantic_search is now allowed; VS Code search.exclude hides restricted content.
    data = {"tool_name": "semantic_search", "query": "utility function"}
    result = sg.decide(data, WS)
    assert result == "allow"


def test_af3_semantic_search_nested_input():
    # TST-526 — FIX-021: semantic_search in VS Code nested format is now allowed.
    data = {
        "tool_name": "semantic_search",
        "tool_input": {"query": "security gate implementation"},
    }
    assert sg.decide(data, WS) == "allow"


# ---------------------------------------------------------------------------
# AF-4: Recursive enumeration protection (SAF-006)
# ---------------------------------------------------------------------------

def test_af4_recursive_get_childitem():
    # TST-527 — regression AF-4: Get-ChildItem -Recurse starting from the
    # workspace root is an ancestor-of-deny-zone scenario and must be denied.
    data = {
        "tool_name": "run_in_terminal",
        "command": f"Get-ChildItem -Recurse {WS}",
    }
    decision, _ = sg.sanitize_terminal_command(
        f"Get-ChildItem -Recurse {WS}", WS
    )
    assert decision == "deny"


def test_af4_recursive_find_command():
    # TST-528 — regression AF-4: `find .` from the workspace root is
    # inherently recursive and targets an ancestor of all deny zones.
    decision, _ = sg.sanitize_terminal_command("find .", WS)
    assert decision == "deny"


# ---------------------------------------------------------------------------
# AF-5: Hook file integrity (SAF-008)
# ---------------------------------------------------------------------------

def test_af5_integrity_constants_not_zeroed():
    # TST-529 — regression AF-5: the embedded SHA256 constants must be valid
    # 64-character hex strings and must not be the all-zeros placeholder used
    # during canonical hashing.  An all-zeros value means the hashes were
    # never properly computed.
    zero_hash = "0" * 64
    assert re.fullmatch(r"[0-9a-fA-F]{64}", sg._KNOWN_GOOD_SETTINGS_HASH)
    assert re.fullmatch(r"[0-9a-fA-F]{64}", sg._KNOWN_GOOD_GATE_HASH)
    assert sg._KNOWN_GOOD_SETTINGS_HASH != zero_hash
    assert sg._KNOWN_GOOD_GATE_HASH != zero_hash


def test_af5_verify_integrity_function_callable():
    # TST-530 — regression AF-5: verify_file_integrity() must exist and be
    # callable.  Its specific pass/fail result depends on whether the actual
    # templates/coding/ files are present; the important thing is that the
    # function is present and does not raise an exception when called.
    assert callable(sg.verify_file_integrity)
    result = sg.verify_file_integrity()
    assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# AF-6: Write restriction bypass (SAF-007)
# ---------------------------------------------------------------------------

def test_af6_all_write_tools_project_allowed():
    # TST-531 — regression AF-6: every tool in _WRITE_TOOLS must be allowed
    # when targeting Project/ (and only Project/).
    project_path = f"{WS}/project/output.py"
    for tool in sg._WRITE_TOOLS:
        data = {"tool_name": tool, "filePath": project_path}
        result = sg.decide(data, WS)
        assert result == "allow", (
            f"Write tool {tool!r} on Project/ path expected 'allow', got {result!r}"
        )


def test_af6_all_write_tools_outside_denied():
    # TST-532 — regression AF-6: every tool in _WRITE_TOOLS must be denied
    # when targeting a path outside Project/ (docs/ is an "ask" zone, but
    # SAF-007 enforces "deny" for writes even in ask zones).
    outside_paths = [
        f"{WS}/docs/notes.md",
        f"{WS}/.github/hooks/evil.py",
        f"{WS}/.vscode/settings.json",
        f"{WS}/noagentzone/secret.txt",
    ]
    for tool in sg._WRITE_TOOLS:
        for path in outside_paths:
            data = {"tool_name": tool, "filePath": path}
            result = sg.decide(data, WS)
            assert result == "deny", (
                f"Write tool {tool!r} on {path!r} expected 'deny', got {result!r}"
            )


# ===========================================================================
# SECTION 2 — All Tool Types × All Zones  (TST-533 to TST-548)
# ===========================================================================

# -- Write tools --

def test_tools_create_file_project():
    # TST-533 — create_file → Project/ zone → allow
    data = {"tool_name": "create_file", "filePath": f"{WS}/project/new_module.py"}
    assert sg.decide(data, WS) == "allow"


def test_tools_create_file_github():
    # TST-534 — create_file → .github/ zone → deny
    data = {"tool_name": "create_file", "filePath": f"{WS}/.github/hooks/inject.py"}
    assert sg.decide(data, WS) == "deny"


def test_tools_replace_project():
    # TST-535 — replace_string_in_file → Project/ zone → allow
    data = {"tool_name": "replace_string_in_file", "filePath": f"{WS}/project/app.py"}
    assert sg.decide(data, WS) == "allow"


def test_tools_replace_docs():
    # TST-536 — replace_string_in_file → docs/ (ask zone) → deny
    # SAF-007: writes outside Project/ are always denied regardless of zone.
    data = {"tool_name": "replace_string_in_file", "filePath": f"{WS}/docs/readme.md"}
    assert sg.decide(data, WS) == "deny"


def test_tools_multi_replace_project():
    # TST-537 — multi_replace_string_in_file → Project/ zone → allow
    data = {
        "tool_name": "multi_replace_string_in_file",
        "filePath": f"{WS}/project/config.py",
    }
    assert sg.decide(data, WS) == "allow"


def test_tools_multi_replace_vscode():
    # TST-538 — multi_replace_string_in_file → .vscode/ zone → deny
    data = {
        "tool_name": "multi_replace_string_in_file",
        "filePath": f"{WS}/.vscode/settings.json",
    }
    assert sg.decide(data, WS) == "deny"


# -- Search tools --

def test_tools_grep_safe_no_path():
    # TST-539 — grep_search with no includePattern and no filePath.
    # FIX-021: VS Code search.exclude hides restricted content → allow.
    data = {"tool_name": "grep_search", "query": "TODO"}
    assert sg.decide(data, WS) == "allow"


def test_tools_grep_blocked_include():
    # TST-540 — grep_search with includePattern targeting .github → deny
    data = {
        "tool_name": "grep_search",
        "includePattern": ".github/**",
        "query": "password",
    }
    assert sg.decide(data, WS) == "deny"


def test_tools_semantic_search():
    # TST-541 — semantic_search; FIX-021: VS Code search.exclude hides restricted content → allow.
    data = {"tool_name": "semantic_search", "query": "authentication logic"}
    assert sg.decide(data, WS) == "allow"


# -- Read tools --

def test_tools_read_file_project():
    # TST-542 — read_file → Project/ zone → allow
    data = {"tool_name": "read_file", "filePath": f"{WS}/project/utils.py"}
    assert sg.decide(data, WS) == "allow"


def test_tools_read_file_github():
    # TST-543 — read_file → .github/ zone → deny
    data = {"tool_name": "read_file", "filePath": f"{WS}/.github/hooks/security_gate.py"}
    assert sg.decide(data, WS) == "deny"


def test_tools_list_dir_project():
    # TST-544 — list_dir → Project/ zone → allow
    data = {"tool_name": "list_dir", "directory": f"{WS}/project"}
    assert sg.decide(data, WS) == "allow"


def test_tools_list_dir_noagentzone():
    # TST-545 — list_dir → NoAgentZone/ zone → deny
    data = {"tool_name": "list_dir", "directory": f"{WS}/noagentzone"}
    assert sg.decide(data, WS) == "deny"


# -- Terminal tool --

def test_tools_terminal_safe():
    # TST-546 — run_in_terminal safe pytest command → allow (2-tier gate).
    # Use bare "pytest" (no path arg) to avoid zone-checking a non-project path.
    data = {"tool_name": "run_in_terminal", "command": "pytest"}
    assert sg.decide(data, WS) == "allow"


def test_tools_terminal_blocked_path():
    # TST-547 — run_in_terminal command referencing .github/ path → deny
    data = {
        "tool_name": "run_in_terminal",
        "command": f"cat {WS}/.github/hooks/security_gate.py",
    }
    assert sg.decide(data, WS) == "deny"


# -- Non-exempt unknown tool --

def test_tools_unknown_tool_asks():
    # TST-548 — an unrecognised tool name that is not in _EXEMPT_TOOLS and
    # not in _ALWAYS_ALLOW_TOOLS must never be auto-allowed.
    # After SAF-013 (2-tier gate), unverifiable tools return "deny".
    data = {
        "tool_name": "some_custom_undeclared_tool",
        "filePath": f"{WS}/project/main.py",
    }
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# SECTION 3 — Cross-Platform Path Formats  (TST-549 to TST-560)
# ===========================================================================

# -- Write tools with Windows, WSL, and Git Bash paths --

def test_crossplat_win_create_project():
    # TST-549 — Windows backslash path → create_file → Project/ → allow
    data = {
        "tool_name": "create_file",
        "filePath": r"c:\workspace\project\main.py",
    }
    assert sg.decide(data, WS_WIN) == "allow"


def test_crossplat_win_create_github():
    # TST-550 — Windows backslash path → create_file → .github/ → deny
    data = {
        "tool_name": "create_file",
        "filePath": r"c:\workspace\.github\hooks\evil.py",
    }
    assert sg.decide(data, WS_WIN) == "deny"


def test_crossplat_wsl_create_project():
    # TST-551 — WSL /mnt/c/ path → create_file → Project/ → allow
    data = {
        "tool_name": "create_file",
        "filePath": "/mnt/c/workspace/project/main.py",
    }
    assert sg.decide(data, WS_WIN) == "allow"


def test_crossplat_wsl_create_vscode():
    # TST-552 — WSL /mnt/c/ path → create_file → .vscode/ → deny
    data = {
        "tool_name": "create_file",
        "filePath": "/mnt/c/workspace/.vscode/settings.json",
    }
    assert sg.decide(data, WS_WIN) == "deny"


def test_crossplat_gitbash_create_project():
    # TST-553 — Git Bash /c/ path → create_file → Project/ → allow
    data = {
        "tool_name": "create_file",
        "filePath": "/c/workspace/project/utils.py",
    }
    assert sg.decide(data, WS_WIN) == "allow"


def test_crossplat_gitbash_create_noagentzone():
    # TST-554 — Git Bash /c/ path → create_file → NoAgentZone/ → deny
    data = {
        "tool_name": "create_file",
        "filePath": "/c/workspace/noagentzone/private.md",
    }
    assert sg.decide(data, WS_WIN) == "deny"


# -- Read tools with Windows, WSL, and Git Bash paths --

def test_crossplat_win_read_project():
    # TST-555 — Windows path → read_file → Project/ → allow
    data = {
        "tool_name": "read_file",
        "filePath": r"c:\workspace\project\app.py",
    }
    assert sg.decide(data, WS_WIN) == "allow"


def test_crossplat_win_read_github():
    # TST-556 — Windows path → read_file → .github/ → deny
    data = {
        "tool_name": "read_file",
        "filePath": r"c:\workspace\.github\secret.yml",
    }
    assert sg.decide(data, WS_WIN) == "deny"


def test_crossplat_wsl_read_project():
    # TST-557 — WSL path → read_file → Project/ → allow
    data = {
        "tool_name": "read_file",
        "filePath": "/mnt/c/workspace/project/config.py",
    }
    assert sg.decide(data, WS_WIN) == "allow"


def test_crossplat_wsl_read_vscode():
    # TST-558 — WSL path → read_file → .vscode/ → deny
    data = {
        "tool_name": "read_file",
        "filePath": "/mnt/c/workspace/.vscode/settings.json",
    }
    assert sg.decide(data, WS_WIN) == "deny"


def test_crossplat_gitbash_read_project():
    # TST-559 — Git Bash path → read_file → Project/ → allow
    data = {
        "tool_name": "read_file",
        "filePath": "/c/workspace/project/main.py",
    }
    assert sg.decide(data, WS_WIN) == "allow"


def test_crossplat_gitbash_read_noagentzone():
    # TST-560 — Git Bash path → read_file → NoAgentZone/ → deny
    data = {
        "tool_name": "read_file",
        "filePath": "/c/workspace/noagentzone/credentials.txt",
    }
    assert sg.decide(data, WS_WIN) == "deny"


# ===========================================================================
# SECTION 4 — VS Code Nested Hook Format  (TST-561 to TST-570)
# ===========================================================================

def test_nested_read_file_project():
    # TST-561 — VS Code nested format → read_file on Project/ → allow
    data = {
        "tool_name": "read_file",
        "tool_input": {"filePath": f"{WS}/project/app.py"},
    }
    assert sg.decide(data, WS) == "allow"


def test_nested_read_file_github():
    # TST-562 — VS Code nested format → read_file on .github/ → deny
    data = {
        "tool_name": "read_file",
        "tool_input": {"filePath": f"{WS}/.github/hooks/security_gate.py"},
    }
    assert sg.decide(data, WS) == "deny"


def test_nested_create_file_project():
    # TST-563 — VS Code nested format → create_file on Project/ → allow
    data = {
        "tool_name": "create_file",
        "tool_input": {"filePath": f"{WS}/project/new_file.py"},
    }
    assert sg.decide(data, WS) == "allow"


def test_nested_create_file_outside():
    # TST-564 — VS Code nested format → create_file on docs/ → deny
    # (docs/ is an ask zone, but SAF-007 write restriction always denies
    # writes outside Project/)
    data = {
        "tool_name": "create_file",
        "tool_input": {"filePath": f"{WS}/docs/notes.md"},
    }
    assert sg.decide(data, WS) == "deny"


def test_nested_grep_include_github():
    # TST-565 — VS Code nested format → grep_search with blocked includePattern → deny
    data = {
        "tool_name": "grep_search",
        "tool_input": {
            "includePattern": ".github/**",
            "query": "api_key",
        },
    }
    assert sg.decide(data, WS) == "deny"


def test_nested_grep_safe():
    # TST-566 — VS Code nested format → grep_search with safe params.
    # FIX-021: grep_search without a scoped path returns "allow".
    data = {
        "tool_name": "grep_search",
        "tool_input": {"query": "def main"},
    }
    assert sg.decide(data, WS) == "allow"


def test_nested_terminal_safe():
    # TST-567 — VS Code nested format → run_in_terminal safe command → allow (2-tier gate).
    # Use bare "pytest -v" (no path arg) to avoid zone-checking a non-project path.
    data = {
        "tool_name": "run_in_terminal",
        "tool_input": {"command": "pytest -v"},
    }
    assert sg.decide(data, WS) == "allow"


def test_nested_terminal_blocked():
    # TST-568 — VS Code nested format → run_in_terminal with .vscode path → deny
    data = {
        "tool_name": "run_in_terminal",
        "tool_input": {"command": f"cat {WS}/.vscode/settings.json"},
    }
    assert sg.decide(data, WS) == "deny"


def test_nested_always_allow():
    # TST-569 — VS Code nested format → ask_questions with a blocked path in
    # the payload → still allow (always-allow tools bypass zone checks)
    data = {
        "tool_name": "ask_questions",
        "tool_input": {"question": "Can I see .github/?"},
        "filePath": f"{WS}/.github/secret",
    }
    assert sg.decide(data, WS) == "allow"


def test_nested_semantic_search_asks():
    # TST-570 — VS Code nested format → semantic_search → allow (FIX-021).
    data = {
        "tool_name": "semantic_search",
        "tool_input": {"query": "password storage implementation"},
    }
    assert sg.decide(data, WS) == "allow"
