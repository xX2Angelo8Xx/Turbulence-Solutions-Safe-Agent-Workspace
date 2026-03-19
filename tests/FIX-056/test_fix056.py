"""Tests for FIX-056: Deploy ts-python shim in macOS DMG build."""
import os
import sys
import importlib
import tempfile
import types
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
LAUNCHER_SPEC = REPO_ROOT / "launcher.spec"
SHIM_CONFIG = REPO_ROOT / "src" / "launcher" / "core" / "shim_config.py"
MAIN_PY = REPO_ROOT / "src" / "launcher" / "main.py"


# ---------------------------------------------------------------------------
# Test 1: build_dmg.sh contains the shim bundling step
# ---------------------------------------------------------------------------

def test_build_dmg_contains_shim_bundle_step():
    """build_dmg.sh must contain the FIX-056 shim copy into Contents/Resources/shims/."""
    content = BUILD_DMG.read_text(encoding="utf-8")
    assert "Contents/Resources/shims/ts-python" in content, (
        "build_dmg.sh should copy ts-python into Contents/Resources/shims/"
    )


def test_build_dmg_creates_shims_dir():
    """build_dmg.sh must create the shims directory before copying the file."""
    content = BUILD_DMG.read_text(encoding="utf-8")
    assert 'mkdir -p "${APP_BUNDLE}/Contents/Resources/shims"' in content, (
        "build_dmg.sh should create the Resources/shims directory"
    )


def test_build_dmg_sets_shim_executable():
    """build_dmg.sh must set +x on the bundled shim."""
    content = BUILD_DMG.read_text(encoding="utf-8")
    assert "chmod +x" in content and "Resources/shims/ts-python" in content, (
        "build_dmg.sh should chmod +x the bundled shim"
    )


# ---------------------------------------------------------------------------
# Test 2: launcher.spec includes shims in datas
# ---------------------------------------------------------------------------

def test_launcher_spec_includes_shims_in_datas():
    """launcher.spec must include src/installer/shims in the datas list."""
    content = LAUNCHER_SPEC.read_text(encoding="utf-8")
    assert "installer', 'shims'" in content or "installer/shims" in content or "installer\\\\shims" in content, (
        "launcher.spec should bundle src/installer/shims as 'shims' in datas"
    )


# ---------------------------------------------------------------------------
# Test 3–6: shim_config.py contains the required functions
# ---------------------------------------------------------------------------

def test_shim_config_has_ensure_shim_deployed():
    """shim_config.py must define ensure_shim_deployed()."""
    content = SHIM_CONFIG.read_text(encoding="utf-8")
    assert "def ensure_shim_deployed(" in content


def test_shim_config_has_find_bundled_shim():
    """shim_config.py must define _find_bundled_shim()."""
    content = SHIM_CONFIG.read_text(encoding="utf-8")
    assert "def _find_bundled_shim(" in content


def test_shim_config_has_find_bundled_python_exe():
    """shim_config.py must define _find_bundled_python_exe()."""
    content = SHIM_CONFIG.read_text(encoding="utf-8")
    assert "def _find_bundled_python_exe(" in content


def test_shim_config_has_add_to_shell_profile():
    """shim_config.py must define _add_to_shell_profile()."""
    content = SHIM_CONFIG.read_text(encoding="utf-8")
    assert "def _add_to_shell_profile(" in content


# ---------------------------------------------------------------------------
# Test 7: ensure_shim_deployed returns early on Windows
# ---------------------------------------------------------------------------

def test_ensure_shim_deployed_skips_on_windows():
    """ensure_shim_deployed() must return early when platform is Windows."""
    from launcher.core import shim_config

    with patch("launcher.core.shim_config.platform.system", return_value="Windows"):
        with patch.object(shim_config, "get_python_path_config") as mock_cfg:
            shim_config.ensure_shim_deployed()
            # get_python_path_config must NOT be called — we returned before it
            mock_cfg.assert_not_called()


# ---------------------------------------------------------------------------
# Test 8: ensure_shim_deployed returns early when config exists and is non-empty
# ---------------------------------------------------------------------------

def test_ensure_shim_deployed_skips_when_already_configured(tmp_path):
    """ensure_shim_deployed() must skip deployment if python-path.txt exists and is non-empty."""
    from launcher.core import shim_config

    config_file = tmp_path / "python-path.txt"
    config_file.write_text("/usr/bin/python3", encoding="utf-8")

    with patch("launcher.core.shim_config.platform.system", return_value="Darwin"):
        with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
            with patch.object(shim_config, "_find_bundled_shim") as mock_find:
                shim_config.ensure_shim_deployed()
                mock_find.assert_not_called()


# ---------------------------------------------------------------------------
# Test 9: _add_to_shell_profile appends export line to a temp profile
# ---------------------------------------------------------------------------

def test_add_to_shell_profile_appends_export(tmp_path):
    """_add_to_shell_profile() must append export PATH line to an existing profile."""
    from launcher.core.shim_config import _add_to_shell_profile

    profile = tmp_path / ".zshrc"
    profile.write_text("# existing content\n", encoding="utf-8")

    bin_dir = "/home/user/.local/share/TurbulenceSolutions/bin"

    with patch("launcher.core.shim_config.platform.system", return_value="Darwin"):
        with patch("launcher.core.shim_config.Path.home", return_value=tmp_path):
            _add_to_shell_profile(bin_dir)

    result = profile.read_text(encoding="utf-8")
    assert bin_dir in result
    assert "export PATH" in result


# ---------------------------------------------------------------------------
# Test 10: _add_to_shell_profile skips if bin_dir already in profile content
# ---------------------------------------------------------------------------

def test_add_to_shell_profile_skips_if_already_present(tmp_path):
    """_add_to_shell_profile() must not duplicate export line if already present."""
    from launcher.core.shim_config import _add_to_shell_profile

    bin_dir = "/home/user/.local/share/TurbulenceSolutions/bin"
    existing = f'export PATH="$PATH:{bin_dir}"\n'
    profile = tmp_path / ".zshrc"
    profile.write_text(existing, encoding="utf-8")

    with patch("launcher.core.shim_config.platform.system", return_value="Darwin"):
        with patch("launcher.core.shim_config.Path.home", return_value=tmp_path):
            _add_to_shell_profile(bin_dir)

    result = profile.read_text(encoding="utf-8")
    # Should appear exactly once
    assert result.count(bin_dir) == 1


# ---------------------------------------------------------------------------
# Test 11: main.py imports and references ensure_shim_deployed
# ---------------------------------------------------------------------------

def test_main_py_imports_ensure_shim_deployed():
    """main.py must import ensure_shim_deployed from shim_config."""
    content = MAIN_PY.read_text(encoding="utf-8")
    assert "ensure_shim_deployed" in content
    assert "shim_config" in content


# ---------------------------------------------------------------------------
# Tester edge-case tests (FIX-056 Review)
# ---------------------------------------------------------------------------

def test_add_to_shell_profile_skips_nonexistent_file(tmp_path):
    """_add_to_shell_profile() must silently skip profiles that do not exist."""
    from launcher.core.shim_config import _add_to_shell_profile

    bin_dir = "/home/user/.local/share/TurbulenceSolutions/bin"
    # tmp_path exists but contains no .zshrc or .bashrc
    with patch("launcher.core.shim_config.platform.system", return_value="Darwin"):
        with patch("launcher.core.shim_config.Path.home", return_value=tmp_path):
            # Should not raise and should not create any file
            _add_to_shell_profile(bin_dir)

    assert not (tmp_path / ".zshrc").exists()
    assert not (tmp_path / ".bashrc").exists()


def test_add_to_shell_profile_readonly_file_does_not_raise(tmp_path):
    """_add_to_shell_profile() must not raise when profile is read-only."""
    import stat
    from launcher.core.shim_config import _add_to_shell_profile

    bin_dir = "/home/user/.local/share/TurbulenceSolutions/bin"
    profile = tmp_path / ".zshrc"
    profile.write_text("# existing\n", encoding="utf-8")
    # Make read-only
    profile.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    try:
        with patch("launcher.core.shim_config.platform.system", return_value="Darwin"):
            with patch("launcher.core.shim_config.Path.home", return_value=tmp_path):
                # Should swallow the OSError and NOT raise
                _add_to_shell_profile(bin_dir)
    finally:
        # Restore write permission so pytest cleanup can delete the temp dir
        profile.chmod(stat.S_IRUSR | stat.S_IWUSR)


def test_ensure_shim_deployed_returns_early_when_shim_not_found(tmp_path):
    """ensure_shim_deployed() must return early when _find_bundled_shim() returns None."""
    from launcher.core import shim_config

    config_file = tmp_path / "python-path.txt"
    # config does NOT exist so we proceed past the early-exit check

    with patch("launcher.core.shim_config.platform.system", return_value="Darwin"):
        with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
            with patch("launcher.core.shim_config._find_bundled_shim", return_value=None):
                with patch("launcher.core.shim_config._find_bundled_python_exe") as mock_py:
                    shim_config.ensure_shim_deployed()
                    # _find_bundled_python_exe must NOT be called — returned early
                    mock_py.assert_not_called()


def test_ensure_shim_deployed_returns_early_when_python_not_found(tmp_path):
    """ensure_shim_deployed() must return early when _find_bundled_python_exe() returns None."""
    from launcher.core import shim_config

    config_file = tmp_path / "python-path.txt"
    fake_shim = tmp_path / "ts-python"
    fake_shim.write_text("#!/bin/sh\n", encoding="utf-8")

    with patch("launcher.core.shim_config.platform.system", return_value="Darwin"):
        with patch("launcher.core.shim_config.get_python_path_config", return_value=config_file):
            with patch("launcher.core.shim_config._find_bundled_shim", return_value=fake_shim):
                with patch("launcher.core.shim_config._find_bundled_python_exe", return_value=None):
                    with patch("launcher.core.shim_config.get_shim_dir") as mock_dir:
                        shim_config.ensure_shim_deployed()
                        # get_shim_dir (and mkdir/copy) must NOT be called — returned early
                        mock_dir.assert_not_called()


def test_find_bundled_shim_returns_none_without_meipass():
    """_find_bundled_shim() must return None when sys._MEIPASS is not set."""
    from launcher.core.shim_config import _find_bundled_shim
    import sys

    # Ensure _MEIPASS is absent for this test
    had_meipass = hasattr(sys, "_MEIPASS")
    original = getattr(sys, "_MEIPASS", None)
    if had_meipass:
        del sys._MEIPASS
    try:
        result = _find_bundled_shim()
        assert result is None, f"Expected None without _MEIPASS, got {result}"
    finally:
        if had_meipass:
            sys._MEIPASS = original
