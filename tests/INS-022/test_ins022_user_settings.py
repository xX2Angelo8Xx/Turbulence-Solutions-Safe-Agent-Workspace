"""Tests for src/launcher/core/user_settings.py (INS-022)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

import launcher.core.user_settings as us


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_settings_path(tmp_path: Path) -> Path:
    """Return a path inside tmp_path that mimics the settings file location."""
    return tmp_path / "TurbulenceSolutions" / "settings.json"


def _redirect_to_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Patch _settings_path() to point into *tmp_path* and return the path."""
    target = _make_settings_path(tmp_path)
    monkeypatch.setattr(us, "_settings_path", lambda: target)
    return target


# ---------------------------------------------------------------------------
# load_settings
# ---------------------------------------------------------------------------

class TestLoadSettings:
    def test_returns_defaults_when_no_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing settings file must return DEFAULT_SETTINGS without error."""
        _redirect_to_tmp(tmp_path, monkeypatch)
        result = us.load_settings()
        assert result == us._DEFAULT_SETTINGS

    def test_returns_copy_of_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """load_settings should return a new dict, not the module-level constant."""
        _redirect_to_tmp(tmp_path, monkeypatch)
        result = us.load_settings()
        result["include_readmes"] = False
        assert us._DEFAULT_SETTINGS["include_readmes"] is True

    def test_returns_defaults_on_corrupt_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Corrupt JSON must fall back to defaults without raising."""
        target = _redirect_to_tmp(tmp_path, monkeypatch)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("NOT VALID JSON }{", encoding="utf-8")
        result = us.load_settings()
        assert result == us._DEFAULT_SETTINGS

    def test_returns_defaults_on_non_dict_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Valid JSON that is not a dict must fall back to defaults."""
        target = _redirect_to_tmp(tmp_path, monkeypatch)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("[1, 2, 3]", encoding="utf-8")
        result = us.load_settings()
        assert result == us._DEFAULT_SETTINGS

    def test_loads_saved_value(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A value written to disk should be returned by load_settings."""
        target = _redirect_to_tmp(tmp_path, monkeypatch)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"include_readmes": False}), encoding="utf-8")
        result = us.load_settings()
        assert result["include_readmes"] is False

    def test_extra_keys_preserved(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Unknown keys present on disk should survive the load."""
        target = _redirect_to_tmp(tmp_path, monkeypatch)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps({"include_readmes": True, "future_option": 42}),
            encoding="utf-8",
        )
        result = us.load_settings()
        assert result["future_option"] == 42

    def test_missing_key_filled_from_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Keys absent from the file must be supplied from _DEFAULT_SETTINGS."""
        target = _redirect_to_tmp(tmp_path, monkeypatch)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Write an empty dict — include_readmes is absent.
        target.write_text("{}", encoding="utf-8")
        result = us.load_settings()
        assert "include_readmes" in result
        assert result["include_readmes"] is True


# ---------------------------------------------------------------------------
# save_settings
# ---------------------------------------------------------------------------

class TestSaveSettings:
    def test_save_creates_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """save_settings must create the JSON file if it does not exist."""
        target = _redirect_to_tmp(tmp_path, monkeypatch)
        assert not target.exists()
        us.save_settings({"include_readmes": False})
        assert target.exists()

    def test_save_creates_missing_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """save_settings must create the parent directory automatically."""
        target = _redirect_to_tmp(tmp_path, monkeypatch)
        assert not target.parent.exists()
        us.save_settings({"include_readmes": True})
        assert target.parent.is_dir()

    def test_roundtrip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A save followed by a load must return the same dict."""
        _redirect_to_tmp(tmp_path, monkeypatch)
        original = {"include_readmes": False, "extra": "hello"}
        us.save_settings(original)
        loaded = us.load_settings()
        # include_readmes and extra must match; defaults may add extra keys.
        assert loaded["include_readmes"] is False
        assert loaded["extra"] == "hello"

    def test_atomic_write_no_temp_file_left(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """After a successful save, no .tmp sibling files should remain."""
        target = _redirect_to_tmp(tmp_path, monkeypatch)
        us.save_settings({"include_readmes": True})
        tmp_files = list(target.parent.glob("*.tmp"))
        assert tmp_files == []

    def test_file_contains_valid_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The written file must be valid JSON."""
        target = _redirect_to_tmp(tmp_path, monkeypatch)
        us.save_settings({"include_readmes": True})
        data = json.loads(target.read_text(encoding="utf-8"))
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# get_setting
# ---------------------------------------------------------------------------

class TestGetSetting:
    def test_returns_existing_value(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_setting returns the persisted value for a known key."""
        target = _redirect_to_tmp(tmp_path, monkeypatch)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"include_readmes": False}), encoding="utf-8")
        assert us.get_setting("include_readmes") is False

    def test_returns_default_for_missing_key(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_setting falls back to the caller-supplied default."""
        _redirect_to_tmp(tmp_path, monkeypatch)
        result = us.get_setting("nonexistent_key", default="fallback")
        assert result == "fallback"

    def test_default_is_none_when_not_supplied(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_setting default is None when not specified."""
        _redirect_to_tmp(tmp_path, monkeypatch)
        assert us.get_setting("totally_missing") is None


# ---------------------------------------------------------------------------
# set_setting
# ---------------------------------------------------------------------------

class TestSetSetting:
    def test_updates_single_key(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """set_setting must persist a single key without erasing others."""
        _redirect_to_tmp(tmp_path, monkeypatch)
        us.save_settings({"include_readmes": True, "other": "value"})
        us.set_setting("include_readmes", False)
        loaded = us.load_settings()
        assert loaded["include_readmes"] is False
        assert loaded["other"] == "value"

    def test_set_creates_new_key(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """set_setting should add a new key that wasn't previously present."""
        _redirect_to_tmp(tmp_path, monkeypatch)
        us.set_setting("brand_new_key", 99)
        assert us.get_setting("brand_new_key") == 99


# ---------------------------------------------------------------------------
# OS path selection
# ---------------------------------------------------------------------------

class TestSettingsPath:
    def test_windows_path_uses_localappdata(self) -> None:
        """On Windows, path should be under %LOCALAPPDATA%\\TurbulenceSolutions."""
        with patch("platform.system", return_value="Windows"):
            with patch.dict(os.environ, {"LOCALAPPDATA": "C:\\Users\\Test\\AppData\\Local"}):
                path = us._settings_path()
        assert "TurbulenceSolutions" in path.parts
        assert path.name == "settings.json"
        assert str(path).startswith("C:\\Users\\Test\\AppData\\Local")

    def test_linux_path_uses_xdg_config(self) -> None:
        """On Linux, path should be under ~/.config/TurbulenceSolutions."""
        with patch("platform.system", return_value="Linux"):
            # Ensure XDG_CONFIG_HOME is not set so we fall back to ~/.config
            env = {k: v for k, v in os.environ.items() if k != "XDG_CONFIG_HOME"}
            with patch.dict(os.environ, env, clear=True):
                path = us._settings_path()
        assert "TurbulenceSolutions" in path.parts
        assert path.name == "settings.json"
        assert ".config" in path.parts

    def test_linux_path_respects_xdg_config_home(self, tmp_path: Path) -> None:
        """XDG_CONFIG_HOME override must be respected on Linux."""
        custom_config = str(tmp_path / "custom_config")
        with patch("platform.system", return_value="Linux"):
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": custom_config}):
                path = us._settings_path()
        assert str(path).startswith(custom_config)

    def test_macos_path_uses_config_dir(self) -> None:
        """On macOS (Darwin), path should be under ~/.config/TurbulenceSolutions."""
        with patch("platform.system", return_value="Darwin"):
            env = {k: v for k, v in os.environ.items() if k != "XDG_CONFIG_HOME"}
            with patch.dict(os.environ, env, clear=True):
                path = us._settings_path()
        assert "TurbulenceSolutions" in path.parts
        assert path.name == "settings.json"
