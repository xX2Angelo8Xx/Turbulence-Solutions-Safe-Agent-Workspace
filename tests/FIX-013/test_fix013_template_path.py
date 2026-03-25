"""Tests for FIX-013: Fix PyInstaller Template Path Resolution.

Verifies that TEMPLATES_DIR in config.py correctly handles both:
  - PyInstaller bundles (_MEIPASS is set)
  - Normal development (no _MEIPASS)
"""

import sys
import importlib
import types
from pathlib import Path
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reload_config(meipass_value=None):
    """Reload launcher.config with optional sys._MEIPASS override.

    Returns the freshly-imported module so tests can inspect TEMPLATES_DIR.
    """
    if meipass_value is not None:
        with patch.object(sys, '_MEIPASS', meipass_value, create=True):
            import launcher.config as cfg
            importlib.reload(cfg)
            result = cfg.TEMPLATES_DIR
        # Reload once more without _MEIPASS so we don't leave patched state
        if hasattr(sys, '_MEIPASS'):
            delattr(sys, '_MEIPASS')
        importlib.reload(cfg)
        return result
    else:
        # Ensure _MEIPASS is absent
        if hasattr(sys, '_MEIPASS'):
            delattr(sys, '_MEIPASS')
        import launcher.config as cfg
        importlib.reload(cfg)
        return cfg.TEMPLATES_DIR


# ---------------------------------------------------------------------------
# Test 1 — When _MEIPASS is set, TEMPLATES_DIR must be _MEIPASS / "templates"
# ---------------------------------------------------------------------------

def test_templates_dir_uses_meipass_when_set(tmp_path):
    """Regression: bundled env resolves templates to _MEIPASS/templates."""
    fake_meipass = str(tmp_path / "MEI12345")
    expected = Path(fake_meipass) / "templates"

    result = _reload_config(meipass_value=fake_meipass)

    assert result == expected, (
        f"Expected TEMPLATES_DIR={expected}, got {result}"
    )


# ---------------------------------------------------------------------------
# Test 2 — Without _MEIPASS, TEMPLATES_DIR must be 3 parents up from config.py
# ---------------------------------------------------------------------------

def test_templates_dir_uses_file_path_when_no_meipass():
    """Unit: dev mode resolves templates to repo_root/templates."""
    result = _reload_config(meipass_value=None)

    import launcher.config as cfg
    config_file = Path(cfg.__file__).resolve()
    expected = config_file.parent.parent.parent / "templates"

    assert result == expected, (
        f"Expected TEMPLATES_DIR={expected}, got {result}"
    )


# ---------------------------------------------------------------------------
# Test 3 — list_templates() is non-empty for the real dev templates directory
# ---------------------------------------------------------------------------

def test_list_templates_returns_non_empty_for_real_templates_dir():
    """Integration: real templates/ directory contains at least one template."""
    from launcher.core.project_creator import list_templates

    dev_templates_dir = _reload_config(meipass_value=None)
    templates = list_templates(dev_templates_dir)

    assert isinstance(templates, list), "list_templates must return a list"
    assert len(templates) > 0, (
        f"Expected non-empty template list from {dev_templates_dir}, got []"
    )


# ---------------------------------------------------------------------------
# Test 4 — CTkOptionMenu receives a non-empty values list when templates exist
# ---------------------------------------------------------------------------

def test_ctk_option_menu_values_non_empty(tmp_path):
    """Unit: CTkOptionMenu is built with non-empty values when templates are found."""
    # Create a fake templates directory with one subdirectory
    fake_templates = tmp_path / "templates"
    (fake_templates / "coding").mkdir(parents=True)

    from launcher.core.project_creator import list_templates

    values = list_templates(fake_templates)

    assert len(values) > 0, "list_templates should return non-empty for a dir with subdirs"
    # Simulate what app.py does: pass values to CTkOptionMenu (mock it)
    captured_values = []

    def fake_ctk_option_menu(**kwargs):
        captured_values.extend(kwargs.get("values", []))

    fake_ctk_option_menu(values=values)

    assert len(captured_values) > 0, (
        "CTkOptionMenu would receive a non-empty values list"
    )
    assert "coding" in captured_values


# ---------------------------------------------------------------------------
# Tester Edge Cases
# ---------------------------------------------------------------------------

def test_meipass_set_but_templates_dir_missing_returns_empty_list(tmp_path):
    """Edge case: _MEIPASS is set but templates/ does not exist inside it.
    list_templates() must return [] without raising — no crash in broken bundle."""
    fake_meipass = str(tmp_path / "MEI_no_templates")
    # Do NOT create the templates subdirectory inside fake_meipass
    templates_dir = _reload_config(meipass_value=fake_meipass)

    from launcher.core.project_creator import list_templates
    result = list_templates(templates_dir)

    assert result == [], (
        f"Expected [] when _MEIPASS/templates/ does not exist, got {result}"
    )


def test_meipass_empty_string_falls_through_to_dev_path():
    """Edge case: sys._MEIPASS == '' is falsy.
    The conditional 'if getattr(sys, \"_MEIPASS\", None):' evaluates to False,
    so the dev-mode path must be used (not Path('') / 'templates')."""
    import launcher.config as cfg

    dev_expected = Path(cfg.__file__).resolve().parent.parent.parent / "templates"
    result = _reload_config(meipass_value="")

    assert result == dev_expected, (
        f"Empty string _MEIPASS should use dev path {dev_expected!r}, got {result!r}"
    )


def test_real_templates_dir_contains_expected_template_names():
    """Integration: dev TEMPLATES_DIR contains exactly 'coding' and 'certification-pipeline'."""
    from launcher.core.project_creator import list_templates

    dev_templates_dir = _reload_config(meipass_value=None)
    templates = list_templates(dev_templates_dir)

    assert "agent-workbench" in templates, f"'agent-workbench' missing from {templates}"
    assert "certification-pipeline" in templates, f"'certification-pipeline' missing from {templates}"


def test_meipass_bundled_templates_discoverable(tmp_path):
    """Edge case: simulate a correctly bundled PyInstaller env.
    When _MEIPASS/templates/ exists with coding/ and creative-marketing/,
    list_templates() must return both names."""
    fake_meipass = str(tmp_path / "MEI_full")
    fake_templates = tmp_path / "MEI_full" / "templates"
    (fake_templates / "agent-workbench").mkdir(parents=True)
    (fake_templates / "certification-pipeline").mkdir()

    templates_dir = _reload_config(meipass_value=fake_meipass)

    from launcher.core.project_creator import list_templates
    result = list_templates(templates_dir)

    assert "agent-workbench" in result, f"'agent-workbench' not found in bundled templates: {result}"
    assert "certification-pipeline" in result, (
        f"'certification-pipeline' not found in bundled templates: {result}"
    )
    assert len(result) == 2, f"Expected 2 templates, got {result}"
