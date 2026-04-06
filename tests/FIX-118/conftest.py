"""FIX-118 conftest.py

Patches zone_classifier.detect_project_folder to return 'project' for the
fake workspace root used in these tests, avoiding real filesystem access.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_project_folder():
    """Return 'project' as the project folder without touching the disk."""
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield
