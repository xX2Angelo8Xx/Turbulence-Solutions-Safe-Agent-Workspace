"""
INS-003 — PyInstaller Config Tests

Verifies that launcher.spec exists at the repository root, is syntactically
valid Python, references the correct entry point, bundles templates/, and
is configured for --onedir mode (not --onefile).
"""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO_ROOT / "launcher.spec"


def _spec_text() -> str:
    return SPEC_PATH.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────

def test_spec_file_exists():
    assert SPEC_PATH.is_file(), "launcher.spec not found at repository root"


# ── Syntax validity ────────────────────────────────────────────────────────────

def test_spec_is_valid_python():
    """ast.parse must succeed — spec file must be syntactically valid Python."""
    try:
        ast.parse(_spec_text())
    except SyntaxError as exc:
        raise AssertionError(f"launcher.spec contains a syntax error: {exc}") from exc


# ── Entry point ────────────────────────────────────────────────────────────────

def test_spec_references_entry_point():
    """The Analysis sources list must reference main.py."""
    assert "main.py" in _spec_text(), (
        "launcher.spec does not reference main.py as the entry point"
    )


def test_spec_entry_point_path_contains_src_launcher():
    """The entry point path must include src/launcher/main.py."""
    content = _spec_text()
    # Accept both forward slash and os.path.join construction.
    assert ("src', 'launcher', 'main.py'" in content) or (
        "src/launcher/main.py" in content
    ), (
        "launcher.spec entry point does not resolve to src/launcher/main.py"
    )


# ── Data bundling ──────────────────────────────────────────────────────────────

def test_spec_includes_templates_in_datas():
    """The datas list must include a 'templates' entry."""
    assert "'templates'" in _spec_text() or '"templates"' in _spec_text(), (
        "launcher.spec datas does not include a templates entry"
    )


# ── Onedir mode ────────────────────────────────────────────────────────────────

def test_spec_uses_onedir_collect():
    """COLLECT() must be present — onedir mode requires it; onefile does not."""
    assert "COLLECT(" in _spec_text(), (
        "launcher.spec missing COLLECT() call — spec is not configured for onedir mode"
    )


def test_spec_exclude_binaries_true():
    """EXE must have exclude_binaries=True — the onedir switch."""
    assert "exclude_binaries=True" in _spec_text(), (
        "launcher.spec does not set exclude_binaries=True in EXE(); "
        "spec is not configured for onedir mode"
    )
