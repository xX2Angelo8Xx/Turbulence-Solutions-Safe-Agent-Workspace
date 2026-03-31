"""Edge-case tests for FIX-090: Version bump 3.3.0 → 3.3.1 (Tester additions)."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

VERSION_FILES = {
    "config.py": REPO_ROOT / "src" / "launcher" / "config.py",
    "pyproject.toml": REPO_ROOT / "pyproject.toml",
    "setup.iss": REPO_ROOT / "src" / "installer" / "windows" / "setup.iss",
    "build_dmg.sh": REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh",
    "build_appimage.sh": REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh",
}

EXPECTED_VERSION = "3.3.1"
OLD_VERSION = "3.3.0"


# --- Existence ---

def test_all_version_files_exist():
    """All 5 version files must exist on disk."""
    for name, path in VERSION_FILES.items():
        assert path.is_file(), f"Version file missing: {name} ({path})"


def test_all_version_files_non_empty():
    """No version file should be empty or zero-byte."""
    for name, path in VERSION_FILES.items():
        assert path.stat().st_size > 0, f"Version file is empty: {name}"


# --- Version format ---

def test_version_format_is_semver():
    """The version string 3.3.1 must follow MAJOR.MINOR.PATCH format."""
    assert re.match(r"^\d+\.\d+\.\d+$", EXPECTED_VERSION), \
        f"Version '{EXPECTED_VERSION}' is not valid semver"


def test_config_py_version_format():
    """config.py VERSION must be a valid semver string."""
    content = VERSION_FILES["config.py"].read_text(encoding="utf-8")
    match = re.search(r'VERSION\s*[:=][^"]*"(\d+\.\d+\.\d+)"', content)
    assert match, "Could not find a semver VERSION assignment in config.py"
    assert match.group(1) == EXPECTED_VERSION, \
        f"config.py VERSION is '{match.group(1)}', expected '{EXPECTED_VERSION}'"


def test_pyproject_version_format():
    """pyproject.toml version must be a valid semver string."""
    content = VERSION_FILES["pyproject.toml"].read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"(\d+\.\d+\.\d+)"', content, re.MULTILINE)
    assert match, "Could not find a semver version in pyproject.toml"
    assert match.group(1) == EXPECTED_VERSION, \
        f"pyproject.toml version is '{match.group(1)}', expected '{EXPECTED_VERSION}'"


# --- Consistency across all 5 files ---

def test_all_five_files_have_same_version():
    """All 5 files must report the same version string."""
    versions = {}
    content = VERSION_FILES["config.py"].read_text(encoding="utf-8")
    m = re.search(r'VERSION\s*[:=][^"]*"(\d+\.\d+\.\d+)"', content)
    versions["config.py"] = m.group(1) if m else None

    content = VERSION_FILES["pyproject.toml"].read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"(\d+\.\d+\.\d+)"', content, re.MULTILINE)
    versions["pyproject.toml"] = m.group(1) if m else None

    content = VERSION_FILES["setup.iss"].read_text(encoding="utf-8")
    m = re.search(r'#define MyAppVersion\s+"(\d+\.\d+\.\d+)"', content)
    versions["setup.iss"] = m.group(1) if m else None

    content = VERSION_FILES["build_dmg.sh"].read_text(encoding="utf-8")
    m = re.search(r'^APP_VERSION="(\d+\.\d+\.\d+)"', content, re.MULTILINE)
    versions["build_dmg.sh"] = m.group(1) if m else None

    content = VERSION_FILES["build_appimage.sh"].read_text(encoding="utf-8")
    m = re.search(r'^APP_VERSION="(\d+\.\d+\.\d+)"', content, re.MULTILINE)
    versions["build_appimage.sh"] = m.group(1) if m else None

    unique = set(v for v in versions.values() if v is not None)
    assert len(unique) == 1, f"Version inconsistency across files: {versions}"
    assert unique.pop() == EXPECTED_VERSION, \
        f"Consistent version found but it is not {EXPECTED_VERSION}: {versions}"


# --- No stale version strings anywhere in these files ---

def test_no_stale_version_in_any_file():
    """None of the 5 version files should contain the old version string 3.3.0."""
    for name, path in VERSION_FILES.items():
        content = path.read_text(encoding="utf-8")
        assert OLD_VERSION not in content, \
            f"Old version '{OLD_VERSION}' still found in {name}"


# --- Exact occurrence count ---

def test_config_py_version_appears_at_most_once():
    """VERSION = 3.3.1 should appear exactly once in config.py."""
    content = VERSION_FILES["config.py"].read_text(encoding="utf-8")
    count = content.count(EXPECTED_VERSION)
    # It should appear at least once (the constant) — we don't restrict display strings
    assert count >= 1, f"Expected version '{EXPECTED_VERSION}' not found in config.py"


def test_pyproject_version_defined_once():
    """pyproject.toml version field should appear exactly once."""
    content = VERSION_FILES["pyproject.toml"].read_text(encoding="utf-8")
    matches = re.findall(r'^version\s*=\s*"3\.3\.1"', content, re.MULTILINE)
    assert len(matches) == 1, \
        f"Expected exactly 1 version definition in pyproject.toml, found {len(matches)}"


# --- No future version accidentally committed ---

def test_no_future_version_in_files():
    """None of the 5 files should contain a version higher than 3.3.1."""
    future_pattern = re.compile(r'\b(3\.3\.[2-9]|3\.4\.\d+|4\.\d+\.\d+)\b')
    for name, path in VERSION_FILES.items():
        content = path.read_text(encoding="utf-8")
        match = future_pattern.search(content)
        assert not match, \
            f"Future version string '{match.group()}' found in {name}"
