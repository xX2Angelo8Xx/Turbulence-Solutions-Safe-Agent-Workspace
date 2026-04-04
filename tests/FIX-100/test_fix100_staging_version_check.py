"""
Tests for FIX-100: Fix Staging Test Version Check

Verifies that .github/workflows/staging-test.yml's "Verify version consistency"
step covers all 5 version files, matching release.yml's validate-version job.
"""

import re
from pathlib import Path

import pytest

STAGING_YML = Path(".github/workflows/staging-test.yml")
RELEASE_YML = Path(".github/workflows/release.yml")

EXPECTED_FILES = [
    "src/launcher/config.py",
    "pyproject.toml",
    "src/installer/windows/setup.iss",
    "src/installer/macos/build_dmg.sh",
    "src/installer/linux/build_appimage.sh",
]

EXPECTED_PATTERNS = {
    "src/launcher/config.py": r'VERSION\s*:\s*str\s*=\s*"([^"]+)"',
    "pyproject.toml": r'^version\s*=\s*"([^"]+)"',
    "src/installer/windows/setup.iss": r'#define MyAppVersion "([^"]+)"',
    "src/installer/macos/build_dmg.sh": r'APP_VERSION="([^"]+)"',
    "src/installer/linux/build_appimage.sh": r'APP_VERSION="([^"]+)"',
}


def _staging_yml_content() -> str:
    return STAGING_YML.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Structural checks on staging-test.yml
# ---------------------------------------------------------------------------


def test_staging_yml_exists():
    assert STAGING_YML.exists(), "staging-test.yml not found"


def test_staging_yml_contains_all_5_file_paths():
    content = _staging_yml_content()
    for fpath in EXPECTED_FILES:
        assert fpath in content, f"staging-test.yml missing file path: {fpath}"


def test_staging_yml_reports_5_files_in_success_message():
    content = _staging_yml_content()
    assert "All 5 version files match" in content, (
        "staging-test.yml success message should say 'All 5 version files match'"
    )


def test_staging_yml_does_not_have_old_2_file_message():
    content = _staging_yml_content()
    assert "All version files match" not in content or "All 5 version files match" in content, (
        "staging-test.yml still has old 'All version files match' (not 5) message"
    )


# ---------------------------------------------------------------------------
# Pattern correctness: each pattern must match the corresponding real file
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("fpath,pattern", list(EXPECTED_PATTERNS.items()))
def test_pattern_matches_real_file(fpath, pattern):
    real_file = Path(fpath)
    assert real_file.exists(), f"Installer file not found: {fpath}"
    content = real_file.read_text(encoding="utf-8")
    match = re.search(pattern, content, re.MULTILINE)
    assert match is not None, (
        f"Pattern {pattern!r} did not match content of {fpath}"
    )
    version = match.group(1)
    assert version, f"Pattern matched but captured empty version in {fpath}"
    # Sanity: version looks like semver (e.g. "3.3.10")
    assert re.match(r"^\d+\.\d+\.\d+", version), (
        f"Extracted version {version!r} from {fpath} does not look like semver"
    )


# ---------------------------------------------------------------------------
# Version consistency: all 5 files must agree on the same version
# ---------------------------------------------------------------------------


def test_all_5_files_have_consistent_versions():
    versions = {}
    for fpath, pattern in EXPECTED_PATTERNS.items():
        real_file = Path(fpath)
        assert real_file.exists(), f"Version file not found: {fpath}"
        content = real_file.read_text(encoding="utf-8")
        match = re.search(pattern, content, re.MULTILINE)
        assert match is not None, f"Pattern not found in {fpath}"
        versions[fpath] = match.group(1)

    unique = set(versions.values())
    assert len(unique) == 1, (
        f"Version mismatch across version files: {versions}"
    )


# ---------------------------------------------------------------------------
# Mismatch detection logic (unit test of the Python snippet's logic)
# ---------------------------------------------------------------------------


def _run_check_logic(file_contents: dict, expected: str) -> list:
    """Replicate the check logic from staging-test.yml to test it in isolation."""
    errors = []
    for fpath, pattern in EXPECTED_PATTERNS.items():
        content = file_contents.get(fpath, "")
        match = re.search(pattern, content, re.MULTILINE)
        if not match:
            errors.append(f"{fpath}: pattern not found")
        elif match.group(1) != expected:
            errors.append(f"{fpath}: expected {expected}, found {match.group(1)}")
    return errors


def _make_valid_contents(version: str) -> dict:
    return {
        "src/launcher/config.py": f'VERSION: str = "{version}"',
        "pyproject.toml": f'version = "{version}"',
        "src/installer/windows/setup.iss": f'#define MyAppVersion "{version}"',
        "src/installer/macos/build_dmg.sh": f'APP_VERSION="{version}"',
        "src/installer/linux/build_appimage.sh": f'APP_VERSION="{version}"',
    }


def test_check_logic_passes_when_all_match():
    contents = _make_valid_contents("3.3.10")
    errors = _run_check_logic(contents, "3.3.10")
    assert errors == []


def test_check_logic_detects_setup_iss_mismatch():
    contents = _make_valid_contents("3.3.10")
    contents["src/installer/windows/setup.iss"] = '#define MyAppVersion "3.3.9"'
    errors = _run_check_logic(contents, "3.3.10")
    assert any("setup.iss" in e for e in errors)


def test_check_logic_detects_build_dmg_mismatch():
    contents = _make_valid_contents("3.3.10")
    contents["src/installer/macos/build_dmg.sh"] = 'APP_VERSION="3.2.0"'
    errors = _run_check_logic(contents, "3.3.10")
    assert any("build_dmg.sh" in e for e in errors)


def test_check_logic_detects_build_appimage_mismatch():
    contents = _make_valid_contents("3.3.10")
    contents["src/installer/linux/build_appimage.sh"] = 'APP_VERSION="3.0.0"'
    errors = _run_check_logic(contents, "3.3.10")
    assert any("build_appimage.sh" in e for e in errors)


def test_check_logic_detects_missing_pattern():
    contents = _make_valid_contents("3.3.10")
    contents["src/installer/windows/setup.iss"] = "no version here"
    errors = _run_check_logic(contents, "3.3.10")
    assert any("pattern not found" in e and "setup.iss" in e for e in errors)


def test_check_logic_reports_no_errors_with_new_version():
    contents = _make_valid_contents("4.0.0")
    errors = _run_check_logic(contents, "4.0.0")
    assert errors == []
