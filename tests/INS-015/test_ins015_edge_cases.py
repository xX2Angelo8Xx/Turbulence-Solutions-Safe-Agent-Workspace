"""
Tester edge-case tests for INS-015: CI macOS Build Jobs

Covers correctness and security vectors not addressed by the developer suite:
  - Distinct artifact names (collision guard)
  - Exact build_dmg.sh script path
  - Architecture args cannot be swapped
  - chmod +x precedes script invocation in the same run block
  - No shell: overrides on any step
  - No secrets/tokens in run commands or env blocks
  - Runners are distinct (macos-13 != macos-14)
  - Artifact paths are the specific dist/*.dmg glob
  - macOS jobs contain no Windows-specific references
"""
import pathlib
import re
import yaml
import pytest

REPO_ROOT = pathlib.Path(__file__).parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"

EXACT_SCRIPT_PATH = "src/installer/macos/build_dmg.sh"
SECRET_PATTERN = re.compile(r"\$\{\{\s*secrets\.", re.IGNORECASE)
TOKEN_PATTERN = re.compile(r"\$\{\{\s*github\.token", re.IGNORECASE)
WINDOWS_REFS = re.compile(r"setup\.iss|innosetup|choco|iscc|\.exe")


@pytest.fixture(scope="module")
def workflow():
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def intel_job(workflow):
    """Return the macos-intel-build job, or skip if removed."""
    if "macos-intel-build" not in workflow.get("jobs", {}):
        pytest.skip("macos-intel-build job was removed in FIX-011 (Intel Mac runners deprecated)")
    return workflow["jobs"]["macos-intel-build"]


@pytest.fixture(scope="module")
def arm_job(workflow):
    return workflow["jobs"]["macos-arm-build"]


@pytest.fixture(scope="module")
def intel_steps(intel_job):
    return intel_job["steps"]


@pytest.fixture(scope="module")
def arm_steps(arm_job):
    return arm_job["steps"]


# ---------------------------------------------------------------------------
# Artifact name collision guard
# ---------------------------------------------------------------------------

def test_artifact_names_are_distinct(intel_steps, arm_steps):
    """Intel and ARM artifact names must be different to prevent upload collision."""
    def get_artifact_name(steps):
        for step in steps:
            if step.get("uses", "").startswith("actions/upload-artifact"):
                return step.get("with", {}).get("name")
        return None

    intel_name = get_artifact_name(intel_steps)
    arm_name = get_artifact_name(arm_steps)
    assert intel_name is not None, "No upload-artifact step found in macos-intel-build"
    assert arm_name is not None, "No upload-artifact step found in macos-arm-build"
    assert intel_name != arm_name, (
        f"Intel and ARM artifact names must differ but both are {intel_name!r}"
    )


# ---------------------------------------------------------------------------
# Architecture arg correctness (cannot be swapped)
# ---------------------------------------------------------------------------

def test_intel_job_does_not_pass_arm64(intel_steps):
    """macos-intel-build must NOT pass 'arm64' to build_dmg.sh."""
    for step in intel_steps:
        if step.get("name") == "Build DMG":
            cmd = step.get("run", "")
            # arm64 must not appear as the arch argument (standalone word)
            assert not re.search(r"\barm64\b", cmd), (
                f"macos-intel-build incorrectly passes arm64: {cmd!r}"
            )
            return
    pytest.fail("'Build DMG' step not found in macos-intel-build")


def test_arm_job_does_not_pass_x86_64(arm_steps):
    """macos-arm-build must NOT pass 'x86_64' to build_dmg.sh."""
    for step in arm_steps:
        if step.get("name") == "Build DMG":
            cmd = step.get("run", "")
            assert not re.search(r"\bx86_64\b", cmd), (
                f"macos-arm-build incorrectly passes x86_64: {cmd!r}"
            )
            return
    pytest.fail("'Build DMG' step not found in macos-arm-build")


# ---------------------------------------------------------------------------
# Exact script path
# ---------------------------------------------------------------------------

def test_macos_intel_exact_script_path(intel_steps):
    """macos-intel-build 'Build DMG' step must reference the exact script path."""
    for step in intel_steps:
        if step.get("name") == "Build DMG":
            cmd = step.get("run", "")
            assert EXACT_SCRIPT_PATH in cmd, (
                f"Expected exact path {EXACT_SCRIPT_PATH!r} in Build DMG run, got: {cmd!r}"
            )
            return
    pytest.fail("'Build DMG' step not found in macos-intel-build")


def test_macos_arm_exact_script_path(arm_steps):
    """macos-arm-build 'Build DMG' step must reference the exact script path."""
    for step in arm_steps:
        if step.get("name") == "Build DMG":
            cmd = step.get("run", "")
            assert EXACT_SCRIPT_PATH in cmd, (
                f"Expected exact path {EXACT_SCRIPT_PATH!r} in Build DMG run, got: {cmd!r}"
            )
            return
    pytest.fail("'Build DMG' step not found in macos-arm-build")


# ---------------------------------------------------------------------------
# chmod +x must precede script invocation
# ---------------------------------------------------------------------------

def test_macos_intel_chmod_before_script_invocation(intel_steps):
    """chmod +x must appear before the bash/sh invocation of build_dmg.sh."""
    for step in intel_steps:
        if step.get("name") == "Build DMG":
            cmd = step.get("run", "")
            chmod_pos = cmd.find("chmod +x")
            script_pos = cmd.find(EXACT_SCRIPT_PATH, chmod_pos + 1 if chmod_pos >= 0 else 0)
            # Find the actual invocation line (the line that calls the script, not chmod)
            invoke_pos = -1
            for line in cmd.splitlines():
                stripped = line.strip()
                if EXACT_SCRIPT_PATH in stripped and "chmod" not in stripped:
                    invoke_pos = cmd.find(stripped)
                    break
            assert chmod_pos >= 0, "chmod +x not found in Build DMG step"
            assert invoke_pos >= 0, "Script invocation line not found in Build DMG step"
            assert chmod_pos < invoke_pos, (
                "chmod +x must appear before the script invocation"
            )
            return
    pytest.fail("'Build DMG' step not found in macos-intel-build")


def test_macos_arm_chmod_before_script_invocation(arm_steps):
    """chmod +x must appear before the bash/sh invocation of build_dmg.sh."""
    for step in arm_steps:
        if step.get("name") == "Build DMG":
            cmd = step.get("run", "")
            chmod_pos = cmd.find("chmod +x")
            invoke_pos = -1
            for line in cmd.splitlines():
                stripped = line.strip()
                if EXACT_SCRIPT_PATH in stripped and "chmod" not in stripped:
                    invoke_pos = cmd.find(stripped)
                    break
            assert chmod_pos >= 0, "chmod +x not found in Build DMG step"
            assert invoke_pos >= 0, "Script invocation line not found in Build DMG step"
            assert chmod_pos < invoke_pos, (
                "chmod +x must appear before the script invocation"
            )
            return
    pytest.fail("'Build DMG' step not found in macos-arm-build")


# ---------------------------------------------------------------------------
# No shell: overrides
# ---------------------------------------------------------------------------

def test_macos_intel_no_shell_override(intel_steps):
    """No step in macos-intel-build should override the default shell."""
    for step in intel_steps:
        assert "shell" not in step, (
            f"Step {step.get('name') or step.get('uses')!r} has a 'shell:' override "
            f"in macos-intel-build — remove it to use the runner default"
        )


def test_macos_arm_no_shell_override(arm_steps):
    """No step in macos-arm-build should override the default shell."""
    for step in arm_steps:
        assert "shell" not in step, (
            f"Step {step.get('name') or step.get('uses')!r} has a 'shell:' override "
            f"in macos-arm-build — remove it to use the runner default"
        )


# ---------------------------------------------------------------------------
# Security: no secrets or tokens in run commands or env blocks
# ---------------------------------------------------------------------------

def _all_run_commands(steps):
    return [step.get("run", "") for step in steps if "run" in step]


def _all_env_values(steps):
    values = []
    for step in steps:
        env = step.get("env", {}) or {}
        values.extend(str(v) for v in env.values())
    return values


def test_macos_intel_no_secrets_in_run(intel_steps):
    """macos-intel-build run commands must not reference secrets context."""
    for cmd in _all_run_commands(intel_steps):
        assert not SECRET_PATTERN.search(cmd), (
            f"Hardcoded secret reference found in macos-intel-build run: {cmd!r}"
        )


def test_macos_arm_no_secrets_in_run(arm_steps):
    """macos-arm-build run commands must not reference secrets context."""
    for cmd in _all_run_commands(arm_steps):
        assert not SECRET_PATTERN.search(cmd), (
            f"Hardcoded secret reference found in macos-arm-build run: {cmd!r}"
        )


def test_macos_intel_no_tokens_in_env(intel_steps):
    """macos-intel-build env blocks must not expose github.token."""
    for val in _all_env_values(intel_steps):
        assert not TOKEN_PATTERN.search(val), (
            f"github.token found in macos-intel-build env: {val!r}"
        )


def test_macos_arm_no_tokens_in_env(arm_steps):
    """macos-arm-build env blocks must not expose github.token."""
    for val in _all_env_values(arm_steps):
        assert not TOKEN_PATTERN.search(val), (
            f"github.token found in macos-arm-build env: {val!r}"
        )


# ---------------------------------------------------------------------------
# Runners are distinct
# ---------------------------------------------------------------------------

def test_macos_runners_are_distinct(workflow, arm_job):
    """macOS build jobs must use distinct runner images.

    Since macos-intel-build was removed in FIX-011, this test now verifies
    that the remaining macos-arm-build uses macos-14 (not macos-15 or same
    as any other macOS job if one were re-added).
    """
    arm_runner = arm_job.get("runs-on")
    assert arm_runner == "macos-14", (
        f"macos-arm-build should use macos-14 runner, got {arm_runner!r}"
    )


# ---------------------------------------------------------------------------
# Artifact path is the specific DMG glob
# ---------------------------------------------------------------------------

def test_macos_intel_artifact_path_exact_glob(intel_steps):
    """macos-intel-build artifact path must be 'dist/*.dmg'."""
    for step in intel_steps:
        if step.get("uses", "").startswith("actions/upload-artifact"):
            path = step.get("with", {}).get("path", "")
            assert path == "dist/*.dmg", (
                f"Expected 'dist/*.dmg' artifact path, got: {path!r}"
            )
            return
    pytest.fail("No upload-artifact step found in macos-intel-build")


def test_macos_arm_artifact_path_exact_glob(arm_steps):
    """macos-arm-build artifact path must be 'dist/*.dmg'."""
    for step in arm_steps:
        if step.get("uses", "").startswith("actions/upload-artifact"):
            path = step.get("with", {}).get("path", "")
            assert path == "dist/*.dmg", (
                f"Expected 'dist/*.dmg' artifact path, got: {path!r}"
            )
            return
    pytest.fail("No upload-artifact step found in macos-arm-build")


# ---------------------------------------------------------------------------
# macOS jobs must not contain Windows-specific references
# ---------------------------------------------------------------------------

def _job_as_yaml_string(job):
    """Serialize a single job dict to YAML for text scanning."""
    return yaml.dump(job, default_flow_style=False)


def test_macos_intel_no_windows_references(intel_job):
    """macos-intel-build must not reference Windows-specific tools (choco, iscc, .exe)."""
    job_text = _job_as_yaml_string(intel_job)
    match = WINDOWS_REFS.search(job_text)
    assert match is None, (
        f"Windows-specific reference found in macos-intel-build: {match.group()!r}"
    )


def test_macos_arm_no_windows_references(arm_job):
    """macos-arm-build must not reference Windows-specific tools (choco, iscc, .exe)."""
    job_text = _job_as_yaml_string(arm_job)
    match = WINDOWS_REFS.search(job_text)
    assert match is None, (
        f"Windows-specific reference found in macos-arm-build: {match.group()!r}"
    )
