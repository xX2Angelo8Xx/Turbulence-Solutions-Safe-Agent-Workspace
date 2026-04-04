import pytest
pytestmark = pytest.mark.skip(reason="CLOUD-orchestrator.agent.md was removed; tests require both orchestrator files")

"""Tests for DOC-034 — Update orchestrator release instructions.

Verifies that both orchestrator agent files contain the correct CI/CD Pipeline
Trigger documentation referencing scripts/release.py as the primary release method.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
ORCHESTRATOR = REPO_ROOT / ".github" / "agents" / "orchestrator.agent.md"
CLOUD_ORCHESTRATOR = REPO_ROOT / ".github" / "agents" / "CLOUD-orchestrator.agent.md"

AGENT_FILES = [ORCHESTRATOR, CLOUD_ORCHESTRATOR]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _cicd_section(content: str) -> str:
    """Extract the CI/CD Pipeline Trigger section from file content."""
    match = re.search(
        r"(## CI/CD Pipeline Trigger.*?)(?=\n## |\Z)",
        content,
        re.DOTALL,
    )
    assert match, "CI/CD Pipeline Trigger section not found"
    return match.group(1)


def test_both_files_contain_release_script_reference():
    """Both agent files must reference scripts/release.py."""
    for path in AGENT_FILES:
        content = _read(path)
        assert "scripts/release.py" in content, (
            f"{path.name} does not reference scripts/release.py"
        )


def test_both_files_contain_dry_run_documentation():
    """Both agent files must document the --dry-run flag."""
    for path in AGENT_FILES:
        content = _read(path)
        assert "--dry-run" in content, (
            f"{path.name} does not document --dry-run"
        )


def test_both_files_mention_validate_version_ci_job():
    """Both agent files must mention the validate-version CI job."""
    for path in AGENT_FILES:
        content = _read(path)
        assert "validate-version" in content, (
            f"{path.name} does not mention validate-version CI job"
        )


def test_both_files_have_fallback_section():
    """Both agent files must have a Fallback section for manual tag operations."""
    for path in AGENT_FILES:
        content = _read(path)
        assert "Fallback" in content, (
            f"{path.name} does not have a Fallback section"
        )


def test_neither_file_uses_old_manual_tag_creation_as_primary():
    """Neither file should use git tag -a as a primary (non-fallback) step."""
    for path in AGENT_FILES:
        content = _read(path)
        section = _cicd_section(content)
        # The old instructions had `git tag -a` outside of a fallback context.
        # We allow it only inside the Fallback subsection.
        fallback_split = re.split(r"### Fallback", section, maxsplit=1)
        primary_section = fallback_split[0]
        assert "git tag -a" not in primary_section, (
            f"{path.name} still uses 'git tag -a' as a primary step "
            "(should only appear in Fallback section)"
        )


def test_cicd_pipeline_trigger_section_exists_in_both_files():
    """The CI/CD Pipeline Trigger section must exist in both agent files."""
    for path in AGENT_FILES:
        content = _read(path)
        assert "## CI/CD Pipeline Trigger" in content, (
            f"{path.name} is missing the CI/CD Pipeline Trigger section"
        )


def test_cicd_section_content_is_identical_in_both_files():
    """The CI/CD Pipeline Trigger section must be identical in both agent files."""
    orchestrator_section = _cicd_section(_read(ORCHESTRATOR))
    cloud_section = _cicd_section(_read(CLOUD_ORCHESTRATOR))
    assert orchestrator_section == cloud_section, (
        "CI/CD Pipeline Trigger section differs between "
        "orchestrator.agent.md and CLOUD-orchestrator.agent.md"
    )
