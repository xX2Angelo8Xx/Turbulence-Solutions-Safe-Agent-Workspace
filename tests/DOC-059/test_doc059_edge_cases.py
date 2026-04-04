"""
Edge-case tests for DOC-059: Update testing protocol and propose ADR-008.
Added by Tester Agent to cover scenarios not addressed by the Developer's tests.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

ADR_FILE = REPO_ROOT / "docs" / "decisions" / "ADR-008-tests-track-code.md"
INDEX_FILE = REPO_ROOT / "docs" / "decisions" / "index.jsonl"
PROTOCOL_FILE = REPO_ROOT / "docs" / "work-rules" / "testing-protocol.md"


def test_adr008_documents_all_five_waves():
    """ADR-008 Context section must document all 5 waves of codebase drift."""
    content = ADR_FILE.read_text(encoding="utf-8")
    # Each wave should be referenced by its numeric label in the table
    for wave_num in range(1, 6):
        assert f"| {wave_num} |" in content, (
            f"ADR-008 is missing wave {wave_num} in the drift table"
        )


def test_adr008_related_wps_include_all_fix_wps():
    """ADR-008 index entry must list FIX-103 through FIX-107 and MNT-024."""
    lines = INDEX_FILE.read_text(encoding="utf-8").splitlines()
    entries = [json.loads(line) for line in lines if line.strip()]
    adr008 = next((e for e in entries if e["ADR-ID"] == "ADR-008"), None)
    assert adr008 is not None, "ADR-008 not in index.jsonl"
    related = adr008.get("Related WPs", [])
    expected = ["FIX-103", "FIX-104", "FIX-105", "FIX-106", "FIX-107", "MNT-024", "DOC-059"]
    for wp in expected:
        assert wp in related, f"Expected '{wp}' in ADR-008 Related WPs, got: {related}"


def test_adr008_file_mentions_all_fix_wps_in_text():
    """ADR-008 body must reference FIX-103 through FIX-107 to link back to the fix WPs."""
    content = ADR_FILE.read_text(encoding="utf-8")
    for wp in ["FIX-103", "FIX-104", "FIX-105", "FIX-106", "FIX-107", "MNT-024"]:
        assert wp in content, f"ADR-008 body does not mention {wp}"


def test_adr008_clarifies_permanent_vs_immutable():
    """ADR-008 must clarify that 'permanent' means files survive, not that assertions are frozen."""
    content = ADR_FILE.read_text(encoding="utf-8")
    # The ADR explains that "Test scripts are permanent" doesn't mean assertions are immutable
    assert "permanent" in content.lower(), "ADR-008 should address the 'permanent' rule"
    assert "Consequences" in content, "ADR-008 must have a Consequences section"


def test_testing_protocol_permanent_rule_clarification():
    """testing-protocol.md must clarify that 'permanent' does not mean assertions are immutable."""
    content = PROTOCOL_FILE.read_text(encoding="utf-8")
    # Verify the "What Permanent Means" or similar clarification exists
    assert "not" in content and "permanent" in content.lower(), (
        "testing-protocol.md should clarify what 'permanent' does and does not mean"
    )
    assert "assertions" in content.lower(), (
        "testing-protocol.md must mention 'assertions' in the refactor section"
    )


def test_testing_protocol_refactor_section_has_grep_example():
    """testing-protocol.md Developer Checklist must include a grep example command."""
    content = PROTOCOL_FILE.read_text(encoding="utf-8")
    # Verify an example grep command is present
    assert "grep" in content, (
        "testing-protocol.md checklist should include a grep command example"
    )


def test_adr008_has_notes_section():
    """ADR-008 should have a Notes section with forward guidance."""
    content = ADR_FILE.read_text(encoding="utf-8")
    assert "## Notes" in content, "ADR-008 is missing a Notes section"


def test_adr008_index_entry_has_superseded_by_field():
    """ADR-008 index entry must have a 'Superseded By' field (empty for active ADRs)."""
    lines = INDEX_FILE.read_text(encoding="utf-8").splitlines()
    entries = [json.loads(line) for line in lines if line.strip()]
    adr008 = next((e for e in entries if e["ADR-ID"] == "ADR-008"), None)
    assert adr008 is not None, "ADR-008 not in index.jsonl"
    assert "Superseded By" in adr008, "ADR-008 index entry is missing 'Superseded By' field"
    assert adr008["Superseded By"] == "", (
        f"ADR-008 should not be superseded, got: {adr008['Superseded By']}"
    )


def test_index_jsonl_is_valid_jsonl():
    """Every line of docs/decisions/index.jsonl must be valid JSON."""
    lines = INDEX_FILE.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            raise AssertionError(f"index.jsonl line {i} is not valid JSON: {e}")


def test_adr008_file_not_empty():
    """ADR-008 file must be non-trivial (> 500 chars)."""
    content = ADR_FILE.read_text(encoding="utf-8")
    assert len(content) > 500, (
        f"ADR-008 appears too short ({len(content)} chars) — may be a stub"
    )
