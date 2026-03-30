"""Edge-case tests for FIX-080: --version flag handling in main.py.

Tester-added tests covering scenarios beyond the Developer's original suite.
"""

from __future__ import annotations

import re
import sys
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Edge case 1: --version combined with other flags
# ---------------------------------------------------------------------------


def test_version_combined_with_other_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    """--version --headless must still exit zero (--version wins)."""
    monkeypatch.setattr(sys, "argv", ["agent-launcher", "--version", "--headless"])
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    import launcher.main as main_mod

    with pytest.raises(SystemExit) as exc_info:
        main_mod.main()

    assert exc_info.value.code == 0


def test_version_flag_last_position(monkeypatch: pytest.MonkeyPatch) -> None:
    """--version in last position must still trigger early exit."""
    monkeypatch.setattr(sys, "argv", ["agent-launcher", "--headless", "--version"])
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    import launcher.main as main_mod

    with pytest.raises(SystemExit) as exc_info:
        main_mod.main()

    assert exc_info.value.code == 0


# ---------------------------------------------------------------------------
# Edge case 2: Version string format
# ---------------------------------------------------------------------------


def test_version_output_format(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Output must match '<APP_NAME> <MAJOR.MINOR.PATCH>' format."""
    monkeypatch.setattr(sys, "argv", ["agent-launcher", "--version"])
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    import launcher.main as main_mod
    from launcher.config import APP_NAME, VERSION

    with pytest.raises(SystemExit):
        main_mod.main()

    output = capsys.readouterr().out.strip()
    # Must contain the full expected string on one line
    expected = f"{APP_NAME} {VERSION}"
    assert output == expected, f"Expected '{expected}', got '{output}'"


def test_version_string_is_semver(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Printed VERSION must conform to MAJOR.MINOR.PATCH (semver-like) pattern."""
    monkeypatch.setattr(sys, "argv", ["agent-launcher", "--version"])
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    import launcher.main as main_mod

    with pytest.raises(SystemExit):
        main_mod.main()

    output = capsys.readouterr().out.strip()
    # Extract the portion after the last space — that should be the version number
    parts = output.rsplit(" ", 1)
    version_part = parts[-1] if len(parts) > 1 else output
    semver_pattern = re.compile(r"^\d+\.\d+\.\d+")
    assert semver_pattern.match(version_part), (
        f"Version '{version_part}' does not start with X.Y.Z semver pattern"
    )


# ---------------------------------------------------------------------------
# Edge case 3: PYTEST_CURRENT_TEST takes priority over --version
# ---------------------------------------------------------------------------


def test_pytest_current_test_takes_priority(monkeypatch: pytest.MonkeyPatch) -> None:
    """PYTEST_CURRENT_TEST env var must prevent main() from reaching --version check."""
    monkeypatch.setattr(sys, "argv", ["agent-launcher", "--version"])
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "some_test_file.py::test_func")
    import launcher.main as main_mod

    # main() must return early (no SystemExit) when PYTEST_CURRENT_TEST is set
    result = main_mod.main()
    assert result is None  # early return, not sys.exit


# ---------------------------------------------------------------------------
# Edge case 4: --version= value form (should NOT match)
# ---------------------------------------------------------------------------


def test_version_equals_form_not_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    """'--version=1.0' must NOT trigger the version exit (unsupported form)."""
    monkeypatch.setattr(sys, "argv", ["agent-launcher", "--version=1.0"])
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
                pytest.fail(
                    f"'--version=1.0' should not cause SystemExit but got "
                    f"SystemExit({e.code})"
                )


# ---------------------------------------------------------------------------
# Edge case 5: --version does not call ensure_shim_deployed
# ---------------------------------------------------------------------------


def test_version_flag_skips_shim_deploy(monkeypatch: pytest.MonkeyPatch) -> None:
    """--version must exit before calling ensure_shim_deployed()."""
    monkeypatch.setattr(sys, "argv", ["agent-launcher", "--version"])
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    import launcher.main as main_mod

    with patch.object(main_mod, "ensure_shim_deployed") as mock_shim:
        with pytest.raises(SystemExit) as exc_info:
            main_mod.main()

    assert exc_info.value.code == 0
    mock_shim.assert_not_called()
