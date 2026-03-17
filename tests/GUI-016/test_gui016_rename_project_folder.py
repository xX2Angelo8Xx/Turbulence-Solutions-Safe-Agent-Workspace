"""Tests for GUI-016 — Rename Internal Project Folder to User's Name.

Verifies that create_project() renames the copied "Project/" subfolder
to the user's project name after shutil.copytree().
"""

from __future__ import annotations

from pathlib import Path

import pytest

from launcher.core.project_creator import create_project


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_template_with_project(tmp_path: Path) -> Path:
    """Template directory that contains a 'Project/' subfolder (standard layout)."""
    template = tmp_path / "template"
    template.mkdir()
    (template / "README.md").write_text("template readme")
    project_dir = template / "Project"
    project_dir.mkdir()
    (project_dir / "app.py").write_text("# placeholder")
    return template


@pytest.fixture()
def tmp_template_without_project(tmp_path: Path) -> Path:
    """Template directory that does NOT contain a 'Project/' subfolder."""
    template = tmp_path / "template_no_project"
    template.mkdir()
    (template / "README.md").write_text("template readme")
    return template


@pytest.fixture()
def tmp_dest(tmp_path: Path) -> Path:
    """Destination directory."""
    dest = tmp_path / "dest"
    dest.mkdir()
    return dest


# ---------------------------------------------------------------------------
# Unit tests — rename behaviour
# ---------------------------------------------------------------------------

class TestRenameProjectFolder:
    def test_project_folder_renamed_to_user_name(
        self, tmp_template_with_project: Path, tmp_dest: Path
    ) -> None:
        """The 'Project/' subfolder must be renamed to the user's project name."""
        result = create_project(tmp_template_with_project, tmp_dest, "MatlabDemo")
        assert (result / "MatlabDemo").is_dir()

    def test_original_project_folder_no_longer_exists(
        self, tmp_template_with_project: Path, tmp_dest: Path
    ) -> None:
        """After renaming, 'Project/' must not exist inside the workspace."""
        result = create_project(tmp_template_with_project, tmp_dest, "MatlabDemo")
        assert not (result / "Project").exists()

    def test_renamed_folder_contents_preserved(
        self, tmp_template_with_project: Path, tmp_dest: Path
    ) -> None:
        """Files inside 'Project/' must still exist under the renamed folder."""
        result = create_project(tmp_template_with_project, tmp_dest, "MatlabDemo")
        assert (result / "MatlabDemo" / "app.py").is_file()

    def test_root_folder_still_ts_sae_prefixed(
        self, tmp_template_with_project: Path, tmp_dest: Path
    ) -> None:
        """Root folder must remain TS-SAE-{name}; only the internal folder is renamed."""
        result = create_project(tmp_template_with_project, tmp_dest, "MyProject")
        assert result.name == "TS-SAE-MyProject"

    def test_no_project_folder_does_not_raise(
        self, tmp_template_without_project: Path, tmp_dest: Path
    ) -> None:
        """If no 'Project/' subfolder exists, create_project() must not raise."""
        result = create_project(tmp_template_without_project, tmp_dest, "NoProjectDir")
        assert result.is_dir()

    def test_different_project_name(
        self, tmp_template_with_project: Path, tmp_dest: Path
    ) -> None:
        """Rename works with a variety of valid project names."""
        result = create_project(tmp_template_with_project, tmp_dest, "Alpha123")
        assert (result / "Alpha123").is_dir()
        assert not (result / "Project").exists()

    def test_project_name_with_spaces(
        self, tmp_template_with_project: Path, tmp_dest: Path
    ) -> None:
        """Project names containing spaces are renamed correctly."""
        result = create_project(tmp_template_with_project, tmp_dest, "My Project")
        assert (result / "My Project").is_dir()
        assert not (result / "Project").exists()

    def test_rename_does_not_collide_when_project_name_equals_project(
        self, tmp_dest: Path, tmp_path: Path
    ) -> None:
        """If user names the project 'Project', the subfolder is effectively no-op but still valid."""
        # When folder_name == "Project", 'Project/' already has the right name;
        # the guard (not renamed_project.exists()) prevents a rename onto itself.
        template = tmp_path / "template_collision"
        template.mkdir()
        (template / "README.md").write_text("readme")
        project_dir = template / "Project"
        project_dir.mkdir()
        (project_dir / "main.py").write_text("# main")

        result = create_project(template, tmp_dest, "Project")
        # The folder must still be "Project" because rename target == source
        assert (result / "Project").is_dir()
        assert (result / "Project" / "main.py").is_file()
