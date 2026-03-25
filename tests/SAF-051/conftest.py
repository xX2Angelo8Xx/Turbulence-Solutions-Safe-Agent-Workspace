"""tests/SAF-051/conftest.py

Override the global _prevent_hook_state_writes fixture so SAF-051 tests
can call _get_session_id directly without interference.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _prevent_hook_state_writes():
    """No-op override: SAF-051 tests manage their own mocking."""
    yield
