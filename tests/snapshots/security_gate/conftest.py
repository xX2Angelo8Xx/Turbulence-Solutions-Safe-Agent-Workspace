"""conftest.py for security_gate snapshot tests.

Patches zone_classifier.detect_project_folder() so that the fake workspace
root '/workspace' used in snapshot fixtures resolves correctly on all platforms.

SAF-078: --update-snapshots flag and update_snapshots fixture are registered in
the parent tests/snapshots/conftest.py so the flag works at all collection levels.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure security_gate is importable before any test is collected.
_SCRIPTS_DIR = str(
    Path(__file__).resolve().parents[3]
    / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


@pytest.fixture(autouse=True)
def _patch_detect_project_folder():
    """Return 'project' for non-existent fake workspace roots used in snapshots."""
    zc = sys.modules.get("zone_classifier")
    if zc is None:
        yield
        return

    original = zc.detect_project_folder

    def _detect_with_fallback(workspace_root: Path) -> str:
        try:
            return original(workspace_root)
        except (RuntimeError, OSError):
            return "project"

    zc.detect_project_folder = _detect_with_fallback
    try:
        yield
    finally:
        zc.detect_project_folder = original
