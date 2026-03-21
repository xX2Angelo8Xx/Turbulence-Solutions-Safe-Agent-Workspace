"""Tester edge-case tests for DOC-009: AGENT-RULES.md placeholder replacement.

Tests the three edge cases not covered by the developer's test suite:
  1. AGENT-RULES.md containing ONLY placeholder tokens is fully replaced.
  2. Non-.md files (e.g. .txt, .py, .json) are NOT modified by the function.
  3. Missing AGENT-RULES.md is handled gracefully (no exception raised).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from launcher.core.project_creator import replace_template_placeholders


# ---------------------------------------------------------------------------
# Edge Case 1 — file with ONLY placeholder tokens
# ---------------------------------------------------------------------------

def test_agent_rules_only_placeholders_fully_replaced(tmp_path):
    """AGENT-RULES.md that contains ONLY {{PROJECT_NAME}} / {{WORKSPACE_NAME}}
    tokens (and nothing else) is fully replaced, leaving no raw placeholders.
    """
    project_name = "OnlyPlaceholders"
    project_dir = tmp_path / project_name
    project_dir.mkdir(parents=True)

    agent_rules = project_dir / "AGENT-RULES.md"
    # Content is nothing but the two placeholder tokens, back-to-back.
    agent_rules.write_text(
        "{{PROJECT_NAME}}{{WORKSPACE_NAME}}",
        encoding="utf-8",
    )

    replace_template_placeholders(tmp_path, project_name)

    result = agent_rules.read_text(encoding="utf-8")
    assert "{{PROJECT_NAME}}" not in result, (
        "{{PROJECT_NAME}} still present after replacement of all-placeholder file"
    )
    assert "{{WORKSPACE_NAME}}" not in result, (
        "{{WORKSPACE_NAME}} still present after replacement of all-placeholder file"
    )
    expected_workspace = f"TS-SAE-{project_name}"
    assert project_name in result, (
        f"Expected '{project_name}' not found in replaced content"
    )
    assert expected_workspace in result, (
        f"Expected workspace name '{expected_workspace}' not found in replaced content"
    )


# ---------------------------------------------------------------------------
# Edge Case 2 — non-.md files are NOT modified
# ---------------------------------------------------------------------------

def test_non_md_txt_file_not_modified(tmp_path):
    """.txt file containing placeholder tokens is NOT modified by replace_template_placeholders()."""
    project_name = "NonMdTest"
    project_dir = tmp_path / project_name
    project_dir.mkdir(parents=True)

    txt_file = project_dir / "notes.txt"
    original_content = "Project: {{PROJECT_NAME}}, Workspace: {{WORKSPACE_NAME}}"
    txt_file.write_text(original_content, encoding="utf-8")

    replace_template_placeholders(tmp_path, project_name)

    result = txt_file.read_text(encoding="utf-8")
    assert result == original_content, (
        f".txt file was modified — should be skipped. Got: {result!r}"
    )


def test_non_md_python_file_not_modified(tmp_path):
    """.py file containing placeholder strings is NOT modified by replace_template_placeholders()."""
    project_name = "PythonFileTest"
    project_dir = tmp_path / project_name
    project_dir.mkdir(parents=True)

    py_file = project_dir / "config.py"
    original_content = 'PROJECT = "{{PROJECT_NAME}}"\nWS = "{{WORKSPACE_NAME}}"\n'
    py_file.write_text(original_content, encoding="utf-8")

    replace_template_placeholders(tmp_path, project_name)

    result = py_file.read_text(encoding="utf-8")
    assert result == original_content, (
        f".py file was modified — should be skipped. Got: {result!r}"
    )


def test_non_md_json_file_not_modified(tmp_path):
    """.json file containing placeholder strings is NOT modified by replace_template_placeholders()."""
    project_name = "JsonFileTest"
    project_dir = tmp_path / project_name
    project_dir.mkdir(parents=True)

    json_file = project_dir / "config.json"
    original_content = '{"project": "{{PROJECT_NAME}}", "workspace": "{{WORKSPACE_NAME}}"}\n'
    json_file.write_text(original_content, encoding="utf-8")

    replace_template_placeholders(tmp_path, project_name)

    result = json_file.read_text(encoding="utf-8")
    assert result == original_content, (
        f".json file was modified — should be skipped. Got: {result!r}"
    )


# ---------------------------------------------------------------------------
# Edge Case 3 — missing AGENT-RULES.md handled gracefully
# ---------------------------------------------------------------------------

def test_missing_agent_rules_no_exception(tmp_path):
    """replace_template_placeholders() does NOT raise if AGENT-RULES.md is absent."""
    project_name = "NoAgentRules"
    project_dir = tmp_path / project_name
    project_dir.mkdir(parents=True)

    # Deliberately do NOT create AGENT-RULES.md; only create a README.md
    readme = project_dir / "README.md"
    readme.write_text("# {{PROJECT_NAME}}\n", encoding="utf-8")

    # Must not raise
    replace_template_placeholders(tmp_path, project_name)

    # Other .md files are still processed normally
    result = readme.read_text(encoding="utf-8")
    assert "{{PROJECT_NAME}}" not in result, (
        "README.md wasn't processed even though AGENT-RULES.md was absent"
    )


def test_missing_agent_rules_empty_project_no_exception(tmp_path):
    """replace_template_placeholders() does NOT raise when the project directory
    contains no .md files at all (AGENT-RULES.md and README.md both absent)."""
    project_name = "EmptyProject"
    project_dir = tmp_path / project_name
    project_dir.mkdir(parents=True)
    # No files created at all — rglob returns nothing

    replace_template_placeholders(tmp_path, project_name)
    # If we reach here without exception, the test passes.
