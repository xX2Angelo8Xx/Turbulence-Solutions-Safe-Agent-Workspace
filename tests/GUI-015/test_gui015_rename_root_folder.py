"""Tests for GUI-015 — Rename Root Folder to TS-SAE-{ProjectName}.

Verifies that create_project() prepends the TS-SAE- prefix to the folder
name and that the duplicate-folder check in _on_create_project() looks for
the prefixed name at the destination.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from launcher.core.project_creator import create_project


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_template(tmp_path: Path) -> Path:
    """Create a minimal template directory with one file."""
    template = tmp_path / "template"
    template.mkdir()
    (template / "README.md").write_text("template readme")
    return template


@pytest.fixture()
def tmp_dest(tmp_path: Path) -> Path:
    """Create a destination directory."""
    dest = tmp_path / "dest"
    dest.mkdir()
    return dest


# ---------------------------------------------------------------------------
# Unit tests — create_project() prefix behaviour
# ---------------------------------------------------------------------------

class TestCreateProjectPrefix:
    def test_creates_ts_sae_prefixed_folder(self, tmp_template: Path, tmp_dest: Path) -> None:
        """Root folder name must be TS-SAE-{folder_name}."""
        result = create_project(tmp_template, tmp_dest, "MatlabDemo")
        assert result.name == "TS-SAE-MatlabDemo"

    def test_returned_path_is_under_destination(self, tmp_template: Path, tmp_dest: Path) -> None:
        """create_project() returns a path inside the destination directory."""
        result = create_project(tmp_template, tmp_dest, "MatlabDemo")
        assert result.parent.resolve() == tmp_dest.resolve()

    def test_folder_physically_created_on_disk(self, tmp_template: Path, tmp_dest: Path) -> None:
        """The TS-SAE- prefixed folder must exist on disk after creation."""
        result = create_project(tmp_template, tmp_dest, "TestProject")
        assert result.is_dir()
        assert (tmp_dest / "TS-SAE-TestProject").is_dir()

    def test_raw_name_folder_not_created(self, tmp_template: Path, tmp_dest: Path) -> None:
        """A folder with only the raw (unprefixed) name must NOT be created."""
        create_project(tmp_template, tmp_dest, "MatlabDemo")
        assert not (tmp_dest / "MatlabDemo").exists()

    def test_template_contents_are_copied(self, tmp_template: Path, tmp_dest: Path) -> None:
        """Template contents appear inside the prefixed project folder."""
        result = create_project(tmp_template, tmp_dest, "Demo")
        assert (result / "README.md").is_file()

    def test_different_folder_names_all_get_prefix(self, tmp_template: Path, tmp_dest: Path) -> None:
        """Every call should individually apply the prefix."""
        names = ["Alpha", "Beta123", "My_Project"]
        for name in names:
            result = create_project(tmp_template, tmp_dest, name)
            assert result.name == f"TS-SAE-{name}", f"Expected TS-SAE-{name}, got {result.name}"

    def test_returned_path_equals_ts_sae_path(self, tmp_template: Path, tmp_dest: Path) -> None:
        """The return value resolves to destination/TS-SAE-{folder_name}."""
        result = create_project(tmp_template, tmp_dest, "Widget")
        expected = (tmp_dest / "TS-SAE-Widget").resolve()
        assert result.resolve() == expected


# ---------------------------------------------------------------------------
# Path-traversal guard still works with the prefix
# ---------------------------------------------------------------------------

class TestCreateProjectTraversalGuard:
    def test_path_traversal_still_rejected(self, tmp_template: Path, tmp_dest: Path) -> None:
        """Path-traversal attempt in folder_name must still raise ValueError.

        Note: with the TS-SAE- prefix, 'TS-SAE-' + '../../escape' creates a path
        where the first '..' only cancels the 'TS-SAE-..' component (back to dest).
        A 3-level traversal '../../../escape' does escape dest and must be blocked.
        """
        with pytest.raises(ValueError, match="path traversal"):
            create_project(tmp_template, tmp_dest, "../../../escape")

    def test_normal_name_is_not_rejected(self, tmp_template: Path, tmp_dest: Path) -> None:
        """A benign folder name must not trigger the traversal guard."""
        result = create_project(tmp_template, tmp_dest, "SafeName")
        assert result.name == "TS-SAE-SafeName"


# ---------------------------------------------------------------------------
# Error handling (pre-existing guards still intact)
# ---------------------------------------------------------------------------

class TestCreateProjectErrors:
    def test_missing_template_raises_value_error(self, tmp_dest: Path) -> None:
        """Non-existent template path raises ValueError."""
        with pytest.raises(ValueError, match="Template path does not exist"):
            create_project(Path("/nonexistent/template"), tmp_dest, "X")

    def test_missing_destination_raises_value_error(self, tmp_template: Path) -> None:
        """Non-existent destination path raises ValueError."""
        with pytest.raises(ValueError, match="Destination path does not exist"):
            create_project(tmp_template, Path("/nonexistent/dest"), "X")

    def test_duplicate_target_raises(self, tmp_template: Path, tmp_dest: Path) -> None:
        """Calling create_project twice with the same name raises an error (shutil)."""
        create_project(tmp_template, tmp_dest, "DoubleCreate")
        with pytest.raises(Exception):
            create_project(tmp_template, tmp_dest, "DoubleCreate")


# ---------------------------------------------------------------------------
# Integration — duplicate folder check uses prefixed name
# ---------------------------------------------------------------------------

class TestDuplicateFolderCheck:
    def test_duplicate_check_uses_ts_sae_prefix(self, tmp_dest: Path) -> None:
        """check_duplicate_folder('TS-SAE-X', dest) returns True if TS-SAE-X exists."""
        from launcher.gui.validation import check_duplicate_folder

        prefixed = tmp_dest / "TS-SAE-Existing"
        prefixed.mkdir()

        # The prefixed name check must find the folder.
        assert check_duplicate_folder("TS-SAE-Existing", str(tmp_dest)) is True

    def test_duplicate_check_raw_name_does_not_collide(self, tmp_dest: Path) -> None:
        """Raw folder name alone should NOT trigger duplicate when only TS-SAE- exists."""
        from launcher.gui.validation import check_duplicate_folder

        prefixed = tmp_dest / "TS-SAE-NoDupe"
        prefixed.mkdir()

        # The unprefixed name doesn't exist, so no collision.
        assert check_duplicate_folder("NoDupe", str(tmp_dest)) is False

    def test_on_create_project_duplicate_guard_uses_prefix(
        self, tmp_template: Path, tmp_dest: Path
    ) -> None:
        """_on_create_project must show an error when TS-SAE-{name} already exists."""
        from unittest.mock import MagicMock, patch

        # Pre-create the prefixed folder so the duplicate check triggers.
        (tmp_dest / "TS-SAE-AlreadyHere").mkdir()

        with (
            patch("launcher.gui.app.TEMPLATES_DIR", tmp_template.parent),
            patch("launcher.gui.app.list_templates", return_value=["template"]),
            patch("launcher.gui.app.is_template_ready", return_value=True),
            patch("launcher.gui.app.check_for_update", return_value=(False, "0.0.0")),
            patch("launcher.gui.app.ctk"),
            patch("sys.platform", "linux"),
        ):
            from launcher.gui.app import App

            app = MagicMock(spec=App)
            app.project_name_entry = MagicMock()
            app.project_name_entry.get.return_value = "AlreadyHere"
            app.project_type_dropdown = MagicMock()
            app.project_type_dropdown.get.return_value = "Template"
            app.destination_entry = MagicMock()
            app.destination_entry.get.return_value = str(tmp_dest)
            app.project_name_error_label = MagicMock()
            app.destination_error_label = MagicMock()
            app._coming_soon_options = set()

            App._on_create_project(app)

            # The error label should have been set (duplicate detected).
            app.project_name_error_label.configure.assert_called()
            call_kwargs = app.project_name_error_label.configure.call_args
            error_text = call_kwargs[1].get("text") or call_kwargs[0][0]
            assert "TS-SAE-AlreadyHere" in error_text
