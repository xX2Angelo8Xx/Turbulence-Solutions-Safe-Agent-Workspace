"""Tests for FIX-075: Fix launcher window title to 'TS - Safe Agent Environment'."""

import ast
from pathlib import Path

import pytest

import launcher.config as config_module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "src" / "launcher" / "config.py"
_APP_PATH = Path(__file__).resolve().parent.parent.parent / "src" / "launcher" / "gui" / "app.py"

_EXPECTED_TITLE = "TS - Safe Agent Environment"
_OLD_TITLE = "Turbulence Solutions Launcher"


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_app_name_value():
    """APP_NAME must equal the new canonical window title."""
    assert config_module.APP_NAME == _EXPECTED_TITLE


def test_app_name_not_old_value():
    """Regression: APP_NAME must not be the old incorrect title."""
    assert config_module.APP_NAME != _OLD_TITLE


def test_no_old_title_in_config_source():
    """The old string must not appear anywhere in config.py source."""
    source = _CONFIG_PATH.read_text(encoding="utf-8")
    assert _OLD_TITLE not in source, (
        f"Old title '{_OLD_TITLE}' still present in config.py"
    )


def test_window_title_set_to_app_name():
    """app.py must pass APP_NAME to self._window.title() — verified via AST."""
    source = _APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    # Walk the AST looking for a Call node: <expr>.title(APP_NAME)
    found = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # Must be an attribute call named 'title'
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "title"):
            continue
        # Must have exactly one argument that is the name APP_NAME
        if len(node.args) == 1 and isinstance(node.args[0], ast.Name):
            if node.args[0].id == "APP_NAME":
                found = True
                break

    assert found, "app.py does not call self._window.title(APP_NAME)"
