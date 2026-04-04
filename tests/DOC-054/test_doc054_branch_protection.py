"""Tests for DOC-054: Document Branch Protection Requirements.

Verifies that docs/work-rules/branch-protection.md exists, contains
all required sections, and is correctly referenced from
commit-branch-rules.md and docs/work-rules/index.md.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BRANCH_PROTECTION_MD = REPO_ROOT / "docs" / "work-rules" / "branch-protection.md"
COMMIT_BRANCH_RULES_MD = REPO_ROOT / "docs" / "work-rules" / "commit-branch-rules.md"
INDEX_MD = REPO_ROOT / "docs" / "work-rules" / "index.md"


# ---------------------------------------------------------------------------
# File existence
# ---------------------------------------------------------------------------


def test_branch_protection_file_exists():
    """docs/work-rules/branch-protection.md must exist."""
    assert BRANCH_PROTECTION_MD.exists(), (
        f"Expected {BRANCH_PROTECTION_MD} to exist but it was not found."
    )


# ---------------------------------------------------------------------------
# Required content checks
# ---------------------------------------------------------------------------


def _read_branch_protection() -> str:
    return BRANCH_PROTECTION_MD.read_text(encoding="utf-8")


def test_branch_protection_title():
    """The file must have a top-level heading 'Branch Protection Requirements'."""
    content = _read_branch_protection()
    assert "# Branch Protection Requirements" in content, (
        "Expected heading '# Branch Protection Requirements' not found."
    )


def test_branch_protection_mentions_main_branch():
    """The document must explicitly scope the rules to the 'main' branch."""
    content = _read_branch_protection()
    assert "main" in content, (
        "Expected branch name 'main' to appear in branch-protection.md."
    )


def test_branch_protection_mentions_pr_review():
    """The document must require pull request reviews."""
    content = _read_branch_protection()
    keywords = ["pull request", "Pull Request", "PR"]
    assert any(kw in content for kw in keywords), (
        "Expected a pull request review requirement to be documented."
    )


def test_branch_protection_mentions_required_approvals():
    """The document must specify at least 1 required approval."""
    content = _read_branch_protection()
    assert "Required approvals" in content or "required approval" in content.lower(), (
        "Expected 'required approvals' count to be mentioned."
    )


def test_branch_protection_mentions_status_check():
    """The document must reference the 'test' status check from test.yml."""
    content = _read_branch_protection()
    # We expect either the job name "test" or "test.yml" to appear
    assert "test.yml" in content or "`test`" in content or "run-tests" in content, (
        "Expected the test.yml status check to be referenced."
    )


def test_branch_protection_mentions_no_bypass():
    """The document must instruct that bypassing branch protection is disabled."""
    content = _read_branch_protection()
    assert "bypass" in content.lower(), (
        "Expected bypass restriction to be documented."
    )


def test_branch_protection_mentions_block_force_pushes():
    """The document must address blocking force pushes to main."""
    content = _read_branch_protection()
    assert "force push" in content.lower() or "force-push" in content.lower(), (
        "Expected force push protection to be documented."
    )


def test_branch_protection_mentions_finalize_wp():
    """The document must note the finalize_wp.py admin exception."""
    content = _read_branch_protection()
    assert "finalize_wp" in content or "finalize_wp.py" in content, (
        "Expected finalize_wp.py admin exception to be documented."
    )


def test_branch_protection_has_manual_setup_note():
    """The document must state that setup is manual (not automated)."""
    content = _read_branch_protection()
    assert "manual" in content.lower(), (
        "Expected a note that these settings require manual configuration."
    )


def test_branch_protection_references_commit_branch_rules():
    """branch-protection.md must link to commit-branch-rules.md."""
    content = _read_branch_protection()
    assert "commit-branch-rules" in content, (
        "Expected a reference to commit-branch-rules.md in branch-protection.md."
    )


def test_branch_protection_references_agent_workflow():
    """branch-protection.md must link to agent-workflow.md."""
    content = _read_branch_protection()
    assert "agent-workflow" in content, (
        "Expected a reference to agent-workflow.md in branch-protection.md."
    )


# ---------------------------------------------------------------------------
# Cross-reference checks
# ---------------------------------------------------------------------------


def test_commit_branch_rules_references_branch_protection():
    """commit-branch-rules.md must reference branch-protection.md."""
    content = COMMIT_BRANCH_RULES_MD.read_text(encoding="utf-8")
    assert "branch-protection" in content, (
        "Expected a reference to branch-protection.md in commit-branch-rules.md."
    )


def test_index_md_references_branch_protection():
    """docs/work-rules/index.md must reference branch-protection.md."""
    content = INDEX_MD.read_text(encoding="utf-8")
    assert "branch-protection" in content, (
        "Expected a reference to branch-protection.md in docs/work-rules/index.md."
    )
