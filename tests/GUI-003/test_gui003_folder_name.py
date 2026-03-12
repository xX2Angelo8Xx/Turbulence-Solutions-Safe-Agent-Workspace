"""Tests for GUI-003: Folder Name Input validation.

All tests run headlessly by replacing `customtkinter` with a MagicMock in
``sys.modules`` before the modules under test are imported.  No display
connection is attempted, so the suite runs on all platforms including
headless CI environments.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Inject the customtkinter mock BEFORE importing any launcher module.
# ---------------------------------------------------------------------------
_CTK_MOCK = MagicMock(name="customtkinter")
sys.modules["customtkinter"] = _CTK_MOCK

for _key in [k for k in sys.modules if k.startswith("launcher.gui")]:
    del sys.modules[_key]

from launcher.gui.validation import (  # noqa: E402
    check_duplicate_folder,
    validate_folder_name,
)
from launcher.gui.app import App  # noqa: E402


def _fresh_app() -> App:
    _CTK_MOCK.reset_mock()
    return App()


# ---------------------------------------------------------------------------
# validate_folder_name — valid names
# ---------------------------------------------------------------------------

class TestValidFolderNames:
    def test_simple_ascii_name(self):
        ok, msg = validate_folder_name("my-project")
        assert ok is True
        assert msg == ""

    def test_name_with_underscores(self):
        ok, msg = validate_folder_name("my_project")
        assert ok is True

    def test_name_with_numbers(self):
        ok, msg = validate_folder_name("project123")
        assert ok is True

    def test_name_with_spaces_inside(self):
        ok, msg = validate_folder_name("my project")
        assert ok is True

    def test_single_character_name(self):
        ok, msg = validate_folder_name("a")
        assert ok is True

    def test_exactly_255_chars(self):
        name = "a" * 255
        ok, msg = validate_folder_name(name)
        assert ok is True


# ---------------------------------------------------------------------------
# validate_folder_name — empty / whitespace
# ---------------------------------------------------------------------------

class TestEmptyAndWhitespace:
    def test_empty_string_rejected(self):
        ok, msg = validate_folder_name("")
        assert ok is False
        assert "empty" in msg.lower()

    def test_whitespace_only_rejected(self):
        ok, msg = validate_folder_name("   ")
        assert ok is False
        assert "empty" in msg.lower()

    def test_none_like_empty_string(self):
        ok, msg = validate_folder_name("")
        assert ok is False


# ---------------------------------------------------------------------------
# validate_folder_name — trailing period / space
# ---------------------------------------------------------------------------

class TestTrailingChars:
    def test_trailing_period_rejected(self):
        ok, msg = validate_folder_name("myproject.")
        assert ok is False
        assert "period" in msg.lower() or "end" in msg.lower()

    def test_trailing_space_rejected(self):
        ok, msg = validate_folder_name("myproject ")
        assert ok is False

    def test_name_that_is_just_period_rejected(self):
        ok, msg = validate_folder_name(".")
        assert ok is False

    def test_name_that_is_dotdot_rejected(self):
        ok, msg = validate_folder_name("..")
        assert ok is False


# ---------------------------------------------------------------------------
# validate_folder_name — illegal characters
# ---------------------------------------------------------------------------

class TestIllegalCharacters:
    @pytest.mark.parametrize("char", ['<', '>', ':', '"', '/', '\\', '|', '?', '*'])
    def test_illegal_char_rejected(self, char: str):
        ok, msg = validate_folder_name(f"proj{char}name")
        assert ok is False
        assert "invalid" in msg.lower() or "character" in msg.lower()

    def test_null_byte_rejected(self):
        ok, msg = validate_folder_name("proj\x00name")
        assert ok is False

    def test_control_char_rejected(self):
        ok, msg = validate_folder_name("proj\x1fname")
        assert ok is False


# ---------------------------------------------------------------------------
# validate_folder_name — Windows reserved names
# ---------------------------------------------------------------------------

class TestWindowsReservedNames:
    @pytest.mark.parametrize("reserved", [
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM9", "LPT1", "LPT9",
    ])
    def test_reserved_name_rejected(self, reserved: str):
        ok, msg = validate_folder_name(reserved)
        assert ok is False
        assert "reserved" in msg.lower()

    def test_reserved_name_lowercase_rejected(self):
        ok, msg = validate_folder_name("con")
        assert ok is False

    def test_reserved_name_mixed_case_rejected(self):
        ok, msg = validate_folder_name("CoN")
        assert ok is False


# ---------------------------------------------------------------------------
# validate_folder_name — length
# ---------------------------------------------------------------------------

class TestNameLength:
    def test_name_256_chars_rejected(self):
        name = "a" * 256
        ok, msg = validate_folder_name(name)
        assert ok is False
        assert "long" in msg.lower() or "255" in msg


# ---------------------------------------------------------------------------
# validate_folder_name — path traversal / security bypasses
# ---------------------------------------------------------------------------

class TestSecurityBypasses:
    def test_path_traversal_dotdot_slash(self):
        ok, _ = validate_folder_name("../evil")
        assert ok is False

    def test_absolute_unix_path(self):
        ok, _ = validate_folder_name("/etc/passwd")
        assert ok is False

    def test_absolute_windows_path(self):
        ok, _ = validate_folder_name("C:\\Windows")
        assert ok is False

    def test_unc_path_rejected(self):
        ok, _ = validate_folder_name("\\\\server\\share")
        assert ok is False


# ---------------------------------------------------------------------------
# check_duplicate_folder
# ---------------------------------------------------------------------------

class TestCheckDuplicateFolder:
    def test_returns_false_for_empty_name(self, tmp_path):
        assert check_duplicate_folder("", str(tmp_path)) is False

    def test_returns_false_for_empty_destination(self):
        assert check_duplicate_folder("myproject", "") is False

    def test_returns_false_when_folder_does_not_exist(self, tmp_path):
        assert check_duplicate_folder("nonexistent", str(tmp_path)) is False

    def test_returns_true_when_folder_exists(self, tmp_path):
        (tmp_path / "existing").mkdir()
        assert check_duplicate_folder("existing", str(tmp_path)) is True

    def test_returns_false_both_empty(self):
        assert check_duplicate_folder("", "") is False


# ---------------------------------------------------------------------------
# App: project_name_error_label attribute
# ---------------------------------------------------------------------------

class TestAppErrorLabel:
    def test_project_name_error_label_exists(self):
        app = _fresh_app()
        assert hasattr(app, "project_name_error_label")

    def test_project_name_error_label_created_with_empty_text(self):
        _CTK_MOCK.reset_mock()
        App()
        label_calls = _CTK_MOCK.CTkLabel.call_args_list
        empty_text_calls = [c for c in label_calls if c.kwargs.get("text") == ""]
        assert len(empty_text_calls) >= 1

    def test_project_name_error_label_has_red_color(self):
        _CTK_MOCK.reset_mock()
        App()
        label_calls = _CTK_MOCK.CTkLabel.call_args_list
        red_calls = [c for c in label_calls if c.kwargs.get("text_color") == "red"]
        assert len(red_calls) >= 1


# ---------------------------------------------------------------------------
# Edge-case tests added by Tester review
# ---------------------------------------------------------------------------

class TestEdgeCasesGui003:
    def test_name_with_leading_spaces_is_valid(self):
        """Leading spaces are NOT stripped by validate_folder_name; only a
        trailing space/period is rejected.  Documents current behaviour."""
        ok, _ = validate_folder_name("  myproject")
        assert ok is True

    def test_tab_character_in_name_rejected(self):
        """Tab (\\x09) falls in the \\x00-\\x1f control-character range and
        must be rejected by the invalid-char regex."""
        ok, _ = validate_folder_name("proj\tname")
        assert ok is False

    def test_validate_folder_name_returns_tuple(self):
        """Return value is always a (bool, str) tuple."""
        result = validate_folder_name("ok-name")
        assert isinstance(result, tuple)
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_error_message_is_non_empty_for_invalid_name(self):
        """Error message for an invalid name is a non-empty string."""
        _, msg = validate_folder_name("")
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_multiple_internal_dots_is_valid(self):
        """Internal dots ('my..project') do not violate any rule."""
        ok, _ = validate_folder_name("my..project")
        assert ok is True

    def test_check_duplicate_folder_matches_file_not_dir(self, tmp_path):
        """check_duplicate_folder returns True when a FILE (not a directory)
        exists at the target path — Path.exists() is True for both."""
        (tmp_path / "target").write_text("data")
        assert check_duplicate_folder("target", str(tmp_path)) is True
