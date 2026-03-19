"""SAF-013 Tester edge-case tests — 2-Tier Security Gate

Additional tests beyond the Developer's baseline.  Focus areas:
- Case-variation bypass attempts (.GITHUB, .Vscode, NOAGENTZONE)
- Path-traversal bypass attempts (project/../.github/)
- Root-level workspace file handling (no subfolder)
- Always-allow tools are never blocked regardless of path
- Write-tool restrictions for .vscode and NoAgentZone
- grep_search with includeIgnoredFiles=true
- grep_search with includePattern targeting .github
- Terminal command targeting .github path
- Brute-force "ask" string absence across all decision branches
- decide() with empty tool name
- decide() for exempt read tools at .vscode path
- Verify validate_grep_search returns allow for project-scoped includePattern
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "coding"
    / ".github"
    / "hooks"
    / "scripts"
)

WS = "c:/workspace"


@pytest.fixture(scope="module")
def sg():
    if SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, SCRIPTS_DIR)
    import security_gate as _sg
    return _sg


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# ---------------------------------------------------------------------------
# 1. Case-variation bypass — uppercase zone names must still be denied
# ---------------------------------------------------------------------------

def test_decide_github_uppercase_returns_deny(sg):
    """.GITHUB (uppercase) must be denied — case normalization required."""
    data = {
        "tool_name": "read_file",
        "tool_input": {"filePath": f"{WS}/.GITHUB/hooks/settings.json"},
    }
    result = sg.decide(data, WS)
    assert result == "deny", (
        f"decide() returned {result!r} for .GITHUB (uppercase) — expected 'deny'"
    )


def test_decide_vscode_mixed_case_returns_deny(sg):
    """.Vscode (mixed case) must be denied."""
    data = {
        "tool_name": "read_file",
        "tool_input": {"filePath": f"{WS}/.Vscode/settings.json"},
    }
    result = sg.decide(data, WS)
    assert result == "deny", (
        f"decide() returned {result!r} for .Vscode (mixed case) — expected 'deny'"
    )


def test_decide_noagentzone_uppercase_returns_deny(sg):
    """NoAgentZone (uppercase N) must be denied."""
    data = {
        "tool_name": "read_file",
        "tool_input": {"filePath": f"{WS}/NoAgentZone/secret.txt"},
    }
    result = sg.decide(data, WS)
    assert result == "deny", (
        f"decide() returned {result!r} for NoAgentZone — expected 'deny'"
    )


# ---------------------------------------------------------------------------
# 2. Path traversal — project/../.github/ must not "allow" .github
# ---------------------------------------------------------------------------

def test_decide_path_traversal_to_github_returns_deny(sg):
    """project/../.github/ is a traversal attempt — must return deny."""
    data = {
        "tool_name": "read_file",
        "tool_input": {"filePath": f"{WS}/project/../.github/hooks/pre-tool-use"},
    }
    result = sg.decide(data, WS)
    assert result == "deny", (
        f"decide() returned {result!r} for path traversal to .github — expected 'deny'"
    )


def test_decide_path_traversal_to_vscode_returns_deny(sg):
    """project/../.vscode/ is a traversal attempt — must return deny."""
    data = {
        "tool_name": "read_file",
        "tool_input": {"filePath": f"{WS}/project/../.vscode/settings.json"},
    }
    result = sg.decide(data, WS)
    assert result == "deny", (
        f"decide() returned {result!r} for path traversal to .vscode — expected 'deny'"
    )


# ---------------------------------------------------------------------------
# 3. Root-level workspace files (no subfolder) must be denied
# ---------------------------------------------------------------------------

def test_decide_root_level_file_returns_deny(sg):
    """A file directly in workspace root (no subfolder) must return deny."""
    data = {
        "tool_name": "read_file",
        "tool_input": {"filePath": f"{WS}/README.md"},
    }
    result = sg.decide(data, WS)
    assert result == "deny", (
        f"decide() returned {result!r} for root-level file — expected 'deny'"
    )


def test_decide_workspace_root_itself_returns_deny(sg):
    """Targeting the workspace root itself must return deny."""
    data = {
        "tool_name": "list_dir",
        "tool_input": {"path": WS},
    }
    result = sg.decide(data, WS)
    assert result == "deny", (
        f"decide() returned {result!r} for workspace root path — expected 'deny'"
    )


# ---------------------------------------------------------------------------
# 4. Always-allow tools never denied regardless of path
# ---------------------------------------------------------------------------

def test_always_allow_tool_with_github_path_returns_allow(sg):
    """vscode_ask_questions is always-allow — must return allow even for .github path."""
    data = {
        "tool_name": "vscode_ask_questions",
        "tool_input": {"filePath": f"{WS}/.github/hooks/something"},
    }
    result = sg.decide(data, WS)
    assert result == "allow", (
        f"Always-allow tool returned {result!r} — expected 'allow'"
    )


def test_todo_write_always_returns_allow(sg):
    """TodoWrite is always-allow — must never return deny."""
    data = {
        "tool_name": "TodoWrite",
        "tool_input": {},
    }
    result = sg.decide(data, WS)
    assert result == "allow"


# ---------------------------------------------------------------------------
# 5. Write-tool restrictions for .vscode and NoAgentZone
# ---------------------------------------------------------------------------

def test_write_tool_vscode_returns_deny(sg):
    """replace_string_in_file targeting .vscode must return deny."""
    data = {
        "tool_name": "replace_string_in_file",
        "tool_input": {"filePath": f"{WS}/.vscode/settings.json"},
    }
    result = sg.decide(data, WS)
    assert result == "deny", (
        f"decide() returned {result!r} for write to .vscode — expected 'deny'"
    )


def test_write_tool_noagentzone_returns_deny(sg):
    """create_file targeting NoAgentZone must return deny."""
    data = {
        "tool_name": "create_file",
        "tool_input": {"filePath": f"{WS}/NoAgentZone/new_file.py"},
    }
    result = sg.decide(data, WS)
    assert result == "deny", (
        f"decide() returned {result!r} for write to NoAgentZone — expected 'deny'"
    )


def test_write_tool_edit_vscode_returns_deny(sg):
    """edit_file targeting .vscode must return deny."""
    data = {
        "tool_name": "edit_file",
        "tool_input": {"filePath": f"{WS}/.vscode/extensions.json"},
    }
    result = sg.decide(data, WS)
    assert result == "deny"


# ---------------------------------------------------------------------------
# 6. grep_search with includeIgnoredFiles=true must return deny
# ---------------------------------------------------------------------------

def test_grep_search_include_ignored_files_returns_deny(sg):
    """includeIgnoredFiles=true must return deny — bypasses file-hiding."""
    data = {
        "tool_name": "grep_search",
        "tool_input": {
            "includeIgnoredFiles": True,
            "filePath": f"{WS}/project/main.py",
        },
    }
    result = sg.validate_grep_search(data, WS)
    assert result == "deny", (
        f"validate_grep_search returned {result!r} for includeIgnoredFiles=true — expected 'deny'"
    )


def test_grep_search_include_ignored_files_string_true_returns_deny(sg):
    """includeIgnoredFiles='true' (string) must also return deny."""
    data = {
        "tool_name": "grep_search",
        "tool_input": {
            "includeIgnoredFiles": "true",
            "filePath": f"{WS}/project/main.py",
        },
    }
    result = sg.validate_grep_search(data, WS)
    assert result == "deny"


# ---------------------------------------------------------------------------
# 7. grep_search with includePattern targeting .github must return deny
# ---------------------------------------------------------------------------

def test_grep_search_include_pattern_github_returns_deny(sg):
    """includePattern targeting .github must return deny."""
    data = {
        "tool_name": "grep_search",
        "tool_input": {
            "includePattern": ".github/**",
            "filePath": f"{WS}/project/main.py",
        },
    }
    result = sg.validate_grep_search(data, WS)
    assert result == "deny", (
        f"validate_grep_search returned {result!r} for .github includePattern — expected 'deny'"
    )


def test_grep_search_include_pattern_project_returns_allow(sg):
    """includePattern targeting project/** should return allow."""
    data = {
        "tool_name": "grep_search",
        "tool_input": {
            "includePattern": "project/**/*.py",
            "filePath": f"{WS}/project/main.py",
        },
    }
    result = sg.validate_grep_search(data, WS)
    assert result == "allow", (
        f"validate_grep_search returned {result!r} for project includePattern — expected 'allow'"
    )


# ---------------------------------------------------------------------------
# 8. Terminal command targeting .github path returns deny
# ---------------------------------------------------------------------------

def test_terminal_with_github_path_returns_deny(sg):
    """cat .github/hooks/settings.json must be denied — path zone = deny."""
    result, reason = sg.sanitize_terminal_command(
        f"cat {WS}/.github/hooks/settings.json", WS
    )
    assert result == "deny", (
        f"sanitize_terminal_command returned {result!r} for .github path — expected 'deny'"
    )


def test_terminal_with_noagentzone_path_returns_deny(sg):
    """cat NoAgentZone/secret.txt must be denied."""
    result, reason = sg.sanitize_terminal_command(
        f"cat {WS}/NoAgentZone/secret.txt", WS
    )
    assert result == "deny"


def test_terminal_obfuscation_python_c_returns_deny(sg):
    """python -c 'import os' is now allowed (SAF-017: -c removed from denied_flags, P-01 removed)."""
    result, reason = sg.sanitize_terminal_command("python -c 'import os'", WS)
    assert result == "allow", (
        f"sanitize_terminal_command returned {result!r} for python -c — expected 'allow'"
    )


# ---------------------------------------------------------------------------
# 9. decide() with empty tool name
# ---------------------------------------------------------------------------

def test_decide_empty_tool_name_no_path_returns_deny(sg):
    """Empty tool name with no path must return deny (no path → fail closed)."""
    data = {"tool_name": "", "tool_input": {}}
    result = sg.decide(data, WS)
    assert result == "deny"


def test_decide_missing_tool_name_key_no_path_returns_deny(sg):
    """Missing tool_name key with no path must return deny."""
    data = {"tool_input": {"someField": "someValue"}}
    result = sg.decide(data, WS)
    assert result == "deny"


# ---------------------------------------------------------------------------
# 10. Exempt read tools at .vscode path must be denied
# ---------------------------------------------------------------------------

def test_read_file_vscode_returns_deny(sg):
    """read_file targeting .vscode must return deny."""
    data = {
        "tool_name": "read_file",
        "tool_input": {"filePath": f"{WS}/.vscode/settings.json"},
    }
    result = sg.decide(data, WS)
    assert result == "deny"


def test_list_dir_github_returns_deny(sg):
    """list_dir targeting .github must return deny."""
    data = {
        "tool_name": "list_dir",
        "tool_input": {"path": f"{WS}/.github"},
    }
    result = sg.decide(data, WS)
    assert result == "deny"


# ---------------------------------------------------------------------------
# 11. Brute-force: no "ask" string ever appears in build_response output
# ---------------------------------------------------------------------------

def test_build_response_deny_never_contains_ask_string(sg):
    """build_response('deny') must not contain the string 'ask'."""
    response = sg.build_response("deny", "some reason")
    assert "ask" not in response, (
        f"build_response('deny') contains 'ask': {response!r}"
    )


def test_build_response_allow_never_contains_ask_string(sg):
    """build_response('allow') must not contain the string 'ask'."""
    response = sg.build_response("allow")
    assert "ask" not in response, (
        f"build_response('allow') contains 'ask': {response!r}"
    )


def test_decision_matrix_never_produces_ask(sg):
    """Brute-force all common tool/path combos: decide() never returns 'ask'."""
    tools_and_paths = [
        ("read_file",              f"{WS}/project/a.py"),
        ("read_file",              f"{WS}/.github/b.py"),
        ("read_file",              f"{WS}/.vscode/c.json"),
        ("read_file",              f"{WS}/NoAgentZone/d.txt"),
        ("read_file",              f"{WS}/README.md"),
        ("create_file",            f"{WS}/project/e.py"),
        ("create_file",            f"{WS}/.github/e.py"),
        ("edit_file",              f"{WS}/project/f.py"),
        ("edit_file",              f"{WS}/.vscode/settings.json"),
        ("replace_string_in_file", f"{WS}/project/g.py"),
        ("replace_string_in_file", f"{WS}/.github/h.py"),
        ("list_dir",               f"{WS}/project/"),
        ("list_dir",               f"{WS}/.github/"),
        ("file_search",            f"{WS}/project/"),
        ("file_search",            f"{WS}/.vscode/"),
        ("some_custom_tool",       f"{WS}/project/i.py"),
        ("some_custom_tool",       f"{WS}/.github/i.py"),
        ("semantic_search",        None),
    ]

    for tool_name, file_path in tools_and_paths:
        if file_path is not None:
            data = {"tool_name": tool_name, "tool_input": {"filePath": file_path}}
        else:
            data = {"tool_name": tool_name, "query": "something"}

        decision = sg.decide(data, WS)
        assert decision != "ask", (
            f"decide() returned 'ask' for tool={tool_name!r}, path={file_path!r} "
            "— 'ask' must never be returned in the 2-tier model"
        )
        assert decision in ("allow", "deny"), (
            f"decide() returned unexpected value {decision!r} for tool={tool_name!r}"
        )

        response = sg.build_response(decision)
        assert "ask" not in response
