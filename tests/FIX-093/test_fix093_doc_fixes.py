"""
Tests for FIX-093: Fix index.md formatting and add branch deletion rule.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_MD = REPO_ROOT / "docs" / "work-rules" / "index.md"
COMMIT_RULES_MD = REPO_ROOT / "docs" / "work-rules" / "commit-branch-rules.md"


def test_index_md_no_concatenated_rows():
    """No line in index.md should contain two table rows concatenated (|| pattern)."""
    content = INDEX_MD.read_text(encoding="utf-8")
    for lineno, line in enumerate(content.splitlines(), start=1):
        # A concatenated row would look like: ...| || |...  (pipe-pipe without newline)
        # More precisely: a line that contains two separate row starts after a cell separator
        assert "| |" not in line or line.count("|") <= 3, (
            f"index.md line {lineno} appears to have concatenated table rows: {line!r}"
        )
        # Direct check for the known bad pattern
        assert not re.search(r"\|\s*\|\s*\|", line), (
            f"index.md line {lineno} contains concatenated row pattern: {line!r}"
        )


def test_index_md_onboard_row_on_own_line():
    """'Onboard as an AI agent' must appear on its own table row line."""
    content = INDEX_MD.read_text(encoding="utf-8")
    lines = content.splitlines()
    matching = [l for l in lines if "Onboard as an AI agent" in l]
    assert len(matching) >= 1, "index.md missing 'Onboard as an AI agent' row"
    for line in matching:
        stripped = line.strip()
        # The row should start with | and not contain another full row
        assert stripped.startswith("|"), (
            f"'Onboard as an AI agent' line does not start with |: {line!r}"
        )
        # Should not also contain "Use a helper script" on the same line
        assert "Use a helper script" not in line, (
            f"'Onboard as an AI agent' and 'Use a helper script' are on the same line: {line!r}"
        )


def test_index_md_helper_script_row_on_own_line():
    """'Use a helper script' must appear on its own table row line."""
    content = INDEX_MD.read_text(encoding="utf-8")
    lines = content.splitlines()
    matching = [l for l in lines if "Use a helper script" in l]
    assert len(matching) >= 1, "index.md missing 'Use a helper script' row"
    for line in matching:
        stripped = line.strip()
        assert stripped.startswith("|"), (
            f"'Use a helper script' line does not start with |: {line!r}"
        )
        assert "Onboard as an AI agent" not in line, (
            f"'Use a helper script' and 'Onboard as an AI agent' are on the same line: {line!r}"
        )


def test_commit_branch_rules_has_deletion_section():
    """commit-branch-rules.md must contain an explicit Branch Deletion section."""
    content = COMMIT_RULES_MD.read_text(encoding="utf-8")
    assert "Branch Deletion" in content, (
        "commit-branch-rules.md is missing a 'Branch Deletion' section"
    )


def test_commit_branch_rules_deletion_mentions_local():
    """The branch deletion rule must cover local branch deletion."""
    content = COMMIT_RULES_MD.read_text(encoding="utf-8")
    assert "git branch -d" in content, (
        "commit-branch-rules.md does not mention local branch deletion (git branch -d)"
    )


def test_commit_branch_rules_deletion_mentions_remote():
    """The branch deletion rule must cover remote branch deletion."""
    content = COMMIT_RULES_MD.read_text(encoding="utf-8")
    assert "git push origin --delete" in content, (
        "commit-branch-rules.md does not mention remote branch deletion (git push origin --delete)"
    )


def test_commit_branch_rules_deletion_is_mandatory():
    """The branch deletion rule must be stated as mandatory/non-negotiable."""
    content = COMMIT_RULES_MD.read_text(encoding="utf-8")
    assert "MUST" in content or "mandatory" in content.lower() or "Mandatory" in content, (
        "commit-branch-rules.md branch deletion section does not express that deletion is mandatory"
    )
