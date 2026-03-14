"""
Tester edge-case tests for INS-013: CI Workflow Skeleton
Covers: round-trip fidelity, duplicate job names, explicit shell directives,
release.needs exact membership, secrets exposure, pull_request_target security.
"""
import io
import pathlib

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"

EXPECTED_BUILD_JOBS = {"windows-build", "macos-arm-build", "linux-build"}  # macos-intel-build removed in FIX-011


@pytest.fixture(scope="module")
def workflow():
    """Parse and return the workflow YAML once for all tests."""
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def raw_text():
    """Return raw file text for low-level checks."""
    return WORKFLOW_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Round-trip fidelity
# ---------------------------------------------------------------------------

def test_yaml_round_trip_no_data_loss(workflow):
    """Dumping the parsed workflow back to YAML and re-parsing must yield
    the same Python structure — no data loss on round-trip."""
    dumped = yaml.dump(workflow, default_flow_style=False, allow_unicode=True)
    reloaded = yaml.safe_load(io.StringIO(dumped))
    assert reloaded == workflow, "Round-trip YAML dump/reload produced a different structure"


# ---------------------------------------------------------------------------
# Job name uniqueness
# ---------------------------------------------------------------------------

def test_no_duplicate_job_names(workflow):
    """YAML dicts forbid duplicates structurally, but verify explicitly
    that the parsed jobs dict count matches the expected distinct job set."""
    jobs = workflow.get("jobs", {})
    job_names = list(jobs.keys())
    assert len(job_names) == len(set(job_names)), (
        f"Duplicate job names detected: {[j for j in job_names if job_names.count(j) > 1]}"
    )
    assert len(jobs) == 4, f"Expected exactly 4 jobs (macos-intel-build removed in FIX-011), found {len(jobs)}: {job_names}"


# ---------------------------------------------------------------------------
# Workflow name
# ---------------------------------------------------------------------------

def test_workflow_name_is_non_empty_string(workflow):
    """Top-level 'name' must be a non-empty string (not None, not a number,
    not an empty string)."""
    name = workflow.get("name")
    assert isinstance(name, str), f"'name' must be a string, got {type(name).__name__}: {name!r}"
    assert name.strip() != "", "Workflow 'name' must not be blank"


# ---------------------------------------------------------------------------
# No explicit shell directives
# ---------------------------------------------------------------------------

def test_no_explicit_shell_directives(workflow):
    """No step in any job should set an explicit 'shell:' key.
    Let GitHub Actions choose the platform default (bash on Linux/macOS,
    pwsh on Windows). Hard-coding shell limits portability of future steps."""
    for job_name, job_def in workflow["jobs"].items():
        for step in job_def.get("steps", []):
            assert "shell" not in step, (
                f"Job '{job_name}' has a step with explicit 'shell:' directive: {step}"
            )


# ---------------------------------------------------------------------------
# Release job needs — exact membership
# ---------------------------------------------------------------------------

def test_release_needs_exactly_the_4_build_jobs(workflow):
    """release.needs must be exactly the 4 build jobs — no extra, no missing."""
    needs = workflow["jobs"]["release"].get("needs", [])
    needs_set = set(needs)
    assert needs_set == EXPECTED_BUILD_JOBS, (
        f"release.needs mismatch.\n"
        f"  Expected: {sorted(EXPECTED_BUILD_JOBS)}\n"
        f"  Got:      {sorted(needs_set)}\n"
        f"  Extra:    {sorted(needs_set - EXPECTED_BUILD_JOBS)}\n"
        f"  Missing:  {sorted(EXPECTED_BUILD_JOBS - needs_set)}"
    )


def test_release_needs_count_is_exactly_4(workflow):
    """release.needs list must have exactly 3 entries (macos-intel-build removed in FIX-011)."""
    needs = workflow["jobs"]["release"].get("needs", [])
    assert len(needs) == 3, (
        f"release.needs should have exactly 3 entries, found {len(needs)}: {needs}"
    )


# ---------------------------------------------------------------------------
# Checkout step present in every job
# ---------------------------------------------------------------------------

def test_each_job_uses_checkout_action(workflow):
    """Every job's first step must invoke actions/checkout (any version)."""
    for job_name, job_def in workflow["jobs"].items():
        steps = job_def.get("steps", [])
        assert steps, f"Job '{job_name}' has no steps at all"
        first_step = steps[0]
        uses = first_step.get("uses", "")
        assert uses.startswith("actions/checkout"), (
            f"Job '{job_name}' first step is not actions/checkout: {first_step}"
        )


# ---------------------------------------------------------------------------
# Security checks
# ---------------------------------------------------------------------------

def test_no_pull_request_target_trigger(workflow):
    """Workflow must NOT use 'pull_request_target' trigger, which can expose
    secrets to untrusted fork code (critical GitHub Actions security risk)."""
    on_section = workflow.get(True) or workflow.get("on") or {}
    assert "pull_request_target" not in on_section, (
        "Workflow uses pull_request_target trigger — this is a critical security risk"
    )


def test_no_hardcoded_secrets_in_raw_file(raw_text):
    """Raw workflow file must not contain obviously hardcoded credentials
    (passwords, tokens, API keys) outside of the approved ${{ secrets.* }} syntax."""
    import re
    # Look for assignment patterns that suggest hardcoded values
    forbidden_patterns = [
        r'password\s*=\s*["\'][^"\']{4,}["\']',   # password="something"
        r'token\s*=\s*["\'][^"\']{4,}["\']',        # token="something"
        r'api[_-]?key\s*=\s*["\'][^"\']{4,}["\']',  # api_key="something"
        r'secret\s*=\s*["\'][^"\']{4,}["\']',        # secret="something" (not ${{ secrets.X }})
    ]
    for pattern in forbidden_patterns:
        matches = re.findall(pattern, raw_text, re.IGNORECASE)
        # Filter out ${{ secrets.* }} references which are the approved form
        suspect = [m for m in matches if "${{" not in m]
        assert not suspect, (
            f"Possible hardcoded credential found matching pattern r'{pattern}': {suspect}"
        )


def test_workflow_file_is_utf8_without_bom(raw_text):
    """Workflow file must be UTF-8. BOM prefix would break YAML parsers
    and GitHub Actions parser in some edge cases."""
    raw_bytes = WORKFLOW_PATH.read_bytes()
    assert not raw_bytes.startswith(b"\xef\xbb\xbf"), (
        "Workflow file starts with a UTF-8 BOM (\\xef\\xbb\\xbf) — remove it"
    )


# ---------------------------------------------------------------------------
# Trigger pattern correctness
# ---------------------------------------------------------------------------

def test_tag_trigger_pattern_is_exact_semver_glob(workflow):
    """The tag pattern should be exactly 'v*.*.*' — not a looser glob like
    'v*' (which would trigger on branch names too if misread) and not an
    overly restrictive regex."""
    on_section = workflow.get(True) or workflow.get("on")
    tags = on_section["push"]["tags"]
    assert tags == ["v*.*.*"], (
        f"Expected tags list to be exactly ['v*.*.*'], got: {tags}"
    )


def test_no_branch_trigger_present(workflow):
    """Workflow must not have a 'branches' trigger under 'push'. INS-013
    is a tag-only workflow; adding a branch trigger would fire on every
    push to main, running expensive build jobs unnecessarily."""
    on_section = workflow.get(True) or workflow.get("on")
    push_section = on_section.get("push", {})
    assert "branches" not in push_section, (
        "push.branches trigger found — workflow should only trigger on tags, not branches"
    )
