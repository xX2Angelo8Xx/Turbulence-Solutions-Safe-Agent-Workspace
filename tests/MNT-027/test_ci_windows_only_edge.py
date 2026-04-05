"""
MNT-027: Edge-case tests by Tester Agent

Covers:
- Orphaned 'needs' references (jobs that no longer exist)
- Source code files were NOT deleted (cross-platform preservation)
- Workflow files were NOT deleted (only modified/disabled)
- macos-source-test.yml still has a valid job (just gated by if: false)
- release.yml release job doesn't reference removed jobs
- No ubuntu/linux runner in test.yml matrix
- staging-test.yml staging-summary doesn't reference deleted jobs
- docs accurately describe deferred (not "removed") platform support
"""
import re
from pathlib import Path

WORKFLOWS = Path(".github/workflows")


def _read(filename: str) -> str:
    return (WORKFLOWS / filename).read_text(encoding="utf-8")


# ── Orphaned needs checks ──────────────────────────────────────────────────────

def test_staging_summary_no_orphaned_needs():
    """staging-summary.needs must not reference jobs that no longer exist."""
    content = _read("staging-test.yml")
    match = re.search(r"staging-summary:\s*\n\s*needs:\s*\[([^\]]+)\]", content)
    assert match, "staging-summary needs block not found"
    needs = [n.strip() for n in match.group(1).split(",")]
    # All referenced jobs must be defined in the file
    for job in needs:
        assert re.search(rf"^  {re.escape(job)}:", content, re.MULTILINE), (
            f"staging-summary references non-existent job: {job}"
        )


def test_release_job_no_orphaned_needs():
    """release.needs must only reference jobs that still exist in release.yml."""
    content = _read("release.yml")
    match = re.search(r"^  release:\s*\n\s*needs:\s*\[([^\]]+)\]", content, re.MULTILINE)
    assert match, "release job needs block not found"
    needs = [n.strip() for n in match.group(1).split(",")]
    for job in needs:
        assert re.search(rf"^  {re.escape(job)}:", content, re.MULTILINE), (
            f"release job references non-existent job: {job}"
        )


def test_release_windows_build_no_orphaned_needs():
    """windows-build.needs must only reference jobs that still exist in release.yml."""
    content = _read("release.yml")
    match = re.search(r"windows-build:\s*\n\s*needs:\s*\[([^\]]+)\]", content)
    assert match, "windows-build needs block not found"
    needs = [n.strip() for n in match.group(1).split(",")]
    for job in needs:
        assert re.search(rf"^  {re.escape(job)}:", content, re.MULTILINE), (
            f"windows-build references non-existent job: {job}"
        )


# ── No Linux/Ubuntu runners in test.yml ───────────────────────────────────────

def test_test_yml_no_ubuntu_runner():
    """test.yml must not contain ubuntu-latest as a runner for matrix jobs."""
    content = _read("test.yml")
    # Find the matrix os list
    match = re.search(r"matrix:\s.*?os:\s*\[([^\]]+)\]", content, re.DOTALL)
    assert match, "matrix.os not found in test.yml"
    os_list_raw = match.group(1)
    assert "ubuntu-latest" not in os_list_raw, (
        "ubuntu-latest still present in test.yml matrix.os"
    )
    assert "macos-latest" not in os_list_raw, (
        "macos-latest still present in test.yml matrix.os"
    )


def test_test_yml_no_ubuntu_runner_anywhere():
    """test.yml must not use ubuntu-latest as runs-on for any job."""
    content = _read("test.yml")
    # Extract all runs-on values
    runs_on_values = re.findall(r"runs-on:\s*(.+)", content)
    for val in runs_on_values:
        val = val.strip()
        # Skip matrix expression — we test matrix separately
        if "${{" in val:
            continue
        assert "ubuntu" not in val.lower(), (
            f"ubuntu runner found in test.yml runs-on: {val}"
        )
        assert "macos" not in val.lower(), (
            f"macos runner found in test.yml runs-on: {val}"
        )


# ── Source code preservation ──────────────────────────────────────────────────

def test_macos_installer_source_exists():
    """src/installer/macos/build_dmg.sh must exist (source preserved, not deleted)."""
    assert Path("src/installer/macos/build_dmg.sh").exists(), (
        "macOS installer source was deleted — only CI should be disabled, not source code"
    )


def test_linux_installer_source_exists():
    """src/installer/linux/build_appimage.sh must exist (source preserved, not deleted)."""
    assert Path("src/installer/linux/build_appimage.sh").exists(), (
        "Linux installer source was deleted — only CI should be disabled, not source code"
    )


def test_macos_install_script_exists():
    """scripts/install-macos.sh must exist (source preserved)."""
    assert Path("scripts/install-macos.sh").exists(), (
        "scripts/install-macos.sh was deleted — it should be preserved"
    )


# ── Workflow files NOT deleted ────────────────────────────────────────────────

def test_macos_source_test_yml_exists():
    """macos-source-test.yml must still exist (disabled, not deleted)."""
    assert (WORKFLOWS / "macos-source-test.yml").exists(), (
        "macos-source-test.yml was deleted — it should be preserved and disabled with if: false"
    )


def test_staging_test_yml_exists():
    """staging-test.yml must still exist."""
    assert (WORKFLOWS / "staging-test.yml").exists(), (
        "staging-test.yml was deleted — unexpected"
    )


def test_release_yml_exists():
    """release.yml must still exist."""
    assert (WORKFLOWS / "release.yml").exists(), (
        "release.yml was deleted — unexpected"
    )


# ── macos-source-test.yml still has valid job structure ───────────────────────

def test_macos_workflow_job_still_defined():
    """macos-source-test.yml must still define macos-source-install job (just gated)."""
    content = _read("macos-source-test.yml")
    assert re.search(r"^  macos-source-install:", content, re.MULTILINE), (
        "macos-source-install job definition missing from macos-source-test.yml"
    )


def test_macos_workflow_if_false_on_correct_job():
    """if: false must be on the macos-source-install job, not elsewhere."""
    content = _read("macos-source-test.yml")
    # The if: false must come right after the job name (within its block)
    match = re.search(
        r"macos-source-install:\s*\n(\s+.*?\n)*?\s+if:\s*false",
        content
    )
    assert match, (
        "if: false must be a property of the macos-source-install job block"
    )


# ── Docs accuracy ─────────────────────────────────────────────────────────────

def test_project_scope_says_deferred_not_removed():
    """Platform Support Status table must use 'Deferred' (not 'Removed' or 'Dropped')."""
    content = Path("docs/project-scope.md").read_text(encoding="utf-8")
    table_match = re.search(
        r"## Platform Support Status\s*\n(.+?)(?:\n##|\Z)", content, re.DOTALL
    )
    assert table_match, "Platform Support Status section not found"
    table_text = table_match.group(1)
    assert "Removed" not in table_text, (
        "Platform table says 'Removed' — should say 'Deferred'"
    )
    assert "Dropped" not in table_text, (
        "Platform table says 'Dropped' — should say 'Deferred'"
    )


def test_architecture_md_ci_note_mentions_adr():
    """Architecture CI note must reference ADR-010."""
    content = Path("docs/architecture.md").read_text(encoding="utf-8")
    # Find the CI note and check it references ADR-010
    idx = content.find("CI/CD currently targets Windows only")
    assert idx != -1, "CI/CD Windows-only note not found in architecture.md"
    surrounding = content[max(0, idx - 50):idx + 200]
    assert "ADR-010" in surrounding, (
        "CI/CD note in architecture.md does not reference ADR-010"
    )


def test_architecture_md_ci_note_mentions_preserved():
    """Architecture CI note must clarify workflows are preserved (not deleted)."""
    content = Path("docs/architecture.md").read_text(encoding="utf-8")
    idx = content.find("CI/CD currently targets Windows only")
    assert idx != -1
    surrounding = content[max(0, idx - 50):idx + 300]
    assert "preserved" in surrounding.lower() or "disabled" in surrounding.lower(), (
        "CI/CD note should clarify macOS/Linux workflows are preserved and disabled"
    )
