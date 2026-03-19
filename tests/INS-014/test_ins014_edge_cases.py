"""
Edge-case tests for INS-014: CI Windows Build Job — added by Tester Agent.

Covers: shell overrides, retention-days, step name quality, secrets hygiene,
artifact path correctness vs real Inno Setup output location, python-version
type safety, and step ordering.
"""
import pathlib
import re

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"
SETUP_ISS_PATH = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"


@pytest.fixture(scope="module")
def workflow():
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def windows_job(workflow):
    return workflow["jobs"]["windows-build"]


@pytest.fixture(scope="module")
def windows_steps(windows_job):
    return windows_job["steps"]


def test_no_shell_override_in_any_step(windows_steps):
    """No step in windows-build should have an explicit 'shell:' key."""
    for step in windows_steps:
        assert "shell" not in step, (
            f"Step {step.get('name', step.get('uses', '?'))!r} has an "
            f"unexpected 'shell:' override: {step.get('shell')!r}. "
            "Remove it and let the runner choose the default shell."
        )


def test_artifact_no_retention_days(windows_steps):
    """upload-artifact should not set retention-days unless required."""
    for step in windows_steps:
        if step.get("uses", "").startswith("actions/upload-artifact"):
            assert "retention-days" not in step.get("with", {}), (
                "upload-artifact sets 'retention-days' — verify this is "
                "an intentional override of the GitHub 90-day default."
            )


def test_all_run_steps_have_human_readable_names(windows_steps):
    """Every 'run:' step must have a non-empty, human-readable name."""
    for step in windows_steps:
        if "run" in step:
            name = step.get("name", "")
            assert name and len(name.strip()) > 0, (
                f"run step with command {step['run']!r} is missing a "
                "'name:' label — add a human-readable description."
            )
            assert not name.strip().startswith("${{"), (
                f"Step name {name!r} starts with an expression rather than "
                "a plain human-readable string."
            )


def test_no_secrets_referenced_in_windows_build_steps(windows_steps):
    """No step in windows-build should reference secrets."""
    secret_pattern = re.compile(r"\$\{\{\s*secrets\.", re.IGNORECASE)
    for step in windows_steps:
        step_str = str(step)
        assert not secret_pattern.search(step_str), (
            f"Step {step.get('name', step.get('uses', '?'))!r} references "
            f"a GitHub secret. The build job must not use secrets."
        )


def test_artifact_path_matches_inno_setup_output_directory(windows_steps):
    """Artifact path must reflect where Inno Setup actually writes the EXE.

    Inno Setup default OutputDir = Output/ relative to the .iss script dir.
    Script at src/installer/windows/setup.iss -> output at:
        src/installer/windows/Output/AgentEnvironmentLauncher-Setup.exe

    Current workflow uses: Output/AgentEnvironmentLauncher-Setup.exe
    This is relative to the repo root and does NOT match Inno Setup output.
    The upload-artifact action will fail with 'No files were found'.
    """
    for step in windows_steps:
        if step.get("uses", "").startswith("actions/upload-artifact"):
            path = step.get("with", {}).get("path", "")
            expected = (
                "src/installer/windows/Output/"
                "AgentEnvironmentLauncher-Setup.exe"
            )
            assert path == expected, (
                f"Artifact path is {path!r}. Inno Setup default OutputDir "
                "is relative to the .iss file directory, so the EXE will be "
                f"written to {expected!r}. Fix the workflow artifact path."
            )
            return
    pytest.fail("No upload-artifact step found in windows-build job")


def test_setup_iss_exists_at_path_referenced_by_iscc(windows_steps):
    """The .iss file referenced in the iscc command must exist in the repo."""
    for step in windows_steps:
        if step.get("name") == "Build installer":
            cmd = step.get("run", "")
            match = re.search(r"iscc\s+(\S+\.iss)", cmd)
            assert match, f"Could not parse .iss path from: {cmd!r}"
            iss_path = REPO_ROOT / match.group(1).replace("\\", "/")
            assert iss_path.exists(), (
                f"setup.iss not found at {iss_path}. "
                "Either the file was deleted or the iscc path is wrong."
            )
            return
    pytest.fail("'Build installer' step not found")


def test_setup_iss_has_no_explicit_output_dir():
    """Confirm setup.iss has no OutputDir — Inno Setup default applies."""
    with open(SETUP_ISS_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(
        r"^\s*OutputDir\s*=\s*(.+)$", content, re.MULTILINE | re.IGNORECASE
    )
    assert match is None, (
        f"setup.iss contains an OutputDir directive: "
        f"{match.group(0).strip()!r}. "
        "Update the workflow artifact path to match, and update TC-EC-05."
    )


def test_python_version_is_string_not_float(windows_steps):
    """python-version must be the string '3.11', not the float 3.1."""
    for step in windows_steps:
        if step.get("uses", "").startswith("actions/setup-python"):
            version = step.get("with", {}).get("python-version")
            assert isinstance(version, str), (
                f"python-version must be quoted string '3.11', "
                f"got {type(version).__name__}: {version!r}. "
                "Unquoted 3.11 parses as float 3.1 in YAML."
            )
            return
    pytest.fail("No setup-python step found")


def test_checkout_is_first_step(windows_steps):
    """Checkout must be the first step so subsequent steps have sources."""
    first = windows_steps[0]
    assert first.get("uses", "").startswith("actions/checkout"), (
        f"First step must be actions/checkout@v4. Got: {first!r}"
    )


def test_upload_artifact_is_last_step(windows_steps):
    """Artifact upload must be the last step in the job."""
    last = windows_steps[-1]
    assert last.get("uses", "").startswith("actions/upload-artifact"), (
        f"Last step must be actions/upload-artifact@v4. Got: {last!r}"
    )


def test_no_user_controlled_values_in_env(windows_steps):
    """No step should inject user-controlled GitHub context into env:."""
    dangerous = re.compile(
        r"\$\{\{\s*github\.(event|head_ref|ref_name)\b", re.IGNORECASE
    )
    for step in windows_steps:
        env_str = str(step.get("env", {}))
        assert not dangerous.search(env_str), (
            f"Step {step.get('name', step.get('uses', '?'))!r} injects a "
            f"user-controlled value into env: {env_str!r}"
        )
