"""SAF-013 — Tests for 2-Tier Security Gate

Tests that security_gate.py only returns "allow" or "deny", never "ask".
"""
import importlib
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "Default-Project"
    / ".github"
    / "hooks"
    / "scripts"
)


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


WS = "c:/workspace"

REPO_ROOT = str(Path(__file__).parents[2])


# ---------------------------------------------------------------------------
# 1. _ASK_REASON constant no longer exists
# ---------------------------------------------------------------------------

def test_ask_reason_constant_removed(sg):
    """_ASK_REASON must not exist in security_gate — removed in SAF-013."""
    assert not hasattr(sg, "_ASK_REASON"), (
        "_ASK_REASON constant was not removed from security_gate.py"
    )


# ---------------------------------------------------------------------------
# 2. sanitize_terminal_command() returns "allow" for safe commands
# ---------------------------------------------------------------------------

def test_sanitize_terminal_python_version_returns_allow(sg):
    """'python --version' is a safe read-only command — must return allow."""
    result = sg.sanitize_terminal_command("python --version", WS)
    assert result == ("allow", None)


def test_sanitize_terminal_git_status_returns_allow(sg):
    """'git status' is a safe read-only command — must return allow."""
    result = sg.sanitize_terminal_command("git status", WS)
    assert result == ("allow", None)


def test_sanitize_terminal_pytest_returns_allow(sg):
    """'pytest' with no args is safe — must return allow."""
    result = sg.sanitize_terminal_command("pytest", WS)
    assert result == ("allow", None)


# ---------------------------------------------------------------------------
# 3. sanitize_terminal_command() returns "deny" for destructive commands
# ---------------------------------------------------------------------------

def test_sanitize_terminal_rm_rf_returns_deny(sg):
    """'rm -rf /' is a destructive command — must return deny (not ask)."""
    decision, reason = sg.sanitize_terminal_command("rm -rf /", WS)
    assert decision == "deny"
    assert reason is not None


# ---------------------------------------------------------------------------
# 4. validate_grep_search() returns "deny" when no path is supplied
# ---------------------------------------------------------------------------

def test_grep_search_no_path_returns_deny(sg):
    """grep_search with no includePattern and no path field must return deny."""
    data = {"tool_name": "grep_search", "query": "something"}
    result = sg.validate_grep_search(data, WS)
    assert result == "deny", (
        f"validate_grep_search returned {result!r} instead of 'deny' for no-path call"
    )


# ---------------------------------------------------------------------------
# 5. validate_semantic_search() always returns "deny"
# ---------------------------------------------------------------------------

def test_semantic_search_always_returns_deny(sg):
    """validate_semantic_search must always return 'deny' in the 2-tier model."""
    data = {"tool_name": "semantic_search", "query": "something"}
    result = sg.validate_semantic_search(data, WS)
    assert result == "deny", (
        f"validate_semantic_search returned {result!r} instead of 'deny'"
    )


# ---------------------------------------------------------------------------
# 6. decide() returns "deny" for unknown tools
# ---------------------------------------------------------------------------

def test_decide_unknown_tool_returns_deny(sg):
    """Unknown tools must return 'deny' in the 2-tier model (not 'ask')."""
    data = {
        "tool_name": "some_unknown_tool_xyz",
        "tool_input": {"filePath": f"{WS}/project/file.py"},
    }
    result = sg.decide(data, WS)
    assert result == "deny", (
        f"decide() returned {result!r} for unknown tool — expected 'deny'"
    )


# ---------------------------------------------------------------------------
# 7. decide() returns "allow" for file tools targeting the project folder
# ---------------------------------------------------------------------------

def test_decide_create_file_project_returns_allow(sg):
    """create_file targeting project folder must be allowed."""
    data = {
        "tool_name": "create_file",
        "tool_input": {"filePath": f"{WS}/project/file.py"},
    }
    result = sg.decide(data, WS)
    assert result == "allow", (
        f"decide() returned {result!r} for create_file in project/ — expected 'allow'"
    )


# ---------------------------------------------------------------------------
# 8. decide() returns "deny" for file tools targeting .github
# ---------------------------------------------------------------------------

def test_decide_create_file_github_returns_deny(sg):
    """create_file targeting .github must be denied."""
    data = {
        "tool_name": "create_file",
        "tool_input": {"filePath": f"{WS}/.github/x"},
    }
    result = sg.decide(data, WS)
    assert result == "deny", (
        f"decide() returned {result!r} for create_file in .github/ — expected 'deny'"
    )


# ---------------------------------------------------------------------------
# 9. Response JSON permissionDecision is only "allow" or "deny" — never "ask"
# ---------------------------------------------------------------------------

def test_response_json_never_ask(sg):
    """build_response() output must only contain 'allow' or 'deny' decisions."""
    scenarios = [
        # (tool_name, filePath, expected_decision)
        ("create_file", f"{WS}/project/readme.txt", "allow"),
        ("create_file", f"{WS}/.github/hook.py", "deny"),
        ("some_unknown_tool", f"{WS}/project/x.py", "deny"),
        ("semantic_search", None, "deny"),
    ]

    for tool_name, file_path, expected in scenarios:
        if file_path is not None:
            data = {"tool_name": tool_name, "tool_input": {"filePath": file_path}}
        else:
            data = {"tool_name": tool_name, "query": "something"}

        decision = sg.decide(data, WS)
        assert decision in ("allow", "deny"), (
            f"decide() returned {decision!r} for tool={tool_name!r} — "
            "must be 'allow' or 'deny', never 'ask'"
        )
        assert decision == expected, (
            f"Expected {expected!r} for tool={tool_name!r}, got {decision!r}"
        )

        response_str = sg.build_response(decision)
        response = json.loads(response_str)
        perm = response["hookSpecificOutput"]["permissionDecision"]
        assert perm in ("allow", "deny"), (
            f"permissionDecision {perm!r} is not 'allow' or 'deny'"
        )
        assert perm != "ask", (
            f"permissionDecision must never be 'ask'; got {perm!r}"
        )
        assert "ask" not in response_str, (
            f"The string 'ask' must not appear anywhere in the JSON response; "
            f"got: {response_str}"
        )


# ---------------------------------------------------------------------------
# 10. Both copies of security_gate.py are identical
# ---------------------------------------------------------------------------

def test_both_copies_identical():
    """Default-Project and templates/coding must have identical security_gate.py."""
    path_a = os.path.join(
        REPO_ROOT,
        "Default-Project", ".github", "hooks", "scripts", "security_gate.py",
    )
    path_b = os.path.join(
        REPO_ROOT,
        "templates", "coding", ".github", "hooks", "scripts", "security_gate.py",
    )
    with open(path_a, "rb") as fa:
        a = fa.read()
    with open(path_b, "rb") as fb:
        b = fb.read()
    assert a == b, (
        "security_gate.py in Default-Project/ and templates/coding/ are not identical. "
        "Run the sync step to bring them into alignment."
    )
