"""GUI-015 conftest: make threading.Thread join immediately after start().

FIX-121 refactored _on_create_project to spawn a background thread and use
self._window.after() for UI callbacks.  Tests that call _on_create_project()
directly need the thread to complete before assertions run.  This fixture
patches launcher.gui.app.threading.Thread with a joining stand-in that starts
a real thread (needed for subprocess.Popen pipe reading) but joins it before
start() returns, ensuring synchronous completion from the caller's perspective.
"""

from __future__ import annotations

import threading

import pytest
from unittest.mock import patch

# Capture the REAL Thread class before any patch replaces it.  _JoiningThread
# uses this reference directly so it does not recursively enter _JoiningThread.
_REAL_THREAD = threading.Thread


class _JoiningThread:
    """Drop-in for threading.Thread: starts a real thread and joins it synchronously."""

    def __init__(self, target=None, daemon=None, args=(), kwargs=None, **extra):
        self._thread = _REAL_THREAD(
            target=target,
            args=tuple(args) if args else (),
            kwargs=dict(kwargs) if kwargs else {},
        )
        if daemon is not None:
            self._thread.daemon = daemon

    @property
    def daemon(self) -> bool:
        return self._thread.daemon

    @daemon.setter
    def daemon(self, value: bool) -> None:
        self._thread.daemon = value

    def start(self) -> None:
        self._thread.start()
        self._thread.join()

    def join(self, timeout=None) -> None:
        self._thread.join(timeout=timeout)

    def is_alive(self) -> bool:
        return self._thread.is_alive()


@pytest.fixture(autouse=True)
def _sync_thread():
    """Patch threading.Thread in app.py to join immediately for all GUI-015 tests."""
    with patch("launcher.gui.app.threading.Thread", _JoiningThread):
        yield
