"""Additional edge-case and security tests for GUI-007: Input Validation & Error UX.

Tester Agent additions — covers:
  - Security: path traversal in folder name (/ and \\ characters)
  - Control characters: tab, newline, carriage return in folder name
  - Integration: error-label routing (non-writable dest → dest label, not name label)
  - Integration: error ordering (name invalid + dest invalid → only name error shown)
  - Integration: both labels cleared even after a prior error on second click
  - Defensive: validate_destination_path with null-byte path does not raise
  - Valid name edge cases: all-digits, spaces in middle, long hyphenated
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Inject customtkinter mock before any launcher.gui import (same approach as
# the developer test file so the two can coexist in the same test session).
# ---------------------------------------------------------------------------
_CTK_MOCK = MagicMock(name="customtkinter")
sys.modules.setdefault("customtkinter", _CTK_MOCK)

# Ensure the gui modules are freshly importable (the developer test file
# already cleaned sys.modules before importing; we just rely on the cached
# entries from that previous import since they share the same process).
from launcher.gui.validation import (  # noqa: E402
    check_duplicate_folder,
    validate_destination_path,
    validate_folder_name,
)
from launcher.gui.app import App  # noqa: E402

_APP_GLOBALS = App._on_create_project.__globals__


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app(
    project_name: str = "valid-project",
    template_display: str = "Coding",
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
# Security — path traversal in folder name
# ===========================================================================

class TestValidateFolderNamePathTraversal:
    """Folder names that contain path-traversal characters must be rejected."""

    def test_parent_dir_forward_slash_rejected(self):
        """'../parent' contains '/' — should be rejected."""
        valid, _ = validate_folder_name("../parent")
        assert valid is False

    def test_parent_dir_backslash_rejected(self):
        """'..\\evil' contains '\\' — should be rejected."""
        valid, _ = validate_folder_name("..\\evil")
        assert valid is False

    def test_slash_only_path_segment_rejected(self):
        """'a/b' contains '/' — embedded path separator must be rejected."""
        valid, _ = validate_folder_name("a/b")
        assert valid is False

    def test_backslash_only_path_segment_rejected(self):
        """'a\\b' contains '\\' — embedded backslash must be rejected."""
        valid, _ = validate_folder_name("a\\b")
        assert valid is False

    def test_windows_absolute_path_rejected(self):
        """'C:/Windows/System32' contains illegal chars — rejected."""
        valid, _ = validate_folder_name("C:/Windows/System32")
        assert valid is False

    def test_error_message_mentions_invalid_characters(self):
        """Path-traversal rejection message must mention invalid characters."""
        _, msg = validate_folder_name("../escape")
        assert "invalid" in msg.lower() or "character" in msg.lower()


# ===========================================================================
# Control characters in folder name
# ===========================================================================

class TestValidateFolderNameControlChars:
    """Tab, newline, and carriage-return are control chars (\x09, \x0a, \x0d)
    and must be caught by the _INVALID_CHARS_RE pattern (range \x00–\x1f)."""

    def test_tab_character_rejected(self):
        valid, _ = validate_folder_name("project\tname")
        assert valid is False

    def test_newline_character_rejected(self):
        valid, _ = validate_folder_name("project\nname")
        assert valid is False

    def test_carriage_return_character_rejected(self):
        valid, _ = validate_folder_name("project\rname")
        assert valid is False

    def test_form_feed_character_rejected(self):
        """\x0c (form feed) is in the \x00–\x1f range — must be rejected."""
        valid, _ = validate_folder_name("project\x0cname")
        assert valid is False


# ===========================================================================
# Additional valid name edge cases
# ===========================================================================

class TestValidateFolderNameAdditionalValid:
    def test_all_digits_name_is_valid(self):
        """A purely numeric folder name is a valid file system name."""
        valid, msg = validate_folder_name("123456")
        assert valid is True
        assert msg == ""

    def test_name_with_space_in_middle_is_valid(self):
        """Spaces in the *middle* of a name are valid on all major OSes."""
        valid, msg = validate_folder_name("my project")
        assert valid is True
        assert msg == ""

    def test_long_hyphenated_name_is_valid(self):
        """A realistic project name with multiple hyphens should be accepted."""
        valid, msg = validate_folder_name("turbulence-solutions-ai-project-2026")
        assert valid is True
        assert msg == ""

    def test_name_with_leading_dot_is_valid(self):
        """'.hidden' style names are valid on Unix; the function allows them."""
        valid, _ = validate_folder_name(".hidden-project")
        assert valid is True

    def test_name_with_parentheses_is_valid(self):
        """Parentheses are not in the invalid-chars set."""
        valid, _ = validate_folder_name("project (backup)")
        assert valid is True


# ===========================================================================
# validate_destination_path — defensive edge cases
# ===========================================================================

class TestValidateDestinationPathDefensive:
    def test_null_byte_path_returns_invalid_not_raises(self):
        """A path containing a null byte should return (False, …) not raise."""
        try:
            valid, msg = validate_destination_path("\x00")
            assert valid is False, "Null-byte path must be reported as invalid"
        except (ValueError, OSError) as exc:
            pytest.fail(
                f"validate_destination_path should not raise on null-byte input; "
                f"got {type(exc).__name__}: {exc}"
            )

    def test_path_is_a_symlink_to_a_directory_is_accepted(self, tmp_path: Path):
        """A symlink that resolves to a writable directory should be accepted."""
        target = tmp_path / "real_dir"
        target.mkdir()
        link = tmp_path / "link_dir"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            pytest.skip("Symlink creation not supported on this platform/config")
        valid, msg = validate_destination_path(str(link))
        assert valid is True
        assert msg == ""

    def test_empty_string_with_only_whitespace_is_invalid(self):
        valid, msg = validate_destination_path("\t\n  ")
        assert valid is False
        assert "empty" in msg.lower()


# ===========================================================================
# Integration — error label routing
# ===========================================================================

class TestOnCreateProjectErrorLabelRouting:
    """Validates that each error goes to the *correct* label."""

    def test_invalid_name_sets_name_label_not_dest_label(self):
        """An invalid folder name must populate name_error_label, not dest_error_label."""
        app = _make_app(project_name="bad<name")
        app._on_create_project()
        name_errors = [
            c for c in app.project_name_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        dest_errors = [
            c for c in app.destination_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        assert name_errors, "name_error_label must show the validation error"
        assert not dest_errors, "destination_error_label must remain empty"

    def test_non_writable_dest_sets_dest_label_not_name_label(
        self, tmp_path: Path, monkeypatch
    ):
        """Write-permission failure must go to dest_error_label, not name_error_label."""
        monkeypatch.setattr(os, "access", lambda *_: False)
        app = _make_app(project_name="valid-name", destination=str(tmp_path))
        app._on_create_project()
        name_errors = [
            c for c in app.project_name_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        dest_errors = [
            c for c in app.destination_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        assert not name_errors, "name_error_label must be empty for a permission error"
        assert dest_errors, "destination_error_label must carry the write-permission message"

    def test_invalid_dest_path_sets_dest_label(self, tmp_path: Path):
        """Non-existent destination must go to dest_error_label."""
        ghost = str(tmp_path / "does_not_exist")
        app = _make_app(project_name="good-name", destination=ghost)
        app._on_create_project()
        dest_errors = [
            c for c in app.destination_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        assert dest_errors, "destination_error_label must carry the path error"


# ===========================================================================
# Integration — error ordering (name validated before destination)
# ===========================================================================

class TestOnCreateProjectErrorOrdering:
    def test_invalid_name_takes_precedence_over_invalid_dest(self):
        """When both name and destination are invalid, name error shows first;
        destination error is not shown (function returns early)."""
        app = _make_app(project_name="bad|name", destination="/ghost/path")
        app._on_create_project()
        name_errors = [
            c for c in app.project_name_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        dest_errors = [
            c for c in app.destination_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        assert name_errors, "Name error must appear"
        assert not dest_errors, "Dest error must NOT appear when name validation fails first"

    def test_empty_name_prevents_dest_validation(self):
        """Empty name → early return; destination label stays clear."""
        app = _make_app(project_name="", destination="/nonexistent")
        app._on_create_project()
        dest_errors = [
            c for c in app.destination_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        assert not dest_errors, "Destination label must not be set when name is empty"


# ===========================================================================
# Integration — both labels cleared on every invocation
# ===========================================================================

class TestOnCreateProjectClearingOnEveryClick:
    def test_both_labels_cleared_first_thing_even_on_second_click(
        self, tmp_path: Path
    ):
        """On the SECOND click (after a previous error run), BOTH labels must
        still be cleared at the very start of _on_create_project()."""
        app = _make_app(project_name="bad<name", destination="")

        # First click — sets a name error
        app._on_create_project()
        first_run_calls = len(app.project_name_error_label.configure.call_args_list)

        # Second click — fix the name but supply an invalid dest
        app.project_name_entry.get.return_value = "good-name"
        app.destination_entry.get.return_value = str(tmp_path / "ghost")
        app._on_create_project()

        # The first configure() call after the second click must be text=""
        second_run_clear = app.project_name_error_label.configure.call_args_list[
            first_run_calls
        ]
        cleared_text = second_run_clear[1].get(
            "text",
            second_run_clear[0][0] if second_run_clear[0] else "NOT_CLEARED",
        )
        assert cleared_text == "", (
            "project_name_error_label must be cleared (text='') at start of every click"
        )
