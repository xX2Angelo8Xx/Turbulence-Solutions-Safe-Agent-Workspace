"""
Tester edge-case tests for FIX-011: Fix CI Spec File and Drop Intel Mac Build

Covers:
- launcher.spec contains valid PyInstaller content keywords
- launcher.spec is syntactically valid Python
- Raw release.yml has no macos-intel-build textual references (incl. comments)
- Raw release.yml has no macos-13 runner reference (Intel Mac runner fully removed)
- macos-arm-build runner is still macos-14 (regression guard: not accidentally changed)
- !launcher.spec negation line has exact correct syntax in .gitignore
- Other *.spec files are still ignored by git (general *.spec rule still active)
"""
import ast
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
GITIGNORE_PATH = REPO_ROOT / ".gitignore"
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"
LAUNCHER_SPEC_PATH = REPO_ROOT / "launcher.spec"

EXPECTED_SPEC_KEYWORDS = ["Analysis", "EXE", "COLLECT"]


@pytest.fixture(scope="module")
def workflow():
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def raw_workflow():
    return WORKFLOW_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# launcher.spec content integrity
# ---------------------------------------------------------------------------

def test_launcher_spec_is_valid_python():
    """launcher.spec must be syntactically valid Python (ast.parse succeeds).

    A malformed spec file (e.g. accidentally truncated during git add -f)
    would cause pyinstaller to abort immediately.
    """
    source = LAUNCHER_SPEC_PATH.read_text(encoding="utf-8")
    try:
        ast.parse(source)
    except SyntaxError as exc:
        pytest.fail(f"launcher.spec has a Python syntax error: {exc}")


def test_launcher_spec_contains_analysis_block():
    """launcher.spec must reference PyInstaller's Analysis() call.

    This is the mandatory first block in any PyInstaller spec file that
    defines the entry point, data files, and hidden imports.
    """
    content = LAUNCHER_SPEC_PATH.read_text(encoding="utf-8")
    assert "Analysis(" in content, (
        "launcher.spec does not contain an Analysis() call — "
        "the file may be corrupted or incomplete"
    )


def test_launcher_spec_contains_exe_block():
    """launcher.spec must reference PyInstaller's EXE() call."""
    content = LAUNCHER_SPEC_PATH.read_text(encoding="utf-8")
    assert "EXE(" in content, (
        "launcher.spec does not contain an EXE() call — "
        "the spec is incomplete without an executable definition"
    )


def test_launcher_spec_contains_collect_block():
    """launcher.spec must reference PyInstaller's COLLECT() call.

    COLLECT() is the --onedir bundling block. Its absence would switch the
    build to --onefile mode, which is not the intended distribution format.
    """
    content = LAUNCHER_SPEC_PATH.read_text(encoding="utf-8")
    assert "COLLECT(" in content, (
        "launcher.spec does not contain a COLLECT() call — "
        "the spec must produce an onedir bundle, not a single executable"
    )


# ---------------------------------------------------------------------------
# release.yml — complete removal of Intel Mac references
# ---------------------------------------------------------------------------

def test_raw_workflow_no_macos_intel_build_text(raw_workflow):
    """Raw release.yml text must contain no reference to 'macos-intel-build'.

    The YAML parser only checks job keys, but a comment or stray string
    could still contain the old job name. This raw-text check catches any
    residual reference including comments.
    """
    assert "macos-intel-build" not in raw_workflow, (
        "The string 'macos-intel-build' appears in release.yml raw text — "
        "it must be completely removed (including any comments)"
    )


def test_raw_workflow_no_macos_13_runner(raw_workflow):
    """Raw release.yml text must contain no reference to 'macos-13'.

    macos-13 was the GitHub-hosted Intel Mac runner. Its complete absence
    confirms the Intel build job was fully removed, not just renamed.
    """
    assert "macos-13" not in raw_workflow, (
        "The string 'macos-13' appears in release.yml — "
        "this is the Intel Mac runner, it must be completely removed"
    )


# ---------------------------------------------------------------------------
# macos-arm-build regression guard
# ---------------------------------------------------------------------------

def test_macos_arm_build_runner_unchanged(workflow):
    """macos-arm-build must still use macos-14 runner after FIX-011.

    FIX-011 only removes the intel job. The ARM job runner must not have
    been accidentally modified as a side-effect.
    """
    runner = workflow["jobs"]["macos-arm-build"]["runs-on"]
    assert runner == "macos-14", (
        f"macos-arm-build runner changed unexpectedly — "
        f"expected 'macos-14', got {runner!r}. "
        "FIX-011 should not have modified the ARM runner."
    )


# ---------------------------------------------------------------------------
# .gitignore negation syntax correctness
# ---------------------------------------------------------------------------

def test_gitignore_negation_line_exact_syntax():
    """The !launcher.spec negation in .gitignore must have exact correct syntax.

    The line must be exactly '!launcher.spec' — no trailing whitespace,
    no extra path separators, correct case. Whitespace after the '!' would
    be matched literally (not as a negation), silently breaking git tracking.
    """
    lines = GITIGNORE_PATH.read_text(encoding="utf-8").splitlines()
    negation_lines = [ln for ln in lines if ln.startswith("!launcher.spec")]
    assert negation_lines, (
        "No line starting with '!launcher.spec' found in .gitignore"
    )
    assert "!launcher.spec" in negation_lines, (
        f"The !launcher.spec line has incorrect syntax: {negation_lines}. "
        "It must be exactly '!launcher.spec' with no extra whitespace or characters."
    )


# ---------------------------------------------------------------------------
# *.spec wildcard still active for other spec files
# ---------------------------------------------------------------------------

def test_other_spec_files_still_ignored():
    """Other *.spec files (not launcher.spec) must still be ignored by git.

    The !launcher.spec negation must not have broken the general *.spec rule.
    A hypothetical 'autogenerated.spec' must still be ignored.
    """
    result = subprocess.run(
        ["git", "check-ignore", "-q", "autogenerated.spec"],
        cwd=str(REPO_ROOT),
        capture_output=True,
    )
    assert result.returncode == 0, (
        "git check-ignore did not recognise 'autogenerated.spec' as ignored — "
        "the *.spec rule may have been accidentally removed or broken by the "
        "!launcher.spec negation. Verify *.spec appears before !launcher.spec in .gitignore."
    )
