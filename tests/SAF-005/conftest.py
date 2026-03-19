"""SAF-005 conftest.py

Compatibility fixture for SAF-005 tests post-SAF-012.

SAF-005 tests use fake workspace paths like '/workspace' that do not exist on
disk. After SAF-012, zone_classifier.detect_project_folder() scans the real
filesystem, so it raises OSError on these fake paths, causing classify() to
return 'deny' instead of 'allow' for project-folder paths.

This fixture patches detect_project_folder to fall back to returning 'project'
when the workspace root does not exist on disk.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _patch_detect_project_folder():
    """Patch zone_classifier.detect_project_folder to handle non-existent workspaces."""
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
