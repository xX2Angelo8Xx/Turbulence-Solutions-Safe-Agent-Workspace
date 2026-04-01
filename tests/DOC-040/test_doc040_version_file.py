"""
DOC-040 — Tests for .github/version file in agent-workbench template.

Verifies:
- The template file exists and contains {{VERSION}} placeholder.
- replace_template_placeholders() replaces {{VERSION}} with the actual version string.
- After replacement the file contains a semver string, not the placeholder.
- {{VERSION}} is also replaced in .md files.
"""

import os
import re
import shutil
import tempfile
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

TEMPLATE_VERSION_FILE = os.path.join(
    REPO_ROOT,
    "templates",
    "agent-workbench",
    ".github",
    "version",
)


def test_agentworkbench_version_file_exists():
    """templates/agent-workbench/.github/version must exist."""
    assert os.path.isfile(TEMPLATE_VERSION_FILE), (
        f"Expected version file at {TEMPLATE_VERSION_FILE}"
    )


def test_agentworkbench_version_file_contains_placeholder():
    """templates/agent-workbench/.github/version must contain {{VERSION}}."""
    with open(TEMPLATE_VERSION_FILE, encoding="utf-8") as fh:
        content = fh.read()
    assert "{{VERSION}}" in content, (
        "Expected {{VERSION}} placeholder in templates/agent-workbench/.github/version"
    )


def test_replace_placeholders_version_replaced():
    """After replace_template_placeholders(), .github/version contains a semver version string."""
    from launcher.core.project_creator import replace_template_placeholders
    from launcher.config import VERSION

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a minimal project tree that mimics what create_project produces.
        github_dir = Path(tmpdir) / ".github"
        github_dir.mkdir()
        version_file = github_dir / "version"
        version_file.write_text("{{VERSION}}", encoding="utf-8")

        replace_template_placeholders(Path(tmpdir), "TestProject")

        result = version_file.read_text(encoding="utf-8")
        assert result == VERSION, (
            f"Expected version file to contain '{VERSION}', got '{result}'"
        )


def test_replace_placeholders_version_not_placeholder():
    """After replace_template_placeholders(), {{VERSION}} must NOT remain in .github/version."""
    from launcher.core.project_creator import replace_template_placeholders

    with tempfile.TemporaryDirectory() as tmpdir:
        github_dir = Path(tmpdir) / ".github"
        github_dir.mkdir()
        version_file = github_dir / "version"
        version_file.write_text("{{VERSION}}", encoding="utf-8")

        replace_template_placeholders(Path(tmpdir), "TestProject")

        result = version_file.read_text(encoding="utf-8")
        assert "{{VERSION}}" not in result, (
            f"{{VERSION}} placeholder was not replaced; file still contains: {result!r}"
        )


def test_replace_placeholders_version_is_semver():
    """After replacement, .github/version must match a semver-like pattern (e.g. 3.3.0)."""
    from launcher.core.project_creator import replace_template_placeholders

    with tempfile.TemporaryDirectory() as tmpdir:
        github_dir = Path(tmpdir) / ".github"
        github_dir.mkdir()
        version_file = github_dir / "version"
        version_file.write_text("{{VERSION}}", encoding="utf-8")

        replace_template_placeholders(Path(tmpdir), "TestProject")

        result = version_file.read_text(encoding="utf-8").strip()
        assert re.match(r"^\d+\.\d+\.\d+", result), (
            f"Expected semver-like version string, got '{result}'"
        )


def test_replace_placeholders_md_version_replaced():
    """{{VERSION}} in .md files is also replaced by replace_template_placeholders()."""
    from launcher.core.project_creator import replace_template_placeholders
    from launcher.config import VERSION

    with tempfile.TemporaryDirectory() as tmpdir:
        md_file = Path(tmpdir) / "README.md"
        md_file.write_text("Launcher version: {{VERSION}}", encoding="utf-8")
        # Also add a dummy .github/version to avoid unintended failures.
        github_dir = Path(tmpdir) / ".github"
        github_dir.mkdir()
        (github_dir / "version").write_text("{{VERSION}}", encoding="utf-8")

        replace_template_placeholders(Path(tmpdir), "TestProject")

        result = md_file.read_text(encoding="utf-8")
        assert "{{VERSION}}" not in result, (
            "{{VERSION}} was not replaced in README.md"
        )
        assert VERSION in result, (
            f"Expected VERSION '{VERSION}' to appear in README.md after replacement"
        )


def test_replace_placeholders_custom_version():
    """replace_template_placeholders() accepts a custom version parameter."""
    from launcher.core.project_creator import replace_template_placeholders

    with tempfile.TemporaryDirectory() as tmpdir:
        github_dir = Path(tmpdir) / ".github"
        github_dir.mkdir()
        version_file = github_dir / "version"
        version_file.write_text("{{VERSION}}", encoding="utf-8")

        replace_template_placeholders(Path(tmpdir), "TestProject", version="9.9.9")

        result = version_file.read_text(encoding="utf-8")
        assert result == "9.9.9", (
            f"Expected '9.9.9', got '{result}'"
        )


def test_replace_placeholders_all_tokens():
    """All three placeholders are replaced in a single file."""
    from launcher.core.project_creator import replace_template_placeholders
    from launcher.config import VERSION

    with tempfile.TemporaryDirectory() as tmpdir:
        md_file = Path(tmpdir) / "README.md"
        md_file.write_text(
            "Project: {{PROJECT_NAME}}, Workspace: {{WORKSPACE_NAME}}, Version: {{VERSION}}",
            encoding="utf-8",
        )

        replace_template_placeholders(Path(tmpdir), "Demo")

        result = md_file.read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" not in result
        assert "{{WORKSPACE_NAME}}" not in result
        assert "{{VERSION}}" not in result
        assert "Demo" in result
        assert "SAE-Demo" in result
        assert VERSION in result
