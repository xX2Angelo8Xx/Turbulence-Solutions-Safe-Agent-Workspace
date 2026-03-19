"""
Tests for INS-013: CI Workflow Skeleton
Verifies that .github/workflows/release.yml exists, has valid YAML,
and contains the correct trigger and job structure.
"""
import pathlib
import yaml
import pytest

REPO_ROOT = pathlib.Path(__file__).parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"

EXPECTED_JOBS = [
    "windows-build",
    "macos-arm-build",
    "linux-build",
    "release",
    # macos-intel-build removed in FIX-011 (Intel Mac runners deprecated)
]


@pytest.fixture(scope="module")
def workflow():
    """Parse and return the workflow YAML once for all tests."""
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_workflow_file_exists():
    """Workflow file must exist at the expected path."""
    assert WORKFLOW_PATH.exists(), f"Workflow file not found: {WORKFLOW_PATH}"


def test_workflow_yaml_valid():
    """Workflow file must be valid YAML (no parse errors)."""
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        content = yaml.safe_load(f)
    assert content is not None, "Workflow YAML parsed to None — file may be empty"
    assert isinstance(content, dict), "Workflow YAML root must be a mapping"


def test_trigger_push_tags(workflow):
    """Workflow must trigger on push to tags matching v*.*.*

    Note: PyYAML (YAML 1.1) parses the bare word 'on' as boolean True.
    The workflow file uses standard GitHub Actions 'on:' syntax which is
    correct; we look up the parsed key as True here.
    """
    # PyYAML parses 'on' (YAML 1.1 boolean alias) as Python True
    on_section = workflow.get(True) or workflow.get("on")
    assert on_section is not None, "Missing 'on' trigger key in workflow"
    assert "push" in on_section, "Missing 'push' trigger"
    push_section = on_section["push"]
    assert "tags" in push_section, "Missing 'tags' under push trigger"
    tags = push_section["tags"]
    assert "v*.*.*" in tags, f"Expected 'v*.*.*' in tags list, got: {tags}"


def test_all_5_jobs_defined(workflow):
    """All 4 expected job keys must be present.

    macos-intel-build was removed in FIX-011 (Intel Mac runners deprecated).
    """
    assert "jobs" in workflow, "Missing 'jobs' key in workflow"
    defined_jobs = set(workflow["jobs"].keys())
    for job in EXPECTED_JOBS:
        assert job in defined_jobs, f"Missing job: {job}"


def test_windows_build_runs_on(workflow):
    """windows-build must use windows-latest runner."""
    assert workflow["jobs"]["windows-build"]["runs-on"] == "windows-latest"


def test_macos_intel_runs_on(workflow):
    """Regression: macos-intel-build must NOT exist in workflow (removed in FIX-011)."""
    assert "macos-intel-build" not in workflow["jobs"], (
        "macos-intel-build job still exists — it should have been removed in FIX-011"
    )


def test_macos_arm_runs_on(workflow):
    """macos-arm-build must use macos-14 (Apple Silicon) runner."""
    assert workflow["jobs"]["macos-arm-build"]["runs-on"] == "macos-14"


def test_linux_build_runs_on(workflow):
    """linux-build must use ubuntu-latest runner."""
    assert workflow["jobs"]["linux-build"]["runs-on"] == "ubuntu-latest"


def test_release_runs_on(workflow):
    """release job must use ubuntu-latest runner."""
    assert workflow["jobs"]["release"]["runs-on"] == "ubuntu-latest"


def test_release_needs_all_builds(workflow):
    """release job must declare needs on all 3 build jobs.

    macos-intel-build was removed in FIX-011 (Intel Mac runners deprecated).
    """
    needs = workflow["jobs"]["release"].get("needs", [])
    expected_builds = ["windows-build", "macos-arm-build", "linux-build"]
    needs_set = set(needs)
    for build_job in expected_builds:
        assert build_job in needs_set, f"release.needs is missing: {build_job}"


def test_each_job_has_steps(workflow):
    """Every job must have at least one step."""
    for job_name, job_def in workflow["jobs"].items():
        steps = job_def.get("steps", [])
        assert len(steps) >= 1, f"Job '{job_name}' has no steps"


def test_workflow_name(workflow):
    """Top-level workflow name must be 'Build and Release'."""
    assert workflow.get("name") == "Build and Release", (
        f"Expected workflow name 'Build and Release', got: {workflow.get('name')}"
    )
