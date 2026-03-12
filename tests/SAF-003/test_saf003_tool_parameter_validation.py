"""Tests for SAF-003 — Tool Parameter Validation

Covers:
  - TST-269 to TST-277: Unit — _is_truthy_flag()
  - TST-278 to TST-284: Unit — _validate_include_pattern()
  - TST-285 to TST-294: Unit — validate_grep_search()
  - TST-295 to TST-297: Unit — validate_semantic_search()
  - TST-298 to TST-300: Security — protection tests
  - TST-301 to TST-307: Security — bypass-attempt tests
  - TST-308 to TST-312: Integration — decide() dispatch
  - TST-313 to TST-314: Cross-platform path tests
"""
from __future__ import annotations

import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Make security_gate importable from its non-standard location
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "Default-Project",
        ".github",
        "hooks",
        "scripts",
    )
)

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg   # noqa: E402
import zone_classifier as zc  # noqa: E402

# Workspace root constant used across all tests
WS = "/workspace"


# ===========================================================================
# _is_truthy_flag  (TST-269 to TST-277)
# ===========================================================================

def test_is_truthy_flag_bool_true():
    # TST-269 — bool True is truthy
    assert sg._is_truthy_flag(True) is True


def test_is_truthy_flag_bool_false():
    # TST-270 — bool False is not truthy
    assert sg._is_truthy_flag(False) is False


def test_is_truthy_flag_string_true_lowercase():
    # TST-271 — string "true" is truthy
    assert sg._is_truthy_flag("true") is True


def test_is_truthy_flag_string_true_mixed_case():
    # TST-272 — string "True" is truthy (case-insensitive)
    assert sg._is_truthy_flag("True") is True


def test_is_truthy_flag_string_true_uppercase():
    # TST-273 — string "TRUE" is truthy (case-insensitive)
    assert sg._is_truthy_flag("TRUE") is True


def test_is_truthy_flag_string_false():
    # TST-274 — string "false" is not truthy
    assert sg._is_truthy_flag("false") is False


def test_is_truthy_flag_int_1():
    # TST-275 — integer 1 is truthy
    assert sg._is_truthy_flag(1) is True


def test_is_truthy_flag_int_0():
    # TST-276 — integer 0 is not truthy
    assert sg._is_truthy_flag(0) is False


def test_is_truthy_flag_none():
    # TST-277 — None is not truthy
    assert sg._is_truthy_flag(None) is False


# ===========================================================================
# _validate_include_pattern  (TST-278 to TST-284)
# ===========================================================================

def test_validate_include_pattern_safe_wildcard_glob():
    # TST-278 — broad wildcard glob targeting no specific zone → allow
    assert sg._validate_include_pattern("**/*.py", WS) == "allow"


def test_validate_include_pattern_src_subdir():
    # TST-279 — glob scoped to src/ (ask zone, but not deny) → allow (not denied)
    assert sg._validate_include_pattern("src/**", WS) == "allow"


def test_validate_include_pattern_github():
    # TST-280 — pattern explicitly targeting .github/ → deny (protection)
    assert sg._validate_include_pattern(".github/**", WS) == "deny"


def test_validate_include_pattern_vscode():
    # TST-281 — pattern explicitly targeting .vscode/ → deny (protection)
    assert sg._validate_include_pattern(".vscode/**", WS) == "deny"


def test_validate_include_pattern_noagentzone():
    # TST-282 — pattern targeting NoAgentZone/ (mixed case) → deny (protection)
    assert sg._validate_include_pattern("NoAgentZone/**", WS) == "deny"


def test_validate_include_pattern_traversal_dotdot():
    # TST-283 — raw ../ traversal in pattern → deny (traversal guard)
    assert sg._validate_include_pattern("../other/**", WS) == "deny"


def test_validate_include_pattern_traversal_deep():
    # TST-284 — deep traversal that escapes workspace root → deny
    # posixpath.normpath("project/../../..") → "../.." — '..' remains
    assert sg._validate_include_pattern("project/../../..", WS) == "deny"


# ===========================================================================
# validate_grep_search  (TST-285 to TST-294)
# ===========================================================================

def test_validate_grep_search_include_pattern_github_denied():
    # TST-285 — includePattern targeting .github/ → deny
    data = {
        "tool_name": "grep_search",
        "query": "secret",
        "includePattern": ".github/**",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


def test_validate_grep_search_include_pattern_vscode_denied():
    # TST-286 — includePattern targeting .vscode/ → deny
    data = {
        "tool_name": "grep_search",
        "query": "settings",
        "includePattern": ".vscode/**",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


def test_validate_grep_search_include_pattern_noagentzone_denied():
    # TST-287 — includePattern targeting NoAgentZone/ → deny
    data = {
        "tool_name": "grep_search",
        "query": "private",
        "includePattern": "NoAgentZone/**",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


def test_validate_grep_search_include_ignored_files_bool_true_denied():
    # TST-288 — includeIgnoredFiles=True → deny
    data = {
        "tool_name": "grep_search",
        "query": "anything",
        "includeIgnoredFiles": True,
    }
    assert sg.validate_grep_search(data, WS) == "deny"


def test_validate_grep_search_include_ignored_files_string_true_denied():
    # TST-289 — includeIgnoredFiles="true" (string) → deny
    data = {
        "tool_name": "grep_search",
        "query": "anything",
        "includeIgnoredFiles": "true",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


def test_validate_grep_search_no_params_no_path_asks():
    # TST-290 — no special params, no filePath → ask (standard fallback)
    data = {"tool_name": "grep_search", "query": "hello"}
    assert sg.validate_grep_search(data, WS) == "ask"


def test_validate_grep_search_no_params_project_path_allowed():
    # TST-291 — no special params + filePath=project/main.py → allow
    data = {
        "tool_name": "grep_search",
        "query": "hello",
        "filePath": f"{WS}/project/main.py",
    }
    assert sg.validate_grep_search(data, WS) == "allow"


def test_validate_grep_search_no_params_deny_path_denied():
    # TST-292 — no special params + filePath=.github/secret → deny via zone check
    data = {
        "tool_name": "grep_search",
        "query": "hello",
        "filePath": f"{WS}/.github/secret",
    }
    assert sg.validate_grep_search(data, WS) == "deny"


def test_validate_grep_search_include_ignored_false_not_denied():
    # TST-293 — includeIgnoredFiles=False is explicitly not a bypass → not denied
    data = {
        "tool_name": "grep_search",
        "query": "anything",
        "includeIgnoredFiles": False,
    }
    result = sg.validate_grep_search(data, WS)
    assert result != "deny"


def test_validate_grep_search_tool_input_nested_format():
    # TST-294 — VS Code hook sends params inside tool_input dict → deny applies
    data = {
        "tool_name": "grep_search",
        "tool_input": {
            "query": "secrets",
            "includePattern": ".github/**",
        },
    }
    assert sg.validate_grep_search(data, WS) == "deny"


# ===========================================================================
# validate_semantic_search  (TST-295 to TST-297)
# ===========================================================================

def test_validate_semantic_search_basic_returns_ask():
    # TST-295 — any semantic_search call returns "ask" for human review
    data = {"tool_name": "semantic_search", "query": "find all functions"}
    assert sg.validate_semantic_search(data, WS) == "ask"


def test_validate_semantic_search_protected_query_still_ask():
    # TST-296 — query containing protected path name still returns "ask"
    # (query is search text, not a path; it must not be denied)
    data = {"tool_name": "semantic_search", "query": ".github/secret hook"}
    assert sg.validate_semantic_search(data, WS) == "ask"


def test_validate_semantic_search_never_returns_allow():
    # TST-297 — semantic_search must never be auto-allowed
    data = {"tool_name": "semantic_search", "query": "safe innocuous query"}
    result = sg.validate_semantic_search(data, WS)
    assert result != "allow", f"semantic_search must not return allow; got {result!r}"


# ===========================================================================
# Security — protection tests  (TST-298 to TST-300)
# ===========================================================================

def test_grep_search_deny_zone_via_include_pattern_protected():
    # TST-298 — protection: .github/ via includePattern → blocked
    data = {
        "tool_name": "grep_search",
        "query": "hook script",
        "includePattern": ".github/**",
    }
    assert sg.decide(data, WS) == "deny"


def test_grep_search_traversal_blocked_protection():
    # TST-299 — protection: path traversal in includePattern → blocked
    data = {
        "tool_name": "grep_search",
        "query": "anything",
        "includePattern": "../../../.vscode/**",
    }
    assert sg.decide(data, WS) == "deny"


def test_grep_search_include_ignored_files_blocked_protection():
    # TST-300 — protection: includeIgnoredFiles=True → blocked
    data = {
        "tool_name": "grep_search",
        "query": "anything",
        "includeIgnoredFiles": True,
    }
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# Security — bypass-attempt tests  (TST-301 to TST-307)
# ===========================================================================

def test_grep_search_github_in_nested_tool_input_bypass():
    # TST-301 — bypass attempt: includePattern in nested tool_input → still denied
    data = {
        "tool_name": "grep_search",
        "tool_input": {
            "query": "secret",
            "includePattern": ".github/**",
        },
    }
    assert sg.decide(data, WS) == "deny"


def test_grep_search_traversal_to_github_bypass():
    # TST-302 — bypass attempt: project/../.github/** resolves to .github/ → denied
    data = {
        "tool_name": "grep_search",
        "query": "secret",
        "includePattern": "project/../.github/**",
    }
    assert sg.decide(data, WS) == "deny"


def test_grep_search_mixed_case_include_pattern_bypass():
    # TST-303 — bypass attempt: ".GITHUB/**" upper-case → normalized and denied
    data = {
        "tool_name": "grep_search",
        "query": "secret",
        "includePattern": ".GITHUB/**",
    }
    assert sg.decide(data, WS) == "deny"


def test_grep_search_include_ignored_string_true_bypass():
    # TST-304 — bypass attempt: includeIgnoredFiles="true" (string) → denied
    data = {
        "tool_name": "grep_search",
        "query": "anything",
        "includeIgnoredFiles": "true",
    }
    assert sg.decide(data, WS) == "deny"


def test_grep_search_noagentzone_lowercase_bypass():
    # TST-305 — bypass attempt: "noagentzone/**" (all lowercase) → denied
    data = {
        "tool_name": "grep_search",
        "query": "private",
        "includePattern": "noagentzone/**",
    }
    assert sg.decide(data, WS) == "deny"


def test_grep_search_star_star_github_bypass():
    # TST-306 — bypass attempt: "**/. github/**" with space does NOT target
    # ".github" — this should NOT be denied (space makes it a different name)
    # But "**/.github/**" without space still must be denied.
    data = {
        "tool_name": "grep_search",
        "query": "secret",
        "includePattern": "**/.github/**",
    }
    assert sg.decide(data, WS) == "deny"


def test_semantic_search_cannot_be_allowed_bypass():
    # TST-307 — bypass attempt: semantic_search must never return "allow"
    # even with a seemingly safe query; always requires human review
    data = {"tool_name": "semantic_search", "query": "project utility functions"}
    result = sg.decide(data, WS)
    assert result != "allow", f"semantic_search bypass: got {result!r}, expected ask"


# ===========================================================================
# Integration — decide() dispatch  (TST-308 to TST-312)
# ===========================================================================

def test_decide_grep_search_include_pattern_github_denied():
    # TST-308 — full decide() pipeline: grep_search with .github includePattern → deny
    data = {
        "tool_name": "grep_search",
        "query": "hook",
        "includePattern": ".github/**",
    }
    assert sg.decide(data, WS) == "deny"


def test_decide_grep_search_clean_params_project_path_allowed():
    # TST-309 — full decide() pipeline: grep_search with safe params → allow
    data = {
        "tool_name": "grep_search",
        "query": "def main",
        "includePattern": "src/**",
        "filePath": f"{WS}/project/main.py",
    }
    result = sg.decide(data, WS)
    assert result == "allow"


def test_decide_grep_search_clean_params_no_path_asks():
    # TST-310 — full decide() pipeline: grep_search with safe params, no path → ask
    data = {
        "tool_name": "grep_search",
        "query": "import os",
        "includePattern": "**/*.py",
    }
    result = sg.decide(data, WS)
    assert result == "ask"


def test_decide_semantic_search_always_ask():
    # TST-311 — full decide() pipeline: semantic_search always → ask
    data = {"tool_name": "semantic_search", "query": "list all public methods"}
    assert sg.decide(data, WS) == "ask"


def test_decide_grep_search_include_ignored_denied():
    # TST-312 — full decide() pipeline: includeIgnoredFiles=True → deny
    data = {
        "tool_name": "grep_search",
        "query": "anything",
        "includeIgnoredFiles": True,
    }
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# Cross-platform path tests  (TST-313 to TST-314)
# ===========================================================================

def test_grep_search_windows_backslash_include_pattern_github_denied():
    # TST-313 — Windows-style backslash includePattern targeting .github → deny
    ws_win = sg.normalize_path("C:\\workspace")
    data = {
        "tool_name": "grep_search",
        "query": "secret",
        "includePattern": ".github\\\\**",
    }
    assert sg.decide(data, ws_win) == "deny"


def test_grep_search_wsl_absolute_include_pattern_github_denied():
    # TST-314 — WSL absolute include pattern targeting .github → deny
    ws_wsl = sg.normalize_path("/mnt/c/workspace")
    data = {
        "tool_name": "grep_search",
        "query": "secret",
        "includePattern": "/mnt/c/workspace/.github/**",
    }
    assert sg.decide(data, ws_wsl) == "deny"
