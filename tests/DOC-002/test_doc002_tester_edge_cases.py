"""Tester edge-case tests for DOC-002: README.md placeholder content verification."""

from __future__ import annotations

from pathlib import Path

from launcher.core.project_creator import replace_template_placeholders, create_project

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_README = _REPO_ROOT / "Default-Project" / "README.md"
_TEMPLATE_README = _REPO_ROOT / "templates" / "coding" / "README.md"
_NOAGENTZONE_README = _REPO_ROOT / "Default-Project" / "NoAgentZone" / "README.md"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Placeholder count: verify exactly 4 occurrences in each template
# ---------------------------------------------------------------------------

class TestPlaceholderCount:
    """Verify that each template README has exactly 4 occurrences of {{PROJECT_NAME}}."""

    def test_default_readme_has_exactly_four_placeholder_occurrences(self):
        """Default-Project/README.md contains exactly 4 {{PROJECT_NAME}} tokens."""
        content = _DEFAULT_README.read_text(encoding="utf-8")
        count = content.count("{{PROJECT_NAME}}")
        assert count == 4, f"Expected 4 occurrences but found {count}"

    def test_coding_template_readme_has_exactly_four_placeholder_occurrences(self):
        """templates/coding/README.md contains exactly 4 {{PROJECT_NAME}} tokens."""
        content = _TEMPLATE_README.read_text(encoding="utf-8")
        count = content.count("{{PROJECT_NAME}}")
        assert count == 4, f"Expected 4 occurrences but found {count}"

    def test_no_workspace_name_placeholder_in_default_readme(self):
        """Default-Project/README.md does not contain {{WORKSPACE_NAME}} (design decision)."""
        content = _DEFAULT_README.read_text(encoding="utf-8")
        assert "{{WORKSPACE_NAME}}" not in content

    def test_no_workspace_name_placeholder_in_coding_template_readme(self):
        """templates/coding/README.md does not contain {{WORKSPACE_NAME}} (design decision)."""
        content = _TEMPLATE_README.read_text(encoding="utf-8")
        assert "{{WORKSPACE_NAME}}" not in content


# ---------------------------------------------------------------------------
# NoAgentZone README remains static (AC 4 from US-023)
# ---------------------------------------------------------------------------

class TestNoAgentZoneUnchanged:
    """NoAgentZone/README.md is generic and must not contain dynamic placeholders."""

    def test_noagentzone_readme_has_no_project_name_placeholder(self):
        """NoAgentZone/README.md does not use {{PROJECT_NAME}} — it should remain generic."""
        content = _NOAGENTZONE_README.read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" not in content

    def test_noagentzone_readme_has_no_workspace_name_placeholder(self):
        """NoAgentZone/README.md does not use {{WORKSPACE_NAME}} — it should remain generic."""
        content = _NOAGENTZONE_README.read_text(encoding="utf-8")
        assert "{{WORKSPACE_NAME}}" not in content


# ---------------------------------------------------------------------------
# Project names with special character patterns
# ---------------------------------------------------------------------------

class TestSpecialProjectNames:
    """Verify placeholder replacement works correctly with edge-case project names."""

    def test_project_name_with_hyphen(self, tmp_path):
        """Project name containing hyphens (e.g. My-Project) is substituted correctly."""
        readme = tmp_path / "README.md"
        _write(readme, "| `{{PROJECT_NAME}}/` | Auto-allowed |\nTargeting `{{PROJECT_NAME}}/`.\n")
        replace_template_placeholders(tmp_path, "My-Project")
        result = readme.read_text(encoding="utf-8")
        assert "`My-Project/`" in result
        assert "{{PROJECT_NAME}}" not in result

    def test_project_name_with_underscore(self, tmp_path):
        """Project name containing underscores is substituted correctly."""
        readme = tmp_path / "README.md"
        _write(readme, "| `{{PROJECT_NAME}}/` | Auto-allowed |\n")
        replace_template_placeholders(tmp_path, "Alpha_Beta")
        result = readme.read_text(encoding="utf-8")
        assert "`Alpha_Beta/`" in result
        assert "{{PROJECT_NAME}}" not in result

    def test_project_name_with_digits(self, tmp_path):
        """Project name containing digits is substituted correctly."""
        readme = tmp_path / "README.md"
        _write(readme, "| `{{PROJECT_NAME}}/` | Auto-allowed |\n")
        replace_template_placeholders(tmp_path, "Project2026")
        result = readme.read_text(encoding="utf-8")
        assert "`Project2026/`" in result
        assert "{{PROJECT_NAME}}" not in result

    def test_project_name_with_regex_special_chars_safe(self, tmp_path):
        """Project name with regex-special chars (dot, plus) is substituted safely via str.replace."""
        readme = tmp_path / "README.md"
        _write(readme, "| `{{PROJECT_NAME}}/` | Auto-allowed |\n")
        # str.replace() is used — no regex, so these chars are safe
        replace_template_placeholders(tmp_path, "Proj.Name")
        result = readme.read_text(encoding="utf-8")
        assert "`Proj.Name/`" in result
        assert "{{PROJECT_NAME}}" not in result

    def test_project_name_multiple_hyphens(self, tmp_path):
        """Project name with multiple hyphens is fully substituted."""
        readme = tmp_path / "README.md"
        _write(readme, "| `{{PROJECT_NAME}}/` | Auto-allowed |\nInside `{{PROJECT_NAME}}/` tools.\n")
        replace_template_placeholders(tmp_path, "Alpha-Beta-Gamma")
        result = readme.read_text(encoding="utf-8")
        assert result.count("`Alpha-Beta-Gamma/`") == 2
        assert "{{PROJECT_NAME}}" not in result


# ---------------------------------------------------------------------------
# All four README occurrences changed after replacement
# ---------------------------------------------------------------------------

class TestAllOccurrencesInActualTemplate:
    """Verify that after replacement, all 4 occurrences in an actual-content copy are resolved."""

    def test_all_four_actual_readme_occurrences_replaced(self, tmp_path):
        """Copy of Default-Project/README.md has all 4 {{PROJECT_NAME}} tokens replaced."""
        readme_src = _DEFAULT_README.read_text(encoding="utf-8")
        dest_readme = tmp_path / "README.md"
        _write(dest_readme, readme_src)

        replace_template_placeholders(tmp_path, "Nimbus")

        result = dest_readme.read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" not in result
        assert result.count("Nimbus/") == 4

    def test_replacement_leaves_other_content_intact(self, tmp_path):
        """After replacement, the standard sections (headings, NoAgentZone, .github) remain."""
        readme_src = _DEFAULT_README.read_text(encoding="utf-8")
        dest_readme = tmp_path / "README.md"
        _write(dest_readme, readme_src)

        replace_template_placeholders(tmp_path, "Cumulus")

        result = dest_readme.read_text(encoding="utf-8")
        assert "NoAgentZone/" in result
        assert ".github/" in result
        assert ".vscode/" in result
        assert "Turbulence Solutions" in result
