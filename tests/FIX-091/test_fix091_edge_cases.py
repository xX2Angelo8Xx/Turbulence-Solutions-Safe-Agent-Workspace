"""
FIX-091 edge-case tests (Tester additions).

Covers:
  - Project directory itself still exists (wasn't accidentally wiped)
  - Exact entry count in Project/ (no stale files left behind)
  - AgentDocs/ is non-empty
  - README.md and AGENT-RULES.md are regular files, not directories or symlinks
  - No __pycache__ or .pyc artefacts inside the template Project directory
"""
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROJECT_DIR = os.path.join(REPO_ROOT, "templates", "agent-workbench", "Project")

EXPECTED_ENTRIES = {"README.md", "AGENT-RULES.md", "AgentDocs"}


def test_project_dir_exists():
    """The Project/ directory itself must still exist after the deletions."""
    assert os.path.isdir(PROJECT_DIR), (
        f"templates/agent-workbench/Project/ directory is missing: {PROJECT_DIR}"
    )


def test_project_dir_exact_contents():
    """Project/ must contain exactly the expected entries — no stale or unexpected files."""
    entries = set(os.listdir(PROJECT_DIR))
    unexpected = entries - EXPECTED_ENTRIES
    missing = EXPECTED_ENTRIES - entries
    assert not unexpected, f"Unexpected entries in Project/: {unexpected}"
    assert not missing, f"Expected entries missing from Project/: {missing}"


def test_agentdocs_dir_not_empty():
    """AgentDocs/ must contain at least one file (directory wasn't emptied by accident)."""
    agentdocs = os.path.join(PROJECT_DIR, "AgentDocs")
    contents = os.listdir(agentdocs)
    assert contents, "AgentDocs/ directory is unexpectedly empty"


def test_readme_is_regular_file():
    """README.md must be a regular file, not a directory or symlink."""
    path = os.path.join(PROJECT_DIR, "README.md")
    assert os.path.isfile(path) and not os.path.islink(path), (
        "README.md is not a regular file"
    )


def test_agent_rules_is_regular_file():
    """AGENT-RULES.md must be a regular file, not a directory or symlink."""
    path = os.path.join(PROJECT_DIR, "AGENT-RULES.md")
    assert os.path.isfile(path) and not os.path.islink(path), (
        "AGENT-RULES.md is not a regular file"
    )


def test_no_pycache_in_project_dir():
    """No __pycache__ directories or .pyc files should exist inside Project/."""
    for root, dirs, files in os.walk(PROJECT_DIR):
        for d in dirs:
            assert d != "__pycache__", (
                f"Unexpected __pycache__ found at: {os.path.join(root, d)}"
            )
        for f in files:
            assert not f.endswith(".pyc"), (
                f"Unexpected .pyc file found at: {os.path.join(root, f)}"
            )
