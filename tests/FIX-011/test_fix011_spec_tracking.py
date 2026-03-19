"""
FIX-011 — Tests for CI Spec File Tracking and Intel Mac Build Removal

Verifies:
  1. .gitignore contains the !launcher.spec negation after *.spec
  2. launcher.spec exists at repository root
  3. release.yml has NO macos-intel-build job
  4. release job needs does NOT include macos-intel-build
  5. release job needs is exactly [windows-build, macos-arm-build, linux-build]
"""

import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
GITIGNORE_PATH = REPO_ROOT / ".gitignore"
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"
LAUNCHER_SPEC_PATH = REPO_ROOT / "launcher.spec"

EXPECTED_RELEASE_NEEDS = ["windows-build", "macos-arm-build", "linux-build"]


@pytest.fixture(scope="module")
def workflow():
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def gitignore_content():
    return GITIGNORE_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# .gitignore negation
# ---------------------------------------------------------------------------

def test_gitignore_has_spec_negation(gitignore_content):
    """!launcher.spec exception must be present in .gitignore."""
    assert "!launcher.spec" in gitignore_content, (
        "!launcher.spec negation is missing from .gitignore — "
        "CI will not be able to find launcher.spec"
    )


def test_gitignore_negation_after_spec_wildcard(gitignore_content):
    """!launcher.spec must appear after the *.spec wildcard rule."""
    lines = gitignore_content.splitlines()
    spec_idx = next(
        (i for i, ln in enumerate(lines) if ln.strip() == "*.spec"),
        None,
    )
    negation_idx = next(
        (i for i, ln in enumerate(lines) if ln.strip() == "!launcher.spec"),
        None,
    )
    assert spec_idx is not None, "*.spec rule not found in .gitignore"
    assert negation_idx is not None, "!launcher.spec negation not found in .gitignore"
    assert negation_idx > spec_idx, (
        f"!launcher.spec (line {negation_idx + 1}) must come after "
        f"*.spec (line {spec_idx + 1}) to override it"
    )


# ---------------------------------------------------------------------------
# launcher.spec existence
# ---------------------------------------------------------------------------

def test_launcher_spec_exists_on_disk():
    """launcher.spec must exist at the repository root."""
    assert LAUNCHER_SPEC_PATH.is_file(), (
        f"launcher.spec not found at {LAUNCHER_SPEC_PATH} — "
        "CI will fail with 'Spec file not found'"
    )


def test_launcher_spec_tracked_by_git():
    """launcher.spec must be tracked in the git index (not ignored)."""
    result = subprocess.run(
        ["git", "ls-files", "--", "launcher.spec"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "launcher.spec", (
        "launcher.spec is not tracked by git. "
        "Run: git add -f launcher.spec"
    )


def test_launcher_spec_not_ignored_by_git():
    """git check-ignore must NOT return 0 for launcher.spec (negation in effect)."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", "launcher.spec"],
        cwd=str(REPO_ROOT),
        capture_output=True,
    )
    assert result.returncode != 0, (
        "git check-ignore says launcher.spec is ignored — "
        "the !launcher.spec negation in .gitignore is not working. "
        "Verify !launcher.spec appears after *.spec in .gitignore."
    )


# ---------------------------------------------------------------------------
# release.yml — macos-intel-build removed
# ---------------------------------------------------------------------------

def test_release_yml_no_macos_intel_job(workflow):
    """release.yml must NOT contain a macos-intel-build job."""
    assert "macos-intel-build" not in workflow.get("jobs", {}), (
        "macos-intel-build job still exists in release.yml — "
        "it must be removed (GitHub no longer offers Intel Mac runners)"
    )


def test_release_job_needs_no_intel(workflow):
    """release job needs must NOT include macos-intel-build."""
    needs = workflow["jobs"]["release"].get("needs", [])
    assert "macos-intel-build" not in needs, (
        f"release job still lists macos-intel-build in needs: {needs}"
    )


def test_release_job_needs_exact(workflow):
    """release job needs must be exactly [windows-build, macos-arm-build, linux-build]."""
    needs = workflow["jobs"]["release"].get("needs", [])
    assert sorted(needs) == sorted(EXPECTED_RELEASE_NEEDS), (
        f"release job needs mismatch.\n"
        f"  Expected (sorted): {sorted(EXPECTED_RELEASE_NEEDS)}\n"
        f"  Got (sorted):      {sorted(needs)}"
    )


def test_release_job_needs_count(workflow):
    """release job needs must contain exactly 3 jobs."""
    needs = workflow["jobs"]["release"].get("needs", [])
    assert len(needs) == 3, (
        f"release job needs should have 3 entries but has {len(needs)}: {needs}"
    )
