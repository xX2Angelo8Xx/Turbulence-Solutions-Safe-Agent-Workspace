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


def test_linux_build_job_exists(workflow):
    assert "linux-build" in workflow["jobs"], "linux-build job is missing from workflow"


def test_linux_build_runs_on_ubuntu_latest(linux_job):
    assert linux_job["runs-on"] == "ubuntu-latest"


def test_linux_build_job_has_7_steps(linux_steps):
    assert len(linux_steps) == 7, (
        f"Expected 7 steps, got {len(linux_steps)}: "
        + str([s.get("name") or s.get("uses") for s in linux_steps])
    )


def test_linux_build_checkout_step(linux_steps):
    uses_values = [s.get("uses", "") for s in linux_steps]
    assert "actions/checkout@v4" in uses_values


def test_linux_build_python_setup_step(linux_steps):
    uses_values = [s.get("uses", "") for s in linux_steps]
    assert "actions/setup-python@v5" in uses_values


def test_linux_build_python_version_is_311(linux_steps):
    for step in linux_steps:
        if step.get("uses", "").startswith("actions/setup-python"):
            version = step.get("with", {}).get("python-version")
            assert version == "3.11", f"Expected python-version '3.11', got: {version!r}"
            return
    pytest.fail("No setup-python step found")


def test_linux_build_install_dependencies_step(linux_steps):
    names = [s.get("name", "") for s in linux_steps]
    assert "Install dependencies" in names


def test_linux_build_pip_install_command(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Install dependencies":
            cmd = step.get("run", "")
            assert "pip install" in cmd
            assert "-e" in cmd
            assert ".[dev]" in cmd
            return
    pytest.fail("'Install dependencies' step not found")


def test_linux_build_install_libfuse2_step(linux_steps):
    names = [s.get("name", "") for s in linux_steps]
    assert "Install libfuse2" in names


def test_linux_build_libfuse2_command_uses_sudo(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Install libfuse2":
            cmd = step.get("run", "")
            assert "sudo" in cmd, f"Expected sudo, got: {cmd!r}"
            return
    pytest.fail("'Install libfuse2' step not found")


def test_linux_build_libfuse2_command_uses_apt_get(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Install libfuse2":
            cmd = step.get("run", "")
            assert "apt-get" in cmd, f"Expected apt-get, got: {cmd!r}"
            return
    pytest.fail("'Install libfuse2' step not found")


def test_linux_build_libfuse2_command_installs_libfuse2(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Install libfuse2":
            cmd = step.get("run", "")
            assert "libfuse2" in cmd, f"Expected libfuse2 package name, got: {cmd!r}"
            return
    pytest.fail("'Install libfuse2' step not found")


def test_linux_build_libfuse2_command_is_noninteractive(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Install libfuse2":
            cmd = step.get("run", "")
            assert "-y" in cmd, f"Expected -y flag, got: {cmd!r}"
            return
    pytest.fail("'Install libfuse2' step not found")


def test_linux_build_libfuse2_apt_get_update_before_install(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Install libfuse2":
            cmd = step.get("run", "")
            update_pos = cmd.find("apt-get update")
            install_pos = cmd.find("apt-get install")
            assert update_pos != -1, "apt-get update not found"
            assert install_pos != -1, "apt-get install not found"
            assert update_pos < install_pos, "apt-get update must appear before apt-get install"
            return
    pytest.fail("'Install libfuse2' step not found")


def test_linux_build_pyinstaller_step(linux_steps):
    names = [s.get("name", "") for s in linux_steps]
    assert "Build with PyInstaller" in names


def test_linux_build_pyinstaller_references_launcher_spec(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Build with PyInstaller":
            cmd = step.get("run", "")
            assert "pyinstaller" in cmd
            assert "launcher.spec" in cmd
            return
    pytest.fail("'Build with PyInstaller' step not found")


def test_linux_build_appimage_step(linux_steps):
    names = [s.get("name", "") for s in linux_steps]
    assert "Build AppImage" in names


def test_linux_build_appimage_script_path(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Build AppImage":
            cmd = step.get("run", "")
            assert "src/installer/linux/build_appimage.sh" in cmd
            return
    pytest.fail("'Build AppImage' step not found")


def test_linux_build_appimage_arch_argument_is_x86_64(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Build AppImage":
            cmd = step.get("run", "")
            assert "x86_64" in cmd, f"Expected x86_64 arg, got: {cmd!r}"
            return
    pytest.fail("'Build AppImage' step not found")


def test_linux_build_appimage_chmod_present(linux_steps):
    for step in linux_steps:
        if step.get("name") == "Build AppImage":
            cmd = step.get("run", "")
            assert "chmod +x" in cmd, f"Expected chmod +x, got: {cmd!r}"
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
            assert chmod_pos < script_pos, "chmod +x must appear before script invocation"
            return
    pytest.fail("'Build AppImage' step not found")


def test_linux_build_upload_artifact_step(linux_steps):
    uses_values = [s.get("uses", "") for s in linux_steps]
    assert "actions/upload-artifact@v4" in uses_values


def test_linux_build_artifact_name_is_linux_appimage(linux_steps):
    for step in linux_steps:
        if step.get("uses", "").startswith("actions/upload-artifact"):
            name = step.get("with", {}).get("name")
            assert name == "linux-appimage", f"Expected 'linux-appimage', got: {name!r}"
            return
    pytest.fail("No upload-artifact step found")


def test_linux_build_artifact_path_is_dist_appimage_glob(linux_steps):
    for step in linux_steps:
        if step.get("uses", "").startswith("actions/upload-artifact"):
            path = step.get("with", {}).get("path")
            assert path == "dist/*.AppImage", f"Expected 'dist/*.AppImage', got: {path!r}"
            return
    pytest.fail("No upload-artifact step found")


def _step_index(steps, name_or_uses: str) -> int:
    for i, step in enumerate(steps):
        if step.get("name") == name_or_uses or step.get("uses", "") == name_or_uses:
            return i
    return -1


def test_linux_build_libfuse2_before_pyinstaller(linux_steps):
    libfuse_idx = _step_index(linux_steps, "Install libfuse2")
    pyinstaller_idx = _step_index(linux_steps, "Build with PyInstaller")
    assert libfuse_idx != -1, "'Install libfuse2' not found"
    assert pyinstaller_idx != -1, "'Build with PyInstaller' not found"
    assert libfuse_idx < pyinstaller_idx, "Install libfuse2 must come before Build with PyInstaller"


def test_linux_build_pyinstaller_before_appimage(linux_steps):
    pyinstaller_idx = _step_index(linux_steps, "Build with PyInstaller")
    appimage_idx = _step_index(linux_steps, "Build AppImage")
    assert pyinstaller_idx != -1, "'Build with PyInstaller' not found"
    assert appimage_idx != -1, "'Build AppImage' not found"
    assert pyinstaller_idx < appimage_idx, "Build with PyInstaller must come before Build AppImage"


def test_linux_build_upload_is_last_step(linux_steps):
    upload_idx = -1
    for i, step in enumerate(linux_steps):
        if step.get("uses", "").startswith("actions/upload-artifact"):
            upload_idx = i
    assert upload_idx == len(linux_steps) - 1, (
        f"Upload must be the last step (index {len(linux_steps) - 1}), found at {upload_idx}"
    )


def test_release_job_needs_linux_build(workflow):
    release_job = workflow["jobs"].get("release", {})
    needs = release_job.get("needs", [])
    assert "linux-build" in needs, f"release job must need linux-build, got: {needs!r}"
