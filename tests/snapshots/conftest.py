"""Root conftest.py for all snapshot test suites.

SAF-078: registers the --update-snapshots CLI flag so that the flag is
available when running 'pytest tests/snapshots/' or any sub-directory.
The update_snapshots fixture is session-scoped and accessible to every
snapshot test in every sub-directory.
"""
from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help=(
            "Overwrite snapshot expected_decision values with actual results. "
            "Use only for intentional security-decision changes; document every "
            "updated snapshot in dev-log.md under '## Behavior Changes'."
        ),
    )


@pytest.fixture(scope="session")
def update_snapshots(request: pytest.FixtureRequest) -> bool:
    """Return True when --update-snapshots was passed on the command line."""
    return request.config.getoption("--update-snapshots")
