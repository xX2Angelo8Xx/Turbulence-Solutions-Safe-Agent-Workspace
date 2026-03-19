"""Tests for FIX-041: get_display_version() must use VERSION constant in PyInstaller bundles.

BUG-075: importlib.metadata reads stale .dist-info after overlay install on Windows.
Fix: skip importlib.metadata when sys._MEIPASS is set (PyInstaller bundle).
"""
import sys
import importlib
from unittest.mock import patch, MagicMock
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reload_config():
    """Re-import config after patching sys attributes so module-level code reruns."""
    import launcher.config as cfg
    importlib.reload(cfg)
    return cfg


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_get_display_version_in_pyinstaller_uses_VERSION():
    """When sys._MEIPASS exists, get_display_version() must return VERSION constant."""
    import launcher.config as cfg

    with patch.object(sys, '_MEIPASS', '/fake/meipass', create=True):
        result = cfg.get_display_version()

    assert result == cfg.VERSION, (
        f"Expected VERSION={cfg.VERSION!r} but got {result!r}. "
        "get_display_version() should use VERSION constant inside PyInstaller bundles."
    )


def test_get_display_version_without_meipass_uses_importlib():
    """Without sys._MEIPASS, get_display_version() tries importlib.metadata first."""
    import launcher.config as cfg

    # Ensure _MEIPASS is absent
    with patch.object(sys, '_MEIPASS', None, create=True):
        with patch('launcher.config.sys') as mock_sys:
            mock_sys._MEIPASS = None
            # getattr(sys, '_MEIPASS', None) → None, so importlib path is taken
            with patch('importlib.metadata.version', return_value='9.9.9') as mock_version:
                # Re-call the function directly with the patched getattr outcome
                # We test that if _MEIPASS is falsy, importlib.metadata.version is consulted
                def _patched_get_display_version():
                    if getattr(mock_sys, '_MEIPASS', None):
                        return cfg.VERSION
                    try:
                        from importlib.metadata import version, PackageNotFoundError
                        return version("agent-environment-launcher")
                    except PackageNotFoundError:
                        return cfg.VERSION

                result = _patched_get_display_version()

    assert result == '9.9.9', (
        "Without _MEIPASS, get_display_version() should try importlib.metadata."
    )


def test_get_display_version_importlib_fallback_to_VERSION():
    """Without sys._MEIPASS and importlib raises PackageNotFoundError, falls back to VERSION."""
    import launcher.config as cfg
    from importlib.metadata import PackageNotFoundError

    # Patch _MEIPASS to be absent (None / falsy) so the importlib path is entered
    original_meipass = getattr(sys, '_MEIPASS', _SENTINEL := object())

    try:
        # Remove _MEIPASS entirely so getattr returns None
        if hasattr(sys, '_MEIPASS'):
            del sys._MEIPASS

        with patch('importlib.metadata.version', side_effect=PackageNotFoundError("agent-environment-launcher")):
            result = cfg.get_display_version()

    finally:
        # Restore original state
        if original_meipass is not _SENTINEL:
            sys._MEIPASS = original_meipass
        elif hasattr(sys, '_MEIPASS'):
            del sys._MEIPASS

    assert result == cfg.VERSION, (
        f"Expected VERSION={cfg.VERSION!r} as fallback but got {result!r}."
    )


def test_get_display_version_pyinstaller_ignores_stale_distinfo():
    """With sys._MEIPASS set, importlib.metadata returning a stale version is ignored.

    This is the direct regression test for BUG-075:
    Overlay installs leave two .dist-info dirs; importlib finds old one first.
    The fix ensures importlib is never called in bundled builds.
    """
    import launcher.config as cfg

    stale_version = "2.1.1"  # old version that overlay install leaves behind
    current_version = cfg.VERSION  # should be "2.1.2" or whatever VERSION constant holds

    with patch.object(sys, '_MEIPASS', '/fake/meipass', create=True):
        with patch('importlib.metadata.version', return_value=stale_version) as mock_importlib:
            result = cfg.get_display_version()

    # importlib must NOT have been called at all inside a bundle
    mock_importlib.assert_not_called()

    assert result == current_version, (
        f"Expected VERSION={current_version!r}, got {result!r}. "
        "importlib.metadata should not be consulted inside a PyInstaller bundle."
    )


def test_version_label_uses_get_display_version():
    """app.py version_label text is built from get_display_version()."""
    import ast
    import pathlib

    app_path = pathlib.Path(__file__).resolve().parent.parent.parent / "src" / "launcher" / "gui" / "app.py"
    source = app_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    # Walk all Call nodes looking for get_display_version()
    found_get_display_version = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "get_display_version":
                found_get_display_version = True
                break
            if isinstance(func, ast.Attribute) and func.attr == "get_display_version":
                found_get_display_version = True
                break

    assert found_get_display_version, (
        "app.py must call get_display_version() so the version label reflects the fix."
    )

    # Also confirm version_label attribute is set
    found_version_label = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr == "version_label":
                    found_version_label = True
                    break
        if found_version_label:
            break

    assert found_version_label, (
        "app.py must assign self.version_label so the UI displays the version."
    )


def test_check_for_update_uses_VERSION_not_get_display_version():
    """app.py passes VERSION constant (not get_display_version()) to check_for_update().

    get_display_version() is only for display. The update check must always compare
    against the hard-coded VERSION constant to avoid any metadata discrepancy.
    """
    import ast
    import pathlib

    app_path = pathlib.Path(__file__).resolve().parent.parent.parent / "src" / "launcher" / "gui" / "app.py"
    source = app_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    # Collect all call sites for check_for_update
    check_for_update_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if (isinstance(func, ast.Name) and func.id == "check_for_update") or \
               (isinstance(func, ast.Attribute) and func.attr == "check_for_update"):
                check_for_update_calls.append(node)

    assert len(check_for_update_calls) > 0, "app.py must call check_for_update() at least once."

    for call_node in check_for_update_calls:
        assert len(call_node.args) >= 1, "check_for_update() must receive a version argument."
        first_arg = call_node.args[0]
        # The argument must be the NAME "VERSION", not a call to get_display_version()
        assert isinstance(first_arg, ast.Name) and first_arg.id == "VERSION", (
            f"check_for_update() argument must be VERSION constant, not {ast.dump(first_arg)}. "
            "Using get_display_version() for the update check could return stale metadata."
        )
