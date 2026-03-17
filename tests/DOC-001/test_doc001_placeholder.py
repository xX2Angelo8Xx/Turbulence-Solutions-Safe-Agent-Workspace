"""Tests for DOC-001: replace_template_placeholders in project_creator.py."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from launcher.core.project_creator import replace_template_placeholders, create_project


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Unit tests for replace_template_placeholders
# ---------------------------------------------------------------------------

class TestReplaceTemplatePlaceholders:

    def test_md_project_name_replaced(self, tmp_path):
        """{{PROJECT_NAME}} in a .md file is replaced with project_name."""
        md = tmp_path / "README.md"
        _write(md, "# {{PROJECT_NAME}}\nWelcome to {{PROJECT_NAME}}.")
        replace_template_placeholders(tmp_path, "MyDemo")
        result = md.read_text(encoding="utf-8")
        assert "MyDemo" in result
        assert "{{PROJECT_NAME}}" not in result

    def test_md_workspace_name_replaced(self, tmp_path):
        """{{WORKSPACE_NAME}} in a .md file is replaced with TS-SAE-{project_name}."""
        md = tmp_path / "README.md"
        _write(md, "Workspace: {{WORKSPACE_NAME}}")
        replace_template_placeholders(tmp_path, "Alpha")
        result = md.read_text(encoding="utf-8")
        assert "TS-SAE-Alpha" in result
        assert "{{WORKSPACE_NAME}}" not in result

    def test_both_placeholders_replaced(self, tmp_path):
        """Both {{PROJECT_NAME}} and {{WORKSPACE_NAME}} are replaced in the same file."""
        md = tmp_path / "docs.md"
        _write(md, "Project: {{PROJECT_NAME}}, Workspace: {{WORKSPACE_NAME}}")
        replace_template_placeholders(tmp_path, "Demo")
        result = md.read_text(encoding="utf-8")
        assert "Demo" in result
        assert "TS-SAE-Demo" in result
        assert "{{PROJECT_NAME}}" not in result
        assert "{{WORKSPACE_NAME}}" not in result

    def test_non_md_file_untouched(self, tmp_path):
        """A .txt file containing placeholder tokens is NOT modified."""
        txt = tmp_path / "notes.txt"
        original = "Project: {{PROJECT_NAME}}, Workspace: {{WORKSPACE_NAME}}"
        _write(txt, original)
        replace_template_placeholders(tmp_path, "Demo")
        assert txt.read_text(encoding="utf-8") == original

    def test_py_file_untouched(self, tmp_path):
        """A .py file containing placeholder tokens is NOT modified."""
        py_file = tmp_path / "config.py"
        original = 'PROJECT = "{{PROJECT_NAME}}"'
        _write(py_file, original)
        replace_template_placeholders(tmp_path, "Demo")
        assert py_file.read_text(encoding="utf-8") == original

    def test_binary_file_skipped(self, tmp_path):
        """A binary file is not corrupted — processing is silently skipped."""
        # Rename trick: write binary bytes to a file with .md extension
        bin_file = tmp_path / "binary.md"
        # Write raw bytes that include the placeholder as bytes + non-UTF-8 sequences
        bin_file.write_bytes(b"\xff\xfe{{PROJECT_NAME}}\x00\x01\x02")
        original_bytes = bin_file.read_bytes()
        replace_template_placeholders(tmp_path, "Demo")
        # File must be byte-for-byte identical after processing
        assert bin_file.read_bytes() == original_bytes

    def test_nested_md_replaced(self, tmp_path):
        """Placeholder in a nested subdirectory .md file is replaced."""
        nested = tmp_path / "sub" / "deeper"
        nested.mkdir(parents=True)
        md = nested / "info.md"
        _write(md, "Folder: {{PROJECT_NAME}}")
        replace_template_placeholders(tmp_path, "NestedDemo")
        assert "NestedDemo" in md.read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" not in md.read_text(encoding="utf-8")

    def test_idempotent(self, tmp_path):
        """Running replacement twice produces the same result."""
        md = tmp_path / "README.md"
        _write(md, "# {{PROJECT_NAME}} — {{WORKSPACE_NAME}}")
        replace_template_placeholders(tmp_path, "Repeat")
        first_run = md.read_text(encoding="utf-8")
        replace_template_placeholders(tmp_path, "Repeat")
        second_run = md.read_text(encoding="utf-8")
        assert first_run == second_run

    def test_no_placeholder_file_not_rewritten(self, tmp_path):
        """A .md file without any placeholder is not rewritten (content unchanged)."""
        md = tmp_path / "notes.md"
        original = "# Static content\nNo placeholders here."
        _write(md, original)
        # Record mtime before
        mtime_before = md.stat().st_mtime
        replace_template_placeholders(tmp_path, "Demo")
        # Content must be identical
        assert md.read_text(encoding="utf-8") == original
        # mtime should not have changed (file was not rewritten)
        assert md.stat().st_mtime == mtime_before

    def test_empty_project_name(self, tmp_path):
        """Empty project_name replaces tokens with empty string."""
        md = tmp_path / "README.md"
        _write(md, "Name: {{PROJECT_NAME}}, WS: {{WORKSPACE_NAME}}")
        replace_template_placeholders(tmp_path, "")
        result = md.read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" not in result
        assert "{{WORKSPACE_NAME}}" not in result
        assert "TS-SAE-" in result  # workspace name still has prefix

    def test_multiple_md_files_all_replaced(self, tmp_path):
        """All .md files in the tree are processed."""
        files = [
            tmp_path / "README.md",
            tmp_path / "sub" / "GUIDE.md",
            tmp_path / "sub" / "deeper" / "info.md",
        ]
        for f in files:
            _write(f, "{{PROJECT_NAME}} — {{WORKSPACE_NAME}}")
        replace_template_placeholders(tmp_path, "Multi")
        for f in files:
            content = f.read_text(encoding="utf-8")
            assert "Multi" in content
            assert "TS-SAE-Multi" in content
            assert "{{PROJECT_NAME}}" not in content
            assert "{{WORKSPACE_NAME}}" not in content


# ---------------------------------------------------------------------------
# Integration test: create_project calls replacement
# ---------------------------------------------------------------------------

class TestCreateProjectIntegration:

    def test_create_project_replaces_placeholders(self, tmp_path):
        """create_project() replaces placeholders in the copied template."""
        # Build a minimal template with a .md placeholder file
        template = tmp_path / "template"
        template.mkdir()
        (template / "README.md").write_text(
            "Project: {{PROJECT_NAME}}, WS: {{WORKSPACE_NAME}}", encoding="utf-8"
        )
        dest = tmp_path / "dest"
        dest.mkdir()

        result = create_project(template, dest, "IntTest")
        readme = result / "README.md"
        content = readme.read_text(encoding="utf-8")
        assert "IntTest" in content
        assert "TS-SAE-IntTest" in content
        assert "{{PROJECT_NAME}}" not in content
        assert "{{WORKSPACE_NAME}}" not in content

    def test_create_project_non_md_untouched(self, tmp_path):
        """create_project() does not modify non-.md files in the template."""
        template = tmp_path / "template"
        template.mkdir()
        original = "Token: {{PROJECT_NAME}}"
        (template / "config.txt").write_text(original, encoding="utf-8")
        dest = tmp_path / "dest"
        dest.mkdir()

        result = create_project(template, dest, "TxtTest")
        assert (result / "config.txt").read_text(encoding="utf-8") == original
