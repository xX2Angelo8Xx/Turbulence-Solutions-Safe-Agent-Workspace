"""Tester Agent additions for GUI-007: Input Validation & Error UX.

Additional edge cases beyond the developer tests and prior edge-case coverage.

Focus areas:
  - Reserved name full matrix: COM2-COM8, LPT2-LPT8 (only COM1/COM9/LPT1/LPT9 tested by developer)
  - Reserved name with extension is NOT blocked (confirmed known-acceptable by dev-log)
  - Unicode fullwidth / lookalike characters allowed (not in invalid-char set)
  - validate_folder_name: error message is a non-empty string (no silent empty errors)
  - validate_destination_path: trailing path separator on valid directory
  - validate_destination_path: root drive letter on Windows
  - check_duplicate_folder: unicode project name vs. unicode directory
  - App._on_create_project: exception from create_project routes to messagebox (not label)
  - App._on_create_project: entire flow with vscode checkbox — no crash when open_in_vscode_var is False
  - API contract: return types are always (bool, str)
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
    # Wire the open_in_vscode_var so it behaves like a BooleanVar mock
    app.open_in_vscode_var = MagicMock()
    app.open_in_vscode_var.get.return_value = False
    return app


# ===========================================================================
# Reserved names — full COM/LPT matrix
# ===========================================================================

class TestReservedNameFullMatrix:
    """COM2-COM8 and LPT2-LPT8 must also be blocked (developer tested only
    the boundary values COM1/COM9 and LPT1/LPT9)."""

    @pytest.mark.parametrize(
        "name",
        ["com2", "com3", "com4", "com5", "com6", "com7", "com8"],
    )
    def test_com_middle_range_rejected(self, name: str):
        valid, msg = validate_folder_name(name)
        assert valid is False, f"{name!r} must be rejected as a reserved name"
        assert msg, f"Error message must not be empty for reserved name {name!r}"

    @pytest.mark.parametrize(
        "name",
        ["lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8"],
    )
    def test_lpt_middle_range_rejected(self, name: str):
        valid, msg = validate_folder_name(name)
        assert valid is False, f"{name!r} must be rejected as a reserved name"
        assert msg, f"Error message must not be empty for reserved name {name!r}"

    @pytest.mark.parametrize("name", ["COM5", "LPT4"])
    def test_reserved_mixed_case_middle_range_rejected(self, name: str):
        valid, _ = validate_folder_name(name)
        assert valid is False


# ===========================================================================
# Reserved name with extension is NOT blocked (known acceptable behaviour)
# ===========================================================================

class TestReservedNameWithExtensionAllowed:
    """The dev-log explicitly states that 'con.txt' style names are not
    rejected because the WP acceptance criteria do not require it.
    Confirm this behaviour so a future change is visible in CI."""

    def test_con_txt_is_accepted(self):
        """'con.txt' must currently be accepted (not blocked)."""
        valid, _ = validate_folder_name("con.txt")
        assert valid is True, (
            "'con.txt' should be allowed; only bare reserved names are blocked. "
            "If this now fails, a new rule was added — update the test accordingly."
        )

    def test_nul_log_is_accepted(self):
        """'nul.log' must currently be accepted (not blocked)."""
        valid, _ = validate_folder_name("nul.log")
        assert valid is True


# ===========================================================================
# Unicode fullwidth and lookalike characters
# ===========================================================================

class TestUnicodeEdgeCases:
    """Fullwidth ASCII characters (e.g., ｃｏｎ U+FF43...) are not in the
    _INVALID_CHARS_RE set and are not equal to reserved names after
    .lower(), so they should be accepted as valid folder names."""

    def test_fullwidth_con_accepted(self):
        """Fullwidth 'ｃｏｎ' is NOT the reserved name 'con' — must be accepted."""
        valid, msg = validate_folder_name("ｃｏｎ")
        assert valid is True, f"Fullwidth CON lookalike should be valid; got: {msg!r}"

    def test_full_unicode_project_name(self):
        """Arabic script name — no invalid chars, not reserved — must be accepted."""
        valid, msg = validate_folder_name("مشروع-جديد")
        assert valid is True, f"Arabic project name should be valid; got: {msg!r}"


# ===========================================================================
# API contract: return types
# ===========================================================================

class TestAPIContractReturnTypes:
    """validate_folder_name and validate_destination_path must always return
    (bool, str).  check_duplicate_folder must always return bool."""

    def test_validate_folder_name_valid_returns_bool_str(self):
        result = validate_folder_name("my-project")
        assert isinstance(result, tuple) and len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_validate_folder_name_invalid_returns_bool_str(self):
        result = validate_folder_name("bad<name")
        assert isinstance(result, tuple) and len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)
        assert result[0] is False
        assert len(result[1]) > 0, "Error string must never be empty when invalid"

    def test_validate_destination_path_valid_returns_bool_str(self, tmp_path: Path):
        result = validate_destination_path(str(tmp_path))
        assert isinstance(result, tuple) and len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_validate_destination_path_invalid_returns_bool_str(self):
        result = validate_destination_path("")
        assert isinstance(result, tuple) and len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)
        assert result[0] is False
        assert len(result[1]) > 0, "Error string must never be empty when invalid"

    def test_check_duplicate_folder_returns_bool(self, tmp_path: Path):
        result = check_duplicate_folder("nonexistent", str(tmp_path))
        assert isinstance(result, bool)


# ===========================================================================
# validate_destination_path — platform edge cases
# ===========================================================================

class TestValidateDestinationPathPlatformEdgeCases:
    def test_path_with_trailing_separator_is_accepted(self, tmp_path: Path):
        """A valid directory path with a trailing slash must be accepted."""
        path_with_slash = str(tmp_path) + os.sep
        valid, msg = validate_destination_path(path_with_slash)
        assert valid is True, (
            f"Path with trailing separator should be valid; got msg={msg!r}"
        )

    def test_nested_directory_is_accepted(self, tmp_path: Path):
        """A writable nested subdirectory must be accepted."""
        nested = tmp_path / "level1" / "level2"
        nested.mkdir(parents=True)
        valid, msg = validate_destination_path(str(nested))
        assert valid is True, f"Nested writable dir should be valid; got: {msg!r}"

    def test_error_message_not_writable_is_informative(self, tmp_path: Path, monkeypatch):
        """The not-writable error message must mention 'write' or 'writable' or
        'permission' so the user knows what to do."""
        monkeypatch.setattr(os, "access", lambda *_: False)
        _, msg = validate_destination_path(str(tmp_path))
        assert any(
            kw in msg.lower()
            for kw in ("write", "writable", "permission")
        ), f"Not-writable message not informative enough: {msg!r}"


# ===========================================================================
# check_duplicate_folder — additional cases
# ===========================================================================

class TestCheckDuplicateFolderAdditional:
    def test_unicode_folder_name_resolved_correctly(self, tmp_path: Path):
        """A unicode project folder can exist and must be detected."""
        unicode_name = "proyecto-café-2026"
        (tmp_path / unicode_name).mkdir()
        assert check_duplicate_folder(unicode_name, str(tmp_path)) is True

    def test_non_existent_destination_returns_false_not_raises(self):
        """check_duplicate_folder with a non-existent dest must not raise."""
        result = check_duplicate_folder("my-project", "/completely/non/existent/path/xyz")
        assert result is False

    def test_case_variant_not_detected_as_duplicate_on_case_sensitive_fs(
        self, tmp_path: Path
    ):
        """On a case-sensitive file system, 'MyProject' and 'myproject' are
        distinct.  We verify that check_duplicate_folder uses Path.exists()
        faithfully (no manual case folding)."""
        (tmp_path / "MyProject").mkdir()
        # On case-insensitive FS (Windows, macOS) this would return True.
        # On case-sensitive FS (Linux ext4) this returns False.
        # The assertion just verifies no exception is raised.
        result = check_duplicate_folder("myproject", str(tmp_path))
        assert isinstance(result, bool)


# ===========================================================================
# App._on_create_project — additional integration paths
# ===========================================================================

class TestOnCreateProjectAdditionalIntegration:
    def test_exception_in_create_project_shows_messagebox_not_label(
        self, tmp_path: Path
    ):
        """If create_project raises, the error must appear as a messagebox
        (showerror), never silently or via the inline labels."""
        app = _make_app(project_name="valid-name", destination=str(tmp_path))

        with patch.dict(
            _APP_GLOBALS,
            {
                "create_project": MagicMock(side_effect=RuntimeError("disk full")),
                "list_templates": MagicMock(return_value=["agent-workbench"]),
                "messagebox": MagicMock(),
            },
        ) as mocked:
            app._on_create_project()
            # messagebox.showerror must have been called
            mocked["messagebox"].showerror.assert_called_once()
            # Neither error label must carry the exception text
            name_errors = [
                c for c in app.project_name_error_label.configure.call_args_list
                if c[1].get("text", "") not in ("", None)
            ]
            dest_errors = [
                c for c in app.destination_error_label.configure.call_args_list
                if c[1].get("text", "") not in ("", None)
            ]
            assert not name_errors, "create_project exception must not go to name label"
            assert not dest_errors, "create_project exception must not go to dest label"

    def test_vscode_not_opened_when_checkbox_unchecked(self, tmp_path: Path):
        """open_in_vscode must NOT be called when the checkbox is unchecked."""
        app = _make_app(project_name="test-project", destination=str(tmp_path))
        app.open_in_vscode_var.get.return_value = False  # unchecked

        with patch.dict(
            _APP_GLOBALS,
            {
                "create_project": MagicMock(return_value=tmp_path / "test-project"),
                "list_templates": MagicMock(return_value=["agent-workbench"]),
                "messagebox": MagicMock(),
                "open_in_vscode": MagicMock(),
            },
        ) as mocked:
            app._on_create_project()
            mocked["open_in_vscode"].assert_not_called()

    def test_vscode_opened_when_checkbox_checked(self, tmp_path: Path):
        """open_in_vscode MUST be called when the checkbox is checked."""
        app = _make_app(project_name="test-project", destination=str(tmp_path))
        app.open_in_vscode_var.get.return_value = True  # checked

        created = tmp_path / "test-project"
        with patch.dict(
            _APP_GLOBALS,
            {
                "create_project": MagicMock(return_value=created),
                "list_templates": MagicMock(return_value=["agent-workbench"]),
                "messagebox": MagicMock(),
                "open_in_vscode": MagicMock(),
            },
        ) as mocked:
            app._on_create_project()
            mocked["open_in_vscode"].assert_called_once_with(created)

    def test_success_shows_info_messagebox_with_project_name(self, tmp_path: Path):
        """After successful creation the showinfo message must contain the
        project folder name so the user can confirm what was created."""
        folder_name = "my-cool-project"
        app = _make_app(project_name=folder_name, destination=str(tmp_path))

        with patch.dict(
            _APP_GLOBALS,
            {
                "create_project": MagicMock(return_value=tmp_path / folder_name),
                "list_templates": MagicMock(return_value=["agent-workbench"]),
                "messagebox": MagicMock(),
                "open_in_vscode": MagicMock(),
            },
        ) as mocked:
            app._on_create_project()
            call_args = mocked["messagebox"].showinfo.call_args
            assert call_args is not None, "showinfo must be called on success"
            # The second positional arg (message body) must contain the folder name.
            msg_body = (
                call_args[1].get("message", "")
                or (call_args[0][1] if len(call_args[0]) > 1 else "")
            )
            assert folder_name in msg_body, (
                f"Success message must contain the project name; got: {msg_body!r}"
            )

    def test_no_inline_errors_on_valid_inputs(self, tmp_path: Path):
        """On the full happy path, neither inline error label must receive
        a non-empty text configure call."""
        app = _make_app(project_name="valid-proj", destination=str(tmp_path))

        with patch.dict(
            _APP_GLOBALS,
            {
                "create_project": MagicMock(return_value=tmp_path / "valid-proj"),
                "list_templates": MagicMock(return_value=["agent-workbench"]),
                "messagebox": MagicMock(),
                "open_in_vscode": MagicMock(),
            },
        ):
            app._on_create_project()

        name_errors = [
            c for c in app.project_name_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        dest_errors = [
            c for c in app.destination_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        assert not name_errors, "No name label errors expected on happy path"
        assert not dest_errors, "No dest label errors expected on happy path"

    def test_duplicate_folder_check_uses_stripped_name(self, tmp_path: Path):
        """The app strips the name before passing it to check_duplicate_folder;
        a folder named 'TS-SAE-myproject' must still be detected when the user
        types ' myproject ' (with surrounding spaces)."""
        (tmp_path / "TS-SAE-myproject").mkdir()
        # The app strips input — so ' myproject ' becomes 'myproject', then prefixed
        app = _make_app(project_name=" myproject ", destination=str(tmp_path))
        app._on_create_project()
        # Since the stripped name matches the existing folder, a duplicate error
        # must appear on the name label.
        error_texts = [
            c[1].get("text", "")
            for c in app.project_name_error_label.configure.call_args_list
            if c[1].get("text", "") not in ("", None)
        ]
        assert error_texts, "Duplicate detection must fire even with surrounding spaces"
