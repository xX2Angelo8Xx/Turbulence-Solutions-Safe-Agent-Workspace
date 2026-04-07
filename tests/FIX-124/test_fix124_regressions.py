"""Tests for FIX-124: CI test regressions from v3.4.0 fixes.

Regression guards that verify each category of fix made in FIX-124 continues
to hold as the codebase evolves.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "templates"

sys.path.insert(0, str(REPO_ROOT / "src"))


# ===========================================================================
# Category 2: Template count
# ===========================================================================

def test_three_template_directories_exist() -> None:
    """Exactly 3 template directories must exist: agent-workbench, certification-pipeline,
    clean-workspace.  Adding or removing templates requires updating GUI-023 test."""
    from launcher.core.project_creator import list_templates

    names = list_templates(TEMPLATES_DIR)
    assert len(names) == 3, (
        f"Expected 3 templates, got {len(names)}: {names}. "
        "Update tests/GUI-023/test_gui023_tester_edge_cases.py::test_list_templates_real_count "
        "and this test when adding or removing templates."
    )


# ===========================================================================
# Category 3: AGENT-RULES path
# ===========================================================================

def test_agent_rules_at_correct_path() -> None:
    """AGENT-RULES.md must be at Project/AgentDocs/AGENT-RULES.md, NOT Project/AGENT-RULES.md."""
    correct_path = TEMPLATES_DIR / "agent-workbench" / "Project" / "AgentDocs" / "AGENT-RULES.md"
    wrong_path = TEMPLATES_DIR / "agent-workbench" / "Project" / "AGENT-RULES.md"

    assert correct_path.is_file(), (
        f"AGENT-RULES.md missing at expected location: {correct_path}"
    )
    assert not wrong_path.exists(), (
        f"AGENT-RULES.md unexpectedly found at old path: {wrong_path}. "
        "File should be at Project/AgentDocs/AGENT-RULES.md after FIX-128."
    )


# ===========================================================================
# Category 4: Version
# ===========================================================================

def test_version_is_3_4_0() -> None:
    """Current VERSION must equal 3.4.0.  Update FIX-070 test when version bumps."""
    from launcher.config import VERSION

    assert VERSION == "3.4.0", (
        f"Expected VERSION == '3.4.0', got '{VERSION}'. "
        "Remember to update tests/FIX-070/test_fix070_version_bump.py after a version bump."
    )


# ===========================================================================
# Category 6: MANIFEST files regenerated
# ===========================================================================

def test_agent_workbench_manifest_exists() -> None:
    """Agent-workbench MANIFEST.json must be present."""
    manifest = TEMPLATES_DIR / "agent-workbench" / ".github" / "hooks" / "scripts" / "MANIFEST.json"
    assert manifest.is_file(), f"MANIFEST.json missing: {manifest}"


def test_clean_workspace_manifest_exists() -> None:
    """Clean-workspace MANIFEST.json must be present."""
    manifest = TEMPLATES_DIR / "clean-workspace" / ".github" / "hooks" / "scripts" / "MANIFEST.json"
    assert manifest.is_file(), f"MANIFEST.json missing: {manifest}"
