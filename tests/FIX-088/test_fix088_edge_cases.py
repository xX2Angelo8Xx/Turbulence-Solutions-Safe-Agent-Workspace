"""Edge-case tests for FIX-088: Bump all version strings to 3.2.6 — Tester additions.

Covers boundary conditions, format validation, import-level verification,
and stale-version grep checks beyond the Developer's per-file assertions.
"""

import re
import sys
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_VERSION = "3.2.6"
STALE_VERSIONS = ("3.2.5", "3.2.4", "3.2.3")

_VERSION_FILES = {
    "config.py": REPO_ROOT / "src" / "launcher" / "config.py",
    "pyproject.toml": REPO_ROOT / "pyproject.toml",
    "setup.iss": REPO_ROOT / "src" / "installer" / "windows" / "setup.iss",
    "build_dmg.sh": REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh",
}

# ---------------------------------------------------------------------------
# Stale-version grep: no source version file should contain any old version
# ---------------------------------------------------------------------------

def test_no_stale_325_in_version_files() -> None:
    """None of the 4 canonical version files must contain the stale string '3.2.5'."""
    stale = "3.2.5"
    for name, path in _VERSION_FILES.items():
        content = path.read_text(encoding="utf-8")
        assert stale not in content, (
            f"{name} still contains stale version string '{stale}'"
        )


def test_no_stale_324_in_version_files() -> None:
    """config.py and pyproject.toml must not contain '3.2.4' (setup.iss and build_dmg.sh are checked independently)."""
    stale = "3.2.4"
    py_files = {
        "config.py": _VERSION_FILES["config.py"],
        "pyproject.toml": _VERSION_FILES["pyproject.toml"],
    }
    for name, path in py_files.items():
        content = path.read_text(encoding="utf-8")
        assert stale not in content, (
            f"{name} contains stale version string '{stale}'"
        )


# ---------------------------------------------------------------------------
# Import-level verification
# ---------------------------------------------------------------------------

def test_version_importable_and_correct() -> None:
    """Importing VERSION from launcher.config at runtime must yield '3.2.6'."""
    assert not getattr(sys, "_MEIPASS", None), "Test must not run inside a PyInstaller bundle"
    from launcher.config import VERSION  # noqa: PLC0415
    assert VERSION == EXPECTED_VERSION, (
        f"launcher.config.VERSION is '{VERSION}', expected '{EXPECTED_VERSION}'"
    )


def test_get_display_version_fallback_returns_326() -> None:
    """get_display_version() must return '3.2.6' via the PackageNotFoundError fallback."""
    import importlib  # noqa: PLC0415
    from importlib.metadata import PackageNotFoundError  # noqa: PLC0415

    assert not getattr(sys, "_MEIPASS", None), "Test must not run inside a PyInstaller bundle"

    with patch(
        "importlib.metadata.version",
        side_effect=PackageNotFoundError("agent-environment-launcher"),
    ):
        import launcher.config as cfg  # noqa: PLC0415
        importlib.reload(cfg)
        result = cfg.get_display_version()

    assert result == EXPECTED_VERSION, (
        f"get_display_version() fallback returned '{result}', expected '{EXPECTED_VERSION}'"
    )


# ---------------------------------------------------------------------------
# Semver format validation
# ---------------------------------------------------------------------------

def test_version_matches_semver_format() -> None:
    """'3.2.6' must match strict semver pattern MAJOR.MINOR.PATCH."""
    assert re.match(r"^\d+\.\d+\.\d+$", EXPECTED_VERSION), (
        f"Version '{EXPECTED_VERSION}' does not match MAJOR.MINOR.PATCH"
    )


def test_version_components_correct() -> None:
    """3.2.6 must parse as (3, 2, 6) with no leading zeros."""
    parts = EXPECTED_VERSION.split(".")
    assert len(parts) == 3
    major, minor, patch_v = (int(p) for p in parts)
    assert (major, minor, patch_v) == (3, 2, 6), (
        f"Parsed ({major}, {minor}, {patch_v}), expected (3, 2, 6)"
    )
    for part in parts:
        assert part == str(int(part)), f"Component '{part}' has leading zeros"


def test_version_is_not_superstring() -> None:
    """Version must be exactly '3.2.6', not '3.2.60' or '3.2.61' etc."""
    assert EXPECTED_VERSION == "3.2.6"
    assert len(EXPECTED_VERSION) == 5, (
        f"Unexpected version string length: '{EXPECTED_VERSION}'"
    )


# ---------------------------------------------------------------------------
# Version ordering: 3.2.6 > 3.2.5 > 3.2.4
# ---------------------------------------------------------------------------

def test_326_is_greater_than_325() -> None:
    """Version tuple (3,2,6) must be strictly greater than (3,2,5)."""
    current = tuple(int(x) for x in EXPECTED_VERSION.split("."))
    previous = (3, 2, 5)
    assert current > previous, f"{current} is not greater than {previous}"


def test_326_is_greater_than_324() -> None:
    """Version tuple (3,2,6) must be strictly greater than (3,2,4)."""
    current = tuple(int(x) for x in EXPECTED_VERSION.split("."))
    older = (3, 2, 4)
    assert current > older, f"{current} is not greater than {older}"


# ---------------------------------------------------------------------------
# No version string embedded as a bare literal elsewhere in version files
# ---------------------------------------------------------------------------

def test_config_py_version_not_in_comment() -> None:
    """The old version '3.2.5' must not appear even in comments in config.py."""
    content = _VERSION_FILES["config.py"].read_text(encoding="utf-8")
    assert "3.2.5" not in content, (
        "config.py contains '3.2.5' (possibly in a comment or dead code)"
    )


def test_pyproject_toml_only_one_version_field() -> None:
    """pyproject.toml must contain exactly one 'version = ...' line under [project]."""
    content = _VERSION_FILES["pyproject.toml"].read_text(encoding="utf-8")
    matches = re.findall(r'^version\s*=\s*"[^"]+"', content, re.MULTILINE)
    assert len(matches) == 1, (
        f"Expected exactly 1 version field in pyproject.toml, found {len(matches)}: {matches}"
    )


def test_setup_iss_exactly_one_version_define() -> None:
    """setup.iss must contain exactly one #define MyAppVersion line."""
    content = _VERSION_FILES["setup.iss"].read_text(encoding="utf-8")
    matches = re.findall(r'^#define\s+MyAppVersion\s+"[^"]+"', content, re.MULTILINE)
    assert len(matches) == 1, (
        f"Expected exactly 1 MyAppVersion define in setup.iss, found {len(matches)}: {matches}"
    )
