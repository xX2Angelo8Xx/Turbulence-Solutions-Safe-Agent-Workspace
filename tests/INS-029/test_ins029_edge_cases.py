"""Edge-case tests for INS-029: Version bump to 3.2.4 — Tester additions.

Covers staleness checks for all 5 installer files and the egg-info cache,
plus version ordering and format boundary conditions not covered by the
Developer's basic per-file assertions.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_VERSION = "3.2.4"
STALE_VERSION = "3.2.3"

_VERSION_FILES = [
    REPO_ROOT / "src" / "launcher" / "config.py",
    REPO_ROOT / "pyproject.toml",
    REPO_ROOT / "src" / "installer" / "windows" / "setup.iss",
    REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh",
    REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh",
]


# ---------------------------------------------------------------------------
# Staleness checks for installer files not covered by Developer tests
# ---------------------------------------------------------------------------

def test_no_stale_version_in_setup_iss() -> None:
    """setup.iss MyAppVersion define must not be the stale 3.2.3."""
    iss_path = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    content = iss_path.read_text(encoding="utf-8")
    match = re.search(r'#define\s+MyAppVersion\s+"([^"]+)"', content)
    assert match is not None, "MyAppVersion define not found in setup.iss"
    assert match.group(1) != STALE_VERSION, (
        "setup.iss MyAppVersion still references stale 3.2.3"
    )


def test_no_stale_version_in_build_dmg() -> None:
    """build_dmg.sh APP_VERSION must not be the stale 3.2.3."""
    dmg_path = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
    content = dmg_path.read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "APP_VERSION not found in build_dmg.sh"
    assert match.group(1) != STALE_VERSION, (
        "build_dmg.sh APP_VERSION still references stale 3.2.3"
    )


def test_no_stale_version_in_build_appimage() -> None:
    """build_appimage.sh APP_VERSION must not be the stale 3.2.3."""
    appimage_path = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
    content = appimage_path.read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "APP_VERSION not found in build_appimage.sh"
    assert match.group(1) != STALE_VERSION, (
        "build_appimage.sh APP_VERSION still references stale 3.2.3"
    )


# ---------------------------------------------------------------------------
# Version ordering — confirm 3.2.4 > 3.2.3
# ---------------------------------------------------------------------------

def test_version_tuple_greater_than_stale() -> None:
    """Parsed 3.2.4 must compare strictly greater than 3.2.3."""
    from launcher.core.updater import parse_version  # noqa: PLC0415

    current = parse_version(EXPECTED_VERSION)
    stale = parse_version(STALE_VERSION)
    assert current > stale, (
        f"Tuple {current} is not > {stale} — version ordering is wrong"
    )


def test_version_tuple_components() -> None:
    """parse_version('3.2.4') must return exactly (3, 2, 4)."""
    from launcher.core.updater import parse_version  # noqa: PLC0415

    result = parse_version(EXPECTED_VERSION)
    assert result == (3, 2, 4), (
        f"parse_version('{EXPECTED_VERSION}') returned {result}, expected (3, 2, 4)"
    )


# ---------------------------------------------------------------------------
# Egg-info / installed metadata cache
# ---------------------------------------------------------------------------

def test_egg_info_pkg_info_version_not_future() -> None:
    """egg-info PKG-INFO must not claim a version newer than 3.2.4.

    The egg-info is a pip-generated artifact; it may legitimately be stale
    (e.g. if the dev venv was not re-installed after a bump). We only assert it
    does not have a *future* version string that would indicate a mis-merge.
    """
    import pytest
    from launcher.core.updater import parse_version  # noqa: PLC0415

    egg_info_dirs = list((REPO_ROOT / "src").glob("*.egg-info"))
    if not egg_info_dirs:
        pytest.skip("No egg-info directory found — package not installed in editable mode")

    for egg_dir in egg_info_dirs:
        for meta_file in ("PKG-INFO", "METADATA"):
            meta_path = egg_dir / meta_file
            if not meta_path.exists():
                continue
            content = meta_path.read_text(encoding="utf-8")
            match = re.search(r"^Version:\s*(.+)$", content, re.MULTILINE)
            if match:
                installed_ver = match.group(1).strip()
                # Stale (older) egg-info is acceptable; a future version is not.
                assert parse_version(installed_ver) <= parse_version(EXPECTED_VERSION), (
                    f"{meta_path.relative_to(REPO_ROOT)} Version header is "
                    f"'{installed_ver}' which is NEWER than '{EXPECTED_VERSION}' — "
                    "possible mis-merge or incorrect bump"
                )
