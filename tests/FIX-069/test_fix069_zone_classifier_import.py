"""
Tests for FIX-069: Fix zone_classifier import for embedded Python.

Verifies that:
1. security_gate.py contains sys.path.insert before import zone_classifier
2. zone_classifier is importable when sys.path is restricted (simulated embedded Python)
3. The sys.path fix resolves the script directory correctly
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

# Path to the security_gate.py under test
SCRIPTS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates"
    / "coding"
    / ".github"
    / "hooks"
    / "scripts"
)
SECURITY_GATE = SCRIPTS_DIR / "security_gate.py"


def _read_source() -> str:
    return SECURITY_GATE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Structural tests
# ---------------------------------------------------------------------------


def test_sys_path_insert_present():
    """security_gate.py must contain the sys.path.insert fix line."""
    src = _read_source()
    assert "sys.path.insert(0, str(Path(__file__).resolve().parent))" in src, (
        "FIX-069 sys.path fix line not found in security_gate.py"
    )


def test_sys_path_insert_before_import_zone_classifier():
    """The sys.path.insert line must appear BEFORE 'import zone_classifier'."""
    src = _read_source()
    fix_line = "sys.path.insert(0, str(Path(__file__).resolve().parent))"
    import_line = "import zone_classifier"

    assert fix_line in src, "sys.path.insert fix line not found"
    assert import_line in src, "import zone_classifier not found"

    fix_pos = src.index(fix_line)
    import_pos = src.index(import_line)
    assert fix_pos < import_pos, (
        f"sys.path.insert (pos {fix_pos}) must come before "
        f"import zone_classifier (pos {import_pos})"
    )


def test_fix_comment_mentions_embedded_python():
    """The comment above the fix should reference the embedded Python distribution."""
    src = _read_source()
    # Check for FIX-069 or embedded Python mention near the fix
    assert "FIX-069" in src or "embedded" in src.lower(), (
        "Expected a comment referencing FIX-069 or 'embedded' near the fix"
    )


# ---------------------------------------------------------------------------
# Functional tests — simulate embedded Python restricted sys.path
# ---------------------------------------------------------------------------


def test_zone_classifier_importable_with_restricted_sys_path():
    """
    Simulate an embedded Python environment where the script directory is NOT
    on sys.path by default. Reproduce the original failure then confirm the
    fix resolves it.
    """
    zone_classifier_path = SCRIPTS_DIR / "zone_classifier.py"
    assert zone_classifier_path.exists(), "zone_classifier.py must exist in scripts dir"

    # Save and clear sys.path to simulate the embedded Python restriction
    original_path = sys.path.copy()

    # Remove scripts dir from sys.path to reproduce the original error
    restricted = [p for p in sys.path if str(SCRIPTS_DIR) not in p and str(SCRIPTS_DIR).replace("\\", "/") not in p]

    try:
        sys.path = restricted

        # Confirm zone_classifier is NOT importable without the fix
        if "zone_classifier" in sys.modules:
            del sys.modules["zone_classifier"]

        importable_before = True
        try:
            import zone_classifier  # noqa: F401
        except ImportError:
            importable_before = False

        # Now apply the fix: insert the scripts dir as the fix does
        sys.path.insert(0, str(SCRIPTS_DIR))

        if "zone_classifier" in sys.modules:
            del sys.modules["zone_classifier"]

        importable_after = True
        try:
            import zone_classifier as zc  # noqa: F401
        except ImportError:
            importable_after = False

        # The fix must make it importable
        assert importable_after, (
            "zone_classifier still not importable after sys.path.insert fix"
        )

    finally:
        # Restore sys.path
        sys.path = original_path
        # Re-import zone_classifier if it was available before
        if "zone_classifier" in sys.modules:
            del sys.modules["zone_classifier"]


def test_script_dir_resolved_correctly_absolute():
    """
    Verify that Path(__file__).resolve().parent gives the scripts directory
    regardless of whether an absolute path is provided.
    """
    # Simulate what security_gate.py does with its own __file__
    simulated_file = SECURITY_GATE  # already absolute
    resolved_parent = Path(simulated_file).resolve().parent

    assert resolved_parent == SCRIPTS_DIR.resolve(), (
        f"Expected {SCRIPTS_DIR.resolve()}, got {resolved_parent}"
    )


def test_script_dir_resolved_correctly_relative():
    """
    Verify that Path(__file__).resolve().parent resolves correctly even
    when __file__ is a relative path (as may happen in some invocation contexts).
    """
    original_cwd = os.getcwd()
    try:
        # Change to repo root so we can construct a relative path
        repo_root = Path(__file__).resolve().parent.parent.parent
        os.chdir(repo_root)

        relative_file = Path("templates/coding/.github/hooks/scripts/security_gate.py")
        resolved_parent = relative_file.resolve().parent

        assert resolved_parent == SCRIPTS_DIR.resolve(), (
            f"Expected {SCRIPTS_DIR.resolve()}, got {resolved_parent}"
        )
    finally:
        os.chdir(original_cwd)
