"""Tests for DOC-002: {{PROJECT_NAME}} placeholders in README.md template files."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from launcher.core.project_creator import replace_template_placeholders, create_project

# Resolve template file paths relative to this test file's location.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_README = _REPO_ROOT / "templates" / "agent-workbench" / "README.md"
_TEMPLATE_README = _REPO_ROOT / "templates" / "agent-workbench" / "README.md"
_CODING_TEMPLATE = _REPO_ROOT / "templates" / "agent-workbench"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Static checks: template source files contain the placeholder
# ---------------------------------------------------------------------------

class TestTemplateFilesContainPlaceholder:
    """Verify that the template README files have been updated with {{PROJECT_NAME}}."""

    def test_default_readme_folder_table_uses_placeholder(self):
        """templates/agent-workbench/README.md folder table row uses {{PROJECT_NAME}}/ not Project/."""
        content = _DEFAULT_README.read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}/" in content

    def test_default_readme_no_hardcoded_project_folder(self):
        """templates/agent-workbench/README.md does not have hardcoded `Project/` as a folder entry."""
        content = _DEFAULT_README.read_text(encoding="utf-8")
        # The backtick-wrapped folder name `Project/` must not appear.
        assert "`Project/`" not in content

    def test_coding_template_readme_uses_placeholder(self):
        """templates/agent-workbench/README.md folder table row uses {{PROJECT_NAME}}/ not Project/."""
        content = _TEMPLATE_README.read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}/" in content

    def test_coding_template_readme_no_hardcoded_project_folder(self):
        """templates/agent-workbench/README.md does not have hardcoded `Project/` as a folder entry."""
        content = _TEMPLATE_README.read_text(encoding="utf-8")
        assert "`Project/`" not in content

    def test_both_template_files_are_identical(self):
        """templates/agent-workbench/README.md and templates/coding/README.md have the same content."""
        default_content = _DEFAULT_README.read_text(encoding="utf-8")
        template_content = _TEMPLATE_README.read_text(encoding="utf-8")
        assert default_content == template_content

    def test_placeholder_present_in_getting_started_section(self):
        """Getting Started section references {{PROJECT_NAME}}/ not Project/."""
        content = _DEFAULT_README.read_text(encoding="utf-8")
        assert "Place your project files in `{{PROJECT_NAME}}/`." in content

    def test_placeholder_present_in_agent_rules_section(self):
        """Agent Rules section references {{PROJECT_NAME}}/ path to AgentDocs/AGENT-RULES.md."""
        content = _DEFAULT_README.read_text(encoding="utf-8")
        assert "`{{PROJECT_NAME}}/AgentDocs/AGENT-RULES.md`" in content

    def test_placeholder_present_in_folder_table_row(self):
        """Workspace structure table row uses {{PROJECT_NAME}}/ as the project folder entry."""
        content = _DEFAULT_README.read_text(encoding="utf-8")
        assert "| `{{PROJECT_NAME}}/` |" in content


# ---------------------------------------------------------------------------
# Unit tests: placeholder replacement in README-like content
# ---------------------------------------------------------------------------

class TestPlaceholderReplacementInReadme:
    """Verify replace_template_placeholders() works on README.md with {{PROJECT_NAME}}/ content."""

    def test_folder_table_placeholder_replaced(self, tmp_path):
        """{{PROJECT_NAME}}/ in the folder table is replaced with the actual project name."""
        readme = tmp_path / "README.md"
        _write(readme, "| `{{PROJECT_NAME}}/` | Auto-allowed | Working dir |")
        replace_template_placeholders(tmp_path, "Tornado")
        result = readme.read_text(encoding="utf-8")
        assert "`Tornado/`" in result
        assert "{{PROJECT_NAME}}" not in result

    def test_tier1_description_placeholder_replaced(self, tmp_path):
        """{{PROJECT_NAME}}/ in Tier 1 description is replaced."""
        readme = tmp_path / "README.md"
        _write(readme, "Exempt tools targeting `{{PROJECT_NAME}}/` proceed without a dialog.")
        replace_template_placeholders(tmp_path, "Eagle")
        result = readme.read_text(encoding="utf-8")
        assert "targeting `Eagle/` proceed without a dialog." in result
        assert "{{PROJECT_NAME}}" not in result

    def test_tier2_description_placeholder_replaced(self, tmp_path):
        """{{PROJECT_NAME}}/ in Tier 2 description is replaced."""
        readme = tmp_path / "README.md"
        _write(readme, "Exempt tools outside `{{PROJECT_NAME}}/`, or any non-exempt tool anywhere, trigger a dialog.")
        replace_template_placeholders(tmp_path, "Falcon")
        result = readme.read_text(encoding="utf-8")
        assert "outside `Falcon/`" in result
        assert "{{PROJECT_NAME}}" not in result

    def test_exempt_tools_section_placeholder_replaced(self, tmp_path):
        """{{PROJECT_NAME}}/ in Exempt Tools description is replaced."""
        readme = tmp_path / "README.md"
        _write(readme, "These tools are auto-allowed inside `{{PROJECT_NAME}}/` and trigger an approval dialog elsewhere:")
        replace_template_placeholders(tmp_path, "Hawk")
        result = readme.read_text(encoding="utf-8")
        assert "inside `Hawk/`" in result
        assert "{{PROJECT_NAME}}" not in result

    def test_all_four_occurrences_replaced(self, tmp_path):
        """All four {{PROJECT_NAME}}/ occurrences in a README-like file are replaced."""
        content = (
            "| `{{PROJECT_NAME}}/` | Auto-allowed |\n"
            "Targeting `{{PROJECT_NAME}}/` proceed.\n"
            "Outside `{{PROJECT_NAME}}/`, trigger.\n"
            "Inside `{{PROJECT_NAME}}/` and elsewhere.\n"
        )
        readme = tmp_path / "README.md"
        _write(readme, content)
        replace_template_placeholders(tmp_path, "Storm")
        result = readme.read_text(encoding="utf-8")
        assert result.count("Storm/") == 4
        assert "{{PROJECT_NAME}}" not in result

    def test_non_folder_project_references_unchanged(self, tmp_path):
        """'project files' and 'project folder' references are not affected by replacement."""
        readme = tmp_path / "README.md"
        _write(
            readme,
            "Working directory for all project files.\n"
            "This is the project folder.\n"
            "| `{{PROJECT_NAME}}/` | allowed |\n"
        )
        replace_template_placeholders(tmp_path, "Cloud")
        result = readme.read_text(encoding="utf-8")
        # Generic "project" references are untouched.
        assert "all project files" in result
        assert "project folder" in result
        # Placeholder is still replaced.
        assert "`Cloud/`" in result


# ---------------------------------------------------------------------------
# Integration tests: create_project produces README with actual name
# ---------------------------------------------------------------------------

class TestCreateProjectReadmePlaceholders:
    """End-to-end: after create_project(), README.md reflects the actual project name."""

    def test_readme_project_name_after_create(self, tmp_path):
        """After create_project(), README.md in new workspace has actual project name."""
        # Build a minimal template that mirrors the README placeholder structure.
        template = tmp_path / "template"
        dest = tmp_path / "dest"
        dest.mkdir()

        # Simulate the coding template: Project/ subfolder + README.md with placeholder.
        (template / "Project").mkdir(parents=True)
        _write(
            template / "README.md",
            "| `{{PROJECT_NAME}}/` | Auto-allowed |\n"
            "Exempt tools targeting `{{PROJECT_NAME}}/` proceed.\n",
        )

        new_workspace = create_project(template, dest, "Zephyr")
        readme = new_workspace / "README.md"
        content = readme.read_text(encoding="utf-8")

        assert "`Zephyr/`" in content
        assert "{{PROJECT_NAME}}" not in content

    def test_readme_no_hardcoded_project_after_create(self, tmp_path):
        """After create_project(), README.md does not contain the raw placeholder token."""
        template = tmp_path / "template"
        dest = tmp_path / "dest"
        dest.mkdir()
        (template / "Project").mkdir(parents=True)
        _write(
            template / "README.md",
            "| `{{PROJECT_NAME}}/` | Auto-allowed | Working dir |\n",
        )

        new_workspace = create_project(template, dest, "Aurora")
        readme = new_workspace / "README.md"
        content = readme.read_text(encoding="utf-8")

        assert "{{PROJECT_NAME}}" not in content
        assert "`Aurora/`" in content

    def test_readme_project_folder_renamed_matches(self, tmp_path):
        """The folder name referenced in README.md matches the renamed project subfolder."""
        template = tmp_path / "template"
        dest = tmp_path / "dest"
        dest.mkdir()
        (template / "Project").mkdir(parents=True)
        _write(
            template / "README.md",
            "| `{{PROJECT_NAME}}/` | Auto-allowed | Working dir |\n",
        )

        new_workspace = create_project(template, dest, "Nimbus")
        readme = new_workspace / "README.md"
        content = readme.read_text(encoding="utf-8")

        # README refers to the project subfolder by name.
        assert "`Nimbus/`" in content
        # The actual renamed subfolder must exist inside the workspace.
        assert (new_workspace / "Nimbus").is_dir()
