"""Tests for DOC-047: Update tests for AGENT-RULES consolidation.

Verifies that test files in DOC-002, DOC-007, DOC-008, and DOC-009 all
reference the new AgentDocs/AGENT-RULES.md path after the DOC-045 consolidation,
and that no stale Project/AGENT-RULES.md (without AgentDocs) references remain.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
TESTS_DIR = REPO_ROOT / "tests"

# Files that should have been updated by DOC-047
UPDATED_TEST_FILES = [
    TESTS_DIR / "DOC-002" / "test_doc002_readme_placeholders.py",
    TESTS_DIR / "DOC-007" / "test_doc007_agent_rules.py",
    TESTS_DIR / "DOC-008" / "test_doc008_read_first_directive.py",
    TESTS_DIR / "DOC-008" / "test_doc008_tester_edge_cases.py",
    TESTS_DIR / "DOC-009" / "test_doc009_placeholder_replacement.py",
]

# Pattern that identifies the OLD (stale) path  — a literal path component
# "Project/AGENT-RULES" without the "AgentDocs" subdirectory in between.
# Matches: Project/AGENT-RULES.md, Project\\AGENT-RULES.md, Project/AGENT-RULES
STALE_PATH_RE = re.compile(r'Project[/\\]AGENT-RULES', re.IGNORECASE)

# Pattern for new path
NEW_PATH_RE = re.compile(r'AgentDocs[/\\]?AGENT-RULES|AgentDocs.*AGENT-RULES', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Existence checks
# ---------------------------------------------------------------------------

def test_doc007_test_file_exists():
    """tests/DOC-007/test_doc007_agent_rules.py must exist."""
    assert (TESTS_DIR / "DOC-007" / "test_doc007_agent_rules.py").is_file()


def test_doc008_test_files_exist():
    """tests/DOC-008 test files must exist."""
    assert (TESTS_DIR / "DOC-008" / "test_doc008_read_first_directive.py").is_file()
    assert (TESTS_DIR / "DOC-008" / "test_doc008_tester_edge_cases.py").is_file()


def test_doc009_placeholder_test_exists():
    """tests/DOC-009/test_doc009_placeholder_replacement.py must exist."""
    assert (TESTS_DIR / "DOC-009" / "test_doc009_placeholder_replacement.py").is_file()


def test_doc002_readme_test_exists():
    """tests/DOC-002/test_doc002_readme_placeholders.py must exist."""
    assert (TESTS_DIR / "DOC-002" / "test_doc002_readme_placeholders.py").is_file()


# ---------------------------------------------------------------------------
# No stale path constants in assertions
# ---------------------------------------------------------------------------

def test_doc007_no_stale_path_in_constant():
    """DOC-007 test file must not reference Project/AGENT-RULES (without AgentDocs) in code paths."""
    content = (TESTS_DIR / "DOC-007" / "test_doc007_agent_rules.py").read_text(encoding="utf-8")
    lines = content.splitlines()
    # Find code lines (not comments/docstrings) with stale patterns
    code_lines = [
        (i + 1, line) for i, line in enumerate(lines)
        if STALE_PATH_RE.search(line) and not line.strip().startswith("#")
    ]
    assert code_lines == [], (
        f"Stale 'Project/AGENT-RULES' path found in non-comment code lines: {code_lines}"
    )


def test_doc009_constant_uses_agentdocs():
    """DOC-009 AGENT_RULES_TEMPLATE constant must include AgentDocs subdirectory."""
    content = (TESTS_DIR / "DOC-009" / "test_doc009_placeholder_replacement.py").read_text(encoding="utf-8")
    # Find the constant assignment line
    match = re.search(r'AGENT_RULES_TEMPLATE\s*=\s*.+', content)
    assert match is not None, "AGENT_RULES_TEMPLATE constant not found"
    constant_line = match.group(0)
    assert "AgentDocs" in constant_line, (
        f"AGENT_RULES_TEMPLATE must include 'AgentDocs'. Got: {constant_line}"
    )


def test_doc009_setup_helper_uses_agentdocs():
    """DOC-009 _setup_agent_rules helper must place file under AgentDocs/ subdirectory."""
    content = (TESTS_DIR / "DOC-009" / "test_doc009_placeholder_replacement.py").read_text(encoding="utf-8")
    assert '"AgentDocs"' in content or "'AgentDocs'" in content, (
        "_setup_agent_rules helper must reference 'AgentDocs' subdirectory"
    )


def test_doc008_read_first_directive_uses_agentdocs():
    """DOC-008 read_first_directive test must assert AgentDocs path in directive."""
    content = (TESTS_DIR / "DOC-008" / "test_doc008_read_first_directive.py").read_text(encoding="utf-8")
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "test_doc008_read_first_directive.py must reference 'AgentDocs/AGENT-RULES.md'"
    )


def test_doc008_tester_edge_cases_uses_agentdocs():
    """DOC-008 tester_edge_cases must assert AgentDocs path."""
    content = (TESTS_DIR / "DOC-008" / "test_doc008_tester_edge_cases.py").read_text(encoding="utf-8")
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "test_doc008_tester_edge_cases.py must reference 'AgentDocs/AGENT-RULES.md'"
    )


def test_doc002_readme_placeholders_uses_agentdocs():
    """DOC-002 readme placeholder test must assert AgentDocs path."""
    content = (TESTS_DIR / "DOC-002" / "test_doc002_readme_placeholders.py").read_text(encoding="utf-8")
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "test_doc002_readme_placeholders.py must reference 'AgentDocs/AGENT-RULES.md'"
    )


# ---------------------------------------------------------------------------
# Actual template file location verification
# ---------------------------------------------------------------------------

def test_agentdocs_agent_rules_template_exists():
    """The real AGENT-RULES.md must exist at the new AgentDocs location."""
    new_path = REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AgentDocs" / "AGENT-RULES.md"
    assert new_path.is_file(), f"AGENT-RULES.md not found at new location: {new_path}"


def test_old_root_agent_rules_does_not_exist():
    """AGENT-RULES.md must NOT exist at the old Project/ root location."""
    old_path = REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AGENT-RULES.md"
    assert not old_path.exists(), (
        f"Stale AGENT-RULES.md found at old path {old_path} — DOC-045 consolidation required removal."
    )


# ---------------------------------------------------------------------------
# Path consistency across all updated files
# ---------------------------------------------------------------------------

def test_all_updated_files_reference_agentdocs():
    """Every file updated by DOC-047 must contain at least one AgentDocs/AGENT-RULES reference."""
    missing = []
    for path in UPDATED_TEST_FILES:
        if path.is_file():
            content = path.read_text(encoding="utf-8")
            if "AgentDocs" not in content:
                missing.append(str(path.relative_to(REPO_ROOT)))
    assert missing == [], f"These files do not reference AgentDocs: {missing}"
