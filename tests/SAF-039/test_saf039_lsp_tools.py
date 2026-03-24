"""SAF-039 — Tests for vscode_listCodeUsages and vscode_renameSymbol Zone Enforcement.

Covers:
- _extract_lsp_file_path() — filePath field, uri field, both formats, edge cases
- validate_vscode_list_code_usages() — project-allowed, outside-denied, .git/-denied, fail-closed
- validate_vscode_rename_symbol() — project-allowed, outside-denied, .git/-denied, fail-closed
- decide() integration — both tools dispatched correctly via decide()
- Security: null bytes, path traversal, non-file URI schemes, write-like protection
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Make security_gate (and zone_classifier) importable
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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WS = "/workspace"
WS_WIN = "c:/workspace"

# Allow-zone paths (inside project folder)
PROJECT_FILE = f"{WS}/project/src/main.py"
PROJECT_FILE_WIN = f"{WS_WIN}/project/src/app.ts"
PROJECT_FILE_NESTED = f"{WS}/project/lib/utils/helpers.py"

# Deny-zone paths (outside project folder)
GITHUB_FILE = f"{WS}/.github/hooks/scripts/security_gate.py"
NOAGENT_FILE = f"{WS}/NoAgentZone/secret.txt"
VSCODE_FILE = f"{WS}/.vscode/settings.json"
DOCS_FILE = f"{WS}/docs/readme.md"
OUTSIDE_FILE = "/etc/passwd"
WINDOWS_OUTSIDE = "c:/windows/system32/cmd.exe"

# .git internals (special deny even within project zone)
GIT_INTERNAL = f"{WS}/project/.git/config"
GIT_OBJECTS = f"{WS}/project/.git/objects/abc123"


# ---------------------------------------------------------------------------
# autouse fixture: patch detect_project_folder for fake workspace
# ---------------------------------------------------------------------------

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
# _extract_lsp_file_path() — path extraction helper
# ===========================================================================

class TestExtractLspFilePath:

    def test_filepath_in_tool_input(self):
        data = {"tool_input": {"filePath": "project/src/main.py", "symbol": "foo"}}
        assert sg._extract_lsp_file_path(data) == "project/src/main.py"

    def test_filepath_at_top_level(self):
        data = {"filePath": "project/utils.py", "symbol": "bar"}
        assert sg._extract_lsp_file_path(data) == "project/utils.py"

    def test_tool_input_filepath_takes_precedence(self):
        data = {
            "tool_input": {"filePath": "project/src/a.py"},
            "filePath": "project/src/b.py",
        }
        # tool_input must win
        assert sg._extract_lsp_file_path(data) == "project/src/a.py"

    def test_uri_unix_in_tool_input(self):
        data = {"tool_input": {"uri": "file:///workspace/project/src/main.py"}}
        result = sg._extract_lsp_file_path(data)
        assert result == "/workspace/project/src/main.py"

    def test_uri_windows_in_tool_input(self):
        data = {"tool_input": {"uri": "file:///C:/workspace/project/src/app.ts"}}
        result = sg._extract_lsp_file_path(data)
        assert result == "C:/workspace/project/src/app.ts"

    def test_uri_with_hostname_stripped(self):
        # file://hostname/path form — hostname is stripped
        data = {"tool_input": {"uri": "file://localhost/workspace/project/file.py"}}
        result = sg._extract_lsp_file_path(data)
        assert result == "/workspace/project/file.py"

    def test_uri_at_top_level(self):
        data = {"uri": "file:///workspace/project/lib/util.py"}
        result = sg._extract_lsp_file_path(data)
        assert result == "/workspace/project/lib/util.py"

    def test_non_file_uri_returns_none(self):
        data = {"tool_input": {"uri": "https://example.com/file.py"}}
        assert sg._extract_lsp_file_path(data) is None

    def test_no_path_returns_none(self):
        data = {"tool_input": {"symbol": "foo", "lineContent": "def foo():"}}
        assert sg._extract_lsp_file_path(data) is None

    def test_empty_data_returns_none(self):
        assert sg._extract_lsp_file_path({}) is None

    def test_filepath_empty_string_falls_through_to_uri(self):
        data = {
            "tool_input": {
                "filePath": "",
                "uri": "file:///workspace/project/x.py",
            }
        }
        result = sg._extract_lsp_file_path(data)
        assert result == "/workspace/project/x.py"

    def test_null_byte_in_filepath_is_returned_as_is(self):
        # extraction doesn't sanitize — classify() / zone-check will handle it
        data = {"tool_input": {"filePath": "project/src\x00/evil.py"}}
        result = sg._extract_lsp_file_path(data)
        assert result == "project/src\x00/evil.py"


# ===========================================================================
# validate_vscode_list_code_usages() — unit tests
# ===========================================================================

class TestValidateVscodeListCodeUsages:

    def test_project_file_allowed(self):
        data = {"tool_input": {"filePath": PROJECT_FILE, "symbol": "MyClass"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "allow"

    def test_project_file_windows_allowed(self):
        data = {"tool_input": {"filePath": PROJECT_FILE_WIN, "symbol": "foo"}}
        assert sg.validate_vscode_list_code_usages(data, WS_WIN) == "allow"

    def test_project_nested_file_allowed(self):
        data = {"tool_input": {"filePath": PROJECT_FILE_NESTED, "symbol": "helper"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "allow"

    def test_github_zone_denied(self):
        data = {"tool_input": {"filePath": GITHUB_FILE, "symbol": "sg"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_noagentzone_denied(self):
        data = {"tool_input": {"filePath": NOAGENT_FILE, "symbol": "secret"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_vscode_zone_denied(self):
        data = {"tool_input": {"filePath": VSCODE_FILE, "symbol": "setting"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_docs_zone_denied(self):
        data = {"tool_input": {"filePath": DOCS_FILE, "symbol": "readme"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_absolute_outside_denied(self):
        data = {"tool_input": {"filePath": OUTSIDE_FILE, "symbol": "root"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_git_internals_denied(self):
        data = {"tool_input": {"filePath": GIT_INTERNAL, "symbol": "core"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_git_objects_denied(self):
        data = {"tool_input": {"filePath": GIT_OBJECTS, "symbol": "blob"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_no_path_fails_closed(self):
        data = {"tool_input": {"symbol": "foo", "lineContent": "def foo():"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_empty_data_fails_closed(self):
        assert sg.validate_vscode_list_code_usages({}, WS) == "deny"

    def test_null_byte_in_path_denied(self):
        data = {"tool_input": {"filePath": f"{WS}/project/src\x00/evil.py"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_path_traversal_denied(self):
        data = {"tool_input": {"filePath": f"{WS}/project/../.github/config"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_uri_project_file_allowed(self):
        data = {"tool_input": {"uri": f"file://{WS}/project/src/main.py"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "allow"

    def test_uri_outside_denied(self):
        data = {"tool_input": {"uri": "file:///etc/passwd"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_non_file_uri_fails_closed(self):
        data = {"tool_input": {"uri": "https://example.com/project/src/main.py"}}
        assert sg.validate_vscode_list_code_usages(data, WS) == "deny"

    def test_windows_outside_path_denied(self):
        data = {"tool_input": {"filePath": WINDOWS_OUTSIDE}}
        assert sg.validate_vscode_list_code_usages(data, WS_WIN) == "deny"


# ===========================================================================
# validate_vscode_rename_symbol() — unit tests
# ===========================================================================

class TestValidateVscodeRenameSymbol:

    def test_project_file_allowed(self):
        data = {"tool_input": {"filePath": PROJECT_FILE, "symbol": "MyClass", "newName": "NewClass"}}
        assert sg.validate_vscode_rename_symbol(data, WS) == "allow"

    def test_project_file_windows_allowed(self):
        data = {"tool_input": {"filePath": PROJECT_FILE_WIN, "symbol": "fn", "newName": "newFn"}}
        assert sg.validate_vscode_rename_symbol(data, WS_WIN) == "allow"

    def test_project_nested_file_allowed(self):
        data = {"tool_input": {"filePath": PROJECT_FILE_NESTED, "symbol": "helper", "newName": "newHelper"}}
        assert sg.validate_vscode_rename_symbol(data, WS) == "allow"

    def test_github_zone_denied(self):
        data = {"tool_input": {"filePath": GITHUB_FILE, "symbol": "sg", "newName": "x"}}
        assert sg.validate_vscode_rename_symbol(data, WS) == "deny"

    def test_noagentzone_denied(self):
        data = {"tool_input": {"filePath": NOAGENT_FILE, "symbol": "s", "newName": "t"}}
        assert sg.validate_vscode_rename_symbol(data, WS) == "deny"

    def test_vscode_zone_denied(self):
        data = {"tool_input": {"filePath": VSCODE_FILE, "symbol": "s", "newName": "t"}}
        assert sg.validate_vscode_rename_symbol(data, WS) == "deny"

    def test_docs_zone_denied(self):
        data = {"tool_input": {"filePath": DOCS_FILE, "symbol": "s", "newName": "t"}}
        assert sg.validate_vscode_rename_symbol(data, WS) == "deny"

    def test_absolute_outside_denied(self):
        data = {"tool_input": {"filePath": OUTSIDE_FILE, "symbol": "root", "newName": "admin"}}
        assert sg.validate_vscode_rename_symbol(data, WS) == "deny"

    def test_git_internals_denied(self):
        """Write-like tool must never touch .git internals."""
        data = {"tool_input": {"filePath": GIT_INTERNAL, "symbol": "core", "newName": "x"}}
        assert sg.validate_vscode_rename_symbol(data, WS) == "deny"

    def test_git_objects_denied(self):
        data = {"tool_input": {"filePath": GIT_OBJECTS, "symbol": "blob", "newName": "x"}}
        assert sg.validate_vscode_rename_symbol(data, WS) == "deny"

    def test_no_path_fails_closed(self):
        data = {"tool_input": {"symbol": "foo", "newName": "bar"}}
        assert sg.validate_vscode_rename_symbol(data, WS) == "deny"

    def test_empty_data_fails_closed(self):
        assert sg.validate_vscode_rename_symbol({}, WS) == "deny"

    def test_null_byte_in_path_denied(self):
        data = {"tool_input": {"filePath": f"{WS}/project/src\x00/evil.py"}}
        assert sg.validate_vscode_rename_symbol(data, WS) == "deny"

    def test_path_traversal_denied(self):
        data = {"tool_input": {"filePath": f"{WS}/project/../.github/hook.py"}}
        assert sg.validate_vscode_rename_symbol(data, WS) == "deny"

    def test_uri_project_file_allowed(self):
        data = {"tool_input": {"uri": f"file://{WS}/project/src/main.py"}}
        assert sg.validate_vscode_rename_symbol(data, WS) == "allow"

    def test_uri_outside_denied(self):
        data = {"tool_input": {"uri": "file:///etc/passwd"}}
        assert sg.validate_vscode_rename_symbol(data, WS) == "deny"

    def test_non_file_uri_fails_closed(self):
        data = {"tool_input": {"uri": "https://example.com/project/src/main.py"}}
        assert sg.validate_vscode_rename_symbol(data, WS) == "deny"

    def test_windows_outside_path_denied(self):
        data = {"tool_input": {"filePath": WINDOWS_OUTSIDE}}
        assert sg.validate_vscode_rename_symbol(data, WS_WIN) == "deny"


# ===========================================================================
# decide() integration — both tools dispatched via full pipeline
# ===========================================================================

class TestDecideIntegration:
    """Verify decide() correctly routes to the LSP validators."""

    def _make_payload(self, tool: str, file_path: str) -> dict:
        return {
            "tool_name": tool,
            "tool_input": {"filePath": file_path, "symbol": "Foo"},
        }

    # --- vscode_listCodeUsages ---

    def test_list_code_usages_project_file_allowed(self):
        data = self._make_payload("vscode_listCodeUsages", PROJECT_FILE)
        assert sg.decide(data, WS) == "allow"

    def test_list_code_usages_github_denied(self):
        data = self._make_payload("vscode_listCodeUsages", GITHUB_FILE)
        assert sg.decide(data, WS) == "deny"

    def test_list_code_usages_noagentzone_denied(self):
        data = self._make_payload("vscode_listCodeUsages", NOAGENT_FILE)
        assert sg.decide(data, WS) == "deny"

    def test_list_code_usages_git_internals_denied(self):
        data = self._make_payload("vscode_listCodeUsages", GIT_INTERNAL)
        assert sg.decide(data, WS) == "deny"

    def test_list_code_usages_no_path_denied(self):
        data = {"tool_name": "vscode_listCodeUsages", "tool_input": {"symbol": "Foo"}}
        assert sg.decide(data, WS) == "deny"

    # --- vscode_renameSymbol ---

    def test_rename_symbol_project_file_allowed(self):
        data = {
            "tool_name": "vscode_renameSymbol",
            "tool_input": {"filePath": PROJECT_FILE, "symbol": "OldName", "newName": "NewName"},
        }
        assert sg.decide(data, WS) == "allow"

    def test_rename_symbol_github_denied(self):
        data = {
            "tool_name": "vscode_renameSymbol",
            "tool_input": {"filePath": GITHUB_FILE, "symbol": "sg", "newName": "x"},
        }
        assert sg.decide(data, WS) == "deny"

    def test_rename_symbol_noagentzone_denied(self):
        data = {
            "tool_name": "vscode_renameSymbol",
            "tool_input": {"filePath": NOAGENT_FILE, "symbol": "s", "newName": "t"},
        }
        assert sg.decide(data, WS) == "deny"

    def test_rename_symbol_git_internals_denied(self):
        data = {
            "tool_name": "vscode_renameSymbol",
            "tool_input": {"filePath": GIT_INTERNAL, "symbol": "core", "newName": "x"},
        }
        assert sg.decide(data, WS) == "deny"

    def test_rename_symbol_no_path_denied(self):
        data = {
            "tool_name": "vscode_renameSymbol",
            "tool_input": {"symbol": "OldName", "newName": "NewName"},
        }
        assert sg.decide(data, WS) == "deny"

    def test_rename_symbol_docs_zone_denied(self):
        data = {
            "tool_name": "vscode_renameSymbol",
            "tool_input": {"filePath": DOCS_FILE, "symbol": "x", "newName": "y"},
        }
        assert sg.decide(data, WS) == "deny"

    # --- URI format via decide() ---

    def test_list_code_usages_uri_project_allowed(self):
        data = {
            "tool_name": "vscode_listCodeUsages",
            "tool_input": {
                "uri": f"file://{WS}/project/src/main.py",
                "symbol": "Foo",
            },
        }
        assert sg.decide(data, WS) == "allow"

    def test_rename_symbol_uri_project_allowed(self):
        data = {
            "tool_name": "vscode_renameSymbol",
            "tool_input": {
                "uri": f"file://{WS}/project/src/main.py",
                "symbol": "Foo",
                "newName": "Bar",
            },
        }
        assert sg.decide(data, WS) == "allow"

    def test_list_code_usages_uri_outside_denied(self):
        data = {
            "tool_name": "vscode_listCodeUsages",
            "tool_input": {"uri": "file:///etc/passwd", "symbol": "root"},
        }
        assert sg.decide(data, WS) == "deny"

    def test_rename_symbol_uri_outside_denied(self):
        data = {
            "tool_name": "vscode_renameSymbol",
            "tool_input": {"uri": "file:///etc/passwd", "symbol": "root", "newName": "admin"},
        }
        assert sg.decide(data, WS) == "deny"

    # --- Both tools are in _EXEMPT_TOOLS ---

    def test_list_code_usages_in_exempt_tools(self):
        assert "vscode_listCodeUsages" in sg._EXEMPT_TOOLS

    def test_rename_symbol_in_exempt_tools(self):
        assert "vscode_renameSymbol" in sg._EXEMPT_TOOLS
