"""
Tests for INS-015: CI macOS Build Jobs

Verifies that macos-intel-build and macos-arm-build jobs in
.github/workflows/release.yml contain all required steps with
correct parameters.
"""
import pathlib
import yaml
import pytest

REPO_ROOT = pathlib.Path(__file__).parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"


@pytest.fixture(scope="module")
def workflow():
    """Parse and return the full workflow YAML."""
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def intel_job(workflow):
    """Return the macos-intel-build job definition, or skip if removed."""
    if "macos-intel-build" not in workflow.get("jobs", {}):
        pytest.skip("macos-intel-build job was removed in FIX-011 (Intel Mac runners deprecated)")
    return workflow["jobs"]["macos-intel-build"]


@pytest.fixture(scope="module")
def arm_job(workflow):
    """Return the macos-arm-build job definition."""
    return workflow["jobs"]["macos-arm-build"]


@pytest.fixture(scope="module")
def intel_steps(intel_job):
    """Return steps for macos-intel-build."""
    return intel_job["steps"]


@pytest.fixture(scope="module")
def arm_steps(arm_job):
    """Return steps for macos-arm-build."""
    return arm_job["steps"]


# ---------------------------------------------------------------------------
# Job existence
# ---------------------------------------------------------------------------

def test_macos_intel_job_exists(workflow):
    """macos-intel-build job must NOT be defined (removed in FIX-011).

    GitHub Actions macOS 14+ runners are ARM-only. Intel Python cannot be
    installed on Apple Silicon. The Intel build job was dropped per user
    decision in FIX-011.
    """
    assert "macos-intel-build" not in workflow["jobs"], (
        "macos-intel-build job still exists in release.yml — "
        "it should have been removed in FIX-011"
    )


def test_macos_arm_job_exists(workflow):
    """macos-arm-build job must be defined."""
    assert "macos-arm-build" in workflow["jobs"]


# ---------------------------------------------------------------------------
# Runner labels
# ---------------------------------------------------------------------------

def test_macos_intel_runs_on_macos15(intel_job):
    """macos-intel-build must use the macos-15 runner."""
    assert intel_job["runs-on"] == "macos-15"


def test_macos_arm_runs_on_macos14(arm_job):
    """macos-arm-build must use the macos-14 runner."""
    assert arm_job["runs-on"] == "macos-14"


# ---------------------------------------------------------------------------
# Step count
# ---------------------------------------------------------------------------

def test_macos_intel_has_5_steps(intel_steps):
    """macos-intel-build must have exactly 5 steps."""
    assert len(intel_steps) == 5, (
        f"Expected 5 steps, got {len(intel_steps)}: "
        + str([s.get("name") or s.get("uses") for s in intel_steps])
    )


def test_macos_arm_has_5_steps(arm_steps):
    """macos-arm-build must have exactly 5 steps."""
    assert len(arm_steps) == 5, (
        f"Expected 5 steps, got {len(arm_steps)}: "
        + str([s.get("name") or s.get("uses") for s in arm_steps])
    )


# ---------------------------------------------------------------------------
# Checkout step
# ---------------------------------------------------------------------------

def test_macos_intel_checkout(intel_steps):
    """macos-intel-build must have actions/checkout@v4 step."""
    uses_values = [s.get("uses", "") for s in intel_steps]
    assert "actions/checkout@v4" in uses_values


def test_macos_arm_checkout(arm_steps):
    """macos-arm-build must have actions/checkout@v4 step."""
    uses_values = [s.get("uses", "") for s in arm_steps]
    assert "actions/checkout@v4" in uses_values


# ---------------------------------------------------------------------------
# Python setup step
# ---------------------------------------------------------------------------

def test_macos_intel_python_setup(intel_steps):
    """macos-intel-build must use actions/setup-python@v5."""
    uses_values = [s.get("uses", "") for s in intel_steps]
    assert "actions/setup-python@v5" in uses_values


def test_macos_arm_python_setup(arm_steps):
    """macos-arm-build must use actions/setup-python@v5."""
    uses_values = [s.get("uses", "") for s in arm_steps]
    assert "actions/setup-python@v5" in uses_values


def test_macos_intel_python_version(intel_steps):
    """macos-intel-build must specify python-version '3.11'."""
    for step in intel_steps:
        if step.get("uses", "").startswith("actions/setup-python"):
            assert step.get("with", {}).get("python-version") == "3.11"
            return
    pytest.fail("No setup-python step found in macos-intel-build")


def test_macos_arm_python_version(arm_steps):
    """macos-arm-build must specify python-version '3.11'."""
    for step in arm_steps:
        if step.get("uses", "").startswith("actions/setup-python"):
            assert step.get("with", {}).get("python-version") == "3.11"
            return
    pytest.fail("No setup-python step found in macos-arm-build")


# ---------------------------------------------------------------------------
# Install dependencies step
# ---------------------------------------------------------------------------

def test_macos_intel_install_deps(intel_steps):
    """macos-intel-build must have 'Install dependencies' step with pip install -e .[dev]."""
    for step in intel_steps:
        if step.get("name") == "Install dependencies":
            cmd = step.get("run", "")
            assert "pip install" in cmd
            assert "-e" in cmd
            assert ".[dev]" in cmd
            return
    pytest.fail("'Install dependencies' step not found in macos-intel-build")


def test_macos_arm_install_deps(arm_steps):
    """macos-arm-build must have 'Install dependencies' step with pip install -e .[dev]."""
    for step in arm_steps:
        if step.get("name") == "Install dependencies":
            cmd = step.get("run", "")
            assert "pip install" in cmd
            assert "-e" in cmd
            assert ".[dev]" in cmd
            return
    pytest.fail("'Install dependencies' step not found in macos-arm-build")


# ---------------------------------------------------------------------------
# PyInstaller step
# ---------------------------------------------------------------------------

def test_macos_intel_no_standalone_pyinstaller_step(intel_steps):
    """macos-intel-build must NOT have a standalone 'Build with PyInstaller' step.

    PyInstaller is invoked by build_dmg.sh with --target-arch; a standalone
    pyinstaller step would run before the script and pre-populate dist/launcher/,
    causing the script to skip the --target-arch build.
    """
    names = [s.get("name", "") for s in intel_steps]
    assert "Build with PyInstaller" not in names, (
        "macos-intel-build must not have a standalone 'Build with PyInstaller' step; "
        "PyInstaller is invoked with --target-arch inside build_dmg.sh"
    )


def test_macos_arm_no_standalone_pyinstaller_step(arm_steps):
    """macos-arm-build must NOT have a standalone 'Build with PyInstaller' step.

    PyInstaller is invoked by build_dmg.sh with --target-arch; a standalone
    pyinstaller step would run before the script and pre-populate dist/launcher/,
    causing the script to skip the --target-arch build.
    """
    names = [s.get("name", "") for s in arm_steps]
    assert "Build with PyInstaller" not in names, (
        "macos-arm-build must not have a standalone 'Build with PyInstaller' step; "
        "PyInstaller is invoked with --target-arch inside build_dmg.sh"
    )


# ---------------------------------------------------------------------------
# Build DMG step
# ---------------------------------------------------------------------------

def test_macos_intel_build_dmg_step_exists(intel_steps):
    """macos-intel-build must have a 'Build DMG' step."""
    names = [s.get("name", "") for s in intel_steps]
    assert "Build DMG" in names


def test_macos_arm_build_dmg_step_exists(arm_steps):
    """macos-arm-build must have a 'Build DMG' step."""
    names = [s.get("name", "") for s in arm_steps]
    assert "Build DMG" in names


def test_macos_intel_build_dmg_chmod(intel_steps):
    """macos-intel-build 'Build DMG' step must chmod +x the script."""
    for step in intel_steps:
        if step.get("name") == "Build DMG":
            cmd = step.get("run", "")
            assert "chmod +x" in cmd, f"Expected chmod +x in Build DMG run, got: {cmd!r}"
            assert "build_dmg.sh" in cmd
            return
    pytest.fail("'Build DMG' step not found in macos-intel-build")


def test_macos_arm_build_dmg_chmod(arm_steps):
    """macos-arm-build 'Build DMG' step must chmod +x the script."""
    for step in arm_steps:
        if step.get("name") == "Build DMG":
            cmd = step.get("run", "")
            assert "chmod +x" in cmd, f"Expected chmod +x in Build DMG run, got: {cmd!r}"
            assert "build_dmg.sh" in cmd
            return
    pytest.fail("'Build DMG' step not found in macos-arm-build")


def test_macos_intel_build_dmg_arch_arg(intel_steps):
    """macos-intel-build 'Build DMG' step must pass x86_64 to build_dmg.sh."""
    for step in intel_steps:
        if step.get("name") == "Build DMG":
            cmd = step.get("run", "")
            assert "x86_64" in cmd, f"Expected x86_64 architecture arg, got: {cmd!r}"
            return
    pytest.fail("'Build DMG' step not found in macos-intel-build")


def test_macos_arm_build_dmg_arch_arg(arm_steps):
    """macos-arm-build 'Build DMG' step must pass arm64 to build_dmg.sh."""
    for step in arm_steps:
        if step.get("name") == "Build DMG":
            cmd = step.get("run", "")
            assert "arm64" in cmd, f"Expected arm64 architecture arg, got: {cmd!r}"
            return
    pytest.fail("'Build DMG' step not found in macos-arm-build")


# ---------------------------------------------------------------------------
# Upload artifact step
# ---------------------------------------------------------------------------

def test_macos_intel_upload_artifact_step(intel_steps):
    """macos-intel-build must have actions/upload-artifact@v4 step."""
    uses_values = [s.get("uses", "") for s in intel_steps]
    assert "actions/upload-artifact@v4" in uses_values


def test_macos_arm_upload_artifact_step(arm_steps):
    """macos-arm-build must have actions/upload-artifact@v4 step."""
    uses_values = [s.get("uses", "") for s in arm_steps]
    assert "actions/upload-artifact@v4" in uses_values


def test_macos_intel_artifact_name(intel_steps):
    """macos-intel-build artifact name must be 'macos-intel-dmg'."""
    for step in intel_steps:
        if step.get("uses", "").startswith("actions/upload-artifact"):
            assert step.get("with", {}).get("name") == "macos-intel-dmg", (
                f"Expected macos-intel-dmg, got: {step.get('with', {}).get('name')!r}"
            )
            return
    pytest.fail("No upload-artifact step found in macos-intel-build")


def test_macos_arm_artifact_name(arm_steps):
    """macos-arm-build artifact name must be 'macos-arm-dmg'."""
    for step in arm_steps:
        if step.get("uses", "").startswith("actions/upload-artifact"):
            assert step.get("with", {}).get("name") == "macos-arm-dmg", (
                f"Expected macos-arm-dmg, got: {step.get('with', {}).get('name')!r}"
            )
            return
    pytest.fail("No upload-artifact step found in macos-arm-build")


def test_macos_intel_artifact_path_contains_dmg(intel_steps):
    """macos-intel-build artifact path must reference a .dmg file."""
    for step in intel_steps:
        if step.get("uses", "").startswith("actions/upload-artifact"):
            path = step.get("with", {}).get("path", "")
            assert ".dmg" in path, f"Expected .dmg in artifact path, got: {path!r}"
            return
    pytest.fail("No upload-artifact step found in macos-intel-build")


def test_macos_arm_artifact_path_contains_dmg(arm_steps):
    """macos-arm-build artifact path must reference a .dmg file."""
    for step in arm_steps:
        if step.get("uses", "").startswith("actions/upload-artifact"):
            path = step.get("with", {}).get("path", "")
            assert ".dmg" in path, f"Expected .dmg in artifact path, got: {path!r}"
            return
    pytest.fail("No upload-artifact step found in macos-arm-build")


# ---------------------------------------------------------------------------
# Regression: other jobs unaffected
# ---------------------------------------------------------------------------

def test_windows_build_job_still_exists(workflow):
    """windows-build job must still be present (regression guard)."""
    assert "windows-build" in workflow["jobs"]


def test_linux_build_job_still_exists(workflow):
    """linux-build job must still be present (regression guard)."""
    assert "linux-build" in workflow["jobs"]


def test_release_job_still_exists(workflow):
    """release job must still be present (regression guard)."""
    assert "release" in workflow["jobs"]
