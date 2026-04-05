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


# --- Edge-case tests added by Tester (MNT-026) ---

def test_adr_009_status_header_is_active():
    """ADR-009 header block must declare Status: Active (not just anywhere in the text)."""
    content = ADR_FILE.read_text(encoding="utf-8")
    # The header section is before the first '##' heading; Status must appear there.
    header_end = content.find("\n## ")
    header = content[:header_end] if header_end != -1 else content
    assert "**Status:** Active" in header, (
        "ADR header must contain '**Status:** Active' (not buried in body text)"
    )


def test_adr_009_references_adr008():
    """ADR-009 must reference ADR-008, the rule it extends."""
    content = ADR_FILE.read_text(encoding="utf-8")
    assert "ADR-008" in content, "ADR-009 must reference ADR-008 (the rule it enforces)"


def test_adr_009_index_entry_has_all_required_fields():
    """ADR-009 index entry must have all mandatory JSONL fields."""
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
    required_fields = ["ADR-ID", "Title", "Status", "Date", "Related WPs", "Superseded By"]
    for field in required_fields:
        assert field in entry, f"ADR-009 index entry missing field: {field}"


def test_adr_009_superseded_by_is_empty():
    """ADR-009 is not superseded — Superseded By must be empty string."""
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
    assert entry.get("Superseded By") == "", (
        f"ADR-009 should not be superseded, got: {entry.get('Superseded By')!r}"
    )


def test_adr_009_index_entry_is_valid_json():
    """Every line in index.jsonl must be valid JSON (no corruption from ADR-009 addition)."""
    raw = INDEX_FILE.read_text(encoding="utf-8")
    for i, line in enumerate(raw.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"index.jsonl line {i} is not valid JSON: {exc}") from exc


def test_adr_009_hook_script_mentioned():
    """ADR-009 must mention check_test_impact.py — the tool it documents."""
    content = ADR_FILE.read_text(encoding="utf-8")
    assert "check_test_impact.py" in content, (
        "ADR-009 must reference scripts/check_test_impact.py"
    )


def test_adr_009_exit_code_0_documented():
    """ADR-009 must document that the hook exits with code 0 (advisory-only)."""
    content = ADR_FILE.read_text(encoding="utf-8")
    assert "exit code 0" in content.lower() or "exits with code 0" in content.lower(), (
        "ADR-009 must explicitly state that the hook exits with code 0"
    )
