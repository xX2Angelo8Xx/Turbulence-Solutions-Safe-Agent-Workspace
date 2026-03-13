"""Tests for GUI-003: Folder Name Input.

Covers validate_folder_name, check_duplicate_folder, and the App error label
widget.  All App tests run headlessly using the same MagicMock pattern as
GUI-001.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# customtkinter is already mocked by tests/conftest.py — reuse that mock.
# ---------------------------------------------------------------------------
_CTK_MOCK = sys.modules["customtkinter"]

from launcher.gui.validation import check_duplicate_folder, validate_folder_name  # noqa: E402
from launcher.gui.app import App  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_app() -> App:
    _CTK_MOCK.reset_mock()
    return App()


# ---------------------------------------------------------------------------
# validate_folder_name — valid names
# ---------------------------------------------------------------------------

class TestValidateFolderNameValid:
    def test_valid_simple_name(self):
        ok, msg = validate_folder_name("my-project")
        assert ok is True
        assert msg == ""

    def test_valid_name_with_numbers(self):
        ok, _ = validate_folder_name("project123")
        assert ok is True

    def test_valid_name_with_underscores(self):
        ok, _ = validate_folder_name("my_project")
        assert ok is True

    def test_valid_name_with_hyphens(self):
        ok, _ = validate_folder_name("my-cool-project")
        assert ok is True

    def test_return_type_is_tuple(self):
        result = validate_folder_name("valid")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_valid_returns_empty_message(self):
        _, msg = validate_folder_name("valid-name")
        assert msg == ""

    def test_unicode_accented_chars_valid(self):
        ok, _ = validate_folder_name("Ünïcödé-project")
        assert ok is True

    def test_emoji_in_name_valid(self):
        ok, _ = validate_folder_name("project-🚀")
        assert ok is True

    def test_leading_dot_valid(self):
        ok, _ = validate_folder_name(".hidden-project")
        assert ok is True

    def test_name_length_255_valid(self):
        ok, _ = validate_folder_name("a" * 255)
        assert ok is True


# ---------------------------------------------------------------------------
# validate_folder_name — empty / whitespace
# ---------------------------------------------------------------------------

class TestValidateFolderNameEmpty:
    def test_empty_string_invalid(self):
        ok, msg = validate_folder_name("")
        assert ok is False
        assert msg != ""

    def test_whitespace_only_invalid(self):
        ok, msg = validate_folder_name("   ")
        assert ok is False
        assert msg != ""

    def test_invalid_returns_nonempty_message(self):
        _, msg = validate_folder_name("")
        assert isinstance(msg, str)
        assert len(msg) > 0


# ---------------------------------------------------------------------------
# validate_folder_name — illegal characters
# ---------------------------------------------------------------------------

class TestValidateFolderNameIllegalChars:
    def test_colon_invalid(self):
        ok, _ = validate_folder_name("my:project")
        assert ok is False

    def test_backslash_invalid(self):
        ok, _ = validate_folder_name("my\\project")
        assert ok is False

    def test_forward_slash_invalid(self):
        ok, _ = validate_folder_name("my/project")
        assert ok is False

    def test_asterisk_invalid(self):
        ok, _ = validate_folder_name("my*project")
        assert ok is False

    def test_question_mark_invalid(self):
        ok, _ = validate_folder_name("my?project")
        assert ok is False

    def test_pipe_invalid(self):
        ok, _ = validate_folder_name("my|project")
        assert ok is False

    def test_less_than_invalid(self):
        ok, _ = validate_folder_name("my<project")
        assert ok is False

    def test_greater_than_invalid(self):
        ok, _ = validate_folder_name("my>project")
        assert ok is False

    def test_double_quote_invalid(self):
        ok, _ = validate_folder_name('my"project')
        assert ok is False

    def test_null_byte_invalid(self):
        ok, _ = validate_folder_name("my\x00project")
        assert ok is False

    def test_control_char_invalid(self):
        ok, _ = validate_folder_name("my\x01project")
        assert ok is False

    def test_tab_char_invalid(self):
        ok, _ = validate_folder_name("my\tproject")
        assert ok is False


# ---------------------------------------------------------------------------
# validate_folder_name — dot names
# ---------------------------------------------------------------------------

class TestValidateFolderNameDots:
    def test_single_dot_invalid(self):
        ok, _ = validate_folder_name(".")
        assert ok is False

    def test_double_dot_invalid(self):
        ok, _ = validate_folder_name("..")
        assert ok is False


# ---------------------------------------------------------------------------
# validate_folder_name — Windows reserved names
# ---------------------------------------------------------------------------

class TestValidateFolderNameWindowsReserved:
    def test_windows_reserved_con_uppercase_invalid(self):
        ok, _ = validate_folder_name("CON")
        assert ok is False

    def test_windows_reserved_nul_lowercase_invalid(self):
        ok, _ = validate_folder_name("nul")
        assert ok is False

    def test_windows_reserved_case_insensitive(self):
        ok, _ = validate_folder_name("Con")
        assert ok is False

    def test_windows_reserved_com9_invalid(self):
        ok, _ = validate_folder_name("com9")
        assert ok is False

    def test_windows_reserved_lpt1_invalid(self):
        ok, _ = validate_folder_name("lpt1")
        assert ok is False

    def test_windows_reserved_prn_invalid(self):
        ok, _ = validate_folder_name("PRN")
        assert ok is False

    def test_windows_reserved_aux_invalid(self):
        ok, _ = validate_folder_name("AUX")
        assert ok is False


# ---------------------------------------------------------------------------
# validate_folder_name — trailing characters
# ---------------------------------------------------------------------------

class TestValidateFolderNameTrailing:
    def test_name_ending_with_dot_invalid(self):
        ok, _ = validate_folder_name("myproject.")
        assert ok is False

    def test_name_ending_with_space_invalid(self):
        ok, _ = validate_folder_name("myproject ")
        assert ok is False


# ---------------------------------------------------------------------------
# validate_folder_name — length
# ---------------------------------------------------------------------------

class TestValidateFolderNameLength:
    def test_name_length_256_invalid(self):
        ok, msg = validate_folder_name("a" * 256)
        assert ok is False
        assert "too long" in msg.lower() or "255" in msg


# ---------------------------------------------------------------------------
# validate_folder_name — security / bypass attempts
# ---------------------------------------------------------------------------

class TestValidateFolderNameSecurity:
    def test_path_traversal_with_slash_rejected(self):
        ok, _ = validate_folder_name("../evil")
        assert ok is False

    def test_path_traversal_backslash_rejected(self):
        ok, _ = validate_folder_name("..\\evil")
        assert ok is False

    def test_null_byte_before_reserved_rejected(self):
        ok, _ = validate_folder_name("\x00con")
        assert ok is False

    def test_control_char_bypass_rejected(self):
        ok, _ = validate_folder_name("valid\x1fname")
        assert ok is False


# ---------------------------------------------------------------------------
# check_duplicate_folder
# ---------------------------------------------------------------------------

class TestValidateFolderNameTesterEdgeCases:
    """Additional edge-case tests added by Tester Agent in Iteration 2."""

    def test_digits_only_name_valid(self):
        """A name composed entirely of digits is a legal folder name."""
        ok, msg = validate_folder_name("123")
        assert ok is True
        assert msg == ""

    def test_carriage_return_invalid(self):
        """Carriage return (0x0D) is a control character and must be rejected."""
        ok, _ = validate_folder_name("my\rproject")
        assert ok is False

    def test_newline_char_invalid(self):
        """Newline (0x0A) is a control character and must be rejected."""
        ok, _ = validate_folder_name("my\nproject")
        assert ok is False


class TestCheckDuplicateFolder:
    def test_nonexistent_folder_returns_false(self, tmp_path):
        ok = check_duplicate_folder("does-not-exist", str(tmp_path))
        assert ok is False

    def test_existing_folder_returns_true(self, tmp_path):
        existing = tmp_path / "my-project"
        existing.mkdir()
        ok = check_duplicate_folder("my-project", str(tmp_path))
        assert ok is True

    def test_empty_name_returns_false(self, tmp_path):
        ok = check_duplicate_folder("", str(tmp_path))
        assert ok is False

    def test_empty_destination_returns_false(self):
        ok = check_duplicate_folder("some-name", "")
        assert ok is False

    def test_both_empty_returns_false(self):
        ok = check_duplicate_folder("", "")
        assert ok is False

    def test_existing_file_at_target_returns_true(self, tmp_path):
        existing = tmp_path / "my-project"
        existing.write_text("file, not a folder")
        ok = check_duplicate_folder("my-project", str(tmp_path))
        assert ok is True

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Symlink creation requires elevated privileges on Windows",
    )
    def test_symlink_to_existing_dir_returns_true(self, tmp_path):
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        link = tmp_path / "my-project"
        link.symlink_to(real_dir)
        ok = check_duplicate_folder("my-project", str(tmp_path))
        assert ok is True


# ---------------------------------------------------------------------------
# App — error label widget
# ---------------------------------------------------------------------------

class TestAppErrorLabel:
    def test_project_name_error_label_exists(self):
        app = _fresh_app()
        assert hasattr(app, "project_name_error_label")

    def test_error_label_created_with_empty_text(self):
        _CTK_MOCK.reset_mock()
        App()
        label_calls = _CTK_MOCK.CTkLabel.call_args_list
        empty_text_calls = [
            c for c in label_calls
            if c.kwargs.get("text") == "" or (c.args and len(c.args) > 1 and c.args[1] == "")
        ]
        assert len(empty_text_calls) >= 1, (
            "Expected at least one CTkLabel created with text='' for the error label"
        )
