"""SAF-021 conftest.py

Same fake-workspace patch as SAF-020: tests use 'c:/workspace' which does not
exist on disk.  After SAF-012, zone_classifier.detect_project_folder() scans
the real filesystem, raising OSError on non-existent paths and causing
classify() to return 'deny' instead of 'allow' for project-folder paths.

This fixture patches detect_project_folder to fall back to 'project' when the
workspace root does not exist, preserving the original test intent without
modifying any test file.
"""
from __future__ import annotations

import sys

import pytest


@pytest.fixture(autouse=True)
def _patch_detect_project_folder_for_fake_workspace():
    """Patch zone_classifier.detect_project_folder for non-existent workspaces."""
    zc = sys.modules.get("zone_classifier")
    if zc is None:
        yield
        return

    original = zc.detect_project_folder

    def _detect_with_fallback(workspace_root):
        try:
            return original(workspace_root)
        except (RuntimeError, OSError):
            return "project"

    zc.detect_project_folder = _detect_with_fallback
    try:
        yield
    finally:
        zc.detect_project_folder = original
