"""Tests for GUI-008: Version Display.

Verifies that:
  1. get_display_version() is present in config.py and behaves correctly.
  2. version_label exists on the App instance and is non-editable (CTkLabel).
  3. version_label text matches the installed/fallback version string.
  4. Version is shown on startup without user action.

Tests run headlessly by mocking customtkinter. Tests that probe missing
version_label functionality are expected to FAIL until the developer adds
the widget to app.py.
"""

from __future__ import annotations

import re
import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Inject customtkinter mock BEFORE any launcher imports.
# ---------------------------------------------------------------------------
_CTK_MOCK = MagicMock(name="customtkinter")
sys.modules["customtkinter"] = _CTK_MOCK

for _key in [k for k in sys.modules if k.startswith("launcher.gui")]:
    del sys.modules[_key]

_VALIDATION_MOCK = MagicMock(name="launcher.gui.validation")
sys.modules["launcher.gui.validation"] = _VALIDATION_MOCK

from launcher.gui.app import App  # noqa: E402
from launcher import config  # noqa: E402


def _fresh_app() -> App:
    _CTK_MOCK.reset_mock()
    return App()


# ---------------------------------------------------------------------------
# Unit tests — get_display_version() in config.py
# ---------------------------------------------------------------------------

class TestGetDisplayVersion:
    """AC2 & AC4: version comes from metadata or VERSION fallback."""

    def test_function_exists(self):
        assert callable(getattr(config, "get_display_version", None))

    def test_returns_string(self):
        result = config.get_display_version()
        assert isinstance(result, str)

    def test_returns_non_empty_string(self):
        result = config.get_display_version()
        assert len(result.strip()) > 0

    def test_fallback_returns_version_constant(self):
        """AC4: If package metadata unavailable, fall back to VERSION."""
        from importlib.metadata import PackageNotFoundError
        with patch("importlib.metadata.version", side_effect=PackageNotFoundError("agent-environment-launcher")):
            # Evict cached config so get_display_version re-runs the lookup.
            import importlib
            import launcher.config as lc
            result = lc.get_display_version()
        assert result == config.VERSION

    def test_fallback_value_is_semver_like(self):
        """Fallback value must look like X.Y.Z."""
        semver_pattern = re.compile(r"^\d+\.\d+\.\d+")
        assert semver_pattern.match(config.VERSION), \
            f"VERSION '{config.VERSION}' does not look like a version string"

    def test_version_constant_exists(self):
        assert hasattr(config, "VERSION")

    def test_version_constant_is_string(self):
        assert isinstance(config.VERSION, str)

    def test_display_version_matches_version_constant_or_installed(self):
        """Result must equal VERSION constant OR the installed package version."""
        result = config.get_display_version()
        try:
            from importlib.metadata import version as meta_version
            installed = meta_version("agent-environment-launcher")
            assert result == installed or result == config.VERSION
        except Exception:
            assert result == config.VERSION

    def test_exception_does_not_propagate(self):
        """AC4: get_display_version() must never raise — always return a string."""
        from importlib.metadata import PackageNotFoundError
        with patch("importlib.metadata.version", side_effect=PackageNotFoundError):
            import launcher.config as lc
            result = lc.get_display_version()
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Integration tests — version_label widget in App
# ---------------------------------------------------------------------------

class TestVersionLabel:
    """AC1 & AC3: version_label visible, non-editable, present at startup."""

    def test_version_label_attribute_exists(self):
        """AC1: App must expose a version_label attribute after __init__."""
        app = _fresh_app()
        assert hasattr(app, "version_label"), \
            "App.version_label is missing — version_label widget not added to app.py"

    def test_version_label_is_ctk_label_not_entry(self):
        """AC1: version_label must be non-editable (CTkLabel, not CTkEntry)."""
        app = _fresh_app()
        assert hasattr(app, "version_label"), "version_label not found on App"
        # The label must NOT be a CTkEntry instance (editable text field).
        assert not isinstance(app.version_label, _CTK_MOCK.CTkEntry), \
            "version_label must not be a CTkEntry (editable)"

    def test_version_label_grid_called(self):
        """AC3: version_label.grid() must be called during __init__ (placed at startup)."""
        app = _fresh_app()
        assert hasattr(app, "version_label"), "version_label not found on App"
        app.version_label.grid.assert_called(), \
            "version_label.grid() was never called — label not placed in layout"

    def test_version_label_text_contains_version(self):
        """AC2: Text displayed in version_label must contain the display version."""
        app = _fresh_app()
        assert hasattr(app, "version_label"), "version_label not found on App"
        expected_version = config.get_display_version()
        # Check CTkLabel was constructed with text containing the version string.
        label_calls = _CTK_MOCK.CTkLabel.call_args_list
        version_labels = [
            c for c in label_calls
            if expected_version in str(c)
        ]
        assert len(version_labels) >= 1, \
            f"No CTkLabel was created with text containing '{expected_version}'"

    def test_version_label_get_display_version_imported(self):
        """AC2 & AC4: app.py must import get_display_version from config."""
        import ast
        import pathlib
        app_source = pathlib.Path("src/launcher/gui/app.py").read_text(encoding="utf-8")
        tree = ast.parse(app_source)
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "config" in node.module:
                    names = [alias.name for alias in node.names]
                    if "get_display_version" in names:
                        found = True
                        break
        assert found, \
            "app.py does not import get_display_version from launcher.config"
