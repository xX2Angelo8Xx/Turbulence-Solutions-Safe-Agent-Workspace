"""Tester edge-case tests for DOC-054: Document Branch Protection Requirements.

These tests cover gaps not addressed by the Developer's test suite:
- Block branch deletion is documented
- ADR-002 is referenced
- Verification steps are included
- File is valid UTF-8 with no encoding errors
- File is non-empty (basic sanity)
- Linked files (commit-branch-rules.md, index.md, agent-workflow.md) actually exist
- No absolute paths (security-rules.md §4)
- Cross-reference link target is the correct filename
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BRANCH_PROTECTION_MD = REPO_ROOT / "docs" / "work-rules" / "branch-protection.md"
COMMIT_BRANCH_RULES_MD = REPO_ROOT / "docs" / "work-rules" / "commit-branch-rules.md"
INDEX_MD = REPO_ROOT / "docs" / "work-rules" / "index.md"
AGENT_WORKFLOW_MD = REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Content completeness — gaps in Developer's tests
# ---------------------------------------------------------------------------


def test_branch_protection_mentions_block_deletion():
    """The document must address blocking deletion of the main branch."""
    content = _read(BRANCH_PROTECTION_MD)
    assert "deletion" in content.lower() or "block delet" in content.lower(), (
        "Expected branch deletion protection to be documented in branch-protection.md."
    )


def test_branch_protection_references_adr002():
    """The document must reference ADR-002 (CI Test Gate architecture decision)."""
    content = _read(BRANCH_PROTECTION_MD)
    assert "ADR-002" in content or "adr-002" in content.lower(), (
        "Expected reference to ADR-002 (Mandatory CI Test Gate) in branch-protection.md."
    )


def test_branch_protection_has_verification_section():
    """The document must include verification steps so admins can confirm settings."""
    content = _read(BRANCH_PROTECTION_MD)
    assert "verif" in content.lower(), (
        "Expected a verification section in branch-protection.md."
    )


# ---------------------------------------------------------------------------
# File integrity
# ---------------------------------------------------------------------------


def test_branch_protection_is_non_empty():
    """branch-protection.md must not be empty."""
    content = _read(BRANCH_PROTECTION_MD)
    assert len(content.strip()) > 0, "branch-protection.md is empty."


def test_branch_protection_utf8_readable():
    """branch-protection.md must be valid UTF-8 (no encoding errors)."""
    # read_text(encoding="utf-8") raises UnicodeDecodeError on invalid UTF-8.
    # If we reach this assert, the file is valid.
    content = _read(BRANCH_PROTECTION_MD)
    assert isinstance(content, str), "branch-protection.md could not be read as UTF-8."


def test_branch_protection_no_absolute_paths():
    """branch-protection.md must not include Windows or Unix absolute paths (security-rules §4)."""
    content = _read(BRANCH_PROTECTION_MD)
    # Look for Windows drive letters or Unix root paths embedded in content
    import re
    absolute_path_pattern = re.compile(r"(?:[A-Za-z]:\\|(?<!\w)/(?!/))")
    # Allow the GitHub URL scheme (https://) but flag bare /path references
    # Strip markdown hyperlinks first so [text](https://...) doesn't false-fire
    stripped = re.sub(r"https?://[^\s)]+", "", content)
    matches = absolute_path_pattern.findall(stripped)
    assert not matches, (
        f"Absolute path(s) found in branch-protection.md: {matches!r}. "
        "Use relative paths only (security-rules.md §4)."
    )


# ---------------------------------------------------------------------------
# Linked file existence (dead-link guard)
# ---------------------------------------------------------------------------


def test_commit_branch_rules_md_exists():
    """commit-branch-rules.md (linked from branch-protection.md) must exist."""
    assert COMMIT_BRANCH_RULES_MD.exists(), (
        f"Linked file {COMMIT_BRANCH_RULES_MD} does not exist."
    )


def test_agent_workflow_md_exists():
    """agent-workflow.md (linked from branch-protection.md) must exist."""
    assert AGENT_WORKFLOW_MD.exists(), (
        f"Linked file {AGENT_WORKFLOW_MD} does not exist."
    )


def test_index_md_exists():
    """docs/work-rules/index.md must exist."""
    assert INDEX_MD.exists(), f"Expected {INDEX_MD} to exist."


# ---------------------------------------------------------------------------
# Cross-reference correctness
# ---------------------------------------------------------------------------


def test_index_md_link_target_is_correct_filename():
    """index.md must link to 'branch-protection.md' (exact filename, no typos)."""
    content = _read(INDEX_MD)
    assert "branch-protection.md" in content, (
        "Expected 'branch-protection.md' (exact filename) in docs/work-rules/index.md."
    )


def test_commit_branch_rules_link_target_is_correct_filename():
    """commit-branch-rules.md must link to 'branch-protection.md' by exact filename."""
    content = _read(COMMIT_BRANCH_RULES_MD)
    assert "branch-protection.md" in content, (
        "Expected 'branch-protection.md' (exact filename) in commit-branch-rules.md."
    )
