"""
INS-017 Tester edge-case tests — CI Release Upload Job

Extra coverage beyond the 21 developer tests:
1. No env: GITHUB_TOKEN leak in release job steps
2. release job needs count is exactly 4 (not under/over)
3. download-artifact path does not conflict with any upload-artifact names
4. No floating action tags (@main, @master, @latest) in the release job
5. No shell: override in any release job step
6. All action version tags in the release job use the approved pinned versions
7. Token not injected at workflow-level env either
8. release job does not declare job-level env block
9. setup-python is NOT used in the release job (it only needs checkout/download/release)
"""
import pathlib
import re
import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"

FLOATING_TAG_RE = re.compile(r"@(main|master|latest|head)", re.IGNORECASE)
PAT_RE = re.compile(r"ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]+")


@pytest.fixture(scope="module")
def workflow():
    """Parse the full workflow YAML once per module."""
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def release_job(workflow):
    return workflow["jobs"]["release"]


@pytest.fixture(scope="module")
def release_steps(release_job):
    return release_job["steps"]


@pytest.fixture(scope="module")
def all_build_jobs(workflow):
    """Return the dict of all build jobs (everything except 'release')."""
    return {k: v for k, v in workflow["jobs"].items() if k != "release"}


# ---------------------------------------------------------------------------
# 1. No env: GITHUB_TOKEN leak in any release step
# ---------------------------------------------------------------------------

def test_release_steps_no_env_github_token(release_steps):
    """No release step should set GITHUB_TOKEN via an env: block."""
    for step in release_steps:
        env_block = step.get("env", {}) or {}
        assert "GITHUB_TOKEN" not in env_block, (
            f"Step '{step.get('name') or step.get('uses')}' leaks GITHUB_TOKEN "
            "via env: — the action uses the automatic token via permissions, no "
            "explicit env injection required."
        )


# ---------------------------------------------------------------------------
# 2. release job needs count is exactly 4
# ---------------------------------------------------------------------------

def test_release_needs_exactly_four_jobs(release_job):
    """needs must list exactly 3 build jobs — no more, no less.

    macos-intel-build was removed in FIX-011 (Intel Mac runners deprecated).
    """
    needs = release_job.get("needs", [])
    assert len(needs) == 3, (
        f"Expected exactly 3 build jobs in needs, got {len(needs)}: {needs}"
    )


# ---------------------------------------------------------------------------
# 3. download-artifact path doesn't conflict with any artifact name
# ---------------------------------------------------------------------------

def test_download_path_no_conflict_with_artifact_names(workflow):
    """The download path 'release-assets' must not clash with any upload-artifact name."""
    upload_names = []
    for job_name, job in workflow["jobs"].items():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if uses.startswith("actions/upload-artifact"):
                name = step.get("with", {}).get("name")
                if name:
                    upload_names.append(name)

    assert "release-assets" not in upload_names, (
        "An upload-artifact step uses the name 'release-assets', which would "
        "conflict with the download destination path used in the release job."
    )


# ---------------------------------------------------------------------------
# 4. No floating action tags in the release job
# ---------------------------------------------------------------------------

def test_release_job_no_floating_action_tags(release_steps):
    """No release step should use @main, @master, @latest, or @HEAD."""
    for step in release_steps:
        uses = step.get("uses", "")
        if uses:
            match = FLOATING_TAG_RE.search(uses)
            assert match is None, (
                f"Step uses floating action tag: '{uses}'. "
                "All actions must be pinned to a specific major version (e.g. @v4)."
            )


# ---------------------------------------------------------------------------
# 5. No shell: override in any release step
# ---------------------------------------------------------------------------

def test_release_job_no_shell_override(release_steps):
    """No release step should declare a shell: override."""
    for step in release_steps:
        assert "shell" not in step, (
            f"Step '{step.get('name') or step.get('uses')}' declares a shell: "
            "override, which is not allowed in the release job."
        )


# ---------------------------------------------------------------------------
# 6. Approved pinned action versions used in the release job
# ---------------------------------------------------------------------------

def test_release_job_checkout_action_version(release_steps):
    """checkout must be pinned to actions/checkout@v4."""
    checkout_uses = [
        step["uses"] for step in release_steps
        if step.get("uses", "").startswith("actions/checkout")
    ]
    assert checkout_uses, "No checkout action found in release job."
    for uses in checkout_uses:
        assert uses == "actions/checkout@v4", (
            f"checkout action must be @v4, got: '{uses}'"
        )


def test_release_job_download_action_version(release_steps):
    """download-artifact must be pinned to actions/download-artifact@v4."""
    dl_uses = [
        step["uses"] for step in release_steps
        if step.get("uses", "").startswith("actions/download-artifact")
    ]
    assert dl_uses, "No download-artifact action found in release job."
    for uses in dl_uses:
        assert uses == "actions/download-artifact@v4", (
            f"download-artifact must be @v4, got: '{uses}'"
        )


def test_release_job_gh_release_action_not_v1(release_steps):
    """softprops/action-gh-release must NOT use deprecated @v1."""
    for step in release_steps:
        uses = step.get("uses", "")
        if "softprops/action-gh-release" in uses:
            assert "@v1" not in uses, (
                f"softprops/action-gh-release@v1 is deprecated; must use @v2. Got: '{uses}'"
            )


# ---------------------------------------------------------------------------
# 7. No GITHUB_TOKEN in workflow-level env
# ---------------------------------------------------------------------------

def test_workflow_level_env_no_github_token(workflow):
    """Workflow-level env block must not expose GITHUB_TOKEN."""
    top_env = workflow.get("env") or {}
    assert "GITHUB_TOKEN" not in top_env, (
        "Workflow-level env: block contains GITHUB_TOKEN — "
        "this leaks the token to every job."
    )


# ---------------------------------------------------------------------------
# 8. Release job has no job-level env block
# ---------------------------------------------------------------------------

def test_release_job_no_job_level_env(release_job):
    """The release job itself must not declare a job-level env: block."""
    assert "env" not in release_job, (
        "release job declares a job-level env: block. "
        "The gh-release action must use the implicit token via permissions only."
    )


# ---------------------------------------------------------------------------
# 9. setup-python must NOT appear in the release job (unnecessary step)
# ---------------------------------------------------------------------------

def test_release_job_no_setup_python(release_steps):
    """The release job does not need Python — setup-python must not appear."""
    for step in release_steps:
        uses = step.get("uses", "")
        assert not uses.startswith("actions/setup-python"), (
            f"release job contains an unnecessary setup-python step: '{uses}'"
        )
