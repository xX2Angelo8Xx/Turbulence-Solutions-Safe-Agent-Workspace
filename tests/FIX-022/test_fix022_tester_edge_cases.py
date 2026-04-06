"""FIX-022 — Tester edge-case tests for project-folder relative path fallback.

Covers:
  - Backslash path variants (Windows-native separators)
  - Trailing-slash heuristic boundary (single-segment with/without /)
  - Mixed deny-zone + project paths in chained commands
  - pip install -r flag behaviour (with and without dot-prefix)
  - Critical MUST-DENY invariants (rm family, ./root files, wildcard deny-zone)
  - Additional fallback-verbs (pytest, mypy, ruff)
"""
from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "templates", "agent-workbench", ".github", "hooks", "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

WS = "c:/workspace"


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


def allow(cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "allow"


def deny(cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "deny"


# ===========================================================================
# Backslash variants (Windows-native path separators)
# ===========================================================================

def test_python_backslash_src_app_allow():
    """TST-1736: python src\\app.py (Windows backslash 2-seg) -> allow via fallback."""
    assert allow("python src\\app.py")


def test_cat_backslash_src_file_allow():
    """TST-1737: cat src\\file.py (Windows backslash 2-seg) -> allow via fallback."""
    assert allow("cat src\\file.py")


def test_python_three_segment_backslash_allow():
    """TST-1738: python src\\main\\app.py (3-segment backslash) -> allow via fallback."""
    assert allow("python src\\main\\app.py")


def test_get_content_backslash_allow():
    """TST-1739: get-content src\\app.py (PowerShell alias, backslash) -> allow."""
    assert allow("get-content src\\app.py")


def test_ls_trailing_backslash_deny():
    """TST-1740: ls tests\\ -> deny.

    Trailing backslash is NOT treated as a directory indicator (only '/' is
    checked in the single-segment fallback heuristic).  Users should use
    'ls tests/' rather than 'ls tests\\' for reliable allow behaviour.
    This is a known platform limitation — not a security regression.
    """
    assert deny("ls tests\\")


# ===========================================================================
# Trailing-slash heuristic boundary
# ===========================================================================

def test_ls_bare_single_segment_allow():
    """TST-1741: ls tests (no slash, no dot) -> allow.

    'tests' has no slash/backslash/dot so _is_path_like returns False and
    no zone-check is performed.  This is correct: bare names like 'tests'
    cannot navigate into deny zones.
    """
    assert allow("ls tests")


def test_cat_bare_single_segment_no_trailing_slash_deny():
    """TST-1742: cat ./config (single ./-segment, no trailing slash) -> deny.

    ./config is path-like (starts with '.') but is a single segment without
    a trailing '/'.  The fallback guard requires either 2+ segments or a
    trailing '/' to safely project into the project folder.
    """
    assert deny("cat ./config")


# ===========================================================================
# Mixed deny-zone + project path in chained commands
# ===========================================================================

def test_chain_project_allow_then_deny_zone_deny():
    """TST-1743: cat src/app.py && cat .vscode/settings.json -> deny.

    First segment (cat src/app.py) would allow via fallback; second segment
    (cat .vscode/settings.json) hits the deny zone.  The gate must deny the
    entire chain.
    """
    assert deny("cat src/app.py && cat .vscode/settings.json")


def test_chain_python_allow_then_github_deny():
    """TST-1744: python src/app.py; python .github/hooks/evil.py -> deny.

    Second segment targets .github (deny zone) — chain must be denied
    regardless of the first segment's outcome.
    """
    assert deny("python src/app.py; python .github/hooks/evil.py")


def test_chain_ls_allow_then_noagentzone_deny():
    """TST-1745: ls src/ || ls noagentzone/ -> deny.

    '||' separator with NoAgentZone in second segment -> deny.
    """
    assert deny("ls src/ || ls noagentzone/")


# ===========================================================================
# pip install -r flag behaviour
# ===========================================================================

def test_pip_install_r_requirements_with_venv_allow():
    """TST-1746: pip install -r requirements.txt (VIRTUAL_ENV set) -> allow.

    'requirements.txt' has no slash/backslash/dot so _is_path_like returns
    False; the file argument is not zone-checked.  With VIRTUAL_ENV pointing
    inside the workspace this should allow.
    """
    with patch.dict(os.environ, {"VIRTUAL_ENV": f"{WS}/project/.venv"}):
        assert allow("pip install -r requirements.txt")


def test_pip_install_r_dot_requirements_with_venv_deny():
    """TST-1747: pip install -r ./requirements.txt (VIRTUAL_ENV set) -> deny.

    './requirements.txt' is path-like (starts with '.').  It normalises to a
    single segment with no trailing '/'.  The single-segment fallback guard
    requires a trailing '/' so no fallback is applied — correctly denied to
    prevent accessing files at the workspace root level like a real
    requirements.txt would resolve there from the hook's CWD.
    """
    with patch.dict(os.environ, {"VIRTUAL_ENV": f"{WS}/project/.venv"}):
        assert deny("pip install -r ./requirements.txt")


def test_pip_install_no_venv_deny():
    """TST-1748: pip install requests (no VIRTUAL_ENV) -> deny.

    No active venv -> global pip install blocked regardless of whether a
    path argument is present.
    """
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    with patch.dict(os.environ, env, clear=True):
        assert deny("pip install requests")


# ===========================================================================
# Critical MUST-DENY invariants
# ===========================================================================

def test_cat_dot_slash_root_config_deny():
    """TST-1749: cat ./root_config.json -> deny.

    Single ./-segment without trailing slash must NOT receive fallback — even
    for safe read verbs like cat.  This is a critical security boundary to
    prevent reading files located at the workspace root.
    """
    assert deny("cat ./root_config.json")


def test_ls_wildcard_github_prefix_deny():
    """TST-1750: ls -la .g* -> deny (wildcard deny-zone coverage).

    .g* can expand to .github/.  The gate must deny even when -la makes
    _prev_was_flag=True at the point where .g* is processed, because
    _check_path_arg calls _wildcard_prefix_matches_deny_zone internally.
    """
    assert deny("ls -la .g*")


def test_rm_family_get_project_fallback():
    """TST-1751: rm/del/remove-item with project-relative path -> all allow (FIX-118).

    FIX-118 introduces _DELETE_PROJECT_FALLBACK_VERBS, superseding the old
    _PROJECT_FALLBACK_VERBS exclusion of destructive commands.
    Multi-segment paths inside the project folder are now allowed.
    """
    assert allow("rm src/utils.py")
    assert allow("del src/utils.py")
    assert allow("remove-item src/utils.py")


# ===========================================================================
# Additional safe fallback verbs
# ===========================================================================

def test_pytest_direct_invocation_allow():
    """TST-1752: pytest tests/ -> allow (pytest in _PROJECT_FALLBACK_VERBS)."""
    assert allow("pytest tests/")


def test_ruff_not_in_allowlist_deny():
    """TST-1753: ruff src/ -> deny.

    'ruff' appears in _PROJECT_FALLBACK_VERBS (read/execute fallback safe list)
    but is NOT present in _COMMAND_ALLOWLIST.  The gate denies any verb that
    is not in the main allowlist before the fallback logic is even reached.
    Note: the _PROJECT_FALLBACK_VERBS entry for ruff is dead code — it has no
    effect unless ruff is added to the main allowlist.
    """
    assert deny("ruff src/")
