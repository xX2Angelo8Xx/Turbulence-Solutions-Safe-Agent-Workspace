"""SAF-062 conftest: override the global _prevent_hook_state_writes fixture.

SAF-062 tests import security_gate directly to validate the _PROJECT_FALLBACK_VERBS
frozenset and the sanitize_terminal_command function.  The global fixture mocks
hook state writes to prevent template directory pollution — this local override
disables that mock for SAF-062 tests.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _prevent_hook_state_writes():
    """No-op override: SAF-062 tests manage their own mocking."""
    yield
