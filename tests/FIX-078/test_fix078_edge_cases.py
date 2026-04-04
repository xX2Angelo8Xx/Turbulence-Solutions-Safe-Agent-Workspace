"""Edge-case tests for FIX-078: Version bump to 3.2.3 — Tester additions.

Covers boundary conditions, format validation, and integration checks that
go beyond the Developer's basic per-file assertions.
"""

import re
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.shared.version_utils import CURRENT_VERSION

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_VERSION = CURRENT_VERSION
STALE_VERSION = "3.2.3"
STALE_PREV = "3.2.2"

_VERSION_FILES = [
    REPO_ROOT / "src" / "launcher" / "config.py",
    REPO_ROOT / "pyproject.toml",
    REPO_ROOT / "src" / "installer" / "windows" / "setup.iss",
    REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh",
    REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh",
]

# ---------------------------------------------------------------------------
# Format validation
# ---------------------------------------------------------------------------

def test_version_matches_semver_format() -> None:
    """The version string '3.2.3' must match the strict semver pattern MAJOR.MINOR.PATCH."""
    pattern = re.compile(r"^\d+\.\d+\.\d+$")
    assert pattern.match(EXPECTED_VERSION), (
        f"Version '{EXPECTED_VERSION}' does not match strict semver format MAJOR.MINOR.PATCH"
    )


def test_version_components_no_leading_zeros() -> None:
    """Each component of the current version must parse as a non-negative integer with no leading zeros."""
    parts = EXPECTED_VERSION.split(".")
    assert len(parts) == 3, f"Expected 3 components, got {len(parts)}: {parts}"
    expected_ints = tuple(int(p) for p in parts)
    for part, expected in zip(parts, expected_ints):
        # A leading-zero int would stringify differently, e.g. "03" != str(int("03"))
        assert part == str(int(part)), (
            f"Component '{part}' has leading zero or invalid format"
        )
        assert int(part) == expected, (
            f"Component '{part}' parses to {int(part)}, expected {expected}"
        )


def test_version_is_exactly_323_not_superstring() -> None:
    """Version string must match strict semver format with no extra characters."""
    assert re.match(r'^\d+\.\d+\.\d+$', EXPECTED_VERSION), (
        f"Version string '{EXPECTED_VERSION}' does not match strict semver format"
    )


# ---------------------------------------------------------------------------
# Python-level import verification
# ---------------------------------------------------------------------------

def test_version_imported_from_config_module() -> None:
    """Importing VERSION from launcher.config must yield '3.2.3' at runtime."""
    from launcher.config import VERSION  # noqa: PLC0415
    assert VERSION == EXPECTED_VERSION, (
        f"launcher.config.VERSION is '{VERSION}', expected '{EXPECTED_VERSION}'"
    )


def test_get_display_version_fallback_returns_323() -> None:
    """get_display_version() must return '3.2.3' via the PackageNotFoundError fallback."""
    import importlib
    import sys
    from importlib.metadata import PackageNotFoundError  # noqa: PLC0415

    assert not getattr(sys, "_MEIPASS", None), "Test must not run inside a PyInstaller bundle"

    # Patch at the source so the local `from importlib.metadata import version`
    # inside get_display_version() picks up the mock.
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
# Tuple / comparison semantics
# ---------------------------------------------------------------------------

def test_parse_version_323_returns_correct_tuple() -> None:
    """parse_version on EXPECTED_VERSION must return the correct tuple."""
    from launcher.core.updater import parse_version  # noqa: PLC0415

    expected_tuple = tuple(int(x) for x in EXPECTED_VERSION.split("."))
    result = parse_version(EXPECTED_VERSION)
    assert result == expected_tuple, (
        f"parse_version('{EXPECTED_VERSION}') returned {result}, expected {expected_tuple}"
    )


def test_version_tuple_greater_than_322_tuple() -> None:
    """Parsed 3.2.3 must compare strictly greater than 3.2.2 (confirms a proper bump)."""
    from launcher.core.updater import parse_version  # noqa: PLC0415

    current = parse_version(EXPECTED_VERSION)
    stale = parse_version(STALE_VERSION)
    assert current > stale, (
        f"Tuple {current} is not > {stale} — version was not actually bumped"
    )


# ---------------------------------------------------------------------------
# Installer integrity
# ---------------------------------------------------------------------------

def test_setup_iss_exactly_one_version_define() -> None:
    """setup.iss must contain exactly one #define MyAppVersion line."""
    iss_path = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    assert iss_path.exists(), f"setup.iss not found: {iss_path}"
    lines = iss_path.read_text(encoding="utf-8").splitlines()
    version_defines = [ln for ln in lines if re.match(r"^#define\s+MyAppVersion\s+", ln)]
    assert len(version_defines) == 1, (
        f"Expected exactly 1 #define MyAppVersion in setup.iss, found {len(version_defines)}: {version_defines}"
    )


def test_no_stale_previous_version_321_in_any_version_file() -> None:
    """None of the 5 canonical version files may contain the older stale version 3.2.1 — belt-and-suspenders check."""
    stale_found: dict[str, list[int]] = {}
    for path in _VERSION_FILES:
        assert path.exists(), f"Version file not found: {path}"
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if STALE_PREV in line:
                stale_found.setdefault(str(path.relative_to(REPO_ROOT)), []).append(lineno)
    assert not stale_found, (
        f"Old stale version '{STALE_PREV}' found in: {stale_found}"
    )
