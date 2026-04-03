"""SAF-025 test configuration.

Cleans up __pycache__ created when pytest imports security_gate from the
templates directory.  Without this, test_no_pycache_in_templates_coding
always fails because the module-level import fires before any test runs.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

_TC_SCRIPTS = (
    Path(__file__).resolve().parent.parent.parent
    / "templates"
    / "agent-workbench"
    / ".github"
    / "hooks"
    / "scripts"
)


@pytest.fixture(autouse=True)
def _cleanup_pycache():
    """Remove __pycache__ from the templates scripts dir before each test."""
    pycache = _TC_SCRIPTS / "__pycache__"
    if pycache.exists():
        shutil.rmtree(pycache)
    yield
    # Also clean after, so subsequent tests start fresh.
    if pycache.exists():
        shutil.rmtree(pycache)
