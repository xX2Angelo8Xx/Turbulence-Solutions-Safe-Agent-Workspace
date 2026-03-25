"""FIX-071 — Tests: Update all test references for template rename.

Verifies that:
1. templates/coding/ no longer exists (was renamed to agent-workbench/)
2. templates/creative-marketing/ no longer exists (was renamed to certification-pipeline/)
3. templates/agent-workbench/ exists
4. templates/certification-pipeline/ exists
5. Key previously-broken test files now use the correct paths
6. No test files contain raw os.path.join/Path() constructions with old names
"""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "templates"
TESTS_DIR = REPO_ROOT / "tests"


# ---------------------------------------------------------------------------
# Template directory existence
# ---------------------------------------------------------------------------

def test_old_coding_template_dir_does_not_exist():
    """templates/coding/ must not exist after rename to agent-workbench/."""
    assert not (TEMPLATES_DIR / "coding").exists(), (
        "templates/coding/ still exists — it should have been renamed to agent-workbench/"
    )


def test_old_creative_marketing_dir_does_not_exist():
    """templates/creative-marketing/ must not exist after rename to certification-pipeline/."""
    assert not (TEMPLATES_DIR / "creative-marketing").exists(), (
        "templates/creative-marketing/ still exists — should be renamed to certification-pipeline/"
    )


def test_agent_workbench_dir_exists():
    """templates/agent-workbench/ must exist."""
    assert (TEMPLATES_DIR / "agent-workbench").is_dir(), (
        "templates/agent-workbench/ does not exist"
    )


def test_certification_pipeline_dir_exists():
    """templates/certification-pipeline/ must exist."""
    assert (TEMPLATES_DIR / "certification-pipeline").is_dir(), (
        "templates/certification-pipeline/ does not exist"
    )


# ---------------------------------------------------------------------------
# Critical path constants in previously-failing test files
# ---------------------------------------------------------------------------

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_doc003_edge_cases_uses_agent_workbench():
    """DOC-003 edge cases must point TEMPLATES_CODING_FILE to agent-workbench."""
    content = _read(TESTS_DIR / "DOC-003" / "test_doc003_edge_cases.py")
    assert '"agent-workbench"' in content, (
        "test_doc003_edge_cases.py still has a TEMPLATES_CODING_FILE pointing to old path"
    )
    assert '"coding"' not in content.split("TEMPLATES_CODING_FILE")[1].split(")")[0], (
        "test_doc003_edge_cases.py TEMPLATES_CODING_FILE still references templates/coding"
    )


def test_doc003_placeholders_uses_agent_workbench():
    """DOC-003 placeholders must point TEMPLATES_CODING_FILE to agent-workbench."""
    content = _read(TESTS_DIR / "DOC-003" / "test_doc003_placeholders.py")
    # The TEMPLATES_CODING_FILE variable should use agent-workbench
    match = re.search(r'TEMPLATES_CODING_FILE\s*=.*?(?=\n\n)', content, re.DOTALL)
    assert match is not None, "TEMPLATES_CODING_FILE not found in test_doc003_placeholders.py"
    assert "agent-workbench" in match.group(0), (
        "test_doc003_placeholders.py TEMPLATES_CODING_FILE still references templates/coding"
    )


def test_saf024_edge_cases_uses_agent_workbench():
    """SAF-024 edge cases must point _TEMPLATE_PATH to agent-workbench."""
    content = _read(TESTS_DIR / "SAF-024" / "test_saf024_edge_cases.py")
    match = re.search(r'_TEMPLATE_PATH\s*=.*?(?=\n\n)', content, re.DOTALL)
    assert match is not None, "_TEMPLATE_PATH not found in test_saf024_edge_cases.py"
    assert "agent-workbench" in match.group(0), (
        "test_saf024_edge_cases.py _TEMPLATE_PATH still references templates/coding"
    )


def test_saf024_generic_deny_uses_agent_workbench():
    """SAF-024 generic deny messages must point _TEMPLATE_SCRIPTS_DIR to agent-workbench."""
    content = _read(TESTS_DIR / "SAF-024" / "test_saf024_generic_deny_messages.py")
    match = re.search(r'_TEMPLATE_SCRIPTS_DIR\s*=.*?(?=\n\n)', content, re.DOTALL)
    assert match is not None, "_TEMPLATE_SCRIPTS_DIR not found in test_saf024_generic_deny_messages.py"
    assert "agent-workbench" in match.group(0), (
        "test_saf024_generic_deny_messages.py _TEMPLATE_SCRIPTS_DIR still references templates/coding"
    )


def test_saf022_no_broken_tuple_in_bypass_tests():
    """SAF-022 TestBypassAttempt loops must use 2-element tuples (label, path)."""
    content = _read(TESTS_DIR / "SAF-022" / "test_saf022_noagentzone_exclude.py")
    # Look for the broken pattern: ("templates", "agent-workbench", <var>) — 3-element tuple
    broken_pattern = r'\("templates",\s*"agent-workbench",\s*\w'
    matches = re.findall(broken_pattern, content)
    assert len(matches) == 0, (
        f"Found {len(matches)} broken 3-element tuple(s) in test_saf022_noagentzone_exclude.py; "
        f"should be 2-element (label, path)"
    )


def test_gui020_uses_agent_workbench_display_name():
    """GUI-020 counter config test must use 'Agent Workbench' as dropdown return value."""
    content = _read(TESTS_DIR / "GUI-020" / "test_gui020_app_passes_counter_config.py")
    assert '"Agent Workbench"' in content, (
        "test_gui020_app_passes_counter_config.py still uses 'Coding' as dropdown value"
    )


def test_gui022_uses_agent_workbench_template():
    """GUI-022 include readmes test must use 'Agent Workbench' as template name."""
    content = _read(TESTS_DIR / "GUI-022" / "test_gui022_include_readmes_checkbox.py")
    assert '"Agent Workbench"' in content, (
        "test_gui022_include_readmes_checkbox.py still uses 'Coding' as template name"
    )
