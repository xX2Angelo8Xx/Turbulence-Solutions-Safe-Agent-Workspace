"""SAF-009 Tester Edge-Case Tests

Additional edge-case and boundary tests added by the Tester Agent
during review of SAF-009 (cross-platform test suite).

These tests target scenarios not covered by the Developer's 50-test suite:
  - Alternative path field names (`path`, `file_path`) in zone checking
  - includeIgnoredFiles=True in VS Code nested tool_input format
  - tree command as another AF-4 recursive enumeration vector
  - decide() with empty payload (fail-safe check)
  - Write tool using `path` field (not filePath) denied outside Project/
"""
from __future__ import annotations

import os
import sys

# ---------------------------------------------------------------------------
# Make security_gate importable
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

WS = "/workspace"
WS_WIN = "c:/workspace"


# ---------------------------------------------------------------------------
# EC-1: `path` field alternative to `filePath`
# The _PATH_FIELDS tuple includes "path" — it must be respected in zone checks.
# ---------------------------------------------------------------------------

def test_path_field_project_allowed():
    """TST-EC-SAF009-01 — 'path' field targeting Project/ → allow."""
    data = {"tool_name": "read_file", "path": f"{WS}/project/main.py"}
    assert sg.decide(data, WS) == "allow"


def test_path_field_github_denied():
    """TST-EC-SAF009-02 — 'path' field targeting .github/ → deny."""
    data = {"tool_name": "read_file", "path": f"{WS}/.github/secret"}
    assert sg.decide(data, WS) == "deny"


# ---------------------------------------------------------------------------
# EC-2: `file_path` (underscore) alternative field
# _PATH_FIELDS includes "file_path" for compatibility.
# ---------------------------------------------------------------------------

def test_file_path_underscore_field_project_allowed():
    """TST-EC-SAF009-03 — 'file_path' (underscore) field targeting Project/ → allow."""
    data = {"tool_name": "read_file", "file_path": f"{WS}/project/config.py"}
    assert sg.decide(data, WS) == "allow"


def test_file_path_underscore_field_vscode_denied():
    """TST-EC-SAF009-04 — 'file_path' (underscore) field targeting .vscode/ → deny."""
    data = {"tool_name": "read_file", "file_path": f"{WS}/.vscode/settings.json"}
    assert sg.decide(data, WS) == "deny"


# ---------------------------------------------------------------------------
# EC-3: includeIgnoredFiles=True in VS Code nested tool_input format
# The Developer tested flat format (TST-540); nested format must also deny.
# ---------------------------------------------------------------------------

def test_include_ignored_files_nested_format_denied():
    """TST-EC-SAF009-05 — includeIgnoredFiles=True in nested tool_input → deny."""
    data = {
        "tool_name": "grep_search",
        "tool_input": {
            "query": "password",
            "includeIgnoredFiles": True,
        },
    }
    assert sg.decide(data, WS) == "deny"


# ---------------------------------------------------------------------------
# EC-4: tree command as AF-4 recursive enumeration vector
# `tree` is a recursive enumeration command; targeting workspace root
# (ancestor of deny zones) must be denied.
# ---------------------------------------------------------------------------

def test_af4_tree_command_blocked():
    """TST-EC-SAF009-06 — `tree /workspace` recursive enumeration → deny."""
    decision, _ = sg.sanitize_terminal_command(f"tree {WS}", WS)
    assert decision == "deny"


# ---------------------------------------------------------------------------
# EC-5: decide() with completely empty payload
# No tool_name, no path — fail-safe must not be "allow".
# For a non-exempt/non-always-allow tool, no path defaults to "ask".
# ---------------------------------------------------------------------------

def test_decide_empty_dict_not_allow():
    """TST-EC-SAF009-07 — decide({}, WS) must not return 'allow' (fail-safe)."""
    result = sg.decide({}, WS)
    assert result != "allow", f"Empty payload should not be auto-allowed; got {result!r}"


# ---------------------------------------------------------------------------
# EC-6: Write tool using `path` field (not filePath) denied outside Project/
# _WRITE_TOOLS branch calls extract_paths_from_payload which reads _PATH_FIELDS.
# The `path` field variant must trigger the SAF-007 write restriction.
# ---------------------------------------------------------------------------

def test_write_tool_path_field_outside_project_denied():
    """TST-EC-SAF009-08 — create_file with 'path' field outside Project/ → deny."""
    data = {"tool_name": "create_file", "path": f"{WS}/docs/notes.md"}
    assert sg.decide(data, WS) == "deny"


def test_write_tool_path_field_inside_project_allowed():
    """TST-EC-SAF009-09 — create_file with 'path' field inside Project/ → allow."""
    data = {"tool_name": "create_file", "path": f"{WS}/project/new_file.py"}
    assert sg.decide(data, WS) == "allow"
