"""SAF-039 — Tester edge-case tests for vscode_listCodeUsages / vscode_renameSymbol.

Focuses on attack vectors not covered by developer tests:
  - Percent-encoded path traversal in file:// URIs  ← SECURITY CONCERN (BUG-SAF-039-01)
  - UNC paths via file:// URIs and filePath
  - Mixed-case tool names (fail-closed behavior)
  - Conflicting filePath + uri in same payload
  - Non-dict tool_input handling
  - URI with fragment suffix
  - Percent-encoded dot-dot via decide() integration
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Import security_gate from the templates directory (same pattern as dev tests)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "coding"
    / ".github"
    / "hooks"
    / "scripts"
)

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg   # noqa: E402
import zone_classifier as zc  # noqa: E402

WS = "/workspace"
WS_WIN = "c:/workspace"

PROJECT_FILE = f"{WS}/project/src/main.py"


@pytest.fixture(autouse=True)
def _patch_detect_project_folder():
    """Patch zone_classifier.detect_project_folder for fake workspace roots."""
    original = zc.detect_project_folder

    def _detect_with_fallback(workspace_root: Path) -> str:
        try:
            return original(workspace_root)
        except (RuntimeError, OSError):
            return "project"

    with patch.object(zc, "detect_project_folder", side_effect=_detect_with_fallback):
        yield


# ===========================================================================
# URI percent-encoded traversal — BUG-SAF-039-01
#
# These tests FAIL with the current implementation, demonstrating that
# percent-encoded %2E%2E sequences in file:// URIs bypass zone checking.
# The fix is to call urllib.parse.unquote() on the extracted URI path before
# passing it to zone_classifier.classify().
# ===========================================================================

class TestPercentEncodedTraversalBypass:
    """Confirm that percent-encoded path traversal in URIs is DENIED.

    All tests in this class document BUG-SAF-039-01: percent-encoded %2E%2E
    sequences pass through _extract_lsp_file_path as literal %2E%2E and are
    NOT resolved by posixpath.normpath (which only resolves raw '..').
    Result: zone_classifier sees 'project/%2e%2e/.github/config' which matches
    the project prefix and returns 'allow' — a security bypass.
    """

    def test_list_code_usages_pct_encoded_traversal_to_github(self):
        """vscode_listCodeUsages: %2E%2E traversal to .github/ must be denied."""
        data = {"tool_input": {
            "uri": "file:///workspace/project/%2E%2E/.github/hooks/security_gate.py",
            "symbol": "validate",
        }}
        # BUG-SAF-039-01: currently returns 'allow' — should return 'deny'
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_list_code_usages_pct_encoded_traversal_to_noagentzone(self):
        """vscode_listCodeUsages: %2E%2E traversal to NoAgentZone/ must be denied."""
        data = {"tool_input": {
            "uri": "file:///workspace/project/%2E%2E/NoAgentZone/secret.txt",
            "symbol": "secret",
        }}
        # BUG-SAF-039-01: currently returns 'allow'
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_rename_symbol_pct_encoded_traversal_to_github(self):
        """vscode_renameSymbol: %2E%2E traversal to .github/ must be denied (write-like)."""
        data = {"tool_input": {
            "uri": "file:///workspace/project/%2E%2E/.github/hooks/scripts/security_gate.py",
            "symbol": "validate_write_tool",
            "newName": "x",
        }}
        # BUG-SAF-039-01: currently returns 'allow' — write-like bypass is critical
        assert sg.validate_vscode_rename_symbol(data, WS) == "deny"

    def test_rename_symbol_pct_encoded_traversal_to_vscode(self):
        """vscode_renameSymbol: %2E%2E traversal to .vscode/ must be denied."""
        data = {"tool_input": {
            "uri": "file:///workspace/project/%2E%2E/.vscode/settings.json",
            "symbol": "x",
            "newName": "y",
        }}
        # BUG-SAF-039-01: currently returns 'allow'
        assert sg.validate_vscode_rename_symbol(data, WS) == "deny"

    def test_lowercase_pct_uppercase_encoded_traversal(self):
        """Lowercase %2e%2e (same as %2E%2E but lowercase) must also be denied."""
        data = {"tool_input": {
            "uri": "file:///workspace/project/%2e%2e/.github/config",
        }}
        # BUG-SAF-039-01: currently returns 'allow'
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_decide_list_code_usages_pct_traversal_denied(self):
        """decide() must deny vscode_listCodeUsages with %2E%2E URI traversal."""
        data = {
            "tool_name": "vscode_listCodeUsages",
            "tool_input": {
                "uri": "file:///workspace/project/%2E%2E/.github/config",
                "symbol": "x",
            },
        }
        # BUG-SAF-039-01: currently returns 'allow'
        assert sg.decide(data, WS) == "deny"

    def test_decide_rename_symbol_pct_traversal_denied(self):
        """decide() must deny vscode_renameSymbol with %2E%2E URI traversal."""
        data = {
            "tool_name": "vscode_renameSymbol",
            "tool_input": {
                "uri": "file:///workspace/project/%2E%2E/.github/config",
                "symbol": "x",
                "newName": "evil",
            },
        }
        # BUG-SAF-039-01: currently returns 'allow'
        assert sg.decide(data, WS) == "deny"


# ===========================================================================
# UNC path handling — expected PASS
# ===========================================================================

class TestUNCPaths:
    """UNC paths must not be accepted as project-folder files."""

    def test_unc_file_path_denied(self):
        r"""filePath with UNC form \\server\share\project\file must be denied."""
        data = {"tool_input": {"filePath": r"\\server\workspace\project\main.py"}}
        # Backslashes → forward slashes → //server/workspace/project/main.py
        # zone_classifier Method 2 deny-pattern should catch UNC (BUG-011 guard)
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_unc_file_uri_for_project_path_allowed(self):
        """file://hostname/path strips hostname; if remaining path is in project, allow.

        file://server/workspace/project/main.py → /workspace/project/main.py → allow.
        This is the expected outcome: zone_classifier only sees the path segment.
        """
        data = {"tool_input": {
            "uri": "file://server/workspace/project/src/main.py",
            "symbol": "foo",
        }}
        assert sg.validate_vscode_list_code_usages(data, WS) == "allow"

    def test_unc_file_uri_to_denied_zone(self):
        """file://hostname/etc/passwd → /etc/passwd → deny."""
        data = {"tool_input": {"uri": "file://server/etc/passwd"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_unc_rename_file_uri_for_project_path_allowed(self):
        """vscode_renameSymbol: file://hostname/path strips hostname; project → allow."""
        data = {"tool_input": {
            "uri": "file://buildserver/workspace/project/src/app.py",
            "symbol": "OldName",
            "newName": "NewName",
        }}
        assert sg.validate_vscode_rename_symbol(data, WS) == "allow"


# ===========================================================================
# Mixed-case tool names — must fail closed (deny)
# ===========================================================================

class TestMixedCaseToolNames:
    """decide() must deny tool calls with wrong-cased tool names.

    The dispatch table uses exact-match string comparisons and _EXEMPT_TOOLS
    contains the exact camelCase names.  Wrong-case variants must not be
    accepted silently — they should fall to the default deny.
    """

    def test_all_lowercase_list_code_usages_denied(self):
        data = {
            "tool_name": "vscode_listcodeusages",
            "tool_input": {"filePath": PROJECT_FILE, "symbol": "Foo"},
        }
        assert sg.decide(data, WS) == "deny"

    def test_all_uppercase_list_code_usages_denied(self):
        data = {
            "tool_name": "VSCODE_LISTCODEUSAGES",
            "tool_input": {"filePath": PROJECT_FILE, "symbol": "Foo"},
        }
        assert sg.decide(data, WS) == "deny"

    def test_mixed_case_rename_symbol_denied(self):
        data = {
            "tool_name": "Vscode_RenameSymbol",
            "tool_input": {"filePath": PROJECT_FILE, "symbol": "Foo", "newName": "Bar"},
        }
        assert sg.decide(data, WS) == "deny"

    def test_wrong_case_rename_symbol_denied(self):
        data = {
            "tool_name": "vscode_renamesymbol",
            "tool_input": {"filePath": PROJECT_FILE, "symbol": "Foo", "newName": "Bar"},
        }
        assert sg.decide(data, WS) == "deny"


# ===========================================================================
# Conflicting filePath + uri in the same payload
# ===========================================================================

class TestConflictingPathAndUri:
    """When both filePath and uri are present, filePath must win.

    This is critical for security: an attacker must not be able to pass a
    safe-looking filePath alongside a malicious uri and have the uri used.
    """

    def test_filepath_wins_over_malicious_uri(self):
        """filePath (project-file) wins; malicious uri is ignored."""
        data = {"tool_input": {
            "filePath": PROJECT_FILE,
            "uri": "file:///etc/passwd",
            "symbol": "foo",
        }}
        assert sg.validate_vscode_list_code_usages(data, WS) == "allow"

    def test_deny_path_wins_even_if_uri_is_safe(self):
        """filePath (outside project) wins; safe-looking uri is irrelevant."""
        data = {"tool_input": {
            "filePath": "/etc/passwd",
            "uri": f"file://{WS}/project/src/main.py",
            "symbol": "root",
        }}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_empty_filepath_falls_through_to_uri(self):
        """Empty filePath must not block the uri fallback."""
        data = {"tool_input": {
            "filePath": "",
            "uri": f"file://{WS}/project/src/main.py",
            "symbol": "foo",
        }}
        assert sg.validate_vscode_list_code_usages(data, WS) == "allow"

    def test_empty_filepath_falls_through_to_malicious_uri(self):
        """Empty filePath fallback to malicious uri must be denied."""
        data = {"tool_input": {
            "filePath": "",
            "uri": "file:///etc/passwd",
        }}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"


# ===========================================================================
# Non-dict / malformed tool_input
# ===========================================================================

class TestMalformedPayloads:
    """Malformed payloads must be handled gracefully — fail closed."""

    def test_non_dict_tool_input_falls_back_to_top_level_filepath(self):
        """tool_input=string should fall back to top-level filePath."""
        data = {"tool_input": "not-a-dict", "filePath": PROJECT_FILE}
        # top-level filePath inside project → allow
        assert sg.validate_vscode_list_code_usages(data, WS) == "allow"

    def test_non_dict_tool_input_with_outside_top_level_filepath(self):
        data = {"tool_input": 42, "filePath": "/etc/passwd"}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_none_tool_input_falls_back_to_top_level_filepath(self):
        """tool_input=None should fall back to top-level filePath."""
        data = {"tool_input": None, "filePath": PROJECT_FILE}
        assert sg.validate_vscode_list_code_usages(data, WS) == "allow"

    def test_none_tool_input_with_missing_top_level_filepath_fails_closed(self):
        data = {"tool_input": None}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_rename_symbol_non_dict_tool_input_denied_when_no_filepath(self):
        data = {"tool_input": ["/workspace/project/src/main.py"]}
        assert sg.validate_vscode_rename_symbol(data, WS) == "deny"


# ===========================================================================
# URI with fragment suffix (#L42 style)
# ===========================================================================

class TestURIWithFragment:
    """URIs with fragment suffixes (#L42) should be handled without security issues.

    VS Code may append line anchors to file URIs.  The fragment becomes part
    of the extracted path string.  The zone classifier still allows the path
    when the pre-fragment portion is inside the project folder.
    """

    def test_list_code_usages_uri_with_line_fragment_project_allowed(self):
        data = {"tool_input": {
            "uri": f"file://{WS}/project/src/main.py#L42",
            "symbol": "foo",
        }}
        # Fragment included in extracted path but still resolves to project
        assert sg.validate_vscode_list_code_usages(data, WS) == "allow"

    def test_rename_symbol_uri_with_line_fragment_project_allowed(self):
        data = {"tool_input": {
            "uri": f"file://{WS}/project/src/util.py#L10",
            "symbol": "old",
            "newName": "new",
        }}
        assert sg.validate_vscode_rename_symbol(data, WS) == "allow"

    def test_uri_with_fragment_pointing_outside_denied(self):
        """Fragment on an outside-zone URI must still be denied."""
        data = {"tool_input": {
            "uri": "file:///etc/passwd#L1",
        }}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"
