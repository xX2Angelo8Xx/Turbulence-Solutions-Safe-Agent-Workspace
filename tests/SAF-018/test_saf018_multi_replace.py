"""SAF-018 — Tests for multi_replace_string_in_file Tool Recognition.

Covers:
- TST-1385 to TST-1396: Unit — validate_multi_replace_tool() direct calls (12 tests)
- TST-1397 to TST-1402: Security — tool recognized and zone-checked via decide() (6 tests)
- TST-1403 to TST-1410: Bypass — mixed paths, traversal, malformed payloads (8 tests)
- TST-1411 to TST-1414: Cross-platform — Windows/POSIX path variants (4 tests)
- TST-1415 to TST-1419: Integration — full decide() pipeline (5 tests)
"""
from __future__ import annotations

import os
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
    / "agent-workbench"
    / ".github"
    / "hooks"
    / "scripts"
)

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WS = "/workspace"
WS_WIN = "c:/workspace"

# Paths used across tests
PROJECT_FILE_1 = f"{WS}/project/src/main.py"
PROJECT_FILE_2 = f"{WS}/project/src/utils.py"
PROJECT_FILE_WIN = f"{WS_WIN}/project/src/main.py"
OUTSIDE_FILE = f"{WS}/docs/readme.md"
GITHUB_FILE = f"{WS}/.github/hooks/scripts/security_gate.py"
NOAGENT_FILE = f"{WS}/NoAgentZone/secret.txt"
VSCODE_FILE = f"{WS}/.vscode/settings.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_replace_payload(replacements: list, use_tool_input: bool = True) -> dict:
    """Build a realistic multi_replace_string_in_file payload."""
    if use_tool_input:
        return {
            "tool_name": "multi_replace_string_in_file",
            "tool_input": {
                "replacements": replacements,
                "explanation": "Test replacement",
            },
        }
    # Flat format for backward compatibility tests
    return {
        "tool_name": "multi_replace_string_in_file",
        "replacements": replacements,
    }


def _rep(file_path: str) -> dict:
    """Build a minimal replacement entry."""
    return {"filePath": file_path, "oldString": "old", "newString": "new"}


# ===========================================================================
# Unit — validate_multi_replace_tool()  (TST-1385 to TST-1396)
# ===========================================================================

def test_unit_single_project_path_allowed():
    # TST-1385 — single replacement inside Project/ is allowed
    data = {"tool_input": {"replacements": [_rep(PROJECT_FILE_1)]}}
    assert sg.validate_multi_replace_tool(data, WS) == "allow"


def test_unit_multiple_project_paths_allowed():
    # TST-1386 — multiple replacements all inside Project/ are allowed
    data = {"tool_input": {"replacements": [
        _rep(PROJECT_FILE_1),
        _rep(PROJECT_FILE_2),
    ]}}
    assert sg.validate_multi_replace_tool(data, WS) == "allow"


def test_unit_any_outside_project_denied():
    # TST-1387 — one replacement outside Project/ causes entire operation to be denied
    data = {"tool_input": {"replacements": [
        _rep(PROJECT_FILE_1),
        _rep(OUTSIDE_FILE),   # docs/ — zone "deny" in 2-tier model
    ]}}
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


def test_unit_github_zone_denied():
    # TST-1388 — replacement targeting .github/ is denied
    data = {"tool_input": {"replacements": [_rep(GITHUB_FILE)]}}
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


def test_unit_noagentzone_denied():
    # TST-1389 — replacement targeting NoAgentZone/ is denied
    data = {"tool_input": {"replacements": [_rep(NOAGENT_FILE)]}}
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


def test_unit_vscode_zone_denied():
    # TST-1390 — replacement targeting .vscode/ is denied
    data = {"tool_input": {"replacements": [_rep(VSCODE_FILE)]}}
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


def test_unit_empty_replacements_denied():
    # TST-1391 — empty replacements list fails closed
    data = {"tool_input": {"replacements": []}}
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


def test_unit_no_replacements_key_denied():
    # TST-1392 — missing replacements key fails closed
    data = {"tool_input": {"explanation": "no replacements"}}
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


def test_unit_none_tool_input_denied():
    # TST-1393 — tool_input is None; no replacements
    data = {"tool_input": None}
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


def test_unit_replacement_missing_filepath_denied():
    # TST-1394 — replacement entry without a filePath key fails closed
    data = {"tool_input": {"replacements": [{"oldString": "a", "newString": "b"}]}}
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


def test_unit_replacement_empty_filepath_denied():
    # TST-1395 — replacement entry with empty filePath string fails closed
    data = {"tool_input": {"replacements": [{"filePath": "", "oldString": "a", "newString": "b"}]}}
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


def test_unit_top_level_replacements_fallback_allowed():
    # TST-1396 — replacements key at top level (fallback path) is accepted
    data = {"replacements": [_rep(PROJECT_FILE_1)]}
    assert sg.validate_multi_replace_tool(data, WS) == "allow"


# ===========================================================================
# Security — tool recognized via decide()  (TST-1397 to TST-1402)
# ===========================================================================

def test_security_recognized_in_decide_allow():
    # TST-1397 — multi_replace_string_in_file routed to validate_multi_replace_tool,
    # not validate_write_tool; single project-folder path is allowed
    data = _make_replace_payload([_rep(PROJECT_FILE_1)])
    assert sg.decide(data, WS) == "allow"


def test_security_recognized_in_decide_deny_outside():
    # TST-1398 — decide() denies when any path is outside Project/
    data = _make_replace_payload([_rep(PROJECT_FILE_1), _rep(OUTSIDE_FILE)])
    assert sg.decide(data, WS) == "deny"


def test_security_recognized_in_decide_deny_github():
    # TST-1399 — decide() denies when path targets .github/
    data = _make_replace_payload([_rep(GITHUB_FILE)])
    assert sg.decide(data, WS) == "deny"


def test_security_recognized_in_decide_deny_noagentzone():
    # TST-1400 — decide() denies when path targets NoAgentZone/
    data = _make_replace_payload([_rep(NOAGENT_FILE)])
    assert sg.decide(data, WS) == "deny"


def test_security_no_replacements_denied_via_decide():
    # TST-1401 — decide() denies multi_replace_string_in_file with no replacements
    data = {"tool_name": "multi_replace_string_in_file", "tool_input": {}}
    assert sg.decide(data, WS) == "deny"


def test_security_multiple_project_paths_decide_allow():
    # TST-1402 — decide() allows when all replacements target project folder
    data = _make_replace_payload([_rep(PROJECT_FILE_1), _rep(PROJECT_FILE_2)])
    assert sg.decide(data, WS) == "allow"


# ===========================================================================
# Bypass attempts  (TST-1403 to TST-1410)
# ===========================================================================

def test_bypass_path_traversal_in_replacement_denied():
    # TST-1403 — path traversal attempt via filePath is denied
    traversal = f"{WS}/project/../../.github/hooks/security_gate.py"
    data = _make_replace_payload([{"filePath": traversal, "oldString": "x", "newString": "y"}])
    assert sg.decide(data, WS) == "deny"


def test_bypass_all_good_except_last_denied():
    # TST-1404 — last entry is outside Project/; entire operation must be denied
    data = _make_replace_payload([
        _rep(PROJECT_FILE_1),
        _rep(PROJECT_FILE_2),
        _rep(GITHUB_FILE),  # last entry is restricted
    ])
    assert sg.decide(data, WS) == "deny"


def test_bypass_null_byte_in_filepath_denied():
    # TST-1405 — null byte in filePath targeting .github/ is denied after stripping.
    # Path: "/workspace/.github\x00/scripts/evil" → strip null → "/workspace/.github/scripts/evil" → deny
    data = _make_replace_payload([{"filePath": f"{WS}/.github\x00/scripts/evil", "oldString": "", "newString": ""}])
    assert sg.decide(data, WS) == "deny"


def test_bypass_non_dict_entry_denied():
    # TST-1406 — non-dict entry in replacements list fails closed
    data = {"tool_name": "multi_replace_string_in_file", "tool_input": {"replacements": ["not_a_dict"]}}
    assert sg.decide(data, WS) == "deny"


def test_bypass_non_list_replacements_denied():
    # TST-1407 — replacements is a string, not a list — fails closed
    data = {"tool_name": "multi_replace_string_in_file", "tool_input": {"replacements": "single_string"}}
    assert sg.decide(data, WS) == "deny"


def test_bypass_none_replacements_denied():
    # TST-1408 — replacements is None — fails closed
    data = {"tool_name": "multi_replace_string_in_file", "tool_input": {"replacements": None}}
    assert sg.decide(data, WS) == "deny"


def test_bypass_filepath_is_integer_denied():
    # TST-1409 — filePath is an integer, not a string — fails closed
    data = {"tool_name": "multi_replace_string_in_file", "tool_input": {
        "replacements": [{"filePath": 42, "oldString": "a", "newString": "b"}]
    }}
    assert sg.decide(data, WS) == "deny"


def test_bypass_double_backslash_github_denied():
    # TST-1410 — Windows-style backslash path targeting .github/ is denied
    data = _make_replace_payload([{
        "filePath": f"{WS_WIN}\\.github\\hooks\\security_gate.py",
        "oldString": "old",
        "newString": "new",
    }])
    assert sg.decide(data, WS_WIN) == "deny"


# ===========================================================================
# Cross-platform  (TST-1411 to TST-1414)
# ===========================================================================

def test_crossplatform_windows_project_path_allowed():
    # TST-1411 — Windows-style path inside Project/ is allowed
    data = _make_replace_payload([_rep(f"{WS_WIN}/project/src/main.py")])
    assert sg.decide(data, WS_WIN) == "allow"


def test_crossplatform_windows_backslash_project_allowed():
    # TST-1412 — Windows backslash path inside Project/ is allowed
    data = _make_replace_payload([{
        "filePath": f"{WS_WIN}\\project\\src\\main.py",
        "oldString": "old",
        "newString": "new",
    }])
    assert sg.decide(data, WS_WIN) == "allow"


def test_crossplatform_mixed_separators_project_allowed():
    # TST-1413 — mixed slash/backslash path inside Project/ is normalized and allowed
    data = _make_replace_payload([{
        "filePath": f"{WS_WIN}/project\\src/main.py",
        "oldString": "old",
        "newString": "new",
    }])
    assert sg.decide(data, WS_WIN) == "allow"


def test_crossplatform_windows_multiple_files_allowed():
    # TST-1414 — multiple Windows-style replacements all inside Project/ are allowed
    data = _make_replace_payload([
        _rep(f"{WS_WIN}/project/src/main.py"),
        _rep(f"{WS_WIN}/project/src/utils.py"),
        _rep(f"{WS_WIN}/project/tests/test_main.py"),
    ])
    assert sg.decide(data, WS_WIN) == "allow"


# ===========================================================================
# Integration — full decide() pipeline  (TST-1415 to TST-1419)
# ===========================================================================

def test_integration_in_exempt_tools():
    # TST-1415 — multi_replace_string_in_file is in _EXEMPT_TOOLS
    assert "multi_replace_string_in_file" in sg._EXEMPT_TOOLS


def test_integration_in_write_tools():
    # TST-1416 — multi_replace_string_in_file is in _WRITE_TOOLS
    assert "multi_replace_string_in_file" in sg._WRITE_TOOLS


def test_integration_validate_multi_replace_tool_is_callable():
    # TST-1417 — validate_multi_replace_tool is a callable function
    assert callable(sg.validate_multi_replace_tool)


def test_integration_does_not_route_to_validate_write_tool():
    # TST-1418 — multi_replace_string_in_file bypasses validate_write_tool;
    # validate_write_tool would deny (no filePath at top level of tool_input),
    # but decide() correctly routes to the new function and allows project paths.
    data = _make_replace_payload([_rep(PROJECT_FILE_1)])
    # validate_write_tool would return "deny" because extract_path returns None
    assert sg.validate_write_tool(data, WS) == "deny"  # confirm old path would fail
    # decide() must return "allow" — it uses the new routing
    assert sg.decide(data, WS) == "allow"


def test_integration_three_files_one_bad_denied():
    # TST-1419 — three replacements, one outside project; entire operation denied
    data = _make_replace_payload([
        _rep(f"{WS}/project/a.py"),
        _rep(f"{WS}/project/b.py"),
        _rep(f"{WS}/.vscode/settings.json"),  # restricted
    ])
    assert sg.decide(data, WS) == "deny"
