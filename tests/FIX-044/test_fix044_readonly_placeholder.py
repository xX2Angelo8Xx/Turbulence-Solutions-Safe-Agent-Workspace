"""Tests for FIX-044: PermissionError on read-only template .md with placeholders.

Regression tests verifying that replace_template_placeholders() silently skips
read-only .md files instead of raising PermissionError (BUG-052).
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from launcher.core.project_creator import replace_template_placeholders


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_readonly(path: Path) -> None:
    """Remove write permission from a file (cross-platform)."""
    current = stat.S_IMODE(os.stat(path).st_mode)
    os.chmod(path, current & ~stat.S_IWRITE & ~stat.S_IWGRP & ~stat.S_IWOTH)


def _restore_writable(path: Path) -> None:
    """Restore write permission so tmp_path cleanup succeeds."""
    current = stat.S_IMODE(os.stat(path).st_mode)
    os.chmod(path, current | stat.S_IWRITE)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestReadOnlyPlaceholder:

    def test_readonly_md_with_placeholder_does_not_raise(self, tmp_path):
        """BUG-052 regression: read-only .md file with placeholders must not
        raise PermissionError (or any exception)."""
        md = tmp_path / "README.md"
        _write(md, "# {{PROJECT_NAME}}\nWelcome to {{WORKSPACE_NAME}}.")
        _make_readonly(md)
        try:
            # Must not raise
            replace_template_placeholders(tmp_path, "TestProject")
        except PermissionError:
            pytest.fail(
                "replace_template_placeholders raised PermissionError on a "
                "read-only .md file — BUG-052 regression"
            )
        finally:
            _restore_writable(md)

    def test_readonly_md_with_placeholder_is_skipped(self, tmp_path):
        """Read-only .md file with placeholders retains original content after
        the call (write is silently skipped)."""
        original_content = "# {{PROJECT_NAME}}\nWelcome to {{WORKSPACE_NAME}}."
        md = tmp_path / "README.md"
        _write(md, original_content)
        _make_readonly(md)
        try:
            replace_template_placeholders(tmp_path, "TestProject")
            result = md.read_text(encoding="utf-8")
            assert result == original_content, (
                "Read-only file content should be unchanged after skipped write"
            )
        finally:
            _restore_writable(md)

    def test_writable_md_with_placeholder_is_replaced(self, tmp_path):
        """Writable .md file with placeholders is still correctly processed."""
        md = tmp_path / "docs.md"
        _write(md, "Project: {{PROJECT_NAME}}, Workspace: {{WORKSPACE_NAME}}")
        replace_template_placeholders(tmp_path, "MyDemo")
        result = md.read_text(encoding="utf-8")
        assert "MyDemo" in result
        assert "TS-SAE-MyDemo" in result
        assert "{{PROJECT_NAME}}" not in result
        assert "{{WORKSPACE_NAME}}" not in result

    def test_readonly_md_without_placeholder_is_unaffected(self, tmp_path):
        """Read-only .md without any placeholder tokens is left untouched;
        no exception is raised."""
        content = "# Static README\nNo placeholders here."
        md = tmp_path / "STATIC.md"
        _write(md, content)
        _make_readonly(md)
        try:
            # Must not raise; file never needs writing (no placeholder found)
            replace_template_placeholders(tmp_path, "AnyName")
            result = md.read_text(encoding="utf-8")
            assert result == content
        finally:
            _restore_writable(md)

    def test_mixed_tree_readonly_and_writable(self, tmp_path):
        """In a tree with both read-only and writable .md files, writable files
        are updated and read-only files are silently skipped without exception."""
        readonly_md = tmp_path / "readonly.md"
        writable_md = tmp_path / "writable.md"
        readonly_content = "# {{PROJECT_NAME}} read-only"
        writable_content = "# {{PROJECT_NAME}} writable"

        _write(readonly_md, readonly_content)
        _write(writable_md, writable_content)
        _make_readonly(readonly_md)

        try:
            replace_template_placeholders(tmp_path, "Alpha")

            # Writable file should be updated
            assert "Alpha" in writable_md.read_text(encoding="utf-8")
            assert "{{PROJECT_NAME}}" not in writable_md.read_text(encoding="utf-8")

            # Read-only file should be unchanged
            assert readonly_md.read_text(encoding="utf-8") == readonly_content
        finally:
            _restore_writable(readonly_md)

    def test_oserror_is_caught_not_only_permission_error(self, tmp_path):
        """The except clause catches OSError (parent of PermissionError),
        verifying that any OS-level write failure is silently skipped."""
        # We test this indirectly: making the file read-only triggers an OSError
        # on Windows (PermissionError is a subclass of OSError). The test
        # verifies no exception escapes replace_template_placeholders.
        md = tmp_path / "test.md"
        _write(md, "{{PROJECT_NAME}}")
        _make_readonly(md)
        try:
            replace_template_placeholders(tmp_path, "Test")  # must not propagate
        except OSError as exc:
            pytest.fail(f"OSError escaped replace_template_placeholders: {exc}")
        finally:
            _restore_writable(md)
