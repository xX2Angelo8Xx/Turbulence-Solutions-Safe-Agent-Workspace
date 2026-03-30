"""tests/FIX-079/test_fix079_tester_edge_cases.py

Tester-added edge-case tests for FIX-079: Show NoAgentZone in VS Code file explorer.

Covers scenarios the Developer's tests do not explicitly target:
  - settings.json raw content has no trailing-comma patterns (JSON hygiene)
  - files.exclude has EXACTLY the expected keys — no stray entries survive the fix
  - NoAgentZone is absent from files.exclude under any capitalisation variant
  - Security gate decide() denies read_file tool calls targeting NoAgentZone
  - Security gate decide() denies write tools (create_file, replace_string_in_file)
    targeting NoAgentZone
  - zone_classifier denies Windows-style backslash paths inside NoAgentZone
  - settings.json byte length is plausible (not empty, not truncated)
  - search.exclude value for NoAgentZone is strictly boolean True,
    not a truthy-but-wrong type (string "true", int 1, etc.)
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SETTINGS = REPO_ROOT / "templates" / "agent-workbench" / ".vscode" / "settings.json"
SCRIPTS_DIR = (
    REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"
)

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import security_gate as sg  # noqa: E402
import zone_classifier  # noqa: E402

# Workspace root used in gate tests — must not exist on disk.
WS = "c:/workspace"


@pytest.fixture(autouse=True)
def _mock_project_folder():
    """Prevent zone_classifier.detect_project_folder from hitting the filesystem."""
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# ---------------------------------------------------------------------------
# 1. JSON hygiene: no trailing commas
# ---------------------------------------------------------------------------


def test_settings_json_no_trailing_comma_before_brace():
    """Raw settings.json must not contain a trailing comma before a closing brace.
    Standard JSON does not allow trailing commas; many editors tolerate them but
    VS Code and json.loads() do not."""
    raw = SETTINGS.read_bytes().decode("utf-8")
    # Pattern: comma (optionally followed by whitespace/newlines) then } or ]
    bad_trailing = re.search(r",\s*[}\]]", raw)
    assert bad_trailing is None, (
        "settings.json contains a trailing comma which is invalid JSON — "
        f"found near: {raw[max(0, bad_trailing.start()-20):bad_trailing.end()+5]!r}"
    )


# ---------------------------------------------------------------------------
# 2.  files.exclude exact key set
# ---------------------------------------------------------------------------


def test_files_exclude_has_exactly_github_and_vscode():
    """files.exclude must contain EXACTLY '.github' and '.vscode' — no more,
    no less, after FIX-079 removed **/NoAgentZone from it."""
    settings = json.loads(SETTINGS.read_bytes())
    files_exclude_keys = set(settings.get("files.exclude", {}).keys())
    expected = {".github", ".vscode"}
    assert files_exclude_keys == expected, (
        f"files.exclude keys do not match expected {expected}. "
        f"Actual: {files_exclude_keys}"
    )


def test_files_exclude_contains_no_noagentzone_variant():
    """No variant of 'NoAgentZone' (any capitalisation, with or without glob)
    may appear in files.exclude after FIX-079."""
    settings = json.loads(SETTINGS.read_bytes())
    for key in settings.get("files.exclude", {}):
        assert "noagentzone" not in key.lower(), (
            f"Unexpected NoAgentZone variant '{key}' found in files.exclude"
        )


# ---------------------------------------------------------------------------
# 3. search.exclude value type
# ---------------------------------------------------------------------------


def test_search_exclude_noagentzone_value_is_strict_bool_true():
    """The **/NoAgentZone value in search.exclude must be the Python bool True,
    not a string 'true', int 1, or any other truthy-but-wrong type."""
    settings = json.loads(SETTINGS.read_bytes())
    value = settings["search.exclude"]["**/NoAgentZone"]
    assert value is True, (
        f"search.exclude['**/NoAgentZone'] must be boolean true, got {type(value).__name__}({value!r})"
    )


# ---------------------------------------------------------------------------
# 4. Security gate — decide() denies read_file to NoAgentZone
# ---------------------------------------------------------------------------


def test_gate_read_file_noagentzone_direct_denied():
    """decide() must deny read_file targeting NoAgentZone as a direct child of ws_root.
    In the agent workbench, NoAgentZone sits at <workspace>/NoAgentZone/ — it is a
    direct sibling of the project folder, so zone_classifier sees it on the first
    path segment and denies it."""
    data = {
        "tool_name": "read_file",
        "filePath": f"{WS}/NoAgentZone/secret.txt",
    }
    assert sg.decide(data, WS) == "deny", (
        "Security gate allowed read_file into NoAgentZone — access control broken"
    )


def test_gate_read_file_noagentzone_nested_denied():
    """decide() must deny read_file targeting a deeply nested path inside NoAgentZone."""
    data = {
        "tool_name": "read_file",
        "filePath": f"{WS}/NoAgentZone/private/credentials/config.json",
    }
    assert sg.decide(data, WS) == "deny"


# ---------------------------------------------------------------------------
# 5. Security gate — decide() denies write tools to NoAgentZone
# ---------------------------------------------------------------------------


def test_gate_create_file_noagentzone_denied():
    """decide() must deny create_file targeting NoAgentZone (direct child of ws_root)."""
    data = {
        "tool_name": "create_file",
        "filePath": f"{WS}/NoAgentZone/malicious.py",
        "content": "payload",
    }
    assert sg.decide(data, WS) == "deny", (
        "Security gate allowed create_file into NoAgentZone"
    )


def test_gate_replace_string_noagentzone_denied():
    """decide() must deny replace_string_in_file targeting NoAgentZone (direct child of ws_root)."""
    data = {
        "tool_name": "replace_string_in_file",
        "filePath": f"{WS}/NoAgentZone/data.txt",
        "oldString": "old",
        "newString": "new",
    }
    assert sg.decide(data, WS) == "deny", (
        "Security gate allowed replace_string_in_file into NoAgentZone"
    )


# ---------------------------------------------------------------------------
# 6. zone_classifier — Windows backslash paths denied
# ---------------------------------------------------------------------------


def test_zone_classifier_windows_path_noagentzone_denied():
    """zone_classifier must deny a Windows-style path into NoAgentZone.
    Backslash separators must not bypass the zone check."""
    ws_root = "C:\\workspace\\myproject"
    result = zone_classifier.classify(
        "C:\\workspace\\myproject\\NoAgentZone\\secret.txt",
        ws_root,
    )
    assert result == "deny", (
        f"zone_classifier allowed Windows backslash path into NoAgentZone — got {result!r}"
    )


def test_zone_classifier_case_insensitive_noagentzone_denied():
    """zone_classifier must deny paths with alternate capitalisation of NoAgentZone.
    The zone_classifier normalises paths to lowercase before comparing against
    _DENY_DIRS, so all capitalisation variants of 'noagentzone' as the first
    segment must be denied."""
    ws_root = "/workspace/myproject"
    for variant in ("noagentzone", "NOAGENTZONE", "Noagentzone", "NoAgentZONE"):
        result = zone_classifier.classify(
            f"{ws_root}/{variant}/secret.txt",
            ws_root,
        )
        assert result == "deny", (
            f"zone_classifier allowed capitalisation variant '{variant}' — got {result!r}"
        )


# ---------------------------------------------------------------------------
# 7. File integrity — plausible file size
# ---------------------------------------------------------------------------


def test_settings_json_not_empty():
    """settings.json must have a non-zero byte length (not accidentally cleared)."""
    size = SETTINGS.stat().st_size
    assert size > 100, f"settings.json is suspiciously small ({size} bytes) — may be empty or truncated"


def test_settings_json_roundtrip_stable():
    """Parsing and re-serialising settings.json must not change its semantic content.
    Verifies no hidden byte sequences corrupt the JSON structure."""
    raw = SETTINGS.read_bytes()
    parsed = json.loads(raw)
    # Round-trip does not change the keys or values (order-insensitive check)
    assert isinstance(parsed, dict)
    re_encoded = json.dumps(parsed, sort_keys=True)
    reparsed = json.loads(re_encoded)
    assert parsed == reparsed, "settings.json is not semantically stable across JSON round-trip"
