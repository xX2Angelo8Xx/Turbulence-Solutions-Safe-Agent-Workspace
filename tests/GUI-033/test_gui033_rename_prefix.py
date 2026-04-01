"""Tests for GUI-033: Rename workspace prefix TS-SAE to SAE."""

import shutil
import tempfile
import textwrap
from pathlib import Path

import pytest

from launcher.core.project_creator import create_project, replace_template_placeholders

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parents[2]
PROJECT_CREATOR_PY = REPO_ROOT / "src" / "launcher" / "core" / "project_creator.py"
APP_PY = REPO_ROOT / "src" / "launcher" / "gui" / "app.py"


def _make_minimal_template(tmp_path: Path) -> Path:
    """Create a minimal template directory suitable for create_project."""
    template = tmp_path / "template"
    template.mkdir()
    (template / "Project").mkdir()
    (template / "Project" / "README.md").write_text(
        "# {{PROJECT_NAME}}\nWorkspace: {{WORKSPACE_NAME}}\n", encoding="utf-8"
    )
    return template


# ---------------------------------------------------------------------------
# Tests: create_project produces SAE- prefix
# ---------------------------------------------------------------------------


def test_create_project_uses_sae_prefix(tmp_path):
    template = _make_minimal_template(tmp_path)
    dest = tmp_path / "dest"
    dest.mkdir()

    created = create_project(template, dest, "MyDemo")

    assert created.name.startswith("SAE-"), (
        f"Expected folder to start with 'SAE-', got: {created.name!r}"
    )


def test_create_project_no_ts_sae_prefix(tmp_path):
    template = _make_minimal_template(tmp_path)
    dest = tmp_path / "dest"
    dest.mkdir()

    created = create_project(template, dest, "MyDemo")

    assert not created.name.startswith("TS-SAE-"), (
        f"Folder still uses old 'TS-SAE-' prefix: {created.name!r}"
    )


def test_create_project_folder_name(tmp_path):
    template = _make_minimal_template(tmp_path)
    dest = tmp_path / "dest"
    dest.mkdir()

    created = create_project(template, dest, "MatlabDemo")

    assert created.name == "SAE-MatlabDemo", (
        f"Expected 'SAE-MatlabDemo', got: {created.name!r}"
    )


# ---------------------------------------------------------------------------
# Tests: replace_template_placeholders uses SAE- for WORKSPACE_NAME
# ---------------------------------------------------------------------------


def test_replace_template_placeholders_workspace_name(tmp_path):
    project_dir = tmp_path / "SAE-TestProject"
    project_dir.mkdir()
    md = project_dir / "README.md"
    md.write_text("Workspace: {{WORKSPACE_NAME}}\n", encoding="utf-8")

    replace_template_placeholders(project_dir, "TestProject")

    content = md.read_text(encoding="utf-8")
    assert "SAE-TestProject" in content, (
        f"Expected 'SAE-TestProject' in README.md, got: {content!r}"
    )


def test_replace_template_placeholders_no_ts_sae(tmp_path):
    project_dir = tmp_path / "SAE-TestProject"
    project_dir.mkdir()
    md = project_dir / "README.md"
    md.write_text("Workspace: {{WORKSPACE_NAME}}\n", encoding="utf-8")

    replace_template_placeholders(project_dir, "TestProject")

    content = md.read_text(encoding="utf-8")
    assert "TS-SAE-" not in content, (
        f"Found old 'TS-SAE-' prefix in README.md after replacement: {content!r}"
    )


# ---------------------------------------------------------------------------
# Tests: no TS-SAE references remain in source files
# ---------------------------------------------------------------------------


def test_source_project_creator_no_ts_sae():
    content = PROJECT_CREATOR_PY.read_text(encoding="utf-8")
    assert "TS-SAE" not in content, (
        "Found 'TS-SAE' in project_creator.py — rename was incomplete."
    )


def test_source_app_no_ts_sae():
    content = APP_PY.read_text(encoding="utf-8")
    assert "TS-SAE" not in content, (
        "Found 'TS-SAE' in app.py — rename was incomplete."
    )
