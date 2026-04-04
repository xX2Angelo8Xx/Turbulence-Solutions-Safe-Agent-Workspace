"""Tests for FIX-077: Version bump to 3.2.2 (regression baseline).

Now that 3.2.3 is the current version, verifies that all 5 canonical
version files contain "3.2.3" and none contain the stale version string "3.2.2".
"""

import re
from pathlib import Path

from tests.shared.version_utils import CURRENT_VERSION

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_VERSION = CURRENT_VERSION
STALE_VERSION = "3.2.2"

_VERSION_FILES = [
    REPO_ROOT / "src" / "launcher" / "config.py",
    REPO_ROOT / "pyproject.toml",
    REPO_ROOT / "src" / "installer" / "windows" / "setup.iss",
    REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh",
    REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh",
]


def test_config_py_is_323() -> None:
    """VERSION constant in src/launcher/config.py must be 3.2.3."""
    config_path = REPO_ROOT / "src" / "launcher" / "config.py"
    assert config_path.exists(), f"config.py not found: {config_path}"
    content = config_path.read_text(encoding="utf-8")
    match = re.search(r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "VERSION constant not found in config.py"
    assert match.group(1) == EXPECTED_VERSION, (
        f"config.py VERSION is '{match.group(1)}', expected '{EXPECTED_VERSION}'"
    )


def test_pyproject_toml_is_323() -> None:
    """version field in pyproject.toml must be 3.2.3."""
    toml_path = REPO_ROOT / "pyproject.toml"
    assert toml_path.exists(), f"pyproject.toml not found: {toml_path}"
    content = toml_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "version field not found in pyproject.toml"
    assert match.group(1) == EXPECTED_VERSION, (
        f"pyproject.toml version is '{match.group(1)}', expected '{EXPECTED_VERSION}'"
    )


def test_setup_iss_is_323() -> None:
    """MyAppVersion define in src/installer/windows/setup.iss must be 3.2.3."""
    iss_path = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    assert iss_path.exists(), f"setup.iss not found: {iss_path}"
    content = iss_path.read_text(encoding="utf-8")
    match = re.search(r'^#define\s+MyAppVersion\s+"([^"]+)"', content, re.MULTILINE)
    assert match is not None, "MyAppVersion define not found in setup.iss"
    assert match.group(1) == EXPECTED_VERSION, (
        f"setup.iss MyAppVersion is '{match.group(1)}', expected '{EXPECTED_VERSION}'"
    )


def test_build_dmg_sh_is_323() -> None:
    """APP_VERSION in src/installer/macos/build_dmg.sh must be 3.2.3."""
    sh_path = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
    assert sh_path.exists(), f"build_dmg.sh not found: {sh_path}"
    content = sh_path.read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION="([^"]+)"', content, re.MULTILINE)
    assert match is not None, "APP_VERSION not found in build_dmg.sh"
    assert match.group(1) == EXPECTED_VERSION, (
        f"build_dmg.sh APP_VERSION is '{match.group(1)}', expected '{EXPECTED_VERSION}'"
    )


def test_build_appimage_sh_is_323() -> None:
    """APP_VERSION in src/installer/linux/build_appimage.sh must be 3.2.3."""
    sh_path = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
    assert sh_path.exists(), f"build_appimage.sh not found: {sh_path}"
    content = sh_path.read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION="([^"]+)"', content, re.MULTILINE)
    assert match is not None, "APP_VERSION not found in build_appimage.sh"
    assert match.group(1) == EXPECTED_VERSION, (
        f"build_appimage.sh APP_VERSION is '{match.group(1)}', expected '{EXPECTED_VERSION}'"
    )


def test_no_stale_322_in_any_version_file() -> None:
    """None of the 5 canonical version files may contain the stale version 3.2.2."""
    stale_found: dict[str, list[int]] = {}
    for path in _VERSION_FILES:
        assert path.exists(), f"Version file not found: {path}"
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if STALE_VERSION in line:
                stale_found.setdefault(str(path.relative_to(REPO_ROOT)), []).append(lineno)
    assert not stale_found, (
        f"Stale version '{STALE_VERSION}' still found in: {stale_found}"
    )


def test_all_version_files_agree() -> None:
    """All 5 canonical version files must reference the same version string 3.2.3."""
    versions: dict[str, str] = {}

    config_path = REPO_ROOT / "src" / "launcher" / "config.py"
    m = re.search(r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"', config_path.read_text(encoding="utf-8"), re.MULTILINE)
    assert m, "VERSION not found in config.py"
    versions["config.py"] = m.group(1)

    toml_path = REPO_ROOT / "pyproject.toml"
    m = re.search(r'^version\s*=\s*"([^"]+)"', toml_path.read_text(encoding="utf-8"), re.MULTILINE)
    assert m, "version not found in pyproject.toml"
    versions["pyproject.toml"] = m.group(1)

    iss_path = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    m = re.search(r'^#define\s+MyAppVersion\s+"([^"]+)"', iss_path.read_text(encoding="utf-8"), re.MULTILINE)
    assert m, "MyAppVersion not found in setup.iss"
    versions["setup.iss"] = m.group(1)

    dmg_path = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
    m = re.search(r'^APP_VERSION="([^"]+)"', dmg_path.read_text(encoding="utf-8"), re.MULTILINE)
    assert m, "APP_VERSION not found in build_dmg.sh"
    versions["build_dmg.sh"] = m.group(1)

    appimage_path = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
    m = re.search(r'^APP_VERSION="([^"]+)"', appimage_path.read_text(encoding="utf-8"), re.MULTILINE)
    assert m, "APP_VERSION not found in build_appimage.sh"
    versions["build_appimage.sh"] = m.group(1)

    unique = set(versions.values())
    assert len(unique) == 1, f"Version mismatch across sources: {versions}"
    assert unique.pop() == EXPECTED_VERSION, (
        f"All sources agree but version is not {EXPECTED_VERSION}: {versions}"
    )


# ---------------------------------------------------------------------------
# Edge-case tests added by Tester
# ---------------------------------------------------------------------------

def test_shared_version_utils_current_version_is_323() -> None:
    """CURRENT_VERSION from tests/shared/version_utils.py must match config.py."""
    assert CURRENT_VERSION == EXPECTED_VERSION, (
        f"tests/shared/version_utils.py CURRENT_VERSION is '{CURRENT_VERSION}', "
        f"expected '{EXPECTED_VERSION}'"
    )


def test_get_display_version_returns_323() -> None:
    """get_display_version() fallback path (PackageNotFoundError) must return CURRENT_VERSION."""
    import sys
    from importlib.metadata import PackageNotFoundError
    from unittest.mock import patch

    # Ensure we're not in a PyInstaller bundle during tests
    assert not getattr(sys, "_MEIPASS", None), (
        "Test must not run inside a PyInstaller bundle"
    )

    # Simulate the installed package being absent (fallback path) — this is the
    # path taken in PyInstaller bundles and clean envs, and must return VERSION.
    with patch(
        "importlib.metadata.version",
        side_effect=PackageNotFoundError("agent-environment-launcher"),
    ):
        import importlib
        import launcher.config as cfg
        importlib.reload(cfg)  # pick up the patched importlib.metadata.version
        result = cfg.get_display_version()

    assert result == EXPECTED_VERSION, (
        f"get_display_version() fallback returned '{result}', expected '{EXPECTED_VERSION}'"
    )


def test_check_for_update_no_update_when_at_same_version() -> None:
    """check_for_update must return (False, version) when latest tag matches current version."""
    import json
    from unittest.mock import MagicMock, patch

    mock_response_data = json.dumps({"tag_name": f"v{EXPECTED_VERSION}"}).encode()
    mock_response = MagicMock()
    mock_response.read.return_value = mock_response_data
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("launcher.core.updater.urllib.request.urlopen", return_value=mock_response):
        from launcher.core.updater import check_for_update
        update_available, latest_version = check_for_update(EXPECTED_VERSION)

    assert not update_available, (
        f"check_for_update reported update available when already at {EXPECTED_VERSION}"
    )
    assert latest_version == EXPECTED_VERSION, (
        f"check_for_update returned latest_version='{latest_version}', expected '{EXPECTED_VERSION}'"
    )


def test_check_for_update_detects_newer_version() -> None:
    """check_for_update must return (True, newer_version) when a newer tag exists."""
    import json
    from unittest.mock import MagicMock, patch

    _parts = EXPECTED_VERSION.split(".")
    _newer_patch = str(int(_parts[-1]) + 1)
    _newer_version = ".".join(_parts[:-1] + [_newer_patch])

    mock_response_data = json.dumps({"tag_name": f"v{_newer_version}"}).encode()
    mock_response = MagicMock()
    mock_response.read.return_value = mock_response_data
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("launcher.core.updater.urllib.request.urlopen", return_value=mock_response):
        from launcher.core.updater import check_for_update
        update_available, latest_version = check_for_update(EXPECTED_VERSION)

    assert update_available, (
        f"check_for_update failed to detect newer version '{_newer_version}' from current '{EXPECTED_VERSION}'"
    )
    assert latest_version == _newer_version


def test_parse_version_323_correct() -> None:
    """parse_version on EXPECTED_VERSION must yield the correct tuple."""
    from launcher.core.updater import parse_version
    expected_tuple = tuple(int(x) for x in EXPECTED_VERSION.split("."))
    assert parse_version(EXPECTED_VERSION) == expected_tuple, (
        f"parse_version('{EXPECTED_VERSION}') did not return {expected_tuple}"
    )


def test_no_stale_322_in_docs_version_bump_wp() -> None:
    """The FIX-078 dev-log must not accidentally re-introduce 3.2.2 as the current version."""
    dev_log = REPO_ROOT / "docs" / "workpackages" / "FIX-078" / "dev-log.md"
    assert dev_log.exists(), f"dev-log.md not found: {dev_log}"
    content = dev_log.read_text(encoding="utf-8")
    # dev-log must not use the stale 3.2.2 as the current version
    assert STALE_VERSION not in content or "stale" in content.lower() or "old" in content.lower(), (
        f"dev-log.md appears to use stale version '{STALE_VERSION}' without context"
    )
