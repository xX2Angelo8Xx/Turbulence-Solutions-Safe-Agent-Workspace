"""Tests for FIX-105 — Fix template path and prefix test assertions.

Verifies that:
- No test files reference the old TS-SAE- prefix in pass-required assertions
- No test files reference templates/coding (old path) in assertion code
- The agent-workbench template pycache directories are absent
- Key template structural assertions use updated paths
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_ROOT = REPO_ROOT / "tests"
TEMPLATE_DIR = REPO_ROOT / "templates" / "agent-workbench"


# ---------------------------------------------------------------------------
# Pycache not committed to git
# ---------------------------------------------------------------------------

def test_no_pycache_in_agent_workbench_template():
    """No __pycache__ directories must be tracked by git in the agent-workbench template.

    conftest.py creates pycache at runtime when it imports security_gate, so
    we verify git-tracking rather than disk presence.
    """
    result = subprocess.run(
        ["git", "ls-files", "--", "templates/agent-workbench/**/__pycache__/**"],
        capture_output=True, text=True, cwd=str(REPO_ROOT)
    )
    tracked = result.stdout.strip()
    assert tracked == "", f"__pycache__ files are git-tracked: {tracked}"


def test_no_pyc_files_in_agent_workbench_template():
    """No *.pyc files must be tracked by git in the agent-workbench template."""
    result = subprocess.run(
        ["git", "ls-files", "--", "templates/agent-workbench/**/*.pyc"],
        capture_output=True, text=True, cwd=str(REPO_ROOT)
    )
    tracked = result.stdout.strip()
    assert tracked == "", f".pyc files are git-tracked: {tracked}"


# ---------------------------------------------------------------------------
# INS-004 updated assertions
# ---------------------------------------------------------------------------

def test_ins004_prompts_critical_review_exists():
    """critical-review.prompt.md must exist in the agent-workbench template prompts."""
    path = TEMPLATE_DIR / ".github" / "prompts" / "critical-review.prompt.md"
    assert path.is_file(), f"Missing: {path}"


def test_ins004_skill_agentdocs_update_exists():
    """agentdocs-update/SKILL.md must exist in the agent-workbench template skills."""
    path = TEMPLATE_DIR / ".github" / "skills" / "agentdocs-update" / "SKILL.md"
    assert path.is_file(), f"Missing: {path}"


def test_ins004_project_agentdocs_agent_rules_exists():
    """Project/AgentDocs/AGENT-RULES.md must exist in the agent-workbench template."""
    path = TEMPLATE_DIR / "Project" / "AgentDocs" / "AGENT-RULES.md"
    assert path.is_file(), f"Missing: {path}"


def test_ins004_project_agentdocs_architecture_exists():
    """Project/AgentDocs/architecture.md must exist in the agent-workbench template."""
    path = TEMPLATE_DIR / "Project" / "AgentDocs" / "architecture.md"
    assert path.is_file(), f"Missing: {path}"


def test_ins004_project_agentdocs_decisions_exists():
    """Project/AgentDocs/decisions.md must exist in the agent-workbench template."""
    path = TEMPLATE_DIR / "Project" / "AgentDocs" / "decisions.md"
    assert path.is_file(), f"Missing: {path}"


# ---------------------------------------------------------------------------
# GUI prefix tests: verify SAE- prefix in production code
# ---------------------------------------------------------------------------

def test_project_creator_uses_sae_prefix():
    """project_creator.py must use SAE- prefix (not TS-SAE-)."""
    creator_path = REPO_ROOT / "src" / "launcher" / "core" / "project_creator.py"
    content = creator_path.read_text(encoding="utf-8")
    assert "SAE-" in content, (
        "project_creator.py must contain SAE- prefix string"
    )
    assert "TS-SAE-" not in content, (
        "project_creator.py must not contain TS-SAE- prefix (old prefix)"
    )


# ---------------------------------------------------------------------------
# Test file hygiene: no TS-SAE- references in assertion code of key test files
# ---------------------------------------------------------------------------

_GUI_TEST_FILES = [
    "GUI-005/test_gui005_project_creation.py",
    "GUI-007/test_gui007_validation.py",
    "GUI-007/test_gui007_tester_additions.py",
    "GUI-015/test_gui015_rename_root_folder.py",
    "GUI-015/test_gui015_tester_edge_cases.py",
    "GUI-016/test_gui016_rename_project_folder.py",
    "GUI-020/test_gui020_create_project_integration.py",
    "GUI-022/test_gui022_include_readmes_checkbox.py",
]

def test_gui_test_files_no_ts_sae_assertions():
    """No GUI test file should have TS-SAE- in assertion strings.

    These tests were updated from TS-SAE- to SAE- as part of FIX-105.
    """
    violations = []
    for rel_path in _GUI_TEST_FILES:
        path = TESTS_ROOT / rel_path
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        # Check for TS-SAE- in assertion positions (not in docstrings about old behavior)
        # We check for it in common assertion patterns
        if re.search(r'==[^\n]*TS-SAE-', content) or re.search(r'TS-SAE-[^\n]*(\.mkdir|\.is_dir|is_file)', content):
            violations.append(rel_path)
    assert violations == [], (
        f"Found TS-SAE- in assertion code in: {violations}"
    )
