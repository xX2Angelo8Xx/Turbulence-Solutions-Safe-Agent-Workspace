"""
FIX-036 — Version Consistency Tests
Verifies that the version string "2.1.0" is correctly set in all 5 canonical
locations and that docs/architecture.md references the new version.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
EXPECTED_VERSION: str = re.search(
    r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"',
    (REPO_ROOT / "src" / "launcher" / "config.py").read_text(encoding="utf-8"),
    re.MULTILINE,
).group(1)


def test_config_py_version() -> None:
    """config.py VERSION constant must be 2.1.0."""
    config = REPO_ROOT / "src" / "launcher" / "config.py"
    text = config.read_text(encoding="utf-8")
    match = re.search(r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match is not None, "VERSION constant not found in config.py"
    assert match.group(1) == EXPECTED_VERSION, (
        f"config.py VERSION is {match.group(1)!r}, expected {EXPECTED_VERSION!r}"
    )


def test_pyproject_toml_version() -> None:
    """pyproject.toml [project] version must be 2.1.0."""
    pyproject = REPO_ROOT / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match is not None, "version field not found in pyproject.toml"
    assert match.group(1) == EXPECTED_VERSION, (
        f"pyproject.toml version is {match.group(1)!r}, expected {EXPECTED_VERSION!r}"
    )


def test_setup_iss_version() -> None:
    """setup.iss MyAppVersion must be 2.1.0."""
    setup_iss = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    text = setup_iss.read_text(encoding="utf-8")
    match = re.search(r'#define\s+MyAppVersion\s+"([^"]+)"', text)
    assert match is not None, "MyAppVersion not found in setup.iss"
    assert match.group(1) == EXPECTED_VERSION, (
        f"setup.iss MyAppVersion is {match.group(1)!r}, expected {EXPECTED_VERSION!r}"
    )


def test_build_dmg_version() -> None:
    """build_dmg.sh APP_VERSION must be 2.1.0."""
    build_dmg = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
    text = build_dmg.read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION="([^"]+)"', text, re.MULTILINE)
    assert match is not None, "APP_VERSION not found in build_dmg.sh"
    assert match.group(1) == EXPECTED_VERSION, (
        f"build_dmg.sh APP_VERSION is {match.group(1)!r}, expected {EXPECTED_VERSION!r}"
    )


def test_build_appimage_version() -> None:
    """build_appimage.sh APP_VERSION must be 2.1.0."""
    build_appimage = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
    text = build_appimage.read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION="([^"]+)"', text, re.MULTILINE)
    assert match is not None, "APP_VERSION not found in build_appimage.sh"
    assert match.group(1) == EXPECTED_VERSION, (
        f"build_appimage.sh APP_VERSION is {match.group(1)!r}, expected {EXPECTED_VERSION!r}"
    )


def test_all_versions_identical() -> None:
    """All 5 version locations must contain the identical string."""
    versions: dict[str, str] = {}

    config = REPO_ROOT / "src" / "launcher" / "config.py"
    m = re.search(r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"', config.read_text(encoding="utf-8"), re.MULTILINE)
    assert m, "VERSION not found in config.py"
    versions["config.py"] = m.group(1)

    pyproject = REPO_ROOT / "pyproject.toml"
    m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"), re.MULTILINE)
    assert m, "version not found in pyproject.toml"
    versions["pyproject.toml"] = m.group(1)

    setup_iss = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
    m = re.search(r'#define\s+MyAppVersion\s+"([^"]+)"', setup_iss.read_text(encoding="utf-8"))
    assert m, "MyAppVersion not found in setup.iss"
    versions["setup.iss"] = m.group(1)

    build_dmg = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
    m = re.search(r'^APP_VERSION="([^"]+)"', build_dmg.read_text(encoding="utf-8"), re.MULTILINE)
    assert m, "APP_VERSION not found in build_dmg.sh"
    versions["build_dmg.sh"] = m.group(1)

    build_appimage = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
    m = re.search(r'^APP_VERSION="([^"]+)"', build_appimage.read_text(encoding="utf-8"), re.MULTILINE)
    assert m, "APP_VERSION not found in build_appimage.sh"
    versions["build_appimage.sh"] = m.group(1)

    unique = set(versions.values())
    assert len(unique) == 1, (
        f"Version mismatch across locations: {versions}"
    )
    assert unique.pop() == EXPECTED_VERSION, (
        f"All files agree but version is not {EXPECTED_VERSION!r}: {versions}"
    )


def test_architecture_md_references_new_version() -> None:
    """docs/architecture.md must reference FIX-036 (Bump Version to 2.1.0)."""
    arch = REPO_ROOT / "docs" / "architecture.md"
    text = arch.read_text(encoding="utf-8")
    assert "FIX-036" in text, "FIX-036 entry missing from docs/architecture.md"
    assert "2.1.0" in text, "2.1.0 not referenced in docs/architecture.md"
