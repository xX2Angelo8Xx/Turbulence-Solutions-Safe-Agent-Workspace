"""FIX-092 local conftest: override global safety fixtures.

FIX-092 tests need direct access to subprocess.Popen and shutil.which
since they test the CREATE_NO_WINDOW flag behavior. The global conftest
guards would interfere with monkeypatch-based test doubles.
"""
import pytest


@pytest.fixture(autouse=True)
def _prevent_vscode_launch():
    """FIX-092 override: do not suppress open_in_vscode - we test it here."""
    yield


@pytest.fixture(autouse=True)
def _prevent_vscode_detection():
    """FIX-092 override: do not suppress shutil.which - we mock it ourselves."""
    yield


@pytest.fixture(autouse=True)
def _subprocess_popen_sentinel():
    """FIX-092 override: do not guard subprocess.Popen - we mock it ourselves."""
    yield
