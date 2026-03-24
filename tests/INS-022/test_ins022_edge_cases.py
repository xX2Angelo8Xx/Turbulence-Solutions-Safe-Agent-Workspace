"""Edge-case tests for src/launcher/core/user_settings.py (INS-022 — Tester).

Covers:
  - Unicode values and key names
  - Nested dict values
  - Falsy value preservation (False, 0, "", None)
  - PermissionError on read → falls back to defaults
  - PermissionError (write failure via os.replace) → re-raised, temp file cleaned up
  - Concurrent writes with threading → file stays valid JSON
  - Large payload round-trip
  - Windows: missing LOCALAPPDATA fallback
  - JSON keys with special characters (dots, spaces)
  - UnicodeDecodeError on read → falls back to defaults
  - Empty dict saved and loaded correctly
  - Overwrite existing file with different data
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import launcher.core.user_settings as us


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _redirect(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "TurbulenceSolutions" / "settings.json"
    monkeypatch.setattr(us, "_settings_path", lambda: target)
    return target


# ---------------------------------------------------------------------------
# Unicode values
# ---------------------------------------------------------------------------

class TestUnicodeHandling:
    def test_unicode_value_round_trips(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Unicode strings (emoji, CJK) must survive save-load without corruption."""
        _redirect(tmp_path, monkeypatch)
        payload = {"greeting": "こんにちは 🎉", "ar": "مرحبا", "emoji_key": "✅"}
        us.save_settings(payload)
        loaded = us.load_settings()
        assert loaded["greeting"] == "こんにちは 🎉"
        assert loaded["ar"] == "مرحبا"
        assert loaded["emoji_key"] == "✅"

    def test_unicode_key_names_round_trip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Non-ASCII key names must be preserved."""
        _redirect(tmp_path, monkeypatch)
        us.save_settings({"设置": "value", "настройки": 42})
        loaded = us.load_settings()
        assert loaded["设置"] == "value"
        assert loaded["настройки"] == 42

    def test_file_written_as_utf8(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """File on disk must be valid UTF-8 (ensure_ascii=False path)."""
        target = _redirect(tmp_path, monkeypatch)
        us.save_settings({"emoji": "🚀"})
        raw_bytes = target.read_bytes()
        decoded = raw_bytes.decode("utf-8")
        # The emoji should appear verbatim (ensure_ascii=False), not as \\uXXXX.
        assert "🚀" in decoded


# ---------------------------------------------------------------------------
# Nested dict values
# ---------------------------------------------------------------------------

class TestNestedDicts:
    def test_nested_dict_round_trips(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Nested dicts must survive save-load intact."""
        _redirect(tmp_path, monkeypatch)
        payload = {"ui": {"theme": "dark", "font_size": 14}, "network": {"timeout": 30}}
        us.save_settings(payload)
        loaded = us.load_settings()
        assert loaded["ui"] == {"theme": "dark", "font_size": 14}
        assert loaded["network"]["timeout"] == 30

    def test_deeply_nested_dict(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Deeply nested structures must survive unchanged."""
        _redirect(tmp_path, monkeypatch)
        deep = {"a": {"b": {"c": {"d": "leaf"}}}}
        us.save_settings(deep)
        loaded = us.load_settings()
        assert loaded["a"]["b"]["c"]["d"] == "leaf"


# ---------------------------------------------------------------------------
# Falsy value preservation
# ---------------------------------------------------------------------------

class TestFalsyValues:
    def test_false_is_preserved(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Boolean False must not be overwritten by a truthy default."""
        _redirect(tmp_path, monkeypatch)
        us.save_settings({"include_readmes": False})
        loaded = us.load_settings()
        assert loaded["include_readmes"] is False

    def test_zero_is_preserved(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Integer 0 must survive as a setting value."""
        _redirect(tmp_path, monkeypatch)
        us.save_settings({"count": 0})
        loaded = us.load_settings()
        assert loaded["count"] == 0

    def test_empty_string_is_preserved(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty string must survive as a setting value."""
        _redirect(tmp_path, monkeypatch)
        us.save_settings({"label": ""})
        loaded = us.load_settings()
        assert loaded["label"] == ""

    def test_none_value_is_preserved(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """None (JSON null) must survive as a setting value."""
        _redirect(tmp_path, monkeypatch)
        us.save_settings({"nullable": None})
        loaded = us.load_settings()
        assert loaded["nullable"] is None

    def test_empty_list_is_preserved(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty list must survive as a setting value."""
        _redirect(tmp_path, monkeypatch)
        us.save_settings({"items": []})
        loaded = us.load_settings()
        assert loaded["items"] == []


# ---------------------------------------------------------------------------
# Error handling — read-side
# ---------------------------------------------------------------------------

class TestReadErrors:
    def test_permission_error_on_read_returns_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PermissionError while reading the settings file must return defaults."""
        target = _redirect(tmp_path, monkeypatch)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}", encoding="utf-8")

        # Patch Path.read_text to raise PermissionError.
        original_read_text = Path.read_text

        def _raise(*args, **kwargs):
            if args[0] == target:
                raise PermissionError("Access denied")
            return original_read_text(*args, **kwargs)

        monkeypatch.setattr(Path, "read_text", _raise)
        result = us.load_settings()
        assert result == us._DEFAULT_SETTINGS

    def test_unicode_decode_error_returns_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Binary garbage (invalid UTF-8) in the file must return defaults."""
        target = _redirect(tmp_path, monkeypatch)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Write raw bytes that are not valid UTF-8.
        target.write_bytes(b"\xff\xfe invalid utf-8 \x80\x81")
        result = us.load_settings()
        assert result == us._DEFAULT_SETTINGS


# ---------------------------------------------------------------------------
# Error handling — write-side
# ---------------------------------------------------------------------------

class TestWriteErrors:
    def test_permission_error_on_replace_propagates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PermissionError from os.replace must propagate to the caller."""
        _redirect(tmp_path, monkeypatch)
        with patch("launcher.core.user_settings.os.replace",
                   side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                us.save_settings({"include_readmes": True})

    def test_temp_file_cleaned_up_after_write_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No .tmp files must be left behind after a failed save."""
        target = _redirect(tmp_path, monkeypatch)
        with patch("launcher.core.user_settings.os.replace",
                   side_effect=OSError("Disk full")):
            with pytest.raises(OSError):
                us.save_settings({"include_readmes": True})
        tmp_files = list(target.parent.glob("*.tmp"))
        assert tmp_files == [], f"Orphaned temp files found: {tmp_files}"

    def test_original_file_untouched_after_write_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If a write fails, the previous good settings file must be unchanged."""
        target = _redirect(tmp_path, monkeypatch)
        original = {"include_readmes": True, "marker": "original"}
        us.save_settings(original)

        with patch("launcher.core.user_settings.os.replace",
                   side_effect=OSError("Disk full")):
            with pytest.raises(OSError):
                us.save_settings({"include_readmes": False, "marker": "overwrite"})

        # Original file must still be intact.
        data = json.loads(target.read_text(encoding="utf-8"))
        assert data["marker"] == "original"


# ---------------------------------------------------------------------------
# Concurrent writes
# ---------------------------------------------------------------------------

class TestConcurrentWrites:
    def test_concurrent_saves_file_stays_valid_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """After concurrent saves the settings file must remain valid JSON.

        NOTE (known limitation — BUG-INS-022-01): On Windows, os.replace() raises
        PermissionError when two threads simultaneously try to rename to the same
        target path.  save_settings() re-raises such errors by design (the write
        is atomic — the original file is never partially overwritten).  Thread
        safety is NOT guaranteed; callers that require it must add their own
        synchronisation.  This test verifies that even if some saves raise, the
        file on disk is never left in a corrupt state.
        """
        _redirect(tmp_path, monkeypatch)
        us.save_settings({"include_readmes": True})

        def _writer(key: str, value: int) -> None:
            for _ in range(20):
                try:
                    us.set_setting(key, value)
                except (PermissionError, OSError):
                    # Expected on Windows under contention — not a corruption.
                    pass

        threads = [
            threading.Thread(target=_writer, args=(f"key_{i}", i))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # File must still be readable and contain valid JSON (no partial writes).
        target = tmp_path / "TurbulenceSolutions" / "settings.json"
        assert target.exists(), "Settings file must still exist after concurrent writes"
        data = json.loads(target.read_text(encoding="utf-8"))  # must not raise
        assert isinstance(data, dict), "File content must be a JSON object"

        loaded = us.load_settings()
        assert isinstance(loaded, dict)


# ---------------------------------------------------------------------------
# Large payload
# ---------------------------------------------------------------------------

class TestLargePayload:
    def test_large_settings_round_trip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A settings dict with 500 keys must save and load without data loss."""
        _redirect(tmp_path, monkeypatch)
        big = {f"key_{i}": f"value_{i}" for i in range(500)}
        us.save_settings(big)
        loaded = us.load_settings()
        for i in range(500):
            assert loaded[f"key_{i}"] == f"value_{i}"


# ---------------------------------------------------------------------------
# Special JSON key characters
# ---------------------------------------------------------------------------

class TestSpecialKeyCharacters:
    def test_key_with_dots_round_trips(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Keys containing dots must be stored and retrieved as-is."""
        _redirect(tmp_path, monkeypatch)
        us.save_settings({"some.setting.key": "dotted"})
        assert us.get_setting("some.setting.key") == "dotted"

    def test_key_with_spaces_round_trips(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Keys containing spaces must survive the round trip."""
        _redirect(tmp_path, monkeypatch)
        us.save_settings({"key with spaces": 123})
        assert us.get_setting("key with spaces") == 123


# ---------------------------------------------------------------------------
# OS path — Windows LOCALAPPDATA fallback
# ---------------------------------------------------------------------------

class TestWindowsPathFallback:
    def test_windows_path_fallback_when_localappdata_missing(self) -> None:
        """If LOCALAPPDATA is absent, Windows path must fall back to home/AppData/Local."""
        with patch("platform.system", return_value="Windows"):
            env = {k: v for k, v in os.environ.items() if k != "LOCALAPPDATA"}
            with patch.dict(os.environ, env, clear=True):
                with patch("launcher.core.user_settings.Path.home",
                           return_value=Path("C:/Users/TestUser")):
                    path = us._settings_path()
        assert "TurbulenceSolutions" in path.parts
        assert path.name == "settings.json"
        assert "AppData" in path.parts
        assert "Local" in path.parts


# ---------------------------------------------------------------------------
# Empty dict
# ---------------------------------------------------------------------------

class TestEmptyDict:
    def test_empty_dict_save_and_load(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Saving an empty dict must produce a valid file; load merges in defaults."""
        _redirect(tmp_path, monkeypatch)
        us.save_settings({})
        loaded = us.load_settings()
        # Defaults must be merged in.
        assert "include_readmes" in loaded

    def test_overwrite_with_new_data(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Saving twice must replace the previous file content completely."""
        _redirect(tmp_path, monkeypatch)
        us.save_settings({"include_readmes": False, "first": 1})
        us.save_settings({"include_readmes": True, "second": 2})
        loaded = us.load_settings()
        assert loaded["include_readmes"] is True
        assert loaded["second"] == 2
        # "first" key was NOT in the second save, but load preserves extra keys
        # only from disk — since it was replaced, "first" is gone.
        assert "first" not in loaded
