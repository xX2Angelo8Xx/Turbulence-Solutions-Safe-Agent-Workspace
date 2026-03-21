"""SAF-036 conftest: override the global _prevent_hook_state_writes fixture.

SAF-036 tests need direct access to _load_counter_config, _load_state,
_save_state, and _increment_deny_counter.  The global fixture mocks these
to prevent template directory pollution — this local override disables
that mock for SAF-036 tests.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _prevent_hook_state_writes():
    """No-op override: SAF-036 tests manage their own mocking."""
    yield
