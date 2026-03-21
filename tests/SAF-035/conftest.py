"""SAF-035 conftest: override the global _prevent_hook_state_writes fixture.

SAF-035 tests need direct access to the real _load_state, _save_state, and
_get_session_id functions because they unit-test those functions directly.
The global fixture (tests/conftest.py) mocks them to prevent template
directory pollution — this local override disables that mock for SAF-035.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _prevent_hook_state_writes():
    """No-op override: SAF-035 tests manage their own mocking."""
    yield
