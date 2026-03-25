"""Tests for DOC-017: Verify all documentation reflects the template rename.

Old names that must NOT exist in live docs:
  - templates/coding/
  - creative-marketing
  - templates/creative/  (old project-scope placeholder)

New names that MUST exist in their respective files:
  - templates/agent-workbench/
  - templates/certification-pipeline/
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Files that MUST NOT contain old template path references
LIVE_DOC_FILES = [
    REPO_ROOT / "docs" / "architecture.md",
    REPO_ROOT / "docs" / "project-scope.md",
    REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md",
    REPO_ROOT / "docs" / "work-rules" / "index.md",
    REPO_ROOT / "docs" / "work-rules" / "maintenance-protocol.md",
    REPO_ROOT / "docs" / "work-rules" / "security-rules.md",
    REPO_ROOT / ".github" / "instructions" / "copilot-instructions.md",
]

# Patterns that must NOT appear in the live doc files
STALE_PATTERNS = [
    r"templates/coding/",
    r"templates/creative-marketing/",
    r"templates/creative/",
    # Old template display name in a table cell context (not as a word inside other words)
    r"\|\s*Coding\s*\|",
    r"\|\s*Creative\s*/\s*Marketing\s*\|",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Stale reference tests
# ---------------------------------------------------------------------------

def test_architecture_no_stale_coding_path():
    content = _read(REPO_ROOT / "docs" / "architecture.md")
    assert "templates/coding/" not in content, \
        "architecture.md still contains 'templates/coding/'"


def test_architecture_no_stale_creative_marketing():
    content = _read(REPO_ROOT / "docs" / "architecture.md")
    assert "creative-marketing/" not in content, \
        "architecture.md still contains 'creative-marketing/'"


def test_project_scope_no_stale_coding_path():
    content = _read(REPO_ROOT / "docs" / "project-scope.md")
    assert "templates/coding/" not in content, \
        "project-scope.md still contains 'templates/coding/'"


def test_project_scope_no_stale_creative_path():
    content = _read(REPO_ROOT / "docs" / "project-scope.md")
    assert "templates/creative/" not in content and "creative-marketing" not in content, \
        "project-scope.md still contains old creative template path"


def test_agent_workflow_no_stale_coding_path():
    content = _read(REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md")
    assert "templates/coding/" not in content, \
        "agent-workflow.md still contains 'templates/coding/'"


def test_index_no_stale_coding_path():
    content = _read(REPO_ROOT / "docs" / "work-rules" / "index.md")
    assert "templates/coding/" not in content, \
        "index.md still contains 'templates/coding/'"


def test_maintenance_protocol_no_stale_coding_path():
    content = _read(REPO_ROOT / "docs" / "work-rules" / "maintenance-protocol.md")
    assert "templates/coding/" not in content, \
        "maintenance-protocol.md still contains 'templates/coding/'"


def test_security_rules_no_stale_coding_path():
    content = _read(REPO_ROOT / "docs" / "work-rules" / "security-rules.md")
    assert "templates/coding/" not in content, \
        "security-rules.md still contains 'templates/coding/'"


def test_copilot_instructions_no_stale_coding_path():
    content = _read(REPO_ROOT / ".github" / "instructions" / "copilot-instructions.md")
    assert "templates/coding/" not in content, \
        "copilot-instructions.md still contains 'templates/coding/'"


# ---------------------------------------------------------------------------
# New name presence tests
# ---------------------------------------------------------------------------

def test_architecture_has_agent_workbench():
    content = _read(REPO_ROOT / "docs" / "architecture.md")
    assert "agent-workbench/" in content, \
        "architecture.md does not reference 'agent-workbench/'"


def test_architecture_has_certification_pipeline():
    content = _read(REPO_ROOT / "docs" / "architecture.md")
    assert "certification-pipeline/" in content, \
        "architecture.md does not reference 'certification-pipeline/'"


def test_project_scope_has_agent_workbench():
    content = _read(REPO_ROOT / "docs" / "project-scope.md")
    assert "templates/agent-workbench/" in content, \
        "project-scope.md does not reference 'templates/agent-workbench/'"


def test_project_scope_has_certification_pipeline():
    content = _read(REPO_ROOT / "docs" / "project-scope.md")
    assert "templates/certification-pipeline/" in content, \
        "project-scope.md does not reference 'templates/certification-pipeline/'"


def test_index_has_agent_workbench():
    content = _read(REPO_ROOT / "docs" / "work-rules" / "index.md")
    assert "templates/agent-workbench/" in content, \
        "index.md does not reference 'templates/agent-workbench/'"


def test_maintenance_protocol_has_agent_workbench():
    content = _read(REPO_ROOT / "docs" / "work-rules" / "maintenance-protocol.md")
    assert "templates/agent-workbench/" in content, \
        "maintenance-protocol.md does not reference 'templates/agent-workbench/'"


def test_security_rules_has_agent_workbench():
    content = _read(REPO_ROOT / "docs" / "work-rules" / "security-rules.md")
    assert "templates/agent-workbench/" in content, \
        "security-rules.md does not reference 'templates/agent-workbench/'"


def test_copilot_instructions_has_agent_workbench():
    content = _read(REPO_ROOT / ".github" / "instructions" / "copilot-instructions.md")
    assert "templates/agent-workbench/" in content, \
        "copilot-instructions.md does not reference 'templates/agent-workbench/'"


# ---------------------------------------------------------------------------
# Copilot instructions line count constraint
# ---------------------------------------------------------------------------

def test_copilot_instructions_under_40_lines():
    lines = _read(REPO_ROOT / ".github" / "instructions" / "copilot-instructions.md").splitlines()
    assert len(lines) <= 40, \
        f"copilot-instructions.md exceeds 40-line limit: {len(lines)} lines"
