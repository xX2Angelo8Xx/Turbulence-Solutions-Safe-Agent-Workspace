"""Tests for GUI-004: Location Browser / destination path validation.

All tests run headlessly by replacing `customtkinter` with a MagicMock in
``sys.modules`` before the modules under test are imported.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Inject the customtkinter mock BEFORE importing any launcher module.
# ---------------------------------------------------------------------------
_CTK_MOCK = MagicMock(name="customtkinter")
sys.modules["customtkinter"] = _CTK_MOCK

for _key in [k for k in sys.modules if k.startswith("launcher.gui")]:
    del sys.modules[_key]

from launcher.gui.validation import validate_destination_path  # noqa: E402
from launcher.gui.app import App  # noqa: E402


def _fresh_app() -> App:
    _CTK_MOCK.reset_mock()
    return App()


# ---------------------------------------------------------------------------
# validate_destination_path — empty / whitespace
# ---------------------------------------------------------------------------

class TestEmptyDestination:
    def test_empty_string_rejected(self):
        ok, msg = validate_destination_path("")
        assert ok is False
        assert "empty" in msg.lower()

    def test_whitespace_only_rejected(self):
        ok, msg = validate_destination_path("   ")
        assert ok is False
        assert "empty" in msg.lower()


# ---------------------------------------------------------------------------
# validate_destination_path — non-existent path
# ---------------------------------------------------------------------------

class TestNonExistentDestination:
    def test_nonexistent_path_rejected(self, tmp_path):
        missing = str(tmp_path / "does_not_exist")
        ok, msg = validate_destination_path(missing)
        assert ok is False
        assert "exist" in msg.lower()


# ---------------------------------------------------------------------------
# validate_destination_path — file instead of directory
# ---------------------------------------------------------------------------

class TestFileNotDirectory:
    def test_file_path_rejected(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("data")
        ok, msg = validate_destination_path(str(f))
        assert ok is False
        assert "directory" in msg.lower()


# ---------------------------------------------------------------------------
# validate_destination_path — valid writable directory
# ---------------------------------------------------------------------------

class TestValidDestination:
    def test_valid_writable_dir_accepted(self, tmp_path):
        ok, msg = validate_destination_path(str(tmp_path))
        assert ok is True
        assert msg == ""

    def test_returns_tuple(self, tmp_path):
        result = validate_destination_path(str(tmp_path))
        assert isinstance(result, tuple)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# validate_destination_path — not writable
# ---------------------------------------------------------------------------

class TestNotWritableDestination:
    def test_non_writable_dir_rejected(self, tmp_path, monkeypatch):
        import os
        monkeypatch.setattr(os, "access", lambda path, mode: False)
        ok, msg = validate_destination_path(str(tmp_path))
        assert ok is False
        assert "writable" in msg.lower()


# ---------------------------------------------------------------------------
# App: destination_error_label attribute
# ---------------------------------------------------------------------------

class TestAppDestinationErrorLabel:
    def test_destination_error_label_exists(self):
        app = _fresh_app()
        assert hasattr(app, "destination_error_label")

    def test_destination_error_label_has_red_color(self):
        _CTK_MOCK.reset_mock()
        App()
        label_calls = _CTK_MOCK.CTkLabel.call_args_list
        red_calls = [c for c in label_calls if c.kwargs.get("text_color") == "red"]
        assert len(red_calls) >= 2

    def test_destination_error_label_initial_text_empty(self):
        _CTK_MOCK.reset_mock()
        App()
        label_calls = _CTK_MOCK.CTkLabel.call_args_list
        empty_text_calls = [c for c in label_calls if c.kwargs.get("text") == ""]
        assert len(empty_text_calls) >= 2


# ---------------------------------------------------------------------------
# App: browse button is present and invokes dialog
# ---------------------------------------------------------------------------

class TestBrowseButton:
    def test_browse_destination_populates_entry(self):
        app = _fresh_app()
        app.destination_entry.reset_mock()
        with patch("launcher.gui.app.filedialog.askdirectory", return_value="/tmp/dest"):
            app._browse_destination()
        app.destination_entry.delete.assert_called_once_with(0, "end")
        app.destination_entry.insert.assert_called_once_with(0, "/tmp/dest")

    def test_browse_noop_when_cancelled(self):
        app = _fresh_app()
        app.destination_entry.reset_mock()
        with patch("launcher.gui.app.filedialog.askdirectory", return_value=""):
            app._browse_destination()
        app.destination_entry.delete.assert_not_called()
        app.destination_entry.insert.assert_not_called()


# ---------------------------------------------------------------------------
# Edge-case tests added by Tester review
# ---------------------------------------------------------------------------

class TestEdgeCasesGui004:
    def test_validate_destination_returns_tuple(self, tmp_path):
        """Return value is always a (bool, str) tuple."""
        result = validate_destination_path(str(tmp_path))
        assert isinstance(result, tuple)
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_invalid_path_error_message_is_non_empty(self):
        """Error message for an invalid path is a non-empty string."""
        _, msg = validate_destination_path("")
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_path_with_surrounding_whitespace_rejected(self, tmp_path):
        """A path with surrounding whitespace is treated as-is (not stripped);
        the padded string will not match the real path and must be rejected."""
        padded = "   " + str(tmp_path) + "   "
        ok, _ = validate_destination_path(padded)
        assert ok is False

    def test_relative_dot_path_accepted(self):
        """A bare '.' resolves to the current working directory which always
        exists and is a writable directory in the test environment."""
        ok, _ = validate_destination_path(".")
        assert ok is True
