"""Tests for GUI-005: Project Creation Logic.

Tests cover the _on_create_project() handler in App, verifying:
- Inline validation errors are shown for invalid inputs.
- Previous errors are cleared on each invocation.
- create_project is called with correct arguments on the happy path.
- Success and error dialogs are shown appropriately.

All App tests run headlessly by replacing `customtkinter` with a MagicMock
in sys.modules before any launcher.gui module is imported.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# ---------------------------------------------------------------------------
# customtkinter is already mocked by tests/conftest.py — reuse that mock.
# ---------------------------------------------------------------------------
_CTK_MOCK = sys.modules["customtkinter"]

from launcher.gui.app import App  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app(
    project_name: str = "my-project",
    template_display: str = "Coding",
    destination: str = "",
) -> App:
    """Return a fresh App instance with independent widget mocks pre-configured.

    Because customtkinter is a MagicMock, all CTkEntry() calls return the same
    mock instance.  We replace each widget attribute with a dedicated MagicMock
    to ensure .get() return values do not bleed between widgets.
    """
    _CTK_MOCK.reset_mock()
    app = App()
    # Replace shared mock widgets with independent instances.
    app.project_name_entry = MagicMock()
    app.project_name_entry.get.return_value = project_name
    app.project_type_dropdown = MagicMock()
    app.project_type_dropdown.get.return_value = template_display
    app.destination_entry = MagicMock()
    app.destination_entry.get.return_value = destination
    app.project_name_error_label = MagicMock()
    app.destination_error_label = MagicMock()
    return app


# ---------------------------------------------------------------------------
# Tests: inline error labels cleared on each call
# ---------------------------------------------------------------------------

class TestOnCreateProjectClearsPreviousErrors:
    def test_name_error_label_cleared_at_start(self, tmp_path):
        app = _make_app(project_name="valid", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=tmp_path / "valid"), \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()
        app.project_name_error_label.configure.assert_any_call(text="")

    def test_destination_error_label_cleared_at_start(self, tmp_path):
        app = _make_app(project_name="valid", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=tmp_path / "valid"), \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()
        app.destination_error_label.configure.assert_any_call(text="")


# ---------------------------------------------------------------------------
# Tests: inline validation — project name
# ---------------------------------------------------------------------------

class TestOnCreateProjectNameValidation:
    def test_empty_name_shows_inline_error(self, tmp_path):
        app = _make_app(project_name="", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(False, "Project name cannot be empty.")):
            app._on_create_project()
        app.project_name_error_label.configure.assert_any_call(text="Project name cannot be empty.")

    def test_invalid_name_shows_inline_error(self, tmp_path):
        app = _make_app(project_name="bad/name", destination=str(tmp_path))
        error_msg = "Name contains invalid characters."
        with patch("launcher.gui.app.validate_folder_name", return_value=(False, error_msg)):
            app._on_create_project()
        app.project_name_error_label.configure.assert_any_call(text=error_msg)

    def test_invalid_name_does_not_call_create_project(self, tmp_path):
        app = _make_app(project_name="", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(False, "empty")), \
             patch("launcher.gui.app.create_project") as mock_create:
            app._on_create_project()
        mock_create.assert_not_called()

    def test_invalid_name_does_not_show_destination_error(self, tmp_path):
        app = _make_app(project_name="", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(False, "empty")):
            app._on_create_project()
        # Only the clear call (text="") should have been made on destination_error_label.
        app.destination_error_label.configure.assert_called_once_with(text="")


# ---------------------------------------------------------------------------
# Tests: inline validation — destination
# ---------------------------------------------------------------------------

class TestOnCreateProjectDestinationValidation:
    def test_bad_destination_shows_inline_error(self):
        app = _make_app(project_name="valid", destination="/nonexistent/path")
        error_msg = "Destination path does not exist."
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(False, error_msg)):
            app._on_create_project()
        app.destination_error_label.configure.assert_any_call(text=error_msg)

    def test_bad_destination_does_not_call_create_project(self):
        app = _make_app(project_name="valid", destination="")
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(False, "empty")), \
             patch("launcher.gui.app.create_project") as mock_create:
            app._on_create_project()
        mock_create.assert_not_called()

    def test_empty_destination_shows_inline_error(self):
        app = _make_app(project_name="valid", destination="")
        error_msg = "Destination path cannot be empty."
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(False, error_msg)):
            app._on_create_project()
        app.destination_error_label.configure.assert_any_call(text=error_msg)


# ---------------------------------------------------------------------------
# Tests: duplicate folder detection
# ---------------------------------------------------------------------------

class TestOnCreateProjectDuplicateFolder:
    def test_duplicate_folder_shows_name_inline_error(self, tmp_path):
        app = _make_app(project_name="existing", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=True):
            app._on_create_project()
        configure_calls = app.project_name_error_label.configure.call_args_list
        error_texts = [c.kwargs.get("text", "") or (c.args[0] if c.args else "") for c in configure_calls]
        assert any("already exists" in t for t in error_texts)

    def test_duplicate_folder_does_not_call_create_project(self, tmp_path):
        app = _make_app(project_name="existing", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=True), \
             patch("launcher.gui.app.create_project") as mock_create:
            app._on_create_project()
        mock_create.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: unknown template
# ---------------------------------------------------------------------------

class TestOnCreateProjectUnknownTemplate:
    def test_unknown_template_shows_error_dialog(self, tmp_path):
        app = _make_app(project_name="proj", template_display="Nonexistent", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()
        mock_mb.showerror.assert_called_once()
        args = mock_mb.showerror.call_args[0]
        assert "Template Not Found" in args[0] or "Template Not Found" in str(args)

    def test_unknown_template_does_not_call_create_project(self, tmp_path):
        app = _make_app(project_name="proj", template_display="Ghost", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project") as mock_create, \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()
        mock_create.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: happy path — successful creation
# ---------------------------------------------------------------------------

class TestOnCreateProjectSuccess:
    def test_create_project_called_with_correct_args(self, tmp_path):
        from launcher.config import TEMPLATES_DIR
        app = _make_app(project_name="my-project", template_display="Coding", destination=str(tmp_path))
        expected_template = TEMPLATES_DIR / "coding"
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=tmp_path / "my-project") as mock_create, \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()
        # GUI-020: create_project now receives counter_enabled and counter_threshold kwargs.
        args, kwargs = mock_create.call_args
        assert args == (expected_template, Path(str(tmp_path)), "my-project")
        assert "counter_enabled" in kwargs
        assert "counter_threshold" in kwargs

    def test_success_shows_info_dialog(self, tmp_path):
        app = _make_app(project_name="my-project", template_display="Coding", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=tmp_path / "my-project"), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()
        mock_mb.showinfo.assert_called_once()

    def test_success_info_dialog_mentions_project_name(self, tmp_path):
        app = _make_app(project_name="awesome-app", template_display="Coding", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=tmp_path / "awesome-app"), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()
        call_args = mock_mb.showinfo.call_args
        full_text = " ".join(str(a) for a in call_args[0])
        assert "awesome-app" in full_text

    def test_success_does_not_show_error_dialog(self, tmp_path):
        app = _make_app(project_name="my-project", template_display="Coding", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=tmp_path / "my-project"), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()
        mock_mb.showerror.assert_not_called()

    def test_success_no_inline_errors_set(self, tmp_path):
        app = _make_app(project_name="my-project", template_display="Coding", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=tmp_path / "my-project"), \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()
        # Only the clear calls (text="") should have been made
        for lbl in (app.project_name_error_label, app.destination_error_label):
            texts = [
                c.kwargs.get("text", "") or (c.args[0] if c.args else "")
                for c in lbl.configure.call_args_list
            ]
            assert all(t == "" for t in texts)

    def test_multiword_template_reverse_mapped_correctly(self, tmp_path):
        """'Creative Marketing' display name must map to 'creative-marketing' dir."""
        from launcher.config import TEMPLATES_DIR
        app = _make_app(
            project_name="proj",
            template_display="Creative Marketing",
            destination=str(tmp_path),
        )
        expected_template = TEMPLATES_DIR / "creative-marketing"
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding", "creative-marketing"]), \
             patch("launcher.gui.app.create_project", return_value=tmp_path / "proj") as mock_create, \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()
        # GUI-020: create_project now receives counter_enabled and counter_threshold kwargs.
        args, kwargs = mock_create.call_args
        assert args == (expected_template, Path(str(tmp_path)), "proj")
        assert "counter_enabled" in kwargs
        assert "counter_threshold" in kwargs


# ---------------------------------------------------------------------------
# Tests: create_project raises an exception
# ---------------------------------------------------------------------------

class TestOnCreateProjectCreationError:
    def test_create_project_exception_shows_error_dialog(self, tmp_path):
        app = _make_app(project_name="proj", template_display="Coding", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", side_effect=ValueError("disk full")), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()
        mock_mb.showerror.assert_called_once()

    def test_create_project_exception_message_passed_to_dialog(self, tmp_path):
        app = _make_app(project_name="proj", template_display="Coding", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", side_effect=ValueError("disk full")), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()
        error_args = mock_mb.showerror.call_args[0]
        assert "disk full" in " ".join(str(a) for a in error_args)

    def test_create_project_exception_does_not_show_info_dialog(self, tmp_path):
        app = _make_app(project_name="proj", template_display="Coding", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", side_effect=OSError("permission denied")), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()
        mock_mb.showinfo.assert_not_called()

    def test_create_project_oserror_shows_error_dialog(self, tmp_path):
        app = _make_app(project_name="proj", template_display="Coding", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", side_effect=OSError("no space")), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()
        mock_mb.showerror.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: imports and module structure
# ---------------------------------------------------------------------------

class TestAppModuleStructure:
    def test_create_project_imported_in_app(self):
        import launcher.gui.app as app_module
        assert hasattr(app_module, "create_project")

    def test_messagebox_imported_in_app(self):
        import launcher.gui.app as app_module
        assert hasattr(app_module, "messagebox")

    def test_path_imported_in_app(self):
        import launcher.gui.app as app_module
        assert hasattr(app_module, "Path")

    def test_on_create_project_is_callable(self):
        assert callable(getattr(App, "_on_create_project", None))


# ---------------------------------------------------------------------------
# Tester-added edge cases — core create_project() unit tests (missed by Dev)
# ---------------------------------------------------------------------------

class TestCreateProjectCoreFunction:
    """Unit tests for launcher.core.project_creator.create_project().

    The Developer only tested the handler with a mocked create_project.
    These tests exercise the real function against an actual filesystem.
    """

    def test_returns_correct_target_path(self, tmp_path):
        from launcher.core.project_creator import create_project
        template = tmp_path / "tmpl"
        template.mkdir()
        (template / "file.txt").write_text("hello")
        dest = tmp_path / "dest"
        dest.mkdir()
        result = create_project(template, dest, "my-project")
        assert result == dest / "TS-SAE-my-project"

    def test_files_are_actually_copied(self, tmp_path):
        from launcher.core.project_creator import create_project
        template = tmp_path / "tmpl"
        template.mkdir()
        (template / "README.md").write_text("readme content")
        (template / "sub").mkdir()
        (template / "sub" / "nested.py").write_text("# code")
        dest = tmp_path / "dest"
        dest.mkdir()
        result = create_project(template, dest, "proj")
        assert (result / "README.md").read_text() == "readme content"
        assert (result / "sub" / "nested.py").read_text() == "# code"

    def test_nonexistent_template_raises_valueerror(self, tmp_path):
        from launcher.core.project_creator import create_project
        dest = tmp_path / "dest"
        dest.mkdir()
        with pytest.raises(ValueError, match="Template path does not exist"):
            create_project(tmp_path / "nonexistent", dest, "proj")

    def test_template_is_file_not_dir_raises_valueerror(self, tmp_path):
        from launcher.core.project_creator import create_project
        template_file = tmp_path / "tmpl.txt"
        template_file.write_text("not a dir")
        dest = tmp_path / "dest"
        dest.mkdir()
        with pytest.raises(ValueError, match="Template path does not exist or is not a directory"):
            create_project(template_file, dest, "proj")

    def test_nonexistent_destination_raises_valueerror(self, tmp_path):
        from launcher.core.project_creator import create_project
        template = tmp_path / "tmpl"
        template.mkdir()
        with pytest.raises(ValueError, match="Destination path does not exist"):
            create_project(template, tmp_path / "nonexistent_dest", "proj")

    def test_path_traversal_in_folder_name_raises_valueerror(self, tmp_path):
        from launcher.core.project_creator import create_project
        template = tmp_path / "tmpl"
        template.mkdir()
        dest = tmp_path / "dest"
        dest.mkdir()
        # With the TS-SAE- prefix, 3 levels are needed to escape dest.
        with pytest.raises(ValueError, match="path traversal"):
            create_project(template, dest, "../../../etc")

    def test_path_traversal_dotdot_slash_raises_valueerror(self, tmp_path):
        from launcher.core.project_creator import create_project
        template = tmp_path / "tmpl"
        template.mkdir()
        dest = tmp_path / "dest"
        dest.mkdir()
        # With the TS-SAE- prefix, 3 levels are needed to escape dest.
        with pytest.raises(ValueError, match="path traversal"):
            create_project(template, dest, "../../../sibling")

    def test_existing_target_directory_raises_error(self, tmp_path):
        """shutil.copytree raises FileExistsError when target already exists."""
        from launcher.core.project_creator import create_project
        import shutil
        template = tmp_path / "tmpl"
        template.mkdir()
        (template / "a.txt").write_text("x")
        dest = tmp_path / "dest"
        dest.mkdir()
        (dest / "TS-SAE-proj").mkdir()  # pre-create target → copytree fails
        with pytest.raises(Exception):
            create_project(template, dest, "proj")

    def test_created_directory_is_relative_to_destination(self, tmp_path):
        """result.is_relative_to(destination) must hold."""
        from launcher.core.project_creator import create_project
        template = tmp_path / "tmpl"
        template.mkdir()
        dest = tmp_path / "dest"
        dest.mkdir()
        result = create_project(template, dest, "project")
        assert result.is_relative_to(dest)


# ---------------------------------------------------------------------------
# Tester-added edge cases — handler edge cases
# ---------------------------------------------------------------------------

class TestOnCreateProjectHandlerEdgeCases:
    def test_generic_runtime_error_shows_error_dialog(self, tmp_path):
        """Any Exception subclass (not just ValueError/OSError) triggers showerror."""
        app = _make_app(project_name="proj", template_display="Coding", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", side_effect=RuntimeError("unexpected")), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()
        mock_mb.showerror.assert_called_once()

    def test_project_name_whitespace_stripped_before_use(self, tmp_path):
        """Leading/trailing whitespace is stripped from the project name entry."""
        app = _make_app(project_name="  my-project  ", destination=str(tmp_path))
        captured_args = {}
        def capture_create(*args, **kwargs):
            captured_args["folder_name"] = args[2]
            return tmp_path / args[2]
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", side_effect=capture_create), \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()
        assert captured_args.get("folder_name") == "my-project"

    def test_empty_template_list_shows_error(self, tmp_path):
        """When list_templates returns [], no template can be matched → showerror."""
        app = _make_app(project_name="proj", template_display="Coding", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=[]), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()
        mock_mb.showerror.assert_called_once()

    def test_success_info_dialog_includes_created_path(self, tmp_path):
        """Success dialog must include the created path for the user to see."""
        created = tmp_path / "proj"
        app = _make_app(project_name="proj", template_display="Coding", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=created), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()
        call_args = mock_mb.showinfo.call_args
        full_text = " ".join(str(a) for a in call_args[0])
        assert str(created) in full_text

    def test_destination_whitespace_stripped_before_use(self, tmp_path):
        """Leading/trailing whitespace in destination entry is stripped."""
        app = _make_app(project_name="proj", destination=f"  {str(tmp_path)}  ")
        captured_dest = {}
        def capture_create(*args, **kwargs):
            captured_dest["dest"] = args[1]
            return args[1] / args[2]
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", side_effect=capture_create), \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()
        assert str(captured_dest.get("dest")) == str(tmp_path)

    def test_create_project_exception_does_not_show_success(self, tmp_path):
        """Permission denied error must not show a success dialog."""
        app = _make_app(project_name="proj", template_display="Coding", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", side_effect=PermissionError("denied")), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()
        mock_mb.showinfo.assert_not_called()
        mock_mb.showerror.assert_called_once()
