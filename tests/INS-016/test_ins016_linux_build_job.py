"""
Tests for INS-016: CI Linux Build Job

Verifies that the linux-build job in .github/workflows/release.yml
contains all required steps with correct parameters.
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
def linux_job(workflow):
    """Return the linux-build job definition."""
    return workflow["jobs"]["linux-build"]


@pytest.fixture(scope="module")
def linux_steps(linux_job):
    """Return the list of steps for the linux-build job."""
    return linux_job["steps"]


# ---------------------------------------------------------------------------
# Job-level checks
# ---------------------------------------------------------------------------

def test_linux_build_job_exists(workflow):
    assert "linux-build" in workflow["jobs"], "linux-build job is missing from workflow"


def test_linux_build_runs_on_ubuntu_latest(linux_job):
    assert linux_job["runs-on"] == "ubuntu-latest", (
        f"Expected runs-on 'ubuntu-latest', got: {linux_job['runs-on']!r}"
    )


def test_linux_build_job_has_6_steps(linux_steps):
    assert len(linux_steps) == 6, (
        f"Expected 6 steps, got {len(linux_steps)}: "
        + str([s.get("name") or s.get("uses") for s in linux_steps])
    )


# ---------------------------------------------------------------------------
# Checkout step
# ---------------------------------------------------------------------------

def test_linux_build_checkout_step(linux_steps):
    uses_values = [s.get("uses", "") for s in linux_steps]
    assert "actions/checkout@v4" in uses_values, "actions/checkout@v4 step not found"


# ---------------------------------------------------------------------------
# Python setup step
# ---------------------------------------------------------------------------

def test_linux_build_python_setup_step(linux_steps):
    uses_values = [s.get("uses", "") for s in linux_steps]
    assert "actions/setup-python@v5" in uses_values, "actions/setup-python@v5 step not found"


def test_linux_build_python_version_is_311(linux_steps):
    for step in linux_steps:
        if step.get("uses", "").startswith("actions/setup-python"):
            version = step.get("with", {}).get("python-version")
            assert version == "3.11", f"Expected python-version '3.11', got: {version!r}"
            return
    pytest.fail("No setup-python step found")


# ---------------------------------------------------------------------------
# Install dependencies step
# ---------------------------------------------------------------------------

def test_linux_build_install_dependencies_step(linux_steps):
    names = [s.get("name", "") for s in linux_steps]
    assert "Install dependencies" in names, "Missing 'Install dependencies' step"


def test_linux_build_pip_install_command(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Install dependencies":
            cmd = step.get("run", "")
            assert "pip install" in cmd, f"Expected pip install in run, got: {cmd!r}"
            assert "-e" in cmd, f"Expected -e flag in run, got: {cmd!r}"
            assert ".[dev]" in cmd, f"Expected .[dev] in run, got: {cmd!r}"
            return
    pytest.fail("'Install dependencies' step not found")


# ---------------------------------------------------------------------------
# Install libfuse2 step
# ---------------------------------------------------------------------------

def test_linux_build_install_libfuse2_step(linux_steps):
    names = [s.get("name", "") for s in linux_steps]
    assert "Install libfuse2" in names, "Missing 'Install libfuse2' step"


def test_linux_build_libfuse2_command_uses_sudo(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Install libfuse2":
            cmd = step.get("run", "")
            assert "sudo" in cmd, f"Expected sudo in libfuse2 command, got: {cmd!r}"
            return
    pytest.fail("'Install libfuse2' step not found")


def test_linux_build_libfuse2_command_uses_apt_get(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Install libfuse2":
            cmd = step.get("run", "")
            assert "apt-get" in cmd, f"Expected apt-get in libfuse2 command, got: {cmd!r}"
            return
    pytest.fail("'Install libfuse2' step not found")


def test_linux_build_libfuse2_command_installs_libfuse2(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Install libfuse2":
            cmd = step.get("run", "")
            assert "libfuse2" in cmd, f"Expected libfuse2 package name in command, got: {cmd!r}"
            return
    pytest.fail("'Install libfuse2' step not found")


def test_linux_build_libfuse2_command_is_noninteractive(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Install libfuse2":
            cmd = step.get("run", "")
            assert "-y" in cmd, f"Expected -y (non-interactive) flag in command, got: {cmd!r}"
            return
    pytest.fail("'Install libfuse2' step not found")


def test_linux_build_libfuse2_apt_get_update_before_install(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Install libfuse2":
            cmd = step.get("run", "")
            update_pos = cmd.find("apt-get update")
            install_pos = cmd.find("apt-get install")
            assert update_pos != -1, "apt-get update not found in libfuse2 command"
            assert install_pos != -1, "apt-get install not found in libfuse2 command"
            assert update_pos < install_pos, (
                "apt-get update must appear before apt-get install"
            )
            return
    pytest.fail("'Install libfuse2' step not found")


# ---------------------------------------------------------------------------
# PyInstaller step
# ---------------------------------------------------------------------------

def test_linux_build_no_standalone_pyinstaller_step(linux_steps):
    """linux-build must NOT have a standalone 'Build with PyInstaller' step.

    PyInstaller is invoked by build_appimage.sh; a standalone pyinstaller step
    would pre-populate dist/launcher/ and cause the script to skip the build.
    """
    names = [s.get("name", "") for s in linux_steps]
    assert "Build with PyInstaller" not in names, (
        "linux-build must not have a standalone 'Build with PyInstaller' step"
    )


def test_linux_build_appimage_script_handles_pyinstaller(linux_steps):
    """linux-build 'Build AppImage' step must invoke build_appimage.sh
    which runs PyInstaller internally.
    """
    for step in linux_steps:
        if step.get("name") == "Build AppImage":
            cmd = step.get("run", "")
            assert "build_appimage.sh" in cmd, (
                f"Expected build_appimage.sh in Build AppImage step, got: {cmd!r}"
            )
            return
    pytest.fail("'Build AppImage' step not found")


# ---------------------------------------------------------------------------
# Build AppImage step
# ---------------------------------------------------------------------------

def test_linux_build_appimage_step(linux_steps):
    names = [s.get("name", "") for s in linux_steps]
    assert "Build AppImage" in names, "Missing 'Build AppImage' step"


def test_linux_build_appimage_script_path(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Build AppImage":
            cmd = step.get("run", "")
            assert "src/installer/linux/build_appimage.sh" in cmd, (
                f"Expected script path src/installer/linux/build_appimage.sh, got: {cmd!r}"
            )
            return
    pytest.fail("'Build AppImage' step not found")


def test_linux_build_appimage_arch_argument_is_x86_64(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Build AppImage":
            cmd = step.get("run", "")
            assert "x86_64" in cmd, (
                f"Expected x86_64 architecture argument, got: {cmd!r}"
            )
            return
    pytest.fail("'Build AppImage' step not found")


def test_linux_build_appimage_chmod_present(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Build AppImage":
            cmd = step.get("run", "")
            assert "chmod +x" in cmd, (
                f"Expected 'chmod +x' in Build AppImage step, got: {cmd!r}"
            )
            return
    pytest.fail("'Build AppImage' step not found")


def test_linux_build_appimage_chmod_before_script(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Build AppImage":
            cmd = step.get("run", "")
            chmod_pos = cmd.find("chmod +x")
            script_pos = cmd.find("build_appimage.sh x86_64")
            assert chmod_pos != -1, "chmod +x not found"
            assert script_pos != -1, "build_appimage.sh x86_64 not found"
            assert chmod_pos < script_pos, (
                "chmod +x must appear before build_appimage.sh invocation"
            )
            return
    pytest.fail("'Build AppImage' step not found")


# ---------------------------------------------------------------------------
# Upload artifact step
# ---------------------------------------------------------------------------

def test_linux_build_upload_artifact_step(linux_steps):
    uses_values = [s.get("uses", "") for s in linux_steps]
    assert "actions/upload-artifact@v4" in uses_values, "actions/upload-artifact@v4 not found"


def test_linux_build_artifact_name_is_linux_appimage(linux_steps):
    for step in linux_steps:
        if step.get("uses", "").startswith("actions/upload-artifact"):
            name = step.get("with", {}).get("name")
            assert name == "linux-appimage", (
                f"Expected artifact name 'linux-appimage', got: {name!r}"
            )
            return
    pytest.fail("No upload-artifact step found")


def test_linux_build_artifact_path_is_dist_appimage_glob(linux_steps):
    for step in linux_steps:
        if step.get("uses", "").startswith("actions/upload-artifact"):
            path = step.get("with", {}).get("path")
            assert path == "dist/*.AppImage", (
                f"Expected artifact path 'dist/*.AppImage', got: {path!r}"
            )
            return
    pytest.fail("No upload-artifact step found")


# ---------------------------------------------------------------------------
# Step ordering checks
# ---------------------------------------------------------------------------

def _step_index(steps, name_or_uses: str) -> int:
    """Return the index of a step by its name or uses value, or -1 if not found."""
    for i, step in enumerate(steps):
        if step.get("name") == name_or_uses or step.get("uses", "") == name_or_uses:
            return i
    return -1


def test_linux_build_libfuse2_before_pyinstaller(linux_steps):
    libfuse_idx = _step_index(linux_steps, "Install libfuse2")
    appimage_idx = _step_index(linux_steps, "Build AppImage")
    assert libfuse_idx != -1, "'Install libfuse2' step not found"
    assert appimage_idx != -1, "'Build AppImage' step not found"
    assert libfuse_idx < appimage_idx, (
        "Install libfuse2 must appear before Build AppImage"
    )


def test_linux_build_pyinstaller_before_appimage(linux_steps):
    appimage_idx = _step_index(linux_steps, "Build AppImage")
    upload_idx = _step_index(linux_steps, "Upload Linux AppImage")
    assert appimage_idx != -1, "'Build AppImage' step not found"
    assert upload_idx != -1, "'Upload Linux AppImage' step not found"
    assert appimage_idx < upload_idx, (
        "Build AppImage must appear before Upload Linux AppImage"
    )


def test_linux_build_upload_is_last_step(linux_steps):
    upload_idx = -1
    for i, step in enumerate(linux_steps):
        if step.get("uses", "").startswith("actions/upload-artifact"):
            upload_idx = i
    assert upload_idx == len(linux_steps) - 1, (
        f"Upload artifact must be the last step (index {len(linux_steps) - 1}), "
        f"found at index {upload_idx}"
    )


# ---------------------------------------------------------------------------
# Release job dependency check
# ---------------------------------------------------------------------------

def test_release_job_needs_linux_build(workflow):
    release_job = workflow["jobs"].get("release", {})
    needs = release_job.get("needs", [])
    assert "linux-build" in needs, (
        f"release job must list linux-build in 'needs', got: {needs!r}"
    )
