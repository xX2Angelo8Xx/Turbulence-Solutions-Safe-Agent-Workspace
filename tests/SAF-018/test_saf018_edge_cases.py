"""SAF-018 — Tester edge-case tests for multi_replace_string_in_file.

Additional tests beyond the Developer's 35 test suite.

Covers:
- TST-1420: Very large replacements array (100 entries all in Project/)
- TST-1421: Very large replacements array with one bad entry at end
- TST-1422: Unicode filePath inside Project/ is allowed
- TST-1423: Unicode filePath outside Project/ is denied
- TST-1424: filePath value is a list (not a string)
- TST-1425: filePath value is None explicitly
- TST-1426: filePath value is whitespace-only string
- TST-1427: tool_input is a list (not dict) — fails closed
- TST-1428: data is empty dict — fails closed
- TST-1429: replacements is a dict (not a list) — fails closed
- TST-1430: replacements is a number — fails closed
- TST-1431: replacements contains mixed types (dict + string + None)
- TST-1432: Single replacement where filePath key has wrong case (FILE_PATH)
- TST-1433: Deeply nested path traversal ../../.github denied
- TST-1434: filePath with double slashes inside Project/ is normalized and allowed
- TST-1435: top-level replacements fallback with invalid filepath denied
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make security_gate (and zone_classifier) importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "Default-Project"
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


def _rep(file_path: str) -> dict:
    """Build a minimal replacement entry."""
    return {"filePath": file_path, "oldString": "old", "newString": "new"}


def _payload(replacements: list) -> dict:
    return {
        "tool_name": "multi_replace_string_in_file",
        "tool_input": {"replacements": replacements, "explanation": "edge case"},
    }


# ===========================================================================
# TST-1420 — Very large replacements array (100 entries all in Project/)
# ===========================================================================

def test_edge_large_array_all_project_allowed():
    # TST-1420 — 100 replacements all inside Project/ must be allowed
    replacements = [_rep(f"{WS}/project/src/file{i}.py") for i in range(100)]
    data = _payload(replacements)
    assert sg.validate_multi_replace_tool(data, WS) == "allow"


# ===========================================================================
# TST-1421 — Large array with one bad entry at end
# ===========================================================================

def test_edge_large_array_one_bad_at_end_denied():
    # TST-1421 — 99 good + 1 outside Project/ at the end; entire op denied
    replacements = [_rep(f"{WS}/project/src/file{i}.py") for i in range(99)]
    replacements.append(_rep(f"{WS}/.github/hooks/evil.py"))
    data = _payload(replacements)
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


# ===========================================================================
# TST-1422 — Unicode filePath inside Project/ is allowed
# ===========================================================================

def test_edge_unicode_filepath_inside_project_allowed():
    # TST-1422 — Unicode characters in filename inside Project/ should be allowed
    data = _payload([_rep(f"{WS}/project/src/módulo_principal.py")])
    assert sg.validate_multi_replace_tool(data, WS) == "allow"


# ===========================================================================
# TST-1423 — Unicode filePath outside Project/ is denied
# ===========================================================================

def test_edge_unicode_filepath_outside_project_denied():
    # TST-1423 — Unicode characters in filename outside Project/ should be denied
    data = _payload([_rep(f"{WS}/.github/scripts/злой.py")])
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


# ===========================================================================
# TST-1424 — filePath value is a list (not a string)
# ===========================================================================

def test_edge_filepath_is_list_denied():
    # TST-1424 — filePath is a list — fails closed (not isinstance str)
    data = _payload([{
        "filePath": [f"{WS}/project/src/main.py"],
        "oldString": "a",
        "newString": "b",
    }])
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


# ===========================================================================
# TST-1425 — filePath value is None explicitly
# ===========================================================================

def test_edge_filepath_is_none_denied():
    # TST-1425 — filePath explicitly set to None — fails closed
    data = _payload([{"filePath": None, "oldString": "a", "newString": "b"}])
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


# ===========================================================================
# TST-1426 — filePath is whitespace-only string
# ===========================================================================

def test_edge_filepath_whitespace_only_denied():
    # TST-1426 — filePath is only spaces — zone_classifier should deny
    # (empty/whitespace paths cannot resolve to a valid project folder path)
    data = _payload([{"filePath": "   ", "oldString": "a", "newString": "b"}])
    result = sg.validate_multi_replace_tool(data, WS)
    # Whitespace path does not start with project folder prefix; must be denied
    assert result == "deny"


# ===========================================================================
# TST-1427 — tool_input is a list (not dict)
# ===========================================================================

def test_edge_tool_input_is_list_denied():
    # TST-1427 — tool_input is a list instead of dict; no replacements found
    data = {
        "tool_name": "multi_replace_string_in_file",
        "tool_input": [_rep(f"{WS}/project/src/main.py")],
    }
    # tool_input is not a dict, so falls through to deny
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


# ===========================================================================
# TST-1428 — data is empty dict
# ===========================================================================

def test_edge_empty_data_dict_denied():
    # TST-1428 — completely empty data dict — no tool_input, no replacements
    data: dict = {}
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


# ===========================================================================
# TST-1429 — replacements is a dict (not a list)
# ===========================================================================

def test_edge_replacements_is_dict_denied():
    # TST-1429 — replacements is a dict rather than a list — fails closed
    data = {
        "tool_name": "multi_replace_string_in_file",
        "tool_input": {
            "replacements": {
                "filePath": f"{WS}/project/src/main.py",
                "oldString": "a",
                "newString": "b",
            },
        },
    }
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


# ===========================================================================
# TST-1430 — replacements is a number
# ===========================================================================

def test_edge_replacements_is_number_denied():
    # TST-1430 — replacements is an integer — fails closed
    data = {
        "tool_name": "multi_replace_string_in_file",
        "tool_input": {"replacements": 42},
    }
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


# ===========================================================================
# TST-1431 — replacements list contains mixed types
# ===========================================================================

def test_edge_replacements_mixed_types_denied():
    # TST-1431 — list has a valid dict entry, a string, and a None;
    # non-dict entries must cause deny
    data = _payload([
        _rep(f"{WS}/project/src/main.py"),
        "this_is_not_a_dict",
        None,
    ])
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


# ===========================================================================
# TST-1432 — filePath key with wrong case is not recognized
# ===========================================================================

def test_edge_filepath_wrong_case_key_denied():
    # TST-1432 — "FILE_PATH" (wrong case) is not the "filePath" key;
    # entry has no valid filePath → fails closed
    data = _payload([{
        "FILE_PATH": f"{WS}/project/src/main.py",
        "oldString": "a",
        "newString": "b",
    }])
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


# ===========================================================================
# TST-1433 — Deeply nested path traversal targeting .github
# ===========================================================================

def test_edge_deep_traversal_github_denied():
    # TST-1433 — multi-level ../ traversal that escapes the project folder and
    # reaches the workspace-root-level .github/.
    # Path: /workspace/project/src/a/b/c/../../../../../.github/hooks/evil.py
    # 5 x '..' from src/a/b/c: c→b→a→src→project→workspace, then .github/
    # Normal form: /workspace/.github/hooks/evil.py  → deny
    traversal = f"{WS}/project/src/a/b/c/../../../../../.github/hooks/evil.py"
    data = _payload([{"filePath": traversal, "oldString": "x", "newString": "y"}])
    assert sg.validate_multi_replace_tool(data, WS) == "deny"


# ===========================================================================
# TST-1434 — filePath with double slashes inside Project/ normalized and allowed
# ===========================================================================

def test_edge_double_slash_in_project_allowed():
    # TST-1434 — zone_classifier normalizes double slashes; must not cause deny
    data = _payload([_rep(f"{WS}/project//src//main.py")])
    # Should be treated as equivalent to project/src/main.py → allow
    assert sg.validate_multi_replace_tool(data, WS) == "allow"


# ===========================================================================
# TST-1435 — top-level replacements fallback with invalid filepath denied
# ===========================================================================

def test_edge_top_level_fallback_invalid_filepath_denied():
    # TST-1435 — replacements at top level with a path outside Project/ denied
    data = {
        "tool_name": "multi_replace_string_in_file",
        "replacements": [_rep(f"{WS}/.github/hooks/evil.py")],
    }
    assert sg.validate_multi_replace_tool(data, WS) == "deny"
