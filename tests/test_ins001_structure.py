"""Tests for INS-001: Project Scaffolding.

Verifies that every expected file and directory in the src/ layout exists and
that the launcher entry point can be executed without import errors.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
LAUNCHER_DIR = SRC_DIR / "launcher"


# ---------------------------------------------------------------------------
# Directory / file existence tests
# ---------------------------------------------------------------------------


def test_src_dir_exists() -> None:
    assert SRC_DIR.is_dir()


def test_launcher_dir_exists() -> None:
    assert LAUNCHER_DIR.is_dir()


def test_launcher_main_exists() -> None:
    assert (LAUNCHER_DIR / "main.py").is_file()


def test_launcher_init_exists() -> None:
    assert (LAUNCHER_DIR / "__init__.py").is_file()


def test_launcher_config_exists() -> None:
    assert (LAUNCHER_DIR / "config.py").is_file()


def test_gui_package_exists() -> None:
    assert (LAUNCHER_DIR / "gui" / "__init__.py").is_file()


def test_gui_app_exists() -> None:
    assert (LAUNCHER_DIR / "gui" / "app.py").is_file()


def test_gui_components_exists() -> None:
    assert (LAUNCHER_DIR / "gui" / "components.py").is_file()


def test_core_package_exists() -> None:
    assert (LAUNCHER_DIR / "core" / "__init__.py").is_file()


def test_core_project_creator_exists() -> None:
    assert (LAUNCHER_DIR / "core" / "project_creator.py").is_file()


def test_core_vscode_exists() -> None:
    assert (LAUNCHER_DIR / "core" / "vscode.py").is_file()


def test_core_os_utils_exists() -> None:
    assert (LAUNCHER_DIR / "core" / "os_utils.py").is_file()


def test_core_updater_exists() -> None:
    assert (LAUNCHER_DIR / "core" / "updater.py").is_file()


def test_installer_dir_exists() -> None:
    assert (SRC_DIR / "installer").is_dir()


def test_installer_windows_dir_exists() -> None:
    assert (SRC_DIR / "installer" / "windows").is_dir()


def test_installer_macos_dir_exists() -> None:
    assert (SRC_DIR / "installer" / "macos").is_dir()


def test_installer_linux_dir_exists() -> None:
    assert (SRC_DIR / "installer" / "linux").is_dir()


# ---------------------------------------------------------------------------
# Import / runtime tests
# ---------------------------------------------------------------------------


def test_main_py_runs_without_import_errors() -> None:
    """Run python src/launcher/main.py as a subprocess; assert exit code 0."""
    result = subprocess.run(
        [sys.executable, str(LAUNCHER_DIR / "main.py")],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, (
        f"main.py exited with code {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_launcher_config_importable() -> None:
    """Import launcher.config and verify expected attributes are present."""
    import launcher.config as config  # noqa: PLC0415

    assert hasattr(config, "APP_NAME"), "APP_NAME missing from launcher.config"
    assert hasattr(config, "VERSION"), "VERSION missing from launcher.config"
    assert isinstance(config.APP_NAME, str)
    assert isinstance(config.VERSION, str)


def test_os_utils_get_platform() -> None:
    """get_platform() must return one of the three recognised OS strings."""
    from launcher.core.os_utils import get_platform  # noqa: PLC0415

    result = get_platform()
    assert result in ("windows", "macos", "linux"), (
        f"Unexpected platform value: {result!r}"
    )


def test_updater_stub_returns_no_update() -> None:
    """check_for_update() stub must report no update available."""
    from launcher.core.updater import check_for_update  # noqa: PLC0415

    available, latest = check_for_update("0.1.0")
    assert available is False
    assert latest == "0.1.0"


def test_project_creator_rejects_path_traversal() -> None:
    """create_project() must reject folder names that escape the destination."""
    import tempfile  # noqa: PLC0415

    from launcher.core.project_creator import create_project  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp)
        # The template dir does not need to exist for the traversal check to fire,
        # but it is checked first — so use a real dir.
        template = dest / "tpl"
        template.mkdir()

        try:
            create_project(template, dest, "../../etc")
            assert False, "Expected ValueError was not raised"
        except ValueError as exc:
            assert "path traversal" in str(exc).lower()


def test_project_creator_rejects_prefix_match_bypass() -> None:
    """BUG-001 regression: create_project() must block the sibling-prefix bypass.

    A naive str.startswith() guard can be fooled when the resolved target begins
    with the destination string but is NOT inside it.  For example:
        destination = /tmp/tmpXXX/foo
        folder_name = ../foobar
        resolved target = /tmp/tmpXXX/foobar
        '/tmp/tmpXXX/foobar'.startswith('/tmp/tmpXXX/foo') → True  ← exploitable!

    The correct guard is Path.is_relative_to() which checks genuine containment.
    """
    import tempfile  # noqa: PLC0415

    from launcher.core.project_creator import create_project  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as base:
        base_path = Path(base)
        dest = base_path / "foo"
        dest.mkdir()
        template = base_path / "tpl"
        template.mkdir()

        # '../foobar' resolves to a sibling that shares the 'foo' prefix.
        # startswith() incorrectly allows this; is_relative_to() correctly blocks it.
        try:
            create_project(template, dest, "../foobar")
            assert False, (
                "Expected ValueError was not raised — BUG-001 path-traversal "
                "prefix-match bypass is still present in project_creator.py. "
                "Replace str(target).startswith(str(destination.resolve())) "
                "with target.is_relative_to(destination.resolve())."
            )
        except ValueError as exc:
            assert "path traversal" in str(exc).lower()
