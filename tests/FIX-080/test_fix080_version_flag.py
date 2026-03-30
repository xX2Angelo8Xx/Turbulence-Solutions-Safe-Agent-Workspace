"""Tests for FIX-080: --version flag handled before GUI import in main.py."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# FIX-080 Tests
# ---------------------------------------------------------------------------


def test_version_flag_exits_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """--version must cause SystemExit with code 0."""
    monkeypatch.setattr(sys, "argv", ["agent-launcher", "--version"])
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    import launcher.main as main_mod

    with pytest.raises(SystemExit) as exc_info:
        main_mod.main()

    assert exc_info.value.code == 0


def test_version_flag_prints_version(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """--version must print the VERSION constant."""
    monkeypatch.setattr(sys, "argv", ["agent-launcher", "--version"])
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    import launcher.main as main_mod
    from launcher.config import VERSION

    with pytest.raises(SystemExit):
        main_mod.main()

    captured = capsys.readouterr()
    assert VERSION in captured.out


def test_version_flag_prints_app_name(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """--version must print the APP_NAME constant."""
    monkeypatch.setattr(sys, "argv", ["agent-launcher", "--version"])
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    import launcher.main as main_mod
    from launcher.config import APP_NAME

    with pytest.raises(SystemExit):
        main_mod.main()

    captured = capsys.readouterr()
    assert APP_NAME in captured.out


def test_version_flag_does_not_import_gui(monkeypatch: pytest.MonkeyPatch) -> None:
    """--version must exit before importing launcher.gui.app (no tkinter needed)."""
    monkeypatch.setattr(sys, "argv", ["agent-launcher", "--version"])
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    # Remove launcher.gui.app from sys.modules so any import during main() would
    # re-add it. After --version, it must remain absent.
    gui_mod_key = "launcher.gui.app"
    original = sys.modules.pop(gui_mod_key, None)
    gui_was_imported = False

    import launcher.main as main_mod

    try:
        with pytest.raises(SystemExit) as exc_info:
            main_mod.main()
        # Check BEFORE finally restores the original module.
        gui_was_imported = gui_mod_key in sys.modules
    finally:
        # Restore whatever was there before (if anything).
        if original is not None:
            sys.modules[gui_mod_key] = original
        elif gui_mod_key in sys.modules:
            del sys.modules[gui_mod_key]

    assert exc_info.value.code == 0
    assert not gui_was_imported, (
        "launcher.gui.app should NOT have been imported by --version"
    )


def test_no_version_flag_imports_app(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without --version, main() should proceed to import and run App (mocked here)."""
    monkeypatch.setattr(sys, "argv", ["agent-launcher"])
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    mock_app_instance = MagicMock()
    mock_app_class = MagicMock(return_value=mock_app_instance)

    import launcher.main as main_mod

    with patch.dict(
        sys.modules,
        {
            "launcher.gui.app": MagicMock(App=mock_app_class),
        },
    ):
        with patch.object(main_mod, "ensure_shim_deployed"):
            main_mod.main()

    mock_app_class.assert_called_once()
    mock_app_instance.run.assert_called_once()


def test_short_flag_not_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    """-V (short flag) must NOT trigger the version exit."""
    monkeypatch.setattr(sys, "argv", ["agent-launcher", "-V"])
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    import launcher.main as main_mod

    with patch.dict(
        sys.modules,
        {
            "launcher.gui.app": MagicMock(App=MagicMock(return_value=MagicMock())),
        },
    ):
        with patch.object(main_mod, "ensure_shim_deployed"):
            try:
                main_mod.main()
            except SystemExit as e:
                pytest.fail(f"-V should not cause SystemExit but got SystemExit({e.code})")
