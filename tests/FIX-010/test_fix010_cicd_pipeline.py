"""
Tests for FIX-010: Fix CI/CD Release Pipeline Failures

Validates the fixes for BUG-036, BUG-037, and BUG-038:
  1. macos-intel-build uses macos-15 runner (BUG-036)
  2. macos-intel-build setup-python has architecture: x64 (BUG-036)
  3. macOS jobs do NOT have standalone 'Build with PyInstaller' step
  4. linux-build does NOT have standalone 'Build with PyInstaller' step
  5. windows-build DOES have 'Build with PyInstaller' step (unchanged)
  6. setup.iss Source path navigates to repo root via ..\\..\\.. (BUG-037)
  7. All 3 build scripts have version 1.0.0 (BUG-038)
  8. Version consistency across setup.iss, build_dmg.sh, build_appimage.sh, pyproject.toml
"""
import pathlib
import re
import tomllib

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"
SETUP_ISS = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
BUILD_APPIMAGE = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
PYPROJECT = REPO_ROOT / "pyproject.toml"


@pytest.fixture(scope="module")
def workflow():
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def intel_job(workflow):
    return workflow["jobs"]["macos-intel-build"]


@pytest.fixture(scope="module")
def arm_job(workflow):
    return workflow["jobs"]["macos-arm-build"]


@pytest.fixture(scope="module")
def linux_job(workflow):
    return workflow["jobs"]["linux-build"]


@pytest.fixture(scope="module")
def windows_job(workflow):
    return workflow["jobs"]["windows-build"]


# ---------------------------------------------------------------------------
# BUG-036: macos-13 runner replaced with macos-15
# ---------------------------------------------------------------------------

def test_macos_intel_runner_is_macos15(intel_job):
    """macos-intel-build must use macos-15 runner (BUG-036 fix)."""
    assert intel_job["runs-on"] == "macos-15", (
        f"Expected runs-on 'macos-15', got: {intel_job['runs-on']!r}. "
        "macos-13 is no longer available in GitHub Actions."
    )


def test_macos_intel_runner_is_not_macos13(intel_job):
    """Regression: macos-intel-build must NOT use the deprecated macos-13 runner."""
    assert intel_job["runs-on"] != "macos-13", (
        "macos-13 is deprecated and unavailable. Runner must be macos-15."
    )


def test_macos_intel_setup_python_has_architecture_x64(intel_job):
    """macos-intel-build setup-python step must specify architecture: x64 (BUG-036 fix)."""
    steps = intel_job["steps"]
    for step in steps:
        if step.get("uses", "").startswith("actions/setup-python"):
            arch = step.get("with", {}).get("architecture")
            assert arch == "x64", (
                f"Expected architecture 'x64' in macos-intel-build setup-python, "
                f"got: {arch!r}. Without x64 the runner may install an ARM Python."
            )
            return
    pytest.fail("No setup-python step found in macos-intel-build")


def test_macos_arm_runner_is_still_macos14(arm_job):
    """macos-arm-build runner must remain macos-14 (Apple Silicon — unchanged)."""
    assert arm_job["runs-on"] == "macos-14", (
        f"Expected macos-arm-build runs-on 'macos-14', got: {arm_job['runs-on']!r}"
    )


# ---------------------------------------------------------------------------
# Redundant PyInstaller step removal from macOS and Linux jobs
# ---------------------------------------------------------------------------

def test_macos_intel_has_no_standalone_pyinstaller_step(intel_job):
    """macos-intel-build must not have a standalone 'Build with PyInstaller' step.

    The step prevents --target-arch from being effective because dist/launcher/
    already exists when build_dmg.sh runs, causing the script to skip the build.
    """
    names = [s.get("name", "") for s in intel_job["steps"]]
    assert "Build with PyInstaller" not in names, (
        "macos-intel-build has a standalone 'Build with PyInstaller' step. "
        "Remove it — PyInstaller is invoked with --target-arch inside build_dmg.sh."
    )


def test_macos_arm_has_no_standalone_pyinstaller_step(arm_job):
    """macos-arm-build must not have a standalone 'Build with PyInstaller' step."""
    names = [s.get("name", "") for s in arm_job["steps"]]
    assert "Build with PyInstaller" not in names, (
        "macos-arm-build has a standalone 'Build with PyInstaller' step. "
        "Remove it — PyInstaller is invoked with --target-arch inside build_dmg.sh."
    )


def test_linux_build_has_no_standalone_pyinstaller_step(linux_job):
    """linux-build must not have a standalone 'Build with PyInstaller' step."""
    names = [s.get("name", "") for s in linux_job["steps"]]
    assert "Build with PyInstaller" not in names, (
        "linux-build has a standalone 'Build with PyInstaller' step. "
        "Remove it — PyInstaller is invoked inside build_appimage.sh."
    )


def test_windows_build_retains_pyinstaller_step(windows_job):
    """windows-build must still have its 'Build with PyInstaller' step.

    Windows does not use a build script for PyInstaller; the step must remain.
    """
    names = [s.get("name", "") for s in windows_job["steps"]]
    assert "Build with PyInstaller" in names, (
        "windows-build is missing the 'Build with PyInstaller' step — it must be kept."
    )


def test_windows_build_pyinstaller_references_launcher_spec(windows_job):
    """windows-build PyInstaller step must reference launcher.spec."""
    for step in windows_job["steps"]:
        if step.get("name") == "Build with PyInstaller":
            cmd = step.get("run", "")
            assert "pyinstaller" in cmd, f"Expected pyinstaller command, got: {cmd!r}"
            assert "launcher.spec" in cmd, f"Expected launcher.spec in command, got: {cmd!r}"
            return
    pytest.fail("'Build with PyInstaller' step not found in windows-build")


# ---------------------------------------------------------------------------
# BUG-037: setup.iss Source path navigates to repo root
# ---------------------------------------------------------------------------

def test_setup_iss_source_path_navigates_to_repo_root():
    """setup.iss Source must start with ..\\..\\..\\ to navigate from the .iss
    directory (src/installer/windows/) three levels up to the repo root.
    """
    content = SETUP_ISS.read_text(encoding="utf-8")
    match = re.search(r'Source:\s*"([^"]+)"', content)
    assert match, "No Source: path found in setup.iss"
    source_val = match.group(1)
    parts = [p for p in source_val.split("\\") if p]
    assert parts[:3] == ["..", "..", ".."], (
        f"Source path {source_val!r} must start with three ..\\  segments "
        "to navigate from src/installer/windows/ to the repo root. "
        "Without this, Inno Setup looks in src/installer/windows/dist/ which does not exist."
    )


def test_setup_iss_source_path_is_not_bare_dist():
    """setup.iss Source must NOT use the bare 'dist\\\\launcher\\\\*' path (regression guard)."""
    content = SETUP_ISS.read_text(encoding="utf-8")
    match = re.search(r'Source:\s*"([^"]+)"', content)
    assert match, "No Source: path found in setup.iss"
    source_val = match.group(1)
    parts = [p for p in source_val.split("\\") if p]
    assert parts[0] != "dist", (
        f"Source path {source_val!r} starts with 'dist' which resolves from "
        "src/installer/windows/dist/ — that path does not exist. "
        "Use ..\\\\..\\\\..\\\\  prefix to navigate to repo root."
    )


# ---------------------------------------------------------------------------
# BUG-038: Version numbers synced to 1.0.0
# ---------------------------------------------------------------------------

def test_setup_iss_version_is_1_0_0():
    """setup.iss MyAppVersion must be 1.0.0 (BUG-038 fix)."""
    content = SETUP_ISS.read_text(encoding="utf-8")
    assert 'MyAppVersion "1.0.0"' in content, (
        "setup.iss MyAppVersion must be 1.0.0 to match pyproject.toml. Got something else."
    )


def test_build_dmg_version_is_1_0_0():
    """build_dmg.sh APP_VERSION must be 1.0.0 (BUG-038 fix)."""
    content = BUILD_DMG.read_text(encoding="utf-8")
    assert 'APP_VERSION="1.0.0"' in content, (
        "build_dmg.sh APP_VERSION must be 1.0.0 to match pyproject.toml. Got something else."
    )


def test_build_appimage_version_is_1_0_0():
    """build_appimage.sh APP_VERSION must be 1.0.0 (BUG-038 fix)."""
    content = BUILD_APPIMAGE.read_text(encoding="utf-8")
    assert 'APP_VERSION="1.0.0"' in content, (
        "build_appimage.sh APP_VERSION must be 1.0.0 to match pyproject.toml. Got something else."
    )


def test_setup_iss_version_is_not_old():
    """Regression: setup.iss must not contain 0.1.0 version."""
    content = SETUP_ISS.read_text(encoding="utf-8")
    assert 'MyAppVersion "0.1.0"' not in content, (
        "setup.iss still contains version 0.1.0 — must be updated to 1.0.0."
    )


def test_build_dmg_version_is_not_old():
    """Regression: build_dmg.sh must not contain APP_VERSION 0.1.0."""
    content = BUILD_DMG.read_text(encoding="utf-8")
    assert 'APP_VERSION="0.1.0"' not in content, (
        "build_dmg.sh still contains version 0.1.0 — must be updated to 1.0.0."
    )


def test_build_appimage_version_is_not_old():
    """Regression: build_appimage.sh must not contain APP_VERSION 0.1.0."""
    content = BUILD_APPIMAGE.read_text(encoding="utf-8")
    assert 'APP_VERSION="0.1.0"' not in content, (
        "build_appimage.sh still contains version 0.1.0 — must be updated to 1.0.0."
    )


# ---------------------------------------------------------------------------
# Version consistency across all build artifacts and pyproject.toml
# ---------------------------------------------------------------------------

def _extract_pyproject_version() -> str:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]


def _extract_iss_version() -> str:
    content = SETUP_ISS.read_text(encoding="utf-8")
    match = re.search(r'#define MyAppVersion\s+"([^"]+)"', content)
    assert match, "Could not parse MyAppVersion from setup.iss"
    return match.group(1)


def _extract_dmg_version() -> str:
    content = BUILD_DMG.read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION="([^"]+)"', content, re.MULTILINE)
    assert match, "Could not parse APP_VERSION from build_dmg.sh"
    return match.group(1)


def _extract_appimage_version() -> str:
    content = BUILD_APPIMAGE.read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION="([^"]+)"', content, re.MULTILINE)
    assert match, "Could not parse APP_VERSION from build_appimage.sh"
    return match.group(1)


def test_setup_iss_version_matches_pyproject():
    """setup.iss version must match pyproject.toml project version."""
    pyproject_ver = _extract_pyproject_version()
    iss_ver = _extract_iss_version()
    assert iss_ver == pyproject_ver, (
        f"setup.iss version {iss_ver!r} does not match "
        f"pyproject.toml version {pyproject_ver!r}"
    )


def test_build_dmg_version_matches_pyproject():
    """build_dmg.sh APP_VERSION must match pyproject.toml project version."""
    pyproject_ver = _extract_pyproject_version()
    dmg_ver = _extract_dmg_version()
    assert dmg_ver == pyproject_ver, (
        f"build_dmg.sh version {dmg_ver!r} does not match "
        f"pyproject.toml version {pyproject_ver!r}"
    )


def test_build_appimage_version_matches_pyproject():
    """build_appimage.sh APP_VERSION must match pyproject.toml project version."""
    pyproject_ver = _extract_pyproject_version()
    appimage_ver = _extract_appimage_version()
    assert appimage_ver == pyproject_ver, (
        f"build_appimage.sh version {appimage_ver!r} does not match "
        f"pyproject.toml version {pyproject_ver!r}"
    )


def test_all_build_scripts_have_same_version():
    """All three build scripts must have the same version string."""
    iss_ver = _extract_iss_version()
    dmg_ver = _extract_dmg_version()
    appimage_ver = _extract_appimage_version()
    assert iss_ver == dmg_ver == appimage_ver, (
        f"Version mismatch across build scripts: "
        f"setup.iss={iss_ver!r}, build_dmg.sh={dmg_ver!r}, "
        f"build_appimage.sh={appimage_ver!r}"
    )
