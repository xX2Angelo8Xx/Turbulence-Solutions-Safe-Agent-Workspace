"""Tests for DOC-009: AGENT-RULES.md included in placeholder replacement.

Verifies that replace_template_placeholders() in project_creator.py processes
AGENT-RULES.md and replaces all {{PROJECT_NAME}} and {{WORKSPACE_NAME}} tokens,
satisfying AC 9 of US-033.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from launcher.core.project_creator import replace_template_placeholders

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
AGENT_RULES_TEMPLATE = REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AGENT-RULES.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_agent_rules(base_dir: Path, project_name: str) -> Path:
    """Copy the real AGENT-RULES.md template into base_dir/<project_name>/AGENT-RULES.md."""
    project_dir = base_dir / project_name
    project_dir.mkdir(parents=True, exist_ok=True)
    agent_rules_dest = project_dir / "AGENT-RULES.md"
    shutil.copy2(str(AGENT_RULES_TEMPLATE), str(agent_rules_dest))
    return agent_rules_dest


# ---------------------------------------------------------------------------
# Scope check: AGENT-RULES.md must be matched by the rglob("*.md") pattern
# ---------------------------------------------------------------------------

def test_agent_rules_is_md_file():
    """AGENT-RULES.md has a .md extension and is therefore in the rglob('*.md') scan scope."""
    assert AGENT_RULES_TEMPLATE.suffix.lower() == ".md", (
        "AGENT-RULES.md does not have a .md extension — it would be skipped by rglob"
    )


def test_agent_rules_template_exists():
    """templates/agent-workbench/Project/AGENT-RULES.md must exist in the template."""
    assert AGENT_RULES_TEMPLATE.is_file(), (
        f"AGENT-RULES.md not found at {AGENT_RULES_TEMPLATE}"
    )


def test_agent_rules_found_by_rglob(tmp_path):
    """After copying the template, rglob('*.md') on the project directory finds AGENT-RULES.md."""
    project_name = "TestProject"
    agent_rules_dest = _setup_agent_rules(tmp_path, project_name)

    found = list(tmp_path.rglob("*.md"))
    assert agent_rules_dest in found, (
        "AGENT-RULES.md was not returned by rglob('*.md') — it would not be processed"
    )


# ---------------------------------------------------------------------------
# Placeholder replacement: {{PROJECT_NAME}}
# ---------------------------------------------------------------------------

def test_project_name_replaced_in_agent_rules(tmp_path):
    """After replace_template_placeholders(), {{PROJECT_NAME}} must not appear in AGENT-RULES.md."""
    project_name = "MatlabDemo"
    agent_rules_dest = _setup_agent_rules(tmp_path, project_name)

    # Confirm the placeholder is present before replacement
    original = agent_rules_dest.read_text(encoding="utf-8")
    assert "{{PROJECT_NAME}}" in original, (
        "Test pre-condition failed: AGENT-RULES.md template has no {{PROJECT_NAME}} placeholder"
    )

    replace_template_placeholders(tmp_path, project_name)

    result = agent_rules_dest.read_text(encoding="utf-8")
    assert "{{PROJECT_NAME}}" not in result, (
        "{{PROJECT_NAME}} placeholder still present in AGENT-RULES.md after replacement"
    )


# ---------------------------------------------------------------------------
# Placeholder replacement: {{WORKSPACE_NAME}}
# ---------------------------------------------------------------------------

def test_workspace_name_replaced_in_agent_rules(tmp_path):
    """After replace_template_placeholders(), {{WORKSPACE_NAME}} must not appear in AGENT-RULES.md."""
    project_name = "MatlabDemo"
    agent_rules_dest = _setup_agent_rules(tmp_path, project_name)

    # Confirm the placeholder is present before replacement
    original = agent_rules_dest.read_text(encoding="utf-8")
    assert "{{WORKSPACE_NAME}}" in original, (
        "Test pre-condition failed: AGENT-RULES.md template has no {{WORKSPACE_NAME}} placeholder"
    )

    replace_template_placeholders(tmp_path, project_name)

    result = agent_rules_dest.read_text(encoding="utf-8")
    assert "{{WORKSPACE_NAME}}" not in result, (
        "{{WORKSPACE_NAME}} placeholder still present in AGENT-RULES.md after replacement"
    )


# ---------------------------------------------------------------------------
# Actual project name appears in replaced content
# ---------------------------------------------------------------------------

def test_actual_project_name_in_agent_rules(tmp_path):
    """After replacement, the actual project name appears in AGENT-RULES.md."""
    project_name = "MatlabDemo"
    agent_rules_dest = _setup_agent_rules(tmp_path, project_name)

    replace_template_placeholders(tmp_path, project_name)

    result = agent_rules_dest.read_text(encoding="utf-8")
    assert project_name in result, (
        f"Expected project name '{project_name}' to appear in AGENT-RULES.md after replacement"
    )


def test_actual_workspace_name_in_agent_rules(tmp_path):
    """After replacement, the SAE-prefixed workspace name appears in AGENT-RULES.md."""
    project_name = "MatlabDemo"
    expected_workspace = f"SAE-{project_name}"
    agent_rules_dest = _setup_agent_rules(tmp_path, project_name)

    replace_template_placeholders(tmp_path, project_name)

    result = agent_rules_dest.read_text(encoding="utf-8")
    assert expected_workspace in result, (
        f"Expected workspace name '{expected_workspace}' to appear in AGENT-RULES.md after replacement"
    )


# ---------------------------------------------------------------------------
# Content completeness: no raw placeholder tokens remain
# ---------------------------------------------------------------------------

def test_no_raw_placeholders_remain_in_agent_rules(tmp_path):
    """All {{...}} placeholder tokens in AGENT-RULES.md are eliminated after replacement."""
    project_name = "DataScienceProject"
    agent_rules_dest = _setup_agent_rules(tmp_path, project_name)

    replace_template_placeholders(tmp_path, project_name)

    result = agent_rules_dest.read_text(encoding="utf-8")
    assert "{{PROJECT_NAME}}" not in result
    assert "{{WORKSPACE_NAME}}" not in result


# ---------------------------------------------------------------------------
# Regression: other .md files are still processed correctly
# ---------------------------------------------------------------------------

def test_regression_readme_still_processed(tmp_path):
    """Regression: README.md in the project directory still has its placeholders replaced."""
    project_name = "RegTest"
    project_dir = tmp_path / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    readme = project_dir / "README.md"
    readme.write_text(
        "# {{PROJECT_NAME}}\nWorkspace: {{WORKSPACE_NAME}}\n",
        encoding="utf-8",
    )

    replace_template_placeholders(tmp_path, project_name)

    result = readme.read_text(encoding="utf-8")
    assert "{{PROJECT_NAME}}" not in result, "README.md still contains {{PROJECT_NAME}}"
    assert "{{WORKSPACE_NAME}}" not in result, "README.md still contains {{WORKSPACE_NAME}}"
    assert project_name in result, "README.md does not contain the actual project name"


def test_regression_multiple_md_files_processed_together(tmp_path):
    """Regression: both AGENT-RULES.md and README.md are replaced in the same call."""
    project_name = "MultiTest"
    agent_rules_dest = _setup_agent_rules(tmp_path, project_name)

    project_dir = tmp_path / project_name
    readme = project_dir / "README.md"
    readme.write_text("# {{PROJECT_NAME}}\nWS: {{WORKSPACE_NAME}}", encoding="utf-8")

    replace_template_placeholders(tmp_path, project_name)

    agent_result = agent_rules_dest.read_text(encoding="utf-8")
    readme_result = readme.read_text(encoding="utf-8")

    assert "{{PROJECT_NAME}}" not in agent_result
    assert "{{WORKSPACE_NAME}}" not in agent_result
    assert "{{PROJECT_NAME}}" not in readme_result
    assert "{{WORKSPACE_NAME}}" not in readme_result


# ---------------------------------------------------------------------------
# Idempotency check
# ---------------------------------------------------------------------------

def test_replacement_is_idempotent(tmp_path):
    """Calling replace_template_placeholders() twice produces the same result."""
    project_name = "IdempotentTest"
    agent_rules_dest = _setup_agent_rules(tmp_path, project_name)

    replace_template_placeholders(tmp_path, project_name)
    first_pass = agent_rules_dest.read_text(encoding="utf-8")

    replace_template_placeholders(tmp_path, project_name)
    second_pass = agent_rules_dest.read_text(encoding="utf-8")

    assert first_pass == second_pass, (
        "replace_template_placeholders() is not idempotent for AGENT-RULES.md"
    )
