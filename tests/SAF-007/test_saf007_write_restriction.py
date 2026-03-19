"""Tests for SAF-007: Write Restriction Outside Project/

validate_write_tool() is implemented in security_gate.py and restricts
file-write tool calls to paths inside Project/ only.  Every other zone —
including "ask" (src/, docs/, tests/) and "deny" (.github/, .vscode/,
NoAgentZone/) — is denied.

Covers:
  - TST-364 to TST-378: Unit — validate_write_tool() (15 tests)
  - TST-379 to TST-388: Security — write tools intercepted (10 tests)
  - TST-389 to TST-399: Bypass attempts (11 tests)
  - TST-400 to TST-411: Cross-platform (12 tests)
  - TST-412 to TST-417: Integration — decide() pipeline (6 tests)
"""
from __future__ import annotations

import os
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
        "templates", "coding",
        ".github",
        "hooks",
        "scripts",
    )
)

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

# ---------------------------------------------------------------------------
# Workspace root constants used across all tests
# ---------------------------------------------------------------------------
WS = "/workspace"
WS_WIN = "c:/workspace"


# ===========================================================================
# Unit — validate_write_tool()  (TST-364 to TST-378)
# ===========================================================================

def test_unit_allows_project_root():
    # TST-364 — path pointing at the Project/ root itself is allowed
    data = {"filePath": f"{WS}/project"}
    assert sg.validate_write_tool(data, WS) == "allow"


def test_unit_allows_project_nested():
    # TST-365 — deeply nested path inside Project/ is allowed
    data = {"filePath": f"{WS}/project/src/main.py"}
    assert sg.validate_write_tool(data, WS) == "allow"


def test_unit_denies_docs_ask_zone():
    # TST-366 — docs/ is an "ask" zone; validate_write_tool must return "deny"
    # (stricter than the zone-only check which would return "ask")
    data = {"filePath": f"{WS}/docs/readme.md"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_unit_denies_src_ask_zone():
    # TST-367 — src/ is an "ask" zone; writes are denied
    data = {"filePath": f"{WS}/src/launcher/main.py"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_unit_denies_tests_ask_zone():
    # TST-368 — tests/ is an "ask" zone; writes are denied
    data = {"filePath": f"{WS}/tests/SAF-007/test_saf007.py"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_unit_denies_root_file_ask_zone():
    # TST-369 — file at workspace root is "ask" zone → deny
    data = {"filePath": f"{WS}/README.md"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_unit_denies_github_deny_zone():
    # TST-370 — .github/ is a hard "deny" zone; writes are denied
    data = {"filePath": f"{WS}/.github/hooks/security_gate.py"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_unit_denies_vscode_deny_zone():
    # TST-371 — .vscode/ is a hard "deny" zone; writes are denied
    data = {"filePath": f"{WS}/.vscode/settings.json"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_unit_denies_noagentzone_deny_zone():
    # TST-372 — NoAgentZone/ is a hard "deny" zone; writes are denied
    data = {"filePath": f"{WS}/noagentzone/private.md"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_unit_fails_closed_no_path():
    # TST-373 — no path field in payload → fail closed → deny
    data = {"tool_name": "create_file", "content": "hello"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_unit_uses_filepath_field():
    # TST-374 — filePath is the first-priority path field → allow
    data = {"filePath": f"{WS}/project/app.py", "file_path": "other.py"}
    assert sg.validate_write_tool(data, WS) == "allow"


def test_unit_uses_file_path_field():
    # TST-375 — file_path used when filePath is absent → allow
    data = {"file_path": f"{WS}/project/app.py"}
    assert sg.validate_write_tool(data, WS) == "allow"


def test_unit_uses_directory_field():
    # TST-376 — directory field used when filePath and file_path are absent → allow
    data = {"directory": f"{WS}/project/src"}
    assert sg.validate_write_tool(data, WS) == "allow"


def test_unit_nested_tool_input_path_allowed():
    # TST-377 — path inside tool_input nested dict → Project/ → allow
    data = {"tool_input": {"filePath": f"{WS}/project/x.py"}}
    assert sg.validate_write_tool(data, WS) == "allow"


def test_unit_nested_tool_input_path_denied():
    # TST-378 — path inside tool_input nested dict → docs/ → deny
    data = {"tool_input": {"filePath": f"{WS}/docs/readme.md"}}
    assert sg.validate_write_tool(data, WS) == "deny"


# ===========================================================================
# Security — write tools intercepted  (TST-379 to TST-388)
# ===========================================================================

def test_security_create_file_project_allowed():
    # TST-379 — create_file inside Project/ is allowed
    data = {"tool_name": "create_file", "filePath": f"{WS}/project/new_module.py"}
    assert sg.validate_write_tool(data, WS) == "allow"


def test_security_create_file_outside_denied():
    # TST-380 — create_file outside Project/ (src/ = "ask") is denied
    data = {"tool_name": "create_file", "filePath": f"{WS}/src/new_file.py"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_security_write_file_outside_denied():
    # TST-381 — write_file targeting docs/ ("ask" zone) is denied
    data = {"tool_name": "write_file", "filePath": f"{WS}/docs/new.md"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_security_replace_string_in_file_project_allowed():
    # TST-382 — replace_string_in_file inside Project/ is allowed
    data = {"tool_name": "replace_string_in_file", "filePath": f"{WS}/project/app.py"}
    assert sg.validate_write_tool(data, WS) == "allow"


def test_security_replace_string_in_file_outside_denied():
    # TST-383 — replace_string_in_file on docs/ ("ask" zone) is denied
    data = {"tool_name": "replace_string_in_file", "filePath": f"{WS}/docs/readme.md"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_security_multi_replace_project_allowed():
    # TST-384 — multi_replace_string_in_file inside Project/ is allowed
    data = {"tool_name": "multi_replace_string_in_file", "filePath": f"{WS}/project/config.py"}
    assert sg.validate_write_tool(data, WS) == "allow"


def test_security_multi_replace_outside_denied():
    # TST-385 — multi_replace_string_in_file on src/ ("ask" zone) is denied
    data = {"tool_name": "multi_replace_string_in_file", "filePath": f"{WS}/src/launcher/main.py"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_security_edit_file_project_allowed():
    # TST-386 — edit_file inside Project/ is allowed
    data = {"tool_name": "edit_file", "filePath": f"{WS}/project/models.py"}
    assert sg.validate_write_tool(data, WS) == "allow"


def test_security_edit_file_outside_denied():
    # TST-387 — edit_file on src/ ("ask" zone) is denied
    data = {"tool_name": "edit_file", "filePath": f"{WS}/src/launcher/config.py"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_security_edit_capitalized_denied_outside():
    # TST-388 — "Edit" (capitalized VS Code tool alias) targeting .vscode/ is denied
    data = {"tool_name": "Edit", "filePath": f"{WS}/.vscode/settings.json"}
    assert sg.validate_write_tool(data, WS) == "deny"


# ===========================================================================
# Bypass attempt tests  (TST-389 to TST-399)
# ===========================================================================

def test_bypass_path_traversal_project_to_docs():
    # TST-389 — "project/../docs/readme.md" resolves to docs/ ("ask") → deny
    data = {"filePath": f"{WS}/project/../docs/readme.md"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_bypass_deep_traversal_to_github():
    # TST-390 — deep traversal escaping workspace must resolve and be denied
    data = {"filePath": f"{WS}/project/../../../../.github/secret"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_bypass_prefix_sibling_project_evil():
    # TST-391 — "project-evil/" must NOT be treated as Project/
    # pathlib.relative_to() rejects sibling-prefix paths that startswith() would pass
    data = {"filePath": f"{WS}/project-evil/payload.py"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_bypass_null_byte_before_dot_github():
    # TST-392 — null byte before .github must be stripped; resulting path is denied
    data = {"filePath": f"{WS}/\x00.github/secret"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_bypass_mixed_case_project_still_allowed():
    # TST-393 — "PROJECT/" lowercased to "project/" by normalizer → allow
    # Verifies case normalization does not block legitimate mixed-case input
    data = {"filePath": f"{WS}/PROJECT/app.py"}
    assert sg.validate_write_tool(data, WS) == "allow"


def test_bypass_unc_path_targeting_docs():
    # TST-394 — UNC path targeting docs on a foreign host; cannot be granted
    # "allow" (zone_classifier requires path to start with ws_root) → deny
    data = {"filePath": "\\\\server\\share\\docs\\readme.md"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_bypass_json_escaped_backslash_to_docs():
    # TST-395 — double-backslash (JSON-escaped) path to docs/ normalizes to
    # "/workspace/docs/readme.md" which is "ask" zone → deny
    raw_path = WS + "\\\\" + "docs" + "\\\\" + "readme.md"
    data = {"filePath": raw_path}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_bypass_traversal_starting_inside_project():
    # TST-396 — "project/subdir/../../docs/readme.md" resolves to docs/ → deny
    data = {"filePath": f"{WS}/project/subdir/../../docs/readme.md"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_bypass_null_byte_inside_project_path_allowed():
    # TST-397 — null byte prepended to a valid absolute project path; after C0
    # stripping the remaining path is genuinely inside Project/ → allow
    data = {"filePath": "\x00" + f"{WS}/project/app.py"}
    assert sg.validate_write_tool(data, WS) == "allow"


def test_bypass_mixed_case_vscode_still_denied():
    # TST-398 — ".VSCODE" is lowercased to ".vscode" by normalizer → deny
    data = {"filePath": f"{WS}/.VSCODE/settings.json"}
    assert sg.validate_write_tool(data, WS) == "deny"


def test_bypass_project_sibling_with_nested_github():
    # TST-399 — "project-evil/.github/x" must be denied via Method 2 pattern search
    data = {"filePath": f"{WS}/project-evil/.github/payload.py"}
    assert sg.validate_write_tool(data, WS) == "deny"


# ===========================================================================
# Cross-platform tests  (TST-400 to TST-411)
# ===========================================================================

def test_crossplat_windows_project_allowed():
    # TST-400 — Windows absolute path inside Project/ with ws = "c:/workspace"
    data = {"filePath": "C:\\workspace\\project\\app.py"}
    assert sg.validate_write_tool(data, WS_WIN) == "allow"


def test_crossplat_windows_outside_denied():
    # TST-401 — Windows absolute path inside docs/ with ws = "c:/workspace" → deny
    data = {"filePath": "C:\\workspace\\docs\\readme.md"}
    assert sg.validate_write_tool(data, WS_WIN) == "deny"


def test_crossplat_windows_github_denied():
    # TST-402 — Windows absolute path inside .github/ → deny
    data = {"filePath": "C:\\workspace\\.github\\secret"}
    assert sg.validate_write_tool(data, WS_WIN) == "deny"


def test_crossplat_windows_vscode_denied():
    # TST-403 — Windows absolute path inside .vscode/ → deny
    data = {"filePath": "C:\\workspace\\.vscode\\settings.json"}
    assert sg.validate_write_tool(data, WS_WIN) == "deny"


def test_crossplat_wsl_project_allowed():
    # TST-404 — WSL /mnt/c/... path inside Project/ → allow
    data = {"filePath": "/mnt/c/workspace/project/app.py"}
    assert sg.validate_write_tool(data, WS_WIN) == "allow"


def test_crossplat_wsl_outside_denied():
    # TST-405 — WSL /mnt/c/... path inside docs/ → deny
    data = {"filePath": "/mnt/c/workspace/docs/readme.md"}
    assert sg.validate_write_tool(data, WS_WIN) == "deny"


def test_crossplat_wsl_github_denied():
    # TST-406 — WSL /mnt/c/... path inside .github/ → deny
    data = {"filePath": "/mnt/c/workspace/.github/secret"}
    assert sg.validate_write_tool(data, WS_WIN) == "deny"


def test_crossplat_gitbash_project_allowed():
    # TST-407 — Git Bash /c/... path inside Project/ → allow
    data = {"filePath": "/c/workspace/project/app.py"}
    assert sg.validate_write_tool(data, WS_WIN) == "allow"


def test_crossplat_gitbash_outside_denied():
    # TST-408 — Git Bash /c/... path inside docs/ → deny
    data = {"filePath": "/c/workspace/docs/readme.md"}
    assert sg.validate_write_tool(data, WS_WIN) == "deny"


def test_crossplat_gitbash_github_denied():
    # TST-409 — Git Bash /c/... path inside .github/ → deny
    data = {"filePath": "/c/workspace/.github/secret"}
    assert sg.validate_write_tool(data, WS_WIN) == "deny"


def test_crossplat_windows_all_backslashes_project():
    # TST-410 — Windows native single-backslash path to nested project file → allow
    data = {"filePath": "C:\\workspace\\project\\sub\\module.py"}
    assert sg.validate_write_tool(data, WS_WIN) == "allow"


def test_crossplat_windows_json_escaped_backslash_outside():
    # TST-411 — Windows JSON double-escaped backslash path to docs/ → deny
    raw_path = "C:" + "\\\\" + "workspace" + "\\\\" + "docs" + "\\\\" + "readme.md"
    data = {"filePath": raw_path}
    assert sg.validate_write_tool(data, WS_WIN) == "deny"


# ===========================================================================
# Integration — full decide() pipeline  (TST-412 to TST-417)
# ===========================================================================

def test_integration_decide_create_file_project():
    # TST-412 — decide() routes create_file to validate_write_tool; Project/ → allow
    data = {"tool_name": "create_file", "filePath": f"{WS}/project/new.py"}
    assert sg.decide(data, WS) == "allow"


def test_integration_decide_create_file_docs():
    # TST-413 — decide() routes create_file to validate_write_tool; docs/ → deny
    data = {"tool_name": "create_file", "filePath": f"{WS}/docs/new_doc.md"}
    assert sg.decide(data, WS) == "deny"


def test_integration_write_tool_no_path_fails_closed():
    # TST-414 — write tool with no path field in payload → decide() fails closed → deny
    data = {"tool_name": "replace_string_in_file", "old_string": "foo", "new_string": "bar"}
    assert sg.decide(data, WS) == "deny"


def test_integration_write_tool_intercepted_before_exempt_check():
    # TST-415 — replace_string_in_file is also in _EXEMPT_TOOLS; without SAF-007
    # the exempt-tool branch would zone-check docs/ and return "ask".  With SAF-007
    # the _WRITE_TOOLS branch runs first and denies docs/ paths.
    data = {"tool_name": "replace_string_in_file", "filePath": f"{WS}/docs/readme.md"}
    assert sg.decide(data, WS) == "deny"


def test_integration_edit_notebook_file_not_in_write_tools_asks():
    # TST-416 — edit_notebook_file is NOT in _WRITE_TOOLS and NOT in _EXEMPT_TOOLS;
    # decide() categorises it as a non-exempt unknown tool → "deny" in 2-tier model (SAF-013)
    data = {"tool_name": "edit_notebook_file", "filePath": f"{WS}/project/nb.ipynb"}
    assert sg.decide(data, WS) == "deny"


def test_integration_write_tools_frozenset_contains_expected_tools():
    # TST-417 — all expected write tool names must be present in _WRITE_TOOLS
    expected = {
        "create_file", "write_file", "Write",
        "edit_file", "Edit",
        "replace_string_in_file", "multi_replace_string_in_file",
    }
    assert expected.issubset(sg._WRITE_TOOLS)
