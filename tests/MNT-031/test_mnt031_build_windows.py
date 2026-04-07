"""Tests for scripts/build_windows.py (MNT-031).

All subprocess calls and network requests are mocked — no real builds occur.
"""

# MNT-031

import sys
import types
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Import the module under test.  We import it directly by manipulating sys.path
# so tests are independent of the workspace layout.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import build_windows  # noqa: E402 (must come after sys.path insert)


# ---------------------------------------------------------------------------
# Helper: reset module-level state between tests where needed
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Tests: find_iscc
# ---------------------------------------------------------------------------


class TestFindIscc:
    def test_find_iscc_via_which(self):
        """ISCC.exe is returned when shutil.which finds it on PATH."""
        fake_path = r"C:\some\custom\path\ISCC.exe"
        with patch("build_windows.shutil.which", return_value=fake_path):
            result = build_windows.find_iscc()
        assert result == Path(fake_path)

    def test_find_iscc_fallback_first_path(self, tmp_path):
        """ISCC.exe is returned from first fallback path when which() returns None."""
        fake_iscc = tmp_path / "ISCC.exe"
        fake_iscc.touch()

        original_fallbacks = build_windows._ISCC_FALLBACK_PATHS
        try:
            build_windows._ISCC_FALLBACK_PATHS = [fake_iscc, Path("nonexistent.exe")]
            with patch("build_windows.shutil.which", return_value=None):
                result = build_windows.find_iscc()
            assert result == fake_iscc
        finally:
            build_windows._ISCC_FALLBACK_PATHS = original_fallbacks

    def test_find_iscc_fallback_second_path(self, tmp_path):
        """ISCC.exe is returned from second fallback path when first doesn't exist."""
        fake_iscc = tmp_path / "ISCC.exe"
        fake_iscc.touch()

        original_fallbacks = build_windows._ISCC_FALLBACK_PATHS
        try:
            build_windows._ISCC_FALLBACK_PATHS = [
                Path("nonexistent_first.exe"),
                fake_iscc,
            ]
            with patch("build_windows.shutil.which", return_value=None):
                result = build_windows.find_iscc()
            assert result == fake_iscc
        finally:
            build_windows._ISCC_FALLBACK_PATHS = original_fallbacks

    def test_find_iscc_not_found_exits(self, capsys):
        """SystemExit is raised with an informative error when ISCC cannot be found."""
        original_fallbacks = build_windows._ISCC_FALLBACK_PATHS
        try:
            build_windows._ISCC_FALLBACK_PATHS = [
                Path("does_not_exist_1.exe"),
                Path("does_not_exist_2.exe"),
            ]
            with patch("build_windows.shutil.which", return_value=None):
                with pytest.raises(SystemExit) as exc_info:
                    build_windows.find_iscc()
        finally:
            build_windows._ISCC_FALLBACK_PATHS = original_fallbacks

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "ISCC.exe not found" in captured.err
        assert "jrsoftware.org" in captured.err


# ---------------------------------------------------------------------------
# Tester edge-case additions (MNT-031)
# ---------------------------------------------------------------------------


class TestTesterEdgeCases:
    def test_dry_run_with_iscc_missing_still_exits(self, capsys):
        """`--dry-run` calls find_iscc() and exits if ISCC is absent.

        Documented behaviour: find_iscc() is invoked before the dry_run guard
        inside step_inno_setup(), so even dry-run fails when ISCC is not found.
        This test pins that behaviour so a future bugfix shows up as a diff.
        """
        original_fallbacks = build_windows._ISCC_FALLBACK_PATHS
        try:
            build_windows._ISCC_FALLBACK_PATHS = [
                Path("no_iscc_dry_1.exe"),
                Path("no_iscc_dry_2.exe"),
            ]
            with (
                patch("build_windows.shutil.which", return_value=None),
                patch.object(
                    build_windows,
                    "PYTHON_EMBED_DIR",
                    Path("nonexistent_embed_dry"),
                ),
            ):
                with patch("sys.argv", ["build_windows.py", "--dry-run"]):
                    with pytest.raises(SystemExit) as exc_info:
                        build_windows.main()
        finally:
            build_windows._ISCC_FALLBACK_PATHS = original_fallbacks

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "ISCC.exe not found" in captured.err

    def test_all_skip_flags_combined(self, tmp_path, capsys):
        """`--skip-pyinstaller --skip-embed` together still runs ISCC exactly once."""
        embed_dir = tmp_path / "python-embed"
        embed_dir.mkdir()
        (embed_dir / "file.txt").touch()

        with (
            patch("build_windows.subprocess.run") as mock_run,
            patch("build_windows.shutil.which", return_value=r"C:\ISCC.exe"),
            patch.object(build_windows, "PYTHON_EMBED_DIR", embed_dir),
        ):
            with patch(
                "sys.argv",
                ["build_windows.py", "--skip-pyinstaller", "--skip-embed"],
            ):
                build_windows.main()

        assert mock_run.call_count == 1
        called_cmd = mock_run.call_args[0][0]
        assert "ISCC" in str(called_cmd) or "iscc" in str(called_cmd).lower()
        captured = capsys.readouterr()
        assert "skipped (--skip-pyinstaller)" in captured.out
        assert "skipped (--skip-embed)" in captured.out

    def test_urlretrieve_exception_does_not_leave_zip(self, tmp_path):
        """If urlretrieve raises, the zip file at zip_path must not persist."""
        embed_dir = tmp_path / "python-embed"
        # No existing files — triggers download attempt.

        with (
            patch(
                "build_windows.urllib.request.urlretrieve",
                side_effect=OSError("Network error"),
            ),
            patch.object(build_windows, "PYTHON_EMBED_DIR", embed_dir),
            patch.object(build_windows, "REPO_ROOT", tmp_path),
        ):
            with pytest.raises(OSError, match="Network error"):
                build_windows.step_python_embed(dry_run=False)

        # Zip was never successfully written so should not exist at all.
        zip_path = tmp_path / "python-embed.zip"
        assert not zip_path.exists()

    def test_corrupted_zip_cleanup(self, tmp_path):
        """If the downloaded zip is corrupt, the zip file is removed by the finally block."""
        embed_dir = tmp_path / "python-embed"
        zip_path = tmp_path / "python-embed.zip"

        def fake_urlretrieve(url, dest):
            # Write an invalid (non-zip) file.
            Path(dest).write_text("not a zip")

        with (
            patch(
                "build_windows.urllib.request.urlretrieve",
                side_effect=fake_urlretrieve,
            ),
            patch.object(build_windows, "PYTHON_EMBED_DIR", embed_dir),
            patch.object(build_windows, "REPO_ROOT", tmp_path),
        ):
            with pytest.raises(Exception):  # BadZipFile or similar
                build_windows.step_python_embed(dry_run=False)

        # The finally block in step_python_embed must have deleted the bad zip.
        assert not zip_path.exists()

    def test_step_pyinstaller_calls_subprocess_with_check_true(self):
        """step_pyinstaller passes check=True so CalledProcessError propagates."""
        with patch("build_windows.subprocess.run") as mock_run:
            build_windows.step_pyinstaller(dry_run=False)

        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs.get("check") is True

    def test_step_inno_setup_calls_subprocess_with_check_true(self):
        """step_inno_setup passes check=True so build failures propagate."""
        with (
            patch("build_windows.subprocess.run") as mock_run,
            patch("build_windows.shutil.which", return_value=r"C:\ISCC.exe"),
        ):
            build_windows.step_inno_setup(dry_run=False)

        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs.get("check") is True

    def test_success_message_printed_after_non_dry_build(self, tmp_path, capsys):
        """main() prints the output EXE path on success when not in dry-run."""
        embed_dir = tmp_path / "python-embed"
        embed_dir.mkdir()
        (embed_dir / "dummy.txt").touch()

        with (
            patch("build_windows.subprocess.run"),
            patch("build_windows.shutil.which", return_value=r"C:\ISCC.exe"),
            patch.object(build_windows, "PYTHON_EMBED_DIR", embed_dir),
        ):
            with patch(
                "sys.argv",
                ["build_windows.py", "--skip-pyinstaller"],
            ):
                build_windows.main()

        captured = capsys.readouterr()
        assert "SUCCESS" in captured.out
        assert "AgentEnvironmentLauncher-Setup.exe" in captured.out


# ---------------------------------------------------------------------------
# Tests: --dry-run
# ---------------------------------------------------------------------------


class TestDryRun:
    def test_dry_run_does_not_call_subprocess(self, capsys):
        """--dry-run prints steps but never invokes subprocess.run."""
        with (
            patch("build_windows.subprocess.run") as mock_run,
            patch("build_windows.shutil.which", return_value=r"C:\ISCC.exe"),
            patch(
                "build_windows.PYTHON_EMBED_DIR",
                new_callable=lambda: property(lambda self: Path("nonexistent_embed_dir")),
            ),
        ):
            # Patch PYTHON_EMBED_DIR to simulate empty directory (force embed step)
            with patch.object(
                build_windows,
                "PYTHON_EMBED_DIR",
                Path("nonexistent_embed_dir_xyz_12345"),
            ):
                build_windows.main.__globals__  # access globals for reference
                # Call main with dry-run args
                with patch("sys.argv", ["build_windows.py", "--dry-run"]):
                    build_windows.main()

        mock_run.assert_not_called()
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
        assert "PyInstaller" in captured.out
        assert "Inno Setup" in captured.out

    def test_dry_run_prints_pyinstaller_command(self, capsys):
        """--dry-run prints the pyinstaller command string."""
        with (
            patch("build_windows.subprocess.run"),
            patch("build_windows.shutil.which", return_value=r"C:\ISCC.exe"),
            patch.object(
                build_windows,
                "PYTHON_EMBED_DIR",
                Path("nonexistent_embed_xyz"),
            ),
        ):
            with patch("sys.argv", ["build_windows.py", "--dry-run"]):
                build_windows.main()

        captured = capsys.readouterr()
        # FIX-125: command is now sys.executable -m PyInstaller (capital I), not bare pyinstaller
        assert "PyInstaller" in captured.out
        assert "launcher.spec" in captured.out


# ---------------------------------------------------------------------------
# Tests: --skip-pyinstaller
# ---------------------------------------------------------------------------


class TestSkipPyinstaller:
    def test_skip_pyinstaller_no_pyinstaller_call(self, capsys, tmp_path):
        """--skip-pyinstaller causes the PyInstaller step to be skipped."""
        # Create a non-empty embed dir so embed step is also skipped automatically
        embed_dir = tmp_path / "python-embed"
        embed_dir.mkdir()
        (embed_dir / "dummy.txt").touch()

        with (
            patch("build_windows.subprocess.run") as mock_run,
            patch("build_windows.shutil.which", return_value=r"C:\ISCC.exe"),
            patch.object(build_windows, "PYTHON_EMBED_DIR", embed_dir),
        ):
            with patch("sys.argv", ["build_windows.py", "--skip-pyinstaller"]):
                build_windows.main()

        # subprocess.run should only have been called once (for ISCC), not for pyinstaller
        assert mock_run.call_count == 1
        called_cmd = mock_run.call_args[0][0]
        assert "pyinstaller" not in str(called_cmd).lower()
        assert "ISCC" in str(called_cmd) or "iscc" in str(called_cmd).lower()

        captured = capsys.readouterr()
        assert "skipped (--skip-pyinstaller)" in captured.out

    def test_skip_pyinstaller_inno_still_runs(self, tmp_path):
        """Inno Setup runs even when --skip-pyinstaller is specified."""
        embed_dir = tmp_path / "python-embed"
        embed_dir.mkdir()
        (embed_dir / "dummy.txt").touch()

        with (
            patch("build_windows.subprocess.run") as mock_run,
            patch("build_windows.shutil.which", return_value=r"C:\ISCC.exe"),
            patch.object(build_windows, "PYTHON_EMBED_DIR", embed_dir),
        ):
            with patch("sys.argv", ["build_windows.py", "--skip-pyinstaller"]):
                build_windows.main()

        assert mock_run.called
        called_cmd = mock_run.call_args[0][0]
        assert "ISCC" in str(called_cmd) or "iscc" in str(called_cmd).lower()


# ---------------------------------------------------------------------------
# Tests: --skip-embed
# ---------------------------------------------------------------------------


class TestSkipEmbed:
    def test_skip_embed_flag_skips_download(self, capsys, tmp_path):
        """--skip-embed flag prevents the download step from running."""
        with (
            patch("build_windows.subprocess.run"),
            patch("build_windows.shutil.which", return_value=r"C:\ISCC.exe"),
            patch("build_windows.urllib.request.urlretrieve") as mock_dl,
        ):
            with patch("sys.argv", ["build_windows.py", "--skip-embed", "--skip-pyinstaller"]):
                build_windows.main()

        mock_dl.assert_not_called()
        captured = capsys.readouterr()
        assert "skipped (--skip-embed)" in captured.out

    def test_skip_embed_when_dir_already_has_files(self, capsys, tmp_path):
        """Embed download is skipped automatically when the directory already has files."""
        embed_dir = tmp_path / "python-embed"
        embed_dir.mkdir()
        (embed_dir / "python311.dll").touch()

        with (
            patch("build_windows.subprocess.run"),
            patch("build_windows.shutil.which", return_value=r"C:\ISCC.exe"),
            patch("build_windows.urllib.request.urlretrieve") as mock_dl,
            patch.object(build_windows, "PYTHON_EMBED_DIR", embed_dir),
        ):
            with patch("sys.argv", ["build_windows.py", "--skip-pyinstaller"]):
                build_windows.main()

        mock_dl.assert_not_called()
        captured = capsys.readouterr()
        assert "already present" in captured.out


# ---------------------------------------------------------------------------
# Tests: embed download logic
# ---------------------------------------------------------------------------


class TestEmbedDownload:
    def test_embed_download_called_when_dir_empty(self, tmp_path):
        """urlretrieve is called when embed directory exists but is empty."""
        embed_dir = tmp_path / "python-embed"
        embed_dir.mkdir()  # empty directory

        fake_zip = tmp_path / "python-embed.zip"

        def fake_urlretrieve(url, dest):
            # Create a valid (but minimal) zip at dest
            import zipfile as zf
            with zf.ZipFile(dest, "w") as z:
                z.writestr("python.exe", b"fake")

        with (
            patch("build_windows.urllib.request.urlretrieve", side_effect=fake_urlretrieve),
            patch.object(build_windows, "PYTHON_EMBED_DIR", embed_dir),
            patch.object(build_windows, "REPO_ROOT", tmp_path),
        ):
            build_windows.step_python_embed(dry_run=False)

        # After extraction at least the dummy file exists
        files = list(embed_dir.iterdir())
        assert len(files) > 0

    def test_embed_dry_run_does_not_download(self, tmp_path):
        """In dry-run mode, urlretrieve is never called."""
        embed_dir = tmp_path / "python-embed"
        # Don't create dir — simulates fresh state

        with (
            patch("build_windows.urllib.request.urlretrieve") as mock_dl,
            patch.object(build_windows, "PYTHON_EMBED_DIR", embed_dir),
        ):
            build_windows.step_python_embed(dry_run=True)

        mock_dl.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: error handling when ISCC not found
# ---------------------------------------------------------------------------


class TestIsccNotFoundError:
    def test_main_exits_when_iscc_not_found(self, tmp_path, capsys):
        """main() exits with code 1 and prints install instructions when ISCC not found."""
        embed_dir = tmp_path / "python-embed"
        embed_dir.mkdir()
        (embed_dir / "dummy").touch()

        original_fallbacks = build_windows._ISCC_FALLBACK_PATHS
        try:
            build_windows._ISCC_FALLBACK_PATHS = [
                Path("no_iscc_here_1.exe"),
                Path("no_iscc_here_2.exe"),
            ]
            with (
                patch("build_windows.shutil.which", return_value=None),
                patch.object(build_windows, "PYTHON_EMBED_DIR", embed_dir),
            ):
                with patch("sys.argv", ["build_windows.py", "--skip-pyinstaller"]):
                    with pytest.raises(SystemExit) as exc_info:
                        build_windows.main()
        finally:
            build_windows._ISCC_FALLBACK_PATHS = original_fallbacks

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "ISCC.exe not found" in captured.err
