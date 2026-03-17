"""
Tests for FIX-029 — Verify Code Signing step in CI macOS build.

These tests validate the YAML structure of .github/workflows/release.yml to
confirm:
1. The "Verify Code Signing" step exists in the macos-arm-build job.
2. It is positioned after "Build DMG" and before "Upload macOS ARM DMG".
3. The step runs the correct codesign command.
4. The step includes the pass-through echo message.
5. The workflow file remains valid YAML after the change.
"""

import pathlib
import yaml
import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"


@pytest.fixture(scope="module")
def workflow() -> dict:
    """Load and parse the release.yml workflow file."""
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def macos_steps(workflow: dict) -> list:
    """Return the ordered list of steps from the macos-arm-build job."""
    return workflow["jobs"]["macos-arm-build"]["steps"]


def _step_names(steps: list) -> list[str]:
    return [s.get("name", "") for s in steps]


class TestWorkflowFileValidity:
    """The workflow file must be syntactically valid YAML."""

    def test_file_exists(self):
        assert WORKFLOW_PATH.exists(), f"Workflow file not found: {WORKFLOW_PATH}"

    def test_file_parses_as_valid_yaml(self):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        assert isinstance(data, dict), "Parsed YAML must be a dict"

    def test_macos_arm_build_job_exists(self, workflow: dict):
        assert "macos-arm-build" in workflow["jobs"]


class TestVerifyCodeSigningStepExists:
    """The 'Verify Code Signing' step must be present in the macos-arm-build job."""

    def test_step_present(self, macos_steps: list):
        names = _step_names(macos_steps)
        assert "Verify Code Signing" in names, (
            f"'Verify Code Signing' step not found in macos-arm-build. Steps: {names}"
        )

    def test_step_has_run_command(self, macos_steps: list):
        step = next(s for s in macos_steps if s.get("name") == "Verify Code Signing")
        assert "run" in step, "Step must have a 'run' key"

    def test_step_run_contains_codesign_verify(self, macos_steps: list):
        step = next(s for s in macos_steps if s.get("name") == "Verify Code Signing")
        run_cmd: str = step["run"]
        assert "codesign --verify --deep --strict" in run_cmd

    def test_step_run_targets_correct_app(self, macos_steps: list):
        step = next(s for s in macos_steps if s.get("name") == "Verify Code Signing")
        run_cmd: str = step["run"]
        assert "dist/AgentEnvironmentLauncher.app" in run_cmd

    def test_step_run_contains_echo_pass_message(self, macos_steps: list):
        step = next(s for s in macos_steps if s.get("name") == "Verify Code Signing")
        run_cmd: str = step["run"]
        assert "echo" in run_cmd and "passed" in run_cmd, (
            "Step run command must include an echo pass message"
        )

    def test_step_run_full_command(self, macos_steps: list):
        """Exact command must match the specified implementation."""
        step = next(s for s in macos_steps if s.get("name") == "Verify Code Signing")
        expected = (
            "codesign --verify --deep --strict dist/AgentEnvironmentLauncher.app"
            " && echo \"Code signing verification passed\""
        )
        assert step["run"].strip() == expected, (
            f"Step run command mismatch.\nExpected: {expected!r}\nActual: {step['run'].strip()!r}"
        )


class TestStepOrdering:
    """The 'Verify Code Signing' step must come after 'Build DMG'
    and before 'Upload macOS ARM DMG'."""

    def test_verify_step_after_build_dmg(self, macos_steps: list):
        names = _step_names(macos_steps)
        build_idx = names.index("Build DMG")
        verify_idx = names.index("Verify Code Signing")
        assert verify_idx == build_idx + 1, (
            f"'Verify Code Signing' (index {verify_idx}) must immediately follow "
            f"'Build DMG' (index {build_idx})"
        )

    def test_verify_step_before_upload_artifact(self, macos_steps: list):
        names = _step_names(macos_steps)
        verify_idx = names.index("Verify Code Signing")
        upload_idx = names.index("Upload macOS ARM DMG")
        assert verify_idx < upload_idx, (
            f"'Verify Code Signing' (index {verify_idx}) must come before "
            f"'Upload macOS ARM DMG' (index {upload_idx})"
        )

    def test_no_upload_step_between_build_and_verify(self, macos_steps: list):
        names = _step_names(macos_steps)
        build_idx = names.index("Build DMG")
        verify_idx = names.index("Verify Code Signing")
        steps_between = names[build_idx + 1:verify_idx]
        assert "Upload macOS ARM DMG" not in steps_between, (
            "Upload step must not appear between Build DMG and Verify Code Signing"
        )


class TestOtherJobsUnchanged:
    """The windows-build and linux-build jobs must not be altered."""

    def test_windows_build_job_present(self, workflow: dict):
        assert "windows-build" in workflow["jobs"]

    def test_linux_build_job_present(self, workflow: dict):
        assert "linux-build" in workflow["jobs"]

    def test_windows_build_has_no_codesign_step(self, workflow: dict):
        steps = workflow["jobs"]["windows-build"]["steps"]
        names = _step_names(steps)
        assert "Verify Code Signing" not in names

    def test_linux_build_has_no_codesign_step(self, workflow: dict):
        steps = workflow["jobs"]["linux-build"]["steps"]
        names = _step_names(steps)
        assert "Verify Code Signing" not in names

    def test_release_job_present(self, workflow: dict):
        assert "release" in workflow["jobs"]
