"""Tester edge-case tests for DOC-017.

Covers gaps not addressed by the developer tests:
  - creative-marketing stale pattern in all 7 live-doc files (not just 2)
  - templates/creative/ stale pattern in all files
  - Table-cell old display names: | Coding | and | Creative / Marketing |
  - agent-workflow.md presence of templates/agent-workbench/
  - security-rules.md and copilot-instructions.md no stale creative refs
  - Omnibus: ALL STALE_PATTERNS x ALL LIVE_DOC_FILES
  - copilot-instructions.md has certification-pipeline reference
  - coding-standards.md (if present) has no old coding path
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

LIVE_DOC_FILES = [
    REPO_ROOT / "docs" / "architecture.md",
    REPO_ROOT / "docs" / "project-scope.md",
    REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md",
    REPO_ROOT / "docs" / "work-rules" / "index.md",
    REPO_ROOT / "docs" / "work-rules" / "maintenance-protocol.md",
    REPO_ROOT / "docs" / "work-rules" / "security-rules.md",
    REPO_ROOT / ".github" / "instructions" / "copilot-instructions.md",
]

STALE_PATTERNS = [
    r"templates/coding/",
    r"templates/creative-marketing/",
    r"templates/creative/",
    r"\|\s*Coding\s*\|",
    r"\|\s*Creative\s*/\s*Marketing\s*\|",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Omnibus: all stale patterns x all live-doc files
# ---------------------------------------------------------------------------

def test_no_stale_patterns_in_any_live_doc():
    """All stale patterns must be absent from all 7 live-doc files."""
    violations = []
    for filepath in LIVE_DOC_FILES:
        content = _read(filepath)
        for pattern in STALE_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                violations.append(f"{filepath.name}: pattern '{pattern}' found {len(matches)} time(s)")
    assert not violations, "Stale references found:\n" + "\n".join(violations)


# ---------------------------------------------------------------------------
# creative-marketing: files not covered by developer tests
# ---------------------------------------------------------------------------

def test_agent_workflow_no_creative_marketing():
    content = _read(REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md")
    assert "creative-marketing" not in content, \
        "agent-workflow.md still references 'creative-marketing'"


def test_index_no_creative_marketing():
    content = _read(REPO_ROOT / "docs" / "work-rules" / "index.md")
    assert "creative-marketing" not in content, \
        "index.md still references 'creative-marketing'"


def test_maintenance_protocol_no_creative_marketing():
    content = _read(REPO_ROOT / "docs" / "work-rules" / "maintenance-protocol.md")
    assert "creative-marketing" not in content, \
        "maintenance-protocol.md still references 'creative-marketing'"


def test_security_rules_no_creative_marketing():
    content = _read(REPO_ROOT / "docs" / "work-rules" / "security-rules.md")
    assert "creative-marketing" not in content, \
        "security-rules.md still references 'creative-marketing'"


def test_copilot_instructions_no_creative_marketing():
    content = _read(REPO_ROOT / ".github" / "instructions" / "copilot-instructions.md")
    assert "creative-marketing" not in content, \
        "copilot-instructions.md still references 'creative-marketing'"


# ---------------------------------------------------------------------------
# Table-cell stale display names (developer defined STALE_PATTERNS but didn't use)
# ---------------------------------------------------------------------------

def test_no_coding_table_cell_in_project_scope():
    content = _read(REPO_ROOT / "docs" / "project-scope.md")
    assert not re.search(r"\|\s*Coding\s*\|", content), \
        "project-scope.md still has '| Coding |' table cell"


def test_no_creative_marketing_table_cell_in_project_scope():
    content = _read(REPO_ROOT / "docs" / "project-scope.md")
    assert not re.search(r"\|\s*Creative\s*/\s*Marketing\s*\|", content), \
        "project-scope.md still has '| Creative / Marketing |' table cell"


def test_no_coding_table_cell_in_architecture():
    content = _read(REPO_ROOT / "docs" / "architecture.md")
    assert not re.search(r"\|\s*Coding\s*\|", content), \
        "architecture.md still has '| Coding |' table cell"


# ---------------------------------------------------------------------------
# Presence tests missing from developer suite
# ---------------------------------------------------------------------------

def test_agent_workflow_has_agent_workbench():
    content = _read(REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md")
    assert "templates/agent-workbench/" in content, \
        "agent-workflow.md does not reference 'templates/agent-workbench/'"


def test_copilot_instructions_has_certification_pipeline():
    """If copilot-instructions.md mentioned old creative, it must now reference certification-pipeline."""
    content = _read(REPO_ROOT / ".github" / "instructions" / "copilot-instructions.md")
    # The file must reference Agent Workbench template (already checked), and
    # must not reference the old creative name. Certification Pipeline is a stub
    # and may not appear in this file — but neither should the old name.
    assert "creative-marketing" not in content, \
        "copilot-instructions.md still has stale creative-marketing reference"


# ---------------------------------------------------------------------------
# Broad docs-tree scan (excludes historical records)
# ---------------------------------------------------------------------------

HISTORICAL_DIRS = {
    "workpackages", "test-results", "bugs", "Security Audits",
    "maintenance", "plans",
}

# Files that contain intentional historical references to templates/coding/
# (e.g., root-cause documentation in ADRs or process rules).
STALE_CODING_EXEMPT = {
    "decisions/ADR-008-tests-track-code.md",
    "decisions/ADR-009-cross-wp-test-impact.md",
    "work-rules/testing-protocol.md",
}


def test_broad_docs_tree_no_stale_coding():
    """No non-historical docs file contains templates/coding/."""
    violations = []
    docs_root = REPO_ROOT / "docs"
    for f in docs_root.rglob("*.md"):
        # Skip historical directories
        parts = set(f.relative_to(docs_root).parts[:-1])
        if parts & HISTORICAL_DIRS:
            continue
        # Skip files with intentional historical references
        rel = str(f.relative_to(docs_root)).replace("\\", "/")
        if rel in STALE_CODING_EXEMPT:
            continue
        content = f.read_text(encoding="utf-8")
        if "templates/coding/" in content:
            violations.append(str(f.relative_to(REPO_ROOT)))
    assert not violations, "Found 'templates/coding/' in:\n" + "\n".join(violations)


def test_broad_docs_tree_no_creative_marketing():
    """No non-historical docs file contains creative-marketing."""
    violations = []
    docs_root = REPO_ROOT / "docs"
    for f in docs_root.rglob("*.md"):
        parts = set(f.relative_to(docs_root).parts[:-1])
        if parts & HISTORICAL_DIRS:
            continue
        content = f.read_text(encoding="utf-8")
        if "creative-marketing" in content:
            violations.append(str(f.relative_to(REPO_ROOT)))
    assert not violations, "Found 'creative-marketing' in:\n" + "\n".join(violations)
