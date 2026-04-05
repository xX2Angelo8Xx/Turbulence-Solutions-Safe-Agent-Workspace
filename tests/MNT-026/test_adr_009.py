"""Tests for MNT-026: ADR-009 cross-WP test impact documentation."""
import json
import pathlib

WORKSPACE = pathlib.Path(__file__).parent.parent.parent
ADR_FILE = WORKSPACE / "docs" / "decisions" / "ADR-009-cross-wp-test-impact.md"
INDEX_FILE = WORKSPACE / "docs" / "decisions" / "index.jsonl"


def test_adr_009_file_exists():
    """ADR-009 file must exist in docs/decisions/."""
    assert ADR_FILE.exists(), f"ADR-009 file not found: {ADR_FILE}"


def test_adr_009_required_sections():
    """ADR-009 must contain all required sections."""
    content = ADR_FILE.read_text(encoding="utf-8")
    required = ["ADR-009", "Status", "Context", "Decision", "Consequences"]
    for section in required:
        assert section in content, f"ADR-009 missing required section/field: {section}"


def test_adr_009_index_entry():
    """index.jsonl must contain an ADR-009 entry with correct fields."""
    lines = INDEX_FILE.read_text(encoding="utf-8").splitlines()
    entry = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        if record.get("ADR-ID") == "ADR-009":
            entry = record
            break
    assert entry is not None, "ADR-009 entry not found in index.jsonl"
    assert entry["Status"] == "Active", f"Expected Status=Active, got {entry['Status']}"
    assert "MNT-025" in entry["Related WPs"], "ADR-009 index entry must list MNT-025 in Related WPs"
    assert "MNT-026" in entry["Related WPs"], "ADR-009 index entry must list MNT-026 in Related WPs"


def test_adr_009_references_mnt025():
    """ADR-009 content must reference MNT-025."""
    content = ADR_FILE.read_text(encoding="utf-8")
    assert "MNT-025" in content, "ADR-009 must reference MNT-025"
