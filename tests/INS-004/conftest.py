"""INS-004 conftest: clean template __pycache__ before tests run.

SAF tests import security_gate directly from the templates/agent-workbench
scripts directory at collection time, which creates __pycache__ there.
This conftest removes those artefacts before any INS-004 test executes so
that test_no_pycache_in_template and test_no_pyc_files_in_template pass.
"""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path

import pytest

_TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates" / "agent-workbench"


@pytest.fixture(autouse=True, scope="session")
def _clean_template_pycache():
    """Delete any __pycache__ dirs inside the agent-workbench template."""
    def _onerror(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    for pycache in list(_TEMPLATE_DIR.rglob("__pycache__")):
        if pycache.is_dir():
            shutil.rmtree(str(pycache), onerror=_onerror)
    yield
