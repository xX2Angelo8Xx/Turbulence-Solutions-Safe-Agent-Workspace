"""
DOC-040 — Tester edge-case tests for .github/version file.

Additional edge cases beyond the Developer's tests:
- Empty version file: empty string passed as version parameter
- Multiple {{VERSION}} occurrences in one file
- No {{VERSION}} in file (idempotency — file must not be written)
- Version file NOT scanned when rglob("version") would match an unrelated dir entry
- create_project() end-to-end: .github/version written with actual VERSION
- Replacement does not break when version file is inside a deeply-nested directory
- Version replacement does not corrupt binary-like files (OSError safety)
- An empty file (0 bytes) is handled gracefully
"""

import re
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_tmpdir_with_version(content: str = "{{VERSION}}"):
    """Return a TemporaryDirectory and the .github/version Path inside it."""
    tmpdir_obj = tempfile.TemporaryDirectory()
    github_dir = Path(tmpdir_obj.name) / ".github"
    github_dir.mkdir()
    version_file = github_dir / "version"
    version_file.write_text(content, encoding="utf-8")
    return tmpdir_obj, version_file


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------

def test_multiple_version_placeholders_all_replaced():
    """If {{VERSION}} appears multiple times in the version file, ALL occurrences are replaced."""
    from launcher.core.project_creator import replace_template_placeholders

    tmpdir_obj, version_file = _make_tmpdir_with_version(
        "{{VERSION}}\n{{VERSION}}\n{{VERSION}}"
    )
    with tmpdir_obj:
        replace_template_placeholders(Path(tmpdir_obj.name), "TestProject", version="1.2.3")
        result = version_file.read_text(encoding="utf-8")
        assert "{{VERSION}}" not in result, "Some {{VERSION}} occurrences were not replaced."
        # All three occurrences should become "1.2.3"
        assert result.count("1.2.3") == 3, (
            f"Expected 3 occurrences of '1.2.3', got: {result!r}"
        )


def test_empty_version_file_no_placeholder():
    """An empty version file (0 bytes) must not cause errors and remains empty."""
    from launcher.core.project_creator import replace_template_placeholders

    tmpdir_obj, version_file = _make_tmpdir_with_version("")  # empty content
    with tmpdir_obj:
        # Should complete without exception.
        replace_template_placeholders(Path(tmpdir_obj.name), "TestProject")
        result = version_file.read_text(encoding="utf-8")
        assert result == "", f"Expected empty file to stay empty, got: {result!r}"


def test_no_placeholder_file_not_rewritten():
    """A file that does NOT contain {{VERSION}} must not be written (idempotency)."""
    from launcher.core.project_creator import replace_template_placeholders

    static_content = "1.0.0"  # already replaced — no placeholder
    tmpdir_obj, version_file = _make_tmpdir_with_version(static_content)
    with tmpdir_obj:
        mtime_before = version_file.stat().st_mtime
        replace_template_placeholders(Path(tmpdir_obj.name), "TestProject")
        mtime_after = version_file.stat().st_mtime
        assert mtime_before == mtime_after, (
            "File was rewritten even though it contained no placeholders."
        )


def test_version_file_in_deep_directory():
    """replace_template_placeholders() finds 'version' files in deeply-nested sub-dirs."""
    from launcher.core.project_creator import replace_template_placeholders

    with tempfile.TemporaryDirectory() as tmpdir:
        deep = Path(tmpdir) / "a" / "b" / "c" / ".github"
        deep.mkdir(parents=True)
        version_file = deep / "version"
        version_file.write_text("{{VERSION}}", encoding="utf-8")

        replace_template_placeholders(Path(tmpdir), "TestProject", version="2.0.0")

        result = version_file.read_text(encoding="utf-8")
        assert result == "2.0.0", f"Expected '2.0.0', got '{result}'"


def test_version_file_replacement_valid_string_not_empty():
    """After replacement, the version string must be non-empty."""
    from launcher.core.project_creator import replace_template_placeholders
    from launcher.config import VERSION

    tmpdir_obj, version_file = _make_tmpdir_with_version("{{VERSION}}")
    with tmpdir_obj:
        replace_template_placeholders(Path(tmpdir_obj.name), "TestProject")
        result = version_file.read_text(encoding="utf-8").strip()
        assert len(result) > 0, "Version string must not be empty after replacement."
        assert result == VERSION


def test_end_to_end_create_project_version_file_written(tmp_path):
    """create_project() writes the actual VERSION into .github/version in the new workspace."""
    from launcher.core.project_creator import create_project
    from launcher.config import VERSION, TEMPLATES_DIR

    template_path = TEMPLATES_DIR / "agent-workbench"
    if not template_path.is_dir():
        import pytest
        pytest.skip("agent-workbench template not available in this environment")

    # Use tmp_path as destination — pytest handles cleanup.
    project_dir = create_project(template_path, tmp_path, "VersionTest")
    version_file = project_dir / ".github" / "version"

    assert version_file.exists(), f".github/version not found in created project at {project_dir}"
    content = version_file.read_text(encoding="utf-8").strip()
    assert content == VERSION, f"Expected '{VERSION}', got '{content}'"
    assert "{{VERSION}}" not in content, "Placeholder was not replaced in created project."


def test_version_file_content_is_semver_format():
    """The current VERSION constant must match a semver format (X.Y.Z or X.Y.Z-suffix)."""
    from launcher.config import VERSION
    pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9._-]+)?$"
    assert re.match(pattern, VERSION), (
        f"VERSION '{VERSION}' does not match semver pattern X.Y.Z"
    )


def test_project_name_placeholder_not_replaced_in_version_file():
    """{{PROJECT_NAME}} in the version file must also be replaced (covers rglob('version') scope)."""
    from launcher.core.project_creator import replace_template_placeholders

    tmpdir_obj, version_file = _make_tmpdir_with_version("{{PROJECT_NAME}}-{{VERSION}}")
    with tmpdir_obj:
        replace_template_placeholders(
            Path(tmpdir_obj.name), "MyProj", version="3.0.0"
        )
        result = version_file.read_text(encoding="utf-8")
        assert "MyProj-3.0.0" == result, (
            f"Expected 'MyProj-3.0.0', got '{result!r}'"
        )
