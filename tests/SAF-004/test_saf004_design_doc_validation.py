"""SAF-004: Validate terminal-sanitization-design.md exists and has required content."""
from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_design_doc_exists():
    """terminal-sanitization-design.md must exist."""
    doc = REPO_ROOT / "docs" / "workpackages" / "SAF-004" / "terminal-sanitization-design.md"
    assert doc.exists(), "terminal-sanitization-design.md must exist in docs/workpackages/SAF-004/"

def test_design_doc_has_sufficient_content():
    """Design doc must be >100 lines (substantive document)."""
    doc = REPO_ROOT / "docs" / "workpackages" / "SAF-004" / "terminal-sanitization-design.md"
    content = doc.read_text(encoding="utf-8")
    lines = content.splitlines()
    assert len(lines) > 100, (
        f"Design doc has only {len(lines)} lines — expected >100 for a substantive design document"
    )

def test_design_doc_has_required_sections():
    """Design doc must contain key section headings."""
    doc = REPO_ROOT / "docs" / "workpackages" / "SAF-004" / "terminal-sanitization-design.md"
    content = doc.read_text(encoding="utf-8").lower()
    
    # A terminal sanitization design doc should cover these topics
    required_keywords = ["sanitiz", "terminal", "security"]
    for keyword in required_keywords:
        assert keyword in content, (
            f"Design doc should mention '{keyword}'"
        )
