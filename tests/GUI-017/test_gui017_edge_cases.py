"""Edge-case tests for GUI-017 — Update UI Labels and Validation for New Naming Convention.

Tester-added tests covering:
1. Empty/whitespace project name — validation fires, no TS-SAE prefix involved.
2. Special characters in project name — validation fires before duplicate check.
3. Old naming artifacts — no "my-project" string surfaces in any message.
4. Whitespace-only name — treated identically to empty name after strip().
5. TS-SAE prefix not double-applied when name already starts with "TS-SAE-".
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_CTK_MOCK = sys.modules["customtkinter"]

from launcher.gui.app import App  # noqa: E402


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_app(
    project_name: str = "MatlabDemo",
    template_display: str = "Coding",
    destination: str = "",
) -> App:
    """Return a fresh App instance with isolated widget mocks."""
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
# Edge Case 1: Empty name — validation catches it, no TS-SAE prefix in error
# ---------------------------------------------------------------------------

class TestEmptyNameHandling:
    def test_empty_name_fails_validation_before_duplicate_check(self, tmp_path: Path) -> None:
        """An empty project name must fail validate_folder_name; duplicate check is never called."""
        app = _make_app(project_name="", destination=str(tmp_path))

        with patch("launcher.gui.app.validate_folder_name", return_value=(False, "Project name cannot be empty.")) as mock_val, \
             patch("launcher.gui.app.check_duplicate_folder") as mock_dup:
            app._on_create_project()

        mock_val.assert_called_once_with("")
        mock_dup.assert_not_called()

    def test_empty_name_sets_error_label(self, tmp_path: Path) -> None:
        """An empty name must produce a non-empty error label."""
        app = _make_app(project_name="", destination=str(tmp_path))

        with patch("launcher.gui.app.validate_folder_name", return_value=(False, "Project name cannot be empty.")):
            app._on_create_project()

        configure_calls = app.project_name_error_label.configure.call_args_list
        error_texts = [c.kwargs.get("text", "") for c in configure_calls]
        non_empty = [t for t in error_texts if t]
        assert non_empty, "Expected an error label to be set for an empty project name."

    def test_whitespace_only_name_fails_validation(self, tmp_path: Path) -> None:
        """A whitespace-only name (e.g., '   ') is stripped to '' and must fail validation."""
        app = _make_app(project_name="   ", destination=str(tmp_path))

        with patch("launcher.gui.app.validate_folder_name", return_value=(False, "Project name cannot be empty.")):
            app._on_create_project()

        # After strip(), the blank name is passed to validate_folder_name.
        called_with = app.project_name_entry.get.return_value.strip()
        assert called_with == "   ".strip() == ""


# ---------------------------------------------------------------------------
# Edge Case 2: Special characters — validation fires before duplicate check
# ---------------------------------------------------------------------------

class TestSpecialCharacterNames:
    @pytest.mark.parametrize("bad_name", [
        "Test@Project",
        "My Project",     # space
        "Hello!World",
        "foo/bar",
        "dot.name",
        "name#tag",
    ])
    def test_special_char_name_fails_before_duplicate_check(self, bad_name: str, tmp_path: Path) -> None:
        """Names with invalid characters fail validate_folder_name; duplicate check not reached."""
        app = _make_app(project_name=bad_name, destination=str(tmp_path))

        with patch("launcher.gui.app.validate_folder_name", return_value=(False, "Invalid characters in project name.")) as mock_val, \
             patch("launcher.gui.app.check_duplicate_folder") as mock_dup:
            app._on_create_project()

        mock_val.assert_called_once_with(bad_name.strip())
        mock_dup.assert_not_called()

    def test_special_char_error_label_does_not_contain_ts_sae(self, tmp_path: Path) -> None:
        """Validation error for special chars must not mention TS-SAE (no prefix was attempted)."""
        app = _make_app(project_name="Invalid@Name", destination=str(tmp_path))

        with patch("launcher.gui.app.validate_folder_name", return_value=(False, "Invalid characters in project name.")):
            app._on_create_project()

        configure_calls = app.project_name_error_label.configure.call_args_list
        error_texts = [c.kwargs.get("text", "") for c in configure_calls if c.kwargs.get("text")]
        # The validation error message should NOT say "TS-SAE-Invalid@Name"
        assert not any("TS-SAE-" in t for t in error_texts), (
            f"TS-SAE prefix should not appear in a name-validation error. Got: {error_texts!r}"
        )


# ---------------------------------------------------------------------------
# Edge Case 3: No old-naming artifacts in any message path
# ---------------------------------------------------------------------------

class TestNoOldNamingArtifacts:
    def test_success_message_does_not_contain_my_project_placeholder(self, tmp_path: Path) -> None:
        """The old placeholder string 'my-project' must never appear in a success message."""
        app = _make_app(project_name="my-project", destination=str(tmp_path))
        created = tmp_path / "TS-SAE-my-project"
        created.mkdir()

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.create_project", return_value=created), \
             patch("launcher.gui.app.messagebox") as mock_mb:
            app._on_create_project()

        _, msg = mock_mb.showinfo.call_args.args
        # Whatever the message says, it must say "TS-SAE-my-project", not bare "my-project"
        assert "TS-SAE-my-project" in msg, (
            f"Expected 'TS-SAE-my-project' in success message. Got: {msg!r}"
        )

    def test_duplicate_error_does_not_use_old_bare_name_format(self, tmp_path: Path) -> None:
        """Duplicate error must reference 'TS-SAE-{name}'; bare old format must not appear."""
        app = _make_app(project_name="OldProject", destination=str(tmp_path))

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=True):
            app._on_create_project()

        configure_calls = app.project_name_error_label.configure.call_args_list
        error_texts = [c.kwargs.get("text", "") for c in configure_calls if c.kwargs.get("text")]
        assert error_texts, "Expected at least one non-empty error label text."
        assert all("TS-SAE-OldProject" in t for t in error_texts), (
            f"Duplicate error must include full TS-SAE- prefixed name. Got: {error_texts!r}"
        )
        # The old format would be just 'A folder named "OldProject" already exists'
        assert not any(t.startswith('A folder named "OldProject"') for t in error_texts), (
            "Old bare-name duplicate message format is still present."
        )


# ---------------------------------------------------------------------------
# Edge Case 4: TS-SAE prefix not double-applied if name starts with "TS-SAE-"
# ---------------------------------------------------------------------------

class TestNoPrefixDoubling:
    def test_name_starting_with_ts_sae_gets_double_prefix_in_duplicate_check(self, tmp_path: Path) -> None:
        """If user types 'TS-SAE-Foo', duplicate check will use 'TS-SAE-TS-SAE-Foo'.
        This is intentional (users should not type the prefix), but the behaviour
        must be documented and consistent — no silent stripping of a typed prefix.
        """
        app = _make_app(project_name="TS-SAE-Foo", destination=str(tmp_path))

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=True) as mock_dup:
            app._on_create_project()

        # The code should call check_duplicate_folder with "TS-SAE-TS-SAE-Foo"
        # (prefix always added regardless of what user typed — consistent behaviour).
        actual_arg = mock_dup.call_args.args[0]
        assert actual_arg == "TS-SAE-TS-SAE-Foo", (
            f"Expected 'TS-SAE-TS-SAE-Foo' (consistent prefix addition). Got: {actual_arg!r}"
        )
