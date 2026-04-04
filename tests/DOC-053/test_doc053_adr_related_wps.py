"""Tests for DOC-053: Populate ADR Related WPs.

Verifies that all ADR entries in docs/decisions/index.csv have non-empty
Related WPs columns, and that every WP ID referenced there exists in
docs/workpackages/workpackages.csv.
"""

import csv
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ADR_INDEX = REPO_ROOT / "docs" / "decisions" / "index.csv"
WORKPACKAGES_CSV = REPO_ROOT / "docs" / "workpackages" / "workpackages.csv"
ADR_DIR = REPO_ROOT / "docs" / "decisions"


def _load_adr_index() -> list[dict]:
    """Return all rows from docs/decisions/index.csv."""
    rows = []
    with ADR_INDEX.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    return rows


def _load_workpackage_ids() -> set[str]:
    """Return all WP IDs from docs/workpackages/workpackages.csv."""
    ids: set[str] = set()
    with WORKPACKAGES_CSV.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            wp_id = row.get("ID", "").strip()
            if wp_id:
                ids.add(wp_id)
    return ids


def _extract_wp_ids(related_wps_field: str) -> list[str]:
    """Parse a comma-separated Related WPs field into a list of WP IDs."""
    raw = related_wps_field.strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_adr_index_has_six_entries():
    """The ADR index must contain exactly 6 entries (ADR-001 through ADR-006)."""
    rows = _load_adr_index()
    assert len(rows) == 6, (
        f"Expected 6 ADR entries, found {len(rows)}: "
        + str([r.get("ADR-ID") for r in rows])
    )


def test_all_adr_entries_have_related_wps():
    """Every ADR entry in index.csv must have a non-empty Related WPs column."""
    rows = _load_adr_index()
    empty = [
        row.get("ADR-ID", "<unknown>")
        for row in rows
        if not row.get("Related WPs", "").strip()
    ]
    assert not empty, (
        f"The following ADRs have empty Related WPs: {empty}"
    )


def test_all_referenced_wp_ids_exist_in_workpackages():
    """Every WP ID referenced in ADR index Related WPs must exist in workpackages.csv."""
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
    assert adr is not None, "ADR-001 not found in index.csv"
    related = _extract_wp_ids(adr.get("Related WPs", ""))
    assert len(related) > 0, "ADR-001 has no Related WPs"


def test_adr_002_related_wps_non_empty():
    """ADR-002 must have at least one Related WP."""
    rows = _load_adr_index()
    adr = next((r for r in rows if r.get("ADR-ID") == "ADR-002"), None)
    assert adr is not None, "ADR-002 not found in index.csv"
    related = _extract_wp_ids(adr.get("Related WPs", ""))
    assert len(related) > 0, "ADR-002 has no Related WPs"


def test_adr_003_related_wps_non_empty():
    """ADR-003 must have at least one Related WP."""
    rows = _load_adr_index()
    adr = next((r for r in rows if r.get("ADR-ID") == "ADR-003"), None)
    assert adr is not None, "ADR-003 not found in index.csv"
    related = _extract_wp_ids(adr.get("Related WPs", ""))
    assert len(related) > 0, "ADR-003 has no Related WPs"


def test_adr_004_related_wps_non_empty():
    """ADR-004 must have at least one Related WP."""
    rows = _load_adr_index()
    adr = next((r for r in rows if r.get("ADR-ID") == "ADR-004"), None)
    assert adr is not None, "ADR-004 not found in index.csv"
    related = _extract_wp_ids(adr.get("Related WPs", ""))
    assert len(related) > 0, "ADR-004 has no Related WPs"


def test_adr_005_related_wps_non_empty():
    """ADR-005 must have at least one Related WP."""
    rows = _load_adr_index()
    adr = next((r for r in rows if r.get("ADR-ID") == "ADR-005"), None)
    assert adr is not None, "ADR-005 not found in index.csv"
    related = _extract_wp_ids(adr.get("Related WPs", ""))
    assert len(related) > 0, "ADR-005 has no Related WPs"


def test_adr_006_related_wps_non_empty():
    """ADR-006 must have at least one Related WP."""
    rows = _load_adr_index()
    adr = next((r for r in rows if r.get("ADR-ID") == "ADR-006"), None)
    assert adr is not None, "ADR-006 not found in index.csv"
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
