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
        # Updated per FIX-038/FIX-039: component-level verification; no --deep --strict on .app bundle
        assert "codesign --verify" in run_cmd

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
        """Step must verify the pre-bundle binary, Python.framework, and the .app bundle.
        Updated per FIX-038 (component-level) and FIX-039 (pre-bundle binary)."""
        step = next(s for s in macos_steps if s.get("name") == "Verify Code Signing")
        run_cmd: str = step["run"]
        # Must verify the pre-bundle binary (FIX-039)
        assert "dist/launcher/launcher" in run_cmd, (
            f"Step must verify dist/launcher/launcher. Actual: {run_cmd!r}"
        )
        # Must verify Python.framework (FIX-038 component-level)
        assert "Python.framework" in run_cmd, (
            f"Step must verify Python.framework. Actual: {run_cmd!r}"
        )
        # Must verify the .app bundle
        assert "dist/AgentEnvironmentLauncher.app" in run_cmd, (
            f"Step must verify dist/AgentEnvironmentLauncher.app. Actual: {run_cmd!r}"
        )
        # Must include a success message
        assert "Code signing verification passed" in run_cmd, (
            f"Step must echo 'Code signing verification passed'. Actual: {run_cmd!r}"
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

    def test_release_job_has_no_codesign_step(self, workflow: dict):
        steps = workflow["jobs"]["release"]["steps"]
        names = _step_names(steps)
        assert "Verify Code Signing" not in names


class TestVerifyStepSafeguards:
    """Edge-case guard tests: the step must always execute and cannot be silenced."""

    def test_step_has_no_continue_on_error(self, macos_steps: list):
        """continue-on-error: true would make a failing codesign pass silently."""
        step = next(s for s in macos_steps if s.get("name") == "Verify Code Signing")
        assert step.get("continue-on-error", False) is not True, (
            "Verify Code Signing must NOT have continue-on-error: true"
        )

    def test_step_has_no_if_condition(self, macos_steps: list):
        """An 'if:' condition could cause the step to be skipped unexpectedly."""
        step = next(s for s in macos_steps if s.get("name") == "Verify Code Signing")
        assert "if" not in step, (
            "Verify Code Signing must not have an 'if:' condition that could skip it"
        )

    def test_step_has_no_shell_override(self, macos_steps: list):
        """No custom shell override — must use the default runner shell."""
        step = next(s for s in macos_steps if s.get("name") == "Verify Code Signing")
        assert "shell" not in step, (
            "Verify Code Signing must not override the default shell"
        )

    def test_only_one_codesign_verify_step_in_entire_workflow(self, workflow: dict):
        """There should be exactly one Verify Code Signing step across all jobs."""
        count = 0
        for job in workflow["jobs"].values():
            for step in job.get("steps", []):
                if step.get("name") == "Verify Code Signing":
                    count += 1
        assert count == 1, (
            f"Expected exactly 1 'Verify Code Signing' step in the workflow, found {count}"
        )

    def test_step_run_contains_strict_flag(self, macos_steps: list):
        """Step must verify the pre-bundle binary per FIX-039 (replaces --strict on .app).
        Updated per FIX-038: --strict on the whole .app bundle was removed in favour of
        component-level verification; pre-bundle binary verification added per FIX-039."""
        step = next(s for s in macos_steps if s.get("name") == "Verify Code Signing")
        run_cmd: str = step["run"]
        # FIX-039: pre-bundle binary must be verified
        assert "dist/launcher/launcher" in run_cmd, (
            "Verify Code Signing step must verify dist/launcher/launcher (pre-bundle binary)"
        )

    def test_step_run_contains_deep_flag(self, macos_steps: list):
        """The --deep flag must be present to check nested components."""
        step = next(s for s in macos_steps if s.get("name") == "Verify Code Signing")
        assert "--deep" in step["run"]


class TestWorkflowTriggerIntegrity:
    """The workflow trigger must not have changed.

    Note: YAML's ``on:`` key is a reserved boolean — yaml.safe_load parses it
    as Python ``True``, not the string ``"on"``.
    """

    def test_workflow_triggers_on_push(self, workflow: dict):
        # yaml.safe_load maps the YAML `on:` key to Python ``True``
        triggers = workflow[True]
        assert "push" in triggers

    def test_push_trigger_uses_version_tags(self, workflow: dict):
        triggers = workflow[True]
        tags = triggers["push"]["tags"]
        assert "v*.*.*" in tags, f"Expected 'v*.*.*' tag pattern, got: {tags}"

    def test_no_pull_request_trigger(self, workflow: dict):
        triggers = workflow[True]
        assert "pull_request" not in triggers and \
               "pull_request_target" not in triggers, \
               "Workflow must not have a pull_request trigger (security risk)"
