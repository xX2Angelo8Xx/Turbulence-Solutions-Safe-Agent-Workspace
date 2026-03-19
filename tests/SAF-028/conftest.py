"""SAF-028 conftest.py

Same zone_classifier mock as SAF-006: patches classify() to return 'deny'
only for recognised deny-zone paths and 'allow' for everything else.
This allows tests to use the fake _WS_ROOT = "/workspace" path without
requiring real disk layout.
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
    """Patch zone_classifier.classify for SAF-028 tests.

    Returns 'deny' only for recognised deny-zone paths; 'allow' for
    everything else.
    """
    zc = sys.modules.get("zone_classifier")
    if zc is None:
        yield
        return

    def _classify(raw_path: str, ws_root: str) -> str:
        norm = zc.normalize_path(raw_path)
        if not re.match(r"^[a-z]:", norm) and not norm.startswith("/"):
            norm = posixpath.normpath(ws_root.rstrip("/") + "/" + norm)
        full_with_slash = "/" + norm
        if _BLOCKED_PATTERN.search(full_with_slash):
            return "deny"
        return "allow"

    with patch.object(zc, "classify", side_effect=_classify):
        yield
