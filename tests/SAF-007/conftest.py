"""SAF-007 conftest.py

Compatibility fixture for SAF-007 tests post-SAF-012.

SAF-007 tests use fake workspace paths like '/workspace' and 'c:/workspace'
that do not exist on disk. After SAF-012, zone_classifier.detect_project_folder()
scans the real filesystem, so it raises OSError on these fake paths, causing
classify() to return 'deny' instead of 'allow' for project-folder paths.

This fixture patches detect_project_folder to fall back to returning 'project'
(the standard folder name used by all SAF-007 tests) when the workspace root
does not exist on disk. This preserves the original test intent without
modifying any existing test file.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _patch_detect_project_folder_for_fake_workspace():
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
            # SAF-007 tests use fake workspace paths that don't exist on disk.
            # Fall back to "project" — the standard folder name used in all SAF-007 tests.
            return "project"

    zc.detect_project_folder = _detect_with_fallback
    try:
        yield
    finally:
        zc.detect_project_folder = original
