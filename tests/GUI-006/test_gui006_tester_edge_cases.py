"""Tester edge-case tests for GUI-006: VS Code Auto-Open.

Additional tests written by: Tester Agent (2026-03-13)
Covers gaps beyond the Developer's test suite:
 - Direct unit tests of launcher.core.vscode (find_vscode, open_in_vscode)
 - Security: no shell injection via workspace path
 - Duplicate-folder failure gate
 - Call ordering: success messagebox before VS Code launch
 - Exactly-once call guarantee
 - Graceful handling when open_in_vscode returns False at runtime
 - Inline error labels cleared on each attempt

IMPORTANT: open_in_vscode is patched in every test that exercises
_on_create_project(), in addition to the autouse _prevent_vscode_launch
fixture in conftest.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Ensure customtkinter is mocked before any launcher.gui import.
# ---------------------------------------------------------------------------
_CTK_MOCK = MagicMock(name="customtkinter")
sys.modules.setdefault("customtkinter", _CTK_MOCK)

# Remove cached gui modules so they re-import with the mock.
for _key in [k for k in list(sys.modules) if k.startswith("launcher.gui")]:
    del sys.modules[_key]

from launcher.gui.app import App  # noqa: E402

# Bind the real vscode functions at import time so the autouse fixture's
# patch on launcher.core.vscode.open_in_vscode does not prevent us from
# exercising the real function bodies.
from launcher.core.vscode import find_vscode as _real_find_vscode
from launcher.core.vscode import open_in_vscode as _real_open_in_vscode


# ---------------------------------------------------------------------------
# Helper — build a minimal App instance with independent widget mocks.
# ---------------------------------------------------------------------------

def _make_app(
    project_name: str = "my-project",
    template_display: str = "Coding",
    destination: str = "",
    vscode_path: str | None = "/usr/bin/code",
    vscode_checked: bool = True,
) -> App:
    _CTK_MOCK.reset_mock()
    with patch("launcher.gui.app.find_vscode", return_value=vscode_path):
        app = App()
    app.project_name_entry = MagicMock()
    app.project_name_entry.get.return_value = project_name
    app.project_type_dropdown = MagicMock()
    app.project_type_dropdown.get.return_value = template_display
    app.destination_entry = MagicMock()
    app.destination_entry.get.return_value = destination
    app.project_name_error_label = MagicMock()
    app.destination_error_label = MagicMock()
    app.open_in_vscode_var = MagicMock()
    app.open_in_vscode_var.get.return_value = vscode_checked
    app.open_in_vscode_checkbox = MagicMock()
    return app


# ===========================================================================
# 1. Core vscode.py — find_vscode()
# ===========================================================================

class TestFindVSCode:
    """Unit tests for launcher.core.vscode.find_vscode()."""

    def test_returns_none_when_code_not_on_path(self):
        """find_vscode must return None when 'code' is not on PATH."""
        with patch("shutil.which", return_value=None):
            result = _real_find_vscode()
        assert result is None

    def test_returns_path_when_code_found(self):
        """find_vscode must return the executable path when found."""
        with patch("shutil.which", return_value="/usr/bin/code"):
            result = _real_find_vscode()
        assert result == "/usr/bin/code"

    def test_queries_code_executable_specifically(self):
        """find_vscode must look up the 'code' command — not any other name."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/code"
            _real_find_vscode()
        mock_which.assert_called_once_with("code")


# ===========================================================================
# 2. Core vscode.py — open_in_vscode()
# ===========================================================================

class TestOpenInVSCodeCore:
    """Unit tests for launcher.core.vscode.open_in_vscode()."""

    def test_returns_false_when_vscode_not_found(self, tmp_path):
        """open_in_vscode must return False if find_vscode returns None."""
        workspace = tmp_path / "project"
        with patch("launcher.core.vscode.find_vscode", return_value=None):
            result = _real_open_in_vscode(workspace)
        assert result is False

    def test_returns_true_when_vscode_found(self, tmp_path):
        """open_in_vscode must return True on a successful Popen launch."""
        workspace = tmp_path / "project"
        with patch("launcher.core.vscode.find_vscode", return_value="/usr/bin/code"), \
             patch("launcher.core.vscode.subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            result = _real_open_in_vscode(workspace)
        assert result is True

    def test_no_subprocess_call_when_vscode_not_found(self, tmp_path):
        """subprocess.Popen must NOT be called when VS Code is absent."""
        workspace = tmp_path / "project"
        with patch("launcher.core.vscode.find_vscode", return_value=None), \
             patch("launcher.core.vscode.subprocess.Popen") as mock_popen:
            _real_open_in_vscode(workspace)
        mock_popen.assert_not_called()

    def test_popen_receives_list_not_string(self, tmp_path):
        """Security: Popen must receive a list of arguments, not a shell string."""
        workspace = tmp_path / "project"
        with patch("launcher.core.vscode.find_vscode", return_value="/usr/bin/code"), \
             patch("launcher.core.vscode.subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            _real_open_in_vscode(workspace)
        positional_args, _ = mock_popen.call_args
        assert isinstance(positional_args[0], list), (
            "Popen must receive a list (not a string) to prevent shell splitting"
        )

    def test_popen_not_called_with_shell_true(self, tmp_path):
        """Security: shell=True must never be passed to Popen."""
        workspace = tmp_path / "project"
        with patch("launcher.core.vscode.find_vscode", return_value="/usr/bin/code"), \
             patch("launcher.core.vscode.subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            _real_open_in_vscode(workspace)
        _, kwargs = mock_popen.call_args
        assert kwargs.get("shell", False) is False, "shell=True must never be used"

    def test_popen_receives_correct_executable(self, tmp_path):
        """Popen must be called with the exact path returned by find_vscode."""
        workspace = tmp_path / "project"
        with patch("launcher.core.vscode.find_vscode", return_value="/custom/bin/code"), \
             patch("launcher.core.vscode.subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            _real_open_in_vscode(workspace)
        args_list = mock_popen.call_args[0][0]
        assert args_list[0] == "/custom/bin/code"

    def test_popen_receives_workspace_as_string(self, tmp_path):
        """Popen must receive the workspace path as a str, not a Path object."""
        workspace = tmp_path / "my-project"
        with patch("launcher.core.vscode.find_vscode", return_value="/usr/bin/code"), \
             patch("launcher.core.vscode.subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            _real_open_in_vscode(workspace)
        args_list = mock_popen.call_args[0][0]
        assert isinstance(args_list[1], str), "workspace path must be str, not Path"
        assert args_list[1] == str(workspace)


# ===========================================================================
# 3. Security — no command injection via workspace path
# ===========================================================================

class TestVSCodeNoCommandInjection:
    """Verify the workspace path cannot cause command injection."""

    def test_path_with_spaces_not_split(self, tmp_path):
        """A path containing spaces must be a single arg — not split by the shell."""
        workspace = tmp_path / "my project with spaces"
        with patch("launcher.core.vscode.find_vscode", return_value="/usr/bin/code"), \
             patch("launcher.core.vscode.subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            _real_open_in_vscode(workspace)
        args_list = mock_popen.call_args[0][0]
        assert len(args_list) == 2, (
            "Popen args must be exactly [exe, path] — spaces must not split the path"
        )

    def test_path_with_semicolons_passed_verbatim(self):
        """A path with semicolons must be one arg — no shell command chaining."""
        workspace = Path("/tmp/project;malicious-command")
        with patch("launcher.core.vscode.find_vscode", return_value="/usr/bin/code"), \
             patch("launcher.core.vscode.subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            _real_open_in_vscode(workspace)
        args_list = mock_popen.call_args[0][0]
        # Exactly two args; the path element equals the full string
        assert len(args_list) == 2
        assert args_list[1] == str(workspace)

    def test_path_with_double_dash_flags_not_interpreted(self, tmp_path):
        """A path that looks like a flag must be passed as the path argument."""
        workspace = tmp_path / "--extensions-dir"
        with patch("launcher.core.vscode.find_vscode", return_value="/usr/bin/code"), \
             patch("launcher.core.vscode.subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            _real_open_in_vscode(workspace)
        args_list = mock_popen.call_args[0][0]
        assert len(args_list) == 2
        assert args_list[1] == str(workspace)


# ===========================================================================
# 4. GUI — duplicate folder failure stops execution before VS Code
# ===========================================================================

class TestVSCodeNotCalledOnDuplicateFolder:
    """open_in_vscode must not be called when a duplicate folder is detected."""

    def test_not_called_when_duplicate_folder_check_fails(self, tmp_path):
        app = _make_app(project_name="existing", destination=str(tmp_path), vscode_checked=True)
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=True), \
             patch("launcher.gui.app.open_in_vscode") as mock_open:
            app._on_create_project()
        mock_open.assert_not_called()


# ===========================================================================
# 5. GUI — call ordering: success dialog shown before VS Code launch
# ===========================================================================

class TestVSCodeCallOrdering:
    """messagebox.showinfo must appear before open_in_vscode is invoked."""

    def test_success_message_shown_before_vscode_opened(self, tmp_path):
        created = tmp_path / "my-project"
        call_order: list[str] = []

        app = _make_app(project_name="my-project", destination=str(tmp_path), vscode_checked=True)
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=created), \
             patch("launcher.gui.app.messagebox") as mock_mb, \
             patch("launcher.gui.app.open_in_vscode") as mock_open:
            mock_mb.showinfo.side_effect = lambda *a, **kw: call_order.append("showinfo")
            mock_open.side_effect = lambda *a, **kw: call_order.append("open_in_vscode")
            app._on_create_project()

        assert call_order == ["showinfo", "open_in_vscode"], (
            "messagebox.showinfo must be called before open_in_vscode"
        )


# ===========================================================================
# 6. GUI — open_in_vscode called exactly once per successful creation
# ===========================================================================

class TestOpenInVSCodeCalledExactlyOnce:
    def test_called_exactly_once_on_success(self, tmp_path):
        created = tmp_path / "my-project"
        app = _make_app(project_name="my-project", destination=str(tmp_path), vscode_checked=True)
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=created), \
             patch("launcher.gui.app.messagebox"), \
             patch("launcher.gui.app.open_in_vscode") as mock_open:
            app._on_create_project()
        assert mock_open.call_count == 1, "open_in_vscode must be called exactly once"


# ===========================================================================
# 7. GUI — app does not crash when open_in_vscode returns False at runtime
# ===========================================================================

class TestOpenInVSCodeReturnValueHandling:
    """The return value of open_in_vscode is discarded — app must not raise."""

    def test_no_exception_when_open_in_vscode_returns_false(self, tmp_path):
        created = tmp_path / "my-project"
        app = _make_app(project_name="my-project", destination=str(tmp_path), vscode_checked=True)
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=created), \
             patch("launcher.gui.app.messagebox"), \
             patch("launcher.gui.app.open_in_vscode", return_value=False):
            # Must complete without raising
            app._on_create_project()


# ===========================================================================
# 8. GUI — inline error labels cleared at the start of each create attempt
# ===========================================================================

class TestInlineErrorsCleared:
    """Both error labels must be cleared to '' before each create attempt."""

    def test_name_error_label_cleared_on_success_path(self, tmp_path):
        app = _make_app(project_name="my-project", destination=str(tmp_path), vscode_checked=True)
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=(tmp_path / "my-project")), \
             patch("launcher.gui.app.messagebox"), \
             patch("launcher.gui.app.open_in_vscode"):
            app._on_create_project()
        cleared = any(
            c == call(text="") for c in app.project_name_error_label.configure.call_args_list
        )
        assert cleared, "project_name_error_label must be reset to '' on each attempt"

    def test_destination_error_label_cleared_on_success_path(self, tmp_path):
        app = _make_app(project_name="my-project", destination=str(tmp_path), vscode_checked=True)
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=(tmp_path / "my-project")), \
             patch("launcher.gui.app.messagebox"), \
             patch("launcher.gui.app.open_in_vscode"):
            app._on_create_project()
        cleared = any(
            c == call(text="") for c in app.destination_error_label.configure.call_args_list
        )
        assert cleared, "destination_error_label must be reset to '' on each attempt"


# ===========================================================================
# 9. GUI — checkbox disabled state does NOT suppress the success message
# ===========================================================================

class TestSuccessMessageWithCheckboxUnchecked:
    """Success dialog must still appear even when the VS Code checkbox is off."""

    def test_success_info_shown_even_when_checkbox_unchecked(self, tmp_path):
        created = tmp_path / "my-project"
        app = _make_app(project_name="my-project", destination=str(tmp_path), vscode_checked=False)
        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=created), \
             patch("launcher.gui.app.messagebox") as mock_mb, \
             patch("launcher.gui.app.open_in_vscode"):
            app._on_create_project()
        mock_mb.showinfo.assert_called_once()
