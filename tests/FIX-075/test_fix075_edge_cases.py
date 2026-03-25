"""Edge-case tests for FIX-075: Fix launcher window title to 'TS - Safe Agent Environment'."""

import ast
import re
from pathlib import Path

import launcher.config as config_module

_SRC_LAUNCHER = Path(__file__).resolve().parent.parent.parent / "src" / "launcher"
_CONFIG_PATH = _SRC_LAUNCHER / "config.py"
_APP_PATH = _SRC_LAUNCHER / "gui" / "app.py"

_EXPECTED_TITLE = "TS - Safe Agent Environment"
_OLD_TITLE = "Turbulence Solutions Launcher"


# ---------------------------------------------------------------------------
# APP_NAME value shape
# ---------------------------------------------------------------------------

def test_app_name_is_nonempty_string():
    """APP_NAME must be a non-empty string."""
    assert isinstance(config_module.APP_NAME, str)
    assert len(config_module.APP_NAME) > 0


def test_app_name_no_leading_trailing_whitespace():
    """APP_NAME must not have leading or trailing whitespace."""
    assert config_module.APP_NAME == config_module.APP_NAME.strip(), (
        "APP_NAME has unexpected leading/trailing whitespace"
    )


def test_app_name_does_not_contain_word_launcher():
    """New title must not include the word 'Launcher' from the old naming scheme."""
    assert "Launcher" not in config_module.APP_NAME, (
        f"APP_NAME still contains 'Launcher': {config_module.APP_NAME!r}"
    )


def test_app_name_exact_format():
    """APP_NAME must match the exact canonical string (case-sensitive)."""
    assert config_module.APP_NAME == _EXPECTED_TITLE, (
        f"Expected {_EXPECTED_TITLE!r}, got {config_module.APP_NAME!r}"
    )


# ---------------------------------------------------------------------------
# config.py structure
# ---------------------------------------------------------------------------

def test_app_name_defined_exactly_once_in_config():
    """APP_NAME must be assigned exactly once in config.py (no shadowing)."""
    source = _CONFIG_PATH.read_text(encoding="utf-8")
    # Count assignment lines: lines that start (ignoring indent) with APP_NAME =
    matches = re.findall(r"^\s*APP_NAME\s*[:=]", source, re.MULTILINE)
    assert len(matches) == 1, (
        f"APP_NAME defined {len(matches)} times in config.py — expected exactly 1"
    )


# ---------------------------------------------------------------------------
# No old string as a string literal in any src/ Python file
# ---------------------------------------------------------------------------

def _collect_string_literals(tree: ast.AST) -> list[str]:
    """Return all string constant values that are NOT module/class/function docstrings."""
    docstring_nodes: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                docstring_nodes.add(id(node.body[0].value))

    literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) not in docstring_nodes:
                literals.append(node.value)
    return literals


def test_no_old_title_as_string_literal_in_src():
    """No .py file under src/launcher/ may contain the old title as a string literal."""
    offenders: list[str] = []
    for py_file in _SRC_LAUNCHER.rglob("*.py"):
        try:
            source = py_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if _OLD_TITLE not in source:
            continue  # Fast path: old string not even in file text
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue
        for lit in _collect_string_literals(tree):
            if _OLD_TITLE in lit:
                offenders.append(str(py_file.relative_to(_SRC_LAUNCHER.parent.parent)))
                break

    assert not offenders, (
        f"Old title '{_OLD_TITLE}' found as string literal in: {offenders}"
    )


# ---------------------------------------------------------------------------
# app.py integration checks
# ---------------------------------------------------------------------------

def test_app_py_imports_app_name_from_config():
    """app.py must import APP_NAME from launcher.config (not define it locally)."""
    source = _APP_PATH.read_text(encoding="utf-8")
    # Accept both 'from launcher.config import ...' styles
    assert re.search(r"from\s+launcher\.config\s+import\b.*\bAPP_NAME\b", source), (
        "app.py does not import APP_NAME from launcher.config"
    )


def test_app_py_no_hardcoded_title_string():
    """app.py must not hardcode the window title as a literal string."""
    source = _APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_APP_PATH))
    literals = _collect_string_literals(tree)
    hardcoded = [lit for lit in literals if lit == _EXPECTED_TITLE or lit == _OLD_TITLE]
    assert not hardcoded, (
        f"app.py hardcodes a window-title string literal: {hardcoded!r}. "
        "Use APP_NAME from config instead."
    )
