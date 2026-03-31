"""
FIX-091: Tests verifying that app.py and requirements.txt have been removed
from the templates/agent-workbench/Project/ directory.
"""
import os
import pytest

# Resolve template Project directory relative to this test file
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROJECT_DIR = os.path.join(REPO_ROOT, "templates", "agent-workbench", "Project")


def test_app_py_does_not_exist():
    """app.py must not exist in the template Project directory."""
    path = os.path.join(PROJECT_DIR, "app.py")
    assert not os.path.exists(path), f"app.py should have been removed but found at: {path}"


def test_requirements_txt_does_not_exist():
    """requirements.txt must not exist in the template Project directory."""
    path = os.path.join(PROJECT_DIR, "requirements.txt")
    assert not os.path.exists(path), (
        f"requirements.txt should have been removed but found at: {path}"
    )


def test_readme_still_exists():
    """README.md must still exist in the template Project directory."""
    path = os.path.join(PROJECT_DIR, "README.md")
    assert os.path.isfile(path), f"README.md is missing from: {PROJECT_DIR}"


def test_agent_rules_still_exists():
    """AGENT-RULES.md must still exist in the template Project directory."""
    path = os.path.join(PROJECT_DIR, "AGENT-RULES.md")
    assert os.path.isfile(path), f"AGENT-RULES.md is missing from: {PROJECT_DIR}"


def test_agentdocs_dir_still_exists():
    """AgentDocs/ directory must still exist in the template Project directory."""
    path = os.path.join(PROJECT_DIR, "AgentDocs")
    assert os.path.isdir(path), f"AgentDocs/ directory is missing from: {PROJECT_DIR}"
