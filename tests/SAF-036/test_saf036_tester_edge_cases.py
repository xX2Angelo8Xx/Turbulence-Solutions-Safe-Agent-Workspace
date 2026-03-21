"""tests/SAF-036/test_saf036_tester_edge_cases.py

Tester-added edge-case tests for SAF-036 counter configuration.

Edge cases covered:
  A. threshold=1  — valid lower bound; locks on the very first denial
  B. threshold=-5 — explicitly negative; falls back to defaults
  C. threshold=True  — Python bool (True==1); rejected because isinstance(True, bool)
  D. threshold=False — Python bool (False==0); rejected because isinstance(False, bool)
  E. threshold=None  — null in JSON; falls back to defaults
  F. threshold=[20]  — list; falls back to defaults
  G. counter_enabled=None — non-bool; falls back to default (True)
  H. counter_enabled=1   — integer, not bool; falls back to default (True)
  I. counter_enabled=0   — integer, not bool; falls back to default (True)
  J. Config with ONLY threshold key (missing enabled) — uses default enabled=True
  K. Config with ONLY enabled key (missing threshold) — uses default threshold=20
  L. disabled-only key config — disabled with default threshold
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Make the security_gate module importable
# ---------------------------------------------------------------------------
SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "templates"
    / "coding"
    / ".github"
    / "hooks"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS_DIR))

import security_gate as sg  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_config(tmpdir: str, data: object) -> None:
    config_path = os.path.join(tmpdir, sg._COUNTER_CONFIG_NAME)
    with open(config_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


# ---------------------------------------------------------------------------
# Test A — threshold=1 (valid lower-bound)
# ---------------------------------------------------------------------------

class TestThresholdOne(unittest.TestCase):
    def test_threshold_1_accepted(self) -> None:
        """threshold=1 is the minimum valid value and must NOT fall back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_config(tmpdir, {"counter_enabled": True, "lockout_threshold": 1})
            cfg = sg._load_counter_config(tmpdir)
            self.assertEqual(cfg["lockout_threshold"], 1)
            self.assertTrue(cfg["counter_enabled"])

    def test_threshold_1_locks_on_first_deny(self) -> None:
        """With threshold=1, the first denial must immediately lock the session."""
        state: dict = {}
        session_id = "edge-threshold-1"
        count, locked = sg._increment_deny_counter(state, session_id, 1)
        self.assertEqual(count, 1)
        self.assertTrue(locked, "Session must be locked after 1 denial when threshold=1")


# ---------------------------------------------------------------------------
# Test B — explicitly negative threshold (-5)
# ---------------------------------------------------------------------------

class TestNegativeThreshold(unittest.TestCase):
    def test_negative_5_falls_back(self) -> None:
        """-5 is below minimum 1; must fall back to default threshold=20."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_config(tmpdir, {"counter_enabled": True, "lockout_threshold": -5})
            cfg = sg._load_counter_config(tmpdir)
            self.assertEqual(cfg["lockout_threshold"], sg._DENY_THRESHOLD_DEFAULT)

    def test_negative_1_falls_back(self) -> None:
        """-1 is below minimum 1; must fall back to default threshold=20."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_config(tmpdir, {"counter_enabled": True, "lockout_threshold": -1})
            cfg = sg._load_counter_config(tmpdir)
            self.assertEqual(cfg["lockout_threshold"], sg._DENY_THRESHOLD_DEFAULT)


# ---------------------------------------------------------------------------
# Test C/D — boolean threshold (True/False)
# ---------------------------------------------------------------------------

class TestBooleanThreshold(unittest.TestCase):
    """In Python, bool is a subclass of int (True==1, False==0).
    The config loader must reject booleans because they are semantically
    wrong for a threshold value.  The implementation checks
    `isinstance(threshold, bool)` specifically to catch this case.
    """

    def test_true_threshold_falls_back(self) -> None:
        """threshold=True (bool) must fall back; bool is an int subclass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_config(tmpdir, {"counter_enabled": True, "lockout_threshold": True})
            cfg = sg._load_counter_config(tmpdir)
            self.assertEqual(cfg["lockout_threshold"], sg._DENY_THRESHOLD_DEFAULT)

    def test_false_threshold_falls_back(self) -> None:
        """threshold=False (bool) must fall back to default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_config(tmpdir, {"counter_enabled": True, "lockout_threshold": False})
            cfg = sg._load_counter_config(tmpdir)
            self.assertEqual(cfg["lockout_threshold"], sg._DENY_THRESHOLD_DEFAULT)


# ---------------------------------------------------------------------------
# Test E/F — non-integer threshold (None, list)
# ---------------------------------------------------------------------------

class TestNonIntegerThreshold(unittest.TestCase):
    def test_none_threshold_falls_back(self) -> None:
        """threshold=null in JSON (None in Python) must fall back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_config(tmpdir, {"counter_enabled": True, "lockout_threshold": None})
            cfg = sg._load_counter_config(tmpdir)
            self.assertEqual(cfg["lockout_threshold"], sg._DENY_THRESHOLD_DEFAULT)

    def test_list_threshold_falls_back(self) -> None:
        """threshold=[20] (list) must fall back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_config(tmpdir, {"counter_enabled": True, "lockout_threshold": [20]})
            cfg = sg._load_counter_config(tmpdir)
            self.assertEqual(cfg["lockout_threshold"], sg._DENY_THRESHOLD_DEFAULT)


# ---------------------------------------------------------------------------
# Test G/H/I — non-bool counter_enabled values
# ---------------------------------------------------------------------------

class TestNonBoolEnabled(unittest.TestCase):
    def test_enabled_none_falls_back(self) -> None:
        """counter_enabled=null must fall back to default (True)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_config(tmpdir, {"counter_enabled": None, "lockout_threshold": 20})
            cfg = sg._load_counter_config(tmpdir)
            self.assertEqual(cfg["counter_enabled"], sg._COUNTER_ENABLED_DEFAULT)

    def test_enabled_integer_1_falls_back(self) -> None:
        """counter_enabled=1 (integer, not bool) must fall back to default (True)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_config(tmpdir, {"counter_enabled": 1, "lockout_threshold": 20})
            cfg = sg._load_counter_config(tmpdir)
            self.assertEqual(cfg["counter_enabled"], sg._COUNTER_ENABLED_DEFAULT)

    def test_enabled_integer_0_falls_back(self) -> None:
        """counter_enabled=0 (integer, not bool) must fall back to default (True)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_config(tmpdir, {"counter_enabled": 0, "lockout_threshold": 20})
            cfg = sg._load_counter_config(tmpdir)
            self.assertEqual(cfg["counter_enabled"], sg._COUNTER_ENABLED_DEFAULT)


# ---------------------------------------------------------------------------
# Test J/K/L — partial configs (only one key present)
# ---------------------------------------------------------------------------

class TestPartialConfig(unittest.TestCase):
    def test_only_threshold_key_uses_default_enabled(self) -> None:
        """Config with only 'lockout_threshold' must use default enabled=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_config(tmpdir, {"lockout_threshold": 10})
            cfg = sg._load_counter_config(tmpdir)
            self.assertEqual(cfg["lockout_threshold"], 10)
            self.assertTrue(cfg["counter_enabled"])

    def test_only_enabled_key_uses_default_threshold(self) -> None:
        """Config with only 'counter_enabled' must use default threshold=20."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_config(tmpdir, {"counter_enabled": True})
            cfg = sg._load_counter_config(tmpdir)
            self.assertEqual(cfg["lockout_threshold"], sg._DENY_THRESHOLD_DEFAULT)
            self.assertTrue(cfg["counter_enabled"])

    def test_disabled_only_key_no_threshold(self) -> None:
        """counter_enabled=false with no threshold falls back to default threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_config(tmpdir, {"counter_enabled": False})
            cfg = sg._load_counter_config(tmpdir)
            self.assertFalse(cfg["counter_enabled"])
            self.assertEqual(cfg["lockout_threshold"], sg._DENY_THRESHOLD_DEFAULT)


if __name__ == "__main__":
    unittest.main()
