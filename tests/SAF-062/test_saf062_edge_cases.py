"""tests/SAF-062/test_saf062_edge_cases.py

Tester edge-case tests for SAF-062: test-path in _PROJECT_FALLBACK_VERBS.

Covers scenarios beyond the developer's test set:
  1. Nested path under dot-prefixed root  (Test-Path .venv/Scripts/python.exe)
  2. Non-directory dot-prefixed file      (Test-Path .gitignore)
  3. Case sensitivity                     (TEST-PATH .venv, test-path .venv)
  4. No arguments                         (Test-Path with no args)
  5. Absolute path outside project        (Test-Path C:/Windows/System32)
  6. .github dot-prefixed deny zone       (Test-Path .github)  — must still deny
  7. test-path with quoted argument       (Test-Path ".venv")
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
    / ".github"
    / "hooks"
    / "scripts"
)

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


@pytest.fixture(scope="module")
def sg():
    import security_gate as _sg
    return _sg


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


WS = "c:/workspace"


def allow(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "allow"


def deny(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# Edge-case 1: nested path under dot-prefixed root (.venv/Scripts/python.exe)
# ---------------------------------------------------------------------------

def test_test_path_nested_under_dot_venv_allowed(sg):
    """Test-Path .venv/Scripts/python.exe must be allowed (still inside project)."""
    assert allow(sg, "Test-Path .venv/Scripts/python.exe")


# ---------------------------------------------------------------------------
# Edge-case 2: non-directory dot-prefixed file (.gitignore)
# ---------------------------------------------------------------------------

def test_test_path_dot_gitignore_allowed(sg):
    """Test-Path .gitignore must be allowed via project-folder fallback."""
    assert allow(sg, "Test-Path .gitignore")


# ---------------------------------------------------------------------------
# Edge-case 3a: uppercase TEST-PATH (case-insensitive check)
# ---------------------------------------------------------------------------

def test_test_path_all_caps_allowed(sg):
    """TEST-PATH .venv must be treated identically to test-path (case-insensitive)."""
    assert allow(sg, "TEST-PATH .venv")


# ---------------------------------------------------------------------------
# Edge-case 3b: mixed case Test-Path (standard PowerShell casing)
# ---------------------------------------------------------------------------

def test_test_path_mixed_case_allowed(sg):
    """Test-Path .venv (standard casing) must be allowed."""
    assert allow(sg, "Test-Path .venv")


# ---------------------------------------------------------------------------
# Edge-case 3c: lowercase test-path
# ---------------------------------------------------------------------------

def test_test_path_lowercase_allowed(sg):
    """test-path .venv (all lowercase) must be allowed."""
    assert allow(sg, "test-path .venv")


# ---------------------------------------------------------------------------
# Edge-case 4: test-path with no arguments
# ---------------------------------------------------------------------------

def test_test_path_no_args(sg):
    """test-path with no arguments should not raise and should produce a verdict."""
    decision, reason = sg.sanitize_terminal_command("Test-Path", WS)
    # No argument means no path to classify; either allow (verb-only) or deny is
    # acceptable, but the gate must not crash.  reason may be None or str.
    assert decision in ("allow", "deny")
    assert reason is None or isinstance(reason, str)


# ---------------------------------------------------------------------------
# Edge-case 5: absolute path outside project must be zone-checked
# ---------------------------------------------------------------------------

def test_test_path_absolute_system_path_denied(sg):
    """Test-Path C:/Windows/System32 must be denied (outside project zone)."""
    assert deny(sg, "Test-Path C:/Windows/System32")


# ---------------------------------------------------------------------------
# Edge-case 6: .github/ deny zone is still enforced for test-path
# ---------------------------------------------------------------------------

def test_test_path_dot_github_denied(sg):
    """Test-Path .github must be denied even though it starts with a dot."""
    assert deny(sg, "Test-Path .github")


# ---------------------------------------------------------------------------
# Edge-case 7: quoted argument (.venv in double-quotes)
# ---------------------------------------------------------------------------

def test_test_path_quoted_dot_venv_allowed(sg):
    """Test-Path \".venv\" (quoted argument) must be allowed."""
    assert allow(sg, 'Test-Path ".venv"')
