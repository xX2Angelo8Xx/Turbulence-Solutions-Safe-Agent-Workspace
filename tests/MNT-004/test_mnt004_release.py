"""Tests for scripts/release.py — MNT-004."""

import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make the scripts directory importable.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import release as rel  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONFIG_PY_CONTENT = '''\
"""Application-wide constants."""

import sys
from pathlib import Path

APP_NAME: str = "TS - Safe Agent Environment"
VERSION: str = "3.2.6"
COLOR_PRIMARY: str = "#0A1D4E"
'''

_PYPROJECT_CONTENT = '''\
[build-system]
requires = ["setuptools>=68,<69"]
build-backend = "setuptools.build_meta"

[project]
name = "agent-environment-launcher"
version = "3.2.6"
description = "Cross-platform launcher."
'''

_SETUP_ISS_CONTENT = '''\
; Inno Setup script
#define MyAppName "TS - Safe Agent Environment"
#define MyAppVersion "3.2.6"
#define MyAppPublisher "Turbulence Solutions"
AppVersion={#MyAppVersion}
'''

_BUILD_DMG_CONTENT = '''\
#!/usr/bin/env bash
set -euo pipefail
APP_NAME="TS - Safe Agent Environment"
APP_VERSION="3.2.6"
TARGET_ARCH="${1:-arm64}"
'''

_BUILD_APPIMAGE_CONTENT = '''\
#!/usr/bin/env bash
set -euo pipefail
APP_NAME="TS - Safe Agent Environment"
APP_VERSION="3.2.6"
TARGET_ARCH="${1:-x86_64}"
'''


def _write_temp_version_files(tmp_path: Path) -> dict:
    """Write all 5 version files into tmp_path and return a key->Path mapping."""
    files = {
        "config_py": tmp_path / "config.py",
        "pyproject_toml": tmp_path / "pyproject.toml",
        "setup_iss": tmp_path / "setup.iss",
        "build_dmg_sh": tmp_path / "build_dmg.sh",
        "build_appimage_sh": tmp_path / "build_appimage.sh",
    }
    contents = {
        "config_py": _CONFIG_PY_CONTENT,
        "pyproject_toml": _PYPROJECT_CONTENT,
        "setup_iss": _SETUP_ISS_CONTENT,
        "build_dmg_sh": _BUILD_DMG_CONTENT,
        "build_appimage_sh": _BUILD_APPIMAGE_CONTENT,
    }
    for key, path in files.items():
        path.write_text(contents[key], encoding="utf-8")
    return files


# ---------------------------------------------------------------------------
# Version validation tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("version", ["3.2.7", "1.0.0", "10.20.30", "0.0.1"])
def test_valid_versions(version: str) -> None:
    assert rel.validate_version(version) is True


@pytest.mark.parametrize("version", [
    "v3.2.7",        # leading v not allowed
    "3.2",           # missing patch
    "3.2.7.1",       # extra segment
    "3.2.a",         # non-numeric
    "",              # empty
    "latest",        # text
    "3.2.7-beta",    # pre-release suffix
])
def test_invalid_versions(version: str) -> None:
    assert rel.validate_version(version) is False


# ---------------------------------------------------------------------------
# File update tests (unit — operate on temp files)
# ---------------------------------------------------------------------------

def test_update_config_py(tmp_path: Path) -> None:
    tmp_files = _write_temp_version_files(tmp_path)
    with patch.dict(rel.VERSION_FILES, {"config_py": tmp_files["config_py"]}):
        result = rel.update_file("config_py", "3.2.7", dry_run=False)
    assert result is True
    content = tmp_files["config_py"].read_text(encoding="utf-8")
    assert 'VERSION: str = "3.2.7"' in content
    assert "3.2.6" not in content


def test_update_pyproject_toml(tmp_path: Path) -> None:
    tmp_files = _write_temp_version_files(tmp_path)
    with patch.dict(rel.VERSION_FILES, {"pyproject_toml": tmp_files["pyproject_toml"]}):
        result = rel.update_file("pyproject_toml", "3.2.7", dry_run=False)
    assert result is True
    content = tmp_files["pyproject_toml"].read_text(encoding="utf-8")
    assert 'version = "3.2.7"' in content
    assert "3.2.6" not in content


def test_update_setup_iss(tmp_path: Path) -> None:
    tmp_files = _write_temp_version_files(tmp_path)
    with patch.dict(rel.VERSION_FILES, {"setup_iss": tmp_files["setup_iss"]}):
        result = rel.update_file("setup_iss", "3.2.7", dry_run=False)
    assert result is True
    content = tmp_files["setup_iss"].read_text(encoding="utf-8")
    assert '#define MyAppVersion "3.2.7"' in content
    assert "3.2.6" not in content


def test_update_build_dmg_sh(tmp_path: Path) -> None:
    tmp_files = _write_temp_version_files(tmp_path)
    with patch.dict(rel.VERSION_FILES, {"build_dmg_sh": tmp_files["build_dmg_sh"]}):
        result = rel.update_file("build_dmg_sh", "3.2.7", dry_run=False)
    assert result is True
    content = tmp_files["build_dmg_sh"].read_text(encoding="utf-8")
    assert 'APP_VERSION="3.2.7"' in content
    assert "3.2.6" not in content


def test_update_build_appimage_sh(tmp_path: Path) -> None:
    tmp_files = _write_temp_version_files(tmp_path)
    with patch.dict(rel.VERSION_FILES, {"build_appimage_sh": tmp_files["build_appimage_sh"]}):
        result = rel.update_file("build_appimage_sh", "3.2.7", dry_run=False)
    assert result is True
    content = tmp_files["build_appimage_sh"].read_text(encoding="utf-8")
    assert 'APP_VERSION="3.2.7"' in content
    assert "3.2.6" not in content


# ---------------------------------------------------------------------------
# update_file returns False when pattern not found
# ---------------------------------------------------------------------------

def test_update_file_pattern_not_found(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("# no version here\n", encoding="utf-8")
    with patch.dict(rel.VERSION_FILES, {"config_py": bad_file}):
        result = rel.update_file("config_py", "3.2.7", dry_run=False)
    assert result is False
    # File should be unchanged
    assert bad_file.read_text(encoding="utf-8") == "# no version here\n"


# ---------------------------------------------------------------------------
# Validate version file
# ---------------------------------------------------------------------------

def test_validate_version_file_confirms_update(tmp_path: Path) -> None:
    tmp_files = _write_temp_version_files(tmp_path)
    with patch.dict(rel.VERSION_FILES, {"config_py": tmp_files["config_py"]}):
        rel.update_file("config_py", "3.2.7", dry_run=False)
        assert rel.validate_version_file("config_py", "3.2.7") is True


def test_validate_version_file_fails_on_missing(tmp_path: Path) -> None:
    tmp_files = _write_temp_version_files(tmp_path)
    # Don't update — check that 3.2.7 is NOT in the original file.
    with patch.dict(rel.VERSION_FILES, {"config_py": tmp_files["config_py"]}):
        assert rel.validate_version_file("config_py", "3.2.7") is False


# ---------------------------------------------------------------------------
# Dry-run mode does not modify files
# ---------------------------------------------------------------------------

def test_dry_run_no_modification(tmp_path: Path) -> None:
    tmp_files = _write_temp_version_files(tmp_path)
    originals = {k: p.read_text(encoding="utf-8") for k, p in tmp_files.items()}

    with patch.dict(rel.VERSION_FILES, tmp_files):
        for key in tmp_files:
            rel.update_file(key, "3.2.7", dry_run=True)

    for key, path in tmp_files.items():
        assert path.read_text(encoding="utf-8") == originals[key], (
            f"dry_run should not have modified {key}"
        )


# ---------------------------------------------------------------------------
# Branch check
# ---------------------------------------------------------------------------

def test_abort_not_on_main_branch(tmp_path: Path, capsys) -> None:
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "feature-branch\n"
    mock_result.stderr = ""

    with patch("release.subprocess.run", return_value=mock_result):
        with pytest.raises(SystemExit) as exc_info:
            rel.check_on_main_branch(tmp_path)
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "feature-branch" in captured.out


def test_on_main_branch_passes(tmp_path: Path) -> None:
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "main\n"
    mock_result.stderr = ""

    with patch("release.subprocess.run", return_value=mock_result):
        # Should not raise
        rel.check_on_main_branch(tmp_path)


# ---------------------------------------------------------------------------
# Dirty working tree check
# ---------------------------------------------------------------------------

def test_abort_dirty_tree(tmp_path: Path, capsys) -> None:
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = " M src/launcher/config.py\n"
    mock_result.stderr = ""

    with patch("release.subprocess.run", return_value=mock_result):
        with pytest.raises(SystemExit) as exc_info:
            rel.check_clean_working_tree(tmp_path)
    assert exc_info.value.code == 1


def test_clean_tree_passes(tmp_path: Path) -> None:
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    with patch("release.subprocess.run", return_value=mock_result):
        # Should not raise
        rel.check_clean_working_tree(tmp_path)


# ---------------------------------------------------------------------------
# Rollback: script aborts before git operations if file update fails
# ---------------------------------------------------------------------------

def test_abort_on_file_update_failure(tmp_path: Path, capsys) -> None:
    """If one file's pattern is missing, main() must exit before any git ops."""
    # Write 4 valid files but make config_py pattern-less.
    tmp_files = _write_temp_version_files(tmp_path)
    tmp_files["config_py"].write_text("# no version line\n", encoding="utf-8")

    with patch.dict(rel.VERSION_FILES, tmp_files):
        with patch("release.subprocess.run") as mock_git:
            with pytest.raises(SystemExit) as exc_info:
                sys.argv = ["release.py", "3.2.7"]
                # Simulate already checked branch and clean tree by patching those checks.
                with patch("release.check_on_main_branch"):
                    with patch("release.check_clean_working_tree"):
                        rel.main()

    assert exc_info.value.code == 1
    # Git must never have been called.
    mock_git.assert_not_called()
