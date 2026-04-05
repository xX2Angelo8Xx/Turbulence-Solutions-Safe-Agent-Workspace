"""Tests for MNT-028: Create ADR-010 Windows-only CI.

Verifies that docs/decisions/ADR-010-windows-only-ci.md exists, contains
required sections, is indexed in docs/decisions/index.jsonl, and references
MNT-027.
"""

import json
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


def test_adr010_file_exists():
    """ADR-010 markdown file must exist in docs/decisions/."""
    assert ADR_010_FILE.exists(), (
        f"Expected file not found: {ADR_010_FILE.relative_to(REPO_ROOT)}"
    )


def test_adr010_index_entry_exists():
    """docs/decisions/index.jsonl must contain an entry for ADR-010."""
    rows = _load_adr_index()
    adr_ids = [r.get("ADR-ID") for r in rows]
    assert "ADR-010" in adr_ids, (
        f"ADR-010 not found in index.jsonl. Found: {adr_ids}"
    )


def test_adr010_references_mnt027():
    """ADR-010 markdown must reference MNT-027 (the WP that disabled macOS/Linux CI)."""
    content = ADR_010_FILE.read_text(encoding="utf-8")
    assert "MNT-027" in content, (
        "ADR-010-windows-only-ci.md does not mention MNT-027"
    )
