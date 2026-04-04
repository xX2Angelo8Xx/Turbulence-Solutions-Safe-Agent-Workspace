"""MNT-014: Verification that ADR-007 and migration WPs were created."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_adr_007_exists():
    adr = REPO / "docs" / "decisions" / "ADR-007-csv-to-jsonl-migration.md"
    assert adr.exists(), "ADR-007 file missing"


def test_adr_007_in_index():
    index = REPO / "docs" / "decisions" / "index.jsonl"
    rows = [json.loads(l) for l in index.read_text(encoding="utf-8").splitlines() if l.strip()]
    ids = [r["ADR-ID"] for r in rows]
    assert "ADR-007" in ids


def test_migration_wps_created():
    wp_file = REPO / "docs" / "workpackages" / "workpackages.jsonl"
    rows = [json.loads(l) for l in wp_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    ids = {r["ID"] for r in rows}
    for i in range(14, 24):
        assert f"MNT-{i:03d}" in ids, f"MNT-{i:03d} missing from workpackages"
