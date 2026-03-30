"""
Tests for MNT-005: Add CI validate-version job to release workflow.

These tests verify the structure and content of .github/workflows/release.yml
to ensure the validate-version job is correctly defined.
"""
import os
import re
import pytest
import yaml

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RELEASE_YML = os.path.join(REPO_ROOT, ".github", "workflows", "release.yml")


@pytest.fixture(scope="module")
def release_yml_text():
    with open(RELEASE_YML, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def release_yml_data(release_yml_text):
    return yaml.safe_load(release_yml_text)


# ---------------------------------------------------------------------------
# Job structure tests
# ---------------------------------------------------------------------------

def test_validate_version_job_exists(release_yml_data):
    """The validate-version job must be defined in the workflow."""
    assert "validate-version" in release_yml_data["jobs"], (
        "validate-version job not found in release.yml"
    )


def test_validate_version_runs_on_ubuntu(release_yml_data):
    """The validate-version job must use ubuntu-latest."""
    job = release_yml_data["jobs"]["validate-version"]
    assert job["runs-on"] == "ubuntu-latest"


def test_checkout_step_present(release_yml_data):
    """The validate-version job must check out the repository."""
    job = release_yml_data["jobs"]["validate-version"]
    steps = job["steps"]
    checkout_steps = [s for s in steps if str(s.get("uses", "")).startswith("actions/checkout")]
    assert len(checkout_steps) >= 1, "No actions/checkout step found in validate-version job"


def test_windows_build_needs_validate_version(release_yml_data):
    """windows-build must depend on validate-version."""
    job = release_yml_data["jobs"]["windows-build"]
    needs = job.get("needs", [])
    if isinstance(needs, str):
        needs = [needs]
    assert "validate-version" in needs, "windows-build does not have needs: [validate-version]"


def test_macos_arm_build_needs_validate_version(release_yml_data):
    """macos-arm-build must depend on validate-version."""
    job = release_yml_data["jobs"]["macos-arm-build"]
    needs = job.get("needs", [])
    if isinstance(needs, str):
        needs = [needs]
    assert "validate-version" in needs, "macos-arm-build does not have needs: [validate-version]"


def test_linux_build_needs_validate_version(release_yml_data):
    """linux-build must depend on validate-version."""
    job = release_yml_data["jobs"]["linux-build"]
    needs = job.get("needs", [])
    if isinstance(needs, str):
        needs = [needs]
    assert "validate-version" in needs, "linux-build does not have needs: [validate-version]"


def test_release_job_unchanged(release_yml_data):
    """release job must still depend on all 3 build jobs."""
    job = release_yml_data["jobs"]["release"]
    needs = job.get("needs", [])
    if isinstance(needs, str):
        needs = [needs]
    for expected in ["windows-build", "macos-arm-build", "linux-build"]:
        assert expected in needs, f"release job missing dependency on {expected}"


# ---------------------------------------------------------------------------
# Version extraction logic tests
# ---------------------------------------------------------------------------

def test_push_trigger_handled(release_yml_text):
    """validate-version must use github.ref_name for push triggers."""
    assert "github.ref_name" in release_yml_text, (
        "github.ref_name not found — push trigger not handled"
    )


def test_workflow_dispatch_trigger_handled(release_yml_text):
    """validate-version must use github.event.inputs.tag for workflow_dispatch."""
    assert "github.event.inputs.tag" in release_yml_text, (
        "github.event.inputs.tag not found — workflow_dispatch trigger not handled"
    )


def test_version_extraction_strip_v(release_yml_text):
    """Version extraction must strip the leading 'v' from the tag."""
    assert "${TAG#v}" in release_yml_text, (
        "'${TAG#v}' shell strip not found — version extraction logic missing"
    )


# ---------------------------------------------------------------------------
# File-check coverage tests
# ---------------------------------------------------------------------------

def test_config_py_checked(release_yml_text):
    """validate-version must check src/launcher/config.py."""
    assert "src/launcher/config.py" in release_yml_text


def test_pyproject_toml_checked(release_yml_text):
    """validate-version must check pyproject.toml."""
    assert "pyproject.toml" in release_yml_text


def test_setup_iss_checked(release_yml_text):
    """validate-version must check src/installer/windows/setup.iss."""
    assert "src/installer/windows/setup.iss" in release_yml_text


def test_build_dmg_checked(release_yml_text):
    """validate-version must check src/installer/macos/build_dmg.sh."""
    assert "src/installer/macos/build_dmg.sh" in release_yml_text


def test_build_appimage_checked(release_yml_text):
    """validate-version must check src/installer/linux/build_appimage.sh."""
    assert "src/installer/linux/build_appimage.sh" in release_yml_text


# ---------------------------------------------------------------------------
# Error reporting tests
# ---------------------------------------------------------------------------

def test_error_reporting_expected_label(release_yml_text):
    """Error output must include 'Expected:' label for debugging."""
    assert "Expected:" in release_yml_text, "Error reporting missing 'Expected:' label"


def test_error_reporting_actual_label(release_yml_text):
    """Error output must include 'Actual:' label for debugging."""
    assert "Actual:" in release_yml_text, "Error reporting missing 'Actual:' label"


def test_failure_exits_nonzero(release_yml_text):
    """On mismatch the job must exit 1 to fail the workflow."""
    assert "exit 1" in release_yml_text, "No 'exit 1' found — mismatch does not fail workflow"


# ---------------------------------------------------------------------------
# Success summary test
# ---------------------------------------------------------------------------

def test_success_summary_present(release_yml_text):
    """A success summary must be printed when all files match."""
    assert "All 5 version files match" in release_yml_text, (
        "Success summary message not found in validate-version job"
    )


# ---------------------------------------------------------------------------
# Job ordering test (validate-version defined before build jobs)
# ---------------------------------------------------------------------------

def test_validate_version_defined_before_build_jobs(release_yml_text):
    """validate-version job definition must appear before the build jobs."""
    pos_validate = release_yml_text.find("validate-version:")
    pos_windows = release_yml_text.find("windows-build:")
    pos_macos = release_yml_text.find("macos-arm-build:")
    pos_linux = release_yml_text.find("linux-build:")
    assert pos_validate != -1, "validate-version job missing"
    assert pos_validate < pos_windows, "validate-version must appear before windows-build"
    assert pos_validate < pos_macos, "validate-version must appear before macos-arm-build"
    assert pos_validate < pos_linux, "validate-version must appear before linux-build"
