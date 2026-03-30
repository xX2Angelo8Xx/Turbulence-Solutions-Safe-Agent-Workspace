"""tests/SAF-062/test_saf062_test_path_fallback.py

Tests for SAF-062: Add test-path to _PROJECT_FALLBACK_VERBS.

Validates:
  1. "test-path" is present in _PROJECT_FALLBACK_VERBS
  2. Test-Path .venv is allowed (dot-prefixed workspace root path fallback)
  3. Test-Path .env is allowed (dot-prefixed workspace root path fallback)
  4. Test-Path .github/hooks/scripts/security_gate.py is denied (deny zone)
  5. Test-Path Project/some-file.txt is allowed (project folder path)
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


# Workspace root used in all tests
WS = "c:/workspace"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def allow(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "allow"


def deny(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# Test 1 — "test-path" is in _PROJECT_FALLBACK_VERBS
# ---------------------------------------------------------------------------

def test_test_path_in_fallback_verbs(sg):
    """test-path must be present in _PROJECT_FALLBACK_VERBS."""
    assert "test-path" in sg._PROJECT_FALLBACK_VERBS


# ---------------------------------------------------------------------------
# Test 2 — Test-Path .venv is allowed via project-folder fallback
# ---------------------------------------------------------------------------

def test_test_path_dot_venv_allowed(sg):
    """Test-Path .venv must be allowed via the project-folder fallback."""
    assert allow(sg, "Test-Path .venv")


# ---------------------------------------------------------------------------
# Test 3 — Test-Path .env is allowed via project-folder fallback
# ---------------------------------------------------------------------------

def test_test_path_dot_env_allowed(sg):
    """Test-Path .env must be allowed via the project-folder fallback."""
    assert allow(sg, "Test-Path .env")


# ---------------------------------------------------------------------------
# Test 4 — Test-Path into .github/ deny zone is denied
# ---------------------------------------------------------------------------

def test_test_path_github_denied(sg):
    """Test-Path targeting .github/ must be denied (deny zone)."""
    assert deny(sg, "Test-Path .github/hooks/scripts/security_gate.py")


# ---------------------------------------------------------------------------
# Test 5 — Test-Path inside project folder is allowed
# ---------------------------------------------------------------------------

def test_test_path_project_file_allowed(sg):
    """Test-Path for a project-folder path must be allowed."""
    assert allow(sg, "Test-Path project/some-file.txt")
