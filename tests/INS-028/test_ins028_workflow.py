"""
Tests for INS-028: macOS source install CI workflow.

Validates the structure and content of .github/workflows/macos-source-test.yml
to ensure the workflow correctly defines the macOS source install CI job.
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


# ── Existence and validity ────────────────────────────────────────────────────

def test_workflow_file_exists():
    assert WORKFLOW_PATH.exists(), f"Workflow file not found: {WORKFLOW_PATH}"


def test_workflow_is_valid_yaml(workflow_yaml):
    assert isinstance(workflow_yaml, dict), "Workflow YAML must parse to a dict"


# ── Runner ────────────────────────────────────────────────────────────────────

def test_workflow_references_macos14_runner(workflow_yaml):
    jobs = workflow_yaml.get("jobs", {})
    found = any(
        job.get("runs-on") == "macos-14"
        for job in jobs.values()
    )
    assert found, "No job uses 'macos-14' runner"


# ── Install script ────────────────────────────────────────────────────────────

def test_workflow_calls_install_script(workflow_yaml):
    jobs = workflow_yaml.get("jobs", {})
    found = False
    for job in jobs.values():
        for step in job.get("steps", []):
            run = step.get("run", "")
            if "install-macos.sh" in run:
                found = True
                break
    assert found, "No step calls scripts/install-macos.sh"


# ── pytest ────────────────────────────────────────────────────────────────────

def test_workflow_runs_pytest(workflow_yaml):
    jobs = workflow_yaml.get("jobs", {})
    found = False
    for job in jobs.values():
        for step in job.get("steps", []):
            run = step.get("run", "")
            if "pytest" in run:
                found = True
                break
    assert found, "No step runs pytest"


# ── actions/setup-python ──────────────────────────────────────────────────────

def test_workflow_uses_setup_python(workflow_yaml):
    jobs = workflow_yaml.get("jobs", {})
    found = False
    for job in jobs.values():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if "actions/setup-python" in uses:
                found = True
                break
    assert found, "No step uses actions/setup-python"


def test_workflow_python_version_311_or_newer(workflow_yaml):
    jobs = workflow_yaml.get("jobs", {})
    for job in jobs.values():
        for step in job.get("steps", []):
            if "actions/setup-python" in step.get("uses", ""):
                version_str = str(step.get("with", {}).get("python-version", ""))
                # Accept '3.11', '3.12', '3.13', etc.
                match = re.match(r"3\.(\d+)", version_str)
                assert match, f"python-version '{version_str}' is not a valid 3.x version"
                minor = int(match.group(1))
                assert minor >= 11, f"python-version '{version_str}' is below 3.11"
                return
    pytest.fail("No actions/setup-python step found — cannot verify python-version")


# ── Trigger events ────────────────────────────────────────────────────────────

def test_workflow_has_correct_triggers(workflow_yaml):
    # PyYAML 5+ parses bare 'on:' as boolean True (YAML 1.1 compat).
    # Fall back to string key for robustness.
    on = workflow_yaml.get(True, workflow_yaml.get("on", {})) or {}
    assert "push" in on, "Workflow must trigger on 'push'"
    assert "pull_request" in on, "Workflow must trigger on 'pull_request'"


# ── Verification steps ────────────────────────────────────────────────────────

def test_workflow_verifies_agent_launcher(workflow_yaml):
    jobs = workflow_yaml.get("jobs", {})
    found = False
    for job in jobs.values():
        for step in job.get("steps", []):
            run = step.get("run", "")
            if "agent-launcher" in run and "--version" in run:
                found = True
                break
    assert found, "No step verifies 'agent-launcher --version'"


def test_workflow_verifies_ts_python(workflow_yaml):
    jobs = workflow_yaml.get("jobs", {})
    found = False
    for job in jobs.values():
        for step in job.get("steps", []):
            run = step.get("run", "")
            if "ts-python" in run and "--version" in run:
                found = True
                break
    assert found, "No step verifies 'ts-python --version'"
