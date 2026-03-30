"""
Tester edge-case tests for INS-028: macOS source install CI workflow.

Covers additional correctness, security, and quality criteria beyond the
Developer's baseline validation tests.
"""

import pathlib
import re

import pytest
import yaml

WORKFLOW_PATH = pathlib.Path(__file__).parents[2] / ".github" / "workflows" / "macos-source-test.yml"


@pytest.fixture(scope="module")
def workflow_yaml():
    with WORKFLOW_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def workflow_text():
    return WORKFLOW_PATH.read_text(encoding="utf-8")


# ── actions/checkout specifics ────────────────────────────────────────────────

def test_workflow_uses_actions_checkout(workflow_yaml):
    """Workflow must use 'actions/checkout', not an arbitrary third-party checkout."""
    jobs = workflow_yaml.get("jobs", {})
    found = False
    for job in jobs.values():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if uses.startswith("actions/checkout"):
                found = True
                break
    assert found, "No step uses 'actions/checkout' (official GitHub action)"


def test_workflow_checkout_not_deprecated_v1_v2(workflow_yaml):
    """actions/checkout@v1 and @v2 are deprecated — must use v3+ or latest."""
    jobs = workflow_yaml.get("jobs", {})
    for job in jobs.values():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if uses.startswith("actions/checkout"):
                assert not uses.endswith("@v1"), f"Deprecated action version: {uses}"
                assert not uses.endswith("@v2"), f"Deprecated action version: {uses}"


def test_workflow_setup_python_not_deprecated_v1_v2_v3_v4(workflow_yaml):
    """actions/setup-python v1–v4 are deprecated — must use v5+."""
    jobs = workflow_yaml.get("jobs", {})
    for job in jobs.values():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if uses.startswith("actions/setup-python"):
                for old_ver in ("@v1", "@v2", "@v3", "@v4"):
                    assert not uses.endswith(old_ver), f"Deprecated action version: {uses}"


# ── Workflow-level name ───────────────────────────────────────────────────────

def test_workflow_has_non_empty_name(workflow_yaml):
    """Workflow must have a top-level 'name' that is non-empty and descriptive."""
    name = workflow_yaml.get("name", "")
    assert isinstance(name, str) and name.strip(), "Workflow must have a non-empty 'name'"
    assert len(name.strip()) >= 5, f"Workflow name is too short to be descriptive: '{name}'"


# ── Step names ────────────────────────────────────────────────────────────────

def test_all_steps_have_names(workflow_yaml):
    """Every step must have a descriptive 'name' field."""
    jobs = workflow_yaml.get("jobs", {})
    for job_id, job in jobs.items():
        for i, step in enumerate(job.get("steps", [])):
            step_name = step.get("name", "")
            assert step_name and step_name.strip(), (
                f"Step {i + 1} in job '{job_id}' has no name"
            )


def test_step_names_are_descriptive(workflow_yaml):
    """Step names must be at least 5 chars — prevents placeholder names like 'step1'."""
    jobs = workflow_yaml.get("jobs", {})
    for job_id, job in jobs.items():
        for i, step in enumerate(job.get("steps", [])):
            name = step.get("name", "")
            assert len(name.strip()) >= 5, (
                f"Step {i + 1} in job '{job_id}' has a suspiciously short name: '{name}'"
            )


# ── shell: bash ───────────────────────────────────────────────────────────────

def test_no_explicit_shell_bash_on_steps(workflow_yaml):
    """macOS runners default to bash — no need to set 'shell: bash' on every step.
    Its presence is not wrong, but the workflow should rely on defaults consistently."""
    jobs = workflow_yaml.get("jobs", {})
    shell_bash_count = 0
    for job in jobs.values():
        for step in job.get("steps", []):
            if step.get("shell") == "bash":
                shell_bash_count += 1
    # We don't fail if present — this is informational. A value > 0 means the
    # developer used redundant shell declarations. We assert zero redundancy.
    assert shell_bash_count == 0, (
        f"{shell_bash_count} step(s) explicitly set 'shell: bash' — unnecessary on macOS runners"
    )


# ── Secrets / credentials ─────────────────────────────────────────────────────

def test_no_hardcoded_tokens_in_workflow(workflow_text):
    """Workflow file must not contain hardcoded API tokens or secrets."""
    # Match common secret patterns: 40-hex-char tokens, ghp_/ghs_ GitHub tokens
    patterns = [
        r"ghp_[A-Za-z0-9]{36}",          # GitHub personal access token
        r"ghs_[A-Za-z0-9]{36}",          # GitHub installation token
        r"glpat-[A-Za-z0-9\-]{20}",      # GitLab personal access token
        r"(?i)(password|secret|token|apikey|api_key)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
    ]
    for pattern in patterns:
        match = re.search(pattern, workflow_text)
        assert match is None, f"Potential hardcoded secret found matching '{pattern}'"


def test_workflow_uses_github_secrets_for_sensitive_data(workflow_text):
    """If the workflow references any secrets, they must use ${{ secrets.* }} syntax."""
    # Ensure no raw token-like strings appear outside of ${{ secrets }} references
    raw_token_pattern = r"(?<!\$\{\{ secrets\.)(?<!\$\{\{ env\.)[A-Z0-9_]{20,}(?!\s*\}\})"
    # This is a heuristic — a very long uppercase string that isn't a secrets ref
    # could be a hardcoded credential. We check for the most suspicious form.
    # Allow known false-positives like runner names, PATH entries, etc.
    # Check that the file doesn't have raw 40-char hex strings (common token length)
    hex40_pattern = r"\b[0-9a-f]{40}\b"
    matches = re.findall(hex40_pattern, workflow_text)
    # Filter out git SHAs in comments (lines starting with #)
    non_comment_hex = [
        m for m in matches
        if not any(
            line.strip().startswith("#")
            for line in workflow_text.splitlines()
            if m in line
        )
    ]
    assert not non_comment_hex, (
        f"Found 40-char hex strings that may be hardcoded tokens: {non_comment_hex}"
    )


# ── continue-on-error ─────────────────────────────────────────────────────────

def test_no_continue_on_error_in_steps(workflow_yaml):
    """No step should have 'continue-on-error: true' — failures must fail the build."""
    jobs = workflow_yaml.get("jobs", {})
    for job_id, job in jobs.items():
        for i, step in enumerate(job.get("steps", [])):
            assert step.get("continue-on-error") is not True, (
                f"Step {i + 1} ('{step.get('name', 'unnamed')}') in job '{job_id}' "
                f"has 'continue-on-error: true' — this masks failures"
            )


def test_no_continue_on_error_at_job_level(workflow_yaml):
    """No job should have 'continue-on-error: true'."""
    jobs = workflow_yaml.get("jobs", {})
    for job_id, job in jobs.items():
        assert job.get("continue-on-error") is not True, (
            f"Job '{job_id}' has 'continue-on-error: true' — job failures must fail the workflow"
        )


# ── Trigger correctness ───────────────────────────────────────────────────────

def test_workflow_has_workflow_dispatch_trigger(workflow_yaml):
    """Workflow must support manual dispatch for debugging CI issues."""
    on = workflow_yaml.get(True, workflow_yaml.get("on", {})) or {}
    assert "workflow_dispatch" in on, (
        "Workflow should include 'workflow_dispatch' for manual execution"
    )


def test_push_trigger_targets_main_branch(workflow_yaml):
    """Push trigger must be scoped to 'main' (not all branches)."""
    on = workflow_yaml.get(True, workflow_yaml.get("on", {})) or {}
    push = on.get("push", {})
    branches = push.get("branches", [])
    assert "main" in branches, f"push trigger must include 'main' branch, got: {branches}"


def test_pull_request_trigger_targets_main_branch(workflow_yaml):
    """pull_request trigger must be scoped to 'main'."""
    on = workflow_yaml.get(True, workflow_yaml.get("on", {})) or {}
    pr = on.get("pull_request", {})
    branches = pr.get("branches", [])
    assert "main" in branches, f"pull_request trigger must include 'main' branch, got: {branches}"


# ── Step ordering ─────────────────────────────────────────────────────────────

def test_checkout_is_first_step(workflow_yaml):
    """actions/checkout must be the first step — nothing can run before the repo is present."""
    jobs = workflow_yaml.get("jobs", {})
    for job_id, job in jobs.items():
        steps = job.get("steps", [])
        assert steps, f"Job '{job_id}' has no steps"
        first_step = steps[0]
        uses = first_step.get("uses", "")
        assert uses.startswith("actions/checkout"), (
            f"First step in job '{job_id}' must be 'actions/checkout', got: '{uses}'"
        )


def test_setup_python_before_install_script(workflow_yaml):
    """Python must be set up before running the install script."""
    jobs = workflow_yaml.get("jobs", {})
    for job_id, job in jobs.items():
        steps = job.get("steps", [])
        setup_idx = None
        install_idx = None
        for i, step in enumerate(steps):
            if "actions/setup-python" in step.get("uses", ""):
                setup_idx = i
            if "install-macos.sh" in step.get("run", ""):
                install_idx = i
        if setup_idx is not None and install_idx is not None:
            assert setup_idx < install_idx, (
                f"In job '{job_id}': setup-python (step {setup_idx + 1}) must come "
                f"before install script (step {install_idx + 1})"
            )


# ── pytest options ────────────────────────────────────────────────────────────

def test_pytest_uses_fail_fast_flag(workflow_yaml):
    """pytest must be run with -x (fail fast) so the first failure is surfaced immediately."""
    jobs = workflow_yaml.get("jobs", {})
    for job in jobs.values():
        for step in job.get("steps", []):
            run = step.get("run", "")
            if "python -m pytest" in run:
                assert "-x" in run, (
                    f"pytest step should use '-x' (fail fast) flag. Got: {run!r}"
                )


def test_pytest_uses_short_traceback(workflow_yaml):
    """pytest should use --tb=short for readable CI output."""
    jobs = workflow_yaml.get("jobs", {})
    for job in jobs.values():
        for step in job.get("steps", []):
            run = step.get("run", "")
            if "python -m pytest" in run:
                assert "--tb=short" in run, (
                    f"pytest step should use '--tb=short' for concise CI output. Got: {run!r}"
                )


# ── Install script invocation ─────────────────────────────────────────────────

def test_install_script_called_with_bash(workflow_yaml):
    """Install script must be explicitly invoked with 'bash' for portability."""
    jobs = workflow_yaml.get("jobs", {})
    for job in jobs.values():
        for step in job.get("steps", []):
            run = step.get("run", "")
            if "install-macos.sh" in run:
                assert run.strip().startswith("bash "), (
                    f"install-macos.sh should be called with 'bash scripts/...', got: {run!r}"
                )
