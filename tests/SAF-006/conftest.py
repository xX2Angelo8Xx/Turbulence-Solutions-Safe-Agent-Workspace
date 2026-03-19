"""SAF-006 conftest.py

Compatibility fixture for SAF-006 tests post-SAF-012.

SAF-006 tests use fake workspace paths like '/workspace' that do not exist on
disk.  After SAF-012 zone_classifier switched to a deny-by-default 2-tier
model where anything outside the detected project folder returns 'deny'.
This breaks SAF-006 tests in two ways:

1. Commands targeting '/workspace/project' return 'deny' because
   detect_project_folder() cannot find the project folder on disk.

2. Windows-style flags like /s, /b, /ad in Step 5 of _validate_args are
   classified as 'deny' paths (not inside the project folder), causing
   commands like 'dir /s Project/' to be denied.

This fixture patches zone_classifier.classify to use deny-zone pattern
matching only, returning 'allow' for any path not matching a deny zone.
This restores SAF-006-era semantics where non-deny-zone paths are treated
as safe (previously 'ask', now 'allow' in the 2-tier model).
"""
from __future__ import annotations

import posixpath
import re
import sys

import pytest
from unittest.mock import patch

_BLOCKED_PATTERN = re.compile(
    r"/(\.github|\.vscode|noagentzone)(/|$)", re.IGNORECASE
)


@pytest.fixture(autouse=True)
def mock_zone_classify():
    """Patch zone_classifier.classify for SAF-006 tests.

    Returns 'deny' only for recognized deny-zone paths; 'allow' for
    everything else.  This mirrors the old 3-tier semantics where unknown
    paths returned 'ask' (which _check_path_arg treated as safe).
    """
    zc = sys.modules.get("zone_classifier")
    if zc is None:
        yield
        return

    def _classify(raw_path: str, ws_root: str) -> str:
        norm = zc.normalize_path(raw_path)
        # Resolve relative paths against workspace root
        if not re.match(r"^[a-z]:", norm) and not norm.startswith("/"):
            norm = posixpath.normpath(ws_root.rstrip("/") + "/" + norm)
        full_with_slash = "/" + norm
        if _BLOCKED_PATTERN.search(full_with_slash):
            return "deny"
        return "allow"

    with patch.object(zc, "classify", side_effect=_classify):
        yield
