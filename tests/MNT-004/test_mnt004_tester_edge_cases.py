"""Tester edge-case tests for scripts/release.py — MNT-004.

These supplement the Developer's 25 tests with boundary conditions, security
checks, full end-to-end main() exercises, and documented limitations.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import release as rel  # noqa: E402


# ---------------------------------------------------------------------------
# Minimal but valid file content (matches each file's regex pattern)
# ---------------------------------------------------------------------------

_CONFIG_PY = 'VERSION: str = "3.2.6"\n'
_PYPROJECT = '[project]\nname = "foo"\nversion = "3.2.6"\n'
_SETUP_ISS = '#define MyAppVersion "3.2.6"\n'
_BUILD_DMG = 'APP_VERSION="3.2.6"\n'
_BUILD_APPIMAGE = 'APP_VERSION="3.2.6"\n'


def _write_temp_files(tmp_path: Path) -> dict:
    """Write all 5 minimal version files into tmp_path."""
    files = {
        "config_py": tmp_path / "config.py",
        "pyproject_toml": tmp_path / "pyproject.toml",
        "setup_iss": tmp_path / "setup.iss",
        "build_dmg_sh": tmp_path / "build_dmg.sh",
        "build_appimage_sh": tmp_path / "build_appimage.sh",
    }
    contents = {
        "config_py": _CONFIG_PY,
        "pyproject_toml": _PYPROJECT,
        "setup_iss": _SETUP_ISS,
        "build_dmg_sh": _BUILD_DMG,
        "build_appimage_sh": _BUILD_APPIMAGE,
    }
    for key, path in files.items():
        path.write_text(contents[key], encoding="utf-8")
    return files


# ---------------------------------------------------------------------------
# validate_version — boundary conditions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("version", ["9999.9999.9999", "0.0.0", "123.456.789"])
def test_large_valid_versions(version: str) -> None:
    """Extreme but valid semver values must be accepted."""
    assert rel.validate_version(version) is True


def test_version_with_leading_zeros_accepted() -> None:
    """Document: '001.002.003' passes \\d+ pattern (leading zeros not prohibited).

    This is a known limitation — \\d+ does not enforce no-leading-zeros.
    It is acceptable risk since the version also flows through git where
    leading zeros in tags are harmless.
    """
    assert rel.validate_version("001.002.003") is True


@pytest.mark.xfail(
    strict=False,
    reason=(
        "Python re $ matches just before a trailing \\n (known regex quirk). "
        "Fix: replace $ with \\Z in SEMVER_RE. Logged as BUG-165."
    ),
)
def test_version_with_trailing_newline_is_rejected() -> None:
    """3.2.7\\n should fail validation; currently passes due to Python's $ behavior."""
    assert rel.validate_version("3.2.7\n") is False


# ---------------------------------------------------------------------------
# Security: injection strings must be rejected by semver validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("version", [
    "3.2.7; rm -rf /",
    "3.2.7 && echo pwned",
    "3.2.7`id`",
    "3.2.7$(whoami)",
    "3.2.7|cat /etc/passwd",
    "3.2.7\x00",          # null byte
    "<script>3.2.7</script>",
    "../../../etc/passwd",
    "3.2.7\r\n3.2.8",     # CRLF injection
])
def test_injection_strings_rejected(version: str) -> None:
    """Malicious version strings must always fail semver validation."""
    assert rel.validate_version(version) is False


# ---------------------------------------------------------------------------
# Multiple version occurrences in pyproject.toml (documents behavior)
# ---------------------------------------------------------------------------

def test_multiple_matches_in_pyproject_toml_all_updated(tmp_path: Path) -> None:
    """If pyproject.toml has >1 line starting with 'version =', all are replaced.

    Documents current behavior: re.subn replaces ALL matches when count > 0.
    In practice, a standard pyproject.toml has only one such line, but if a
    [tool.poetry] section also has 'version = "..."' both get updated — which
    is acceptable.
    """
    content = '[project]\nversion = "3.2.6"\n\n[tool.poetry]\nversion = "3.2.6"\n'
    f = tmp_path / "pyproject.toml"
    f.write_text(content, encoding="utf-8")

    with patch.dict(rel.VERSION_FILES, {"pyproject_toml": f}):
        result = rel.update_file("pyproject_toml", "3.2.7", dry_run=False)

    assert result is True
    updated = f.read_text(encoding="utf-8")
    assert updated.count('version = "3.2.7"') == 2  # both lines updated
    assert "3.2.6" not in updated


# ---------------------------------------------------------------------------
# Empty file returns False
# ---------------------------------------------------------------------------

def test_update_file_empty_file_returns_false(tmp_path: Path) -> None:
    """An empty file has no version pattern — update_file must return False."""
    empty = tmp_path / "config.py"
    empty.write_text("", encoding="utf-8")

    with patch.dict(rel.VERSION_FILES, {"config_py": empty}):
        result = rel.update_file("config_py", "3.2.7", dry_run=False)

    assert result is False
    assert empty.read_text(encoding="utf-8") == ""  # unchanged


# ---------------------------------------------------------------------------
# validate_version_file — substring / superstring limitation (documented)
# ---------------------------------------------------------------------------

def test_validate_version_file_superstring_passes(tmp_path: Path) -> None:
    """Document: validate_version_file uses 'in', so '3.2.7' matches inside '3.2.70'.

    This is a theoretically possible false positive.  In practice it cannot
    occur because update_file would have replaced the exact pattern first;
    any remaining '3.2.70' string would mean the pattern was not matched, so
    update_file would have returned False and main() would have aborted.
    """
    f = tmp_path / "config.py"
    f.write_text('VERSION: str = "3.2.70"\n', encoding="utf-8")

    with patch.dict(rel.VERSION_FILES, {"config_py": f}):
        result = rel.validate_version_file("config_py", "3.2.7")

    # Documents the limitation: "3.2.7" IS a substring of "3.2.70"
    assert result is True


# ---------------------------------------------------------------------------
# _run_git raises RuntimeError on non-zero exit code
# ---------------------------------------------------------------------------

def test_run_git_raises_runtime_error_on_nonzero(tmp_path: Path) -> None:
    """_run_git must raise RuntimeError when git exits with a non-zero code."""
    mock_result = MagicMock()
    mock_result.returncode = 128
    mock_result.stdout = ""
    mock_result.stderr = "fatal: not a git repository"

    with patch("release.subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="exit 128"):
            rel._run_git(["status"], tmp_path)


def test_run_git_returns_result_on_zero(tmp_path: Path) -> None:
    """_run_git returns the CompletedProcess on success (exit 0)."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "ok\n"
    mock_result.stderr = ""

    with patch("release.subprocess.run", return_value=mock_result) as mock_run:
        result = rel._run_git(["status"], tmp_path)

    assert result is mock_result
    # Verify subprocess.run was called with the correct args list
    called_args = mock_run.call_args[0][0]
    assert called_args[0] == "git"
    assert called_args[1] == "status"


# ---------------------------------------------------------------------------
# Full main() end-to-end — non-dry-run with all git mocked
# ---------------------------------------------------------------------------

def test_main_end_to_end_non_dry_run(tmp_path: Path) -> None:
    """main() non-dry-run: all 5 files updated and git operations invoked."""
    tmp_files = _write_temp_files(tmp_path)

    mock_git = MagicMock()
    mock_git.return_value.returncode = 0
    mock_git.return_value.stdout = ""
    mock_git.return_value.stderr = ""

    with patch.dict(rel.VERSION_FILES, tmp_files):
        with patch("release._REPO_ROOT", tmp_path):
            with patch("release.subprocess.run", mock_git):
                with patch("release.check_on_main_branch"):
                    with patch("release.check_clean_working_tree"):
                        sys.argv = ["release.py", "3.2.7"]
                        rel.main()

    # Every version file must now contain the new version.
    for key, path in tmp_files.items():
        content = path.read_text(encoding="utf-8")
        assert "3.2.7" in content, f"{key} was not updated to 3.2.7"
        assert "3.2.6" not in content, f"{key} still contains old version"

    # At minimum: git add, commit, tag, push commit, push tag = 5 calls.
    assert mock_git.call_count >= 5


# ---------------------------------------------------------------------------
# Full main() dry-run — no file changes, no git calls
# ---------------------------------------------------------------------------

def test_main_dry_run_no_file_changes_no_git(tmp_path: Path) -> None:
    """main() --dry-run: files unmodified and git never invoked."""
    tmp_files = _write_temp_files(tmp_path)
    originals = {k: p.read_text(encoding="utf-8") for k, p in tmp_files.items()}

    with patch.dict(rel.VERSION_FILES, tmp_files):
        with patch("release.subprocess.run") as mock_git:
            sys.argv = ["release.py", "3.2.7", "--dry-run"]
            rel.main()

    for key, path in tmp_files.items():
        assert path.read_text(encoding="utf-8") == originals[key], (
            f"dry-run must not modify {key}"
        )

    mock_git.assert_not_called()


# ---------------------------------------------------------------------------
# Git failure mid-sequence — push tag fails → exit 1
# ---------------------------------------------------------------------------

def test_git_push_tag_failure_aborts(tmp_path: Path, capsys) -> None:
    """If git push tag fails, main() must exit with code 1."""
    tmp_files = _write_temp_files(tmp_path)
    call_count = [0]

    def mock_side_effect(*args, **kwargs):
        call_count[0] += 1
        r = MagicMock()
        r.stdout = ""
        # Call 5 = push tag — simulate failure.
        if call_count[0] == 5:
            r.returncode = 1
            r.stderr = "error: failed to push some refs to 'origin'"
        else:
            r.returncode = 0
            r.stderr = ""
        return r

    with patch.dict(rel.VERSION_FILES, tmp_files):
        with patch("release._REPO_ROOT", tmp_path):
            with patch("release.subprocess.run", side_effect=mock_side_effect):
                with patch("release.check_on_main_branch"):
                    with patch("release.check_clean_working_tree"):
                        sys.argv = ["release.py", "3.2.7"]
                        with pytest.raises(SystemExit) as exc_info:
                            rel.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "ABORT" in captured.out


# ---------------------------------------------------------------------------
# Git commit failure — exit 1 before tag is created
# ---------------------------------------------------------------------------

def test_git_commit_failure_aborts_before_tag(tmp_path: Path, capsys) -> None:
    """If git commit fails, main() exits 1 and no tag is attempted."""
    tmp_files = _write_temp_files(tmp_path)
    call_count = [0]

    def mock_side_effect(*args, **kwargs):
        call_count[0] += 1
        r = MagicMock()
        r.stdout = ""
        # Call 1 = git add (success), call 2 = git commit (fail).
        if call_count[0] == 2:
            r.returncode = 1
            r.stderr = "error: nothing to commit"
        else:
            r.returncode = 0
            r.stderr = ""
        return r

    with patch.dict(rel.VERSION_FILES, tmp_files):
        with patch("release._REPO_ROOT", tmp_path):
            with patch("release.subprocess.run", side_effect=mock_side_effect):
                with patch("release.check_on_main_branch"):
                    with patch("release.check_clean_working_tree"):
                        sys.argv = ["release.py", "3.2.7"]
                        with pytest.raises(SystemExit) as exc_info:
                            rel.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "ABORT" in captured.out
    # Only 2 git calls: add + commit. Tag was never reached.
    assert call_count[0] == 2


# ---------------------------------------------------------------------------
# Invalid version argument causes exit 1 without touching files or git
# ---------------------------------------------------------------------------

def test_invalid_version_arg_exits_before_any_changes(tmp_path: Path, capsys) -> None:
    """main() must exit 1 immediately on invalid version, not touching files/git."""
    tmp_files = _write_temp_files(tmp_path)
    originals = {k: p.read_text(encoding="utf-8") for k, p in tmp_files.items()}

    with patch.dict(rel.VERSION_FILES, tmp_files):
        with patch("release.subprocess.run") as mock_git:
            sys.argv = ["release.py", "not-a-version"]
            with pytest.raises(SystemExit) as exc_info:
                rel.main()

    assert exc_info.value.code == 1
    mock_git.assert_not_called()
    for key, path in tmp_files.items():
        assert path.read_text(encoding="utf-8") == originals[key], (
            f"{key} should not have been modified on invalid version"
        )


# ---------------------------------------------------------------------------
# Permission error propagates out of update_file (not silently swallowed)
# ---------------------------------------------------------------------------

def test_update_file_read_permission_error_propagates(tmp_path: Path) -> None:
    """PermissionError from read_text must propagate — not be swallowed.

    This documents that release.py does not handle OS-level read failures
    gracefully (exits with an uncaught exception rather than a clean message).
    This is a known limitation logged in the test report.
    """
    dummy = tmp_path / "config.py"
    dummy.write_text('VERSION: str = "3.2.6"\n', encoding="utf-8")

    with patch.dict(rel.VERSION_FILES, {"config_py": dummy}):
        with patch.object(dummy.__class__, "read_text", side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                rel.update_file("config_py", "3.2.7", dry_run=False)
