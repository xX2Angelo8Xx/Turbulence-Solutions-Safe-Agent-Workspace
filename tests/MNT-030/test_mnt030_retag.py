"""Tests for MNT-030: --retag mode in scripts/release.py."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# Make the scripts package importable.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import release  # noqa: E402  (import after sys.path tweak)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_version_files(tmp_path: Path, version: str) -> dict:
    """
    Create temporary fake versions of the 5 version files, all containing
    the given version string.  Returns a dict {key: Path} identical in
    structure to release.VERSION_FILES.
    """
    config_py = tmp_path / "config.py"
    config_py.write_text(f'VERSION : str = "{version}"\n', encoding="utf-8")

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(f'version = "{version}"\n', encoding="utf-8")

    setup_iss = tmp_path / "setup.iss"
    setup_iss.write_text(f'#define MyAppVersion "{version}"\n', encoding="utf-8")

    build_dmg = tmp_path / "build_dmg.sh"
    build_dmg.write_text(f'APP_VERSION="{version}"\n', encoding="utf-8")

    build_appimage = tmp_path / "build_appimage.sh"
    build_appimage.write_text(f'APP_VERSION="{version}"\n', encoding="utf-8")

    return {
        "config_py": config_py,
        "pyproject_toml": pyproject,
        "setup_iss": setup_iss,
        "build_dmg_sh": build_dmg,
        "build_appimage_sh": build_appimage,
    }


# ---------------------------------------------------------------------------
# Test 1: --retag with all version files matching → succeeds
# ---------------------------------------------------------------------------

def test_retag_all_files_match_succeeds(tmp_path: Path, capsys) -> None:
    """retag_release() must complete successfully when all version files match."""
    version = "3.5.0"
    fake_files = _make_fake_version_files(tmp_path, version)

    # Patch VERSION_FILES to use our temp files.
    with patch.dict(release.VERSION_FILES, fake_files, clear=True):
        # Mock check_on_main_branch and check_clean_working_tree (no-ops).
        # Mock _run_git and _run_git_optional to simulate successful git calls.
        with (
            patch.object(release, "check_on_main_branch"),
            patch.object(release, "check_clean_working_tree"),
            patch.object(release, "_run_git") as mock_run_git,
            patch.object(release, "_run_git_optional") as mock_run_git_optional,
        ):
            mock_run_git_optional.return_value = MagicMock()  # simulate tag/remote exist
            mock_run_git.return_value = MagicMock()

            release.retag_release(version, dry_run=False, repo_root=tmp_path)

    out = capsys.readouterr().out

    # Verify key output lines are present.
    assert "Retag v3.5.0" in out
    assert "Retag v3.5.0 complete." in out
    assert "[ABORT]" not in out
    assert "[FAIL]" not in out

    # Verify git commands were issued in correct order:
    # delete local tag, delete remote tag, create tag, push tag.
    delete_local_call = call(["tag", "-d", "v3.5.0"], tmp_path)
    delete_remote_call = call(["push", "origin", ":refs/tags/v3.5.0"], tmp_path)
    assert mock_run_git_optional.call_args_list == [delete_local_call, delete_remote_call]

    create_tag_call = call(["tag", "-a", "v3.5.0", "-m", "Release v3.5.0"], tmp_path)
    push_tag_call = call(["push", "origin", "v3.5.0"], tmp_path)
    assert create_tag_call in mock_run_git.call_args_list
    assert push_tag_call in mock_run_git.call_args_list


# ---------------------------------------------------------------------------
# Test 2: --retag with version files NOT matching → aborts with clear error
# ---------------------------------------------------------------------------

def test_retag_version_mismatch_aborts(tmp_path: Path, capsys) -> None:
    """retag_release() must abort when any version file does not match."""
    version = "3.5.0"
    fake_files = _make_fake_version_files(tmp_path, "3.4.9")  # wrong version in all files

    with patch.dict(release.VERSION_FILES, fake_files, clear=True):
        with (
            patch.object(release, "check_on_main_branch"),
            patch.object(release, "check_clean_working_tree"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                release.retag_release(version, dry_run=False, repo_root=tmp_path)

    assert exc_info.value.code == 1

    out = capsys.readouterr().out
    assert "[ABORT]" in out
    assert "version file(s) do not match" in out
    assert "Use normal release mode" in out


def test_retag_partial_mismatch_aborts(tmp_path: Path, capsys) -> None:
    """retag_release() must abort even if only ONE file does not match."""
    version = "3.5.0"
    fake_files = _make_fake_version_files(tmp_path, version)
    # Corrupt one file.
    fake_files["pyproject_toml"].write_text('version = "3.4.9"\n', encoding="utf-8")

    with patch.dict(release.VERSION_FILES, fake_files, clear=True):
        with (
            patch.object(release, "check_on_main_branch"),
            patch.object(release, "check_clean_working_tree"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                release.retag_release(version, dry_run=False, repo_root=tmp_path)

    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "[FAIL]  pyproject.toml does NOT contain 3.5.0" in out
    assert "[ABORT]" in out


# ---------------------------------------------------------------------------
# Test 3: --retag --dry-run → prints plan, no git commands executed
# ---------------------------------------------------------------------------

def test_retag_dry_run_no_git_calls(tmp_path: Path, capsys) -> None:
    """retag_release() with dry_run=True must not execute any git commands."""
    version = "3.5.0"
    fake_files = _make_fake_version_files(tmp_path, version)

    with patch.dict(release.VERSION_FILES, fake_files, clear=True):
        with (
            patch.object(release, "_run_git") as mock_run_git,
            patch.object(release, "_run_git_optional") as mock_run_git_optional,
        ):
            release.retag_release(version, dry_run=True, repo_root=tmp_path)

    # No git commands must have been called.
    mock_run_git.assert_not_called()
    mock_run_git_optional.assert_not_called()

    out = capsys.readouterr().out
    assert "[DRY-RUN]" in out
    assert "Would delete local tag" in out
    assert "Would delete remote tag" in out
    assert "Would create annotated tag" in out
    assert "Would push tag" in out
    assert "No changes were made." in out


def test_retag_dry_run_aborts_on_mismatch(tmp_path: Path, capsys) -> None:
    """retag_release() with dry_run=True must still abort if files don't match."""
    version = "3.5.0"
    fake_files = _make_fake_version_files(tmp_path, "3.4.9")

    with patch.dict(release.VERSION_FILES, fake_files, clear=True):
        with pytest.raises(SystemExit) as exc_info:
            release.retag_release(version, dry_run=True, repo_root=tmp_path)

    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "[ABORT]" in out


# ---------------------------------------------------------------------------
# Test 4: Normal mode unchanged (no regression)
# ---------------------------------------------------------------------------

def test_normal_mode_dry_run_still_works(tmp_path: Path, capsys) -> None:
    """Normal release dry-run must still work after the --retag addition."""
    version = "3.6.0"
    fake_files = _make_fake_version_files(tmp_path, "3.5.9")  # current version

    with patch.dict(release.VERSION_FILES, fake_files, clear=True):
        # Patch _FILE_PATTERNS to match the simple format we wrote above.
        simple_patterns = {
            "config_py": (r'(VERSION\s*:\s*str\s*=\s*")[^"]+(")', r'\g<1>{version}\g<2>'),
            "pyproject_toml": (r'(^version\s*=\s*")[^"]+(")', r'\g<1>{version}\g<2>'),
            "setup_iss": (r'(#define\s+MyAppVersion\s+")[^"]+(")', r'\g<1>{version}\g<2>'),
            "build_dmg_sh": (r'(^APP_VERSION=")[^"]+(")', r'\g<1>{version}\g<2>'),
            "build_appimage_sh": (r'(^APP_VERSION=")[^"]+(")', r'\g<1>{version}\g<2>'),
        }
        with patch.dict(release._FILE_PATTERNS, simple_patterns, clear=True):
            with patch("sys.argv", ["release.py", version, "--dry-run"]):
                release.main()  # must not raise

    out = capsys.readouterr().out
    assert "[DRY-RUN]" in out
    assert f"Release v{version}" in out
    assert "Would create git commit" in out
    assert "Would create annotated tag" in out
    assert "No changes were made." in out


def test_normal_mode_retag_flag_absent(tmp_path: Path, capsys) -> None:
    """Calling main() without --retag must not invoke retag_release()."""
    version = "3.6.0"
    fake_files = _make_fake_version_files(tmp_path, "3.5.9")

    with patch.dict(release.VERSION_FILES, fake_files, clear=True):
        simple_patterns = {
            "config_py": (r'(VERSION\s*:\s*str\s*=\s*")[^"]+(")', r'\g<1>{version}\g<2>'),
            "pyproject_toml": (r'(^version\s*=\s*")[^"]+(")', r'\g<1>{version}\g<2>'),
            "setup_iss": (r'(#define\s+MyAppVersion\s+")[^"]+(")', r'\g<1>{version}\g<2>'),
            "build_dmg_sh": (r'(^APP_VERSION=")[^"]+(")', r'\g<1>{version}\g<2>'),
            "build_appimage_sh": (r'(^APP_VERSION=")[^"]+(")', r'\g<1>{version}\g<2>'),
        }
        with patch.dict(release._FILE_PATTERNS, simple_patterns, clear=True):
            with (
                patch("sys.argv", ["release.py", version, "--dry-run"]),
                patch.object(release, "retag_release") as mock_retag,
            ):
                release.main()

    mock_retag.assert_not_called()


# ---------------------------------------------------------------------------
# Test 5: --retag handles missing local / remote tag gracefully
# ---------------------------------------------------------------------------

def test_retag_missing_local_tag_continues(tmp_path: Path, capsys) -> None:
    """retag_release() must continue gracefully if local tag does not exist."""
    version = "3.5.0"
    fake_files = _make_fake_version_files(tmp_path, version)

    def local_tag_absent(args, cwd):
        # Simulate: local tag delete fails, remote delete succeeds.
        if args[:2] == ["tag", "-d"]:
            return None  # local tag absent
        return MagicMock()

    with patch.dict(release.VERSION_FILES, fake_files, clear=True):
        with (
            patch.object(release, "check_on_main_branch"),
            patch.object(release, "check_clean_working_tree"),
            patch.object(release, "_run_git") as mock_run_git,
            patch.object(release, "_run_git_optional", side_effect=local_tag_absent),
        ):
            mock_run_git.return_value = MagicMock()
            release.retag_release(version, dry_run=False, repo_root=tmp_path)

    out = capsys.readouterr().out
    assert "did not exist" in out
    assert "[ABORT]" not in out
    assert "Retag v3.5.0 complete." in out


def test_retag_missing_remote_tag_continues(tmp_path: Path, capsys) -> None:
    """retag_release() must continue gracefully if remote tag does not exist."""
    version = "3.5.0"
    fake_files = _make_fake_version_files(tmp_path, version)

    def remote_tag_absent(args, cwd):
        # Simulate: local tag delete succeeds, remote delete fails.
        if args[:2] == ["tag", "-d"]:
            return MagicMock()  # local tag present
        return None  # remote tag absent

    with patch.dict(release.VERSION_FILES, fake_files, clear=True):
        with (
            patch.object(release, "check_on_main_branch"),
            patch.object(release, "check_clean_working_tree"),
            patch.object(release, "_run_git") as mock_run_git,
            patch.object(release, "_run_git_optional", side_effect=remote_tag_absent),
        ):
            mock_run_git.return_value = MagicMock()
            release.retag_release(version, dry_run=False, repo_root=tmp_path)

    out = capsys.readouterr().out
    assert "did not exist" in out
    assert "[ABORT]" not in out
    assert "Retag v3.5.0 complete." in out


def test_retag_both_tags_missing_is_fine(tmp_path: Path, capsys) -> None:
    """retag_release() must succeed when both local and remote tags are absent."""
    version = "3.5.0"
    fake_files = _make_fake_version_files(tmp_path, version)

    with patch.dict(release.VERSION_FILES, fake_files, clear=True):
        with (
            patch.object(release, "check_on_main_branch"),
            patch.object(release, "check_clean_working_tree"),
            patch.object(release, "_run_git") as mock_run_git,
            patch.object(release, "_run_git_optional", return_value=None),  # both absent
        ):
            mock_run_git.return_value = MagicMock()
            release.retag_release(version, dry_run=False, repo_root=tmp_path)

    out = capsys.readouterr().out
    assert out.count("did not exist") == 2
    assert "[ABORT]" not in out
    assert "Retag v3.5.0 complete." in out


# ---------------------------------------------------------------------------
# Tester edge-case tests
# ---------------------------------------------------------------------------


def test_main_invalid_version_with_retag_aborts(capsys) -> None:
    """main() must reject an invalid version format even when --retag is set."""
    with patch("sys.argv", ["release.py", "not.a.valid.version", "--retag"]):
        with pytest.raises(SystemExit) as exc_info:
            release.main()
    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "[ERROR]" in out
    assert "Invalid version" in out


def test_retag_tag_creation_failure_exits(tmp_path: Path, capsys) -> None:
    """retag_release() must exit(1) cleanly if git tag creation fails."""
    version = "3.5.0"
    fake_files = _make_fake_version_files(tmp_path, version)

    def tag_create_fails(args, cwd):
        if args[:2] == ["tag", "-a"]:
            raise RuntimeError("tag already exists")
        return MagicMock()

    with patch.dict(release.VERSION_FILES, fake_files, clear=True):
        with (
            patch.object(release, "check_on_main_branch"),
            patch.object(release, "check_clean_working_tree"),
            patch.object(release, "_run_git_optional", return_value=MagicMock()),
            patch.object(release, "_run_git", side_effect=tag_create_fails),
        ):
            with pytest.raises(SystemExit) as exc_info:
                release.retag_release(version, dry_run=False, repo_root=tmp_path)

    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "[ABORT]" in out
    assert "Tag creation failed" in out


def test_retag_tag_push_failure_exits(tmp_path: Path, capsys) -> None:
    """retag_release() must exit(1) cleanly if pushing the tag fails."""
    version = "3.5.0"
    fake_files = _make_fake_version_files(tmp_path, version)

    def push_fails(args, cwd):
        if args[:2] == ["push", "origin"] and not args[2].startswith(":"):
            raise RuntimeError("push rejected")
        return MagicMock()

    with patch.dict(release.VERSION_FILES, fake_files, clear=True):
        with (
            patch.object(release, "check_on_main_branch"),
            patch.object(release, "check_clean_working_tree"),
            patch.object(release, "_run_git_optional", return_value=MagicMock()),
            patch.object(release, "_run_git", side_effect=push_fails),
        ):
            with pytest.raises(SystemExit) as exc_info:
                release.retag_release(version, dry_run=False, repo_root=tmp_path)

    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "[ABORT]" in out
    assert "Tag push failed" in out
