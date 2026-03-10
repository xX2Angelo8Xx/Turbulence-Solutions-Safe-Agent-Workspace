"""Configure pytest so that src/ is on sys.path for all tests.

This is required for the src-layout: packages live under src/ and are not
installed during development unless `pip install -e .` has been run
(deferred to INS-002).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
