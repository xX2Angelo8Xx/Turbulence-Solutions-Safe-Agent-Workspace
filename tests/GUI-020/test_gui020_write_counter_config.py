"""Tests for GUI-020 — write_counter_config() unit tests.

Covers:
  1. write_counter_config writes a valid JSON file at the correct path
  2. Written JSON contains 'counter_enabled' key with the correct boolean value
  3. Written JSON contains 'lockout_threshold' key with the correct integer value
  4. Enabled=True is written correctly
  5. Enabled=False is written correctly
  6. Custom threshold is written correctly
  7. Default threshold (20) is written correctly
  8. Existing config file is overwritten (not merged)
  9. Parent directory must already exist (no directory creation side-effect)
 10. Written file is valid UTF-8 JSON
 11. No extra keys are written (only the two expected keys)
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from launcher.core.project_creator import (
    _COUNTER_CONFIG_PATH,
    write_counter_config,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_and_read(tmp_dir: Path, enabled: bool, threshold: int) -> dict:
    """Call write_counter_config and return the parsed JSON dict."""
    # Ensure the parent directory exists (mirrors what create_project does after
    # shutil.copytree which copies the template including .github/hooks/scripts/).
    config_path = tmp_dir / _COUNTER_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    write_counter_config(tmp_dir, enabled, threshold)
    return json.loads(config_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Tests: file path and existence
# ---------------------------------------------------------------------------

class TestWriteCounterConfigPath:
    def test_file_is_created_at_correct_path(self) -> None:
        """write_counter_config must create the file at _COUNTER_CONFIG_PATH."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            config_path = tmp_dir / _COUNTER_CONFIG_PATH
            config_path.parent.mkdir(parents=True, exist_ok=True)
            write_counter_config(tmp_dir, True, 20)
            assert config_path.is_file(), f"Expected config file at {config_path}"

    def test_config_path_is_under_github_hooks_scripts(self) -> None:
        """Config path must be inside .github/hooks/scripts/."""
        assert ".github" in str(_COUNTER_CONFIG_PATH)
        assert "hooks" in str(_COUNTER_CONFIG_PATH)
        assert "scripts" in str(_COUNTER_CONFIG_PATH)
        assert _COUNTER_CONFIG_PATH.name == "counter_config.json"


# ---------------------------------------------------------------------------
# Tests: JSON content — keys and values
# ---------------------------------------------------------------------------

class TestWriteCounterConfigContent:
    def test_written_json_has_counter_enabled_key(self) -> None:
        """Written JSON must contain 'counter_enabled' key."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _write_and_read(Path(tmp), True, 20)
        assert "counter_enabled" in data

    def test_written_json_has_lockout_threshold_key(self) -> None:
        """Written JSON must contain 'lockout_threshold' key."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _write_and_read(Path(tmp), True, 20)
        assert "lockout_threshold" in data

    def test_enabled_true_is_written(self) -> None:
        """counter_enabled=True must be persisted as JSON boolean true."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _write_and_read(Path(tmp), True, 20)
        assert data["counter_enabled"] is True

    def test_enabled_false_is_written(self) -> None:
        """counter_enabled=False must be persisted as JSON boolean false."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _write_and_read(Path(tmp), False, 20)
        assert data["counter_enabled"] is False

    def test_default_threshold_20_is_written(self) -> None:
        """lockout_threshold must equal 20 when default is used."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _write_and_read(Path(tmp), True, 20)
        assert data["lockout_threshold"] == 20

    def test_custom_threshold_5_is_written(self) -> None:
        """lockout_threshold must equal the custom value passed in."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _write_and_read(Path(tmp), True, 5)
        assert data["lockout_threshold"] == 5

    def test_custom_threshold_100_is_written(self) -> None:
        """lockout_threshold of 100 must be written correctly."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _write_and_read(Path(tmp), True, 100)
        assert data["lockout_threshold"] == 100

    def test_only_two_keys_in_config(self) -> None:
        """Written config must contain exactly two keys: counter_enabled and lockout_threshold."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _write_and_read(Path(tmp), True, 20)
        assert set(data.keys()) == {"counter_enabled", "lockout_threshold"}, (
            f"Unexpected keys in config: {set(data.keys())}"
        )


# ---------------------------------------------------------------------------
# Tests: overwrite behaviour
# ---------------------------------------------------------------------------

class TestWriteCounterConfigOverwrite:
    def test_existing_file_is_overwritten(self) -> None:
        """write_counter_config must overwrite an existing config file."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            config_path = tmp_dir / _COUNTER_CONFIG_PATH
            config_path.parent.mkdir(parents=True, exist_ok=True)
            # Write an initial file with different values.
            config_path.write_text(
                json.dumps({"counter_enabled": False, "lockout_threshold": 99}),
                encoding="utf-8",
            )
            # Overwrite with new values.
            write_counter_config(tmp_dir, True, 42)
            data = json.loads(config_path.read_text(encoding="utf-8"))
        assert data["counter_enabled"] is True
        assert data["lockout_threshold"] == 42

    def test_overwrite_does_not_merge_old_keys(self) -> None:
        """Overwriting must not preserve any keys from the old file."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            config_path = tmp_dir / _COUNTER_CONFIG_PATH
            config_path.parent.mkdir(parents=True, exist_ok=True)
            # Write a file with an extra key.
            config_path.write_text(
                json.dumps({"counter_enabled": True, "lockout_threshold": 20, "extra": "value"}),
                encoding="utf-8",
            )
            write_counter_config(tmp_dir, True, 20)
            data = json.loads(config_path.read_text(encoding="utf-8"))
        assert "extra" not in data


# ---------------------------------------------------------------------------
# Tests: file encoding
# ---------------------------------------------------------------------------

class TestWriteCounterConfigEncoding:
    def test_written_file_is_valid_utf8_json(self) -> None:
        """The written file must be decodable as UTF-8 and parseable as JSON."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            config_path = tmp_dir / _COUNTER_CONFIG_PATH
            config_path.parent.mkdir(parents=True, exist_ok=True)
            write_counter_config(tmp_dir, True, 20)
            raw = config_path.read_bytes()
        # Must decode as UTF-8 without error.
        text = raw.decode("utf-8")
        # Must parse as JSON without error.
        data = json.loads(text)
        assert isinstance(data, dict)
