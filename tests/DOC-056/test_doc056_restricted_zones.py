"""
Tests for DOC-056: Clarify Restricted Zone Paths.

Verifies that docs/work-rules/agent-workflow.md no longer contains the
ambiguous restricted-zones sentence and now has a clear table with explicit
repo-root-relative paths and a Scope column.
"""

import re
from pathlib import Path

AGENT_WORKFLOW = Path(__file__).parents[2] / "docs" / "work-rules" / "agent-workflow.md"


def _content() -> str:
    return AGENT_WORKFLOW.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Old ambiguous sentence must be gone
# ---------------------------------------------------------------------------

def test_ambiguous_sentence_removed():
    """The original ambiguous single-line restricted-zones rule is not present."""
    content = _content()
    assert "NoAgentZone/` in `templates/agent-workbench/`" not in content, (
        "Old ambiguous sentence still present in agent-workflow.md"
    )


def test_old_inline_list_removed():
    """The old pattern 'Never access .github/, .vscode/, or NoAgentZone/' is gone."""
    content = _content()
    # The original phrasing used inline backticks joined by 'or'
    assert "`.github/`, `.vscode/`, or `NoAgentZone/`" not in content, (
        "Old inline combined path list still present"
    )


# ---------------------------------------------------------------------------
# 2. New Restricted Zones heading must exist
# ---------------------------------------------------------------------------

def test_restricted_zones_heading_or_bold_exists():
    """A 'Restricted Zones' heading or bold label exists in the Rules section."""
    content = _content()
    assert "Restricted Zones" in content, (
        "No 'Restricted Zones' heading or label found in agent-workflow.md"
    )


# ---------------------------------------------------------------------------
# 3. All three paths appear as full repo-root-relative paths
# ---------------------------------------------------------------------------

def test_github_path_present():
    """`.github/` appears as a standalone table cell path."""
    content = _content()
    assert "`.github/`" in content, "`.github/` path not found in restricted zones table"


def test_vscode_path_present():
    """`.vscode/` appears as a standalone table cell path."""
    content = _content()
    assert "`.vscode/`" in content, "`.vscode/` path not found in restricted zones table"


def test_no_agent_zone_full_path_present():
    """The full path `templates/agent-workbench/NoAgentZone/` is present."""
    content = _content()
    assert "templates/agent-workbench/NoAgentZone/" in content, (
        "Full path 'templates/agent-workbench/NoAgentZone/' not found in restricted zones"
    )


# ---------------------------------------------------------------------------
# 4. Scope column header is present in the table
# ---------------------------------------------------------------------------

def test_scope_column_header_present():
    """The restricted zones table has a 'Scope' column header."""
    content = _content()
    assert "Scope" in content, (
        "No 'Scope' column header found in restricted zones table"
    )


# ---------------------------------------------------------------------------
# 5. All three restricted paths are attributed to repo root scope
# ---------------------------------------------------------------------------

def test_repo_root_scope_mentioned():
    """The text 'Repo root' or 'repository root' appears in the restricted zones context."""
    content = _content()
    has_scope = "Repo root" in content or "repository root" in content
    assert has_scope, (
        "No 'Repo root' or 'repository root' scope annotation found near restricted zones"
    )


# ---------------------------------------------------------------------------
# 6. Table structure validation
# ---------------------------------------------------------------------------

def test_table_has_three_restricted_paths():
    """The restricted zones table lists exactly three restricted paths."""
    content = _content()
    # Find the Restricted Zones section
    start = content.find("Restricted Zones")
    assert start != -1, "Restricted Zones section not found"
    # Extract text after the heading up to the next heading or horizontal rule
    section = content[start:]
    next_heading = re.search(r"\n##|\n---", section[20:])
    if next_heading:
        section = section[:20 + next_heading.start()]
    # Count table data rows (lines starting with '|' that are not header/separator)
    rows = [
        line.strip()
        for line in section.splitlines()
        if line.strip().startswith("|")
        and not re.match(r"^\|[-| ]+\|$", line.strip())  # skip separator rows
        and "Path" not in line  # skip header row
    ]
    assert len(rows) == 3, (
        f"Expected 3 restricted path rows in table, found {len(rows)}: {rows}"
    )
