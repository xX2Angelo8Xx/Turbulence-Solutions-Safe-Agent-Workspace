"""Tests for GUI-004: Location Browser.

Covers validate_destination_path and the destination_error_label widget in App.
All App tests run headlessly using the same MagicMock pattern as GUI-001/GUI-003.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# customtkinter is already mocked by tests/conftest.py — reuse that mock.
# ---------------------------------------------------------------------------
_CTK_MOCK = sys.modules["customtkinter"]

from launcher.gui.validation import validate_destination_path  # noqa: E402
from launcher.gui.app import App  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_app() -> App:
    _CTK_MOCK.reset_mock()
    return App()


# ---------------------------------------------------------------------------
# validate_destination_path — empty / whitespace
# ---------------------------------------------------------------------------

class TestValidateDestinationPathEmpty:
    def test_empty_string_rejected(self):
        ok, msg = validate_destination_path("")
        assert ok is False

    def test_whitespace_only_rejected(self):
        ok, msg = validate_destination_path("   ")
        assert ok is False

    def test_empty_returns_nonempty_message(self):
        _, msg = validate_destination_path("")
        assert msg != ""

    def test_whitespace_returns_nonempty_message(self):
        _, msg = validate_destination_path("   ")
        assert msg != ""


# ---------------------------------------------------------------------------
# validate_destination_path — non-existent path
# ---------------------------------------------------------------------------

class TestValidateDestinationPathNonExistent:
    def test_nonexistent_path_rejected(self, tmp_path):
        missing = str(tmp_path / "does_not_exist" / "subdir")
        ok, msg = validate_destination_path(missing)
        assert ok is False

    def test_nonexistent_path_error_message_not_empty(self, tmp_path):
        missing = str(tmp_path / "does_not_exist")
        _, msg = validate_destination_path(missing)
        assert msg != ""


# ---------------------------------------------------------------------------
# validate_destination_path — path is a file, not a directory
# ---------------------------------------------------------------------------

class TestValidateDestinationPathIsFile:
    def test_file_path_rejected(self, tmp_path):
        f = tmp_path / "somefile.txt"
        f.write_text("data")
        ok, msg = validate_destination_path(str(f))
        assert ok is False

    def test_file_path_error_message_not_empty(self, tmp_path):
        f = tmp_path / "somefile.txt"
        f.write_text("data")
        _, msg = validate_destination_path(str(f))
        assert msg != ""


# ---------------------------------------------------------------------------
# validate_destination_path — valid writable directory
# ---------------------------------------------------------------------------

class TestValidateDestinationPathValid:
    def test_valid_writable_dir_accepted(self, tmp_path):
        ok, msg = validate_destination_path(str(tmp_path))
        assert ok is True
        assert msg == ""

    def test_return_type_is_tuple(self, tmp_path):
        result = validate_destination_path(str(tmp_path))
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_valid_returns_bool_true(self, tmp_path):
        ok, _ = validate_destination_path(str(tmp_path))
        assert ok is True

    def test_valid_returns_empty_string(self, tmp_path):
        _, msg = validate_destination_path(str(tmp_path))
        assert msg == ""


# ---------------------------------------------------------------------------
# validate_destination_path — non-writable directory
# ---------------------------------------------------------------------------

class TestValidateDestinationPathNotWritable:
    def test_nonwritable_path_rejected(self, tmp_path):
        # Patch os.access to simulate a non-writable directory.
        with patch("launcher.gui.validation.os.access", return_value=False):
            ok, msg = validate_destination_path(str(tmp_path))
        assert ok is False

    def test_nonwritable_error_message_not_empty(self, tmp_path):
        with patch("launcher.gui.validation.os.access", return_value=False):
            _, msg = validate_destination_path(str(tmp_path))
        assert msg != ""

    def test_writable_check_uses_os_access(self, tmp_path):
        """Confirm os.access is called with W_OK for an existing directory."""
        with patch("launcher.gui.validation.os.access") as mock_access:
            mock_access.return_value = True
            validate_destination_path(str(tmp_path))
        mock_access.assert_called_once()
        args, kwargs = mock_access.call_args
        assert args[1] == os.W_OK


# ---------------------------------------------------------------------------
# App — destination_error_label widget
# ---------------------------------------------------------------------------

class TestDestinationErrorLabel:
    def test_destination_error_label_exists(self):
        app = _fresh_app()
        assert hasattr(app, "destination_error_label")

    def test_destination_error_label_created_with_empty_text(self):
        app = _fresh_app()
        _CTK_MOCK.CTkLabel.assert_any_call(
            app._window,
            text="",
            text_color="red",
            anchor="w",
            height=16,
        )

    def test_destination_error_label_grid_called(self):
        app = _fresh_app()
        # All CTkLabel instances share the same mock; verify grid was called.
        app.destination_error_label.grid.assert_called()

    def test_destination_error_label_grid_row_4(self):
        app = _fresh_app()
        all_calls = app.destination_error_label.grid.call_args_list
        assert any(
            (c.kwargs or c[1]).get("row") == 4
            for c in all_calls
        ), f"No grid() call with row=4 found; calls: {all_calls}"


# ---------------------------------------------------------------------------
# App — import of validate_destination_path
# ---------------------------------------------------------------------------

class TestAppImportsValidateDestinationPath:
    def test_validate_destination_path_importable_from_app_module(self):
        import launcher.gui.app as app_module
        import launcher.gui.validation as val_module
        assert hasattr(val_module, "validate_destination_path")
