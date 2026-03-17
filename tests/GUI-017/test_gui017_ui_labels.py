"""Tests for GUI-017 — Update UI Labels and Validation for New Naming Convention.

Verifies that:
1. The project name entry placeholder text is "MatlabDemo".
2. The success message shows "TS-SAE-{folder_name}" in the notification.
3. The duplicate folder check calls check_duplicate_folder with "TS-SAE-{name}".
4. The duplicate error label contains the TS-SAE- prefix.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# Reuse the shared customtkinter mock from conftest.py.
_CTK_MOCK = sys.modules["customtkinter"]

from launcher.gui.app import App  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app(
    project_name: str = "MatlabDemo",
    template_display: str = "Coding",
    destination: str = "",
) -> App:
    """Return a fresh App instance with independent widget mocks.

    All widget attributes are replaced with dedicated MagicMocks to prevent
    return-value bleed between tests.
    """
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


# ---------------------------------------------------------------------------
# Tests: placeholder text
# ---------------------------------------------------------------------------

class TestPlaceholderText:
    def test_placeholder_text_is_matlab_demo(self) -> None:
        """Project name entry placeholder must read 'MatlabDemo' (US-017 example)."""
        with patch("launcher.gui.app.make_label_entry_row") as mock_make_row:
            mock_make_row.return_value = MagicMock()
            _CTK_MOCK.reset_mock()
            app = App()

        # The first call to make_label_entry_row is for the Project Name row.
        first_call_kwargs = mock_make_row.call_args_list[0].kwargs
        assert first_call_kwargs.get("placeholder") == "MatlabDemo", (
            f"Expected placeholder='MatlabDemo', got {first_call_kwargs.get('placeholder')!r}"
        )

    def test_placeholder_is_not_old_value(self) -> None:
        """The old placeholder 'my-project' must no longer be used."""
        with patch("launcher.gui.app.make_label_entry_row") as mock_make_row:
            mock_make_row.return_value = MagicMock()
            _CTK_MOCK.reset_mock()
            App()

        first_call_kwargs = mock_make_row.call_args_list[0].kwargs
        assert first_call_kwargs.get("placeholder") != "my-project", (
            "Old placeholder 'my-project' is still present — not updated."
        )


# ---------------------------------------------------------------------------
# Tests: success message shows TS-SAE prefix
# ---------------------------------------------------------------------------

class TestSuccessMessage:
    def test_success_message_contains_ts_sae_prefix(self, tmp_path: Path) -> None:
        """showinfo must include 'TS-SAE-{folder_name}' in the message body."""
        app = _make_app(project_name="MatlabDemo", destination=str(tmp_path))
        created = tmp_path / "TS-SAE-MatlabDemo"
        created.mkdir()

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=created), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()

        mock_mb.showinfo.assert_called_once()
        _, msg = mock_mb.showinfo.call_args.args
        assert "TS-SAE-MatlabDemo" in msg, (
            f"Expected 'TS-SAE-MatlabDemo' in success message, got: {msg!r}"
        )

    def test_success_message_does_not_show_bare_name_only(self, tmp_path: Path) -> None:
        """The success message must not use only the bare project name without TS-SAE- prefix."""
        app = _make_app(project_name="TestProject", destination=str(tmp_path))
        created = tmp_path / "TS-SAE-TestProject"
        created.mkdir()

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=created), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()

        _, msg = mock_mb.showinfo.call_args.args
        # Message should reference TS-SAE-TestProject, not just "TestProject"
        assert "TS-SAE-TestProject" in msg, (
            f"Success message missing TS-SAE- prefix: {msg!r}"
        )

    def test_success_message_shows_full_created_path(self, tmp_path: Path) -> None:
        """The success message must include the full created_path returned by create_project."""
        app = _make_app(project_name="Alpha", destination=str(tmp_path))
        created = tmp_path / "TS-SAE-Alpha"
        created.mkdir()

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=created), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()

        _, msg = mock_mb.showinfo.call_args.args
        assert str(created) in msg, (
            f"Success message does not include the created path. Message: {msg!r}"
        )


# ---------------------------------------------------------------------------
# Tests: duplicate folder check uses TS-SAE prefix
# ---------------------------------------------------------------------------

class TestDuplicateFolderCheck:
    def test_duplicate_check_called_with_ts_sae_prefix(self, tmp_path: Path) -> None:
        """check_duplicate_folder must be called with 'TS-SAE-{name}', not just '{name}'."""
        app = _make_app(project_name="MatlabDemo", destination=str(tmp_path))

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=True) as mock_dup:
            app._on_create_project()

        mock_dup.assert_called_once_with("TS-SAE-MatlabDemo", str(tmp_path))

    def test_duplicate_check_not_called_with_bare_name(self, tmp_path: Path) -> None:
        """check_duplicate_folder must never be called with the bare unprefixed name."""
        app = _make_app(project_name="Widget", destination=str(tmp_path))

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=True) as mock_dup:
            app._on_create_project()

        # Confirm the first argument passed is the prefixed name.
        actual_name_arg = mock_dup.call_args.args[0]
        assert actual_name_arg == "TS-SAE-Widget", (
            f"Expected 'TS-SAE-Widget', got '{actual_name_arg}'"
        )
        assert actual_name_arg != "Widget", (
            "check_duplicate_folder was called with bare name instead of prefixed name."
        )

    def test_duplicate_error_label_shows_ts_sae_prefix(self, tmp_path: Path) -> None:
        """When a duplicate exists, the error label must mention 'TS-SAE-{name}'."""
        app = _make_app(project_name="MatlabDemo", destination=str(tmp_path))

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=True):
            app._on_create_project()

        configure_calls = app.project_name_error_label.configure.call_args_list
        error_texts = [c.kwargs.get("text", "") for c in configure_calls]
        assert any("TS-SAE-MatlabDemo" in t for t in error_texts), (
            f"Expected TS-SAE-MatlabDemo in error label. Got: {error_texts!r}"
        )

    def test_duplicate_error_label_does_not_use_bare_name(self, tmp_path: Path) -> None:
        """Duplicate error label must not say just '{name}' — must include TS-SAE prefix."""
        app = _make_app(project_name="Bravo", destination=str(tmp_path))

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=True):
            app._on_create_project()

        configure_calls = app.project_name_error_label.configure.call_args_list
        error_texts = [c.kwargs.get("text", "") for c in configure_calls]
        # Filter out empty string (initial clear)
        non_empty = [t for t in error_texts if t]
        assert non_empty, "No non-empty error label text was set."
        assert all("TS-SAE-" in t for t in non_empty), (
            f"Duplicate error label is missing TS-SAE- prefix. Got: {non_empty!r}"
        )


# ---------------------------------------------------------------------------
# Tests: end-to-end — correct project name flows through to success
# ---------------------------------------------------------------------------

class TestEndToEndNaming:
    def test_various_project_names_all_prefixed_in_success_message(self, tmp_path: Path) -> None:
        """Several different project names must all appear with TS-SAE- in success message."""
        names = ["Alpha", "BetaV2", "My_Project123"]
        for name in names:
            app = _make_app(project_name=name, destination=str(tmp_path))
            created = tmp_path / f"TS-SAE-{name}"
            created.mkdir(exist_ok=True)

            with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
                 patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
                 patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
                 patch("launcher.gui.app.list_templates", return_value=["coding"]), \
                 patch("launcher.gui.app.create_project", return_value=created), \
                 patch("launcher.gui.app.messagebox") as mock_mb:
                app._on_create_project()

            _, msg = mock_mb.showinfo.call_args.args
            assert f"TS-SAE-{name}" in msg, (
                f"Expected 'TS-SAE-{name}' in success message, got: {msg!r}"
            )
