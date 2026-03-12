"""Tests for GUI-003: Folder Name Input.

Covers validate_folder_name(), check_duplicate_folder(), and the
project_name_error_label widget added to App in GUI-003.

All App tests run headlessly using the same MagicMock technique as GUI-001.
"""

from __future__ import annotations

import os
import sys
import tempfile
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Headless customtkinter mock — must happen before any launcher.gui import.
# ---------------------------------------------------------------------------
_CTK_MOCK = MagicMock(name="customtkinter")
sys.modules["customtkinter"] = _CTK_MOCK

for _key in [k for k in sys.modules if k.startswith("launcher.gui")]:
    del sys.modules[_key]

from launcher.gui.validation import check_duplicate_folder, validate_folder_name  # noqa: E402
from launcher.gui.app import App  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_app() -> App:
    _CTK_MOCK.reset_mock()
    return App()


# ===========================================================================
# validate_folder_name — valid names
# ===========================================================================

class TestValidateFolderNameValid:
    def test_valid_simple_name(self):
        ok, msg = validate_folder_name("my-project")
        assert ok is True

    def test_valid_name_with_numbers(self):
        ok, msg = validate_folder_name("project123")
        assert ok is True

    def test_valid_name_with_underscores(self):
        ok, msg = validate_folder_name("my_project")
        assert ok is True

    def test_valid_name_with_hyphens(self):
        ok, msg = validate_folder_name("my-cool-project")
        assert ok is True

    def test_return_type_is_tuple(self):
        result = validate_folder_name("valid")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_valid_returns_empty_message(self):
        _, msg = validate_folder_name("valid-name")
        assert msg == ""


# ===========================================================================
# validate_folder_name — invalid: empty / whitespace
# ===========================================================================

class TestValidateFolderNameEmpty:
    def test_empty_string_invalid(self):
        ok, _ = validate_folder_name("")
        assert ok is False

    def test_whitespace_only_invalid(self):
        ok, _ = validate_folder_name("   ")
        assert ok is False

    def test_invalid_returns_nonempty_message(self):
        _, msg = validate_folder_name("")
        assert msg != ""


# ===========================================================================
# validate_folder_name — invalid: forbidden characters
# ===========================================================================

class TestValidateFolderNameInvalidChars:
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
        ok, _ = validate_folder_name("my\x1fproject")
        assert ok is False


# ===========================================================================
# validate_folder_name — invalid: dot/space names
# ===========================================================================

class TestValidateFolderNameDots:
    def test_single_dot_invalid(self):
        ok, _ = validate_folder_name(".")
        assert ok is False

    def test_double_dot_invalid(self):
        ok, _ = validate_folder_name("..")
        assert ok is False

    def test_name_ending_with_dot_invalid(self):
        ok, _ = validate_folder_name("project.")
        assert ok is False

    def test_name_ending_with_space_invalid(self):
        ok, _ = validate_folder_name("project ")
        assert ok is False


# ===========================================================================
# validate_folder_name — invalid: Windows reserved names
# ===========================================================================

class TestValidateFolderNameReserved:
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
        ok, _ = validate_folder_name("COM9")
        assert ok is False

    def test_windows_reserved_lpt1_invalid(self):
        ok, _ = validate_folder_name("LPT1")
        assert ok is False

    def test_windows_reserved_prn_invalid(self):
        ok, _ = validate_folder_name("PRN")
        assert ok is False

    def test_windows_reserved_aux_invalid(self):
        ok, _ = validate_folder_name("AUX")
        assert ok is False


# ===========================================================================
# validate_folder_name — security: path traversal / injection
# ===========================================================================

class TestValidateFolderNameSecurity:
    def test_path_traversal_with_slash_rejected(self):
        ok, _ = validate_folder_name("../secret")
        assert ok is False

    def test_path_traversal_backslash_rejected(self):
        ok, _ = validate_folder_name("..\\secret")
        assert ok is False

    def test_null_byte_before_reserved_rejected(self):
        ok, _ = validate_folder_name("\x00CON")
        assert ok is False

    def test_control_char_bypass_rejected(self):
        ok, _ = validate_folder_name("proj\x01ect")
        assert ok is False


# ===========================================================================
# validate_folder_name — edge cases (tester additions)
# ===========================================================================

class TestValidateFolderNameEdgeCases:
    def test_unicode_accented_chars_valid(self):
        ok, _ = validate_folder_name("Ünïcödé-project")
        assert ok is True

    def test_emoji_in_name_valid(self):
        ok, _ = validate_folder_name("project-\U0001F680")
        assert ok is True

    def test_tab_char_invalid(self):
        ok, _ = validate_folder_name("my\tproject")
        assert ok is False

    def test_name_length_255_valid(self):
        ok, _ = validate_folder_name("a" * 255)
        assert ok is True

    def test_leading_dot_valid(self):
        ok, _ = validate_folder_name(".hidden-project")
        assert ok is True


# ===========================================================================
# check_duplicate_folder
# ===========================================================================

class TestCheckDuplicateFolder:
    def test_nonexistent_folder_returns_false(self, tmp_path):
        result = check_duplicate_folder("ghost-project", str(tmp_path))
        assert result is False

    def test_existing_folder_returns_true(self, tmp_path):
        (tmp_path / "my-project").mkdir()
        result = check_duplicate_folder("my-project", str(tmp_path))
        assert result is True

    def test_empty_name_returns_false(self, tmp_path):
        result = check_duplicate_folder("", str(tmp_path))
        assert result is False

    def test_empty_destination_returns_false(self):
        result = check_duplicate_folder("my-project", "")
        assert result is False

    def test_both_empty_returns_false(self):
        result = check_duplicate_folder("", "")
        assert result is False

    def test_existing_file_at_target_returns_true(self, tmp_path):
        (tmp_path / "my-project").write_text("file, not a folder")
        result = check_duplicate_folder("my-project", str(tmp_path))
        assert result is True

    @pytest.mark.skipif(
        sys.platform == "win32" and not os.environ.get("CI_ELEVATED"),
        reason="Symlink creation requires elevated privileges on Windows without Developer Mode",
    )
    def test_symlink_to_existing_dir_returns_true(self, tmp_path):
        target = tmp_path / "_real"
        target.mkdir()
        link = tmp_path / "my-project"
        link.symlink_to(target, target_is_directory=True)
        result = check_duplicate_folder("my-project", str(tmp_path))
        assert result is True


# ===========================================================================
# App widget — project_name_error_label
# ===========================================================================

class TestAppErrorLabel:
    def test_project_name_error_label_exists(self):
        app = _fresh_app()
        assert hasattr(app, "project_name_error_label"), (
            "App must have a 'project_name_error_label' attribute after _build_ui()"
        )

    def test_error_label_created_with_empty_text(self):
        app = _fresh_app()
        # The CTkLabel constructor is mocked; inspect the call that created
        # the error label (text="", text_color="red").
        ctk_label_calls = _CTK_MOCK.CTkLabel.call_args_list
        error_label_call = next(
            (
                c
                for c in ctk_label_calls
                if c.kwargs.get("text") == "" and c.kwargs.get("text_color") == "red"
            ),
            None,
        )
        assert error_label_call is not None, (
            "CTkLabel(text='', text_color='red', ...) was not called during App._build_ui()"
        )
