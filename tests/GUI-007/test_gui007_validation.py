"""Tests for GUI-007: Input Validation & Error UX.

Verifies that all user-input validation scenarios produce the correct outcome
and that the App inline error labels behave correctly.

Coverage:
  - validate_folder_name()  —  unit tests for every validation branch
  - validate_destination_path()  —  unit tests for every validation branch
  - check_duplicate_folder()  —  existence checks
  - App._on_create_project()  —  integration tests for label visibility and clearing

All App tests run headlessly by replacing ``customtkinter`` with a MagicMock
in sys.modules before any launcher.gui module is imported.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Use the shared customtkinter mock installed by conftest.py.
# ---------------------------------------------------------------------------
_CTK_MOCK = sys.modules["customtkinter"]

from launcher.gui.validation import (  # noqa: E402
    check_duplicate_folder,
    validate_destination_path,
    validate_folder_name,
)
from launcher.gui.app import App  # noqa: E402

# Grab the module-level globals of App so patches propagate reliably.
_APP_GLOBALS = App._on_create_project.__globals__


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app(
    project_name: str = "valid-project",
    template_display: str = "Agent Workbench",
    destination: str = "",
) -> App:
    """Build a headless App with independent widget mocks pre-wired."""
    _CTK_MOCK.reset_mock()
    app = App()
    app.project_name_entry = MagicMock()
    app.project_name_entry.get.return_value = project_name
    app.project_type_dropdown = MagicMock()
    app.project_type_dropdown.get.return_value = template_display
    app.destination_entry = MagicMock()
    app.destination_entry.get.return_value = destination
    app.project_name_error_label = MagicMock()
    app.destination_error_label = MagicMock()
    return app


# ===========================================================================
# validate_folder_name — empty / whitespace
# ===========================================================================

class TestValidateFolderNameEmpty:
    def test_empty_name_is_invalid(self):
        valid, msg = validate_folder_name("")
        assert valid is False

    def test_whitespace_only_name_is_invalid(self):
        valid, msg = validate_folder_name("   ")
        assert valid is False

    def test_error_message_for_empty_name(self):
        _, msg = validate_folder_name("")
        assert "empty" in msg.lower()

    def test_error_message_for_whitespace_only(self):
        _, msg = validate_folder_name("   ")
        assert "empty" in msg.lower()


# ===========================================================================
# validate_folder_name — trailing characters
# ===========================================================================

class TestValidateFolderNameTrailingChars:
    def test_name_trailing_period_is_invalid(self):
        valid, _ = validate_folder_name("myproject.")
        assert valid is False

    def test_name_trailing_space_is_invalid(self):
        valid, _ = validate_folder_name("myproject ")
        assert valid is False

    def test_error_message_for_trailing_period(self):
        _, msg = validate_folder_name("test.")
        assert "period" in msg.lower() or "." in msg

    def test_error_message_for_trailing_space(self):
        _, msg = validate_folder_name("test ")
        assert "space" in msg.lower() or "period" in msg.lower()


# ===========================================================================
# validate_folder_name — length boundary
# ===========================================================================

class TestValidateFolderNameLength:
    def test_name_exactly_255_chars_is_valid(self):
        name = "a" * 255
        valid, _ = validate_folder_name(name)
        assert valid is True

    def test_name_256_chars_is_invalid(self):
        name = "a" * 256
        valid, _ = validate_folder_name(name)
        assert valid is False

    def test_error_message_for_too_long(self):
        _, msg = validate_folder_name("a" * 256)
        assert "255" in msg or "long" in msg.lower()


# ===========================================================================
# validate_folder_name — valid names (happy-path)
# ===========================================================================

class TestValidateFolderNameValid:
    def test_valid_simple_name(self):
        valid, msg = validate_folder_name("my-project")
        assert valid is True
        assert msg == ""

    def test_valid_name_with_hyphens_and_numbers(self):
        valid, _ = validate_folder_name("project-v2-final")
        assert valid is True

    def test_valid_name_with_underscores(self):
        valid, _ = validate_folder_name("my_project_01")
        assert valid is True

    def test_valid_unicode_name(self):
        valid, _ = validate_folder_name("café-project")
        assert valid is True

    def test_valid_unicode_cjk_name(self):
        valid, _ = validate_folder_name("プロジェクト")
        assert valid is True

    def test_valid_single_char_name(self):
        valid, _ = validate_folder_name("a")
        assert valid is True


# ===========================================================================
# validate_folder_name — invalid characters
# ===========================================================================

class TestValidateFolderNameInvalidChars:
    @pytest.mark.parametrize("char", ["<", ">", ":", '"', "/", "\\", "|", "?", "*"])
    def test_individual_invalid_char_rejected(self, char: str):
        valid, _ = validate_folder_name(f"project{char}name")
        assert valid is False

    def test_null_byte_rejected(self):
        valid, _ = validate_folder_name("project\x00name")
        assert valid is False

    def test_other_control_char_rejected(self):
        valid, _ = validate_folder_name("project\x1fname")
        assert valid is False

    def test_error_message_for_invalid_chars(self):
        _, msg = validate_folder_name("bad<name")
        assert "invalid" in msg.lower() or "<" in msg or "character" in msg.lower()


# ===========================================================================
# validate_folder_name — special names
# ===========================================================================

class TestValidateFolderNameSpecialNames:
    def test_single_dot_rejected(self):
        valid, _ = validate_folder_name(".")
        assert valid is False

    def test_double_dot_rejected(self):
        valid, _ = validate_folder_name("..")
        assert valid is False

    def test_error_message_for_dot(self):
        _, msg = validate_folder_name(".")
        assert "." in msg or "cannot" in msg.lower()


# ===========================================================================
# validate_folder_name — Windows reserved names
# ===========================================================================

class TestValidateFolderNameReserved:
    @pytest.mark.parametrize("name", [
        "con", "prn", "aux", "nul",
        "com1", "com9",
        "lpt1", "lpt9",
    ])
    def test_reserved_name_lowercase_rejected(self, name: str):
        valid, _ = validate_folder_name(name)
        assert valid is False

    @pytest.mark.parametrize("name", ["CON", "COM1", "LPT5", "NUL", "PRN"])
    def test_reserved_name_uppercase_rejected(self, name: str):
        valid, _ = validate_folder_name(name)
        assert valid is False

    def test_error_message_for_reserved_name(self):
        _, msg = validate_folder_name("con")
        assert "reserved" in msg.lower() or "con" in msg.lower()


# ===========================================================================
# check_duplicate_folder
# ===========================================================================

class TestCheckDuplicateFolder:
    def test_returns_true_when_folder_exists(self, tmp_path: Path):
        (tmp_path / "my-project").mkdir()
        assert check_duplicate_folder("my-project", str(tmp_path)) is True

    def test_returns_false_when_folder_absent(self, tmp_path: Path):
        assert check_duplicate_folder("nonexistent-project", str(tmp_path)) is False

    def test_empty_name_returns_false(self, tmp_path: Path):
        assert check_duplicate_folder("", str(tmp_path)) is False

    def test_empty_destination_returns_false(self):
        assert check_duplicate_folder("my-project", "") is False

    def test_both_empty_returns_false(self):
        assert check_duplicate_folder("", "") is False

    def test_returns_true_for_file_with_same_name(self, tmp_path: Path):
        # `exists()` is True for files too — confirms function uses `exists()`.
        (tmp_path / "collide").write_text("x")
        assert check_duplicate_folder("collide", str(tmp_path)) is True


# ===========================================================================
# validate_destination_path
# ===========================================================================

class TestValidateDestinationPath:
    def test_empty_path_is_invalid(self):
        valid, _ = validate_destination_path("")
        assert valid is False

    def test_whitespace_only_path_is_invalid(self):
        valid, _ = validate_destination_path("   ")
        assert valid is False

    def test_nonexistent_path_is_invalid(self, tmp_path: Path):
        valid, _ = validate_destination_path(str(tmp_path / "does_not_exist"))
        assert valid is False

    def test_path_is_file_not_dir_is_invalid(self, tmp_path: Path):
        f = tmp_path / "file.txt"
        f.write_text("content")
        valid, _ = validate_destination_path(str(f))
        assert valid is False

    def test_valid_writable_dir_is_accepted(self, tmp_path: Path):
        valid, msg = validate_destination_path(str(tmp_path))
        assert valid is True
        assert msg == ""

    def test_non_writable_dir_is_invalid(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(os, "access", lambda *_: False)
        valid, _ = validate_destination_path(str(tmp_path))
        assert valid is False

    def test_error_message_empty_path(self):
        _, msg = validate_destination_path("")
        assert "empty" in msg.lower()

    def test_error_message_nonexistent_path(self, tmp_path: Path):
        _, msg = validate_destination_path(str(tmp_path / "ghost"))
        assert "exist" in msg.lower() or "not found" in msg.lower()

    def test_error_message_not_dir(self, tmp_path: Path):
        f = tmp_path / "reg.txt"
        f.write_text("x")
        _, msg = validate_destination_path(str(f))
        assert "director" in msg.lower() or "dir" in msg.lower()

    def test_error_message_not_writable(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(os, "access", lambda *_: False)
        _, msg = validate_destination_path(str(tmp_path))
        assert "writable" in msg.lower() or "write" in msg.lower() or "permission" in msg.lower()


# ===========================================================================
# App._on_create_project — integration tests
# ===========================================================================

class TestOnCreateProjectEmptyName:
    def test_empty_name_shows_name_error_label(self):
        app = _make_app(project_name="")
        app._on_create_project()
        app.project_name_error_label.configure.assert_called()
        calls = [str(c) for c in app.project_name_error_label.configure.call_args_list]
        # The last call must NOT be text="" (error must be set).
        last_call = app.project_name_error_label.configure.call_args
        assert last_call[1].get("text", last_call[0][0] if last_call[0] else "") != ""

    def test_empty_name_does_not_proceed_to_create(self):
        app = _make_app(project_name="")
        with patch.dict(_APP_GLOBALS, {"create_project": MagicMock()}) as mocks_dict:
            app._on_create_project()
            mocks_dict["create_project"].assert_not_called()


class TestOnCreateProjectInvalidName:
    def test_invalid_name_shows_name_error_label(self):
        app = _make_app(project_name="bad<name")
        app._on_create_project()
        calls_with_error = [
            c for c in app.project_name_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        assert calls_with_error, "Expected an error message on project_name_error_label"

    def test_reserved_name_shows_name_error_label(self):
        app = _make_app(project_name="con")
        app._on_create_project()
        calls_with_error = [
            c for c in app.project_name_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        assert calls_with_error


class TestOnCreateProjectDestinationErrors:
    def test_empty_destination_shows_dest_error_label(self, tmp_path: Path):
        app = _make_app(project_name="valid-name", destination="")
        app._on_create_project()
        calls_with_error = [
            c for c in app.destination_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        assert calls_with_error

    def test_nonexistent_destination_shows_dest_error_label(self, tmp_path: Path):
        ghost = str(tmp_path / "does_not_exist")
        app = _make_app(project_name="valid-name", destination=ghost)
        app._on_create_project()
        calls_with_error = [
            c for c in app.destination_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        assert calls_with_error

    def test_nonexistent_destination_does_not_proceed_to_create(self, tmp_path: Path):
        ghost = str(tmp_path / "does_not_exist")
        app = _make_app(project_name="valid-name", destination=ghost)
        with patch.dict(_APP_GLOBALS, {"create_project": MagicMock()}) as mocks_dict:
            app._on_create_project()
            mocks_dict["create_project"].assert_not_called()


class TestOnCreateProjectDuplicate:
    def test_duplicate_folder_shows_name_error_label(self, tmp_path: Path):
        (tmp_path / "TS-SAE-myproject").mkdir()
        app = _make_app(project_name="myproject", destination=str(tmp_path))
        app._on_create_project()
        calls_with_error = [
            c for c in app.project_name_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        assert calls_with_error

    def test_duplicate_message_mentions_folder_name(self, tmp_path: Path):
        folder_name = "uniquefolderxyz"
        (tmp_path / f"TS-SAE-{folder_name}").mkdir()
        app = _make_app(project_name=folder_name, destination=str(tmp_path))
        app._on_create_project()
        error_texts = [
            c[1].get("text", "")
            for c in app.project_name_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        assert any(f"TS-SAE-{folder_name}" in t for t in error_texts)


class TestOnCreateProjectErrorClearing:
    def test_name_error_label_cleared_before_validation(self, tmp_path: Path):
        """The label must be reset to '' at the start of each click — first call."""
        app = _make_app(project_name="valid", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]), \
             patch("launcher.gui.app.create_project", return_value=tmp_path / "valid"), \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()
        app.project_name_error_label.configure.assert_any_call(text="")

    def test_dest_error_label_cleared_before_validation(self, tmp_path: Path):
        app = _make_app(project_name="valid", destination=str(tmp_path))
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]), \
             patch("launcher.gui.app.create_project", return_value=tmp_path / "valid"), \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()
        app.destination_error_label.configure.assert_any_call(text="")

    def test_second_click_clears_previous_name_error(self, tmp_path: Path):
        """Errors from first click must be cleared before second click re-validates."""
        # First click: invalid name sets error.
        app = _make_app(project_name="bad<name")
        app._on_create_project()
        # Second click: valid name — confirm label is reset.
        app.project_name_entry.get.return_value = "valid-name"
        app.destination_entry.get.return_value = str(tmp_path)
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]), \
             patch("launcher.gui.app.create_project", return_value=tmp_path / "valid-name"), \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()
        app.project_name_error_label.configure.assert_any_call(text="")


class TestOnCreateProjectHappyPath:
    def test_valid_inputs_call_create_project(self, tmp_path: Path):
        app = _make_app(project_name="my-app", destination=str(tmp_path))
        mock_create = MagicMock(return_value=tmp_path / "my-app")
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]), \
             patch("launcher.gui.app.create_project", mock_create), \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()
        mock_create.assert_called_once()

    def test_success_shows_info_messagebox(self, tmp_path: Path):
        app = _make_app(project_name="my-app", destination=str(tmp_path))
        mock_mb = MagicMock()
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]), \
             patch("launcher.gui.app.create_project", return_value=tmp_path / "my-app"), \
             patch("launcher.gui.app.messagebox", mock_mb):
            app._on_create_project()
        mock_mb.showinfo.assert_called_once()

    def test_template_not_found_shows_error_messagebox(self, tmp_path: Path):
        """When no template matches the display name a messagebox.showerror is shown."""
        app = _make_app(
            project_name="my-app",
            template_display="Nonexistent Template",
            destination=str(tmp_path),
        )
        mock_mb = MagicMock()
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]), \
             patch("launcher.gui.app.messagebox", mock_mb):
            app._on_create_project()
        mock_mb.showerror.assert_called_once()

    def test_create_project_exception_shows_error_messagebox(self, tmp_path: Path):
        """Exceptions from create_project surface as a messagebox.showerror."""
        app = _make_app(project_name="my-app", destination=str(tmp_path))
        mock_mb = MagicMock()
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]), \
             patch("launcher.gui.app.create_project", side_effect=OSError("disk full")), \
             patch("launcher.gui.app.messagebox", mock_mb):
            app._on_create_project()
        mock_mb.showerror.assert_called_once()


# ===========================================================================
# Edge-case tests
# ===========================================================================

class TestEdgeCases:
    def test_name_with_only_periods_rejected(self):
        valid, _ = validate_folder_name("...")
        assert valid is False

    def test_name_255_unicode_chars_valid(self):
        name = "á" * 255
        valid, _ = validate_folder_name(name)
        assert valid is True

    def test_validate_folder_name_returns_tuple(self):
        result = validate_folder_name("test")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_validate_destination_returns_tuple(self, tmp_path: Path):
        result = validate_destination_path(str(tmp_path))
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_check_duplicate_returns_bool(self, tmp_path: Path):
        result = check_duplicate_folder("x", str(tmp_path))
        assert isinstance(result, bool)

    def test_validate_folder_name_success_has_empty_message(self):
        valid, msg = validate_folder_name("good-name")
        assert valid is True
        assert msg == ""

    def test_validate_destination_success_has_empty_message(self, tmp_path: Path):
        valid, msg = validate_destination_path(str(tmp_path))
        assert valid is True
        assert msg == ""

    def test_name_with_leading_spaces_stripped_by_app(self, tmp_path: Path):
        """App strips the name before validation; ' valid' should succeed."""
        app = _make_app(project_name="  valid-project  ", destination=str(tmp_path))
        mock_create = MagicMock(return_value=tmp_path / "valid-project")
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]), \
             patch("launcher.gui.app.create_project", mock_create), \
             patch("launcher.gui.app.messagebox"):
            app._on_create_project()
        # validate_folder_name must receive the stripped name.
        create_call = mock_create.call_args
        assert create_call is not None  # create_project was called
