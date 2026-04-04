"""
Tests for DOC-059: Update testing protocol and propose ADR-008.

Verifies:
- ADR-008 file exists in docs/decisions/
- docs/decisions/index.jsonl contains the ADR-008 entry
- docs/work-rules/testing-protocol.md contains the new "Test Maintenance During Refactors" section
- The key refactor rule text is present in testing-protocol.md
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

ADR_FILE = REPO_ROOT / "docs" / "decisions" / "ADR-008-tests-track-code.md"
INDEX_FILE = REPO_ROOT / "docs" / "decisions" / "index.jsonl"
PROTOCOL_FILE = REPO_ROOT / "docs" / "work-rules" / "testing-protocol.md"


def test_adr008_file_exists():
    """ADR-008 markdown file must exist in docs/decisions/."""
    assert ADR_FILE.exists(), f"ADR-008 file not found at {ADR_FILE}"


def test_adr008_file_has_required_sections():
    """ADR-008 must contain the standard ADR sections."""
    content = ADR_FILE.read_text(encoding="utf-8")
    required_sections = ["## Context", "## Decision", "## Consequences"]
    for section in required_sections:
        assert section in content, f"ADR-008 is missing section: {section}"


def test_adr008_in_index_jsonl():
    """docs/decisions/index.jsonl must have an entry for ADR-008."""
    lines = INDEX_FILE.read_text(encoding="utf-8").splitlines()
    entries = [json.loads(line) for line in lines if line.strip()]
    adr_ids = [e["ADR-ID"] for e in entries]
    assert "ADR-008" in adr_ids, f"ADR-008 not found in index.jsonl. Found: {adr_ids}"


def test_adr008_index_entry_fields():
    """ADR-008 index entry must have required fields populated."""
    lines = INDEX_FILE.read_text(encoding="utf-8").splitlines()
    entries = [json.loads(line) for line in lines if line.strip()]
    adr008 = next((e for e in entries if e["ADR-ID"] == "ADR-008"), None)
    assert adr008 is not None, "ADR-008 entry not found in index.jsonl"
    assert adr008.get("Title"), "ADR-008 Title is empty"
    assert adr008.get("Status") == "Active", f"ADR-008 Status expected 'Active', got: {adr008.get('Status')}"
    assert adr008.get("Date") == "2026-04-04", f"ADR-008 Date expected '2026-04-04', got: {adr008.get('Date')}"
    related_wps = adr008.get("Related WPs", [])
    assert "DOC-059" in related_wps, f"DOC-059 not in ADR-008 Related WPs: {related_wps}"


def test_testing_protocol_has_refactor_section():
    """testing-protocol.md must contain the 'Test Maintenance During Refactors' section heading."""
    content = PROTOCOL_FILE.read_text(encoding="utf-8")
    assert "## Test Maintenance During Refactors" in content, (
        "testing-protocol.md is missing the '## Test Maintenance During Refactors' section"
    )


def test_testing_protocol_has_refactor_rule():
    """testing-protocol.md must contain the key refactor rule about updating tests in the same commit."""
    content = PROTOCOL_FILE.read_text(encoding="utf-8")
    assert "MUST update all affected test assertions in the same commit or PR" in content, (
        "testing-protocol.md is missing the mandatory refactor rule text"
    )


def test_testing_protocol_has_developer_checklist():
    """testing-protocol.md must contain the Developer Checklist for Refactors."""
    content = PROTOCOL_FILE.read_text(encoding="utf-8")
    assert "Developer Checklist for Refactors" in content, (
        "testing-protocol.md is missing the 'Developer Checklist for Refactors' subsection"
    )


def test_testing_protocol_has_adr008_reference():
    """testing-protocol.md must reference ADR-008 to link back to the decision record."""
    content = PROTOCOL_FILE.read_text(encoding="utf-8")
    assert "ADR-008" in content, (
        "testing-protocol.md does not reference ADR-008"
    )
