"""
Tests for INS-017: CI Release Upload Job

Verifies that the release job in .github/workflows/release.yml correctly:
- Declares needs on all 4 platform build jobs
- Has permissions: contents: write
- Downloads all artifacts via actions/download-artifact@v4
- Creates a GitHub Release via softprops/action-gh-release@v2
- Attaches all platform artifacts using the correct glob
- Enables auto-generated release notes
"""
import pathlib
import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"

EXPECTED_NEEDS = {"windows-build", "macos-arm-build", "linux-build"}


@pytest.fixture(scope="module")
def workflow():
    """Parse and return the full workflow YAML."""
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def release_job(workflow):
    """Return the release job definition."""
    return workflow["jobs"]["release"]


@pytest.fixture(scope="module")
def release_steps(release_job):
    """Return the list of steps in the release job."""
    return release_job["steps"]


@pytest.fixture(scope="module")
def download_step(release_steps):
    """Return the download-artifact step."""
    for step in release_steps:
        uses = step.get("uses", "")
        if uses.startswith("actions/download-artifact"):
            return step
    return None


@pytest.fixture(scope="module")
def gh_release_step(release_steps):
    """Return the softprops/action-gh-release step."""
    for step in release_steps:
        uses = step.get("uses", "")
        if "softprops/action-gh-release" in uses:
            return step
    return None


# --- Job existence and structure ---

def test_release_job_exists(workflow):
    """release job must be present in the workflow."""
    assert "release" in workflow["jobs"], "release job is missing from workflow"


def test_release_job_runs_on_ubuntu_latest(release_job):
    """release job must run on ubuntu-latest."""
    assert release_job["runs-on"] == "ubuntu-latest"


def test_release_job_has_3_steps(release_steps):
    """release job must have exactly 5 steps.
    Updated: Fetch tags and Validate tag exist steps added for workflow_dispatch support.
    Steps: checkout, fetch-tags (conditional), validate-tag (conditional), download-artifacts, gh-release.
    """
    assert len(release_steps) == 5, (
        f"Expected 5 steps, got {len(release_steps)}: "
        + str([s.get("name") or s.get("uses") for s in release_steps])
    )


# --- Needs dependency ---

def test_release_needs_all_four_build_jobs(release_job):
    """release job must declare needs on all 3 platform build jobs.

    macos-intel-build was removed in FIX-011 (Intel Mac runners deprecated).
    """
    needs = set(release_job.get("needs", []))
    assert needs == EXPECTED_NEEDS, (
        f"Expected needs={EXPECTED_NEEDS}, got needs={needs}"
    )


def test_release_needs_windows_build(release_job):
    assert "windows-build" in release_job.get("needs", [])


def test_release_needs_macos_intel_build(release_job):
    """Regression: macos-intel-build must NOT be in release needs (removed in FIX-011)."""
    assert "macos-intel-build" not in release_job.get("needs", []), (
        "macos-intel-build should not be in release needs — job was removed in FIX-011"
    )


def test_release_needs_macos_arm_build(release_job):
    assert "macos-arm-build" in release_job.get("needs", [])


def test_release_needs_linux_build(release_job):
    assert "linux-build" in release_job.get("needs", [])


# --- Permissions ---

def test_release_job_has_permissions_key(release_job):
    """release job must declare permissions explicitly."""
    assert "permissions" in release_job, "release job is missing 'permissions' key"


def test_release_job_permissions_contents_write(release_job):
    """permissions.contents must be 'write' to allow creating GitHub Releases."""
    perms = release_job.get("permissions", {})
    assert perms.get("contents") == "write", (
        f"Expected permissions.contents=write, got {perms.get('contents')}"
    )


# --- Checkout step ---

def test_release_first_step_is_checkout(release_steps):
    """First step must be actions/checkout@v4."""
    first = release_steps[0]
    assert first.get("uses") == "actions/checkout@v4", (
        f"Expected first step to be actions/checkout@v4, got {first.get('uses')}"
    )


# --- Download artifact step ---

def test_download_artifact_step_exists(download_step):
    """A download-artifact step must exist."""
    assert download_step is not None, "No actions/download-artifact step found"


def test_download_artifact_uses_v4(download_step):
    """download-artifact must use @v4."""
    assert download_step is not None
    assert download_step["uses"] == "actions/download-artifact@v4", (
        f"Expected actions/download-artifact@v4, got {download_step['uses']}"
    )


def test_download_artifact_path_is_release_assets(download_step):
    """download-artifact path must be 'release-assets'."""
    assert download_step is not None
    path = download_step.get("with", {}).get("path")
    assert path == "release-assets", (
        f"Expected path=release-assets, got path={path}"
    )


def test_download_artifact_has_no_name_key(download_step):
    """download-artifact must not specify a 'name' — downloads ALL artifacts."""
    assert download_step is not None
    name = download_step.get("with", {}).get("name")
    assert name is None, (
        f"download-artifact 'name' key should be absent (downloads all), but got name={name}"
    )


# --- GitHub Release step ---

def test_gh_release_step_exists(gh_release_step):
    """A softprops/action-gh-release step must exist."""
    assert gh_release_step is not None, "No softprops/action-gh-release step found"


def test_gh_release_uses_v2(gh_release_step):
    """softprops/action-gh-release must use @v2."""
    assert gh_release_step is not None
    assert gh_release_step["uses"] == "softprops/action-gh-release@v2", (
        f"Expected softprops/action-gh-release@v2, got {gh_release_step['uses']}"
    )


def test_gh_release_files_glob(gh_release_step):
    """files must be 'release-assets/**/*' to attach all platform artifacts."""
    assert gh_release_step is not None
    files = gh_release_step.get("with", {}).get("files")
    assert files == "release-assets/**/*", (
        f"Expected files=release-assets/**/*, got files={files}"
    )


def test_gh_release_generate_release_notes_true(gh_release_step):
    """generate_release_notes must be true for auto-generated release notes."""
    assert gh_release_step is not None
    generate = gh_release_step.get("with", {}).get("generate_release_notes")
    assert generate is True, (
        f"Expected generate_release_notes=true, got {generate}"
    )


# --- No hardcoded secrets ---

def test_release_job_no_hardcoded_github_token(release_steps):
    """No step should hardcode a GITHUB_TOKEN or PAT value."""
    import re
    token_pattern = re.compile(r"ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]+")
    for step in release_steps:
        step_str = yaml.dump(step)
        assert not token_pattern.search(step_str), (
            f"Hardcoded token found in step: {step.get('name') or step.get('uses')}"
        )


# --- YAML validity (round-trip sanity) ---

def test_workflow_yaml_is_valid(workflow):
    """Workflow must parse as valid YAML without errors.

    Note: PyYAML parses the bare 'on:' key as the boolean True (YAML 1.1
    spec), so we check for True rather than the string 'on'.
    """
    assert isinstance(workflow, dict), "Workflow did not parse as a dict"
    assert "jobs" in workflow
    # PyYAML evaluates bare 'on' as True (YAML 1.1 boolean coercion)
    assert True in workflow, "workflow 'on:' trigger block is missing"
