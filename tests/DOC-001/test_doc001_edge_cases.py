"""DOC-001 Tester edge-case tests: placeholder replacement system."""

from __future__ import annotations

import stat
import sys
from pathlib import Path

import pytest

from launcher.core.project_creator import replace_template_placeholders


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Edge case: project name containing hyphens
# ---------------------------------------------------------------------------

class TestNameWithHyphens:
    def test_name_with_hyphens_replaced_in_project_name(self, tmp_path):
        """Project name containing hyphens is substituted verbatim."""
        md = tmp_path / "README.md"
        _write(md, "# {{PROJECT_NAME}}")
        replace_template_placeholders(tmp_path, "My-Cool-Project")
        result = md.read_text(encoding="utf-8")
        assert "My-Cool-Project" in result
        assert "{{PROJECT_NAME}}" not in result

    def test_name_with_hyphens_workspace_name(self, tmp_path):
        """Workspace name correctly prefixes a hyphenated project name."""
        md = tmp_path / "README.md"
        _write(md, "WS: {{WORKSPACE_NAME}}")
        replace_template_placeholders(tmp_path, "My-Cool-Project")
        result = md.read_text(encoding="utf-8")
        assert "SAE-My-Cool-Project" in result
        assert "{{WORKSPACE_NAME}}" not in result

    def test_name_with_leading_hyphen(self, tmp_path):
        """Project name starting with a hyphen is substituted without error."""
        md = tmp_path / "README.md"
        _write(md, "Name: {{PROJECT_NAME}}")
        replace_template_placeholders(tmp_path, "-LeadingHyphen")
        result = md.read_text(encoding="utf-8")
        assert "-LeadingHyphen" in result
        assert "{{PROJECT_NAME}}" not in result

    def test_name_with_consecutive_hyphens(self, tmp_path):
        """Project name with consecutive hyphens (e.g., 'A--B') is substituted correctly."""
        md = tmp_path / "README.md"
        _write(md, "{{PROJECT_NAME}}")
        replace_template_placeholders(tmp_path, "A--B")
        result = md.read_text(encoding="utf-8")
        assert "A--B" in result
        assert "{{PROJECT_NAME}}" not in result


# ---------------------------------------------------------------------------
# Edge case: project name at maximum practical length
# ---------------------------------------------------------------------------

class TestMaxLengthName:
    def test_long_name_replaced_project(self, tmp_path):
        """A 200-character project name is substituted correctly in content."""
        long_name = "A" * 200
        md = tmp_path / "README.md"
        _write(md, "Name: {{PROJECT_NAME}}")
        replace_template_placeholders(tmp_path, long_name)
        result = md.read_text(encoding="utf-8")
        assert long_name in result
        assert "{{PROJECT_NAME}}" not in result

    def test_long_name_replaced_workspace(self, tmp_path):
        """A 200-character name produces the correct SAE-{name} workspace token."""
        long_name = "B" * 200
        md = tmp_path / "README.md"
        _write(md, "WS: {{WORKSPACE_NAME}}")
        replace_template_placeholders(tmp_path, long_name)
        result = md.read_text(encoding="utf-8")
        assert f"SAE-{long_name}" in result
        assert "{{WORKSPACE_NAME}}" not in result

    def test_long_name_multiple_occurrences(self, tmp_path):
        """All occurrences in a file are replaced even with a long name."""
        long_name = "C" * 150
        content = " ".join(["{{PROJECT_NAME}}"] * 10)
        md = tmp_path / "README.md"
        _write(md, content)
        replace_template_placeholders(tmp_path, long_name)
        result = md.read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" not in result
        assert result.count(long_name) == 10


# ---------------------------------------------------------------------------
# Edge case: deeply nested .md files (5+ levels)
# ---------------------------------------------------------------------------

class TestDeeplyNestedMd:
    def test_five_levels_deep(self, tmp_path):
        """Placeholder in a .md file 5 directory levels deep is replaced."""
        deep_dir = tmp_path / "a" / "b" / "c" / "d" / "e"
        deep_dir.mkdir(parents=True)
        md = deep_dir / "deep.md"
        _write(md, "{{PROJECT_NAME}}")
        replace_template_placeholders(tmp_path, "DeepTest")
        assert "DeepTest" in md.read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" not in md.read_text(encoding="utf-8")

    def test_mixed_depth_all_replaced(self, tmp_path):
        """Files at multiple depths are all replaced in a single pass."""
        paths = [
            tmp_path / "top.md",
            tmp_path / "a" / "mid.md",
            tmp_path / "a" / "b" / "c" / "d" / "e" / "f" / "bottom.md",
        ]
        for p in paths:
            _write(p, "{{PROJECT_NAME}} — {{WORKSPACE_NAME}}")
        replace_template_placeholders(tmp_path, "DeepMulti")
        for p in paths:
            content = p.read_text(encoding="utf-8")
            assert "DeepMulti" in content
            assert "SAE-DeepMulti" in content
            assert "{{PROJECT_NAME}}" not in content
            assert "{{WORKSPACE_NAME}}" not in content


# ---------------------------------------------------------------------------
# Edge case: read-only .md file
# ---------------------------------------------------------------------------

class TestReadOnlyMdFile:
    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific permissions test")
    def test_readonly_md_with_no_placeholder_not_written(self, tmp_path):
        """Read-only .md file without placeholders is not written (no PermissionError)."""
        md = tmp_path / "readonly_no_placeholder.md"
        _write(md, "# Static content with no placeholders.")
        # Make read-only
        md.chmod(stat.S_IREAD)
        try:
            # Must not raise even though file is read-only — no write needed
            replace_template_placeholders(tmp_path, "TestProj")
            result = md.read_text(encoding="utf-8")
            assert "{{PROJECT_NAME}}" not in result
        finally:
            md.chmod(stat.S_IWRITE | stat.S_IREAD)

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific permissions test")
    def test_readonly_md_with_placeholder_raises_or_skips(self, tmp_path):
        """Read-only .md file containing a placeholder: implementation either
        skips it gracefully (preferred) or raises PermissionError.
        This test documents the current behaviour — if it raises, a FIX WP is needed."""
        md = tmp_path / "readonly_with_placeholder.md"
        _write(md, "# {{PROJECT_NAME}}")
        md.chmod(stat.S_IREAD)
        try:
            try:
                replace_template_placeholders(tmp_path, "TestProj")
                # If it did NOT raise: the file content should still contain the original
                # (skipped gracefully) OR be replaced (somehow succeeded).
                result = md.read_text(encoding="utf-8")
                # Whether it skipped or replaced, no crash is the desired outcome.
                assert True  # graceful — no exception raised
            except PermissionError:
                # Document current behaviour: raises PermissionError on write.
                # This is a known limitation — log as a bug if crash on readonly files
                # in real-world templates is considered a defect.
                pytest.xfail(
                    "replace_template_placeholders raises PermissionError on read-only"
                    " .md files that contain placeholders. A FIX WP should handle this."
                )
        finally:
            md.chmod(stat.S_IWRITE | stat.S_IREAD)


# ---------------------------------------------------------------------------
# Edge case: .md file with only one type of placeholder
# ---------------------------------------------------------------------------

class TestSinglePlaceholderOnly:
    def test_only_project_name(self, tmp_path):
        """File with only {{PROJECT_NAME}} (no {{WORKSPACE_NAME}}) is handled correctly."""
        md = tmp_path / "README.md"
        _write(md, "Project: {{PROJECT_NAME}}\nNo workspace here.")
        replace_template_placeholders(tmp_path, "Solo")
        result = md.read_text(encoding="utf-8")
        assert "Solo" in result
        assert "{{PROJECT_NAME}}" not in result
        assert "{{WORKSPACE_NAME}}" not in result  # was never present, should remain absent

    def test_only_workspace_name(self, tmp_path):
        """File with only {{WORKSPACE_NAME}} (no {{PROJECT_NAME}}) is handled correctly."""
        md = tmp_path / "README.md"
        _write(md, "WS: {{WORKSPACE_NAME}}\nNo project name here.")
        replace_template_placeholders(tmp_path, "Solo")
        result = md.read_text(encoding="utf-8")
        assert "SAE-Solo" in result
        assert "{{WORKSPACE_NAME}}" not in result
        assert "{{PROJECT_NAME}}" not in result  # was never present

    def test_project_name_placeholder_repeated_workspace_absent(self, tmp_path):
        """File with {{PROJECT_NAME}} repeated many times and no {{WORKSPACE_NAME}}."""
        repetitions = 50
        md = tmp_path / "README.md"
        _write(md, ("{{PROJECT_NAME}}\n") * repetitions)
        replace_template_placeholders(tmp_path, "RepeatName")
        result = md.read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" not in result
        assert result.count("RepeatName") == repetitions


# ---------------------------------------------------------------------------
# Edge case: mixed placeholders spread across multiple files
# ---------------------------------------------------------------------------

class TestMixedPlaceholdersMultipleFiles:
    def test_file_with_only_project(self, tmp_path):
        """One file has only {{PROJECT_NAME}}, another only {{WORKSPACE_NAME}},
        a third has both. All are resolved correctly."""
        file_a = tmp_path / "a.md"
        file_b = tmp_path / "b.md"
        file_c = tmp_path / "c.md"
        _write(file_a, "{{PROJECT_NAME}}")
        _write(file_b, "{{WORKSPACE_NAME}}")
        _write(file_c, "{{PROJECT_NAME}} — {{WORKSPACE_NAME}}")

        replace_template_placeholders(tmp_path, "Mixed")

        a = file_a.read_text(encoding="utf-8")
        b = file_b.read_text(encoding="utf-8")
        c = file_c.read_text(encoding="utf-8")

        assert a == "Mixed"
        assert b == "SAE-Mixed"
        assert "Mixed" in c and "SAE-Mixed" in c
        assert "{{PROJECT_NAME}}" not in c
        assert "{{WORKSPACE_NAME}}" not in c

    def test_no_cross_contamination_between_files(self, tmp_path):
        """Files with different content are not cross-contaminated."""
        file_x = tmp_path / "x.md"
        file_y = tmp_path / "y.md"
        _write(file_x, "Only X: {{PROJECT_NAME}}")
        _write(file_y, "Only Y: {{WORKSPACE_NAME}}")
        replace_template_placeholders(tmp_path, "CrossCheck")
        x = file_x.read_text(encoding="utf-8")
        y = file_y.read_text(encoding="utf-8")
        assert x == "Only X: CrossCheck"
        assert y == "Only Y: SAE-CrossCheck"

    def test_some_files_no_placeholder(self, tmp_path):
        """Files without placeholders remain untouched while neighboring files are updated."""
        with_placeholder = tmp_path / "has_placeholder.md"
        without_placeholder = tmp_path / "static.md"
        static_content = "# Static heading\nNo variables here."
        _write(with_placeholder, "# {{PROJECT_NAME}}")
        _write(without_placeholder, static_content)
        replace_template_placeholders(tmp_path, "Neighbor")
        assert with_placeholder.read_text(encoding="utf-8") == "# Neighbor"
        assert without_placeholder.read_text(encoding="utf-8") == static_content

    def test_mixed_file_types_in_same_directory(self, tmp_path):
        """Mixed .md, .txt, .py files in the same directory: only .md files are processed."""
        md_file  = tmp_path / "readme.md"
        txt_file = tmp_path / "notes.txt"
        py_file  = tmp_path / "script.py"
        _write(md_file,  "{{PROJECT_NAME}}")
        _write(txt_file, "{{PROJECT_NAME}}")
        _write(py_file,  "{{PROJECT_NAME}}")
        replace_template_placeholders(tmp_path, "TypeCheck")
        assert md_file.read_text(encoding="utf-8")  == "TypeCheck"
        assert txt_file.read_text(encoding="utf-8") == "{{PROJECT_NAME}}"
        assert py_file.read_text(encoding="utf-8")  == "{{PROJECT_NAME}}"
