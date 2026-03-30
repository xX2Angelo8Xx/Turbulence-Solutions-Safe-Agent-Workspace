"""tests/SAF-036/test_saf036_counter_config.py

Tests for counter configuration support (SAF-036).
Validates:
  1. Default config: threshold=20, enabled=true when no config file
  2. Custom threshold: setting threshold=5 locks at 5 denials
  3. Disabled counter: no Block N of M messages, no locking
  4. Corrupt config file: falls back to defaults
  5. Missing config file: falls back to defaults
  6. Config with extra keys: works fine, ignores extras
  7. Config file exists in template directory
"""
from __future__ import annotations

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
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import security_gate as sg  # noqa: E402


# ---------------------------------------------------------------------------
# Test 1 — Default config when no config file exists
# ---------------------------------------------------------------------------

class TestDefaultConfigNoFile(unittest.TestCase):
    def test_defaults_when_no_config_file(self) -> None:
        """When counter_config.json is missing, defaults are used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = sg._load_counter_config(tmpdir)
            self.assertTrue(cfg["counter_enabled"])
            self.assertEqual(cfg["lockout_threshold"], 20)


# ---------------------------------------------------------------------------
# Test 2 — Custom threshold locks at configured value
# ---------------------------------------------------------------------------

class TestCustomThreshold(unittest.TestCase):
    def test_custom_threshold_locks_at_5(self) -> None:
        """Setting threshold=5 should lock after 5 denials."""
        custom_threshold = 5
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, sg._COUNTER_CONFIG_NAME)
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump({"counter_enabled": True, "lockout_threshold": custom_threshold}, fh)

            cfg = sg._load_counter_config(tmpdir)
            self.assertEqual(cfg["lockout_threshold"], custom_threshold)
            self.assertTrue(cfg["counter_enabled"])

            # Verify the counter actually locks at the custom threshold
            state_path = os.path.join(tmpdir, ".hook_state.json")
            session_id = "test-custom-threshold"
            for i in range(custom_threshold):
                state = sg._load_state(state_path)
                # SAF-061: clear timestamp so each call is treated as a separate block
                if session_id in state and isinstance(state[session_id], dict):
                    state[session_id]["timestamp"] = ""
                count, locked = sg._increment_deny_counter(
                    state, session_id, cfg["lockout_threshold"]
                )
                sg._save_state(state_path, state)
                if i < custom_threshold - 1:
                    self.assertFalse(locked)
                else:
                    self.assertTrue(locked)
                    self.assertEqual(count, custom_threshold)


# ---------------------------------------------------------------------------
# Test 3 — Disabled counter: no Block N of M, no locking
# ---------------------------------------------------------------------------

class TestDisabledCounter(unittest.TestCase):
    def test_disabled_counter_no_block_messages(self) -> None:
        """When counter_enabled=false, config returns disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, sg._COUNTER_CONFIG_NAME)
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump({"counter_enabled": False, "lockout_threshold": 20}, fh)

            cfg = sg._load_counter_config(tmpdir)
            self.assertFalse(cfg["counter_enabled"])

    def test_disabled_counter_main_skips_counter(self) -> None:
        """main() with disabled counter should not produce Block N of M."""
        import io

        deny_payload = json.dumps({
            "tool_name": "run_in_terminal",
            "tool_input": {"command": "rm -rf /"},
        })

        disabled_cfg = {"counter_enabled": False, "lockout_threshold": 20}

        with tempfile.TemporaryDirectory() as tmpdir:
            captured = io.StringIO()

            with patch.object(sg, "verify_file_integrity", return_value=True), \
                 patch.object(sg, "_load_counter_config", return_value=disabled_cfg), \
                 patch("sys.stdin", io.StringIO(deny_payload)), \
                 patch("sys.stdout", captured), \
                 patch("os.getcwd", return_value=tmpdir):
                try:
                    sg.main()
                except SystemExit:
                    pass

            output = captured.getvalue()
            self.assertNotIn("Block", output)
            self.assertNotIn("Session locked", output)
            # Should still contain a deny
            self.assertIn("deny", output.lower())

    def test_disabled_counter_no_state_file_written(self) -> None:
        """When counter is disabled, _load_state and _save_state should not be called."""
        import io

        deny_payload = json.dumps({
            "tool_name": "run_in_terminal",
            "tool_input": {"command": "rm -rf /"},
        })

        disabled_cfg = {"counter_enabled": False, "lockout_threshold": 20}

        with tempfile.TemporaryDirectory() as tmpdir:
            captured = io.StringIO()

            with patch.object(sg, "verify_file_integrity", return_value=True), \
                 patch.object(sg, "_load_counter_config", return_value=disabled_cfg), \
                 patch.object(sg, "_load_state", return_value={}) as mock_load, \
                 patch.object(sg, "_save_state") as mock_save, \
                 patch("sys.stdin", io.StringIO(deny_payload)), \
                 patch("sys.stdout", captured), \
                 patch("os.getcwd", return_value=tmpdir):
                try:
                    sg.main()
                except SystemExit:
                    pass

            # _load_state and _save_state should not have been called
            mock_load.assert_not_called()
            mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# Test 4 — Corrupt config file falls back to defaults
# ---------------------------------------------------------------------------

class TestCorruptConfigFallback(unittest.TestCase):
    def test_corrupt_json_falls_back(self) -> None:
        """Corrupt JSON config should fall back to defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, sg._COUNTER_CONFIG_NAME)
            with open(config_path, "w", encoding="utf-8") as fh:
                fh.write("this is not valid json {{{")

            cfg = sg._load_counter_config(tmpdir)
            self.assertTrue(cfg["counter_enabled"])
            self.assertEqual(cfg["lockout_threshold"], 20)

    def test_array_config_falls_back(self) -> None:
        """Config file containing a JSON array should fall back to defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, sg._COUNTER_CONFIG_NAME)
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump([1, 2, 3], fh)

            cfg = sg._load_counter_config(tmpdir)
            self.assertTrue(cfg["counter_enabled"])
            self.assertEqual(cfg["lockout_threshold"], 20)

    def test_empty_file_falls_back(self) -> None:
        """Empty config file should fall back to defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, sg._COUNTER_CONFIG_NAME)
            with open(config_path, "w", encoding="utf-8") as fh:
                pass  # empty file

            cfg = sg._load_counter_config(tmpdir)
            self.assertTrue(cfg["counter_enabled"])
            self.assertEqual(cfg["lockout_threshold"], 20)

    def test_invalid_types_fall_back(self) -> None:
        """Non-bool enabled and non-int threshold should fall back to defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, sg._COUNTER_CONFIG_NAME)
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump({"counter_enabled": "yes", "lockout_threshold": "ten"}, fh)

            cfg = sg._load_counter_config(tmpdir)
            self.assertTrue(cfg["counter_enabled"])
            self.assertEqual(cfg["lockout_threshold"], 20)

    def test_negative_threshold_falls_back(self) -> None:
        """Threshold < 1 should fall back to default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, sg._COUNTER_CONFIG_NAME)
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump({"counter_enabled": True, "lockout_threshold": 0}, fh)

            cfg = sg._load_counter_config(tmpdir)
            self.assertEqual(cfg["lockout_threshold"], 20)

    def test_float_threshold_falls_back(self) -> None:
        """Float threshold (not int) should fall back to default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, sg._COUNTER_CONFIG_NAME)
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump({"counter_enabled": True, "lockout_threshold": 5.5}, fh)

            cfg = sg._load_counter_config(tmpdir)
            self.assertEqual(cfg["lockout_threshold"], 20)


# ---------------------------------------------------------------------------
# Test 5 — Missing config file falls back to defaults
# ---------------------------------------------------------------------------

class TestMissingConfigFallback(unittest.TestCase):
    def test_nonexistent_directory(self) -> None:
        """Config loader with nonexistent directory returns defaults."""
        cfg = sg._load_counter_config("/nonexistent/path/to/scripts")
        self.assertTrue(cfg["counter_enabled"])
        self.assertEqual(cfg["lockout_threshold"], 20)

    def test_empty_directory(self) -> None:
        """Config loader in empty directory returns defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = sg._load_counter_config(tmpdir)
            self.assertTrue(cfg["counter_enabled"])
            self.assertEqual(cfg["lockout_threshold"], 20)


# ---------------------------------------------------------------------------
# Test 6 — Config with extra keys works fine
# ---------------------------------------------------------------------------

class TestExtraKeysIgnored(unittest.TestCase):
    def test_extra_keys_are_ignored(self) -> None:
        """Extra keys in config should be silently ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, sg._COUNTER_CONFIG_NAME)
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump({
                    "counter_enabled": True,
                    "lockout_threshold": 10,
                    "extra_key": "ignored_value",
                    "another_extra": 42,
                }, fh)

            cfg = sg._load_counter_config(tmpdir)
            self.assertTrue(cfg["counter_enabled"])
            self.assertEqual(cfg["lockout_threshold"], 10)
            # The returned dict should only have the two expected keys
            self.assertEqual(set(cfg.keys()), {"counter_enabled", "lockout_threshold"})


# ---------------------------------------------------------------------------
# Test 7 — Config file exists in template directory
# ---------------------------------------------------------------------------

class TestConfigFileExistsInTemplate(unittest.TestCase):
    def test_template_counter_config_exists(self) -> None:
        """counter_config.json must exist in the template scripts directory."""
        config_path = SCRIPTS_DIR / sg._COUNTER_CONFIG_NAME
        self.assertTrue(config_path.is_file(),
                        f"Expected config at {config_path}")

    def test_template_counter_config_valid(self) -> None:
        """The template counter_config.json must be valid JSON with correct keys."""
        config_path = SCRIPTS_DIR / sg._COUNTER_CONFIG_NAME
        with open(config_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertIsInstance(data, dict)
        self.assertIn("counter_enabled", data)
        self.assertIn("lockout_threshold", data)
        self.assertIsInstance(data["counter_enabled"], bool)
        self.assertIsInstance(data["lockout_threshold"], int)
        self.assertTrue(data["counter_enabled"])
        self.assertEqual(data["lockout_threshold"], 20)


if __name__ == "__main__":
    unittest.main()
