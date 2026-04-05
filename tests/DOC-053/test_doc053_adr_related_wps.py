"""Tests for DOC-053: Populate ADR Related WPs.

Verifies that all ADR entries in docs/decisions/index.jsonl have non-empty
Related WPs columns, and that every WP ID referenced there exists in
docs/workpackages/workpackages.jsonl.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ADR_INDEX = REPO_ROOT / "docs" / "decisions" / "index.jsonl"
WORKPACKAGES_JSONL = REPO_ROOT / "docs" / "workpackages" / "workpackages.jsonl"
ADR_DIR = REPO_ROOT / "docs" / "decisions"


def _load_adr_index() -> list[dict]:
    """Return all rows from docs/decisions/index.jsonl."""
    rows = []
    for line in ADR_INDEX.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _load_workpackage_ids() -> set[str]:
    """Return all WP IDs from docs/workpackages/workpackages.jsonl."""
    ids: set[str] = set()
    for line in WORKPACKAGES_JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            row = json.loads(line)
            wp_id = row.get("ID", "").strip()
            if wp_id:
                ids.add(wp_id)
    return ids


def _extract_wp_ids(related_wps_field) -> list:
    """Parse Related WPs field (string or list) into a list of WP IDs."""
    if isinstance(related_wps_field, list):
        return [p for p in related_wps_field if p]
    raw = related_wps_field.strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_adr_index_has_ten_entries():
    """The ADR index must contain exactly 10 entries (ADR-001 through ADR-010)."""
    rows = _load_adr_index()
    assert len(rows) == 10, (
        f"Expected 10 ADR entries, found {len(rows)}: "
        + str([r.get("ADR-ID") for r in rows])
    )


def test_all_adr_entries_have_related_wps():
    """Every ADR entry in index.jsonl must have a non-empty Related WPs column."""
    rows = _load_adr_index()
    empty = [
        row.get("ADR-ID", "<unknown>")
        for row in rows
        if not _extract_wp_ids(row.get("Related WPs", ""))
    ]
    assert not empty, (
        f"The following ADRs have empty Related WPs: {empty}"
    )


def test_all_referenced_wp_ids_exist_in_workpackages():
    """Every WP ID referenced in ADR index Related WPs must exist in workpackages.jsonl."""
    adr_rows = _load_adr_index()
    wp_ids = _load_workpackage_ids()
    missing: list[str] = []
    for row in adr_rows:
        adr_id = row.get("ADR-ID", "<unknown>")
        referenced = _extract_wp_ids(row.get("Related WPs", ""))
        for wp_id in referenced:
            if wp_id not in wp_ids:
                missing.append(f"{adr_id} references unknown WP '{wp_id}'")
    assert not missing, (
        "Unknown WP references found in ADR index:\n  " + "\n  ".join(missing)
    )


def test_adr_001_related_wps_non_empty():
    """ADR-001 must have at least one Related WP."""
    rows = _load_adr_index()
    adr = next((r for r in rows if r.get("ADR-ID") == "ADR-001"), None)
    assert adr is not None, "ADR-001 not found in index.jsonl"
    related = _extract_wp_ids(adr.get("Related WPs", ""))
    assert len(related) > 0, "ADR-001 has no Related WPs"


def test_adr_002_related_wps_non_empty():
    """ADR-002 must have at least one Related WP."""
    rows = _load_adr_index()
    adr = next((r for r in rows if r.get("ADR-ID") == "ADR-002"), None)
    assert adr is not None, "ADR-002 not found in index.jsonl"
    related = _extract_wp_ids(adr.get("Related WPs", ""))
    assert len(related) > 0, "ADR-002 has no Related WPs"


def test_adr_003_related_wps_non_empty():
    """ADR-003 must have at least one Related WP."""
    rows = _load_adr_index()
    adr = next((r for r in rows if r.get("ADR-ID") == "ADR-003"), None)
    assert adr is not None, "ADR-003 not found in index.jsonl"
    related = _extract_wp_ids(adr.get("Related WPs", ""))
    assert len(related) > 0, "ADR-003 has no Related WPs"


def test_adr_004_related_wps_non_empty():
    """ADR-004 must have at least one Related WP."""
    rows = _load_adr_index()
    adr = next((r for r in rows if r.get("ADR-ID") == "ADR-004"), None)
    assert adr is not None, "ADR-004 not found in index.jsonl"
    related = _extract_wp_ids(adr.get("Related WPs", ""))
    assert len(related) > 0, "ADR-004 has no Related WPs"


def test_adr_005_related_wps_non_empty():
    """ADR-005 must have at least one Related WP."""
    rows = _load_adr_index()
    adr = next((r for r in rows if r.get("ADR-ID") == "ADR-005"), None)
    assert adr is not None, "ADR-005 not found in index.jsonl"
    related = _extract_wp_ids(adr.get("Related WPs", ""))
    assert len(related) > 0, "ADR-005 has no Related WPs"


def test_adr_006_related_wps_non_empty():
    """ADR-006 must have at least one Related WP."""
    rows = _load_adr_index()
    adr = next((r for r in rows if r.get("ADR-ID") == "ADR-006"), None)
    assert adr is not None, "ADR-006 not found in index.jsonl"
    related = _extract_wp_ids(adr.get("Related WPs", ""))
    assert len(related) > 0, "ADR-006 has no Related WPs"


def test_adr_001_markdown_has_related_wps():
    """ADR-001 markdown file must have a non-empty Related WPs field."""
    adr_file = ADR_DIR / "ADR-001-draft-releases.md"
    content = adr_file.read_text(encoding="utf-8")
    match = re.search(r"\*\*Related WPs:\*\*\s*(.+)", content)
    assert match is not None, "ADR-001 markdown missing **Related WPs:** line"
    value = match.group(1).strip()
    assert value, "ADR-001 markdown Related WPs field is empty"


def test_adr_002_markdown_has_related_wps():
    """ADR-002 markdown file must have a non-empty Related WPs field."""
    adr_file = ADR_DIR / "ADR-002-ci-test-gate.md"
    content = adr_file.read_text(encoding="utf-8")
    match = re.search(r"\*\*Related WPs:\*\*\s*(.+)", content)
    assert match is not None, "ADR-002 markdown missing **Related WPs:** line"
    value = match.group(1).strip()
    assert value, "ADR-002 markdown Related WPs field is empty"


def test_adr_003_markdown_has_related_wps():
    """ADR-003 markdown file must have a non-empty Related WPs field."""
    adr_file = ADR_DIR / "ADR-003-workspace-upgrade.md"
    content = adr_file.read_text(encoding="utf-8")
    match = re.search(r"\*\*Related WPs:\*\*\s*(.+)", content)
    assert match is not None, "ADR-003 markdown missing **Related WPs:** line"
    value = match.group(1).strip()
    assert value, "ADR-003 markdown Related WPs field is empty"


def test_adr_004_markdown_has_related_wps():
    """ADR-004 markdown file must have a non-empty Related WPs field."""
    adr_file = ADR_DIR / "ADR-004-architecture-decision-records.md"
    content = adr_file.read_text(encoding="utf-8")
    match = re.search(r"\*\*Related WPs:\*\*\s*(.+)", content)
    assert match is not None, "ADR-004 markdown missing **Related WPs:** line"
    value = match.group(1).strip()
    assert value, "ADR-004 markdown Related WPs field is empty"


def test_adr_005_markdown_has_related_wps():
    """ADR-005 markdown file must have a non-empty Related WPs field."""
    adr_file = ADR_DIR / "ADR-005-no-rollback-ui.md"
    content = adr_file.read_text(encoding="utf-8")
    match = re.search(r"\*\*Related WPs:\*\*\s*(.+)", content)
    assert match is not None, "ADR-005 markdown missing **Related WPs:** line"
    value = match.group(1).strip()
    assert value, "ADR-005 markdown Related WPs field is empty"


def test_adr_006_markdown_has_related_wps():
    """ADR-006 markdown file must have a non-empty Related WPs field."""
    adr_file = ADR_DIR / "ADR-006-defer-code-signing.md"
    content = adr_file.read_text(encoding="utf-8")
    match = re.search(r"\*\*Related WPs:\*\*\s*(.+)", content)
    assert match is not None, "ADR-006 markdown missing **Related WPs:** line"
    value = match.group(1).strip()
    assert value, "ADR-006 markdown Related WPs field is empty"


def test_adr_007_related_wps_non_empty():
    """ADR-007 must have at least one Related WP."""
    rows = _load_adr_index()
    adr = next((r for r in rows if r.get("ADR-ID") == "ADR-007"), None)
    assert adr is not None, "ADR-007 not found in index.jsonl"
    related = _extract_wp_ids(adr.get("Related WPs", ""))
    assert len(related) > 0, "ADR-007 has no Related WPs"


def test_adr_007_markdown_has_related_wps():
    """ADR-007 markdown file must have a non-empty Related WPs field."""
    adr_file = ADR_DIR / "ADR-007-csv-to-jsonl-migration.md"
    content = adr_file.read_text(encoding="utf-8")
    match = re.search(r"\*\*Related WPs:\*\*\s*(.+)", content)
    assert match is not None, "ADR-007 markdown missing **Related WPs:** line"
    value = match.group(1).strip()
    assert value, "ADR-007 markdown Related WPs field is empty"


def test_wp_ids_in_index_have_valid_format():
    """All WP IDs in the ADR index must match the pattern CATEGORY-NNN."""
    wp_id_pattern = re.compile(r"^[A-Z]+-\d+$")
    adr_rows = _load_adr_index()
    invalid: list[str] = []
    for row in adr_rows:
        adr_id = row.get("ADR-ID", "<unknown>")
        for wp_id in _extract_wp_ids(row.get("Related WPs", "")):
            if not wp_id_pattern.match(wp_id):
                invalid.append(f"{adr_id}: invalid WP ID format '{wp_id}'")
    assert not invalid, (
        "Invalid WP ID formats in ADR index:\n  " + "\n  ".join(invalid)
    )
