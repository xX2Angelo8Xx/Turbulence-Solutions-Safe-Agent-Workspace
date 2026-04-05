"""
MNT-027: Narrow CI to Windows-only — test suite
"""
import re
from pathlib import Path

WORKFLOWS = Path(".github/workflows")


def _read(filename: str) -> str:
    return (WORKFLOWS / filename).read_text(encoding="utf-8")


def test_test_yml_matrix_windows_only():
    """test.yml matrix.os must only contain windows-latest."""
    content = _read("test.yml")
    # Find the os: line within the matrix block
    match = re.search(r"matrix:\s.*?os:\s*\[([^\]]+)\]", content, re.DOTALL)
    assert match, "Could not find matrix.os in test.yml"
    os_list = [o.strip().strip("'\"") for o in match.group(1).split(",")]
    assert os_list == ["windows-latest"], (
        f"Expected matrix.os == ['windows-latest'], got {os_list}"
    )


def test_test_yml_manifest_check_on_windows():
    """manifest-check job must run on windows-latest (not ubuntu-latest)."""
    content = _read("test.yml")
    # Find manifest-check job section
    match = re.search(r"manifest-check:\s*\n\s*runs-on:\s*(\S+)", content)
    assert match, "Could not find manifest-check job in test.yml"
    assert match.group(1) == "windows-latest", (
        f"manifest-check must run on windows-latest, got {match.group(1)}"
    )


def test_test_yml_parity_check_on_windows():
    """parity-check job must run on windows-latest (not ubuntu-latest)."""
    content = _read("test.yml")
    match = re.search(r"parity-check:\s*\n\s*runs-on:\s*(\S+)", content)
    assert match, "Could not find parity-check job in test.yml"
    assert match.group(1) == "windows-latest", (
        f"parity-check must run on windows-latest, got {match.group(1)}"
    )


def test_macos_workflow_has_if_false():
    """macos-source-test.yml macos-source-install job must have 'if: false'."""
    content = _read("macos-source-test.yml")
    # The job block should contain 'if: false'
    assert "if: false" in content, (
        "Expected 'if: false' in macos-source-test.yml but not found"
    )


def test_macos_workflow_has_adr_comment():
    """macos-source-test.yml must include ADR-010 disable comment."""
    content = _read("macos-source-test.yml")
    assert "ADR-010" in content, (
        "Expected ADR-010 comment in macos-source-test.yml but not found"
    )


def test_staging_no_ubuntu_job():
    """staging-test.yml must not have smoke-test-ubuntu job."""
    content = _read("staging-test.yml")
    assert "smoke-test-ubuntu" not in content, (
        "smoke-test-ubuntu job found in staging-test.yml — should be removed"
    )


def test_staging_no_macos_job():
    """staging-test.yml must not have smoke-test-macos job."""
    content = _read("staging-test.yml")
    assert "smoke-test-macos" not in content, (
        "smoke-test-macos job found in staging-test.yml — should be removed"
    )


def test_staging_summary_needs_only_windows():
    """staging-summary job needs must only reference smoke-test-windows."""
    content = _read("staging-test.yml")
    match = re.search(r"staging-summary:\s*\n\s*needs:\s*\[([^\]]+)\]", content)
    assert match, "Could not find staging-summary needs in staging-test.yml"
    needs = [n.strip() for n in match.group(1).split(",")]
    assert needs == ["smoke-test-windows"], (
        f"staging-summary needs must be [smoke-test-windows], got {needs}"
    )


def test_release_no_macos_arm_build_job():
    """release.yml must not have macos-arm-build job."""
    content = _read("release.yml")
    assert "macos-arm-build:" not in content, (
        "macos-arm-build job found in release.yml — should be removed"
    )


def test_release_no_linux_build_job():
    """release.yml must not have linux-build job."""
    content = _read("release.yml")
    assert "linux-build:" not in content, (
        "linux-build job found in release.yml — should be removed"
    )


def test_release_run_tests_matrix_windows_only():
    """release.yml run-tests matrix must only contain windows-latest."""
    content = _read("release.yml")
    # Find the matrix os list in the run-tests job
    match = re.search(r"run-tests:.*?matrix:.*?os:\s*\[([^\]]+)\]", content, re.DOTALL)
    assert match, "Could not find run-tests matrix.os in release.yml"
    os_list = [o.strip().strip("'\"") for o in match.group(1).split(",")]
    assert os_list == ["windows-latest"], (
        f"Expected run-tests matrix.os == ['windows-latest'], got {os_list}"
    )


def test_release_job_needs_only_windows_build():
    """release job needs must only reference windows-build."""
    content = _read("release.yml")
    match = re.search(r"^  release:\s*\n\s*needs:\s*\[([^\]]+)\]", content, re.MULTILINE)
    assert match, "Could not find release job needs in release.yml"
    needs = [n.strip() for n in match.group(1).split(",")]
    assert needs == ["windows-build"], (
        f"release needs must be [windows-build], got {needs}"
    )


def test_project_scope_has_platform_table():
    """docs/project-scope.md must contain the Platform Support Status table."""
    content = Path("docs/project-scope.md").read_text(encoding="utf-8")
    assert "## Platform Support Status" in content, (
        "Platform Support Status section not found in docs/project-scope.md"
    )
    assert "| Windows | Active | Yes |" in content, (
        "Windows Active row not found in Platform Support Status table"
    )
    assert "| macOS | Deferred | No |" in content, (
        "macOS Deferred row not found in Platform Support Status table"
    )
    assert "| Linux | Deferred | No |" in content, (
        "Linux Deferred row not found in Platform Support Status table"
    )


def test_architecture_md_has_ci_note():
    """docs/architecture.md must contain CI/CD Windows-only note."""
    content = Path("docs/architecture.md").read_text(encoding="utf-8")
    assert "CI/CD currently targets Windows only" in content, (
        "CI/CD Windows-only note not found in docs/architecture.md"
    )
