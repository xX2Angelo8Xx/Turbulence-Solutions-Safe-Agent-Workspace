"""Tester edge-case tests for MNT-028: Create ADR-010 Windows-only CI.

These tests go beyond the developer's basic existence checks and verify
content correctness, schema compliance, and structural integrity of ADR-010.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ADR_010_FILE = REPO_ROOT / "docs" / "decisions" / "ADR-010-windows-only-ci.md"
ADR_INDEX = REPO_ROOT / "docs" / "decisions" / "index.jsonl"


def _load_adr_index() -> list[dict]:
    rows = []
    for line in ADR_INDEX.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _get_adr010_entry() -> dict:
    rows = _load_adr_index()
    entry = next((r for r in rows if r.get("ADR-ID") == "ADR-010"), None)
    assert entry is not None, "ADR-010 entry not found in index.jsonl"
    return entry


# ---------------------------------------------------------------------------
# ADR document content checks
# ---------------------------------------------------------------------------

def test_adr010_has_required_sections():
    """ADR-010 must contain all required structural sections."""
    content = ADR_010_FILE.read_text(encoding="utf-8")
    required = ["## Context", "## Decision", "## Consequences", "## Re-Enablement Criteria"]
    missing = [s for s in required if s not in content]
    assert not missing, f"ADR-010 is missing required sections: {missing}"


def test_adr010_status_header_is_active():
    """ADR-010 markdown Status: field must be 'Active'."""
    content = ADR_010_FILE.read_text(encoding="utf-8")
    assert "**Status:** Active" in content, (
        "ADR-010 markdown does not declare Status: Active"
    )


def test_adr010_references_mnt028():
    """ADR-010 markdown must reference MNT-028 (the WP that created it)."""
    content = ADR_010_FILE.read_text(encoding="utf-8")
    assert "MNT-028" in content, (
        "ADR-010-windows-only-ci.md does not mention MNT-028"
    )


def test_adr010_date_header_is_present():
    """ADR-010 markdown must include a Date: header."""
    content = ADR_010_FILE.read_text(encoding="utf-8")
    assert "**Date:**" in content, "ADR-010 markdown is missing the Date header"


def test_adr010_mentions_windows_only():
    """ADR-010 decision section must explicitly mention Windows-only CI."""
    content = ADR_010_FILE.read_text(encoding="utf-8")
    assert "windows-latest" in content.lower() or "windows only" in content.lower(), (
        "ADR-010 does not clearly state the Windows-only CI decision"
    )


# ---------------------------------------------------------------------------
# index.jsonl schema checks for ADR-010
# ---------------------------------------------------------------------------

def test_adr010_index_title_non_empty():
    """ADR-010 index entry Title must be non-empty."""
    entry = _get_adr010_entry()
    assert entry.get("Title", "").strip(), "ADR-010 index entry has empty Title"


def test_adr010_index_status_is_active():
    """ADR-010 index entry Status must be 'Active'."""
    entry = _get_adr010_entry()
    assert entry.get("Status") == "Active", (
        f"Expected Status 'Active', got '{entry.get('Status')}'"
    )


def test_adr010_index_date_format():
    """ADR-010 index entry Date must match YYYY-MM-DD format."""
    entry = _get_adr010_entry()
    date_val = entry.get("Date", "")
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", date_val), (
        f"ADR-010 Date '{date_val}' does not match YYYY-MM-DD format"
    )


def test_adr010_index_superseded_by_empty():
    """ADR-010 index entry Superseded By must be empty (it is a new active ADR)."""
    entry = _get_adr010_entry()
    superseded = entry.get("Superseded By", "")
    assert superseded == "" or superseded is None, (
        f"ADR-010 unexpectedly has Superseded By = '{superseded}'"
    )


def test_adr010_index_related_wps_includes_mnt027_and_mnt028():
    """ADR-010 index Related WPs must include both MNT-027 and MNT-028."""
    entry = _get_adr010_entry()
    related = entry.get("Related WPs", [])
    if isinstance(related, str):
        related = [p.strip() for p in related.split(",") if p.strip()]
    assert "MNT-027" in related, f"MNT-027 not found in ADR-010 Related WPs: {related}"
    assert "MNT-028" in related, f"MNT-028 not found in ADR-010 Related WPs: {related}"


def test_adr010_is_last_entry_in_index():
    """ADR-010 must be the last (most recent) entry in index.jsonl."""
    rows = _load_adr_index()
    assert rows, "index.jsonl is empty"
    last_id = rows[-1].get("ADR-ID")
    assert last_id == "ADR-010", (
        f"Expected ADR-010 to be the last entry, but last entry is '{last_id}'"
    )
