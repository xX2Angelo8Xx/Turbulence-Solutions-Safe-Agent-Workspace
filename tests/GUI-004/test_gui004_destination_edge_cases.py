"""Edge-case tests for GUI-004: Destination Path Validation.

Covers scenarios the developer's initial test suite did not exercise:
  - Paths with trailing / leading whitespace
  - Paths with special characters (spaces, Unicode, parentheses, hyphens)
  - Very long and deeply-nested non-existent paths
  - Cross-platform path separators (forward-slash vs back-slash on Windows)
  - Defensive input handling (None, return-type guarantees)

TST-339 through TST-354  (16 tests added by Tester Agent — GUI-004 review)
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# customtkinter must be mocked before *any* launcher.gui module is imported.
# validation.py itself does not import customtkinter, but if another test
# in the same session has already imported a launcher.gui module that does,
# the mock is already in place.  We inject it defensively here.
# ---------------------------------------------------------------------------
if "customtkinter" not in sys.modules:
    sys.modules["customtkinter"] = MagicMock(name="customtkinter")

from launcher.gui.validation import validate_destination_path  # noqa: E402


# ---------------------------------------------------------------------------
# TST-339 to TST-341 — Trailing and leading whitespace handling
# ---------------------------------------------------------------------------

class TestWhitespacePaths:
    def test_single_space_rejected(self):
        """A single space character is whitespace-only and must be rejected.

        TST-339
        """
        ok, msg = validate_destination_path(" ")
        assert ok is False
        assert msg != ""

    def test_leading_whitespace_on_valid_path_rejected(self, tmp_path: Path):
        """Path string with leading spaces makes the path non-existent on
        all platforms (leading spaces are significant everywhere).

        TST-340
        """
        mangled = "   " + str(tmp_path)
        ok, msg = validate_destination_path(mangled)
        assert ok is False
        # Leading spaces cause path-not-found on Windows and Linux alike.
        assert msg != ""

    def test_trailing_whitespace_no_crash(self, tmp_path: Path):
        """Path string with trailing spaces must not crash the validator.

        On Windows, Win32 silently strips trailing spaces from paths, so the
        function may return (True, '').  On Linux/macOS, the mangled path is
        non-existent, so the function returns (False, <message>).
        In all cases the return value must be a 2-tuple of (bool, str).

        TST-341
        """
        mangled = str(tmp_path) + "   "
        result = validate_destination_path(mangled)
        assert isinstance(result, tuple)
        assert len(result) == 2
        ok, msg = result
        assert isinstance(ok, bool)
        assert isinstance(msg, str)
        # Rule: when rejected, the message must be non-empty.
        if not ok:
            assert msg != ""


# ---------------------------------------------------------------------------
# TST-342 to TST-346 — Paths with special characters
# ---------------------------------------------------------------------------

class TestSpecialCharacterPaths:
    def test_dir_with_spaces_in_name_accepted(self, tmp_path: Path):
        """A valid directory whose name contains spaces is accepted.

        TST-342
        """
        spaced_dir = tmp_path / "my project folder"
        spaced_dir.mkdir()
        ok, msg = validate_destination_path(str(spaced_dir))
        assert ok is True
        assert msg == ""

    def test_dir_with_unicode_chars_accepted(self, tmp_path: Path):
        """A valid directory whose name contains Unicode characters is accepted.

        TST-343
        """
        unicode_dir = tmp_path / "proj\u00e9ct_\u03b1\u03b2\u03b3"
        unicode_dir.mkdir()
        ok, msg = validate_destination_path(str(unicode_dir))
        assert ok is True
        assert msg == ""

    def test_dir_with_parentheses_accepted(self, tmp_path: Path):
        """A valid directory whose name contains parentheses is accepted.

        TST-344
        """
        paren_dir = tmp_path / "my(project)"
        paren_dir.mkdir()
        ok, msg = validate_destination_path(str(paren_dir))
        assert ok is True
        assert msg == ""

    def test_dir_with_hyphens_and_underscores_accepted(self, tmp_path: Path):
        """A valid directory whose name contains hyphens and underscores is accepted.

        TST-345
        """
        named_dir = tmp_path / "my-project_folder"
        named_dir.mkdir()
        ok, msg = validate_destination_path(str(named_dir))
        assert ok is True
        assert msg == ""

    def test_dir_starting_with_dot_accepted(self, tmp_path: Path):
        """A valid directory whose name begins with a dot (hidden dir) is accepted.

        TST-346
        """
        dot_dir = tmp_path / ".hidden"
        dot_dir.mkdir()
        ok, msg = validate_destination_path(str(dot_dir))
        assert ok is True
        assert msg == ""


# ---------------------------------------------------------------------------
# TST-347 to TST-348 — Very long paths
# ---------------------------------------------------------------------------

class TestVeryLongPaths:
    def test_long_segment_nonexistent_rejected(self, tmp_path: Path):
        """A path with a 200-character segment that does not exist is rejected
        gracefully without raising an exception.

        TST-347
        """
        long_segment = "a" * 200
        long_path = str(tmp_path / long_segment)
        ok, msg = validate_destination_path(long_path)
        assert ok is False
        assert msg != ""

    def test_deeply_nested_nonexistent_path_rejected(self, tmp_path: Path):
        """A deeply nested (20 levels) path that does not exist is rejected
        gracefully without an exception.

        TST-348
        """
        deep_path = tmp_path
        for _ in range(20):
            deep_path = deep_path / "nested"
        ok, msg = validate_destination_path(str(deep_path))
        assert ok is False
        assert msg != ""


# ---------------------------------------------------------------------------
# TST-349 — Cross-platform path separators
# ---------------------------------------------------------------------------

class TestCrossPlatformPathSeparators:
    def test_forward_slashes_accepted_on_windows(self, tmp_path: Path):
        """On Windows, a path using forward slashes instead of back-slashes
        is resolved correctly by pathlib and must be accepted.

        TST-349
        """
        forward_path = str(tmp_path).replace("\\", "/")
        ok, msg = validate_destination_path(forward_path)
        assert ok is True
        assert msg == ""


# ---------------------------------------------------------------------------
# TST-350 to TST-354 — Defensive input handling
# ---------------------------------------------------------------------------

class TestDefensiveInputHandling:
    def test_none_input_rejected_without_crash(self):
        """None passed as the path argument must be rejected cleanly —
        the ``if not path`` guard short-circuits before any str method is called.

        TST-350
        """
        ok, msg = validate_destination_path(None)
        assert ok is False
        assert msg != ""

    def test_return_is_two_tuple_for_valid_path(self, tmp_path: Path):
        """Return value for a valid path is a 2-tuple of (bool, str).

        TST-351
        """
        result = validate_destination_path(str(tmp_path))
        assert isinstance(result, tuple)
        assert len(result) == 2
        ok, msg = result
        assert isinstance(ok, bool)
        assert isinstance(msg, str)

    def test_return_is_two_tuple_for_invalid_path(self):
        """Return value for an invalid path is a 2-tuple of (bool, str).

        TST-352
        """
        result = validate_destination_path("")
        assert isinstance(result, tuple)
        assert len(result) == 2
        ok, msg = result
        assert isinstance(ok, bool)
        assert isinstance(msg, str)

    def test_error_message_nonempty_when_rejected(self, tmp_path: Path):
        """The error message is always a non-empty string when the function
        rejects a path (i.e. when the first element is False).

        TST-353
        """
        some_file = tmp_path / "file.txt"
        some_file.write_text("data")
        ok, msg = validate_destination_path(str(some_file))
        assert ok is False
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_error_message_empty_when_accepted(self, tmp_path: Path):
        """The error message is always an empty string when the function
        accepts a path (i.e. when the first element is True).

        TST-354
        """
        ok, msg = validate_destination_path(str(tmp_path))
        assert ok is True
        assert msg == ""
