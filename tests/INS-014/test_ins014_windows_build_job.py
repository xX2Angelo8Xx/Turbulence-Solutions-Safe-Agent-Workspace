"""
Tests for INS-014: CI Windows Build Job

Verifies that the windows-build job in .github/workflows/release.yml
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
def windows_job(workflow):
    """Return the windows-build job definition."""
    return workflow["jobs"]["windows-build"]


@pytest.fixture(scope="module")
def windows_steps(windows_job):
    """Return the list of steps for the windows-build job."""
    return windows_job["steps"]


def test_windows_build_job_exists(workflow):
    assert "windows-build" in workflow["jobs"], "windows-build job is missing"


def test_windows_build_runs_on_windows_latest(windows_job):
    assert windows_job["runs-on"] == "windows-latest"


def test_windows_build_job_has_7_steps(windows_steps):
    assert len(windows_steps) == 8, (
        f"Expected 8 steps (added Python embeddable download step in INS-018), got {len(windows_steps)}: "
        + str([s.get("name") or s.get("uses") for s in windows_steps])
    )


def test_windows_build_checkout_step(windows_steps):
    uses_values = [s.get("uses", "") for s in windows_steps]
    assert "actions/checkout@v4" in uses_values, "actions/checkout@v4 step not found"


def test_windows_build_python_setup_step(windows_steps):
    uses_values = [s.get("uses", "") for s in windows_steps]
    assert "actions/setup-python@v5" in uses_values, "actions/setup-python@v5 step not found"


def test_windows_build_python_version_is_311(windows_steps):
    for step in windows_steps:
        if step.get("uses", "").startswith("actions/setup-python"):
            version = step.get("with", {}).get("python-version")
            assert version == "3.11", f"Expected python-version '3.11', got: {version!r}"
            return
    pytest.fail("No setup-python step found")


def test_windows_build_install_dependencies_step(windows_steps):
    names = [s.get("name", "") for s in windows_steps]
    assert "Install dependencies" in names, "Missing 'Install dependencies' step"


def test_windows_build_pip_install_command(windows_steps):
    for step in windows_steps:
        if step.get("name") == "Install dependencies":
            cmd = step.get("run", "")
            assert "pip install" in cmd, f"Expected pip install in run, got: {cmd!r}"
            assert ".[dev]" in cmd, f"Expected .[dev] in run, got: {cmd!r}"
            assert "-e" in cmd, f"Expected -e flag in run, got: {cmd!r}"
            return
    pytest.fail("'Install dependencies' step not found")


def test_windows_build_pyinstaller_step(windows_steps):
    names = [s.get("name", "") for s in windows_steps]
    assert "Build with PyInstaller" in names, "Missing 'Build with PyInstaller' step"


def test_windows_build_pyinstaller_references_launcher_spec(windows_steps):
    for step in windows_steps:
        if step.get("name") == "Build with PyInstaller":
            cmd = step.get("run", "")
            assert "pyinstaller" in cmd, f"Expected pyinstaller command, got: {cmd!r}"
            assert "launcher.spec" in cmd, f"Expected launcher.spec in command, got: {cmd!r}"
            return
    pytest.fail("'Build with PyInstaller' step not found")


def test_windows_build_inno_setup_install_step(windows_steps):
    names = [s.get("name", "") for s in windows_steps]
    assert "Install Inno Setup" in names, "Missing 'Install Inno Setup' step"


def test_windows_build_choco_command(windows_steps):
    for step in windows_steps:
        if step.get("name") == "Install Inno Setup":
            cmd = step.get("run", "")
            assert "choco" in cmd, f"Expected choco in command, got: {cmd!r}"
            assert "innosetup" in cmd, f"Expected innosetup in command, got: {cmd!r}"
            assert "-y" in cmd, f"Expected -y flag in command, got: {cmd!r}"
            return
    pytest.fail("'Install Inno Setup' step not found")


def test_windows_build_iscc_step(windows_steps):
    names = [s.get("name", "") for s in windows_steps]
    assert "Build installer" in names, "Missing 'Build installer' step"


def test_windows_build_iscc_references_setup_iss(windows_steps):
    for step in windows_steps:
        if step.get("name") == "Build installer":
            cmd = step.get("run", "")
            assert "iscc" in cmd, f"Expected iscc command, got: {cmd!r}"
            assert "src/installer/windows/setup.iss" in cmd, (
                f"Expected src/installer/windows/setup.iss in command, got: {cmd!r}"
            )
            return
    pytest.fail("'Build installer' step not found")


def test_windows_build_upload_artifact_step(windows_steps):
    uses_values = [s.get("uses", "") for s in windows_steps]
    assert "actions/upload-artifact@v4" in uses_values, "actions/upload-artifact@v4 step not found"


def test_windows_build_artifact_name_and_path(windows_steps):
    for step in windows_steps:
        if step.get("uses", "").startswith("actions/upload-artifact"):
            artifact_with = step.get("with", {})
            assert artifact_with.get("name") == "windows-installer", (
                f"Expected artifact name 'windows-installer', got: {artifact_with.get('name')!r}"
            )
            expected_path = "src/installer/windows/Output/AgentEnvironmentLauncher-Setup.exe"
            assert artifact_with.get("path") == expected_path, (
                f"Expected artifact path {expected_path!r}, got: {artifact_with.get('path')!r}"
            )
            return
    pytest.fail("No upload-artifact step found")
